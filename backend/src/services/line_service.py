from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    TextMessage,
    PushMessageRequest
)
from linebot.v3.webhook import WebhookHandler
from backend.src.utils.logger import setup_logger

logger = setup_logger(__name__)

class LineService:
    def __init__(self, config):
        line_config = config['line']
        self.token = line_config['token']
        self.user_id = line_config['user_id']
        self.channel_secret = line_config['channel_secret']
        
        # LINE Messaging APIの設定
        configuration = Configuration(
            access_token=self.token
        )
        self.api_client = ApiClient(configuration)
        self.messaging_api = MessagingApi(self.api_client)
        self.handler = WebhookHandler(self.channel_secret)

    def send_message(self, message):
        try:
            request = PushMessageRequest(
                to=self.user_id,
                messages=[TextMessage(text=message)]
            )
            self.messaging_api.push_message(request)
            logger.info("LINE message sent successfully")
        except Exception as e:
            logger.error(f"Error sending LINE message: {e}")
