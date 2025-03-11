from concurrent.futures import ThreadPoolExecutor
from backend.src.services.line_service import LineService
from backend.src.services.sound_service import SoundService
from backend.src.services.twilio_service import TwilioService
from backend.src.utils.logger import setup_logger

logger = setup_logger(__name__)

class AlertService:
    def __init__(self, config):
        self.line_service = LineService(config)
        self.sound_service = SoundService(config)
        self.twilio_service = TwilioService(config)
        self.executor = ThreadPoolExecutor(max_workers=4)

    def trigger_alert(self, message, sound_file='alert.wav'):
        """非同期で通知と音声再生を実行"""
        # self.executor.submit(self.line_service.send_message, message)
        self.executor.submit(self.sound_service.play_alert, sound_file)

    def trigger_absence_alert(self):
        self.trigger_alert("早く監視範囲に戻れ～！", 'person_alert.wav')

    def trigger_smartphone_alert(self):
        self.trigger_alert("スマホばかり触っていないで勉強をしろ！", 'smartphone_alert.wav')

    def shutdown(self):
        self.executor.shutdown(wait=True)
