"""
Flask Web Application

KanshiChan Webアプリケーションのメインエントリーポイント
"""

import os
import sys
from pathlib import Path

# tqdmの進捗バー表示を全体的に無効化
os.environ['TQDM_DISABLE'] = '1'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'

import tqdm
tqdm.tqdm.disable = True

from flask import Flask, request, jsonify, send_from_directory, current_app
from flask_cors import CORS
from flask_socketio import SocketIO
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from web.handlers import setup_handlers
from web.api import api
from web.routes import (
    basic_analysis_bp, advanced_analysis_bp, prediction_analysis_bp, realtime_analysis_bp,
    tts_synthesis_bp, tts_voice_clone_bp, tts_file_bp, tts_emotion_bp, 
    tts_streaming_bp, tts_system_bp, init_tts_services,
    behavior_bp, monitor_bp
)
from web.routes.monitor_routes import init_monitor_service
from web.websocket import init_websocket, socketio, init_audio_streaming
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
    """
    Flaskアプリケーションを作成し、設定を適用します。
    
    Args:
        config_manager: 初期化済みのConfigManagerインスタンス。
            必須パラメーターであり、未指定または未初期化の場合はエラーとなります。
    
    Returns:
        tuple: (Flask app, SocketIO instance)
        
    Raises:
        ConfigError: ConfigManagerが正しく初期化されていない場合
    """
    # ConfigManagerの検証
    if not config_manager:
        error_msg = "create_appにConfigManagerが指定されていません"
        logger.critical(error_msg)
        raise ConfigError(error_msg)
        
    app = Flask(__name__, static_folder='../../../frontend/dist')
    
    # ConfigManagerをFlaskアプリケーションに注入
    app.config['config_manager'] = config_manager
    
    # データベース設定 - 絶対パスに修正
    # src/instance/kanshichan.dbへの絶対パス
    db_path = Path(__file__).parent.parent / 'instance' / 'kanshichan.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path.absolute()}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CORS設定
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/socket.io/*": {"origins": "*"}
    })
    
    # 設定を取得
    config = config_manager.get_all()
    
    # WebSocket初期化
    try:
        init_websocket(app)
    except Exception as e:
        logger.error(f"❌ Failed to initialize WebSocket: {e}")
    
    try:
        init_audio_streaming()
    except Exception as e:
        logger.error(f"❌ Failed to initialize audio streaming system: {e}")
        # 音声配信システムの初期化失敗は致命的ではないため継続
    
    # TTS サービス初期化
    try:
        init_tts_services(config)
    except Exception as e:
        tts_init_error = wrap_exception(
            e, InitializationError,
            "Failed to initialize TTS services",
            details={'config_keys': list(config.keys())}
        )
        logger.error(f"❌ TTS services initialization error: {tts_init_error.to_dict()}")
        # TTSサービスの初期化失敗は致命的ではないため継続
    
    # Monitor サービス初期化
    try:
        init_monitor_service(config)
    except Exception as e:
        monitor_init_error = wrap_exception(
            e, InitializationError,
            "Failed to initialize Monitor services",
            details={'config_keys': list(config.keys())}
        )
        logger.error(f"❌ Monitor services initialization error: {monitor_init_error.to_dict()}")
        # Monitorサービスの初期化失敗は致命的ではないため継続
    
    # API Blueprint登録
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(basic_analysis_bp)
    app.register_blueprint(advanced_analysis_bp)
    app.register_blueprint(prediction_analysis_bp)
    app.register_blueprint(realtime_analysis_bp)
    app.register_blueprint(tts_synthesis_bp)
    app.register_blueprint(tts_voice_clone_bp)
    app.register_blueprint(tts_file_bp)
    app.register_blueprint(tts_emotion_bp)
    app.register_blueprint(tts_streaming_bp)
    app.register_blueprint(tts_system_bp)
    app.register_blueprint(behavior_bp)
    app.register_blueprint(monitor_bp)
    
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
            logger.info("✅ LINE Bot handler initialized successfully.")
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
            logger.error(f"❌ LINE Bot initialization error: {line_init_error.to_dict()}")
            line_handler = None
            line_bot_api = None

    # サービスの初期化状況を集約してロギング
    initialized_services = [
        "WebSocket", "Audio Streaming", "TTS", "Monitor", "LINE Bot"
    ]
    total_services = len(initialized_services)
    logger.info(f"🎉 Application started successfully with all {total_services} services initialized")

    # 登録されているルートをDEBUGレベルでログ出力
    logger.debug("=== Registered Routes ===")
    for rule in app.url_map.iter_rules():
        # OPTIONS, HEADは冗長なので除外
        methods = ', '.join(sorted([m for m in rule.methods if m not in ['OPTIONS', 'HEAD']]))
        logger.debug(f"Route: {rule.endpoint} -> {rule.rule} [{methods}]")
    logger.debug("========================")

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
    
    # SPAの404エラーハンドラー（APIパスは除外）
    @app.errorhandler(404)
    def spa_route_handler(error):
        # APIパスの場合は404エラーのまま返す
        if request.path.startswith('/api/'):
            return jsonify({"error": "API endpoint not found"}), 404
            
        # 静的ファイルの場合はそのまま404を返す
        if request.path.startswith('/assets/') or '.' in request.path.split('/')[-1]:
            return jsonify({"error": "File not found"}), 404
            
        # SPAのindex.htmlを返す
        index_path = os.path.join(app.static_folder, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            frontend_error = FileNotFoundError(
                f"Frontend index.html not found at {index_path}",
                details={
                    'index_path': index_path,
                    'static_folder': app.static_folder,
                    'path_requested': request.path
                }
            )
            logger.error(f"Frontend file error: {frontend_error.to_dict()}")
            return jsonify({"error": "Frontend not found"}), 404
    
    # ルートパス用の明示的なルート
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_spa(path):
        # パスがファイル（拡張子を持つ）を指している場合
        if '.' in path.split('/')[-1]:
            # 安全なファイルパスか確認
            safe_path = os.path.normpath(os.path.join(app.static_folder, path))
            if os.path.commonpath([app.static_folder, safe_path]) == app.static_folder:
                 if os.path.exists(safe_path):
                     return send_from_directory(app.static_folder, path)

        # それ以外はindex.htmlを返す（SPAルーティング）
        return send_from_directory(app.static_folder, 'index.html')

    return app, socketio
