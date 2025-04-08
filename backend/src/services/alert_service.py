import asyncio
from services.line_service import LineService
from services.sound_service import SoundService
from services.twilio_service import TwilioService
from utils.logger import setup_logger
import requests
from utils.config_manager import ConfigManager

logger = setup_logger(__name__)

class AlertService:
    """
    通知（LINE Notifyなど）を送信するサービス。
    ConfigManager を介して設定を管理する。
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        # 設定からメッセージマッピングとアラート音声の設定を取得
        self.message_sound_mapping = config_manager.get_message_sound_mapping()
        self.alert_sounds = config_manager.get_alert_sounds()
        
        logger.info("AlertService initialized with ConfigManager.")
        self.line_service = LineService(config_manager)
        self.sound_service = SoundService()
        self.twilio_service = TwilioService(config_manager)

    def _send_line_notify(self, message):
        """LINE Notifyにメッセージを送信する"""
        line_enabled = self.config_manager.get('line.enabled', False)
        line_token = self.config_manager.get('line.token')

        if not line_enabled:
            logger.info("LINE Notify is disabled in config.")
            return

        if not line_token or line_token == 'YOUR_LINE_NOTIFY_TOKEN':
            logger.warning("LINE Notify token is not set or is default.")
            return

        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {line_token}"}
        data = {"message": message}
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            logger.info("LINE Notify sent successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send LINE Notify: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending LINE Notify: {e}")

    def trigger_alert(self, message):
        """汎用的なアラートをトリガーする"""
        logger.warning(f"Triggering alert: {message}")
        self._send_line_notify(f"🚨 アラート: {message}")
        # 汎用アラート用の音声 (デフォルト)
        self.sound_service.play_alert() 

    def trigger_absence_alert(self, absence_duration):
        """不在アラートをトリガーする"""
        message = f"ユーザーが席を離れて {absence_duration:.0f} 秒が経過しました。"
        logger.warning(message)
        self._send_line_notify(f"🚶‍♂️ 不在検知: {message}")
        # 不在アラート用の音声
        sound_file = self.alert_sounds.get("absence", "alert.wav") # デフォルトは alert.wav
        self.sound_service.play_alert(sound_file)

    def trigger_smartphone_alert(self, usage_duration):
        """スマートフォン使用アラートをトリガーする"""
        message = f"ユーザーがスマートフォンを {usage_duration:.0f} 秒間使用しています。"
        logger.warning(message)
        self._send_line_notify(f"📱 スマホ使用検知: {message}")
        # スマホアラート用の音声
        sound_file = self.alert_sounds.get("smartphone", "alert.wav") # デフォルトは alert.wav
        self.sound_service.play_alert(sound_file)
