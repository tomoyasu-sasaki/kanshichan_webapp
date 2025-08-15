"""
Analysis Routes Package

basic/advanced/prediction/realtime 分析系Blueprintの集約（再エクスポート）
"""

from .basic import basic_analysis_bp
from .advanced import advanced_analysis_bp
from .prediction import prediction_analysis_bp
from .realtime import realtime_analysis_bp

__all__ = [
    'basic_analysis_bp',
    'advanced_analysis_bp',
    'prediction_analysis_bp',
    'realtime_analysis_bp',
]

