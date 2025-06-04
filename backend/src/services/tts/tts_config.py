"""
TTS Configuration Manager - TTS設定管理

設定の初期化、検証、デバイス選択、最適化設定を管理
"""

import os
from typing import Dict, Any, List
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TTSConfig:
    """TTS設定管理クラス
    
    設定の初期化、検証、デバイス選択を一元管理
    """
    
    def __init__(self, config: Dict[str, Any]):
        """設定初期化
        
        Args:
            config: アプリケーション設定辞書
        """
        self.config = config
        self.tts_config = config.get('tts', {})
        
        # ディレクトリ設定
        self._setup_directories()
        
        # 基本設定
        self.model_name = self.tts_config.get('model', 'Zyphra/Zonos-v0.1-transformer')
        self.use_hybrid = self.tts_config.get('use_hybrid', False)
        self.enable_voice_cloning = self.tts_config.get('enable_voice_cloning', True)
        self.default_language = self.tts_config.get('default_language', 'ja')
        self.max_generation_length = self.tts_config.get('max_generation_length', 30)
        
        # パフォーマンス設定
        self.enable_audio_cache = self.tts_config.get('enable_audio_cache', True)
        self.cache_ttl_hours = self.tts_config.get('cache_ttl_hours', 24)
        self.max_cache_size_mb = self.tts_config.get('max_cache_size_mb', 500)
        self.enable_async_generation = self.tts_config.get('enable_async_generation', True)
        self.max_worker_threads = self.tts_config.get('max_worker_threads', 2)
        self.gpu_memory_optimization = self.tts_config.get('gpu_memory_optimization', True)
        
        # 進捗表示制御
        self.disable_progress_bars = self.tts_config.get('disable_progress_bars', True)
        self.verbose_logging = self.tts_config.get('verbose_logging', False)
        self.suppress_warnings = self.tts_config.get('suppress_warnings', True)
        
        # MPS設定
        self.enable_mps = self.tts_config.get('enable_mps', True)
        self.mps_memory_fraction = self.tts_config.get('mps_memory_fraction', 0.75)
        self.mps_half_precision = self.tts_config.get('mps_half_precision', False)
        self.debug_mps = self.tts_config.get('debug_mps', False)
        
        # 設定適用
        self._apply_environment_settings()
        
        logger.info(f"TTSConfig initialized - Model: {self.model_name}, Cache: {self.enable_audio_cache}")
    
    def _setup_directories(self) -> None:
        """ディレクトリ設定の初期化"""
        cache_dir_config = self.tts_config.get('cache_dir', 'voice_data/tts_cache')
        voice_samples_dir_config = self.tts_config.get('voice_samples_dir', 'voice_data/voice_samples')
        
        # backendディレクトリからの相対パス解決
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent.parent.parent  # services/tts/tts_config.py から backend/ への相対パス
        
        # 絶対パス or 相対パスの処理
        if Path(cache_dir_config).is_absolute():
            self.audio_cache_dir = Path(cache_dir_config)
        else:
            self.audio_cache_dir = backend_dir / cache_dir_config
            
        if Path(voice_samples_dir_config).is_absolute():
            self.voice_samples_dir = Path(voice_samples_dir_config)
        else:
            self.voice_samples_dir = backend_dir / voice_samples_dir_config
        
        # ディレクトリ作成
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)
        self.voice_samples_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Cache dir: {self.audio_cache_dir}")
        logger.debug(f"Voice samples dir: {self.voice_samples_dir}")
    
    def _apply_environment_settings(self) -> None:
        """環境変数とシステム設定の適用"""
        # 進捗バー無効化
        if self.disable_progress_bars:
            os.environ['TQDM_DISABLE'] = '1'
            os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
            os.environ['TQDM_MININTERVAL'] = '999999'
            os.environ['TQDM_MAXINTERVAL'] = '999999'
            logger.debug("Progress bars disabled")
        
        # 冗長ログ制御
        if not self.verbose_logging:
            os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
            logger.debug("Verbose logging disabled")
        
        # MPS設定
        if self.enable_mps:
            os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
            os.environ['MPS_GRAPH_CACHE_DEPTH'] = '5'
            os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.75'
            os.environ['PYTORCH_MPS_LOW_WATERMARK_RATIO'] = '0.70'
            os.environ['PYTORCH_MPS_PREFER_CPU_FALLBACK'] = '1'
            os.environ['PYTORCH_ENABLE_MPS_CPU_FALLBACK'] = '1'
            logger.debug("MPS environment configured")
        
        # デバッグ設定
        if self.debug_mps:
            os.environ['PYTORCH_VERBOSE'] = '1'
            os.environ['PYTORCH_MPS_LOG_LEVEL'] = '1'
    
    def get_model_id(self) -> str:
        """モデルIDを取得
        
        Returns:
            str: 使用するモデルID
        """
        return "Zyphra/Zonos-v0.1-hybrid" if self.use_hybrid else "Zyphra/Zonos-v0.1-transformer"
    
    def get_supported_languages(self) -> List[str]:
        """サポート言語リストを取得
        
        Returns:
            List[str]: サポート言語リスト
        """
        return ['ja', 'en-us', 'zh-cn', 'fr', 'de', 'es']
    
    def normalize_language_code(self, language: str) -> str:
        """言語コードの正規化
        
        Args:
            language: 入力言語コード
            
        Returns:
            str: 正規化された言語コード
        """
        language_mapping = {
            'ja': 'ja',
            'japanese': 'ja',
            'en': 'en-us',
            'english': 'en-us',
            'zh': 'zh-cn',
            'chinese': 'zh-cn',
            'fr': 'fr',
            'french': 'fr',
            'de': 'de',
            'german': 'de',
            'es': 'es',
            'spanish': 'es'
        }
        
        normalized = language_mapping.get(language.lower(), language)
        logger.debug(f"Language normalized: {language} -> {normalized}")
        return normalized
    
    def to_dict(self) -> Dict[str, Any]:
        """設定情報を辞書として取得
        
        Returns:
            Dict[str, Any]: 設定情報辞書
        """
        return {
            'model_name': self.model_name,
            'use_hybrid': self.use_hybrid,
            'enable_voice_cloning': self.enable_voice_cloning,
            'default_language': self.default_language,
            'enable_audio_cache': self.enable_audio_cache,
            'cache_ttl_hours': self.cache_ttl_hours,
            'max_cache_size_mb': self.max_cache_size_mb,
            'enable_async_generation': self.enable_async_generation,
            'max_worker_threads': self.max_worker_threads,
            'audio_cache_dir': str(self.audio_cache_dir),
            'voice_samples_dir': str(self.voice_samples_dir),
            'supported_languages': self.get_supported_languages()
        } 