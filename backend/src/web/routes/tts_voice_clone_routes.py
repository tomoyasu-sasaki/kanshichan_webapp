"""
TTS Voice Clone API Routes - 音声クローンAPI

音声クローン機能のAPIエンドポイント群
基本クローン、品質向上版クローン、高速クローン機能を提供
"""

import os
import logging
import tempfile
import uuid
import contextlib
import io
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file

from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import (
    AudioError, ServiceUnavailableError, ValidationError, wrap_exception
)
from .tts_helpers import ensure_tqdm_disabled, get_backend_path

logger = setup_logger(__name__)

# Blueprint定義
tts_voice_clone_bp = Blueprint('tts_voice_clone', __name__, url_prefix='/api/tts')

# サービスインスタンス（tts_helpers.pyで初期化）
tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_voice_clone_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    """音声クローンサービスの初期化
    
    Args:
        tts_svc: TTSServiceインスタンス
        vm: VoiceManagerインスタンス
    """
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_voice_clone_bp.route('/clone-voice', methods=['POST'])
def clone_voice():
    """音声クローン（ファイルアップロード版）
    
    Form Data:
        text: 合成するテキスト
        audio_file: 参照音声ファイル (5-30秒推奨)
        emotion: 感情設定 (optional)
        language: 言語設定 (optional)
        return_url: URL返却フラグ (optional)
    
    Returns:
        JSON response with cloned audio information or binary audio data
    """
    if not tts_service or not voice_manager:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # テキスト取得
        text = request.form.get('text', '').strip()
        if not text or len(text) > 1000:
            raise ValidationError("Text length must be between 1 and 1000 characters")
        
        # 音声ファイル取得
        if 'audio_file' not in request.files:
            raise ValidationError("Missing audio file")
        
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            raise ValidationError("No audio file selected")
        
        # パラメータ取得
        emotion = request.form.get('emotion', 'neutral')
        language = request.form.get('language', 'ja')
        return_url = request.form.get('return_url', 'false').lower() == 'true'
        display_name = request.form.get('display_name', '').strip()  # カスタム名前を追加
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            audio_file.save(temp_file.name)
            temp_audio_path = temp_file.name
        
        try:
            # 音声クローン実行
            logger.info(f"Cloning voice for text: '{text[:50]}...' (emotion: {emotion})")
            
            # API実行時の進捗バー無効化を確実にする
            ensure_tqdm_disabled()
            
            # 標準出力/エラー出力も抑制してtqdmの表示を完全に防ぐ
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                output_path = tts_service.clone_voice(
                    text=text,
                    reference_audio_path=temp_audio_path,
                    emotion=emotion
                )
            
            # 参照音声をサンプルとして保存
            sample_id = voice_manager.save_audio_file(
                audio_path=temp_audio_path,
                file_type='sample',
                metadata={
                    'voice_sample_for': 'temp_user',  # 実際の実装ではユーザーIDを使用
                    'language': language,
                    'display_name': display_name if display_name else None
                }
            )
            
            # 生成音声を保存
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
            
            # send_file前にパス検証（clone_voice）
            absolute_output_path = os.path.abspath(output_path)
            logger.debug(f"Sending cloned voice file: {output_path} -> absolute: {absolute_output_path}")
            logger.debug(f"File exists: {os.path.exists(output_path)}")
            
            # レスポンス生成
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
                return jsonify(response)
            else:
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=f'cloned_voice_{emotion}.wav',
                    mimetype='audio/wav'
                )
                
        finally:
            # 一時ファイル削除
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
    
    except ValidationError as e:
        logger.warning(f"Validation error in voice cloning: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except (AudioError, ServiceUnavailableError) as e:
        logger.error(f"TTS error in voice cloning: {e}")
        return jsonify({
            'error': 'cloning_error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        error = wrap_exception(e, AudioError, "Unexpected error in voice cloning")
        logger.error(f"Unexpected error in voice cloning: {error.to_dict()}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An unexpected error occurred'
        }), 500


@tts_voice_clone_bp.route('/clone-voice-enhanced', methods=['POST'])
def clone_voice_enhanced():
    """音声クローン（品質向上版）
    
    Form Data:
        text: 合成するテキスト
        audio_file: 参照音声ファイル
        emotion: 感情設定 (optional)
        language: 言語設定 (optional)
        enhance_quality: 品質向上を有効にするか (optional, default: true)
        return_url: URL返却フラグ (optional)
        display_name: カスタム名前 (optional)
    
    Returns:
        JSON response with enhanced cloned audio information or binary audio data
    """
    if not tts_service or not voice_manager:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # テキスト取得
        text = request.form.get('text', '').strip()
        if not text or len(text) > 1000:
            raise ValidationError("Text length must be between 1 and 1000 characters")
        
        # 音声ファイル取得
        if 'audio_file' not in request.files:
            raise ValidationError("Missing audio file")
        
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            raise ValidationError("No audio file selected")
        
        # パラメータ取得
        emotion = request.form.get('emotion', 'neutral')
        language = request.form.get('language', 'ja')
        enhance_quality = request.form.get('enhance_quality', 'true').lower() == 'true'
        return_url = request.form.get('return_url', 'false').lower() == 'true'
        display_name = request.form.get('display_name', '').strip()  # カスタム名前を追加
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            audio_file.save(temp_file.name)
            temp_audio_path = temp_file.name
        
        try:
            # 品質評価（オプション）
            quality_info = None
            if enhance_quality:
                try:
                    quality_evaluation = tts_service.evaluate_voice_sample_quality(temp_audio_path)
                    quality_info = {
                        'quality_score': quality_evaluation['overall_score'],
                        'suitable_for_cloning': quality_evaluation['suitable_for_cloning']
                    }
                    
                    if not quality_evaluation['suitable_for_cloning']:
                        logger.warning(f"Low quality audio detected (score: {quality_evaluation['overall_score']:.2f})")
                        
                except Exception as e:
                    logger.warning(f"Quality evaluation failed: {e}")
            
            # 音声クローン実行（品質向上版）
            logger.info(f"Enhanced voice cloning for text: '{text[:50]}...' (emotion: {emotion})")
            
            # API実行時の進捗バー無効化を確実にする
            ensure_tqdm_disabled()
            
            # 標準出力/エラー出力も抑制してtqdmの表示を完全に防ぐ
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                output_path = tts_service.clone_voice(
                    text=text,
                    reference_audio_path=temp_audio_path,
                    emotion=emotion,
                    enhance_quality=enhance_quality
                )
            
            # 参照音声をサンプルとして保存
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
            
            # 生成音声を保存
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
            
            # send_file前にパス検証（clone_voice）
            absolute_output_path = os.path.abspath(output_path)
            logger.debug(f"Sending cloned voice file: {output_path} -> absolute: {absolute_output_path}")
            logger.debug(f"File exists: {os.path.exists(output_path)}")
            
            # レスポンス生成
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
                
                return jsonify(response)
            else:
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=f'enhanced_cloned_voice_{emotion}.wav',
                    mimetype='audio/wav'
                )
                
        finally:
            # 一時ファイル削除
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
    
    except ValidationError as e:
        logger.warning(f"Validation error in enhanced voice cloning: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except (AudioError, ServiceUnavailableError) as e:
        logger.error(f"TTS error in enhanced voice cloning: {e}")
        return jsonify({
            'error': 'cloning_error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        error = wrap_exception(e, AudioError, "Unexpected error in enhanced voice cloning")
        logger.error(f"Unexpected error in enhanced voice cloning: {error.to_dict()}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An unexpected error occurred'
        }), 500


@tts_voice_clone_bp.route('/clone-voice-fast', methods=['POST'])
def clone_voice_fast():
    """高速音声クローン（シンプル版相当の性能）
    
    Request Body:
        {
            "text": "合成するテキスト",
            "reference_audio": file,  # 参照音声ファイル（multipart/form-data）
            "language": "ja",  # optional, default: "ja"
            "return_url": true  # optional, default: false
        }
    
    Returns:
        JSON response with audio file information or binary audio data
    """
    if not tts_service or not voice_manager:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # フォームデータから取得
        text = request.form.get('text', '').strip()
        language = request.form.get('language', 'ja')
        return_url = request.form.get('return_url', 'false').lower() == 'true'
        
        # 参照音声ファイル取得
        if 'reference_audio' not in request.files:
            raise ValidationError("Reference audio file is required")
        
        reference_file = request.files['reference_audio']
        if reference_file.filename == '':
            raise ValidationError("Reference audio file is required")

        # バリデーション
        if not text:
            raise ValidationError("Text is required")
        if len(text) > 1000:
            raise ValidationError("Text is too long (max 1000 characters)")

        # 音声ID生成
        audio_id = str(uuid.uuid4())
        
        # 参照音声を一時保存
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            reference_file.save(temp_file.name)
            reference_audio_path = temp_file.name

        try:
            # 高速音声クローン実行
            logger.info(f"🚀 Fast voice cloning: '{text[:50]}...' (language: {language})")
            
            ensure_tqdm_disabled()
            
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                output_path = tts_service.clone_voice_fast(
                    text=text,
                    reference_audio_path=reference_audio_path,
                    language=language
                )

            # ファイル管理
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

            # レスポンス生成
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
                return jsonify(response)
            else:
                logger.info(f"✅ Fast voice cloning completed, returning binary data: {audio_id}")
                return send_file(
                    output_path,
                    as_attachment=False,
                    download_name=f'voice_clone_fast_{audio_id}.wav',
                    mimetype='audio/wav'
                )

        finally:
            # 一時ファイル削除
            try:
                os.unlink(reference_audio_path)
            except Exception:
                pass

    except ValidationError as e:
        logger.warning(f"Fast voice cloning validation error: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
    except AudioError as e:
        logger.error(f"Fast voice cloning audio error: {e}")
        return jsonify({
            'error': 'audio_error',
            'message': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Fast voice cloning unexpected error: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Fast voice cloning failed due to internal error'
        }), 500 