"""
TTS Emotion Processing API Routes - 感情処理API

感情認識・処理機能のAPIエンドポイント群
基本感情、カスタム感情ベクトル、感情ミキシング、プリセット管理を提供
"""

import logging
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify

from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import ValidationError, ServiceUnavailableError, wrap_exception

logger = setup_logger(__name__)

# Blueprint定義
tts_emotion_bp = Blueprint('tts_emotion', __name__, url_prefix='/api/tts')

# サービスインスタンス（tts_helpers.pyで初期化）
tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_emotion_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    """感情処理サービスの初期化
    
    Args:
        tts_svc: TTSServiceインスタンス
        vm: VoiceManagerインスタンス
    """
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_emotion_bp.route('/emotions', methods=['GET'])
def get_available_emotions():
    """利用可能な感情設定を取得
    
    Returns:
        JSON response with available emotions
    """
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        emotions = tts_service.get_available_emotions()
        
        return jsonify({
            'success': True,
            'emotions': emotions,
            'total_count': len(emotions)
        })
        
    except Exception as e:
        logger.error(f"Error getting available emotions: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to get available emotions'
        }), 500


@tts_emotion_bp.route('/emotions/custom', methods=['POST'])
def create_custom_emotion():
    """カスタム感情ベクトル作成
    
    Request JSON:
        base_emotion: 基となる感情 (required)
        intensity: 感情の強度 0.0-1.0 (optional, default: 0.5)
        custom_vector: カスタム感情ベクトル (optional)
        name: カスタム感情名 (required)
        description: 説明 (optional)
    
    Returns:
        JSON response with custom emotion result
    """
    logger.info("🎭 Custom emotion creation request received")
    
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # リクエストデータ検証
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
        
        logger.info(f"🎭 Creating custom emotion: {name} (base: {base_emotion}, intensity: {intensity})")
        
        # カスタム感情作成
        result = tts_service.create_custom_emotion(
            base_emotion=base_emotion,
            intensity=intensity,
            custom_vector=custom_vector,
            name=name,
            description=description
        )
        
        return jsonify({
            'success': True,
            'custom_emotion': result,
            'message': f'Custom emotion "{name}" created successfully'
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in custom emotion creation: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except ServiceUnavailableError as e:
        logger.error(f"Service error in custom emotion creation: {e}")
        return jsonify({
            'error': 'service_error',
            'message': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"Error creating custom emotion: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to create custom emotion'
        }), 500


@tts_emotion_bp.route('/emotions/mix', methods=['POST'])
def mix_emotions():
    """感情ミキシング
    
    Request JSON:
        emotions: 感情リスト [{"emotion": str, "weight": float}, ...]
        normalize_weights: 重みを正規化するかどうか (optional, default: true)
        result_name: 結果の感情名 (optional)
    
    Returns:
        JSON response with mixed emotion result
    """
    logger.info("🎨 Emotion mixing request received")
    
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # リクエストデータ検証
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        
        emotions = data.get('emotions')
        if not emotions or not isinstance(emotions, list):
            raise ValidationError("emotions list is required")
        
        if len(emotions) < 2:
            raise ValidationError("At least 2 emotions are required for mixing")
        
        normalize_weights = data.get('normalize_weights', True)
        result_name = data.get('result_name', 'mixed_emotion')
        
        # 感情の重み検証
        for emotion_data in emotions:
            if not isinstance(emotion_data, dict):
                raise ValidationError("Each emotion must be an object")
            if 'emotion' not in emotion_data or 'weight' not in emotion_data:
                raise ValidationError("Each emotion must have 'emotion' and 'weight' fields")
            if not isinstance(emotion_data['weight'], (int, float)):
                raise ValidationError("Emotion weights must be numbers")
        
        logger.info(f"🎨 Mixing {len(emotions)} emotions: {[e['emotion'] for e in emotions]}")
        
        # 感情ミキシング実行
        result = tts_service.mix_emotions(
            emotions=emotions,
            normalize_weights=normalize_weights,
            result_name=result_name
        )
        
        return jsonify({
            'success': True,
            'mixed_emotion': result,
            'input_emotions': emotions,
            'message': f'Emotions mixed successfully as "{result_name}"'
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in emotion mixing: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except ServiceUnavailableError as e:
        logger.error(f"Service error in emotion mixing: {e}")
        return jsonify({
            'error': 'service_error',
            'message': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"Error mixing emotions: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to mix emotions'
        }), 500


@tts_emotion_bp.route('/emotions/presets', methods=['GET'])
def get_emotion_presets():
    """感情プリセット一覧取得
    
    Query Parameters:
        category: プリセットカテゴリ (optional)
        language: 言語フィルタ (optional)
    
    Returns:
        JSON response with emotion presets
    """
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        category = request.args.get('category')
        language = request.args.get('language')
        
        logger.info(f"🎭 Getting emotion presets (category: {category}, language: {language})")
        
        presets = tts_service.get_emotion_presets(
            category=category,
            language=language
        )
        
        return jsonify({
            'success': True,
            'presets': presets,
            'total_count': len(presets),
            'filters': {
                'category': category,
                'language': language
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting emotion presets: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to get emotion presets'
        }), 500


@tts_emotion_bp.route('/emotions/presets', methods=['POST'])
def create_emotion_preset():
    """感情プリセット作成
    
    Request JSON:
        name: プリセット名 (required)
        emotion_config: 感情設定 (required)
        category: カテゴリ (optional, default: "custom")
        language: 言語 (optional, default: "ja")
        description: 説明 (optional)
        tags: タグリスト (optional)
    
    Returns:
        JSON response with creation result
    """
    logger.info("🎭 Emotion preset creation request received")
    
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # リクエストデータ検証
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
        
        logger.info(f"🎭 Creating emotion preset: {name} (category: {category})")
        
        # プリセット作成
        result = tts_service.create_emotion_preset(
            name=name,
            emotion_config=emotion_config,
            category=category,
            language=language,
            description=description,
            tags=tags
        )
        
        return jsonify({
            'success': True,
            'preset': result,
            'message': f'Emotion preset "{name}" created successfully'
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in emotion preset creation: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except ServiceUnavailableError as e:
        logger.error(f"Service error in emotion preset creation: {e}")
        return jsonify({
            'error': 'service_error',
            'message': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"Error creating emotion preset: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to create emotion preset'
        }), 500


@tts_emotion_bp.route('/emotions/presets/<preset_id>', methods=['DELETE'])
def delete_emotion_preset(preset_id: str):
    """感情プリセット削除
    
    Args:
        preset_id: プリセットID
    
    Returns:
        JSON response with deletion result
    """
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        logger.info(f"🗑️ Deleting emotion preset: {preset_id}")
        
        success = tts_service.delete_emotion_preset(preset_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Emotion preset {preset_id} deleted successfully'
            })
        else:
            return jsonify({
                'error': 'preset_not_found',
                'message': f'Emotion preset {preset_id} not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error deleting emotion preset {preset_id}: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to delete emotion preset'
        }), 500


@tts_emotion_bp.route('/emotions/analyze', methods=['POST'])
def analyze_text_emotion():
    """テキストの感情分析
    
    Request JSON:
        text: 分析するテキスト (required)
        language: 言語 (optional, default: "ja")
        return_confidence: 信頼度を返すかどうか (optional, default: true)
    
    Returns:
        JSON response with emotion analysis result
    """
    logger.info("🔍 Text emotion analysis request received")
    
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # リクエストデータ検証
        data = request.get_json()
        if not data:
            raise ValidationError("Missing JSON data")
        
        text = data.get('text')
        if not text:
            raise ValidationError("text is required")
        
        language = data.get('language', 'ja')
        return_confidence = data.get('return_confidence', True)
        
        logger.info(f"🔍 Analyzing emotion in text: '{text[:50]}...' (language: {language})")
        
        # 感情分析実行
        result = tts_service.analyze_text_emotion(
            text=text,
            language=language,
            return_confidence=return_confidence
        )
        
        return jsonify({
            'success': True,
            'text': text,
            'analysis': result,
            'language': language
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in emotion analysis: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except ServiceUnavailableError as e:
        logger.error(f"Service error in emotion analysis: {e}")
        return jsonify({
            'error': 'service_error',
            'message': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"Error analyzing text emotion: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to analyze text emotion'
        }), 500


@tts_emotion_bp.route('/emotions/apply', methods=['POST'])
def apply_emotion_to_speech():
    """音声に感情を適用
    
    Request JSON:
        text: 音声化するテキスト (required)
        emotion: 適用する感情 (required)
        intensity: 感情の強度 0.0-1.0 (optional, default: 0.5)
        voice_sample_id: 音声サンプルID (optional)
        language: 言語 (optional, default: "ja")
    
    Returns:
        JSON response with synthesized audio file ID
    """
    logger.info("🎭 Emotion application to speech request received")
    
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # リクエストデータ検証
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
        
        logger.info(f"🎭 Applying emotion '{emotion}' (intensity: {intensity}) to text")
        
        # 感情適用音声合成実行
        result = tts_service.synthesize_with_emotion(
            text=text,
            emotion=emotion,
            intensity=intensity,
            voice_sample_id=voice_sample_id,
            language=language
        )
        
        return jsonify({
            'success': True,
            'audio_file_id': result['audio_file_id'],
            'applied_emotion': {
                'emotion': emotion,
                'intensity': intensity
            },
            'metadata': result.get('metadata', {}),
            'message': 'Emotion applied to speech successfully'
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in emotion application: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except ServiceUnavailableError as e:
        logger.error(f"Service error in emotion application: {e}")
        return jsonify({
            'error': 'service_error',
            'message': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"Error applying emotion to speech: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to apply emotion to speech'
        }), 500 