import pytest
from unittest import mock
from src.kanshichan.core.monitor import handle_message, activity_threshold_map, save_thresholds, absence_threshold, smartphone_threshold, MAX_ABSENCE_THRESHOLD, MAX_SMARTPHONE_THRESHOLD

@pytest.fixture
def mock_event():
    """モックイベントを生成するフィクスチャ。LINEからのメッセージイベントをシミュレートします。"""
    event = mock.Mock()
    event.message.text = "お風呂入ってくる"  # テスト用のメッセージ
    event.reply_token = "test_token"  # テスト用のリプライトークン
    return event

def test_handle_message_activity_update(mock_event):
    """特定のアクティビティメッセージを受信した際に閾値が正しく更新されるかをテストします。"""
    with mock.patch('monitor.save_thresholds') as mock_save, \
         mock.patch('monitor.line_bot_api.reply_message') as mock_reply:

        handle_message(mock_event)  # メッセージハンドラーを呼び出し

        activity = activity_threshold_map["お風呂入ってくる"]
        expected_new_threshold = min(absence_threshold + activity["additional_time"], MAX_ABSENCE_THRESHOLD)

        assert absence_threshold == expected_new_threshold  # 閾値が期待通りに更新されたか確認
        mock_save.assert_called_once()  # 閾値保存関数が一度呼ばれたか確認
        mock_reply.assert_called_once()  # LINEへの返信が一度行われたか確認

def test_handle_message_reset():
    """'リセット'メッセージを受信した際に閾値が初期値にリセットされるかをテストします。"""
    reset_event = mock.Mock()
    reset_event.message.text = "リセット"  # リセットコマンド
    reset_event.reply_token = "reset_token"  # リセット用のリプライトークン

    with mock.patch('monitor.save_thresholds') as mock_save, \
         mock.patch('monitor.line_bot_api.reply_message') as mock_reply:

        handle_message(reset_event)  # リセットメッセージを処理

        assert absence_threshold == mock.ANY  # 不在閾値が初期値にリセットされたか
        assert smartphone_threshold == mock.ANY  # スマホ使用閾値が初期値にリセットされたか
        mock_save.assert_called_once()  # 閾値保存関数が一度呼ばれたか
        mock_reply.assert_called_once_with(reset_event.reply_token, mock.ANY)  # 正しいリプライが送信されたか

def test_handle_message_unknown_command(mock_event):
    """未知のコマンドを受信した際に適切なエラーメッセージとサウンドが再生されるかをテストします。"""
    mock_event.message.text = "未知のコマンド"  # 未知のコマンドメッセージ

    with mock.patch('monitor.send_sound_alert') as mock_sound, \
         mock.patch('monitor.line_bot_api.reply_message') as mock_reply:

        handle_message(mock_event)  # 未知のコマンドを処理

        mock_sound.assert_called_with("unknown_command.wav")  # 未知コマンド用のサウンドが再生されたか
        mock_reply.assert_called_once()  # エラーメッセージが一度送信されたか 