import time
import cv2
import threading
from backend.src.utils.logger import setup_logger
from backend.src.core.camera import Camera
from backend.src.core.detector import Detector
from backend.src.services.alert_service import AlertService
from backend.src.web.websocket import broadcast_status
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import platform
import os

logger = setup_logger(__name__)

class Monitor:
    _instance = None

    @classmethod
    def get_instance(cls):
        return cls._instance

    def __init__(self, config):
        """モニターの初期化"""
        if Monitor._instance is not None:
            raise Exception("Monitor is a singleton!")
        Monitor._instance = self
        
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
        
        # フレームバッファの初期化
        self.frame_buffer = None
        self.frame_lock = threading.Lock()
        
        # 検出結果の初期化
        self.detection_results = {
            'person_detected': False,
            'smartphone_detected': False,
            'person_bbox': None,
            'phone_bbox': None
        }
        self.detection_lock = threading.Lock()

    def update_detection_results(self, results):
        """検出結果を更新"""
        with self.detection_lock:
            self.detection_results = results

    def draw_detection_overlay(self, frame):
        """検出結果をフレームに描画"""
        with self.detection_lock:
            results = self.detection_results.copy()

        # 人物検出の表示
        if results['person_bbox'] is not None:
            x1, y1, x2, y2 = results['person_bbox']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, 'Person', (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # スマートフォン検出の表示
        if results['phone_bbox'] is not None:
            x1, y1, x2, y2 = results['phone_bbox']
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
            cv2.putText(frame, 'Smartphone', (int(x1), int(y1)-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        # ステータス表示
        status_text = []
        if not results['person_detected']:
            elapsed = time.time() - self.last_seen_time
            if elapsed > self.absence_threshold:
                status_text.append(f'不在中: {int(elapsed)}秒')
        if results['smartphone_detected']:
            phone_elapsed = time.time() - self.last_phone_detection_time
            if phone_elapsed > self.smartphone_threshold:
                status_text.append(f'スマホ使用中: {int(phone_elapsed)}秒')

        # ステータステキストの描画
        y_offset = 30
        for text in status_text:
            cv2.putText(frame, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            y_offset += 30

        return frame

    def get_current_frame(self):
        """WebUIで使用するフレームを取得（検出結果付き）"""
        with self.frame_lock:
            if self.frame_buffer is None:
                return None
            
            # フレームのコピーを作成
            frame = self.frame_buffer.copy()
            
            # 検出結果を取得
            with self.detection_lock:
                detection_results = self.detection_results.copy()
            
            # 検出結果を描画
            self.detector.draw_detections(frame, detection_results)
            
            # JPEG形式にエンコード
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            return buffer.tobytes()

    def extend_absence_threshold(self, extension_time):
        """absence_thresholdを延長するメソッド"""
        self.absence_threshold += extension_time
        self.extension_display_time = extension_time
        self.extension_applied_at = time.time()  # 延長された時刻を記録
        logger.info(f"Absence threshold updated to: {self.absence_threshold}")

    def run(self):
        try:
            while True:
                # カメラからフレームを取得
                frame = self.camera.get_frame()
                if frame is None:
                    continue

                # 検出処理の実行
                detection_results = self.detector.detect_objects(frame)
                
                # 人物の検出状態を更新（MediaPipeまたはYOLOのいずれかで検出された場合）
                person_detected = detection_results['person_detected']
                if person_detected:
                    self.handle_person_presence()
                else:
                    self.handle_person_absence()

                # スマートフォンの検出状態を更新
                smartphone_detected = 'smartphone' in detection_results.get('detections', {})
                if smartphone_detected:
                    if not self.smartphone_in_use:
                        self.last_phone_detection_time = time.time()
                        self.smartphone_in_use = True
                    
                    # スマートフォン使用時間のチェック
                    phone_use_time = time.time() - self.last_phone_detection_time
                    if phone_use_time > self.smartphone_threshold and not self.alert_triggered_smartphone:
                        self.alert_service.trigger_smartphone_alert()
                        self.alert_triggered_smartphone = True
                else:
                    self.smartphone_in_use = False
                    self.alert_triggered_smartphone = False

                # 検出結果の更新
                with self.detection_lock:
                    self.detection_results = {
                        'person_detected': person_detected,
                        'smartphone_detected': smartphone_detected,
                        'landmarks': detection_results.get('landmarks'),
                        'detections': detection_results.get('detections', {})
                    }

                # フレームの更新
                with self.frame_lock:
                    self.frame_buffer = frame.copy()
                
                # WebSocket経由でステータス送信
                status = {
                    'personDetected': person_detected,
                    'smartphoneDetected': smartphone_detected,
                    'absenceTime': time.time() - self.last_seen_time if not person_detected else 0,
                    'smartphoneUseTime': time.time() - self.last_phone_detection_time if smartphone_detected else 0
                }
                broadcast_status(status)

                # OpenCVウィンドウの表示（設定で有効な場合）
                if self.config.get('display', {}).get('show_opencv_window', True):
                    display_frame = frame.copy()
                    self.detector.draw_detections(display_frame, detection_results)
                    self.camera.show_frame(display_frame)

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
                # 人物のバウンディングボックスを描画
                if person_result['bbox'] is not None:
                    x1, y1, x2, y2 = person_result['bbox']
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # スマートフォン検出の実行
                phone_result = self.detector.detect_phone(frame)
                self.handle_phone_detection(phone_result['detected'])  # スマートフォン検出結果を処理
                
                # スマートフォンの検出状態に基づいて描画
                if phone_result['detected'] and phone_result.get('detections'):
                    for detection in phone_result['detections']:
                        bbox = detection['bbox']
                        cv2.rectangle(
                            frame,
                            (int(bbox[0]), int(bbox[1])),
                            (int(bbox[2]), int(bbox[3])),
                            (0, 0, 255),
                            2
                        )
            
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
