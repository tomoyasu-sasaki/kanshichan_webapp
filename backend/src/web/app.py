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
from utils.exceptions import (
    InitializationError, LineAPIError, ConfigError, AudioError,
    FileNotFoundError, wrap_exception
)
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
            line_init_error = wrap_exception(
                e, LineAPIError,
                "Failed to initialize LINE Bot handler",
                details={
                    'channel_secret_configured': bool(channel_secret and channel_secret != 'YOUR_CHANNEL_SECRET'),
                    'access_token_configured': bool(access_token and access_token != 'YOUR_LINE_TOKEN'),
                    'line_enabled': line_enabled
                }
            )
            logger.error(f"LINE Bot initialization error: {line_init_error.to_dict()}")
            line_handler = None
            line_bot_api = None

    # メッセージハンドラーの設定
    if line_handler:
        @line_handler.add(MessageEvent, message=TextMessageContent)
        def handle_message(event):
            try:
                text = event.message.text
                logger.info(f"LINEからメッセージを受信: '{text}'")
                
                # ConfigManagerからメッセージマッピングを取得
                message_sound_mapping = config_manager.get_message_sound_mapping()
                logger.info(f"現在のメッセージマッピング: {message_sound_mapping}")
                
                if text in message_sound_mapping:
                    logger.info(f"メッセージ '{text}' はマッピングに存在します")
                    extension_time = message_sound_mapping[text].get("extension")
                    logger.info(f"マッピングされた延長時間: {extension_time}")
                    
                    # 音声ファイルの取得と再生を追加
                    sound_file = message_sound_mapping[text].get("sound")
                    logger.info(f"マッピングされた音声ファイル: {sound_file}")
                    
                    # 音声再生用のSoundServiceを取得
                    monitor = current_app.config.get('monitor_instance')
                    
                    if monitor and sound_file:
                        try:
                            # モニターからSoundServiceを取得して音声再生
                            sound_service = monitor.alert_manager.alert_service.sound_service
                            logger.info(f"音声ファイル '{sound_file}' を再生します")
                            sound_service.play_alert(sound_file)
                        except Exception as e:
                            audio_error = wrap_exception(
                                e, AudioError,
                                f"音声再生中にエラーが発生: {sound_file}",
                                details={
                                    'sound_file': sound_file,
                                    'sound_service_available': hasattr(monitor, 'alert_manager') and hasattr(monitor.alert_manager, 'alert_service') and hasattr(monitor.alert_manager.alert_service, 'sound_service')
                                }
                            )
                            logger.error(f"Sound playback error: {audio_error.to_dict()}")
                    
                    # 閾値延長処理（既存の処理）
                    if extension_time is not None:
                        monitor = current_app.config.get('monitor_instance')
                        logger.info(f"Monitor取得結果: {monitor is not None}")
                        if monitor:
                            logger.info(f"Received LINE message '{text}', extending absence threshold by {extension_time}s.")
                            # 念のため現在の閾値をログに記録
                            logger.info(f"現在の離席閾値: {monitor.state.absence_threshold}秒")
                            monitor.extend_absence_threshold(extension_time)
                            # 延長後の閾値をログに記録
                            logger.info(f"延長後の離席閾値: {monitor.state.absence_threshold}秒")
                        else:
                            logger.warning("Monitor instance not found in app config. Cannot extend threshold.")
                    else:
                         logger.warning(f"Extension time not found for message '{text}' in message_sound_mapping.")
                else:
                    logger.info(f"メッセージ '{text}' はマッピングに存在しません")

            except Exception as e:
                message_error = wrap_exception(
                    e, LineAPIError,
                    "Error handling LINE message",
                    details={
                        'text': text if 'text' in locals() else None,
                        'handler_available': line_handler is not None,
                        'monitor_available': current_app.config.get('monitor_instance') is not None
                    }
                )
                logger.error(f"LINE message handling error: {message_error.to_dict()}")
    
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
                 frontend_error = FileNotFoundError(
                     f"Frontend index.html not found at {index_path}",
                     details={
                         'index_path': index_path,
                         'static_folder': app.static_folder,
                         'path_requested': path
                     }
                 )
                 logger.error(f"Frontend file error: {frontend_error.to_dict()}")
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
