"""
TTS Voice Clone API Routes - 音声クローンAPI

音声クローン機能のAPIエンドポイント群
基本クローン、品質向上版クローン、高速クローン機能を提供
"""

import os
from datetime import datetime
import tempfile
import uuid
import contextlib
import io
from typing import Optional
from flask import Blueprint, request, send_file

from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import (
    AudioError, ServiceUnavailableError, ValidationError, wrap_exception
)
from web.response_utils import success_response, error_response
from .helpers import ensure_tqdm_disabled

logger = setup_logger(__name__)

# Blueprint定義（相対パス化。上位で /api および /api/v1 を付与）
tts_voice_clone_bp = Blueprint('tts_voice_clone', __name__, url_prefix='/tts')

# サービスインスタンス（helpers.pyで初期化）
tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_voice_clone_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    """音声クローンサービスの初期化"""
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_voice_clone_bp.route('/clone-voice', methods=['POST'])
def clone_voice():
    """音声クローン（ファイルアップロード版）"""
    if not tts_service or not voice_manager:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)

    try:
        text = request.form.get('text', '').strip()
        if not text or len(text) > 1000:
            raise ValidationError("Text length must be between 1 and 1000 characters")

        if 'audio_file' not in request.files:
            raise ValidationError("Missing audio file")
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            raise ValidationError("No audio file selected")

        emotion = request.form.get('emotion', 'neutral')
        language = request.form.get('language', 'ja')
        return_url = request.form.get('return_url', 'false').lower() == 'true'
        display_name = request.form.get('display_name', '').strip()

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            audio_file.save(temp_file.name)
            temp_audio_path = temp_file.name

        try:
            logger.info(f"Cloning voice for text: '{text[:50]}...' (emotion: {emotion})")
            ensure_tqdm_disabled()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                output_path = tts_service.clone_voice(
                    text=text,
                    reference_audio_path=temp_audio_path,
                    emotion=emotion
                )

            sample_id = voice_manager.save_audio_file(
                audio_path=temp_audio_path,
                file_type='sample',
                metadata={
                    'voice_sample_for': 'temp_user',
                    'language': language,
                    'display_name': display_name if display_name else None
                }
            )

            file_id = voice_manager.save_audio_file(
                audio_path=output_path,
                file_type='generated',
                metadata={
                    'text_content': text,
                    'emotion': emotion,
                    'language': language,
                    'cloned_from': sample_id
                }
            )

            if return_url:
                file_size = os.path.getsize(output_path)
                response = {
                    'success': True,
                    'file_id': file_id,
                    'sample_id': sample_id,
                    'file_size': file_size,
                    'parameters': {
                        'text': text,
                        'emotion': emotion,
                        'language': language
                    }
                }
                return success_response(response)
            else:
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=f'cloned_voice_{emotion}.wav',
                    mimetype='audio/wav'
                )
        finally:
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except (AudioError, ServiceUnavailableError) as e:
        return error_response(str(e), code='CLONING_ERROR', status_code=500)
    except Exception as e:
        error = wrap_exception(e, AudioError, "Unexpected error in voice cloning")
        logger.error(f"Unexpected error in voice cloning: {error.to_dict()}")
        return error_response('An unexpected error occurred', code='INTERNAL_ERROR', status_code=500)


@tts_voice_clone_bp.route('/clone-voice-enhanced', methods=['POST'])
def clone_voice_enhanced():
    """音声クローン（品質向上版）"""
    if not tts_service or not voice_manager:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)

    try:
        text = request.form.get('text', '').strip()
        if not text or len(text) > 1000:
            raise ValidationError("Text length must be between 1 and 1000 characters")

        if 'audio_file' not in request.files:
            raise ValidationError("Missing audio file")
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            raise ValidationError("No audio file selected")

        emotion = request.form.get('emotion', 'neutral')
        language = request.form.get('language', 'ja')
        enhance_quality = request.form.get('enhance_quality', 'true').lower() == 'true'
        return_url = request.form.get('return_url', 'false').lower() == 'true'
        display_name = request.form.get('display_name', '').strip()

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            audio_file.save(temp_file.name)
            temp_audio_path = temp_file.name

        try:
            quality_info = None
            if enhance_quality:
                try:
                    quality_evaluation = tts_service.evaluate_voice_sample_quality(temp_audio_path)
                    quality_info = {
                        'quality_score': quality_evaluation['overall_score'],
                        'suitable_for_cloning': quality_evaluation['suitable_for_cloning']
                    }
                except Exception:
                    pass

            ensure_tqdm_disabled()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                output_path = tts_service.clone_voice(
                    text=text,
                    reference_audio_path=temp_audio_path,
                    emotion=emotion,
                    enhance_quality=enhance_quality
                )

            sample_id = voice_manager.save_audio_file(
                audio_path=temp_audio_path,
                file_type='sample',
                metadata={
                    'voice_sample_for': 'temp_user',
                    'language': language,
                    'quality_enhanced': enhance_quality,
                    'quality_score': quality_info['quality_score'] if quality_info else None,
                    'display_name': display_name if display_name else None
                }
            )

            file_id = voice_manager.save_audio_file(
                audio_path=output_path,
                file_type='generated',
                metadata={
                    'text_content': text,
                    'emotion': emotion,
                    'language': language,
                    'cloned_from': sample_id,
                    'enhanced_cloning': enhance_quality
                }
            )

            if return_url:
                file_size = os.path.getsize(output_path)
                response = {
                    'success': True,
                    'file_id': file_id,
                    'sample_id': sample_id,
                    'file_size': file_size,
                    'enhanced_processing': enhance_quality,
                    'parameters': {
                        'text': text,
                        'emotion': emotion,
                        'language': language
                    }
                }
                if quality_info:
                    response['quality_info'] = quality_info
                return success_response(response)
            else:
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=f'enhanced_cloned_voice_{emotion}.wav',
                    mimetype='audio/wav'
                )
        finally:
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except (AudioError, ServiceUnavailableError) as e:
        return error_response(str(e), code='CLONING_ERROR', status_code=500)
    except Exception as e:
        error = wrap_exception(e, AudioError, "Unexpected error in enhanced voice cloning")
        logger.error(f"Unexpected error in enhanced voice cloning: {error.to_dict()}")
        return error_response('An unexpected error occurred', code='INTERNAL_ERROR', status_code=500)


@tts_voice_clone_bp.route('/clone-voice-fast', methods=['POST'])
def clone_voice_fast():
    """高速音声クローン（シンプル版相当の性能）"""
    if not tts_service or not voice_manager:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)

    try:
        text = request.form.get('text', '').strip()
        language = request.form.get('language', 'ja')
        return_url = request.form.get('return_url', 'false').lower() == 'true'

        if 'reference_audio' not in request.files:
            raise ValidationError("Reference audio file is required")
        reference_file = request.files['reference_audio']
        if reference_file.filename == '':
            raise ValidationError("Reference audio file is required")

        if not text:
            raise ValidationError("Text is required")
        if len(text) > 1000:
            raise ValidationError("Text is too long (max 1000 characters)")

        audio_id = str(uuid.uuid4())

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            reference_file.save(temp_file.name)
            reference_audio_path = temp_file.name

        try:
            logger.info(f"🚀 Fast voice cloning: '{text[:50]}...' (language: {language})")
            ensure_tqdm_disabled()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                output_path = tts_service.clone_voice_fast(
                    text=text,
                    reference_audio_path=reference_audio_path,
                    language=language
                )

            file_id = voice_manager.save_audio_file(
                audio_path=output_path,
                file_type='fast_cache',
                metadata={
                    'audio_id': audio_id,
                    'text_content': text,
                    'language': language,
                    'fast_mode': True,
                    'voice_cloned': True,
                    'synthesis_timestamp': datetime.now().isoformat()
                }
            )

            if return_url:
                file_size = os.path.getsize(output_path)
                response = {
                    'success': True,
                    'audio_id': audio_id,
                    'file_id': file_id,
                    'file_size': file_size,
                    'fast_mode': True,
                    'voice_cloned': True,
                    'text_content': text,
                    'language': language
                }
                logger.info(f"✅ Fast voice cloning completed: {audio_id}")
                return success_response(response)
            else:
                logger.info(f"✅ Fast voice cloning completed, returning binary data: {audio_id}")
                return send_file(
                    output_path,
                    as_attachment=False,
                    download_name=f'voice_clone_fast_{audio_id}.wav',
                    mimetype='audio/wav'
                )
        finally:
            try:
                os.unlink(reference_audio_path)
            except Exception:
                pass

    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except AudioError as e:
        return error_response(str(e), code='AUDIO_ERROR', status_code=500)
    except Exception as e:
        return error_response('Fast voice cloning failed due to internal error', code='INTERNAL_ERROR', status_code=500)

__all__ = ['tts_voice_clone_bp', 'init_voice_clone_services']

