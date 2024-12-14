import pytest
from unittest import mock
from src.kanshichan.core.monitor import play_sound_alert, send_line_message, send_sms, trigger_alert

def test_play_sound_alert():
    """指定されたサウンドファイルが正しく再生されるかをテストします。"""
    with mock.patch('monitor.sa.WaveObject.from_wave_file') as mock_wave:
        mock_play = mock.Mock()
        mock_wave.return_value.play.return_value = mock_play

        play_sound_alert('test_sound.wav')  # サウンド再生関数を呼び出し

        mock_wave.assert_called_with(mock.ANY)  # サウンドファイルが指定されたか確認
        mock_play.wait_done.assert_called_once()  # サウンド再生完了待ちが呼ばれたか確認

def test_send_line_message():
    """LINEへのメッセージ送信が正しく行われるかをテストします。"""
    message = "テストメッセージ"
    with mock.patch('monitor.line_bot_api.push_message_with_http_info') as mock_push:
        send_line_message(message)  # LINEメッセージ送信関数を呼び出し
        mock_push.assert_called_once()  # PUSHメッセージが一度送信された��確認

def test_send_sms():
    """Twilioを介したSMS送信が正しく行われるかをテストします。"""
    message = "テストSMS"
    with mock.patch('monitor.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.messages.create.return_value.sid = "SM1234567890"

        send_sms(message)  # SMS送信関数を呼び出し

        mock_client.messages.create.assert_called_once_with(
            body=message,
            from_=mock.ANY,
            to=mock.ANY
        )  # SMS送信が正しく呼ばれたか確認

def test_trigger_alert():
    """アラートがトリガーされた際にLINEメッセージとサウンドアラートが正しく実行されるかをテストします。"""
    message = "アラートメッセージ"
    sound_file = "alert.wav"

    with mock.patch('monitor.send_line_message') as mock_send_line, \
         mock.patch('monitor.play_sound_alert') as mock_play_sound, \
         mock.patch('monitor.executor.submit') as mock_submit:

        trigger_alert(message, sound_file)  # アラートトリガー関数を呼び出し

        mock_submit.assert_any_call(send_line_message, message)  # LINEメッセージ送信がサブミットされたか確認
        mock_submit.assert_any_call(play_sound_alert, sound_file)  # サウンドアラートがサブミットされたか確認
        assert mock_submit.call_count == 2  # 2つのタスクがサブミットされたか確認 