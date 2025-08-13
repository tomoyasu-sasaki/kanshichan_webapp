"""
TTS Service - Refactored Zonos TTSサービス

リファクタリング版：モジュール化、可読性向上、保守性向上
Zonos TTSを使用した音声合成・音声クローン機能
"""

import os
import sys
import tempfile
import warnings
import time
import contextlib
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
import torch
import torchaudio
import numpy as np
import random
import inspect

# tqdmの進捗バー表示を無効化
os.environ['TQDM_DISABLE'] = '1'
import tqdm
tqdm.tqdm.disable = True

from utils.logger import setup_logger
from utils.exceptions import AudioError, ServiceUnavailableError, wrap_exception
from .tts_config import TTSConfig
from .device_manager import DeviceManager
from .emotion_manager import EmotionManager
from .audio_processor import AudioProcessor
from .quality_evaluator import QualityEvaluator

# 埋め込みZonosへのパスを追加
EMBEDDED_ZONOS_PATH = os.path.join(os.path.dirname(__file__), 'vendor', 'zonos')
if EMBEDDED_ZONOS_PATH not in sys.path:
    sys.path.insert(0, EMBEDDED_ZONOS_PATH)

# ローカルモデルのパス設定
LOCAL_MODEL_DIR = os.path.join(EMBEDDED_ZONOS_PATH, "model")
LOCAL_CONFIG_PATH = os.path.join(LOCAL_MODEL_DIR, "config.json")
LOCAL_MODEL_PATH = os.path.join(LOCAL_MODEL_DIR, "model.safetensors")

logger = setup_logger(__name__)


class TTSService:
    """TTS音声合成サービス (リファクタリング版)
    
    Zonos TTSを使用したテキスト音声変換・音声クローン機能
    - ゼロショット音声クローン（5-30秒サンプル）
    - 感情・トーン制御
    - 多言語対応（日本語メイン）
    - 44kHz高品質音声出力
    - モジュール化による保守性向上
    """
    
    def __init__(self, config: Dict[str, Any]):
        """TTSサービス初期化
        
        Args:
            config: TTS設定辞書
        """
        # モジュール初期化
        self.tts_config = TTSConfig(config)
        self.device_manager = DeviceManager(self.tts_config)
        self.emotion_manager = EmotionManager()
        self.audio_processor = AudioProcessor(self.tts_config)
        self.quality_evaluator = QualityEvaluator()
        
        # Zonosモデル関連
        self.model = None
        self.make_cond_dict = None
        self.is_initialized = False
        
        # 高速モード設定
        self.fast_mode = config.get('tts', {}).get('fast_mode', False)
        
        logger.info(f"TTSService initialized - Model: {self.tts_config.model_name}, Device: {self.device_manager.device}, Fast Mode: {self.fast_mode}")
    
    def initialize(self) -> bool:
        """TTSモデルの初期化
        
        Returns:
            bool: 初期化成功フラグ
        """
        if self.is_initialized:
            logger.info("✅ TTS model already initialized")
            return True
        
        try:
            logger.info("🚀 TTS MODEL LOADING STARTED")
            logger.info("🔄 Initializing Zonos TTS model...")
            
            # Torch Compile最適化無効化
            logger.info("🔧 Disabling torch compile optimizations...")
            self._disable_torch_compile_optimizations()
            
            # Zonosライブラリのインポート
            logger.info("📦 Importing Zonos library...")
            try:
                # まず埋め込みコードからインポートを試みる
                logger.info("🔍 Trying embedded Zonos import...")
                from zonos.model import Zonos
                from zonos.conditioning import make_cond_dict
                logger.info("✅ Zonos library imported from embedded code")
            except ImportError:
                # 埋め込みコードのインポートに失敗した場合、インストール済みパッケージからインポート
                logger.warning("⚠️ Embedded import failed, trying installed package...")
                from zonos.model import Zonos
                from zonos.conditioning import make_cond_dict
                logger.info("✅ Zonos library imported from installed package")
            except ImportError as import_error:
                logger.error("❌ ZONOS LIBRARY IMPORT FAILED")
                error = wrap_exception(
                    import_error, ServiceUnavailableError,
                    "Zonos TTS library not available. Check embedded code or install zonos package.",
                    details={
                        'install_command': 'pip install git+https://github.com/Zyphra/Zonos.git',
                        'model_id': self.tts_config.get_model_id(),
                        'device': self.device_manager.device,
                        'embedded_path': EMBEDDED_ZONOS_PATH
                    }
                )
                logger.error(f"Zonos import error: {error.to_dict()}")
                return False
            
            # モデル読み込みとデバイス最適化
            try:
                model_id = self.tts_config.get_model_id()
                logger.info(f"📥 Loading TTS model: {model_id} on {self.device_manager.device}")
                
                # モデル読み込み開始時刻記録
                start_time = time.time()
                
                # ローカルモデルファイルのチェック
                if os.path.exists(LOCAL_CONFIG_PATH) and os.path.exists(LOCAL_MODEL_PATH):
                    logger.info(f"📂 Using local model files from: {LOCAL_MODEL_DIR}")
                    self.model = Zonos.from_local(LOCAL_CONFIG_PATH, LOCAL_MODEL_PATH, device=self.device_manager.device)
                else:
                    logger.warning(f"⚠️ Local model files not found. Downloading from HuggingFace: {model_id}")
                    # モデル読み込み
                    self.model = Zonos.from_pretrained(model_id, device=self.device_manager.device)
                
                load_time = time.time() - start_time
                logger.info(f"✅ Model loaded in {load_time:.2f} seconds")
                
                # デバイス最適化適用
                logger.info(f"⚙️ Optimizing model for {self.device_manager.device}...")
                
                optimization_start = time.time()
                self.model = self.device_manager.optimize_model_for_device(self.model)
                optimization_time = time.time() - optimization_start
                
                logger.info(f"✅ Device optimization completed in {optimization_time:.2f} seconds")
                
                self.make_cond_dict = make_cond_dict
                self.is_initialized = True
                
                total_time = time.time() - start_time
                
                logger.info(f"🎉 Zonos TTS model initialized successfully on {self.device_manager.device.upper()} (total: {total_time:.2f}s)")
                return True
                
            except Exception as e:
                # デバイスエラー時はCPUにフォールバック
                logger.warning(f"Device error detected, attempting fallback to CPU: {e}")
                
                # シンプルなCPUフォールバック
                new_device, _ = self.device_manager.handle_device_error(e, self.model)
                
                try:
                    # CPUでモデルを再ロード
                    model_id = self.tts_config.get_model_id()
                    logger.info("📥 Re-loading model on CPU...")
                    
                    fallback_start = time.time()
                    
                    # ローカルモデルファイルのチェック
                    if os.path.exists(LOCAL_CONFIG_PATH) and os.path.exists(LOCAL_MODEL_PATH):
                        logger.info(f"📂 Using local model files for CPU fallback: {LOCAL_MODEL_DIR}")
                        self.model = Zonos.from_local(LOCAL_CONFIG_PATH, LOCAL_MODEL_PATH, device='cpu')
                    else:
                        logger.warning(f"⚠️ Local model files not found. Downloading from HuggingFace for CPU fallback: {model_id}")
                        self.model = Zonos.from_pretrained(model_id, device='cpu')
                        
                    self.model = self.device_manager.optimize_model_for_device(self.model)
                    
                    self.make_cond_dict = make_cond_dict
                    self.is_initialized = True
                    
                    fallback_time = time.time() - fallback_start
                    
                    logger.info(f"🎉 TTS MODEL LOADING COMPLETED (CPU FALLBACK)")
                    logger.info(f"📊 Model: {model_id}")
                    logger.info(f"🎯 Device: CPU (fallback)")
                    logger.info(f"⏰ Fallback initialization time: {fallback_time:.2f} seconds")

                    logger.info(f"✅ Zonos TTS model initialized successfully on CPU (fallback, {fallback_time:.2f}s)")
                    return True
                    
                except Exception as fallback_error:
                    logger.error("❌ TTS MODEL LOADING COMPLETELY FAILED!")
                    logger.error(f"❌ Original error: {str(e)}")
                    logger.error(f"❌ Fallback error: {str(fallback_error)}")
                    
                    error = wrap_exception(
                        fallback_error, ServiceUnavailableError,
                        f"Failed to initialize Zonos TTS model even with CPU fallback: {model_id}",
                        details={
                            'model_id': model_id,
                            'device': self.device_manager.device,
                            'original_error': str(e),
                            'fallback_error': str(fallback_error)
                        }
                    )
                    logger.error(f"TTS initialization error with fallback: {error.to_dict()}")
                    return False
            
        except Exception as e:
            logger.error("❌ TTS MODEL LOADING FAILED!")
            logger.error(f"❌ Error: {str(e)}")
            
            error = wrap_exception(
                e, ServiceUnavailableError,
                f"Failed to initialize Zonos TTS model: {self.tts_config.get_model_id()}",
                details={
                    'model_id': self.tts_config.get_model_id(),
                    'device': self.device_manager.device
                }
            )
            logger.error(f"TTS initialization error: {error.to_dict()}")
            return False
    
    def generate_speech(self, 
                       text: str,
                       speaker_sample_path: Optional[str] = None,
                       language: Optional[str] = None,
                       emotion: str = 'neutral',
                       speed: float = 1.0,
                       pitch: float = 1.0,
                       max_frequency: int = 24000,
                       audio_quality: float = 4.0,
                       vq_score: float = 0.78,
                       output_path: Optional[str] = None,
                       # 生成パラメータ
                       cfg_scale: float = 0.8,
                       min_p: float = 0.0,
                       seed: Optional[int] = None,
                       # スタイル設定
                       breath_style: bool = False,
                       whisper_style: bool = False,
                       style_intensity: float = 0.5,
                       speaker_noised: bool = False,
                       # 処理オプション
                       noise_reduction: bool = True) -> str:
        """音声合成
        
        Args:
            text: 合成するテキスト
            speaker_sample_path: 音声クローン用サンプル音声ファイルパス
            language: 言語コード (ja, en-us, etc.)
            emotion: 感情設定 (neutral, happy, sad, angry, etc.)
            speed: 話速調整 (0.5-2.0)
            pitch: 音程調整 (0.5-2.0)
            max_frequency: 最大周波数 (8000-24000 Hz)
            audio_quality: 音質スコア目標 (1.0-5.0)
            vq_score: VQスコア (0.5-0.8)
            output_path: 出力ファイルパス（指定しない場合は自動生成）
            
            # 生成パラメータ
            cfg_scale: 条件付き確率スケール (0.0-1.5)
            min_p: 最小確率サンプリング (0.0-1.0)
            seed: 乱数シード値（再現性のため）
            
            # スタイル設定
            breath_style: 息継ぎスタイルの適用
            whisper_style: ささやきスタイルの適用
            style_intensity: スタイル適用強度 (0.1-1.0)
            speaker_noised: 話者ノイズ付与
            
            # 処理オプション
            noise_reduction: ノイズ除去適用
            
        Returns:
            str: 生成された音声ファイルのパス
        """
        if not self.is_initialized:
            if not self.initialize():
                raise ServiceUnavailableError("TTS service is not available")
        
        try:
            # パラメータ設定
            language = language or self.tts_config.default_language
            language = self.tts_config.normalize_language_code(language)
            output_path = output_path or self.audio_processor.generate_output_path()
            
            # キャッシュチェック
            cache_key = self.audio_processor.generate_cache_key(text, emotion, language, speaker_sample_path)
            cached_result = self.audio_processor.get_from_cache(cache_key)
            if cached_result:
                logger.info(f"🎯 Cache hit for audio generation: {cache_key[:8]}...")
                return cached_result
            
            # 乱数シード設定（再現性のため）
            if seed is not None and seed > 0:
                logger.info(f"🎲 シード値を設定: {seed}")
                torch.manual_seed(seed)
                np.random.seed(seed)
                random.seed(seed)
            
            # 音声合成実行
            start_time = time.time()
            result_path = self._perform_speech_generation(
                text=text, 
                speaker_sample_path=speaker_sample_path, 
                language=language, 
                emotion=emotion, 
                speed=speed, 
                pitch=pitch, 
                max_frequency=max_frequency, 
                audio_quality=audio_quality, 
                vq_score=vq_score, 
                output_path=output_path,
                cfg_scale=cfg_scale,
                min_p=min_p,
                breath_style=breath_style,
                whisper_style=whisper_style,
                style_intensity=style_intensity,
                speaker_noised=speaker_noised,
                noise_reduction=noise_reduction
            )
            generation_time = time.time() - start_time
            
            # パフォーマンス指標更新
            self.audio_processor.update_metrics(generation_time)
            
            # キャッシュに保存
            self.audio_processor.save_to_cache(cache_key, result_path)
            
            logger.info(f"🎉 音声合成完了! 総所要時間: {generation_time:.2f}秒")
            return result_path
            
        except Exception as e:
            # デバイスエラーの処理
            error_str = str(e).lower()
            if 'scatter_reduce' in error_str or 'aten::' in error_str or 'mps' in error_str:
                try:
                    logger.warning(f"🔧 Device error detected, attempting fallback: {e}")
                    new_device, _ = self.device_manager.handle_device_error(e, self.model)
                    
                    # フォールバック後のモデル再初期化が必要
                    if new_device == 'cpu' and self.device_manager.device == 'cpu':
                        logger.info("🔄 Reinitializing model on CPU after fallback...")
                        
                        # 現在のモデルを破棄
                        self.model = None
                        self.is_initialized = False
                        
                        # CPU環境でモデルを再初期化
                        if self.initialize():
                            logger.info("✅ Model successfully reinitialized on CPU")
                            # フォールバック後に再試行
                            return self.generate_speech(text, speaker_sample_path, language, emotion, speed, pitch, max_frequency, audio_quality, vq_score, output_path, cfg_scale, min_p, seed, breath_style, whisper_style, style_intensity, speaker_noised, noise_reduction)
                        else:
                            raise ServiceUnavailableError("Failed to reinitialize TTS model on CPU")
                    
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {fallback_error}")
                    raise AudioError(f"Speech generation failed even with device fallback: {str(e)}")
            
            # 通常のエラー処理
            error = wrap_exception(
                e, AudioError,
                f"Failed to generate speech for text: {text[:50]}...",
                details={
                    'text_length': len(text),
                    'language': language,
                    'emotion': emotion,
                    'speed': speed,
                    'pitch': pitch,
                    'speaker_sample': speaker_sample_path is not None,
                    'output_path': output_path
                }
            )
            logger.error(f"Speech generation error: {error.to_dict()}")
            raise AudioError(f"Speech generation failed: {str(e)}")
    
    def _perform_speech_generation(self, text: str, speaker_sample_path: Optional[str], 
                                 language: str, emotion: str, speed: float, pitch: float, 
                                 max_frequency: int, audio_quality: float, vq_score: float,
                                 output_path: str,
                                 cfg_scale: float,
                                 min_p: float,
                                 breath_style: bool,
                                 whisper_style: bool,
                                 style_intensity: float,
                                 speaker_noised: bool,
                                 noise_reduction: bool) -> str:
        """音声合成の実際の処理
        
        Args:
            text: 合成するテキスト
            speaker_sample_path: 音声サンプルパス
            language: 言語コード
            emotion: 感情設定
            speed: 話速
            pitch: 音程
            max_frequency: 最大周波数 (Hz)
            audio_quality: 音質スコア目標
            vq_score: VQスコア
            output_path: 出力パス
            
            # 生成パラメータ
            cfg_scale: 条件付き確率スケール (0.0-1.5)
            min_p: 最小確率サンプリング (0.0-1.0)
            breath_style: 息継ぎスタイルの適用
            whisper_style: ささやきスタイルの適用
            style_intensity: スタイル適用強度 (0.1-1.0)
            speaker_noised: 話者ノイズ付与
            noise_reduction: ノイズ除去適用
            
        Returns:
            str: 生成された音声ファイルのパス
        """
        with torch.no_grad():
            logger.info(f"🎵 音声合成開始: '{text[:50]}...' (言語: {language}, 感情: {emotion})")
            
            # スピーカー埋め込み生成
            speaker_embedding = None
            if speaker_sample_path and self.tts_config.enable_voice_cloning:
                logger.info("📝 スピーカー埋め込み生成中...")
                speaker_embedding = self._create_speaker_embedding(speaker_sample_path)
                logger.info("✅ スピーカー埋め込み生成完了")
            
            # 感情パラメータ準備
            logger.info("⚙️ 音声生成条件を準備中...")
            emotion_params = self.emotion_manager.prepare_emotion_parameters(emotion, speed, pitch)
            
            # 条件辞書構築
            cond_dict_params = {
                'text': text,
                'language': language,
                'fmax': max_frequency,       # 最大周波数
                'dnsmos_ovrl': audio_quality, # 音質スコア目標
                'vqscore_8': vq_score,       # VQスコア
                **emotion_params
            }
            
            # スピーカー埋め込み設定
            if speaker_embedding is not None:
                cond_dict_params['speaker'] = speaker_embedding
                
                # 話者ノイズ設定（ボイスクローン時のみ有効）
                if speaker_noised:
                    # Zonosのmake_cond_dictで処理可能なパラメータ
                    cond_dict_params['speaker_noised'] = True
                    logger.info("👤 話者ノイズを適用します")
            
            # 生成パラメータとスタイル設定をログに記録
            generation_params = {}
            
            # 生成パラメータ設定
            generation_params['cfg_scale'] = cfg_scale
            generation_params['min_p'] = min_p
            logger.info(f"⚙️ 生成パラメータ設定: CFG={cfg_scale}, Min-P={min_p}")
            
            # スタイル設定
            if breath_style:
                generation_params['breath_style'] = True
                generation_params['style_intensity'] = style_intensity
                logger.info(f"💨 息継ぎスタイルを適用します (強度: {style_intensity})")
                
            if whisper_style:
                generation_params['whisper_style'] = True
                generation_params['style_intensity'] = style_intensity
                logger.info(f"🤫 ささやきスタイルを適用します (強度: {style_intensity})")
                
            # ノイズ除去設定
            generation_params['noise_reduction'] = noise_reduction
            if noise_reduction:
                logger.info("🔇 ノイズ除去を適用します")
            
            # コンディショニング準備（パラメータは直接make_cond_dictに渡せるものだけを渡す）
            cond_dict = self.make_cond_dict(**cond_dict_params)
            cond_dict = self._ensure_conditioning_device_consistency(cond_dict)
            conditioning = self.model.prepare_conditioning(cond_dict)
            logger.info("✅ 音声生成条件の準備完了")
            
            # 音声生成（進捗バー抑制）
            logger.info("🚀 Zonos TTSモデルによる音声生成中...")
            generation_start = time.time()
            
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()), \
                 warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # モデル生成時に追加パラメータを渡す
                generate_params = {}
                
                # CFGスケールをモデル生成パラメータとして渡す（サポートされている場合）
                if hasattr(self.model, 'generate') and 'cfg_scale' in inspect.signature(self.model.generate).parameters:
                    generate_params['cfg_scale'] = cfg_scale
                    
                # Min-Pをモデル生成パラメータとして渡す（サポートされている場合）
                if hasattr(self.model, 'generate') and 'min_p' in inspect.signature(self.model.generate).parameters:
                    generate_params['min_p'] = min_p
                
                # モデル生成実行
                if generate_params:
                    logger.info(f"🔧 生成パラメータ適用: {generate_params}")
                    codes = self.model.generate(conditioning, **generate_params)
                else:
                    # 追加パラメータをサポートしていない場合は通常通り生成
                    logger.info("ℹ️ 標準パラメータで生成します")
                    codes = self.model.generate(conditioning)
            
            generation_time = time.time() - generation_start
            logger.info(f"✅ 音声コード生成完了 (所要時間: {generation_time:.2f}秒)")
            
            # デコードして音声波形を取得
            logger.info("🎶 音声波形デコード中...")
            wavs = self.model.autoencoder.decode(codes).cpu()
            logger.info("✅ 音声波形デコード完了")
        
        # ファイル保存
        logger.info(f"💾 音声ファイル保存中: {output_path}")
        torchaudio.save(output_path, wavs[0], self.model.autoencoder.sampling_rate)
        
        # 保存検証
        if not os.path.exists(output_path):
            raise AudioError(f"Generated audio file not found: {output_path}")
        
        file_size = os.path.getsize(output_path)
        logger.info(f"📁 保存完了: {output_path} (サイズ: {file_size} bytes)")
        
        return output_path
    
    def _create_speaker_embedding(self, audio_path: str) -> torch.Tensor:
        """スピーカー埋め込みを作成
        
        Args:
            audio_path: 音声ファイルパス
            
        Returns:
            torch.Tensor: スピーカー埋め込み
        """
        try:
            with torch.no_grad():
                wav, sampling_rate = torchaudio.load(audio_path)
                
                # デバイス一貫性の確保
                wav = self.device_manager.ensure_tensor_device_consistency(wav, self.model)
                
                speaker_embedding = self.model.make_speaker_embedding(wav, sampling_rate)
                logger.info(f"Speaker embedding created from: {audio_path}")
                return speaker_embedding
            
        except Exception as e:
            error = wrap_exception(
                e, AudioError,
                f"Failed to create speaker embedding from: {audio_path}",
                details={
                    'audio_path': audio_path,
                    'exists': os.path.exists(audio_path) if audio_path else False
                }
            )
            logger.error(f"Speaker embedding error: {error.to_dict()}")
            raise AudioError(f"Failed to create speaker embedding: {str(e)}")
    
    def _ensure_conditioning_device_consistency(self, cond_dict: Dict[str, Any]) -> Dict[str, Any]:
        """条件辞書内のテンソルのデバイス一貫性を確保
        
        Args:
            cond_dict: 条件辞書
            
        Returns:
            Dict[str, Any]: デバイス一貫性が確保された条件辞書
        """
        if not self.is_initialized or self.model is None:
            return cond_dict
            
        try:
            for key, value in cond_dict.items():
                if isinstance(value, torch.Tensor):
                    # MPSデバイスの場合はfloat16に統一（BF16/F16混在問題の回避）
                    if self.device_manager.device == 'mps':
                        # bfloat16が含まれている場合は特別な処理
                        if hasattr(value, 'dtype') and value.dtype == torch.bfloat16:
                            # 一度float32に変換してからfloat16に変換（直接の変換はエラーになる）
                            cond_dict[key] = value.to(dtype=torch.float32).to(self.device_manager.device, dtype=torch.float16)
                        else:
                            cond_dict[key] = self.device_manager.ensure_tensor_device_consistency(value, self.model)
                        
                        # 型の確認と記録
                        if hasattr(cond_dict[key], 'dtype'):
                            logger.debug(f"Tensor '{key}' dtype: {cond_dict[key].dtype}")
                    else:
                        cond_dict[key] = self.device_manager.ensure_tensor_device_consistency(value, self.model)
                        
            return cond_dict
        except Exception as e:
            logger.warning(f"Failed to ensure conditioning device consistency: {str(e)}")
            return cond_dict
    
    def _disable_torch_compile_optimizations(self) -> None:
        """Torch Compileの最適化を無効化"""
        try:
            import torch._dynamo
            torch._dynamo.config.disable = True
            torch._dynamo.config.suppress_errors = True
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            logger.debug("Torch compile optimizations disabled for stable inference")
        except Exception as e:
            logger.warning(f"Failed to disable torch compile optimizations: {e}")
    
    # 公開API（既存インターフェース維持）
    def clone_voice(self, text: str, reference_audio_path: str, emotion: str = 'neutral',
                   output_path: Optional[str] = None, enhance_quality: bool = True) -> str:
        """音声クローン（特化版）
        
        Args:
            text: 合成するテキスト
            reference_audio_path: 参照音声ファイルパス（5-30秒推奨）
            emotion: 感情設定
            output_path: 出力ファイルパス
            enhance_quality: 音声品質向上処理を有効にするか
            
        Returns:
            str: 生成された音声ファイルのパス
        """
        if not self.tts_config.enable_voice_cloning:
            raise ServiceUnavailableError("Voice cloning is disabled")
        
        # 参照音声の検証
        self.audio_processor.validate_reference_audio(reference_audio_path)
        
        # 音声品質向上の前処理
        processed_audio_path = reference_audio_path
        if enhance_quality:
            try:
                processed_audio_path = self.audio_processor.preprocess_reference_audio(reference_audio_path)
                logger.info(f"Using enhanced audio for voice cloning: {processed_audio_path}")
            except Exception as e:
                logger.warning(f"Audio enhancement failed, using original: {e}")
                processed_audio_path = reference_audio_path
        
        try:
            result = self.generate_speech(
                text=text,
                speaker_sample_path=processed_audio_path,
                emotion=emotion,
                output_path=output_path
            )
            
            # 前処理済みファイルの削除
            if processed_audio_path != reference_audio_path and os.path.exists(processed_audio_path):
                try:
                    os.unlink(processed_audio_path)
                    logger.debug(f"Cleaned up preprocessed audio: {processed_audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup preprocessed audio: {e}")
            
            return result
            
        except Exception as e:
            # エラー時も前処理済みファイルを削除
            if processed_audio_path != reference_audio_path and os.path.exists(processed_audio_path):
                try:
                    os.unlink(processed_audio_path)
                except Exception:
                    pass
            raise
    
    # 感情制御API
    def create_custom_emotion(self, **kwargs) -> List[float]:
        """カスタム感情ベクトルを作成"""
        return self.emotion_manager.create_custom_emotion(**kwargs)
    
    def mix_emotions(self, primary_emotion: str, secondary_emotion: str, primary_weight: float = 0.7) -> List[float]:
        """感情をミキシング"""
        return self.emotion_manager.mix_emotions(primary_emotion, secondary_emotion, primary_weight)
    
    def get_available_emotions(self) -> List[str]:
        """利用可能な感情名のリストを取得"""
        return self.emotion_manager.get_available_emotions()
    
    # 品質評価API
    def evaluate_voice_sample_quality(self, audio_path: str) -> Dict[str, Any]:
        """音声サンプル品質評価"""
        return self.quality_evaluator.evaluate_voice_sample_quality(audio_path)
    
    # キャッシュ・メンテナンスAPI
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """古いキャッシュファイルを削除"""
        return self.audio_processor.cleanup_old_files(max_age_hours)
    
    def clear_audio_cache(self) -> int:
        """音声キャッシュをクリア"""
        return self.audio_processor.clear_cache()
    
    # 非同期API
    async def generate_speech_async(self, text: str, **kwargs) -> str:
        """非同期音声生成"""
        return await self.audio_processor.generate_audio_async(self.generate_speech, text, **kwargs)
    
    # 情報取得API
    def get_supported_languages(self) -> List[str]:
        """サポート言語を取得"""
        return self.tts_config.get_supported_languages()
    
    def get_service_status(self) -> Dict[str, Any]:
        """サービス状態を取得"""
        status = {
            'initialized': self.is_initialized,
            'model_name': self.tts_config.model_name,
            'device_info': self.device_manager.get_device_info(),
            'voice_cloning_enabled': self.tts_config.enable_voice_cloning,
            'default_language': self.tts_config.default_language,
            'config': self.tts_config.to_dict(),
            'supported_languages': self.get_supported_languages(),
            'available_emotions': self.get_available_emotions()
        }
        
        return status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンス指標を取得"""
        metrics = self.audio_processor.get_performance_metrics()
        metrics['device_info'] = self.device_manager.get_device_info()
        metrics['emotion_info'] = self.emotion_manager.get_emotion_info()
        return metrics
    
    def generate_speech_fast(self, 
                           text: str,
                           speaker_sample_path: Optional[str] = None,
                           language: Optional[str] = None,
                           emotion: str = 'neutral',
                           speed: float = 1.0,
                           pitch: float = 1.0,
                           max_frequency: int = 24000,
                           audio_quality: float = 4.0,
                           vq_score: float = 0.78,
                           output_path: Optional[str] = None,
                           # 生成パラメータ
                           cfg_scale: float = 0.8,
                           min_p: float = 0.0,
                           seed: Optional[int] = None,
                           # スタイル設定
                           breath_style: bool = False,
                           whisper_style: bool = False,
                           style_intensity: float = 0.5,
                           speaker_noised: bool = False,
                           # 処理オプション
                           noise_reduction: bool = True) -> str:
        """高速モード音声合成
        
        Args:
            text: 合成するテキスト
            speaker_sample_path: 音声クローン用サンプル音声ファイルパス
            language: 言語コード (ja, en-us, etc.)
            emotion: 感情設定 (neutral, happy, sad, angry, etc.)
            speed: 話速調整 (0.5-2.0)
            pitch: 音程調整 (0.5-2.0)
            max_frequency: 最大周波数 (8000-24000 Hz)
            audio_quality: 音質スコア目標 (1.0-5.0)
            vq_score: VQスコア (0.5-0.8)
            output_path: 出力ファイルパス（指定しない場合は自動生成）
            
            # 生成パラメータ
            cfg_scale: 条件付き確率スケール (0.0-1.5)
            min_p: 最小確率サンプリング (0.0-1.0)
            seed: 乱数シード値（再現性のため）
            
            # スタイル設定
            breath_style: 息継ぎスタイルの適用
            whisper_style: ささやきスタイルの適用
            style_intensity: スタイル適用強度 (0.1-1.0)
            speaker_noised: 話者ノイズ付与
            
            # 処理オプション
            noise_reduction: ノイズ除去適用
            
        Returns:
            str: 生成された音声ファイルのパス
        """
        # クイックチェック
        if speaker_sample_path:
            logger.warning("高速モードではボイスクローン機能の一部に制限があります")
        
        # 標準の音声合成関数に委譲し、高速化用の設定を適用
        return self.generate_speech(
            text=text,
            speaker_sample_path=speaker_sample_path,
            language=language,
            emotion=emotion,
            speed=speed,
            pitch=pitch,
            max_frequency=max_frequency,
            audio_quality=audio_quality,
            vq_score=vq_score,
            output_path=output_path,
            cfg_scale=cfg_scale,
            min_p=min_p,
            seed=seed,
            breath_style=breath_style,
            whisper_style=whisper_style,
            style_intensity=style_intensity,
            speaker_noised=speaker_noised,
            noise_reduction=noise_reduction
        )
    
    def clone_voice_fast(self, text: str, reference_audio_path: str, 
                        language: Optional[str] = None, 
                        emotion: str = 'neutral',
                        speed: float = 1.0,
                        pitch: float = 1.0,
                        max_frequency: int = 24000,
                        audio_quality: float = 4.0,
                        vq_score: float = 0.78,
                        output_path: Optional[str] = None) -> str:
        """高速音声クローン（シンプル版相当）
        
        Args:
            text: 合成するテキスト
            reference_audio_path: 参照音声ファイルパス
            language: 言語コード
            emotion: 感情設定
            speed: 話速調整 (0.5-2.0)
            pitch: 音程調整 (0.5-2.0)
            max_frequency: 最大周波数 (8000-24000 Hz)
            audio_quality: 音質スコア目標 (1.0-5.0)
            vq_score: VQスコア (0.5-0.8)
            output_path: 出力ファイルパス
            
        Returns:
            str: 生成された音声ファイルのパス
        """
        return self.generate_speech_fast(
            text=text,
            speaker_sample_path=reference_audio_path,
            language=language,
            emotion=emotion,
            speed=speed,
            pitch=pitch,
            max_frequency=max_frequency,
            audio_quality=audio_quality,
            vq_score=vq_score,
            output_path=output_path
        ) 