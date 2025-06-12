"""
TTS Synthesis API Routes - 音声合成API

テキスト音声合成機能のAPIエンドポイント群
基本合成、高速合成、高度合成機能を提供
"""

import os
import logging
import tempfile
import uuid
import contextlib
import io
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file

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
from .tts_helpers import ensure_tqdm_disabled, get_backend_path

logger = setup_logger(__name__)

# Blueprint定義
tts_synthesis_bp = Blueprint('tts_synthesis', __name__, url_prefix='/api/tts')

# サービスインスタンス（tts_helpers.pyで初期化）
tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_synthesis_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    """音声合成サービスの初期化
    
    Args:
        tts_svc: TTSServiceインスタンス
        vm: VoiceManagerインスタンス
    """
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_synthesis_bp.route('/synthesize', methods=['POST'])
def synthesize_speech():
    """テキスト音声合成
    
    Request Body:
        {
            "text": "合成するテキスト",
            "language": "ja",  # optional, default: "ja"
            "emotion": "neutral",  # optional, default: "neutral"
            "speed": 1.0,  # optional, default: 1.0
            "pitch": 1.0,  # optional, default: 1.0
            "speaker_sample_id": "file_id",  # optional, for voice cloning
            "return_url": true,  # optional, default: false
            "save_to_cache": true,  # optional, default: true
            "stream_to_clients": false,  # optional, WebSocket配信するか
            "target_clients": []  # optional, 特定クライアントID配信
            
            # 以下、新規パラメータ
            "cfg_scale": 0.8,  # optional, 条件付き確率スケール
            "min_p": 0.0,  # optional, 最小確率サンプリング
            "seed": 1234,  # optional, 乱数シード値
            "audio_prefix": "えっと、",  # optional, 音声プレフィックス
            "breath_style": true,  # optional, 息継ぎスタイル
            "whisper_style": false,  # optional, ささやきスタイル
            "style_intensity": 0.5,  # optional, スタイル強度
            "noise_reduction": true,  # optional, ノイズ除去
            "stream_playback": false,  # optional, ストリーミング再生
            "speaker_noised": false,  # optional, 話者ノイズ付与
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
        # リクエストデータ取得
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
        target_clients = data.get('target_clients', [])
        
        # 音質パラメータを取得
        max_frequency = int(data.get('max_frequency', 24000))  # fmax: 最大周波数
        audio_quality = float(data.get('audio_quality', 4.0))  # dnsmos_ovrl: 音質スコア
        vq_score = float(data.get('vq_score', 0.78))          # vqscore_8: VQスコア
        
        # 新規パラメータを取得
        cfg_scale = float(data.get('cfg_scale', 0.8))
        min_p = float(data.get('min_p', 0.0))
        seed = int(data.get('seed', 0)) if data.get('seed') is not None else None
        audio_prefix = data.get('audio_prefix')
        breath_style = data.get('breath_style', False)
        whisper_style = data.get('whisper_style', False)
        style_intensity = float(data.get('style_intensity', 0.5))
        noise_reduction = data.get('noise_reduction', True)
        stream_playback = data.get('stream_playback', False)
        speaker_noised = data.get('speaker_noised', False)
        
        # 音声モードの明示的な指定をチェック
        tts_mode = data.get('tts_mode', False)
        voice_clone_mode = data.get('voice_clone_mode', False)

        # バリデーション
        if not text:
            raise ValidationError("Text is required")
        if len(text) > 1000:
            raise ValidationError("Text is too long (max 1000 characters)")

        # オーディオプレフィックスの処理
        if audio_prefix and audio_prefix.strip():
            # 空白を除去して先頭に追加
            text = f"{audio_prefix.strip()} {text}"
            logger.info(f"Added audio prefix: '{audio_prefix.strip()}'")

        # 音声ID生成
        audio_id = str(uuid.uuid4())
        
        # TTS開始通知
        if stream_to_clients and get_connected_clients_count() > 0:
            broadcast_audio_notification(
                'tts_started',
                f'音声合成を開始: {text[:50]}...',
                audio_id
            )

        # 音声クローン用のサンプル音声パス取得
        speaker_sample_path = None
        
        # TTS標準モードが明示的に指定されている場合はボイスクローンを無効化
        if tts_mode:
            logger.info(f"🎵 TTS標準モード明示指定 - ボイスクローンを無効化")
            speaker_sample_path = None
        elif voice_clone_mode and speaker_sample_id:
            logger.info(f"🎭 ボイスクローンモード明示指定")
            if speaker_sample_id == 'default_sample':
                # デフォルト音声サンプル（sample.wav）を使用
                default_sample_path = get_backend_path() / 'voice_data/voice_samples/sample.wav'
                if default_sample_path.exists():
                    speaker_sample_path = str(default_sample_path)
                    logger.info("Using default voice sample: sample.wav")
                else:
                    logger.warning("Default sample.wav not found, proceeding without voice cloning")
            else:
                try:
                    speaker_sample_path, _ = voice_manager.get_audio_file(speaker_sample_id)
                    logger.info(f"Using voice sample: {speaker_sample_id}")
                except FileNotFoundError as e:
                    logger.warning(f"Voice sample not found: {speaker_sample_id}, proceeding without voice cloning")
                    speaker_sample_path = None
                except Exception as e:
                    logger.error(f"Error loading voice sample {speaker_sample_id}: {e}, proceeding without voice cloning")
                    speaker_sample_path = None
        elif speaker_sample_id:
            # 従来の互換性のための処理（モード指定なしで speaker_sample_id がある場合）
            logger.info(f"🔄 レガシーモード - speaker_sample_id による自動判定")
            if speaker_sample_id == 'default_sample':
                # デフォルト音声サンプル（sample.wav）を使用
                default_sample_path = get_backend_path() / 'voice_data/voice_samples/sample.wav'
                if default_sample_path.exists():
                    speaker_sample_path = str(default_sample_path)
                    logger.info("Using default voice sample: sample.wav")
                else:
                    logger.warning("Default sample.wav not found, proceeding without voice cloning")
            else:
                try:
                    speaker_sample_path, _ = voice_manager.get_audio_file(speaker_sample_id)
                    logger.info(f"Using voice sample: {speaker_sample_id}")
                except FileNotFoundError as e:
                    logger.warning(f"Voice sample not found: {speaker_sample_id}, proceeding without voice cloning")
                    speaker_sample_path = None
                except Exception as e:
                    logger.error(f"Error loading voice sample {speaker_sample_id}: {e}, proceeding without voice cloning")
                    speaker_sample_path = None

        # 音声合成実行
        processing_mode = "TTS標準" if speaker_sample_path is None else "ボイスクローン"
        logger.info(f"Synthesizing speech: '{text[:50]}...' (emotion: {emotion}, language: {language}, mode: {processing_mode})")
        
        # API実行時の進捗バー無効化を確実にする
        ensure_tqdm_disabled()
        
        # 標準出力/エラー出力も抑制してtqdmの表示を完全に防ぐ
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            
            # 追加パラメータの設定
            advanced_params = {}
            
            # CFGスケールとMin-P（新規パラメータ）
            advanced_params['cfg_scale'] = cfg_scale
            advanced_params['min_p'] = min_p
            
            # スタイル設定
            if breath_style:
                advanced_params['breath_style'] = breath_style
                advanced_params['style_intensity'] = style_intensity
                
            if whisper_style:
                advanced_params['whisper_style'] = whisper_style
                advanced_params['style_intensity'] = style_intensity
            
            # 話者ノイズ設定
            if speaker_sample_path:
                if speaker_noised:
                    style_params = {'speaker_noised': True}
                else:
                    style_params = {}
            else:
                style_params = {}
            
            # 音声処理オプション
            advanced_params['noise_reduction'] = noise_reduction
            
            # シード設定
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
                **advanced_params
            )

        # TTS完了通知
        if stream_to_clients and get_connected_clients_count() > 0:
            broadcast_audio_notification(
                'tts_completed',
                f'音声合成が完了: {text[:50]}...',
                audio_id
            )

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
                    'synthesis_timestamp': datetime.now().isoformat()
                }
            )

        # WebSocket配信の実行
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
                'synthesis_timestamp': datetime.now().isoformat()
            }
            
            # 音声配信キューに追加
            queue_audio_for_streaming(output_path, stream_metadata)
            
            logger.info(f"Audio queued for WebSocket streaming: {audio_id}")
        
        # レスポンス形式選択
        if return_url:
            # ファイル情報を返す
            file_size = os.path.getsize(output_path)
            response = {
                'success': True,
                'audio_id': audio_id,
                'file_id': file_id,
                'file_size': file_size,
                'duration': None,  # 実装時に音声長を計算可能
                'streamed': stream_to_clients,
                'connected_clients': get_connected_clients_count(),
                'parameters': {
                    'text': text,
                    'language': language,
                    'emotion': emotion,
                    'speed': speed,
                    'pitch': pitch,
                    'voice_cloned': speaker_sample_path is not None
                }
            }
            return jsonify(response)
        else:
            # send_file前にパス検証
            absolute_output_path = os.path.abspath(output_path)
            logger.debug(f"Sending file: {output_path} -> absolute: {absolute_output_path}")
            logger.debug(f"File exists: {os.path.exists(output_path)}")
            
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f'speech_{emotion}_{language}.wav',
                mimetype='audio/wav'
            )
    
    except ValidationError as e:
        logger.warning(f"Validation error in speech synthesis: {e}")
        
        # エラー通知
        if stream_to_clients:
            broadcast_audio_notification(
                'tts_error',
                f'音声合成エラー: {str(e)}',
                audio_id if 'audio_id' in locals() else None
            )
        
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except (AudioError, ServiceUnavailableError) as e:
        logger.error(f"TTS error in speech synthesis: {e}")
        
        # エラー通知
        if stream_to_clients:
            broadcast_audio_notification(
                'tts_error',
                f'音声合成エラー: {str(e)}',
                audio_id if 'audio_id' in locals() else None
            )
        
        return jsonify({
            'error': 'synthesis_error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in speech synthesis: {e}")
        
        # エラー通知
        if stream_to_clients:
            broadcast_audio_notification(
                'tts_error',
                f'予期しないエラー: {str(e)}',
                audio_id if 'audio_id' in locals() else None
            )
        
        return jsonify({
            'error': 'internal_error',
            'message': 'An unexpected error occurred'
        }), 500


@tts_synthesis_bp.route('/synthesize-fast', methods=['POST'])
def synthesize_speech_fast():
    """高速版テキスト音声合成
    
    Request Body:
        {
            "text": "合成するテキスト",
            "language": "ja",  # optional, default: "ja"
            "emotion": "neutral",  # optional, default: "neutral"
            "speed": 1.0,  # optional, default: 1.0
            "pitch": 1.0,  # optional, default: 1.0
            "speaker_sample_id": "file_id",  # optional, for voice cloning
            "return_url": true,  # optional, default: false
            
            # 以下、新規パラメータ
            "cfg_scale": 0.8,  # optional, 条件付き確率スケール
            "min_p": 0.0,  # optional, 最小確率サンプリング
            "seed": 1234,  # optional, 乱数シード値
            "audio_prefix": "えっと、",  # optional, 音声プレフィックス
            "breath_style": true,  # optional, 息継ぎスタイル
            "whisper_style": false,  # optional, ささやきスタイル
            "style_intensity": 0.5,  # optional, スタイル強度
            "noise_reduction": true,  # optional, ノイズ除去
            "stream_playback": false,  # optional, ストリーミング再生
            "speaker_noised": false,  # optional, 話者ノイズ付与
        }
    
    Returns:
        Binary audio data
    """
    if not tts_service or not voice_manager:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        # リクエストデータ取得（シンプル版）
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'ja')
        emotion = data.get('emotion', 'neutral')
        speed = float(data.get('speed', 1.0))
        pitch = float(data.get('pitch', 1.0))
        speaker_sample_id = data.get('speaker_sample_id')
        return_url = data.get('return_url', False)
        
        # 音質パラメータを取得
        max_frequency = int(data.get('max_frequency', 24000))  # fmax: 最大周波数
        audio_quality = float(data.get('audio_quality', 4.0))  # dnsmos_ovrl: 音質スコア
        vq_score = float(data.get('vq_score', 0.78))          # vqscore_8: VQスコア
        
        # 新規パラメータを取得
        cfg_scale = float(data.get('cfg_scale', 0.8))
        min_p = float(data.get('min_p', 0.0))
        seed = int(data.get('seed', 0)) if data.get('seed') is not None else None
        audio_prefix = data.get('audio_prefix')
        breath_style = data.get('breath_style', False)
        whisper_style = data.get('whisper_style', False)
        style_intensity = float(data.get('style_intensity', 0.5))
        noise_reduction = data.get('noise_reduction', True)
        stream_playback = data.get('stream_playback', False)
        speaker_noised = data.get('speaker_noised', False)

        # バリデーション（最小限）
        if not text:
            raise ValidationError("Text is required")
        if len(text) > 1000:
            raise ValidationError("Text is too long (max 1000 characters)")

        # オーディオプレフィックスの処理
        if audio_prefix and audio_prefix.strip():
            # 空白を除去して先頭に追加
            text = f"{audio_prefix.strip()} {text}"
            logger.info(f"Added audio prefix: '{audio_prefix.strip()}'")

        # 音声クローン用のサンプル音声パス取得
        speaker_sample_path = None
        if speaker_sample_id:
            if speaker_sample_id == 'default_sample':
                # デフォルト音声サンプル（sample.wav）を使用
                default_sample_path = get_backend_path() / 'voice_data/voice_samples/sample.wav'
                if default_sample_path.exists():
                    speaker_sample_path = str(default_sample_path)
                    logger.info("Using default voice sample: sample.wav")
                else:
                    logger.warning("Default sample.wav not found, proceeding without voice cloning")
            else:
                try:
                    speaker_sample_path, _ = voice_manager.get_audio_file(speaker_sample_id)
                    logger.info(f"Using voice sample: {speaker_sample_id}")
                except Exception as e:
                    logger.warning(f"Voice sample error: {e}, proceeding without voice cloning")
                    speaker_sample_path = None

        # 音声合成実行（高速モード）
        logger.info(f"Fast synthesizing speech: '{text[:30]}...' (emotion: {emotion})")
        
        # API実行時の進捗バー無効化を確実にする
        ensure_tqdm_disabled()
        
        # 標準出力/エラー出力も抑制してtqdmの表示を完全に防ぐ
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            
            # 追加パラメータの設定
            advanced_params = {}
            
            # CFGスケールとMin-P（新規パラメータ）
            advanced_params['cfg_scale'] = cfg_scale
            advanced_params['min_p'] = min_p
            
            # スタイル設定
            if breath_style:
                advanced_params['breath_style'] = breath_style
                advanced_params['style_intensity'] = style_intensity
                
            if whisper_style:
                advanced_params['whisper_style'] = whisper_style
                advanced_params['style_intensity'] = style_intensity
            
            # 話者ノイズ設定
            if speaker_sample_path:
                if speaker_noised:
                    style_params = {'speaker_noised': True}
                else:
                    style_params = {}
            else:
                style_params = {}
            
            # 音声処理オプション
            advanced_params['noise_reduction'] = noise_reduction
            
            # シード設定
            if seed:
                advanced_params['seed'] = int(seed)
                
            output_path = tts_service.generate_speech_fast(
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
                **advanced_params
            )

        # ファイル管理（最小限）
        file_id = voice_manager.save_audio_file(
            audio_path=output_path,
            file_type='fast_cache',
            metadata={
                'audio_id': audio_id,
                'text_content': text,
                'language': language,
                'emotion': emotion,
                'speed': speed,
                'pitch': pitch,
                'fast_mode': True,
                'synthesis_timestamp': datetime.now().isoformat()
            }
        )

        # WebSocket配信（簡素化）
        if stream_to_clients and get_connected_clients_count() > 0:
            stream_metadata = {
                'audio_id': audio_id,
                'file_id': file_id,
                'text_content': text,
                'language': language,
                'emotion': emotion,
                'speed': speed,
                'pitch': pitch,
                'fast_mode': True,
                'voice_cloned': speaker_sample_path is not None,
                'synthesis_timestamp': datetime.now().isoformat()
            }
            queue_audio_for_streaming(output_path, stream_metadata)
        
        # レスポンス生成
        if return_url:
            file_size = os.path.getsize(output_path)
            response = {
                'success': True,
                'audio_id': audio_id,
                'file_id': file_id,
                'file_size': file_size,
                'fast_mode': True,
                'streamed': stream_to_clients,
                'text_content': text,
                'language': language,
                'emotion': emotion,
                'speed': speed,
                'pitch': pitch,
                'voice_cloned': speaker_sample_path is not None,
                'quality_params': {
                    'max_frequency': max_frequency,
                    'audio_quality': audio_quality,
                    'vq_score': vq_score
                }
            }
            logger.info(f"✅ Fast synthesis completed: {audio_id}")
            return jsonify(response)
        else:
            # バイナリ音声データを直接返す
            logger.info(f"✅ Fast synthesis completed, returning binary data: {audio_id}")
            return send_file(
                output_path,
                as_attachment=False,
                download_name=f'tts_fast_{audio_id}.wav',
                mimetype='audio/wav'
            )

    except ValidationError as e:
        logger.warning(f"Fast synthesis validation error: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
    except AudioError as e:
        logger.error(f"Fast synthesis audio error: {e}")
        return jsonify({
            'error': 'audio_error',
            'message': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Fast synthesis unexpected error: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Fast synthesis failed due to internal error'
        }), 500


@tts_synthesis_bp.route('/synthesize-advanced', methods=['POST'])
def synthesize_advanced_speech():
    """高度なテキスト音声合成
    
    Request Body:
        {
            "text": "合成するテキスト",
            "language": "ja",
            "emotion": "happy",  # 感情名 or カスタムベクトル
            "emotion_vector": [0.7, 0.1, 0.1, 0.0, 0.1, 0.0, 0.0, 0.0],  # optional
            "emotion_mixing": {  # optional
                "primary_emotion": "happy",
                "secondary_emotion": "excited",
                "primary_weight": 0.7
            },
            "speed": 1.0,
            "pitch": 1.0,
            "speaker_sample_id": "file_id",
            "return_url": true,
            "save_to_cache": true
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
        # リクエストデータ検証
        data = request.get_json()
        if not data or 'text' not in data:
            raise ValidationError("Missing required field: text")
        
        text = data['text'].strip()
        if not text or len(text) > 1000:
            raise ValidationError("Text length must be between 1 and 1000 characters")
        
        # 基本パラメータ取得
        language = data.get('language', 'ja')
        speed = float(data.get('speed', 1.0))
        pitch = float(data.get('pitch', 1.0))
        speaker_sample_id = data.get('speaker_sample_id')
        return_url = data.get('return_url', False)
        save_to_cache = data.get('save_to_cache', True)
        
        # パラメータ検証
        if speed < 0.5 or speed > 2.0:
            raise ValidationError("Speed must be between 0.5 and 2.0")
        if pitch < 0.5 or pitch > 2.0:
            raise ValidationError("Pitch must be between 0.5 and 2.0")
        
        # 感情パラメータの高度な処理
        emotion = 'neutral'
        emotion_info = {}
        
        if 'emotion_vector' in data:
            # カスタム感情ベクトルを直接使用
            emotion_vector = data['emotion_vector']
            if len(emotion_vector) != 8:
                raise ValidationError("emotion_vector must have exactly 8 elements")
            emotion = emotion_vector
            emotion_info['type'] = 'custom_vector'
            emotion_info['vector'] = emotion_vector
            
        elif 'emotion_mixing' in data:
            # 感情ミキシング
            mix_data = data['emotion_mixing']
            primary_emotion = mix_data.get('primary_emotion')
            secondary_emotion = mix_data.get('secondary_emotion')
            primary_weight = float(mix_data.get('primary_weight', 0.7))
            
            if not primary_emotion or not secondary_emotion:
                raise ValidationError("emotion_mixing requires primary_emotion and secondary_emotion")
            
            mixed_vector = tts_service.mix_emotions(primary_emotion, secondary_emotion, primary_weight)
            emotion = mixed_vector
            emotion_info['type'] = 'mixed'
            emotion_info['primary_emotion'] = primary_emotion
            emotion_info['secondary_emotion'] = secondary_emotion
            emotion_info['primary_weight'] = primary_weight
            emotion_info['vector'] = mixed_vector
            
        else:
            # 通常の感情名
            emotion = data.get('emotion', 'neutral')
            emotion_info['type'] = 'preset'
            emotion_info['emotion_name'] = emotion
        
        # スピーカーサンプル取得
        speaker_sample_path = None
        if speaker_sample_id:
            if speaker_sample_id == 'default_sample':
                # デフォルト音声サンプル（sample.wav）を使用
                default_sample_path = get_backend_path() / 'voice_data/voice_samples/sample.wav'
                if default_sample_path.exists():
                    speaker_sample_path = str(default_sample_path)
                    logger.info("Using default voice sample: sample.wav")
                else:
                    logger.warning("Default sample.wav not found, proceeding without voice cloning")
            else:
                try:
                    speaker_sample_path, _ = voice_manager.get_audio_file(speaker_sample_id)
                    logger.info(f"Using voice sample: {speaker_sample_id}")
                except FileNotFoundError as e:
                    logger.warning(f"Voice sample not found: {speaker_sample_id}, proceeding without voice cloning")
                    speaker_sample_path = None
                except Exception as e:
                    logger.error(f"Error loading voice sample {speaker_sample_id}: {e}, proceeding without voice cloning")
                    speaker_sample_path = None

        # 音声合成実行
        logger.info(f"Advanced speech synthesis: '{text[:50]}...' (lang: {language}, emotion: {emotion_info})")
        
        # API実行時の進捗バー無効化を確実にする
        ensure_tqdm_disabled()
        
        # 標準出力/エラー出力も抑制してtqdmの表示を完全に防ぐ
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            
            # 追加パラメータの設定
            advanced_params = {}
            
            # CFGスケールとMin-P（新規パラメータ）
            advanced_params['cfg_scale'] = cfg_scale
            advanced_params['min_p'] = min_p
            
            # スタイル設定
            if breath_style:
                advanced_params['breath_style'] = breath_style
                advanced_params['style_intensity'] = style_intensity
                
            if whisper_style:
                advanced_params['whisper_style'] = whisper_style
                advanced_params['style_intensity'] = style_intensity
            
            # 話者ノイズ設定
            if speaker_sample_path:
                speaker_noised = data.get('speaker_noised', False)
                if speaker_noised:
                    style_params = {'speaker_noised': True}
                else:
                    style_params = {}
            else:
                style_params = {}
            
            # 音声処理オプション
            advanced_params['noise_reduction'] = noise_reduction
            
            # シード設定
            seed = data.get('seed')
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
                **advanced_params
            )
        
        # 音声ファイル保存
        file_id = None
        if save_to_cache:
            file_id = voice_manager.save_audio_file(
                audio_path=output_path,
                file_type='cache',
                metadata={
                    'text_content': text,
                    'emotion_info': emotion_info,
                    'language': language,
                    'advanced_synthesis': True
                }
            )
        
        # レスポンス形式選択
        if return_url:
            file_size = os.path.getsize(output_path)
            response = {
                'success': True,
                'file_id': file_id,
                'file_size': file_size,
                'parameters': {
                    'text': text,
                    'language': language,
                    'emotion_info': emotion_info,
                    'speed': speed,
                    'pitch': pitch,
                    'voice_cloned': speaker_sample_path is not None,
                    'advanced_synthesis': True
                }
            }
            return jsonify(response)
        else:
            emotion_str = emotion_info.get('emotion_name', 'custom')
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f'advanced_speech_{emotion_str}_{language}.wav',
                mimetype='audio/wav'
            )
    
    except ValidationError as e:
        logger.warning(f"Validation error in advanced speech synthesis: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except (AudioError, ServiceUnavailableError) as e:
        logger.error(f"TTS error in advanced speech synthesis: {e}")
        return jsonify({
            'error': 'synthesis_error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in advanced speech synthesis: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'An unexpected error occurred'
        }), 500 