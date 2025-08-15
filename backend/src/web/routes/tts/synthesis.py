"""
TTS Synthesis API Routes - 音声合成API

テキスト音声合成機能のAPIエンドポイント群
基本合成、高速合成、高度合成機能を提供
"""

import os
import contextlib
import io
import uuid
from typing import Optional
from datetime import datetime
from flask import Blueprint, request, send_file

from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import (
    AudioError, ServiceUnavailableError, ValidationError
)
from web.websocket import (
    broadcast_audio_notification, queue_audio_for_streaming,
    get_connected_clients_count
)
from web.response_utils import success_response, error_response
from .helpers import ensure_tqdm_disabled, get_backend_path

logger = setup_logger(__name__)

# Blueprint定義（相対パス化。上位で /api および /api/v1 を付与）
tts_synthesis_bp = Blueprint('tts_synthesis', __name__, url_prefix='/tts')

# サービスインスタンス（helpers.pyで初期化）
tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_synthesis_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    """音声合成サービスの初期化"""
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm

__all__ = ['tts_synthesis_bp', 'init_synthesis_services']


@tts_synthesis_bp.route('/synthesize', methods=['POST'])
def synthesize_speech():
    if not tts_service or not voice_manager:
        return error_response('TTS service is not available', code='SERVICE_UNAVAILABLE', status_code=503)
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'ja')
        emotion = data.get('emotion', 'neutral')
        speed = float(data.get('speed', 1.0))
        pitch = float(data.get('pitch', 1.0))
        speaker_sample_id = data.get('speaker_sample_id')
        return_url = data.get('return_url', False)
        save_to_cache = data.get('save_to_cache', True)
        stream_to_clients = data.get('stream_to_clients', False)

        max_frequency = int(data.get('max_frequency', 24000))
        audio_quality = float(data.get('audio_quality', 4.0))
        vq_score = float(data.get('vq_score', 0.78))

        cfg_scale = float(data.get('cfg_scale', 0.8))
        min_p = float(data.get('min_p', 0.0))
        seed = int(data.get('seed', 0)) if data.get('seed') is not None else None
        audio_prefix = data.get('audio_prefix')
        breath_style = data.get('breath_style', False)
        whisper_style = data.get('whisper_style', False)
        style_intensity = float(data.get('style_intensity', 0.5))
        noise_reduction = data.get('noise_reduction', True)
        speaker_noised = data.get('speaker_noised', False)

        tts_mode = data.get('tts_mode', False)
        voice_clone_mode = data.get('voice_clone_mode', False)

        if not text:
            raise ValidationError('Text is required')
        if len(text) > 1000:
            raise ValidationError('Text is too long (max 1000 characters)')

        if audio_prefix and audio_prefix.strip():
            text = f"{audio_prefix.strip()} {text}"

        audio_id = str(uuid.uuid4())

        if stream_to_clients and get_connected_clients_count() > 0:
            broadcast_audio_notification('tts_started', f'音声合成を開始: {text[:50]}...', audio_id)

        speaker_sample_path = None
        if tts_mode:
            speaker_sample_path = None
        elif voice_clone_mode and speaker_sample_id:
            if speaker_sample_id == 'default_sample':
                default_sample_path = get_backend_path() / 'voice_data/voice_samples/sample.wav'
                if default_sample_path.exists():
                    speaker_sample_path = str(default_sample_path)
            else:
                try:
                    speaker_sample_path, _ = voice_manager.get_audio_file(speaker_sample_id)
                except Exception:
                    speaker_sample_path = None
        elif speaker_sample_id:
            if speaker_sample_id == 'default_sample':
                default_sample_path = get_backend_path() / 'voice_data/voice_samples/sample.wav'
                if default_sample_path.exists():
                    speaker_sample_path = str(default_sample_path)
            else:
                try:
                    speaker_sample_path, _ = voice_manager.get_audio_file(speaker_sample_id)
                except Exception:
                    speaker_sample_path = None

        ensure_tqdm_disabled()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            advanced_params = {
                'cfg_scale': cfg_scale,
                'min_p': min_p,
                'noise_reduction': noise_reduction,
            }
            if breath_style:
                advanced_params['breath_style'] = breath_style
                advanced_params['style_intensity'] = style_intensity
            if whisper_style:
                advanced_params['whisper_style'] = whisper_style
                advanced_params['style_intensity'] = style_intensity
            style_params = {'speaker_noised': True} if speaker_sample_path and speaker_noised else {}
            if seed:
                advanced_params['seed'] = int(seed)
            output_path = tts_service.generate_speech(
                text=text,
                speaker_sample_path=speaker_sample_path,
                language=language,
                emotion=emotion,
                speed=speed,
                pitch=pitch,
                max_frequency=max_frequency,
                audio_quality=audio_quality,
                vq_score=vq_score,
                **style_params,
                **advanced_params,
            )

        if stream_to_clients and get_connected_clients_count() > 0:
            broadcast_audio_notification('tts_completed', f'音声合成が完了: {text[:50]}...', audio_id)

        file_id = None
        if save_to_cache:
            file_id = voice_manager.save_audio_file(
                audio_path=output_path,
                file_type='cache',
                metadata={
                    'audio_id': audio_id,
                    'text_content': text,
                    'emotion': emotion,
                    'language': language,
                    'synthesis_timestamp': datetime.now().isoformat(),
                },
            )

        if stream_to_clients and get_connected_clients_count() > 0:
            stream_metadata = {
                'audio_id': audio_id,
                'file_id': file_id,
                'text_content': text,
                'emotion': emotion,
                'language': language,
                'speed': speed,
                'pitch': pitch,
                'voice_cloned': speaker_sample_path is not None,
                'synthesis_timestamp': datetime.now().isoformat(),
            }
            queue_audio_for_streaming(output_path, stream_metadata)

        if return_url:
            file_size = os.path.getsize(output_path)
            response = {
                'success': True,
                'audio_id': audio_id,
                'file_id': file_id,
                'file_size': file_size,
                'duration': None,
                'streamed': stream_to_clients,
                'connected_clients': get_connected_clients_count(),
                'parameters': {
                    'text': text,
                    'language': language,
                    'emotion': emotion,
                    'speed': speed,
                    'pitch': pitch,
                    'voice_cloned': speaker_sample_path is not None,
                },
            }
            return success_response(response)
        else:
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f'speech_{emotion}_{language}.wav',
                mimetype='audio/wav',
            )
    except ValidationError as e:
        return error_response(str(e), code='VALIDATION_ERROR', status_code=400)
    except (AudioError, ServiceUnavailableError) as e:
        return error_response(str(e), code='SYNTHESIS_ERROR', status_code=500)
    except Exception:
        return error_response('An unexpected error occurred', code='INTERNAL_ERROR', status_code=500)
