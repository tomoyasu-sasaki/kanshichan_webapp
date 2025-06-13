"""
Flask Web Application

KanshiChan Webアプリケーションのメインエントリーポイント
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# tqdmの進捗バー表示を全体的に無効化
os.environ['TQDM_DISABLE'] = '1'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'

import tqdm
tqdm.tqdm.disable = True

from flask import Flask, request, jsonify, send_from_directory, current_app
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from web.api import api
from web.routes import (
    basic_analysis_bp, advanced_analysis_bp, prediction_analysis_bp, realtime_analysis_bp,
    tts_synthesis_bp, tts_voice_clone_bp, tts_file_bp, tts_emotion_bp, 
    tts_streaming_bp, tts_system_bp, init_tts_services,
    behavior_bp, monitor_bp
)
from web.routes.monitor_routes import init_monitor_service
from web.websocket import (
    init_websocket, socketio, init_audio_streaming, init_system_metrics_broadcast
)
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    InitializationError, ConfigError, AudioError,
    FileNotFoundError, wrap_exception
)
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
    
    # セキュリティ強化: シークレットキーの設定
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    
    # セキュリティ強化: CSRF保護を有効化
    csrf = CSRFProtect(app)
    # WebSocketとファイルアップロード向けにCSRF保護を除外するルート
    csrf.exempt('web.routes.tts_file_bp.upload_file')
    
    # セキュリティ強化: レート制限の設定
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        strategy="fixed-window",
        storage_uri="memory://",
    )
    
    # ConfigManagerをFlaskアプリケーションに注入
    app.config['config_manager'] = config_manager
    
    # データベース設定 - 絶対パスに修正
    # src/instance/kanshichan.dbへの絶対パス
    db_path = Path(__file__).parent.parent / 'instance' / 'kanshichan.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path.absolute()}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CORS設定
    # 環境変数からCORS許可オリジンを取得
    cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '*')
    # カンマ区切りの文字列を配列に変換（'*'の場合はそのまま）
    origins = [origin.strip() for origin in cors_origins.split(',')] if cors_origins != '*' else '*'
    
    CORS(app, resources={
        r"/api/*": {"origins": origins},
        r"/socket.io/*": {"origins": origins}
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
        
    try:
        init_system_metrics_broadcast()
    except Exception as e:
        logger.error(f"❌ Failed to initialize system metrics broadcast: {e}")
        # システムメトリクス配信の初期化失敗は致命的ではないため継続
    
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
    
    # レート制限の適用
    # 主要なAPIエンドポイントに対するレート制限の設定
    limiter.limit("100 per minute")(monitor_bp)
    limiter.limit("100 per minute")(api)
    limiter.limit("100 per minute")(basic_analysis_bp)
    limiter.limit("60 per minute")(advanced_analysis_bp)
    limiter.limit("30 per minute")(tts_synthesis_bp)
    
    # サービスの初期化状況を集約してロギング
    initialized_services = [
        "WebSocket", "Audio Streaming", "System Metrics Broadcast", "TTS", "Monitor"
    ]
    total_services = len(initialized_services)
    logger.info(f"🎉 Application started successfully with all {total_services} services initialized")

    # 登録されているルートをDEBUGレベルでロギング
    logger.debug("=== Registered Routes ===")
    for rule in app.url_map.iter_rules():
        # OPTIONS, HEADは冗長なので除外
        methods = ', '.join(sorted([m for m in rule.methods if m not in ['OPTIONS', 'HEAD']]))
        logger.debug(f"Route: {rule.endpoint} -> {rule.rule} [{methods}]")
    logger.debug("========================")

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
            
    # CSRFエラーハンドラ
    @app.errorhandler(CSRFProtect.error_handler)
    def handle_csrf_error(e):
        return jsonify({
            'status': 'error',
            'error': 'CSRF token validation failed',
            'code': 'CSRF_ERROR',
            'details': {'csrf': 'Invalid or missing CSRF token'},
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    # レート制限エラーハンドラ
    @app.errorhandler(429)
    def handle_ratelimit_error(e):
        return jsonify({
            'status': 'error',
            'error': 'Rate limit exceeded',
            'code': 'RATE_LIMIT_ERROR',
            'details': {'message': str(e.description)},
            'timestamp': datetime.utcnow().isoformat()
        }), 429
    
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
