from twilio.rest import Client
from src.kanshichan.utils.logger import setup_logger

logger = setup_logger(__name__)

class TwilioService:
    def __init__(self, config):
        twilio_config = config['twilio']
        self.account_sid = twilio_config['account_sid']
        self.auth_token = twilio_config['auth_token']
        self.to_number = twilio_config['to_number']
        self.from_number = twilio_config['from_number']
        self.client = Client(self.account_sid, self.auth_token)

    def send_sms(self, message):
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            logger.info(f"SMS sent successfully. SID: {msg.sid}")
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
