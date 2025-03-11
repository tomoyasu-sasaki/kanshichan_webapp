import pytest
from unittest import mock
from backend.src.services.alert_service import AlertService
from backend.src.services.line_service import LineService
from backend.src.services.sound_service import SoundService

@pytest.fixture
def config():
    return {
        'line': {
            'token': 'test_token',
            'user_id': 'test_user_id',
            'channel_secret': 'test_secret'
        }
    }

def test_trigger_alert(config):
    """アラートがトリガーされた際にLINEメッセージとサウンドアラートが正しく実行されるかをテストします。"""
    alert_service = AlertService(config)
    
    with mock.patch.object(LineService, 'send_message') as mock_line, \
         mock.patch.object(SoundService, 'play_alert') as mock_sound:
        
        alert_service.trigger_alert("テストメッセージ", "test.wav")
        
        # 非同期実行されるため、少し待機
        import time
        time.sleep(0.1)
        
        mock_line.assert_called_once_with("テストメッセージ")
        mock_sound.assert_called_once_with("test.wav")

def test_trigger_absence_alert(config):
    """不在アラートが正しくトリガーされるかをテストします。"""
    alert_service = AlertService(config)
    
    with mock.patch.object(LineService, 'send_message') as mock_line, \
         mock.patch.object(SoundService, 'play_alert') as mock_sound:
        
        alert_service.trigger_absence_alert()
        
        # 非同期実行されるため、少し待機
        import time
        time.sleep(0.1)
        
        mock_line.assert_called_once_with("早く監視範囲に戻れ～！")
        mock_sound.assert_called_once_with("person_alert.wav")

def test_trigger_smartphone_alert(config):
    """スマートフォン使用アラートが正しくトリガーされるかをテストします。"""
    alert_service = AlertService(config)
    
    with mock.patch.object(LineService, 'send_message') as mock_line, \
         mock.patch.object(SoundService, 'play_alert') as mock_sound:
        
        alert_service.trigger_smartphone_alert()
        
        # 非同期実行されるため、少し待機
        import time
        time.sleep(0.1)
        
        mock_line.assert_called_once_with("スマホばかり触っていないで勉強をしろ！")
        mock_sound.assert_called_once_with("smartphone_alert.wav")