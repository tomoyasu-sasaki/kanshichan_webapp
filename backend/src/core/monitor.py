import time
import cv2
import threading
import datetime
from utils.logger import setup_logger
from core.camera import Camera
from core.detector import Detector
from services.alert_manager import AlertManager
from core.state import StateManager
from core.detection import DetectionManager
from web.websocket import broadcast_status, socketio
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import platform
import os
from utils.config_manager import ConfigManager

# 新しく分割されたクラスをインポート
from core.frame_processor import FrameProcessor
from core.status_broadcaster import StatusBroadcaster
from core.schedule_checker import ScheduleChecker
from core.threshold_manager import ThresholdManager

logger = setup_logger(__name__)


class Monitor:
    """
    メイン制御クラス（リファクタリング済み）
    - 各専門クラスの統合管理
    - メインループの制御
    - 初期化とクリーンアップ
    """
    
    def __init__(self,
                 config_manager: ConfigManager,
                 camera: Camera,
                 detector: Detector,
                 detection: DetectionManager,
                 state: StateManager,
                 alert_manager: AlertManager,
                 schedule_manager=None):
        """モニターの初期化 (依存性注入・ConfigManager 版)"""
        self.config_manager = config_manager
        self.camera = camera
        self.detector = detector
        self.detection = detection
        self.state = state
        self.alert_manager = alert_manager
        self.schedule_manager = schedule_manager
        
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
        
        logger.info("Monitor initialized with refactored architecture.")

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
        """メインループ"""
        try:
            while True:
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

                # OpenCVウィンドウ表示
                self.status_broadcaster.display_frame(frame, detection_results)
                
                # スケジュールチェック（一定間隔ごとに実行）
                self.schedule_checker.check_if_needed()
                
                # 短い sleep を入れることでCPU使用率を下げる
                time.sleep(0.01)

        finally:
            self.cleanup()

    def cleanup(self):
        """リソースのクリーンアップ"""
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
