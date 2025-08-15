"""
TTS Emotion Processing API Routes - 感情処理API
"""

from typing import Optional
from flask import Blueprint, request
from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import ValidationError, ServiceUnavailableError
from web.response_utils import success_response, error_response

logger = setup_logger(__name__)

tts_emotion_bp = Blueprint('tts_emotion', __name__, url_prefix='/tts')

tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_emotion_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_emotion_bp.route('/emotions', methods=['GET'])
def get_available_emotions():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        emotions = tts_service.get_available_emotions()
        return success_response({'emotions': emotions, 'total_count': len(emotions)})
    except Exception as e:
        logger.error(f"Error getting available emotions: {e}")
        return error_response('Failed to get available emotions', code='INTERNAL_ERROR', status_code=500)


@tts_emotion_bp.route('/emotions/custom', methods=['POST'])
def create_custom_emotion():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        base_emotion = data.get('base_emotion')
        if not base_emotion:
            raise ValidationError("base_emotion is required")
        name = data.get('name')
        if not name:
            raise ValidationError("name is required")
        intensity = data.get('intensity', 0.5)
        custom_vector = data.get('custom_vector')
        description = data.get('description', '')
        result = tts_service.create_custom_emotion(
            base_emotion=base_emotion,
            intensity=intensity,
            custom_vector=custom_vector,
            name=name,
            description=description,
        )
        return success_response({'custom_emotion': result, 'message': f'Custom emotion "{name}" created successfully'})
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except ServiceUnavailableError as e:
        return error_response(str(e), code='SERVICE_ERROR', status_code=503)
    except Exception as e:
        logger.error(f"Error creating custom emotion: {e}")
        return error_response('Failed to create custom emotion', code='INTERNAL_ERROR', status_code=500)


@tts_emotion_bp.route('/emotions/mix', methods=['POST'])
def mix_emotions():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        emotions = data.get('emotions')
        if not emotions or not isinstance(emotions, list) or len(emotions) < 2:
            raise ValidationError("At least 2 emotions are required for mixing")
        normalize_weights = data.get('normalize_weights', True)
        result_name = data.get('result_name', 'mixed_emotion')
        result = tts_service.mix_emotions(
            emotions=emotions,
            normalize_weights=normalize_weights,
            result_name=result_name,
        )
        return success_response({'mixed_emotion': result, 'input_emotions': emotions, 'message': f'Emotions mixed successfully as "{result_name}"'})
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except ServiceUnavailableError as e:
        return error_response(str(e), code='SERVICE_ERROR', status_code=503)
    except Exception as e:
        logger.error(f"Error mixing emotions: {e}")
        return error_response('Failed to mix emotions', code='INTERNAL_ERROR', status_code=500)


@tts_emotion_bp.route('/emotions/presets', methods=['GET'])
def get_emotion_presets():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        category = request.args.get('category')
        language = request.args.get('language')
        presets = tts_service.get_emotion_presets(category=category, language=language)
        return success_response({'presets': presets, 'total_count': len(presets), 'filters': {'category': category, 'language': language}})
    except Exception as e:
        logger.error(f"Error getting emotion presets: {e}")
        return error_response('Failed to get emotion presets', code='INTERNAL_ERROR', status_code=500)


@tts_emotion_bp.route('/emotions/presets', methods=['POST'])
def create_emotion_preset():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        name = data.get('name')
        if not name:
            raise ValidationError("name is required")
        emotion_config = data.get('emotion_config')
        if not emotion_config:
            raise ValidationError("emotion_config is required")
        category = data.get('category', 'custom')
        language = data.get('language', 'ja')
        description = data.get('description', '')
        tags = data.get('tags', [])
        result = tts_service.create_emotion_preset(
            name=name,
            emotion_config=emotion_config,
            category=category,
            language=language,
            description=description,
            tags=tags,
        )
        return success_response({'preset': result, 'message': f'Emotion preset "{name}" created successfully'})
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except ServiceUnavailableError as e:
        return error_response(str(e), code='SERVICE_ERROR', status_code=503)
    except Exception as e:
        logger.error(f"Error creating emotion preset: {e}")
        return error_response('Failed to create emotion preset', code='INTERNAL_ERROR', status_code=500)


@tts_emotion_bp.route('/emotions/presets/<preset_id>', methods=['DELETE'])
def delete_emotion_preset(preset_id: str):
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        success = tts_service.delete_emotion_preset(preset_id)
        if success:
            return success_response({'message': f'Emotion preset {preset_id} deleted successfully'})
        else:
            return error_response(f'Emotion preset {preset_id} not found', code='PRESET_NOT_FOUND', status_code=404)
    except Exception as e:
        logger.error(f"Error deleting emotion preset {preset_id}: {e}")
        return error_response('Failed to delete emotion preset', code='INTERNAL_ERROR', status_code=500)


@tts_emotion_bp.route('/emotions/analyze', methods=['POST'])
def analyze_text_emotion():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        text = data.get('text')
        if not text:
            raise ValidationError("text is required")
        language = data.get('language', 'ja')
        return_confidence = data.get('return_confidence', True)
        result = tts_service.analyze_text_emotion(text=text, language=language, return_confidence=return_confidence)
        return success_response({'text': text, 'analysis': result, 'language': language})
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except ServiceUnavailableError as e:
        return error_response(str(e), code='SERVICE_ERROR', status_code=503)
    except Exception as e:
        logger.error(f"Error analyzing text emotion: {e}")
        return error_response('Failed to analyze text emotion', code='INTERNAL_ERROR', status_code=500)


@tts_emotion_bp.route('/emotions/apply', methods=['POST'])
def apply_emotion_to_speech():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        text = data.get('text')
        if not text:
            raise ValidationError("text is required")
        emotion = data.get('emotion')
        if not emotion:
            raise ValidationError("emotion is required")
        intensity = data.get('intensity', 0.5)
        voice_sample_id = data.get('voice_sample_id')
        language = data.get('language', 'ja')
        result = tts_service.synthesize_with_emotion(
            text=text,
            emotion=emotion,
            intensity=intensity,
            voice_sample_id=voice_sample_id,
            language=language,
        )
        return success_response({'audio_file_id': result['audio_file_id'], 'applied_emotion': {'emotion': emotion, 'intensity': intensity}, 'metadata': result.get('metadata', {}), 'message': 'Emotion applied to speech successfully'})
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except ServiceUnavailableError as e:
        return error_response(str(e), code='SERVICE_ERROR', status_code=503)
    except Exception as e:
        logger.error(f"Error applying emotion to speech: {e}")
        return error_response('Failed to apply emotion to speech', code='INTERNAL_ERROR', status_code=500)

__all__ = ['tts_emotion_bp', 'init_emotion_services']

