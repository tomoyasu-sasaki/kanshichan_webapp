import time
import cv2
from src.kanshichan.utils.logger import setup_logger
from src.kanshichan.core.camera import Camera
from src.kanshichan.core.detector import Detector
from src.kanshichan.services.alert_service import AlertService

logger = setup_logger(__name__)

class Monitor:
    def __init__(self, config):
        self.config = config
        self.camera = Camera()
        self.detector = Detector()
        self.alert_service = AlertService(config)
        
        self.last_seen_time = time.time()
        self.alert_triggered_absence = False
        self.smartphone_in_use = False
        self.alert_triggered_smartphone = False
        self.last_phone_detection_time = time.time()
        
        self.absence_threshold = config['conditions']['absence']['threshold_seconds']
        self.smartphone_threshold = config['conditions']['smartphone_usage']['threshold_seconds']

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
        
        if phone_detected:
            if not self.smartphone_in_use:
                self.smartphone_in_use = True
                self.last_phone_detection_time = current_time
            else:
                phone_usage_time = current_time - self.last_phone_detection_time
                if phone_usage_time > self.smartphone_threshold and not self.alert_triggered_smartphone:
                    self.alert_service.trigger_smartphone_alert()
                    self.alert_triggered_smartphone = True
        else:
            if current_time - self.last_phone_detection_time > 5.0:  # RESET_BUFFER
                self.smartphone_in_use = False
                self.alert_triggered_smartphone = False

    def cleanup(self):
        self.camera.release()
        cv2.destroyAllWindows()

    def update_display(self, frame):
        """画面表示を更新する"""
        try:
            # 検出結果を描画
            self.draw_detection_results(frame)
            
            # フレームを表示
            self.camera.show_frame(frame)
        except Exception as e:
            logger.error(f"Error updating display: {e}")

    def draw_detection_results(self, frame):
        """検出結果を画面に描画する"""
        # 現在の状態を表示
        status_text = []
        if self.alert_triggered_absence:
            status_text.append("不在警告中")
        if self.alert_triggered_smartphone:
            status_text.append("スマホ使用警告中")
        
        # テキストを描画
        for i, text in enumerate(status_text):
            cv2.putText(
                frame,
                text,
                (10, 30 + i * 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
