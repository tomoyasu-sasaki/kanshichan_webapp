"""
Monitor Blueprint and service initialization
"""

from typing import Dict, Any, Optional
from datetime import datetime
from flask import Blueprint
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SimpleMonitor:
    """Monitor API用の簡素化されたMonitorラッパークラス"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = True
        self.initialized_at = datetime.utcnow()

    def start(self) -> None:
        self.is_active = True

    def stop(self) -> None:
        self.is_active = False

    def get_camera_status(self) -> str:
        return 'active' if self.is_active else 'inactive'

    def get_device_status(self) -> str:
        return 'active' if self.is_active else 'inactive'


monitor_bp = Blueprint('monitor', __name__, url_prefix='/monitor')

# Monitorインスタンス（アプリケーション初期化時に設定）
monitor_instance: Optional[SimpleMonitor] = None


def init_monitor_service(config: Dict[str, Any]) -> None:
    """Monitorサービスを初期化"""
    global monitor_instance
    try:
        monitor_instance = SimpleMonitor(config)
        logger.info("Monitor service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Monitor service: {e}")
        raise


__all__ = ['monitor_bp', 'init_monitor_service', 'monitor_instance', 'SimpleMonitor']

