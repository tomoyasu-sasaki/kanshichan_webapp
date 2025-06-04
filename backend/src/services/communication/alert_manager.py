from .alert_service import AlertService
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

    def trigger_absence_alert(self):
        """不在アラートの通知を AlertService に依頼する。"""
        logger.debug("Received request to trigger absence alert. Delegating to AlertService.")
        try:
            self.alert_service.trigger_absence_alert()
        except Exception as e:
            absence_alert_error = wrap_exception(
                e, AlertError,
                "Error occurred while triggering absence alert via AlertService",
                details={'alert_type': 'absence'}
            )
            logger.error(f"Absence alert error: {absence_alert_error.to_dict()}")

    def trigger_smartphone_alert(self, usage_duration: float):
        """スマートフォン使用アラートの通知を AlertService に依頼する。"""
        logger.debug(f"Received request to trigger smartphone alert (duration: {usage_duration}). Delegating to AlertService.")
        try:
            self.alert_service.trigger_smartphone_alert(usage_duration)
        except Exception as e:
            smartphone_alert_error = wrap_exception(
                e, AlertError,
                "Error occurred while triggering smartphone alert via AlertService",
                details={
                    'alert_type': 'smartphone',
                    'usage_duration': usage_duration
                }
            )
            logger.error(f"Smartphone alert error: {smartphone_alert_error.to_dict()}")

    # 将来的には、アラートの種類に応じたメッセージ生成や、
    # 通知頻度の制御（クールダウン）などのロジックをここに追加することも考えられる。 