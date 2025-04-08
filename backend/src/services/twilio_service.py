from utils.logger import setup_logger
from twilio.rest import Client
from utils.config_manager import ConfigManager

logger = setup_logger(__name__)

class TwilioService:
    def __init__(self, config_manager: ConfigManager):
        self.enabled = config_manager.get('twilio.enabled', False)
        if self.enabled:
            account_sid = config_manager.get('twilio.account_sid')
            auth_token = config_manager.get('twilio.auth_token')
            self.from_number = config_manager.get('twilio.from_number')
            self.to_number = config_manager.get('twilio.to_number')

            if not account_sid or not auth_token:
                 logger.error("Twilio account SID or Auth Token not found in config. Disabling Twilio.")
                 self.enabled = False
                 self.client = None
                 return

            try:
                self.client = Client(account_sid, auth_token)
                logger.info("Twilio client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.enabled = False
                self.client = None
        else:
             logger.info("Twilio service is disabled in config.")
             self.client = None

    def send_sms(self, message):
        if not self.enabled or not self.client:
            logger.warning("Twilio is disabled or not initialized. Cannot send SMS.")
            return
        if not self.from_number or not self.to_number:
             logger.error("Twilio 'from' or 'to' number not configured. Cannot send SMS.")
             return

        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            logger.info(f"SMS sent successfully. SID: {msg.sid}")
        except Exception as e:
            logger.error(f"Error sending SMS via Twilio: {e}")
