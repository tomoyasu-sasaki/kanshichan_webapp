import pytest
from unittest import mock

@pytest.fixture
def mock_line_event():
    """LINEメッセージイベントのモックを提供するフィクスチャ"""
    event = mock.Mock()
    event.message.text = "お風呂入ってくる"
    event.reply_token = "test_token"
    return event

@pytest.fixture
def mock_config():
    """設定のモックを提供するフィクスチャ"""
    return {
        'conditions': {
            'absence': {'threshold_seconds': 300},
            'smartphone_usage': {'threshold_seconds': 180}
        }
    }