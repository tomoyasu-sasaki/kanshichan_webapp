"""
TTS File Management API Routes - ファイル管理API

音声ファイル管理機能のAPIエンドポイント群
ファイル取得、一覧表示、削除、アップロード、品質評価、プロファイル管理を提供
"""

import os
import logging
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file

from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import (
    AudioError, ServiceUnavailableError, ValidationError, 
    FileNotFoundError, wrap_exception
)
from .tts_helpers import get_tts_service, get_voice_manager

logger = setup_logger(__name__)

# Blueprint定義
tts_file_bp = Blueprint('tts_file', __name__, url_prefix='/api/tts')

# サービスインスタンス（tts_helpers.pyで初期化）
tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_file_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    """ファイル管理サービスの初期化
    
    Args:
        tts_svc: TTSServiceインスタンス
        vm: VoiceManagerインスタンス
    """
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_file_bp.route('/audio/<file_id>', methods=['GET'])
def get_audio_file(file_id: str):
    """音声ファイル取得
    
    Args:
        file_id: ファイルID
    
    Returns:
        Audio file or JSON error
    """
    if not voice_manager:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'Voice manager is not available'
        }), 503
    
    try:
        file_path, metadata = voice_manager.get_audio_file(file_id)
        
        return send_file(
            file_path,
            as_attachment=False,
            download_name=metadata.original_filename,
            mimetype='audio/wav'
        )
        
    except FileNotFoundError as e:
        return jsonify({
            'error': 'file_not_found',
            'message': str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"Error retrieving audio file {file_id}: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to retrieve audio file'
        }), 500


@tts_file_bp.route('/voices', methods=['GET'])
def list_voice_files():
    """音声ファイル一覧取得
    
    Query Parameters:
        type: ファイルタイプフィルタ (sample, generated, cache)
        user_id: ユーザーIDフィルタ
    
    Returns:
        JSON response with voice file list
    """
    if not voice_manager:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'Voice manager is not available'
        }), 503
    
    try:
        file_type = request.args.get('type')
        user_id = request.args.get('user_id')
        
        files = voice_manager.list_audio_files(
            file_type=file_type,
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        logger.error(f"Error listing voice files: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to list voice files'
        }), 500


@tts_file_bp.route('/voices/<file_id>', methods=['DELETE'])
def delete_voice_file(file_id: str):
    """音声ファイル削除
    
    Args:
        file_id: ファイルID
    
    Returns:
        JSON response with deletion result
    """
    if not voice_manager:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'Voice manager is not available'
        }), 503
    
    try:
        success = voice_manager.delete_audio_file(file_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Audio file {file_id} deleted successfully'
            })
        else:
            return jsonify({
                'error': 'file_not_found',
                'message': f'Audio file {file_id} not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error deleting audio file {file_id}: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to delete audio file'
        }), 500


@tts_file_bp.route('/upload_voice_sample', methods=['POST'])
def upload_voice_sample():
    """音声サンプルファイルのアップロード
    
    Request Form Data:
        audio_file: アップロードする音声ファイル（必須）
        text: 音声内容のテキスト（オプション）
        emotion: 感情設定（オプション、デフォルト: "neutral"）
        language: 言語設定（オプション、デフォルト: "ja"）
        custom_filename: カスタムファイル名（オプション）
        return_url: URLを返すか（オプション、デフォルト: "false"）
    
    Returns:
        JSON response with upload result
    """
    logger.info("🎵 Audio upload request received")
    
    if not voice_manager:
        logger.error("Voice Manager service is not available")
        return jsonify({
            'success': False,
            'error': 'service_unavailable',
            'message': 'Voice Manager service is not available'
        }), 503
    
    try:
        logger.info("🔍 Checking for audio file in request")
        
        # ファイルが存在するかチェック
        if 'audio_file' not in request.files:
            logger.warning("No audio_file in request.files")
            return jsonify({
                'success': False,
                'error': 'missing_file',
                'message': 'Audio file is required'
            }), 400
        
        file = request.files['audio_file']
        if file.filename == '':
            logger.warning("Empty filename provided")
            return jsonify({
                'success': False,
                'error': 'invalid_file',
                'message': 'No file selected'
            }), 400
        
        logger.info(f"📁 Processing file: {file.filename}")
        
        # フォームデータの取得
        text = request.form.get('text', '')
        emotion = request.form.get('emotion', 'neutral')
        language = request.form.get('language', 'ja')
        custom_filename = request.form.get('custom_filename', '')
        return_url = request.form.get('return_url', 'false').lower() == 'true'
        
        logger.info(f"📋 Form data: text='{text}', emotion='{emotion}', language='{language}'")
        
        # ファイルサイズチェック（10MB制限）
        file.seek(0, 2)  # ファイル末尾に移動
        file_size = file.tell()
        file.seek(0)  # ファイル先頭に戻る
        
        logger.info(f"📏 File size: {file_size} bytes")
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            logger.warning(f"File too large: {file_size} bytes")
            return jsonify({
                'success': False,
                'error': 'file_too_large',
                'message': 'File size must be less than 10MB'
            }), 413
        
        # ファイル形式チェック
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac'}
        file_ext = Path(file.filename).suffix.lower()
        logger.info(f"🎵 File extension: {file_ext}")
        
        if file_ext not in allowed_extensions:
            logger.warning(f"Invalid file format: {file_ext}")
            return jsonify({
                'success': False,
                'error': 'invalid_format',
                'message': f'Unsupported file format. Allowed: {", ".join(allowed_extensions)}'
            }), 400
        
        logger.info("💾 Saving to temporary file")
        
        # 一時ファイル保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        logger.info(f"💾 Temporary file saved: {temp_path}")
        
        try:
            # メタデータ準備
            metadata = {
                'voice_sample_for': 'user_uploaded',
                'language': language,
                'emotion': emotion,
                'upload_timestamp': datetime.now().isoformat(),
                'original_filename': file.filename
            }
            
            if text:
                metadata['text_content'] = text
            
            logger.info("📝 Metadata prepared")
            
            # ファイル名決定
            if custom_filename:
                # カスタムファイル名を使用（拡張子は元ファイルから）
                filename = f"{custom_filename}{file_ext}"
            else:
                # 元のファイル名を使用
                filename = file.filename
            
            logger.info(f"📂 Target filename: {filename}")
            
            # Voice Managerを使ってファイルを保存
            logger.info("🗃️ Calling voice_manager.save_audio_file")
            
            # カスタムファイル名はメタデータで渡す
            if custom_filename:
                metadata['display_name'] = f"{custom_filename}{file_ext}"
            
            file_id = voice_manager.save_audio_file(
                temp_path,
                file_type='sample',  # 音声サンプルとして保存
                metadata=metadata
            )
            
            logger.info(f"✅ File saved with ID: {file_id}")
            
            # 音声品質評価（TTSServiceが利用可能な場合）
            quality_score = None
            quality_details = None
            if tts_service:
                try:
                    logger.info("🔍 Evaluating voice quality")
                    quality_result = tts_service.evaluate_voice_sample_quality(temp_path)
                    quality_score = quality_result.get('overall_score', None)
                    quality_details = quality_result
                    logger.info(f"✅ Quality evaluation completed: {quality_score}")
                    
                except Exception as e:
                    logger.warning(f"Quality evaluation failed: {e}")
            
            # ファイル情報を取得（VoiceManagerから直接）
            file_info = None
            try:
                _, file_metadata = voice_manager.get_audio_file(file_id)
                file_info = file_metadata
            except Exception as e:
                logger.warning(f"Failed to get file info: {e}")
            
            result = {
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'file_size': file_size,
                'metadata': metadata,
                'quality_score': quality_score
            }
            
            if return_url and file_info:
                result['file_url'] = f"/api/tts/audio/{file_id}"
            
            if quality_details:
                result['quality_details'] = quality_details
            
            logger.info(f"Voice sample uploaded successfully: {file_id} ({filename})")
            
            return jsonify(result), 200
            
        finally:
            # 一時ファイルを削除
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {e}")
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Voice sample upload error: {e}")
        return jsonify({
            'success': False,
            'error': 'upload_failed',
            'message': 'Failed to upload voice sample'
        }), 500


@tts_file_bp.route('/evaluate-quality', methods=['POST'])
def evaluate_voice_quality():
    """音声品質評価
    
    Form Data:
        audio_file: 評価する音声ファイル
        return_recommendations: 推奨事項を返すかどうか (optional)
    
    Returns:
        JSON response with quality evaluation results
    """
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # 音声ファイル取得
        if 'audio_file' not in request.files:
            raise ValidationError("Missing audio file")
        
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            raise ValidationError("No audio file selected")
        
        # パラメータ取得
        return_recommendations = request.form.get('return_recommendations', 'true').lower() == 'true'
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            audio_file.save(temp_file.name)
            temp_audio_path = temp_file.name
        
        try:
            # 品質評価実行
            logger.info(f"Evaluating voice sample quality: {audio_file.filename}")
            
            evaluation = tts_service.evaluate_voice_sample_quality(temp_audio_path)
            
            # レスポンス形式の調整
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
            
            return jsonify(response)
            
        finally:
            # 一時ファイル削除
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
    
    except ValidationError as e:
        logger.warning(f"Validation error in quality evaluation: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except (AudioError, ServiceUnavailableError) as e:
        logger.error(f"TTS error in quality evaluation: {e}")
        return jsonify({
            'error': 'evaluation_error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        error = wrap_exception(e, AudioError, "Unexpected error in quality evaluation")
        logger.error(f"Unexpected error in quality evaluation: {error.to_dict()}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An unexpected error occurred'
        }), 500


@tts_file_bp.route('/voice-profiles', methods=['GET'])
def get_voice_profiles():
    """音声プロファイル一覧取得
    
    Query Parameters:
        user_id: ユーザーID (optional)
        quality_threshold: 品質閾値 (optional, default: 0.0)
        limit: 取得件数制限 (optional, default: 50)
    
    Returns:
        JSON response with voice profiles list
    """
    if not voice_manager:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'Voice manager service is not available'
        }), 503
    
    try:
        # クエリパラメータ取得
        user_id = request.args.get('user_id')
        quality_threshold = float(request.args.get('quality_threshold', 0.0))
        limit = int(request.args.get('limit', 50))
        
        # 音声サンプル一覧取得
        voice_samples = voice_manager.list_audio_files(
            file_type='sample',
            user_id=user_id
        )
        
        # 品質閾値でフィルタリング
        if quality_threshold > 0.0:
            voice_samples = [
                sample for sample in voice_samples 
                if sample.get('quality_score', 0.0) >= quality_threshold
            ]
        
        # 制限適用
        if limit > 0:
            voice_samples = voice_samples[:limit]
        
        # レスポンス整形
        profiles = []
        for sample in voice_samples:
            profile = {
                'file_id': sample['file_id'],
                'user_id': sample.get('voice_sample_for', 'unknown'),
                'duration_seconds': sample['duration_seconds'],
                'quality_score': sample.get('quality_score'),
                'language': sample.get('language', 'unknown'),
                'created_at': sample['created_at'],
                'suitable_for_cloning': sample.get('quality_score', 0.0) >= 0.7,
                'file_size': sample['file_size'],
                'exists': sample['exists']
            }
            profiles.append(profile)
        
        response = {
            'success': True,
            'profiles': profiles,
            'total_count': len(profiles),
            'filters': {
                'user_id': user_id,
                'quality_threshold': quality_threshold,
                'limit': limit
            }
        }
        
        return jsonify(response)
        
    except ValueError as e:
        logger.warning(f"Parameter error in voice profiles: {e}")
        return jsonify({
            'error': 'parameter_error',
            'message': 'Invalid parameter values'
        }), 400
        
    except Exception as e:
        error = wrap_exception(e, AudioError, "Unexpected error in voice profiles")
        logger.error(f"Unexpected error in voice profiles: {error.to_dict()}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An unexpected error occurred'
        }), 500 