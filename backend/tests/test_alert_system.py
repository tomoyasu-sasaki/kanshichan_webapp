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

@pytest.mark.asyncio
async def test_trigger_alert(config):
    """アラートのテスト（非同期処理対応）"""
    alert_service = AlertService(config)
    
    with mock.patch.object(LineService, 'send_message') as mock_line, \
         mock.patch.object(SoundService, 'play_alert') as mock_sound:
        
        await alert_service.trigger_alert("テストメッセージ", "test.wav")
        mock_line.assert_called_once_with("テストメッセージ")
        mock_sound.assert_called_once_with("test.wav")

@pytest.mark.asyncio
async def test_trigger_absence_alert(config):
    alert_service = AlertService(config)
    
    with mock.patch.object(LineService, 'send_message') as mock_line, \
         mock.patch.object(SoundService, 'play_alert') as mock_sound:
        
        await alert_service.trigger_absence_alert()
        mock_line.assert_called_once_with("早く監視範囲に戻れ～！")

@pytest.mark.asyncio
async def test_trigger_smartphone_alert(config):
    """スマートフォン使用アラートのテスト（非同期対応）"""
    alert_service = AlertService(config)
    
    with mock.patch.object(LineService, 'send_message') as mock_line, \
         mock.patch.object(SoundService, 'play_alert') as mock_sound:
        
        await alert_service.trigger_smartphone_alert()
        mock_line.assert_called_once_with("スマホばかり触っていないで勉強をしろ！")
        mock_sound.assert_called_once()