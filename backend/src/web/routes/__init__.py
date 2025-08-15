"""
Routes Package

分析API・行動データAPI・TTS API・モニターAPIのBlueprint定義
"""

# 分割された分析系Blueprint（analysis サブパッケージ再エクスポート）
from .analysis import (
    basic_analysis_bp,
    advanced_analysis_bp,
    prediction_analysis_bp,
    realtime_analysis_bp,
)

# 分割されたTTS系Blueprint（tts サブパッケージ再エクスポート）
from .tts import (
    tts_synthesis_bp,
    tts_voice_clone_bp,
    tts_file_bp,
    tts_emotion_bp,
    tts_streaming_bp,
    tts_system_bp,
    init_tts_services,
)

# その他のBlueprint
from .behavior import behavior_bp
from .monitor import monitor_bp
from .settings import settings_bp

__all__ = [
    # 分析系Blueprint
    'basic_analysis_bp', 'advanced_analysis_bp', 'prediction_analysis_bp', 'realtime_analysis_bp',
    # TTS系Blueprint
    'tts_synthesis_bp', 'tts_voice_clone_bp', 'tts_file_bp', 'tts_emotion_bp', 
    'tts_streaming_bp', 'tts_system_bp',
    # TTS初期化関数
    'init_tts_services',
    # その他Blueprint
    'behavior_bp', 'monitor_bp', 'settings_bp'
] 