import asyncio
from typing import List, Optional, Dict, Any
from ..tts.sound_service import SoundService
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    AlertError, AlertDeliveryError, NetworkError,
    HTTPError, ConfigError, wrap_exception
)
from .enums import AlertChannel
from .notification_delivery import NotificationDeliveryService

logger = setup_logger(__name__)

class AlertService:
    """
    通知（音声アラート、メールなど）を送信するサービス。
    ConfigManager を介して設定を管理する。
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.alert_sounds = config_manager.get_alert_sounds()
        self.notification_delivery = NotificationDeliveryService(config_manager)
        self.sound_service = SoundService()
        logger.info("AlertService initialized with ConfigManager.")


    def trigger_alert(self, message: str, channels: Optional[List[AlertChannel]] = None):
        """汎用的なアラートをトリガーする"""
        logger.warning(f"Triggering alert: {message}")

        # デフォルトチャンネルは音声のみ
        if channels is None:
            channels = [AlertChannel.SOUND]

        # 音声アラート処理
        if AlertChannel.SOUND in channels:
            self.sound_service.play_alert()

        # その他のチャンネルへの通知配信
        other_channels = [ch for ch in channels if ch != AlertChannel.SOUND]
        if other_channels:
            self.notification_delivery.deliver_notification(
                message,
                other_channels,
                subject="KanshiChan アラート通知"
            )

    def trigger_absence_alert(self, absence_duration: float, channels: Optional[List[AlertChannel]] = None):
        """不在アラートをトリガーする"""
        message = f"ユーザーが席を離れて {absence_duration:.0f} 秒が経過しました。"
        logger.warning(message)

        # デフォルトチャンネルは音声のみ
        if channels is None:
            channels = [AlertChannel.SOUND]

        # 音声アラート処理
        if AlertChannel.SOUND in channels:
            # 不在アラート用の音声
            sound_file = self.alert_sounds.get("absence", "alert.wav") # デフォルトは alert.wav
            self.sound_service.play_alert(sound_file)
        
        # その他のチャンネルへの通知配信
        other_channels = [ch for ch in channels if ch != AlertChannel.SOUND]
        if other_channels:
            self.notification_delivery.deliver_notification(
                message,
                other_channels,
                subject="KanshiChan 不在アラート"
            )

    def trigger_smartphone_alert(self, usage_duration: float, channels: Optional[List[AlertChannel]] = None):
        """スマートフォン使用アラートをトリガーする"""
        message = f"ユーザーがスマートフォンを {usage_duration:.0f} 秒間使用しています。"
        logger.warning(message)

        # デフォルトチャンネルは音声のみ
        if channels is None:
            channels = [AlertChannel.SOUND]

        # 音声アラート処理
        if AlertChannel.SOUND in channels:
            # スマホアラート用の音声
            sound_file = self.alert_sounds.get("smartphone", "alert.wav") # デフォルトは alert.wav
            self.sound_service.play_alert(sound_file)
            
        # その他のチャンネルへの通知配信
        other_channels = [ch for ch in channels if ch != AlertChannel.SOUND]
        if other_channels:
            self.notification_delivery.deliver_notification(
                message,
                other_channels,
                subject="KanshiChan スマートフォン使用アラート"
            )
            
    def _send_email(self, message: str, subject: str, additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Eメール通知を送信する（直接使用せず、NotificationDeliveryServiceを使用）
        
        Args:
            message: メール本文
            subject: メール件名
            additional_data: 追加データ
            
        Returns:
            送信成功時True、失敗時False
        """
        try:
            # NotificationDeliveryServiceのメソッドを呼び出し
            return self.notification_delivery._send_email(message, subject, additional_data)
        except Exception as e:
            email_error = wrap_exception(
                e, AlertDeliveryError,
                "Error sending email via AlertService",
                details={'subject': subject}
            )
            logger.error(f"Email notification error: {email_error.to_dict()}")
            return False
