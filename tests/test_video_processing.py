import pytest
from unittest import mock
from src.kanshichan.core.monitor import trigger_alert, absence_threshold, smartphone_threshold

# ここでは主にメインループの一部であるフレーム処理をテストします。
# 具体的な実装はコードに依存するため、適宜モックを使用します。

def test_trigger_alert():
    """アラートがトリガーされた際にLINEメッセージとサウンドアラートが正しく実行されるかをテストします。"""
    with mock.patch('monitor.send_line_message') as mock_line, \
         mock.patch('monitor.play_sound_alert') as mock_sound:

        trigger_alert("テストアラート", "test_sound.wav")  # アラートトリガー関数を呼び出し

        mock_line.assert_called_once_with("テストアラート")  # LINEメッセージ送信が正しく行われたか確認
        mock_sound.assert_called_once_with("test_sound.wav")  # サウンドアラートが正しく再生されたか確認 