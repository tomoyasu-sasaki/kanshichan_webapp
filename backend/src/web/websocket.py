from flask_socketio import SocketIO, emit
from flask import request
from utils.logger import setup_logger
from utils.exceptions import (
    NetworkError, InitializationError, AudioError, wrap_exception
)
import base64
import threading
import queue
import time
import psutil
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
from datetime import datetime

logger = setup_logger(__name__)
socketio = SocketIO()

# 音声配信用のキューとスレッド管理
audio_queue = queue.Queue()
connected_clients: List[str] = []  # 接続中のクライアントID管理

# システムメトリクス配信用の設定
metrics_broadcast_interval = 5.0  # 5秒ごとに配信
metrics_broadcast_enabled = True  # 配信有効フラグ

def init_websocket(app):
    """WebSocketの初期化"""
    socketio.init_app(app, cors_allowed_origins="*")

    @socketio.on('connect')
    def handle_connect():
        client_id = request.sid
        connected_clients.append(client_id)
        logger.info(f'Client connected: {client_id}')

    @socketio.on('disconnect')
    def handle_disconnect():
        client_id = request.sid
        if client_id in connected_clients:
            connected_clients.remove(client_id)
        logger.info(f'Client disconnected: {client_id}')
    
    @socketio.on('audio_playback_status')
    def handle_audio_status(data):
        """クライアントからの音声再生状態を受信"""
        client_id = request.sid
        status = data.get('status')  # 'playing', 'finished', 'error'
        audio_id = data.get('audio_id')
        
        logger.info(f"Audio playback status from {client_id}: {status} for audio {audio_id}")
        
        # 他のクライアントに再生状態を通知（必要に応じて）
        socketio.emit('audio_status_update', {
            'client_id': client_id,
            'audio_id': audio_id,
            'status': status
        }, room=None, include_self=False)
        
    @socketio.on('toggle_metrics_broadcast')
    def handle_toggle_metrics(data):
        """システムメトリクス配信の有効/無効を切り替え"""
        global metrics_broadcast_enabled
        enabled = data.get('enabled', True)
        interval = data.get('interval', 5.0)
        
        # 値の範囲チェック
        if interval < 1.0:
            interval = 1.0  # 最小1秒
        elif interval > 60.0:
            interval = 60.0  # 最大60秒
            
        metrics_broadcast_enabled = enabled
        global metrics_broadcast_interval
        metrics_broadcast_interval = interval
        
        logger.info(f"System metrics broadcast {'enabled' if enabled else 'disabled'} with interval {interval}s")
        return {'success': True, 'enabled': metrics_broadcast_enabled, 'interval': metrics_broadcast_interval}

def broadcast_status(status):
    """検出状態の変更をブロードキャスト"""
    try:
        # 互換性のためエイリアスイベント名でも二重配信
        socketio.emit('status_update', status)
        socketio.emit('detection_status', status)
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

def broadcast_system_metrics():
    """システムメトリクスを収集してブロードキャスト"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count()
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        
        # メモリ使用率
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent
        memory_used = memory_info.used
        memory_total = memory_info.total
        
        # ディスク使用率
        disk_info = psutil.disk_usage('/')
        disk_percent = disk_info.percent
        disk_used = disk_info.used
        disk_total = disk_info.total
        
        # GPU情報取得（可能な場合）
        gpu_info = {
            'available': False,
            'usage_percent': 0,
            'memory_used': 0,
            'memory_total': 0
        }
        
        system_metrics = {
            'cpu': {
                'usage_percent': cpu_percent,
                'cores': cpu_cores,
                'per_core_usage': cpu_per_core
            },
            'memory': {
                'usage_percent': memory_percent,
                'used_bytes': memory_used,
                'total_bytes': memory_total,
                'used_gb': round(memory_used / (1024 ** 3), 2),
                'total_gb': round(memory_total / (1024 ** 3), 2)
            },
            'disk': {
                'usage_percent': disk_percent,
                'used_bytes': disk_used,
                'total_bytes': disk_total,
                'used_gb': round(disk_used / (1024 ** 3), 2),
                'total_gb': round(disk_total / (1024 ** 3), 2)
            },
            'gpu': gpu_info,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # WebSocketで配信（互換エイリアス含む）
        socketio.emit('system_metrics', system_metrics)
        socketio.emit('performance_stats', system_metrics)
        
    except Exception as e:
        metrics_error = wrap_exception(
            e, NetworkError,
            "Error broadcasting system metrics via WebSocket",
            details={'socketio_initialized': socketio is not None}
        )
        logger.error(f"System metrics broadcast error: {metrics_error.to_dict()}")

def broadcast_audio_stream(audio_data: bytes, audio_metadata: Dict[str, Any], 
                          target_clients: Optional[List[str]] = None):
    """音声データのストリーミング配信
    
    Args:
        audio_data: 音声バイナリデータ
        audio_metadata: 音声メタデータ（ID、形式、長さ等）
        target_clients: 配信対象クライアントIDリスト（Noneの場合は全クライアント）
    """
    try:
        # 音声データをBase64エンコードして配信
        encoded_audio = base64.b64encode(audio_data).decode('utf-8')
        
        payload = {
            'audio_data': encoded_audio,
            'metadata': audio_metadata,
            'timestamp': audio_metadata.get('timestamp', ''),
            'format': 'audio/wav',
            'encoding': 'base64'
        }
        
        # 配信対象の決定
        if target_clients:
            # 特定クライアントに配信
            for client_id in target_clients:
                if client_id in connected_clients:
                    socketio.emit('audio_stream', payload, room=client_id)
            logger.info(f"Audio streamed to {len(target_clients)} specific clients")
        else:
            # 全クライアントに配信
            socketio.emit('audio_stream', payload)
            logger.info(f"Audio streamed to {len(connected_clients)} connected clients")
            
    except Exception as e:
        audio_stream_error = wrap_exception(
            e, NetworkError,
            "Error broadcasting audio stream via WebSocket",
            details={
                'audio_metadata': audio_metadata,
                'connected_clients_count': len(connected_clients),
                'target_clients': target_clients
            }
        )
        logger.error(f"Audio stream broadcast error: {audio_stream_error.to_dict()}")

def broadcast_audio_notification(notification_type: str, message: str, 
                                audio_id: Optional[str] = None):
    """音声関連通知の配信
    
    Args:
        notification_type: 通知タイプ ('tts_started', 'tts_completed', 'tts_error', 'audio_ready')
        message: 通知メッセージ
        audio_id: 関連する音声ID
    """
    try:
        payload = {
            'type': notification_type,
            'message': message,
            'audio_id': audio_id,
            'timestamp': datetime.now().isoformat()
        }
        
        socketio.emit('audio_notification', payload)
        logger.info(f"Audio notification sent: {notification_type} - {message}")
        
    except Exception as e:
        notification_error = wrap_exception(
            e, NetworkError,
            "Error broadcasting audio notification via WebSocket",
            details={
                'notification_type': notification_type,
                'message': message,
                'audio_id': audio_id
            }
        )
        logger.error(f"Audio notification broadcast error: {notification_error.to_dict()}")

def queue_audio_for_streaming(file_path: str, metadata: Dict[str, Any]):
    """音声ファイルをストリーミングキューに追加
    
    Args:
        file_path: 音声ファイルパス
        metadata: 音声メタデータ
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # 音声ファイルを読み込み
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        file_size = len(audio_data)
        logger.info(f"Queueing audio for streaming: {file_path} ({file_size} bytes)")
        
        # キューに追加
        audio_item = {
            'audio_data': audio_data,
            'metadata': {
                **metadata,
                'file_path': file_path,
                'file_size': file_size,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        audio_queue.put(audio_item)
        
        # 配信開始通知
        broadcast_audio_notification(
            'audio_ready', 
            f"音声ファイルが配信準備完了: {metadata.get('text_content', 'Unknown')[:50]}...",
            metadata.get('audio_id')
        )
        
    except Exception as e:
        queue_error = wrap_exception(
            e, AudioError,
            "Error queueing audio for streaming",
            details={
                'file_path': file_path,
                'metadata': metadata
            }
        )
        logger.error(f"Audio queueing error: {queue_error.to_dict()}")

def start_audio_streaming_worker():
    """音声ストリーミングワーカースレッドを開始"""
    def audio_worker():
        """音声配信ワーカー関数"""
        while True:
            try:
                # キューから音声アイテムを取得（ブロッキング）
                audio_item = audio_queue.get(timeout=1)
                
                if audio_item:
                    broadcast_audio_stream(
                        audio_item['audio_data'],
                        audio_item['metadata']
                    )
                    
                audio_queue.task_done()
                
            except queue.Empty:
                # タイムアウト時は続行
                continue
            except Exception as e:
                worker_error = wrap_exception(
                    e, NetworkError,
                    "Error in audio streaming worker",
                    details={'queue_size': audio_queue.qsize()}
                )
                logger.error(f"Audio worker error: {worker_error.to_dict()}")
    
    # ワーカースレッドを開始
    worker_thread = threading.Thread(target=audio_worker, daemon=True)
    worker_thread.start()
    logger.info("Audio streaming worker thread started")

def start_system_metrics_worker():
    """システムメトリクス配信ワーカースレッドを開始"""
    def metrics_worker():
        """システムメトリクス配信ワーカー関数"""
        while True:
            try:
                if metrics_broadcast_enabled and connected_clients:
                    broadcast_system_metrics()
                
                # 設定された間隔で待機
                time.sleep(metrics_broadcast_interval)
                
            except Exception as e:
                metrics_worker_error = wrap_exception(
                    e, NetworkError,
                    "Error in system metrics worker",
                    details={'connected_clients': len(connected_clients)}
                )
                logger.error(f"System metrics worker error: {metrics_worker_error.to_dict()}")
                time.sleep(5)  # エラー発生時は5秒待機
    
    # ワーカースレッドを開始
    worker_thread = threading.Thread(target=metrics_worker, daemon=True)
    worker_thread.start()
    logger.info("System metrics worker thread started")

def get_connected_clients_count() -> int:
    """接続中のクライアント数を取得"""
    return len(connected_clients)

# 音声配信システムの初期化
def init_audio_streaming():
    """音声配信システムの初期化"""
    try:
        start_audio_streaming_worker()
        logger.info("Audio streaming system initialized successfully")
    except Exception as e:
        init_error = wrap_exception(
            e, InitializationError,
            "Failed to initialize audio streaming system",
            details={}
        )
        logger.error(f"Audio streaming initialization error: {init_error.to_dict()}")
        raise

# システムメトリクス配信システムの初期化
def init_system_metrics_broadcast():
    """システムメトリクス配信システムの初期化"""
    try:
        start_system_metrics_worker()
        logger.info("System metrics broadcast initialized successfully")
    except Exception as e:
        init_error = wrap_exception(
            e, InitializationError,
            "Failed to initialize system metrics broadcast",
            details={}
        )
        logger.error(f"System metrics broadcast initialization error: {init_error.to_dict()}")
        raise 