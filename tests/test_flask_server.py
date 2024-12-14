import pytest
from unittest import mock

from src.kanshichan.core.monitor import app, callback, monitor
from flask import Flask

@pytest.fixture
def client():
    """Flaskテストクライアントを提供するフィクスチャ。"""
    with app.test_client() as client:
        yield client

def test_callback_valid_signature(client):
    """有効なシグネチャを持つコールバックリクエストが正しく処理されるかをテストします。"""
    body = '{"events": []}'
    signature = "valid_signature"

    with mock.patch('monitor.line_handler.handle') as mock_handle:
        # リクエストヘッダーを設定
        response = client.post('/callback', data=body, headers={'X-Line-Signature': signature})

        mock_handle.assert_called_once_with(body, signature)  # ハンドラーが正しく呼ばれたか確認
        assert response.status_code == 200  # ステータスコードが200であることを確認
        assert response.data == b'OK'  # レスポンスボディが'OK'であることを確認

def test_callback_invalid_signature(client):
    """無効なシグネチャを持つコールバック���クエストが適切に拒否されるかをテストします。"""
    body = '{"events": []}'
    signature = "invalid_signature"

    with mock.patch('monitor.line_handler.handle', side_effect=monitor.InvalidSignatureError):
        # 無効なシグネチャでリクエストを送信
        response = client.post('/callback', data=body, headers={'X-Line-Signature': signature})

        assert response.status_code == 400  # ステータスコードが400であることを確認

def test_callback_exception(client):
    """コールバック処理中に例外が発生した場合でも適切に200ステータスを返すかをテストします。"""
    body = '{"events": []}'
    signature = "valid_signature"

    with mock.patch('monitor.line_handler.handle', side_effect=Exception("Unhandled Error")), \
         mock.patch('monitor.logger') as mock_logger:
        # 例外を発生させてリクエストを送信
        response = client.post('/callback', data=body, headers={'X-Line-Signature': signature})

        mock_logger.error.assert_called_with('Error handling webhook: Unhandled Error')  # エラーログが記録されたか確認
        assert response.status_code == 200  # ステータスコードが200であることを確認
        assert response.data == b'OK'  # レスポンスボディが'OK'であることを確認 