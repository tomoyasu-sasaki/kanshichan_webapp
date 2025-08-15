"""
TTS System Management API Routes - システム管理API
"""

import os
from typing import Optional
from datetime import datetime
from flask import Blueprint, request
from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import ValidationError
from web.response_utils import success_response, error_response
from .helpers import get_backend_path

logger = setup_logger(__name__)

tts_system_bp = Blueprint('tts_system', __name__, url_prefix='/tts')

tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_system_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_system_bp.route('/status', methods=['GET'])
def get_tts_status():
    try:
        # TTSサービスの詳細ステータスを取得
        tts_details = None
        if tts_service:
            tts_status = tts_service.get_service_status()
            device_info = tts_status.get('device_info', {})
            tts_details = {
                'initialized': tts_status.get('initialized', False),
                'model_name': tts_status.get('model_name', 'Unknown'),
                'device': device_info.get('current_device', 'Unknown'),
                'voice_cloning_enabled': bool(tts_status.get('voice_cloning_enabled', False)),
                'default_language': tts_status.get('default_language', 'ja'),
                'supported_languages': tts_status.get('supported_languages', ['ja']),
                'available_emotions': tts_status.get('available_emotions', ['neutral'])
            }
        
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'services': {
                'tts_service': 'available' if tts_service else 'unavailable',
                'voice_manager': 'available' if voice_manager else 'unavailable'
            },
            'system_health': 'healthy' if tts_service and voice_manager else 'degraded',
            'tts_details': tts_details
        }
        return success_response(response)
    except Exception as e:
        return error_response('Failed to get TTS service status', code='INTERNAL_ERROR', status_code=500)


@tts_system_bp.route('/languages', methods=['GET'])
def get_supported_languages():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        languages = tts_service.get_supported_languages()
        return success_response({'languages': languages, 'total_count': len(languages), 'default_language': 'ja'})
    except Exception as e:
        return error_response('Failed to get supported languages', code='INTERNAL_ERROR', status_code=500)


@tts_system_bp.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    if not voice_manager:
        return error_response('Voice manager is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)
        file_types = data.get('file_types', ['cache', 'temp'])
        dry_run = data.get('dry_run', False)
        force = data.get('force', False)
        if not isinstance(max_age_hours, (int, float)) or max_age_hours <= 0:
            raise ValidationError("max_age_hours must be a positive number")
        if not isinstance(file_types, list) or not all(isinstance(t, str) for t in file_types):
            raise ValidationError("file_types must be a list of strings")
        cleanup_result = voice_manager.cleanup_old_files(max_age_hours=max_age_hours, file_types=file_types, dry_run=dry_run, force=force)
        response = {
            'success': True,
            'cleanup_performed': not dry_run,
            'dry_run': dry_run,
            'max_age_hours': max_age_hours,
            'file_types': file_types,
            'results': cleanup_result
        }
        return success_response(response)
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except Exception as e:
        return error_response('Failed to perform cleanup operation', code='INTERNAL_ERROR', status_code=500)


@tts_system_bp.route('/config', methods=['GET'])
def get_system_config():
    try:
        config = {'success': True, 'configuration': {'backend_path': str(get_backend_path()), 'services_available': {'tts_service': tts_service is not None, 'voice_manager': voice_manager is not None}}}
        return success_response(config)
    except Exception as e:
        return error_response('Failed to get system configuration', code='INTERNAL_ERROR', status_code=500)


@tts_system_bp.route('/health', methods=['GET'])
def health_check():
    try:
        health_status = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'components': {}
        }
        return success_response(health_status, status_code=200)
    except Exception as e:
        return error_response('Health check failed', code='INTERNAL_ERROR', status_code=500)


@tts_system_bp.route('/metrics', methods=['GET'])
def get_system_metrics():
    try:
        return success_response({'success': True, 'time_range': request.args.get('time_range', '1h'), 'timestamp': datetime.now().isoformat(), 'metrics': {}})
    except Exception as e:
        return error_response('Failed to get system metrics', code='INTERNAL_ERROR', status_code=500)


@tts_system_bp.route('/restart', methods=['POST'])
def restart_services():
    try:
        data = request.get_json() or {}
        service = data.get('service', 'all')
        force = data.get('force', False)
        restart_results = {'success': True, 'service': service, 'force': force, 'timestamp': datetime.now().isoformat(), 'results': {}}
        return success_response(restart_results)
    except Exception as e:
        return error_response('Failed to restart services', code='INTERNAL_ERROR', status_code=500)


@tts_system_bp.route('/voice-settings', methods=['GET'])
def get_voice_settings():
    try:
        from flask import current_app
        config_manager = current_app.config.get('config_manager')
        if not config_manager:
            return error_response('Configuration manager is not available', code='CONFIG_NOT_AVAILABLE', status_code=500)
        voice_settings = {
            'success': True,
            'voice_settings': {
                'voiceMode': config_manager.get('tts.default_voice_mode', 'tts'),
                'defaultEmotion': config_manager.get('tts.default_emotion', 'neutral'),
                'defaultLanguage': config_manager.get('tts.default_language', 'ja'),
                'voiceSpeed': config_manager.get('tts.default_voice_speed', 1.0),
                'voicePitch': config_manager.get('tts.default_voice_pitch', 1.0),
                'voiceVolume': config_manager.get('tts.default_voice_volume', 0.7),
                'fastMode': config_manager.get('tts.default_fast_mode', False),
                'voiceSampleId': config_manager.get('tts.default_voice_sample_id', None),
                'maxFrequency': config_manager.get('tts.default_max_frequency', 24000),
                'audioQuality': config_manager.get('tts.default_audio_quality', 4.0),
                'vqScore': config_manager.get('tts.default_vq_score', 0.78)
            }
        }
        return success_response(voice_settings)
    except Exception as e:
        return error_response('Failed to get voice settings', code='INTERNAL_ERROR', status_code=500)


@tts_system_bp.route('/voice-settings', methods=['POST'])
def save_voice_settings():
    try:
        data = request.json
        from flask import current_app
        config_manager = current_app.config.get('config_manager')
        if not config_manager:
            return error_response('Configuration manager is not available', code='CONFIG_NOT_AVAILABLE', status_code=500)
        config_manager.set('tts.default_voice_mode', data.get('voiceMode', 'tts'))
        config_manager.save()
        return success_response({'message': 'Voice settings saved as default'})
    except Exception as e:
        return error_response(str(e), code='SAVE_FAILED', status_code=500)

__all__ = ['tts_system_bp', 'init_system_services']

