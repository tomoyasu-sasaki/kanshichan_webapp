from flask import Flask
from linebot.v3 import WebhookHandler
from linebot.v3.webhook import MessageEvent
from src.kanshichan.web.handlers import setup_handlers
from src.kanshichan.utils.logger import setup_logger
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, ReplyMessageRequest, TextMessage

logger = setup_logger(__name__)

def create_app(config):
    app = Flask(__name__)
    
    # LINE Handlerの初期化
    line_handler = WebhookHandler(config['line']['channel_secret'])
    
    # メッセージハンドラーの設定
    @line_handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        try:
            # メッセージの内容に応じた処理
            text = event.message.text
            reply_text = f"受信しました: {text}"
            
            # 返信
            configuration = Configuration(access_token=config['line']['token'])
            with ApiClient(configuration) as api_client:
                messaging_api = MessagingApi(api_client)
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    # configにline_handlerを追加
    config['line_handler'] = line_handler
    
    app.config.from_mapping(config)
    setup_handlers(app, config)
    
    return app
