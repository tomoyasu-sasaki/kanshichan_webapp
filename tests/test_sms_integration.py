import pytest
from unittest import mock
from src.kanshichan.core.monitor import send_sms

def test_send_sms_success():
    """SMSが正常に送信される場合の挙動をテストします。"""
    with mock.patch('monitor.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_message = mock.Mock()
        mock_message.sid = "SM1234567890"
        mock_client.messages.create.return_value = mock_message

        send_sms("テストメッセージ")  # SMS送信関数を呼び出し

        mock_client.messages.create.assert_called_once()  # SMS送信が一度呼ばれたか確認

def test_send_sms_failure():
    """SMS送信時にエラーが発生した場合のエラーハンドリングをテストします。"""
    with mock.patch('monitor.Client') as mock_client_cls, \
         mock.patch('monitor.logger') as mock_logger:
        mock_client = mock_client_cls.return_value
        mock_client.messages.create.side_effect = Exception("Twilioエラー")  # 例外を発生させる

        send_sms("テストメッセージ")  # SMS送信関数を呼び出し

        mock_client.messages.create.assert_called_once()  # SMS送信が一度呼ばれたか確認
        mock_logger.error.assert_called_once_with("Error sending SMS: Twilioエラー")  # エラーログが記録されたか確認 