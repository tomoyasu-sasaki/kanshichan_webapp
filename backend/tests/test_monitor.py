import pytest
from unittest import mock
import time
from backend.src.core.monitor import Monitor
from backend.src.services.alert_service import AlertService

@pytest.fixture
def config():
    return {
        'line': {
            'token': 'test_token',
            'user_id': 'test_user_id',
            'channel_secret': 'test_secret'
        },
        'conditions': {
            'absence': {'threshold_seconds': 5},
            'smartphone_usage': {'threshold_seconds': 3}
        }
    }

def test_handle_person_absence(config):
    """不在検知が正しく動作するかテスト"""
    monitor = Monitor(config)
    
    with mock.patch.object(AlertService, 'trigger_absence_alert') as mock_alert:
        # 初期状態では警告なし
        assert not monitor.alert_triggered_absence
        
        # 不在時間しきい値を超えた場合
        monitor.last_seen_time = time.time() - (monitor.absence_threshold + 1)
        monitor.handle_person_absence()
        
        assert monitor.alert_triggered_absence
        mock_alert.assert_called_once()

def test_handle_phone_detection(config):
    """スマートフォン使用検知が正しく動作するかテスト"""
    monitor = Monitor(config)
    
    with mock.patch.object(AlertService, 'trigger_smartphone_alert') as mock_alert:
        # 初期状態では警告なし
        assert not monitor.alert_triggered_smartphone
        
        # スマホ使用時間しきい値を超えた場合
        monitor.smartphone_in_use = True
        monitor.last_phone_detection_time = time.time() - (monitor.smartphone_threshold + 1)
        monitor.handle_phone_detection(True)
        
        assert monitor.alert_triggered_smartphone
        mock_alert.assert_called_once() 