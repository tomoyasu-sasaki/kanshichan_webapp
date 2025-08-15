"""
Monitor Routes Package

monitor ルートの分割後集約
"""

from .blueprint import monitor_bp, init_monitor_service

# エンドポイント登録
from . import status  # noqa: F401
from . import control  # noqa: F401
from . import metrics  # noqa: F401
from . import performance  # noqa: F401
from . import system_metrics  # noqa: F401

__all__ = ['monitor_bp', 'init_monitor_service']

