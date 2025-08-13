"""
Routes Package

分析API・行動データAPI・TTS API・モニターAPIのBlueprint定義
"""

# 分割された分析系Blueprint
from .basic_analysis_routes import basic_analysis_bp
from .advanced_analysis_routes import advanced_analysis_bp
from .prediction_analysis_routes import prediction_analysis_bp
from .realtime_analysis_routes import realtime_analysis_bp

# 分割されたTTS系Blueprint
from .tts_synthesis_routes import tts_synthesis_bp
from .tts_voice_clone_routes import tts_voice_clone_bp
from .tts_file_routes import tts_file_bp
from .tts_emotion_routes import tts_emotion_bp
from .tts_streaming_routes import tts_streaming_bp
from .tts_system_routes import tts_system_bp

# TTS共通初期化関数
from .tts_helpers import init_tts_services

# その他のBlueprint
from .behavior_routes import behavior_bp
from .monitor_routes import monitor_bp
from .settings_routes import settings_bp

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