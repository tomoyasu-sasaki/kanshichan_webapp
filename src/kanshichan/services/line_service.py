from linebot.v3 import WebhookHandler
from linebot.v3.messaging import TextMessage, PushMessageRequest
from src.kanshichan.utils.logger import setup_logger

logger = setup_logger(__name__)

class LineService:
    def __init__(self, config):
        line_config = config['line']
        self.token = line_config['token']
        self.user_id = line_config['user_id']
        self.channel_secret = line_config['channel_secret']
        self.handler = WebhookHandler(self.channel_secret)
        self.bot_api = WebhookHandler(self.token)

    def send_message(self, message):
        try:
            self.bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=self.user_id,
                    messages=[TextMessage(text=message)]
                )
            )
            logger.info("LINE message sent successfully")
        except Exception as e:
            logger.error(f"Error sending LINE message: {e}")
