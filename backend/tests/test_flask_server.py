import pytest
from unittest import mock
from linebot.v3.exceptions import InvalidSignatureError
from flask import Flask
import json
from web.app import create_app
from web.api import api
from utils.config_manager import ConfigManager
from unittest.mock import MagicMock

@pytest.fixture
def app():
    mock_config_manager = MagicMock(spec=ConfigManager)
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'line.enabled': True,
        'line.channel_secret': 'test_secret',
        'line.token': 'test_token'
    }.get(key, default)

    test_app = create_app(mock_config_manager)
    test_app.config['TESTING'] = True
    mock_monitor = MagicMock(spec='core.monitor.Monitor')
    test_app.config['monitor_instance'] = mock_monitor
    test_app.config['config_manager'] = mock_config_manager
    return test_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_callback_valid_signature(client):
    """有効なシグネチャを持つコールバックリクエストが正しく処理されるかをテストします。"""
    body = '{"events": [{"type": "message", "message": {"type": "text", "text": "テスト"}}]}'
    signature = "valid_signature"

    with mock.patch('linebot.v3.webhook.WebhookHandler.handle') as mock_handle:
        response = client.post('/callback',
                             data=body,
                             headers={'X-Line-Signature': signature})

        mock_handle.assert_called_once_with(body, signature)
        assert response.status_code == 200
        assert response.data == b'OK'

def test_callback_invalid_signature(client):
    """無効なシグネチャを持つコールバックリクエストが適切に拒否されるかをテストします。"""
    body = '{"events": []}'
    signature = "invalid_signature"

    with mock.patch('linebot.v3.webhook.WebhookHandler.handle',
                   side_effect=InvalidSignatureError("Invalid signature")) as mock_handle:
        response = client.post('/callback',
                             data=body,
                             headers={'X-Line-Signature': signature})
        mock_handle.assert_called_once_with(body, signature)
        assert response.status_code == 400
  