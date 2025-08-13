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
from flask_wtf.csrf import CSRFError
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
    # TTS 関連は大量のバイナリ POST を行うため CSRF を除外
    csrf.exempt(api)                    # /api/* 全体
    csrf.exempt(tts_file_bp)            # /api/tts/file/*
    csrf.exempt(tts_synthesis_bp)       # /api/tts/synthesize* すべて
    # 音声設定などTTSシステム管理系はフォーム送信ではなくJSON APIのためCSRFを除外
    csrf.exempt(tts_system_bp)         # /api/tts/* システム管理API
    # 解析系APIはJSONのみのためCSRFを除外
    csrf.exempt(basic_analysis_bp)
    csrf.exempt(advanced_analysis_bp)
    csrf.exempt(prediction_analysis_bp)
    csrf.exempt(realtime_analysis_bp)
    # スケジュール管理APIを除外（/api/schedules*）
    for ep in [
        'api.add_schedule',
        'api.get_schedules',
        'api.delete_schedule',
        'tts_synthesis.synthesize_speech',
        'tts_synthesis.synthesize_speech_fast',
        'tts_synthesis.synthesize_advanced_speech'
    ]:
        csrf.exempt(ep)
    
    # 開発時の利便性向上: レート制限を一括無効化（環境変数またはENVに応じて）
    disable_rl_by_env = (
        os.environ.get('KANSHICHAN_DISABLE_RATELIMITS', '0') == '1'
        or os.environ.get('FLASK_ENV') == 'development'
        or os.environ.get('ENV') == 'development'
        or app.config.get('ENV') == 'development'
    )

    # セキュリティ強化: レート制限の設定（開発環境では無効化可能）
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[] if disable_rl_by_env else ["200 per day", "50 per hour"],
        strategy="fixed-window",
        storage_uri="memory://",
    )
    if disable_rl_by_env:
        @limiter.request_filter
        def _disable_rate_limiting_for_dev():
            return True
        logger.warning("Rate limiting is disabled for development environment")
    
    # 特定エンドポイントのレート制限除外: TTS ステータス
    @limiter.request_filter
    def _exempt_tts_status_endpoint():
        try:
            path = request.path or ""
            # 正式版（/api/v1/tts/status）と万一の後方互換（/api/tts/status）を除外
            return path.endswith('/api/v1/tts/status') or path.endswith('/api/tts/status')
        except Exception:
            return False
    
    # ConfigManagerをFlaskアプリケーションに注入
    app.config['config_manager'] = config_manager
    
    # データベース設定 - 絶対パスに修正
    # backend/instance/kanshichan.db, backend/instance/config.db の絶対パス
    db_path = Path(__file__).parent.parent.parent / 'instance' / 'kanshichan.db'
    config_db_path = Path(__file__).parent.parent.parent / 'instance' / 'config.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path.absolute()}'
    app.config['SQLALCHEMY_BINDS'] = {
        'config': f'sqlite:///{config_db_path.absolute()}'
    }
    logger.info(f"Configured SQLALCHEMY_BINDS['config'] -> {config_db_path.absolute()}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CORS設定
    # 環境変数からCORS許可オリジンを取得
    cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '*')
    # カンマ区切りの文字列を配列に変換（'*'の場合はそのまま）
    origins = [origin.strip() for origin in cors_origins.split(',')] if cors_origins != '*' else '*'
    
    CORS(app, resources={
        r"/api/*": {"origins": origins},
        r"/api/v1/*": {"origins": origins},
        r"/socket.io/*": {"origins": origins}
    })
    
    # 設定を取得
    config = config_manager.get_all()
    
    # ---- テスト用の軽量化フラグ ----
    TEST_MODE_DISABLE_TTS = os.environ.get('KANSHICHAN_ENABLE_TTS', '1') == '0'
    TEST_MODE_DISABLE_AUDIO = os.environ.get('KANSHICHAN_ENABLE_AUDIO', '1') == '0'
    TEST_MODE_DISABLE_METRICS = os.environ.get('KANSHICHAN_ENABLE_METRICS', '1') == '0'

    # WebSocket初期化
    try:
        init_websocket(app)
    except Exception as e:
        logger.error(f"❌ Failed to initialize WebSocket: {e}")
    
    # Audio Streaming
    if not TEST_MODE_DISABLE_AUDIO:
        try:
            init_audio_streaming()
        except Exception as e:
            logger.error(f"❌ Failed to initialize audio streaming system: {e}")

    try:
        if not TEST_MODE_DISABLE_METRICS:
            init_system_metrics_broadcast()
    except Exception as e:
        logger.error(f"❌ Failed to initialize system metrics broadcast: {e}")
    
    # TTS サービス初期化
    if not TEST_MODE_DISABLE_TTS:
        try:
            init_tts_services(config)
        except Exception as e:
            tts_init_error = wrap_exception(
                e, InitializationError,
                "Failed to initialize TTS services",
                details={'config_keys': list(config.keys())}
            )
            logger.error(f"❌ TTS services initialization error: {tts_init_error.to_dict()}")
    
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
    
    # API Blueprint登録（/api/v1 を正とし、/api は非推奨互換ルートに変更）
    # 正式ルート（/api/v1 配下）
    app.register_blueprint(api, url_prefix='/api/v1')
    app.register_blueprint(basic_analysis_bp, url_prefix='/api/v1/analysis')
    app.register_blueprint(advanced_analysis_bp, url_prefix='/api/v1/analysis')
    app.register_blueprint(prediction_analysis_bp, url_prefix='/api/v1/analysis')
    app.register_blueprint(realtime_analysis_bp, url_prefix='/api/v1/analysis')
    app.register_blueprint(tts_synthesis_bp, url_prefix='/api/v1/tts')
    app.register_blueprint(tts_voice_clone_bp, url_prefix='/api/v1/tts')
    app.register_blueprint(tts_file_bp, url_prefix='/api/v1/tts')
    app.register_blueprint(tts_emotion_bp, url_prefix='/api/v1/tts')
    app.register_blueprint(tts_streaming_bp, url_prefix='/api/v1/tts')
    app.register_blueprint(tts_system_bp, url_prefix='/api/v1/tts')
    app.register_blueprint(behavior_bp, url_prefix='/api/v1/behavior')
    app.register_blueprint(monitor_bp, url_prefix='/api/v1/monitor')
    from web.routes import settings_bp
    # 設定系はJSON APIのみのためCSRF除外
    csrf.exempt(settings_bp)
    # 正式ルートで提供（末尾スラッシュ有り/無しの両方を許容するためFlaskに任せる）
    app.register_blueprint(settings_bp, url_prefix='/api/v1/settings')

    # 後方互換ルート（/api 配下）はDeprecatedヘッダを付与して /api/v1 に誘導
    @app.after_request
    def add_deprecation_header(response):
        try:
            if request.path.startswith('/api/') and not request.path.startswith('/api/v1/'):
                response.headers['Deprecation'] = 'true'
                response.headers['Sunset'] = 'Mon, 01 Dec 2025 00:00:00 GMT'
                response.headers['Link'] = '</api/v1>; rel="successor-version"'
        finally:
            return response
    
    # レート制限の適用（開発環境ではスキップ）
    if not disable_rl_by_env:
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
            from web.response_utils import error_response
            return error_response('API endpoint not found', code='NOT_FOUND', status_code=404)
            
        # 静的ファイルの場合はそのまま404を返す
        if request.path.startswith('/assets/') or '.' in request.path.split('/')[-1]:
            from web.response_utils import error_response
            return error_response('File not found', code='NOT_FOUND', status_code=404)
            
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
            from web.response_utils import error_response
            return error_response('Frontend not found', code='NOT_FOUND', status_code=404)
            
    # CSRFエラーハンドラ
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from web.response_utils import error_response
        return error_response(
            'CSRF token validation failed',
            code='CSRF_ERROR',
            details={'csrf': 'Invalid or missing CSRF token'},
            status_code=400,
        )
    
    # レート制限エラーハンドラ
    @app.errorhandler(429)
    def handle_ratelimit_error(e):
        from web.response_utils import error_response
        return error_response(
            'Rate limit exceeded',
            code='RATE_LIMIT_ERROR',
            details={'message': str(e.description)},
            status_code=429,
        )
    
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
