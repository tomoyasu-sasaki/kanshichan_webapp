import os
import yaml
import logging
from linebot.v3.messaging import (
    Configuration,
    MessagingApi,
    ApiClient,
    PushMessageRequest,
    ApiException,
)
BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)
# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# LINE Messaging APIの設定     # 送信先のチャンネルID（ユーザーID）
LINE_ACCESS_TOKEN = config['line']['token']
LINE_CHANNEL_ID = config['line']['channel_id']
# Configurationの設定
configuration = Configuration(access_token=LINE_ACCESS_TOKEN)

def send_test_message():
    """LINEへテストメッセージを送信する。"""
    message_dict = {
        'to': LINE_CHANNEL_ID,
        'messages': [
            {'type': 'text', 'text': 'これはテストメッセージです！'}
        ],
    }

    # LINE Messaging APIのクライアントを作成
    with ApiClient(configuration) as api_client:
        api_instance = MessagingApi(api_client)

        try:
            # メッセージを送信
            response = api_instance.push_message_with_http_info(
                PushMessageRequest(message_dict)
            )
            logger.info(f"Message sent successfully! Status code: {response[1]}")
        except ApiException as e:
            logger.error(f"Error sending message: {e}")

if __name__ == "__main__":
    send_test_message()