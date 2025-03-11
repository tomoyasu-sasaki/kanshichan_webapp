from twilio.rest import Client
from backend.src.utils.logger import setup_logger

logger = setup_logger(__name__)

class TwilioService:
    def __init__(self, config):
        self.enabled = 'twilio' in config
        if self.enabled:
            twilio_config = config['twilio']
            self.client = Client(
                twilio_config['account_sid'],
                twilio_config['auth_token']
            )
            self.from_number = twilio_config['from_number']
            self.to_number = twilio_config['to_number']

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
