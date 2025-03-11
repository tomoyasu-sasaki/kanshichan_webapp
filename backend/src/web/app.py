from flask import Flask, send_from_directory
from flask_cors import CORS
from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import (
	MessageEvent, TextMessageContent
)
from backend.src.core.monitor import Monitor
from backend.src.services.alert_service import AlertService
from backend.src.web.handlers import setup_handlers
from backend.src.web.api import api
from backend.src.web.websocket import init_websocket, socketio
from backend.src.utils.logger import setup_logger
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, ReplyMessageRequest, TextMessage
from backend.src.config.message_settings import message_sound_mapping

logger = setup_logger(__name__)

def create_app(config):
    app = Flask(__name__, static_folder='../../frontend/dist')
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/socket.io/*": {"origins": "*"}
    })

    # APIエンドポイントの登録
    app.register_blueprint(api, url_prefix='/api')
    
    # WebSocketの初期化
    init_websocket(app)
    
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
                monitor = Monitor.get_instance()
                if monitor:
                    monitor.extend_absence_threshold(extension_time)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    # configにline_handlerを追加
    config['line_handler'] = line_handler
    
    # SPAのルーティング
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path and path.startswith('api/'):
            return app.send_static_file('index.html')
        return send_from_directory(app.static_folder, path or 'index.html')
    
    setup_handlers(app, config)
    
    return app
