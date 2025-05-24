from flask_socketio import SocketIO, emit
from utils.logger import setup_logger
from utils.exceptions import (
    NetworkError, InitializationError, wrap_exception
)

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
        broadcast_error = wrap_exception(
            e, NetworkError,
            "Error broadcasting status update via WebSocket",
            details={
                'status': status,
                'socketio_initialized': socketio is not None
            }
        )
        logger.error(f"WebSocket broadcast error: {broadcast_error.to_dict()}") 