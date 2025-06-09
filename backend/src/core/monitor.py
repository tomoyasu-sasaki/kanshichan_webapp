import time
import cv2
import threading
import datetime
from utils.logger import setup_logger
from core.camera import Camera
from core.detector import Detector
from services.communication.alert_manager import AlertManager
from core.state import StateManager
from core.detection import DetectionManager
from web.websocket import broadcast_status, socketio
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import platform
import os
from utils.config_manager import ConfigManager
from typing import Any, Dict, Optional

# 新しく分割されたクラスをインポート
from core.frame_processor import FrameProcessor
from core.status_broadcaster import StatusBroadcaster
from core.schedule_checker import ScheduleChecker
from core.threshold_manager import ThresholdManager

logger = setup_logger(__name__)


class Monitor:
    """
    統合監視システム - リアルタイム最適化版
    
    リファクタリングされたアーキテクチャ:
    - FrameProcessor: フレーム処理専門
    - StatusBroadcaster: ステータス配信専門  
    - ScheduleChecker: スケジュール確認専門
    - ThresholdManager: 閾値管理専門
    """
    
    def __init__(self,
                 config_manager: ConfigManager,
                 camera: Camera,
                 detector: Detector,
                 detection: DetectionManager,
                 state: StateManager,
                 alert_manager: AlertManager,
                 schedule_manager=None,
                 data_collector=None,
                 storage_service=None,
                 flask_app=None):
        """モニターの初期化 (依存性注入・ConfigManager 版)"""
        self.config_manager = config_manager
        self.camera = camera
        self.detector = detector
        self.detection = detection
        self.state = state
        self.alert_manager = alert_manager
        self.schedule_manager = schedule_manager
        self.flask_app = flask_app
        self.data_collector = data_collector
        self.storage_service = storage_service
        
        # DataCollector開始
        if self.data_collector:
            logger.info("Attempting to start DataCollector...")
            result = self.data_collector.start_collection()
            logger.info(f"DataCollector start result: {result}")
            if result:
                logger.info("DataCollector started successfully")
            else:
                logger.error("DataCollector failed to start")
        else:
            logger.warning("DataCollector instance not available")
        
        # FPS制御設定
        self.target_fps = config_manager.get('optimization.target_fps', 15.0)
        self.min_fps = config_manager.get('optimization.min_fps', 10.0)
        self.frame_time = 1.0 / self.target_fps  # 1/15 ≈ 0.067秒（67ms）
        self.last_frame_time = time.time()
        
        # 専門クラスのインスタンス化
        self.frame_processor = FrameProcessor(
            camera=camera,
            detection_manager=detection,
            state_manager=state
        )
        
        self.status_broadcaster = StatusBroadcaster(
            detector=detector,
            state_manager=state,
            camera=camera,
            config_manager=config_manager
        )
        
        self.schedule_checker = ScheduleChecker(
            schedule_manager=schedule_manager,
            alert_manager=alert_manager,
            check_interval=10
        )
        
        self.threshold_manager = ThresholdManager(
            state_manager=state,
            config_manager=config_manager
        )
        
        self.last_analysis_broadcast = time.time()
        self.analysis_broadcast_interval = 10  # 10秒間隔で分析データ配信
        
        logger.info(f"Monitor initialized with target FPS: {self.target_fps}")

    def update_detection_results(self, results):
        """検出結果を更新（互換性のため）"""
        self.frame_processor.update_stored_detection_results(results)

    def get_current_frame(self):
        """WebUIで使用する描画済みのフレームを取得（互換性のため）"""
        detection_results = self.frame_processor.get_detection_results()
        return self.status_broadcaster.get_current_frame(detection_results)

    def extend_absence_threshold(self, extension_time):
        """absence_thresholdを延長するメソッド（互換性のため）"""
        return self.threshold_manager.extend_absence_threshold(extension_time)

    def run(self):
        """メインループ - FPS制御対応"""
        try:
            frame_count = 0
            fps_start_time = time.time()
            
            while True:
                current_time = time.time()
                
                # FPS制御: 目標フレーム時間に達していない場合はスキップ
                if current_time - self.last_frame_time < self.frame_time:
                    time.sleep(0.001)  # 1ms待機
                    continue
                
                # フレーム処理と状態更新
                processed_data = self.frame_processor.process_frame()
                if processed_data is None:
                    continue
                    
                frame, detections_list = processed_data

                # フレーム処理結果の更新
                self.frame_processor.update_detection_results(detections_list)
                detection_results = self.frame_processor.get_detection_results()

                # フレームバッファ更新とステータスブロードキャスト
                self.status_broadcaster.update_frame_buffer(frame)
                self.status_broadcaster.broadcast_status()

                if current_time - self.last_analysis_broadcast >= self.analysis_broadcast_interval:
                    self._broadcast_analysis_data(detection_results)
                    self.last_analysis_broadcast = current_time

                # OpenCVウィンドウ表示
                self.status_broadcaster.display_frame(frame, detection_results)
                
                # スケジュールチェック（一定間隔ごとに実行）
                self.schedule_checker.check_if_needed()
                
                # FPS統計更新
                frame_count += 1
                self.last_frame_time = current_time
                
                # 1秒ごとにFPS統計をログ出力
                if frame_count % int(self.target_fps) == 0:
                    elapsed = current_time - fps_start_time
                    actual_fps = frame_count / elapsed if elapsed > 0 else 0
                    logger.debug(f"Actual FPS: {actual_fps:.1f}, Target: {self.target_fps}")
                    frame_count = 0
                    fps_start_time = current_time

        finally:
            self.cleanup()

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.data_collector:
            self.data_collector.stop_collection()
            logger.info("DataCollector stopped")
        
        self.camera.release()
        cv2.destroyAllWindows()
        logger.info("Monitor cleanup completed.")

    def draw_detection_results(self, frame):
        """検出結果を画面に描画する（互換性のため）"""
        # PILイメージに変換
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # フォントの設定（システムにインストールされているフォントのパスを指定）
        try:
            font_path = self._get_system_font()
            font = ImageFont.truetype(font_path, 32)
        except Exception:
            font = ImageFont.load_default()  # デフォルトフォント
        
        # 状態テキストのリスト
        status_text = []
        
        # 基本的な状態表示
        if self.state.person_detected:
            status_text.append("人物検出中")
        else:
            status_text.append("人物未検出")
        
        if self.state.smartphone_in_use:
            status_text.append("スマホ使用中")
        
        # 警告状態
        if self.state.alert_triggered_absence:
            status_text.append("不在警告中")
        if self.state.alert_triggered_smartphone:
            status_text.append("スマホ使用警告中")

        # 延長時間の表示（閾値の更新状態）
        display_info = self.threshold_manager.get_extension_display_info()
        if display_info['should_display']:
            status_text.append(f"しきい値延長: +{display_info['extension_time']}秒")

        # テキストを描画
        for i, text in enumerate(status_text):
            draw.text((10, 30 + i * 40), text, font=font, fill=(255, 0, 0))
        
        # OpenCV形式に戻す
        frame[:] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _get_system_font(self):
        """OSに応じたフォントパスを返す"""
        system = platform.system()
        try:
            if system == "Windows":
                font_paths = [
                    "C:\\Windows\\Fonts\\msgothic.ttc",  # MSゴシック
                    "C:\\Windows\\Fonts\\meiryo.ttc",    # メイリオ
                    "C:\\Windows\\Fonts\\arial.ttf"      # Arial
                ]
            elif system == "Darwin":  # macOS
                font_paths = [
                    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                    "/System/Library/Fonts/Arial.ttf",
                    "/System/Library/Fonts/Helvetica.ttc"
                ]
            else:  # Linux
                font_paths = [
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/TTF/arial.ttf"
                ]
            
            # 利用可能なフォントを検索
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return font_path
            
            # フォールバック: デフォルトフォント用のパス
            return font_paths[0] if font_paths else ""
            
        except Exception as e:
            logger.warning(f"システムフォント取得中にエラー: {e}")
            return ""

    def analyze_behavior(self, frame, person_detected, smartphone_in_use):
        """行動分析（互換性のため維持）"""
        # この機能は現在未実装のため、ログのみ出力
        logger.debug(f"Behavior analysis: person={person_detected}, smartphone={smartphone_in_use}")

    def _create_context(self, person_detected, smartphone_in_use):
        """コンテキスト作成（互換性のため維持）"""
        return {
            "person_detected": person_detected,
            "smartphone_in_use": smartphone_in_use,
            "timestamp": time.time()
        }

    def get_status_summary(self):
        """統合ステータス情報を取得"""
        base_status = self.state.get_status_summary()
        
        # 各専門クラスの状態を追加
        status = base_status.copy()
        status.update({
            'frame_processor_status': self.frame_processor.get_detection_results(),
            'frame_buffer_status': self.status_broadcaster.get_frame_buffer_status(),
            'schedule_checker_status': self.schedule_checker.get_status(),
            'threshold_manager_status': self.threshold_manager.get_status()
        })
        
        return status

    def _broadcast_analysis_data(self, current_detection_results: Dict[str, Any]) -> None:
        """
        分析データをWebSocketで配信する
        
        Args:
            current_detection_results: 現在の検出結果
        """
        try:
            if not self.flask_app:
                logger.warning("Flask app not available for analysis broadcast")
                return
                
            with self.flask_app.app_context():
                # BehaviorLogから最近のデータを取得
                from models.behavior_log import BehaviorLog
                from datetime import datetime
                
                # 最近10件のログを取得
                recent_logs = BehaviorLog.get_recent_logs(hours=1)
                if not recent_logs:
                    logger.debug("No recent behavior logs for analysis broadcast")
                    return
                
                # 最近10件のデータを分析用に変換
                behavior_data = {
                    'focus_trends': self._extract_focus_trends(recent_logs[-10:]),
                    'current_status': {
                        'presence_status': self.state.get_status_summary().get('presence_status', 'unknown'),
                        'smartphone_detected': current_detection_results.get('smartphone_detected', False),
                        'focus_level': self._calculate_current_focus(current_detection_results),
                        'posture_score': self._calculate_posture_score(current_detection_results)
                    },
                    'timestamp': datetime.now().isoformat(),
                    'session_stats': {
                        'total_logs': len(recent_logs),
                        'present_time_ratio': self._calculate_presence_ratio(recent_logs),
                        'smartphone_usage_ratio': self._calculate_smartphone_ratio(recent_logs)
                    }
                }
                
                # 拡張ステータスで配信
                enhanced_status = {
                    'behavior_data': behavior_data,
                    'detection_data': current_detection_results,
                    'analysis_results': self._generate_quick_insights(recent_logs)
                }
                
                # WebSocket配信
                self.status_broadcaster.broadcast_enhanced_status(enhanced_status)
                logger.debug(f"Analysis data broadcasted: {len(recent_logs)} logs, {len(behavior_data['focus_trends'])} trends")
            
        except Exception as e:
            logger.error(f"Error broadcasting analysis data: {e}", exc_info=True)

    def _extract_focus_trends(self, logs):
        """ログからフォーカストレンドを抽出"""
        trends = []
        for log in logs:
            trends.append({
                'timestamp': log.timestamp.isoformat(),
                'focus_level': log.focus_level or 0.5,  # デフォルト値
                'presence_status': log.presence_status or 'unknown'  # 在席状況も含める
            })
        return trends
    
    def _calculate_current_focus(self, detection_results):
        """現在のフォーカスレベルを計算"""
        # スマートフォン検出でフォーカスレベル下がる
        if detection_results.get('smartphone_detected', False):
            return 0.3
        # 手検出ありでフォーカス中程度
        elif detection_results.get('hands_detected', False):
            return 0.7
        else:
            return 0.5
    
    def _calculate_posture_score(self, detection_results):
        """姿勢スコアを計算"""
        if detection_results.get('pose_detected', False):
            return 0.8  # ポーズ検出時は良い姿勢と仮定
        return 0.6  # デフォルト値
    
    def _calculate_presence_ratio(self, logs):
        """在席時間の比率を計算"""
        if not logs:
            return 0.0
        present_count = sum(1 for log in logs if log.presence_status == 'present')
        return present_count / len(logs)
    
    def _calculate_smartphone_ratio(self, logs):
        """スマートフォン使用の比率を計算"""
        if not logs:
            return 0.0
        smartphone_count = sum(1 for log in logs if log.smartphone_detected)
        return smartphone_count / len(logs)
    
    def _generate_quick_insights(self, logs):
        """簡単な分析結果を生成"""
        if not logs:
            return []
        
        presence_ratio = self._calculate_presence_ratio(logs)
        smartphone_ratio = self._calculate_smartphone_ratio(logs)
        
        insights = []
        if presence_ratio > 0.8:
            insights.append("高い在席率を維持しています")
        elif presence_ratio < 0.5:
            insights.append("離席時間が多くなっています")
            
        if smartphone_ratio > 0.3:
            insights.append("スマートフォンの使用頻度が高めです")
        elif smartphone_ratio < 0.1:
            insights.append("集中して作業に取り組んでいます")
            
        return insights
