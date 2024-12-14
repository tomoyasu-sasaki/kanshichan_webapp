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
def config():
    """共通の設定フィクスチャ"""
    return {
        'line': {
            'token': 'test_token',
            'user_id': 'test_user_id',
            'channel_secret': 'test_secret'
        },
        'twilio': {
            'account_sid': 'test_sid',
            'auth_token': 'test_token',
            'from_number': 'test_number',
            'to_number': 'test_number'
        },
        'conditions': {
            'absence': {'threshold_seconds': 5},
            'smartphone_usage': {'threshold_seconds': 3}
        }
    }