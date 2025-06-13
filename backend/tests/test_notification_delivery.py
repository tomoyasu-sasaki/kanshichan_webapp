import os
import sys
from unittest.mock import patch

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.config_manager import ConfigManager
from services.communication.notification_delivery import NotificationDeliveryService
from services.communication.enums import AlertChannel


def test_email_delivery_disabled_returns_false():
    """Email チャンネルが無効な場合に False が返ることを確認"""
    cfg = ConfigManager()
    cfg.load()  # デフォルト設定読み込み

    # Email 設定を強制的に無効化
    with patch.object(ConfigManager, 'get_email_config', return_value={"enabled": False}):
        service = NotificationDeliveryService(cfg)
        result = service.deliver_notification(
            message="テストメッセージ",
            channels=[AlertChannel.EMAIL],
            subject="テスト"
        )
        assert result[AlertChannel.EMAIL] is False 