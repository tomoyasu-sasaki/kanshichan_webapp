"""
Services Package

KanshiChanバックエンドサービス群
- TTS音声合成サービス
- AI/ML分析サービス
- 個人化エンジン
- 監視・アラートシステム
- ストリーミング処理
- データ管理サービス
"""

# メインサービス
from .voice_manager import VoiceManager

# サブパッケージのインポート
from . import tts
from . import ai_ml
from . import personalization
from . import monitoring
from . import streaming
from . import analysis
from . import data
from . import communication
from . import automation

__all__ = [
    'VoiceManager',
    'tts',
    'ai_ml', 
    'personalization',
    'monitoring',
    'streaming',
    'analysis',
    'data',
    'communication',
    'automation'
] 