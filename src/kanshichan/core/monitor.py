import time
import cv2
from src.kanshichan.utils.logger import setup_logger
from src.kanshichan.core.camera import Camera
from src.kanshichan.core.detector import Detector
from src.kanshichan.services.alert_service import AlertService
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import platform
import os

logger = setup_logger(__name__)

class Monitor:
    def __init__(self, config):
        """モニターの初期化"""
        self.config = config
        self.camera = Camera()
        self.detector = Detector()
        self.alert_service = AlertService(config)
        
        # 検出状態の初期化
        self.person_detected = False
        self.smartphone_in_use = False
        
        # 警告状態の初期化
        self.alert_triggered_absence = False
        self.alert_triggered_smartphone = False
        
        # タイムスタンプの初期化
        self.last_seen_time = time.time()
        self.last_phone_detection_time = time.time()
        
        # しきい値の設定
        conditions = config.get('conditions', {})
        absence_condition = conditions.get('absence', {})
        self.absence_threshold = absence_condition.get('threshold_seconds', 5)
        if self.absence_threshold is None:
            logger.warning("Absence threshold is None, setting to default value of 5.")
            self.absence_threshold = 5

        smartphone_condition = conditions.get('smartphone_usage', {})
        self.smartphone_threshold = smartphone_condition.get('threshold_seconds', 3)
        if self.smartphone_threshold is None:
            logger.warning("Smartphone threshold is None, setting to default value of 3.")
            self.smartphone_threshold = 3

        # 延長時間を管理する変数
        self.extension_display_time = 0
        self.extension_applied_at = None

    def extend_absence_threshold(self, extension_time):
        """absence_thresholdを延長するメソッド"""
        self.absence_threshold += extension_time
        self.extension_display_time = extension_time
        self.extension_applied_at = time.time()  # 延長された時刻を記録
        logger.info(f"Absence threshold updated to: {self.absence_threshold}")

    def run(self):
        try:
            while True:
                frame = self.camera.get_frame()
                if frame is None:
                    break

                # 人物検出
                person_detected = self.detector.detect_person(frame)
                if person_detected:
                    self.handle_person_presence()
                    
                    # スマホ検出
                    phone_detected = self.detector.detect_phone(frame)
                    self.handle_phone_detection(phone_detected)
                else:
                    self.handle_person_absence()

                # 画面表示の更新
                self.update_display(frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            self.cleanup()

    def handle_person_presence(self):
        self.last_seen_time = time.time()
        if self.alert_triggered_absence:
            self.alert_triggered_absence = False

    def handle_person_absence(self):
        current_time = time.time()
        absence_time = current_time - self.last_seen_time
        
        if absence_time > self.absence_threshold and not self.alert_triggered_absence:
            self.alert_service.trigger_absence_alert()
            self.alert_triggered_absence = True

    def handle_phone_detection(self, phone_detected):
        current_time = time.time()
        
        if phone_detected['detected']:
            if not self.smartphone_in_use:
                self.smartphone_in_use = True
                self.last_phone_detection_time = current_time
            else:
                phone_usage_time = current_time - self.last_phone_detection_time
                if phone_usage_time > self.smartphone_threshold and not self.alert_triggered_smartphone:
                    self.alert_service.trigger_smartphone_alert()
                    self.alert_triggered_smartphone = True
        else:
            # スマートフォンが検出されなかった場合の処理
            if self.smartphone_in_use:
                # 一定間内に再度検出されなければ使用中を解除
                if current_time - self.last_phone_detection_time > 5.0:  # 5秒のしきい値
                    self.smartphone_in_use = False
                    self.alert_triggered_smartphone = False

    def cleanup(self):
        self.camera.release()
        cv2.destroyAllWindows()

    def update_display(self, frame):
        """画面表示を更新する"""
        try:
            # 人物検出の実行
            person_result = self.detector.detect_person(frame)
            self.person_detected = person_result['detected']
            
            if self.person_detected:
                # 人物のランドマークを描画
                self.detector.draw_landmarks(frame, person_result)
                
                # スマートフォン検出の実行
                phone_result = self.detector.detect_phone(frame)
                self.handle_phone_detection(phone_result)  # スマートフォン検出結果を処理
                
                # スマートフォンの検出状態に基づいて描画
                if self.smartphone_in_use:
                    combined_results = {
                        'landmarks': person_result.get('landmarks'),
                        'detections': phone_result.get('detections')
                    }
                    self.detector.draw_landmarks(frame, combined_results)
            
            # 検出結果のテキストを描画
            self.draw_detection_results(frame)
            
            # 延長時間が設定された場合の表示
            if self.extension_display_time > 0 and self.extension_applied_at:
                elapsed_time = time.time() - self.extension_applied_at
                if elapsed_time < 5:  # 5秒間表示
                    cv2.putText(frame, f"しきい値延長: +{self.extension_display_time}秒", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            # フレームを表示
            self.camera.show_frame(frame)
            
        except Exception as e:
            logger.error(f"画面表示の更新中にエラーが発生しました: {e}")

    def draw_detection_results(self, frame):
        """検出結果を画面に描画する"""
        # PILイメージに変換
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # フォントの設定（システムにインストールされているフォントのパスを指定）
        try:
            font_path = self._get_system_font()
            font = ImageFont.truetype(font_path, 32)
        except Exception:
            font = ImageFont.load_default()  # デフォルトフォント
        
        # 現在の状態を表示
        status_text = []
        
        # 人物検出状態
        if self.person_detected:
            status_text.append("人物検出中")
        else:
            status_text.append("人物未検出")
        
        # スマートフォン検出状態
        if self.smartphone_in_use:
            status_text.append("スマホ使用中")
        
        # 警告状態
        if self.alert_triggered_absence:
            status_text.append("不在警告中")
        if self.alert_triggered_smartphone:
            status_text.append("スマホ使用警告中")

         # 延長時間が設定された場合の表示
        if self.extension_display_time > 0 and self.extension_applied_at:
            elapsed_time = time.time() - self.extension_applied_at
            if elapsed_time < 5:  # 5秒間表示
                status_text.append(f"しきい値延長: +{self.extension_display_time}秒")
            else:
                # 表示をリセット
                self.extension_display_time = 0
                self.extension_applied_at = None
        
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
                    "C:\\Windows\\Fonts\\yugothic.ttf"   # 游ゴシック
                ]
            elif system == "Darwin":  # macOS
                font_paths = [
                    "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
                    "/System/Library/Fonts/AppleGothic.ttf"
                ]
            else:  # Linux
                font_paths = [
                    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
                ]

            # 利用可能なフォントを探す
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return font_path

        except Exception as e:
            logger.warning(f"Error loading system font: {e}")
        
        return None
