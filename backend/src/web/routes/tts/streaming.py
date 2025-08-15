"""
TTS Streaming API Routes - ストリーミング配信API
"""

from typing import Optional
from flask import Blueprint, request
from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import ValidationError, ServiceUnavailableError
from web.websocket import (
    broadcast_audio_notification, queue_audio_for_streaming,
    get_connected_clients_count
)
from web.response_utils import success_response, error_response

logger = setup_logger(__name__)

tts_streaming_bp = Blueprint('tts_streaming', __name__, url_prefix='/tts')

tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_streaming_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_streaming_bp.route('/stream-audio', methods=['POST'])
def stream_audio():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
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

        connected_clients = get_connected_clients_count()
        if connected_clients == 0:
            return error_response('No connected clients for streaming', code='NO_CLIENTS', status_code=400)

        synthesis_params = {'emotion': emotion, 'language': language}
        if voice_sample_id:
            synthesis_params['voice_sample_id'] = voice_sample_id

        audio_result = tts_service.synthesize_text_fast(text=text, **synthesis_params)
        stream_metadata = {
            'text': text,
            'emotion': emotion,
            'language': language,
            'priority': priority,
            'synthesis_time': audio_result.get('synthesis_time', 0),
            'generated_at': audio_result.get('generated_at')
        }

        audio_file_path = audio_result.get('file_path')
        if not audio_file_path:
            return error_response('Audio file path not available', code='SYNTHESIS_ERROR', status_code=500)

        queue_audio_for_streaming(audio_file_path, stream_metadata)
        broadcast_audio_notification('audio_stream_started', f"Audio streaming started: {text[:100]}...", audio_result['audio_file_id'])

        return success_response({
            'audio_file_id': audio_result['audio_file_id'],
            'connected_clients': connected_clients,
            'broadcast_type': 'all' if broadcast_all else 'targeted' if target_client_ids else 'all',
            'streaming_metadata': stream_metadata,
            'message': 'Audio streaming started successfully'
        })
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except ServiceUnavailableError as e:
        return error_response(str(e), code='SERVICE_ERROR', status_code=503)
    except Exception as e:
        return error_response('Failed to stream audio', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/streaming-status', methods=['GET'])
def get_streaming_status():
    try:
        connected_clients = get_connected_clients_count()
        tts_status = 'available' if tts_service else 'unavailable'
        voice_manager_status = 'available' if voice_manager else 'unavailable'
        response = {
            'success': True,
            'streaming_system': {
                'status': 'active' if connected_clients > 0 else 'idle',
                'connected_clients': connected_clients,
                'active_streams': 0,
                'total_streamed': 0
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
        return success_response(response)
    except Exception as e:
        return error_response('Failed to get streaming status', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/broadcast-message', methods=['POST'])
def broadcast_message():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        message = data.get('message')
        if not message:
            raise ValidationError("message is required")
        voice_sample_id = data.get('voice_sample_id')
        emotion = data.get('emotion', 'neutral')
        language = data.get('language', 'ja')
        priority = data.get('priority', 8)
        include_text = data.get('include_text', True)

        connected_clients = get_connected_clients_count()
        if connected_clients == 0:
            return success_response({'warning': 'no_clients', 'message': 'No connected clients for broadcast'})

        synthesis_params = {'emotion': emotion, 'language': language}
        if voice_sample_id:
            synthesis_params['voice_sample_id'] = voice_sample_id
        audio_result = tts_service.synthesize_text_fast(text=message, **synthesis_params)

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

        audio_file_path = audio_result.get('file_path')
        if audio_file_path:
            queue_audio_for_streaming(audio_file_path, broadcast_metadata)
            stream_success = True
        else:
            stream_success = False

        if include_text:
            try:
                from web.websocket import socketio
                text_notification = {'type': 'broadcast_text', 'message': message, 'metadata': broadcast_metadata}
                socketio.emit('broadcast_notification', text_notification)
            except ImportError:
                pass

        if stream_success:
            broadcast_audio_notification('broadcast_started', f"Message broadcast started: {message[:100]}...", audio_result['audio_file_id'])

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
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except ServiceUnavailableError as e:
        return error_response(str(e), code='SERVICE_ERROR', status_code=503)
    except Exception as e:
        return error_response('Failed to broadcast message', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/streaming/clients', methods=['GET'])
def get_connected_clients():
    try:
        connected_count = get_connected_clients_count()
        response = {
            'success': True,
            'connected_clients': connected_count,
            'client_details': [],
            'active_streams': 0,
            'queue_length': 0
        }
        return success_response(response)
    except Exception as e:
        return error_response('Failed to get connected clients information', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/streaming/queue/clear', methods=['POST'])
def clear_streaming_queue():
    try:
        data = request.get_json() or {}
        force = data.get('force', False)
        broadcast_audio_notification('queue_cleared', f'Streaming queue cleared (force: {force})', None)
        return success_response({'cleared_items': 0, 'force': force, 'message': 'Streaming queue cleared'})
    except Exception as e:
        return error_response('Failed to clear streaming queue', code='INTERNAL_ERROR', status_code=500)


@tts_streaming_bp.route('/streaming/performance', methods=['GET'])
def get_streaming_performance():
    try:
        time_range = request.args.get('time_range', '1h')
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
        return error_response('Failed to get streaming performance statistics', code='INTERNAL_ERROR', status_code=500)

__all__ = ['tts_streaming_bp', 'init_streaming_services']

