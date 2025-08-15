"""
Behavior Routes Package

分割後の behavior ルートを集約
"""

from .blueprint import behavior_bp

# エンドポイント登録のためのモジュール読み込み
from . import logs  # noqa: F401
from . import stats  # noqa: F401
from . import exports  # noqa: F401
from . import dashboard  # noqa: F401

__all__ = ['behavior_bp']

