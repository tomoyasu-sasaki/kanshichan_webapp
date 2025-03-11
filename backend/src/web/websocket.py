from flask_socketio import SocketIO
from backend.src.utils.logger import setup_logger

logger = setup_logger(__name__)
socketio = SocketIO()

def init_websocket(app):
    """WebSocketの初期化"""
    socketio.init_app(app, cors_allowed_origins="*")

    @socketio.on('connect')
    def handle_connect():
        logger.info('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info('Client disconnected')

def broadcast_status(status):
    """検出状態の変更をブロードキャスト"""
    try:
        socketio.emit('status_update', status)
    except Exception as e:
        logger.error(f"Error broadcasting status: {e}") 