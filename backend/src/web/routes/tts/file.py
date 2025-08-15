"""
TTS File Management API Routes - ファイル管理API
"""

import os
from typing import Optional
from flask import Blueprint, request, send_file
from datetime import datetime
from pathlib import Path

from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import (
    AudioError, ServiceUnavailableError, ValidationError, FileNotFoundError, wrap_exception
)
from web.response_utils import success_response, error_response

logger = setup_logger(__name__)

tts_file_bp = Blueprint('tts_file', __name__, url_prefix='/tts')

tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_file_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_file_bp.route('/audio/<file_id>', methods=['GET'])
def get_audio_file(file_id: str):
    if not voice_manager:
        return error_response('Voice manager is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        file_path, metadata = voice_manager.get_audio_file(file_id)
        return send_file(file_path, as_attachment=False, download_name=metadata.original_filename, mimetype='audio/wav')
    except FileNotFoundError as e:
        return error_response(str(e), code='FILE_NOT_FOUND', status_code=404)
    except Exception as e:
        logger.error(f"Error retrieving audio file {file_id}: {e}")
        return error_response('Failed to retrieve audio file', code='INTERNAL_ERROR', status_code=500)


@tts_file_bp.route('/voices', methods=['GET'])
def list_voice_files():
    if not voice_manager:
        return error_response('Voice manager is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        file_type = request.args.get('type')
        user_id = request.args.get('user_id')
        files = voice_manager.list_audio_files(file_type=file_type, user_id=user_id)
        return success_response({'files': files, 'count': len(files)})
    except Exception as e:
        logger.error(f"Error listing voice files: {e}")
        return error_response('Failed to list voice files', code='INTERNAL_ERROR', status_code=500)


@tts_file_bp.route('/voices/<file_id>', methods=['DELETE'])
def delete_voice_file(file_id: str):
    if not voice_manager:
        return error_response('Voice manager is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        success = voice_manager.delete_audio_file(file_id)
        if success:
            return success_response({'message': f'Audio file {file_id} deleted successfully'})
        else:
            return error_response(f'Audio file {file_id} not found', code='FILE_NOT_FOUND', status_code=404)
    except Exception as e:
        logger.error(f"Error deleting audio file {file_id}: {e}")
        return error_response('Failed to delete audio file', code='INTERNAL_ERROR', status_code=500)


@tts_file_bp.route('/upload_voice_sample', methods=['POST'])
def upload_voice_sample():
    logger.info("🎵 Audio upload request received")
    if not voice_manager:
        logger.error("Voice Manager service is not available")
        return error_response('Voice Manager service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        if 'audio_file' not in request.files:
            return error_response('Audio file is required', code='MISSING_FILE', status_code=400)
        file = request.files['audio_file']
        if file.filename == '':
            return error_response('No file selected', code='INVALID_FILE', status_code=400)
        text = request.form.get('text', '')
        emotion = request.form.get('emotion', 'neutral')
        language = request.form.get('language', 'ja')
        custom_filename = request.form.get('custom_filename', '')
        return_url = request.form.get('return_url', 'false').lower() == 'true'

        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        if file_size > 10 * 1024 * 1024:
            return error_response('File size must be less than 10MB', code='FILE_TOO_LARGE', status_code=413)

        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return error_response(f'Unsupported file format. Allowed: {", ".join(allowed_extensions)}', code='INVALID_FORMAT', status_code=400)

        with Path(os.getenv('TMPDIR') or '/tmp').joinpath(f'upload_{file_ext.strip(".")}_{datetime.now().timestamp()}').open('wb') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            metadata = {
                'voice_sample_for': 'user_uploaded',
                'language': language,
                'emotion': emotion,
                'upload_timestamp': datetime.now().isoformat(),
                'original_filename': file.filename
            }
            if text:
                metadata['text_content'] = text
            if custom_filename:
                metadata['display_name'] = f"{custom_filename}{file_ext}"

            file_id = voice_manager.save_audio_file(temp_path, file_type='sample', metadata=metadata)

            quality_score = None
            quality_details = None
            if tts_service:
                try:
                    quality_result = tts_service.evaluate_voice_sample_quality(temp_path)
                    quality_score = quality_result.get('overall_score', None)
                    quality_details = quality_result
                except Exception:
                    pass

            result = {
                'success': True,
                'file_id': file_id,
                'filename': (custom_filename + file_ext) if custom_filename else file.filename,
                'file_size': file_size,
                'metadata': metadata,
                'quality_score': quality_score
            }
            if return_url:
                result['file_url'] = f"/api/tts/audio/{file_id}"
            if quality_details:
                result['quality_details'] = quality_details
            return success_response(result, status_code=200)
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except Exception as e:
        logger.error(f"Voice sample upload error: {e}")
        return error_response('Failed to upload voice sample', code='UPLOAD_FAILED', status_code=500)


@tts_file_bp.route('/evaluate-quality', methods=['POST'])
def evaluate_voice_quality():
    if not tts_service:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        if 'audio_file' not in request.files:
            raise ValidationError("Missing audio file")
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            raise ValidationError("No audio file selected")
        return_recommendations = request.form.get('return_recommendations', 'true').lower() == 'true'

        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            audio_file.save(temp_file.name)
            temp_audio_path = temp_file.name
        try:
            evaluation = tts_service.evaluate_voice_sample_quality(temp_audio_path)
            response = {
                'success': True,
                'quality_score': evaluation['overall_score'],
                'suitable_for_cloning': evaluation['suitable_for_cloning'],
                'audio_info': {
                    'duration_seconds': evaluation['duration_seconds'],
                    'sampling_rate': evaluation['sampling_rate'],
                    'channels': evaluation['channels'],
                    'rms_level': evaluation['rms_level']
                },
                'evaluation_timestamp': evaluation['evaluation_timestamp']
            }
            if return_recommendations:
                response['recommendations'] = evaluation['recommendations']
            return success_response(response)
        finally:
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except (AudioError, ServiceUnavailableError) as e:
        return error_response(str(e), code='EVALUATION_ERROR', status_code=500)
    except Exception as e:
        error = wrap_exception(e, AudioError, "Unexpected error in quality evaluation")
        logger.error(f"Unexpected error in quality evaluation: {error.to_dict()}")
        return error_response('An unexpected error occurred', code='INTERNAL_ERROR', status_code=500)


@tts_file_bp.route('/voice-profiles', methods=['GET'])
def get_voice_profiles():
    if not voice_manager:
        return error_response('Voice manager service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        user_id = request.args.get('user_id')
        quality_threshold = float(request.args.get('quality_threshold', 0.0))
        limit = int(request.args.get('limit', 50))

        voice_samples = voice_manager.list_audio_files(file_type='sample', user_id=user_id)
        if quality_threshold > 0.0:
            voice_samples = [s for s in voice_samples if s.get('quality_score', 0.0) >= quality_threshold]
        if limit > 0:
            voice_samples = voice_samples[:limit]

        profiles = []
        for sample in voice_samples:
            profiles.append({
                'file_id': sample['file_id'],
                'user_id': sample.get('voice_sample_for', 'unknown'),
                'duration_seconds': sample['duration_seconds'],
                'quality_score': sample.get('quality_score'),
                'language': sample.get('language', 'unknown'),
                'created_at': sample['created_at'],
                'suitable_for_cloning': sample.get('quality_score', 0.0) >= 0.7,
                'file_size': sample['file_size'],
                'exists': sample['exists']
            })

        return success_response({'profiles': profiles, 'total_count': len(profiles), 'filters': {'user_id': user_id, 'quality_threshold': quality_threshold, 'limit': limit}})
    except ValueError as e:
        return error_response('Invalid parameter values', code='PARAMETER_ERROR', status_code=400)
    except Exception as e:
        error = wrap_exception(e, AudioError, "Unexpected error in voice profiles")
        logger.error(f"Unexpected error in voice profiles: {error.to_dict()}")
        return error_response('An unexpected error occurred', code='INTERNAL_ERROR', status_code=500)

__all__ = ['tts_file_bp', 'init_file_services']

