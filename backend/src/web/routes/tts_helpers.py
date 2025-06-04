"""
TTS Helpers - TTS共通ヘルパー関数

TTS関連コンポーネントで使用される共通ヘルパー関数群
進捗バー無効化、パス取得、サービス初期化などの機能を提供
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

# グローバルサービスインスタンス
tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def ensure_tqdm_disabled():
    """API実行時にtqdmの進捗バーを確実に無効化する
    
    機械学習モデルの初期化やインファレンス時に表示される
    進捗バーを完全に無効化します。API実行時の出力を
    クリーンに保つために使用されます。
    """
    import os
    import tqdm
    
    # 環境変数による無効化
    os.environ['TQDM_DISABLE'] = '1'
    os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
    os.environ['TQDM_MININTERVAL'] = '999999'
    os.environ['TQDM_MAXINTERVAL'] = '999999'
    
    # tqdmのダミークラスで完全に置換
    class DummyTqdm:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def update(self, *args, **kwargs): pass
        def close(self): pass
        def set_description(self, *args, **kwargs): pass
        def set_postfix(self, **kwargs): pass
        def write(self, s): pass
        def clear(self): pass
        def refresh(self): pass
    
    tqdm.tqdm = DummyTqdm
    tqdm.trange = lambda *args, **kwargs: range(args[0] if args else 0)
    tqdm.tqdm.disable = True


def get_backend_path() -> Path:
    """backendディレクトリの絶対パスを取得
    
    プロジェクトのbackendディレクトリを基準とした
    絶対パスを動的に取得します。音声サンプルファイルや
    設定ファイルへのアクセスに使用されます。
    
    Returns:
        Path: backendディレクトリの絶対パス
    """
    current_file = Path(__file__).resolve()
    # src/web/routes/tts_helpers.py から backend/ への相対パス
    return current_file.parent.parent.parent.parent


def init_tts_services(config: Dict[str, Any]) -> None:
    """TTSサービスを初期化
    
    TTSService と VoiceManager のインスタンスを作成し、
    全体的な初期化処理を実行します。
    
    Args:
        config: アプリケーション設定辞書
        
    Raises:
        Exception: 初期化に失敗した場合
    """
    global tts_service, voice_manager
    
    try:
        print("\n" + "="*70)
        print("🎯 TTS SERVICE INITIALIZATION STARTED")
        print("="*70)
        
        # TTS初期化時の進捗バー無効化
        ensure_tqdm_disabled()
        logger.info("📝 TTS initialization with progress bars disabled")
        print("📝 Progress bars disabled for initialization")
        
        logger.info("🏗️ Creating TTS Service instance...")
        print("🏗️ Creating TTS Service instance...")
        tts_service = TTSService(config)
        
        logger.info("🏗️ Creating Voice Manager instance...")
        print("🏗️ Creating Voice Manager instance...")
        voice_manager = VoiceManager(config)
        
        # 強制初期化実行
        logger.info("🚀 Forcing TTS model initialization...")
        print("🚀 Forcing TTS model initialization...")
        
        init_start_time = time.time()
        
        if tts_service.initialize():
            init_total_time = time.time() - init_start_time
            
            print("\n" + "="*70)
            print("🎉 TTS SERVICE INITIALIZATION COMPLETED!")
            print(f"⏰ Total service initialization time: {init_total_time:.2f} seconds")
            print("✅ TTS Service: Ready")
            print("✅ Voice Manager: Ready")
            print("✅ Model Status: Initialized")
            print("="*70 + "\n")
            
            logger.info(f"✅ TTS services initialization completed in {init_total_time:.2f} seconds")
        else:
            print("\n" + "="*70)
            print("⚠️ TTS SERVICE INITIALIZATION PARTIALLY FAILED")
            print("❌ Model Status: Not Initialized")
            print("⚠️ Service will continue with limited functionality")
            print("="*70 + "\n")
            
            logger.warning("⚠️ TTS model initialization failed but services created")
        
        # 分割されたコンポーネントに初期化
        _initialize_tts_components()
        
        logger.info("✅ TTS services setup completed")
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ TTS SERVICE INITIALIZATION FAILED!")
        print(f"❌ Error: {str(e)}")
        print("❌ TTS functionality will be unavailable")
        print("="*70 + "\n")
        
        logger.error(f"Failed to initialize TTS services: {e}")
        raise


def _initialize_tts_components() -> None:
    """分割されたTTSコンポーネントを初期化
    
    各分割されたTTSコンポーネント（音声合成、音声クローン、
    ファイル管理、感情処理、ストリーミング、システム）に
    サービスインスタンスを渡して初期化します。
    """
    if not tts_service or not voice_manager:
        logger.warning("TTS services not available for component initialization")
        return
    
    try:
        # 音声合成コンポーネント初期化
        from .tts_synthesis_routes import init_synthesis_services
        init_synthesis_services(tts_service, voice_manager)
        logger.info("🎵 TTS Synthesis component initialized")
        
        # 音声クローンコンポーネント初期化
        from .tts_voice_clone_routes import init_voice_clone_services
        init_voice_clone_services(tts_service, voice_manager)
        logger.info("🎭 TTS Voice Clone component initialized")
        
        # ファイル管理コンポーネント初期化
        from .tts_file_routes import init_file_services
        init_file_services(tts_service, voice_manager)
        logger.info("📁 TTS File Management component initialized")
        
        # 感情処理コンポーネント初期化
        from .tts_emotion_routes import init_emotion_services
        init_emotion_services(tts_service, voice_manager)
        logger.info("😊 TTS Emotion Processing component initialized")
        
        # ストリーミングコンポーネント初期化
        from .tts_streaming_routes import init_streaming_services
        init_streaming_services(tts_service, voice_manager)
        logger.info("📡 TTS Streaming component initialized")
        
        # システム管理コンポーネント初期化
        from .tts_system_routes import init_system_services
        init_system_services(tts_service, voice_manager)
        logger.info("⚙️ TTS System Management component initialized")
        
        logger.info("🎉 All TTS components successfully initialized")
        
    except ImportError as e:
        logger.warning(f"Some TTS components not yet available: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize TTS components: {e}")
        raise


def get_tts_service() -> Optional[TTSService]:
    """TTSServiceインスタンスを取得
    
    Returns:
        TTSServiceインスタンスまたはNone
    """
    return tts_service


def get_voice_manager() -> Optional[VoiceManager]:
    """VoiceManagerインスタンスを取得
    
    Returns:
        VoiceManagerインスタンスまたはNone
    """
    return voice_manager


def check_services_available() -> bool:
    """TTSサービスの利用可能性をチェック
    
    Returns:
        bool: 両方のサービスが利用可能な場合True
    """
    return tts_service is not None and voice_manager is not None


def get_service_status() -> Dict[str, Any]:
    """TTSサービス全体の状態を取得
    
    Returns:
        Dict: サービス状態情報
    """
    return {
        'tts_service_available': tts_service is not None,
        'voice_manager_available': voice_manager is not None,
        'services_ready': check_services_available(),
        'tts_service_status': tts_service.get_service_status() if tts_service else None,
        'voice_manager_status': voice_manager.get_service_status() if voice_manager else None
    } 