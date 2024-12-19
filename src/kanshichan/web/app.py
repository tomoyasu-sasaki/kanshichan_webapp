from flask import Flask
from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import (
	MessageEvent, TextMessageContent
)
from src.kanshichan.core.monitor import Monitor
from src.kanshichan.services.alert_service import AlertService
from src.kanshichan.web.handlers import setup_handlers
from src.kanshichan.utils.logger import setup_logger
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, ReplyMessageRequest, TextMessage

logger = setup_logger(__name__)

# メッセージと音声ファイルのマッピング
message_sound_mapping = {
	"お風呂入ってくる": {"sound": "Copythat.wav", "extension": 1200},
	"買い物行ってくる": {"sound": "Copythat.wav", "extension": 1200},
	"料理しなきゃ": {"sound": "Copythat.wav", "extension": 1200},
	"散歩してくる": {"sound": "Copythat.wav", "extension": 1200},
	"うんこ": {"sound": "Copythat.wav", "extension": 600},
	"とりあえず離席": {"Copythat": "Copythat.wav", "extension": 600},
}

def create_app(config):
    app = Flask(__name__)

    # Monitorインスタンスを初期化
    monitor = Monitor(config)
    
    # LINE Handlerの初期化
    line_handler = WebhookHandler(config['line']['channel_secret'])
    configuration = Configuration(access_token=config['line']['token'])
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
    
    # メッセージハンドラーの設定
    @line_handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        try:
            text = event.message.text
            if text in message_sound_mapping:
                sound_file = message_sound_mapping[text]["sound"]
                extension_time = message_sound_mapping[text]["extension"]
                
                # 音声メッセージを再生
                alert_service = AlertService(config)
                alert_service.trigger_alert(text, sound_file)
                
                # absenceのthreshold_secondsを延長
                monitor.extend_absence_threshold(extension_time)

                # reply_text = f"受信しました: {text}"
                # line_bot_api.reply_message(
                #     ReplyMessageRequest(
                #         reply_token=event.reply_token,
                #         messages=[TextMessage(text=reply_text)]
                #     )
                # )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    # configにline_handlerを追加
    config['line_handler'] = line_handler
    
    app.config.from_mapping(config)
    setup_handlers(app, config)
    
    return app
