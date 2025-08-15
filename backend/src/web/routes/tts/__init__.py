"""
TTS Routes Package

tts_* ルートの集約（分割後モジュール）
"""

from .synthesis import tts_synthesis_bp
from .voice_clone import tts_voice_clone_bp
from .file import tts_file_bp
from .emotion import tts_emotion_bp
from .streaming import tts_streaming_bp
from .system import tts_system_bp
from .helpers import init_tts_services

__all__ = [
    'tts_synthesis_bp',
    'tts_voice_clone_bp',
    'tts_file_bp',
    'tts_emotion_bp',
    'tts_streaming_bp',
    'tts_system_bp',
    'init_tts_services',
]

