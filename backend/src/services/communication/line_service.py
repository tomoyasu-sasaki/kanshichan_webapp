from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    TextMessage,
    PushMessageRequest,
    ReplyMessageRequest
)
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    LineAPIError, APIError, ConfigError, InitializationError,
    AlertDeliveryError, wrap_exception
)

logger = setup_logger(__name__)

class LineService:
    def __init__(self, config_manager: ConfigManager):
        self.enabled = config_manager.get('line.enabled', False)
        self.token = config_manager.get('line.token')
        self.user_id = config_manager.get('line.user_id')
        self.channel_secret = config_manager.get('line.channel_secret')
        
        if not self.enabled:
            logger.info("LINE service is disabled in config.")
            self.messaging_api = None
            return
            
        if not self.token or self.token == 'YOUR_LINE_NOTIFY_TOKEN':
            logger.warning("LINE token not found or is set to default value. LineService may not function.")
            self.messaging_api = None
            return

        try:
            configuration = Configuration(access_token=self.token)
            self.api_client = ApiClient(configuration)
            self.messaging_api = MessagingApi(self.api_client)
            logger.info("LineService initialized successfully.")
        except Exception as e:
            line_init_error = wrap_exception(
                e, LineAPIError,
                "Failed to initialize LINE Messaging API",
                details={
                    'token_configured': bool(self.token and self.token != 'YOUR_LINE_NOTIFY_TOKEN'),
                    'user_id_configured': bool(self.user_id and self.user_id != 'YOUR_LINE_USER_ID'),
                    'enabled': self.enabled
                }
            )
            logger.error(f"LINE API initialization error: {line_init_error.to_dict()}")
            self.messaging_api = None

    def send_message(self, message):
        if not self.enabled:
            logger.debug("LINE service is disabled. Message not sent.")
            return
            
        if not self.messaging_api:
            logger.error("LINE Messaging API not initialized. Cannot send message.")
            return
            
        if not self.user_id or self.user_id == 'YOUR_LINE_USER_ID':
            logger.error("LINE user_id not configured or is set to default. Cannot send message.")
            return

        try:
            request = PushMessageRequest(
                to=self.user_id,
                messages=[TextMessage(text=message)]
            )
            self.messaging_api.push_message(request)
            logger.info("LINE message sent successfully")
        except Exception as e:
            line_send_error = wrap_exception(
                e, LineAPIError,
                "Error sending LINE message",
                details={
                    'message_length': len(message),
                    'user_id': self.user_id,
                    'api_initialized': bool(self.messaging_api)
                }
            )
            logger.error(f"LINE message sending error: {line_send_error.to_dict()}")
