import asyncio
from ..tts.sound_service import SoundService
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    AlertError, AlertDeliveryError, NetworkError,
    HTTPError, ConfigError, wrap_exception
)

logger = setup_logger(__name__)

class AlertService:
    """
    通知（LINE Notifyなど）を送信するサービス。
    ConfigManager を介して設定を管理する。
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.alert_sounds = config_manager.get_alert_sounds()
        
        logger.info("AlertService initialized with ConfigManager.")
        self.sound_service = SoundService()


    def trigger_alert(self, message):
        """汎用的なアラートをトリガーする"""
        logger.warning(f"Triggering alert: {message}")
        # 汎用アラート用の音声 (デフォルト)
        self.sound_service.play_alert() 

    def trigger_absence_alert(self, absence_duration):
        """不在アラートをトリガーする"""
        message = f"ユーザーが席を離れて {absence_duration:.0f} 秒が経過しました。"
        logger.warning(message)
        # 不在アラート用の音声
        sound_file = self.alert_sounds.get("absence", "alert.wav") # デフォルトは alert.wav
        self.sound_service.play_alert(sound_file)

    def trigger_smartphone_alert(self, usage_duration):
        """スマートフォン使用アラートをトリガーする"""
        message = f"ユーザーがスマートフォンを {usage_duration:.0f} 秒間使用しています。"
        logger.warning(message)
        # スマホアラート用の音声
        sound_file = self.alert_sounds.get("smartphone", "alert.wav") # デフォルトは alert.wav
        self.sound_service.play_alert(sound_file)
