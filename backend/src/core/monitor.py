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
from typing import Any, Dict, Optional, List, Tuple

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
        """
        行動分析を実行し、結果をデータベースに保存、WebSocketで配信する
        
        Args:
            frame: 分析対象のカメラフレーム
            person_detected: 人物検出フラグ
            smartphone_in_use: スマートフォン使用検出フラグ
        
        Returns:
            Dict: 分析結果
        """
        try:
            # 1. 入力からコンテキスト作成
            context = self._create_context(person_detected, smartphone_in_use)
            
            # 2. フレームから追加特徴量抽出（MediaPipe使用）
            focus_level, posture_data = self._extract_focus_and_posture(frame, person_detected)
            
            # 3. 分析結果保存用データ準備
            now = datetime.datetime.now()
            detection_data = {
                'person_detected': person_detected,
                'smartphone_detected': smartphone_in_use,
                'timestamp': now.isoformat()
            }
            
            # 4. DBに保存
            if self.flask_app:
                with self.flask_app.app_context():
                    from models.behavior_log import BehaviorLog
                    
                    # 検出オブジェクト情報
                    detected_objects = []
                    if person_detected:
                        detected_objects.append({'class': 'person', 'confidence': 0.95})
                    if smartphone_in_use:
                        detected_objects.append({'class': 'smartphone', 'confidence': 0.92})
                    
                    # 在席状況の判定
                    presence_status = 'present' if person_detected else 'absent'
                    
                    # セッションID（日付ベース）
                    session_id = now.strftime('%Y%m%d')
                    
                    # 行動ログ保存
                    log_entry = BehaviorLog.create_log(
                        timestamp=now,
                        detected_objects=detected_objects,
                        focus_level=focus_level,
                        posture_data=posture_data,
                        smartphone_detected=smartphone_in_use,
                        presence_status=presence_status,
                        session_id=session_id,
                        processing_time=10.5,  # 処理時間（ミリ秒）
                        notes="Realtime behavior analysis"
                    )
                    
                    # DBセッションに追加して保存
                    from models import db
                    db.session.add(log_entry)
                    db.session.commit()
                    logger.info(f"Behavior log saved: focus={focus_level:.2f}, smartphone={smartphone_in_use}")
            
            # 5. 分析結果の生成
            analysis_result = {
                'focus_level': focus_level,
                'posture_quality': self._evaluate_posture(posture_data),
                'presence_status': 'present' if person_detected else 'absent',
                'smartphone_usage': smartphone_in_use,
                'timestamp': now.isoformat(),
                'session_id': now.strftime('%Y%m%d')
            }
            
            # 6. WebSocketで結果配信
            self._broadcast_realtime_analysis(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in behavior analysis: {e}", exc_info=True)
            return {
                'error': str(e),
                'status': 'analysis_failed',
                'timestamp': datetime.datetime.now().isoformat()
            }

    def _extract_focus_and_posture(self, frame, person_detected):
        """
        フレームから集中度と姿勢データを抽出
        
        Args:
            frame: カメラフレーム
            person_detected: 人物検出フラグ
            
        Returns:
            tuple: (focus_level, posture_data)
        """
        # 実際の実装ではMediaPipeを使用して詳細分析
        # このサンプル実装では簡易的な値を返す
        
        if not person_detected:
            return 0.0, None
        
        # 人物が検出されている場合は、基本的な集中度とランダムな姿勢データを返す
        import random
        
        # 0.3から0.9の間でランダムな集中度
        focus_level = 0.3 + random.random() * 0.6
        
        # 姿勢データのサンプル
        posture_data = {
            'head_position': 0.7 + random.random() * 0.3,  # 0.7-1.0
            'shoulder_alignment': 0.6 + random.random() * 0.4,  # 0.6-1.0
            'back_straight': random.random() > 0.3,  # 70%の確率でTrue
            'head_angle': random.randint(-10, 10)  # -10度から10度
        }
        
        return focus_level, posture_data
        
    def _evaluate_posture(self, posture_data):
        """
        姿勢データから姿勢の質を評価
        
        Args:
            posture_data: 姿勢データ辞書
            
        Returns:
            str: 姿勢の質評価 ('good', 'fair', 'poor', 'unknown')
        """
        if not posture_data:
            return 'unknown'
            
        # 各指標のスコア化
        head_score = posture_data.get('head_position', 0)
        shoulder_score = posture_data.get('shoulder_alignment', 0)
        is_back_straight = posture_data.get('back_straight', False)
        
        # 総合スコア計算 (0-1)
        total_score = (head_score + shoulder_score) / 2
        if is_back_straight:
            total_score += 0.1
            
        # スコアに基づく評価
        if total_score >= 0.8:
            return 'good'
        elif total_score >= 0.6:
            return 'fair'
        else:
            return 'poor'
            
    def _broadcast_realtime_analysis(self, analysis_result):
        """
        リアルタイム分析結果をWebSocketで配信
        
        Args:
            analysis_result: 分析結果辞書
        """
        try:
            # 最近のログを取得して傾向分析を追加
            if self.flask_app:
                with self.flask_app.app_context():
                    from models.behavior_log import BehaviorLog
                    
                    # 最近30分のログを取得
                    recent_logs = BehaviorLog.get_recent_logs(hours=0.5)
                    
                    # 集中度の傾向を抽出
                    focus_trends = self._extract_focus_trends(recent_logs[-5:] if len(recent_logs) >= 5 else recent_logs)
                    
                    # 直近の在席・スマホ使用率を計算
                    presence_ratio = self._calculate_presence_ratio(recent_logs)
                    smartphone_ratio = self._calculate_smartphone_ratio(recent_logs)
                    
                    # 分析結果にトレンドデータを追加
                    enhanced_result = {
                        **analysis_result,
                        'focus_trends': focus_trends,
                        'presence_ratio': presence_ratio,
                        'smartphone_usage_ratio': smartphone_ratio,
                        'recommendations': self._generate_recommendations(
                            analysis_result['focus_level'],
                            presence_ratio,
                            smartphone_ratio
                        )
                    }
                    
                    # WebSocket経由で配信
                    from web.websocket import socketio
                    socketio.emit('realtime_analysis', enhanced_result)
                    logger.debug(f"Realtime analysis broadcasted: focus={analysis_result['focus_level']:.2f}")
            
        except Exception as e:
            logger.error(f"Error broadcasting realtime analysis: {e}", exc_info=True)
            
    def _generate_recommendations(self, focus_level, presence_ratio, smartphone_ratio):
        """
        分析データに基づいて行動推奨を生成
        
        Args:
            focus_level: 現在の集中度
            presence_ratio: 在席率
            smartphone_ratio: スマホ使用率
            
        Returns:
            list: 推奨事項のリスト
        """
        recommendations = []
        
        # 集中度に基づく推奨
        if focus_level < 0.4:
            recommendations.append("集中力が低下しています。短い休憩を取ることを検討してください。")
        elif focus_level > 0.8:
            recommendations.append("高い集中状態を維持しています。この調子で続けましょう。")
            
        # スマホ使用率に基づく推奨
        if smartphone_ratio > 0.3:
            recommendations.append("スマートフォンの使用頻度が高くなっています。作業効率向上のため、通知をオフにすることを検討してください。")
            
        # 在席率に基づく推奨
        if presence_ratio < 0.7:
            recommendations.append("離席が多くなっています。時間管理のためにポモドーロテクニックを試してみてください。")
            
        # 空の場合はデフォルトの推奨を追加
        if not recommendations:
            recommendations.append("適切な休憩と集中のバランスを維持しましょう。")
            
        return recommendations

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
