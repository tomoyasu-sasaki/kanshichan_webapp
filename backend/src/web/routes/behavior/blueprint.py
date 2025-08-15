"""
Behavior Blueprint definition
"""

from flask import Blueprint

behavior_bp = Blueprint('behavior', __name__, url_prefix='/behavior')

__all__ = ['behavior_bp']

