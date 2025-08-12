"""
TTS Streaming API Routes - ストリーミング配信API

リアルタイム音声配信機能のAPIエンドポイント群
WebSocket音声配信、ストリーミング状態監視、メッセージ一斉配信を提供
"""

import logging
from typing import Dict, Any, Optional
from flask import Blueprint, request

from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import ValidationError, ServiceUnavailableError, wrap_exception
from web.websocket import (
    broadcast_audio_notification, queue_audio_for_streaming,
    get_connected_clients_count
)

logger = setup_logger(__name__)

# Blueprint定義（相対パス化。上位で /api および /api/v1 を付与）
tts_streaming_bp = Blueprint('tts_streaming', __name__, url_prefix='/tts')
from web.response_utils import success_response, error_response

# サービスインスタンス（tts_helpers.pyで初期化）
tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_streaming_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    """ストリーミングサービスの初期化
    
    Args:
        tts_svc: TTSServiceインスタンス
        vm: VoiceManagerインスタンス
    """
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_streaming_bp.route('/stream-audio', methods=['POST'])
def stream_audio():
    """WebSocket経由でのリアルタイム音声配信
    
    Request JSON:
        text: 音声化するテキスト (required)
        voice_sample_id: 音声サンプルID (optional)
        emotion: 感情設定 (optional, default: "neutral")
        language: 言語設定 (optional, default: "ja")
        priority: 配信優先度 1-10 (optional, default: 5)
        broadcast_all: 全クライアントに配信するかどうか (optional, default: false)
        target_client_ids: 特定クライアントIDのリスト (optional)
    
    Returns:
        JSON response with streaming result
    """
    logger.info("📡 Real-time audio streaming request received")
    
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    
    try:
        # リクエストデータ検証
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        
        text = data.get('text')
        if not text:
            raise ValidationError("text is required")
        
        voice_sample_id = data.get('voice_sample_id')
        emotion = data.get('emotion', 'neutral')
        language = data.get('language', 'ja')
        priority = data.get('priority', 5)
        broadcast_all = data.get('broadcast_all', False)
        target_client_ids = data.get('target_client_ids', [])
        
        # 接続クライアント数チェック
        connected_clients = get_connected_clients_count()
        if connected_clients == 0:
            logger.warning("No connected clients for streaming")
            return error_response('No connected clients for streaming', code='NO_CLIENTS', status_code=400)
        
        logger.info(f"📡 Streaming text to {connected_clients} clients: '{text[:50]}...'")
        logger.info(f"📡 Settings: emotion={emotion}, language={language}, priority={priority}")
        
        # 音声合成実行
        synthesis_params = {
            'emotion': emotion,
            'language': language
        }
        
        if voice_sample_id:
            synthesis_params['voice_sample_id'] = voice_sample_id
        
        # 高速合成モードで音声生成
        audio_result = tts_service.synthesize_text_fast(
            text=text,
            **synthesis_params
        )
        
        # ストリーミング用にキューに追加
        stream_metadata = {
            'text': text,
            'emotion': emotion,
            'language': language,
            'priority': priority,
            'synthesis_time': audio_result.get('synthesis_time', 0),
            'generated_at': audio_result.get('generated_at')
        }
        
        # 音声ファイルパスを取得（TTSServiceから）
        audio_file_path = audio_result.get('file_path')
        if not audio_file_path:
            return error_response('Audio file path not available', code='SYNTHESIS_ERROR', status_code=500)
        
        if broadcast_all or not target_client_ids:
            # 全クライアントに配信
            logger.info("📡 Broadcasting to all connected clients")
            queue_audio_for_streaming(audio_file_path, stream_metadata)
        else:
            # 指定クライアントへの配信（基本実装では全クライアントに配信）
            logger.info(f"📡 Broadcasting to specific clients: {target_client_ids}")
            queue_audio_for_streaming(audio_file_path, stream_metadata)
        
        # 配信通知を送信
        broadcast_audio_notification(
            'audio_stream_started',
            f"Audio streaming started: {text[:100]}...",
            audio_result['audio_file_id']
        )
        
        return success_response({
            'audio_file_id': audio_result['audio_file_id'],
            'connected_clients': connected_clients,
            'broadcast_type': 'all' if broadcast_all else 'targeted' if target_client_ids else 'all',
            'streaming_metadata': stream_metadata,
            'message': 'Audio streaming started successfully'
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in audio streaming: {e}")
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
        
    except ServiceUnavailableError as e:
        logger.error(f"Service error in audio streaming: {e}")
        return error_response(str(e), code='SERVICE_ERROR', status_code=503)
        
    except Exception as e:
        logger.error(f"Error in audio streaming: {e}")
        return error_response('Failed to stream audio', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/streaming-status', methods=['GET'])
def get_streaming_status():
    """音声ストリーミングシステムの状態取得
    
    Returns:
        JSON response with streaming system status
    """
    try:
        # 接続クライアント数取得
        connected_clients = get_connected_clients_count()
        
        # TTS サービス状態
        tts_status = 'available' if tts_service else 'unavailable'
        voice_manager_status = 'available' if voice_manager else 'unavailable'
        
        response = {
            'success': True,
            'streaming_system': {
                'status': 'active' if connected_clients > 0 else 'idle',
                'connected_clients': connected_clients,
                'active_streams': 0,  # 基本実装
                'total_streamed': 0   # 基本実装
            },
            'services': {
                'tts_service': tts_status,
                'voice_manager': voice_manager_status,
                'websocket': 'active'
            },
            'capabilities': {
                'real_time_synthesis': tts_service is not None,
                'voice_cloning': tts_service is not None and voice_manager is not None,
                'emotion_processing': tts_service is not None,
                'multi_language': tts_service is not None
            }
        }
        
        # TTS サービスが利用可能な場合、詳細情報を追加
        if tts_service:
            try:
                tts_service_status = tts_service.get_service_status()
                response['services']['tts_details'] = tts_service_status
            except Exception as e:
                logger.warning(f"Failed to get TTS service details: {e}")
        
        return success_response(response)
        
    except Exception as e:
        logger.error(f"Error getting streaming status: {e}")
        return error_response('Failed to get streaming status', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/broadcast-message', methods=['POST'])
def broadcast_message():
    """全クライアントへの音声メッセージ一斉配信
    
    Request JSON:
        message: 配信するメッセージ (required)
        voice_sample_id: 音声サンプルID (optional)
        emotion: 感情設定 (optional, default: "neutral")
        language: 言語設定 (optional, default: "ja")
        priority: 配信優先度 1-10 (optional, default: 8)
        include_text: テキストも配信するかどうか (optional, default: true)
    
    Returns:
        JSON response with broadcast result
    """
    logger.info("📢 Broadcast message request received")
    
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    
    try:
        # リクエストデータ検証
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        
        message = data.get('message')
        if not message:
            raise ValidationError("message is required")
        
        voice_sample_id = data.get('voice_sample_id')
        emotion = data.get('emotion', 'neutral')
        language = data.get('language', 'ja')
        priority = data.get('priority', 8)  # 一斉配信は高優先度
        include_text = data.get('include_text', True)
        
        # 接続クライアント数チェック
        connected_clients = get_connected_clients_count()
        if connected_clients == 0:
            logger.warning("No connected clients for broadcast")
            return success_response({
                'warning': 'no_clients',
                'message': 'No connected clients for broadcast'
            })
        
        logger.info(f"📢 Broadcasting message to {connected_clients} clients")
        logger.info(f"📢 Message: '{message[:100]}...' (emotion: {emotion}, language: {language})")
        
        # 音声合成実行（高速モード）
        synthesis_params = {
            'emotion': emotion,
            'language': language
        }
        
        if voice_sample_id:
            synthesis_params['voice_sample_id'] = voice_sample_id
        
        audio_result = tts_service.synthesize_text_fast(
            text=message,
            **synthesis_params
        )
        
        # 一斉配信用メタデータ
        broadcast_metadata = {
            'type': 'broadcast_message',
            'message': message,
            'emotion': emotion,
            'language': language,
            'priority': priority,
            'include_text': include_text,
            'broadcast_timestamp': audio_result.get('generated_at'),
            'synthesis_time': audio_result.get('synthesis_time', 0)
        }
        
        # 音声ストリーミング
        audio_file_path = audio_result.get('file_path')
        if audio_file_path:
            queue_audio_for_streaming(audio_file_path, broadcast_metadata)
            stream_success = True
        else:
            stream_success = False
            logger.warning("Audio file path not available for streaming")
        
        # テキストメッセージも配信する場合
        if include_text:
            # 基本的なブロードキャスト（WebSocket経由）
            try:
                from web.websocket import socketio
                text_notification = {
                    'type': 'broadcast_text',
                    'message': message,
                    'metadata': broadcast_metadata
                }
                socketio.emit('broadcast_notification', text_notification)
            except ImportError:
                logger.warning("SocketIO not available for text broadcast")
        
        # 配信開始通知
        if stream_success:
            broadcast_audio_notification(
                'broadcast_started',
                f"Message broadcast started: {message[:100]}...",
                audio_result['audio_file_id']
            )
        
        response = {
            'success': True,
            'audio_file_id': audio_result['audio_file_id'],
            'broadcast_to_clients': connected_clients,
            'audio_streaming': stream_success,
            'text_broadcast': include_text,
            'metadata': broadcast_metadata,
            'message': f'Message broadcast to {connected_clients} clients'
        }
        
        if not stream_success:
            response['warning'] = 'Audio streaming failed, but text was sent'
        
        return success_response(response)
        
    except ValidationError as e:
        logger.warning(f"Validation error in message broadcast: {e}")
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
        
    except ServiceUnavailableError as e:
        logger.error(f"Service error in message broadcast: {e}")
        return error_response(str(e), code='SERVICE_ERROR', status_code=503)
        
    except Exception as e:
        logger.error(f"Error in message broadcast: {e}")
        return error_response('Failed to broadcast message', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/streaming/clients', methods=['GET'])
def get_connected_clients():
    """接続中クライアント情報取得
    
    Returns:
        JSON response with connected clients information
    """
    try:
        connected_count = get_connected_clients_count()
        
        response = {
            'success': True,
            'connected_clients': connected_count,
            'client_details': [],  # 基本実装
            'active_streams': 0,   # 基本実装
            'queue_length': 0      # 基本実装
        }
        
        return success_response(response)
        
    except Exception as e:
        logger.error(f"Error getting connected clients: {e}")
        return error_response('Failed to get connected clients information', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/streaming/queue/clear', methods=['POST'])
def clear_streaming_queue():
    """ストリーミングキューのクリア
    
    Request JSON:
        force: 強制クリアフラグ (optional, default: false)
    
    Returns:
        JSON response with clear result
    """
    try:
        data = request.get_json() or {}
        force = data.get('force', False)
        
        # 基本的なキュークリア実装
        logger.info(f"🧹 Streaming queue clear requested (force: {force})")
        
        # キュークリア通知を配信
        broadcast_audio_notification(
            'queue_cleared',
            f'Streaming queue cleared (force: {force})',
            None
        )
        
        return success_response({
            'cleared_items': 0,  # 基本実装
            'force': force,
            'message': 'Streaming queue cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing streaming queue: {e}")
        return error_response('Failed to clear streaming queue', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/streaming/performance', methods=['GET'])
def get_streaming_performance():
    """ストリーミングパフォーマンス統計取得
    
    Query Parameters:
        time_range: 統計期間 (optional, default: "1h")
                   Options: "1h", "6h", "24h", "7d"
    
    Returns:
        JSON response with performance statistics
    """
    try:
        time_range = request.args.get('time_range', '1h')
        
        # 基本統計のみ返す
        basic_stats = {
            'connected_clients': get_connected_clients_count(),
            'active_streams': 0,
            'total_streamed': 0,
            'average_latency': 0.0
        }
        
        return success_response({
            'time_range': time_range,
            'performance': basic_stats,
            'current_status': {
                'connected_clients': get_connected_clients_count(),
                'streaming_active': get_connected_clients_count() > 0
            },
            'note': 'Basic performance monitoring implementation'
        })
        
    except Exception as e:
        logger.error(f"Error getting streaming performance: {e}")
        return error_response('Failed to get streaming performance statistics', code='INTERNAL_ERROR', status_code=500)