"""
アラート管理サービス

状態管理等からの通知要求を受け取り、`AlertService` に委譲する
薄いファサードレイヤーを提供します。
"""

from typing import List, Optional
from .alert_service import AlertService
from .enums import AlertChannel
from utils.logger import setup_logger
from utils.exceptions import (
    AlertError, AlertDeliveryError, ValidationError,
    wrap_exception
)

logger = setup_logger(__name__)

class AlertManager:
    """
    アラート通知のトリガーを管理するクラス。
    StateManagerからの通知依頼を受け、AlertServiceを呼び出す。
    """
    def __init__(self, alert_service: AlertService):
        """
        AlertManagerを初期化します。

        Args:
            alert_service (AlertService): 実際の通知処理を行うサービス。
        """
        if alert_service is None:
            logger.error("AlertService instance is required for AlertManager.")
            raise ValidationError(
                "AlertService instance cannot be None",
                details={'required_type': 'AlertService'}
            )
        self.alert_service = alert_service
        logger.info("AlertManager initialized.")

    def trigger_absence_alert(
        self, 
        absence_duration: float, 
        channels: Optional[List[AlertChannel]] = None
    ):
        """
        不在アラートの通知を AlertService に依頼する。
        
        Args:
            absence_duration: 不在持続時間（秒）
            channels: 通知チャンネル一覧（未指定ならデフォルト設定を使用）
        """
        logger.debug(f"Received request to trigger absence alert (duration: {absence_duration}). Delegating to AlertService.")
        try:
            self.alert_service.trigger_absence_alert(absence_duration, channels)
        except Exception as e:
            absence_alert_error = wrap_exception(
                e, AlertError,
                "Error occurred while triggering absence alert via AlertService",
                details={
                    'alert_type': 'absence', 
                    'absence_duration': absence_duration,
                    'channels': [ch.name for ch in channels] if channels else None
                }
            )
            logger.error(f"Absence alert error: {absence_alert_error.to_dict()}")

    def trigger_smartphone_alert(
        self, 
        usage_duration: float,
        channels: Optional[List[AlertChannel]] = None
    ):
        """
        スマートフォン使用アラートの通知を AlertService に依頼する。
        
        Args:
            usage_duration: 使用時間（秒）
            channels: 通知チャンネル一覧（未指定ならデフォルト設定を使用）
        """
        logger.debug(f"Received request to trigger smartphone alert (duration: {usage_duration}). Delegating to AlertService.")
        try:
            self.alert_service.trigger_smartphone_alert(usage_duration, channels)
        except Exception as e:
            smartphone_alert_error = wrap_exception(
                e, AlertError,
                "Error occurred while triggering smartphone alert via AlertService",
                details={
                    'alert_type': 'smartphone',
                    'usage_duration': usage_duration,
                    'channels': [ch.name for ch in channels] if channels else None
                }
            )
            logger.error(f"Smartphone alert error: {smartphone_alert_error.to_dict()}")
            
    def trigger_alert(
        self, 
        message: str, 
        channels: Optional[List[AlertChannel]] = None
    ):
        """
        汎用アラートの通知を AlertService に依頼する。
        
        Args:
            message: アラートメッセージ
            channels: 通知チャンネル一覧（未指定ならデフォルト設定を使用）
        """
        logger.debug(f"Received request to trigger general alert. Delegating to AlertService.")
        try:
            self.alert_service.trigger_alert(message, channels)
        except Exception as e:
            alert_error = wrap_exception(
                e, AlertError,
                "Error occurred while triggering general alert via AlertService",
                details={
                    'alert_type': 'general',
                    'channels': [ch.name for ch in channels] if channels else None
                }
            )
            logger.error(f"General alert error: {alert_error.to_dict()}")

    # 将来的には、アラートの種類に応じたメッセージ生成や、
    # 通知頻度の制御（クールダウン）などのロジックをここに追加することも考えられる。 