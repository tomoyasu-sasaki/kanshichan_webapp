from flask import Flask, request, jsonify, send_from_directory, current_app
from flask_cors import CORS
from flask_socketio import SocketIO
from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import (
	MessageEvent, TextMessageContent
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from web.handlers import setup_handlers
from web.api import api
from web.websocket import init_websocket, socketio
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
# 古いインポートを削除
# from config.message_settings import message_sound_mapping
import os

logger = setup_logger(__name__)

def create_app(config_manager: ConfigManager):
    app = Flask(__name__, static_folder='../../../frontend/dist')
    CORS(app)

    # APIエンドポイントの登録
    app.register_blueprint(api, url_prefix='/api')
    
    # WebSocketの初期化
    init_websocket(app)
    
    # LINE Handlerの初期化
    channel_secret = config_manager.get('line.channel_secret')
    access_token = config_manager.get('line.token')
    line_enabled = config_manager.get('line.enabled', False)

    if not line_enabled or not channel_secret or not access_token:
        logger.warning("LINE Bot is disabled or Channel Secret/Access Token is not configured. LINE Bot functionalities will be disabled.")
        line_handler = None
        line_bot_api = None
    else:
        try:
            line_handler = WebhookHandler(channel_secret)
            configuration = Configuration(access_token=access_token)
            api_client = ApiClient(configuration)
            line_bot_api = MessagingApi(api_client)
            logger.info("LINE Bot handler initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize LINE Bot handler: {e}")
            line_handler = None
            line_bot_api = None

    # メッセージハンドラーの設定
    if line_handler:
        @line_handler.add(MessageEvent, message=TextMessageContent)
        def handle_message(event):
            try:
                text = event.message.text
                # ConfigManagerからメッセージマッピングを取得
                message_sound_mapping = config_manager.get_message_sound_mapping()
                
                if text in message_sound_mapping:
                    extension_time = message_sound_mapping[text].get("extension")

                    if extension_time is not None:
                        monitor = current_app.config.get('monitor_instance')
                        if monitor:
                            logger.info(f"Received LINE message '{text}', extending absence threshold by {extension_time}s.")
                            monitor.extend_absence_threshold(extension_time)
                        else:
                            logger.warning("Monitor instance not found in app config. Cannot extend threshold.")
                    else:
                         logger.warning(f"Extension time not found for message '{text}' in message_sound_mapping.")

            except Exception as e:
                logger.error(f"Error handling LINE message: {e}", exc_info=True)
    
    # SPAのルーティング
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            index_path = os.path.join(app.static_folder, 'index.html')
            if os.path.exists(index_path):
                 return send_from_directory(app.static_folder, 'index.html')
            else:
                 logger.error(f"Frontend index.html not found at {index_path}")
                 return jsonify({"error": "Frontend not found"}), 404
    
    # setup_handlers(app, ...)
    # setup_handlers(app, config_manager.get_all())
    # setup_handlers(app, config_manager)
    # setup_handlers(app, line_handler)
    # setup_handlers(app, ...)
    # setup_handlers(app, ...)
    
    # LINE Bot ハンドラーのセットアップ
    setup_handlers(app, line_handler)
    
    return app
