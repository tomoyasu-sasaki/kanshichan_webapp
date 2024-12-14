import pytest
from unittest import mock
from linebot.v3.exceptions import InvalidSignatureError
from src.kanshichan.web.app import create_app

@pytest.fixture
def app():
    config = {
        'line': {
            'token': 'test_token',
            'user_id': 'test_user_id',
            'channel_secret': 'test_secret'
        }
    }
    return create_app(config)

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

        mock_handle.assert_called_once()
        assert response.status_code == 200
        assert response.data == b'OK'

def test_callback_invalid_signature(client):
    """無効なシグネチャを持つコールバックリクエストが適切に拒否されるかをテストします。"""
    body = '{"events": []}'
    signature = "invalid_signature"

    with mock.patch('linebot.v3.webhook.WebhookHandler.handle', 
                   side_effect=InvalidSignatureError):
        response = client.post('/callback', 
                             data=body, 
                             headers={'X-Line-Signature': signature})

        assert response.status_code == 400
  