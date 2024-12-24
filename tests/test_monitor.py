import pytest
from unittest import mock
import time
from src.kanshichan.core.monitor import Monitor
from src.kanshichan.services.alert_service import AlertService
from src.kanshichan.services.llm_service import LLMService

@pytest.fixture
def mock_config():
    return {
        'line': {
            'token': 'test_token',
            'user_id': 'test_user_id',
            'channel_secret': 'test_secret'
        },
        'conditions': {
            'absence': {'threshold_seconds': 5},
            'smartphone_usage': {'threshold_seconds': 3}
        },
        'llm': {
            'model_name': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
            'temperature': 0.7
        }
    }

def test_handle_person_absence(mock_config):
    """不在検知が正しく動作するかテスト"""
    monitor = Monitor(mock_config)
    
    with mock.patch.object(AlertService, 'trigger_absence_alert') as mock_alert:
        # 初期状態では警告なし
        assert not monitor.alert_triggered_absence
        
        # 不在時間しきい値を超えた場合
        monitor.last_seen_time = time.time() - (monitor.absence_threshold + 1)
        monitor.handle_person_absence()
        
        assert monitor.alert_triggered_absence
        mock_alert.assert_called_once()

def test_handle_phone_detection(mock_config):
    """スマートフォン検知のテスト修正版"""
    monitor = Monitor(mock_config)
    
    with mock.patch.object(monitor.alert_service, 'trigger_smartphone_alert') as mock_alert:
        # スマホ検知データの形式修正
        phone_data = {'detected': True, 'confidence': 0.95}
        
        # 初期状態
        assert not monitor.alert_triggered_smartphone
        
        # スマホ使用時間しきい値を超えた場合
        monitor.smartphone_in_use = True
        monitor.last_phone_detection_time = time.time() - (monitor.smartphone_threshold + 1)
        monitor.handle_phone_detection(phone_data)
        
        mock_alert.assert_called_once()

def test_analyze_behavior(mock_config):
    """行動分析機能が正しく動作するかテスト"""
    monitor = Monitor(mock_config)
    
    with mock.patch.object(LLMService, 'generate_response', return_value="集中を続けましょう"), \
         mock.patch.object(AlertService, 'trigger_alert') as mock_alert:
        
        # 分析間隔をテスト用に短く設定
        monitor.analysis_interval = 0
        monitor.analyze_behavior(None, True, False)
        
        mock_alert.assert_called_once_with("集中を続けましょう")

@pytest.mark.asyncio
async def test_create_context(mock_config):
    """コンテキスト生成テスト（非同期対応）"""
    with mock.patch('src.kanshichan.services.llm_service.LLMService'):
        monitor = Monitor(mock_config)
        
        # 不在時のコンテキスト
        context = monitor._create_context(False, False)
        assert "ユーザーが席を離れています" in context
        
        # スマホ使用時のコンテキスト
        context = monitor._create_context(True, True)
        assert "ユーザーがスマートフォンを使用しています" in context
        
        # 集中時のコンテキスト
        context = monitor._create_context(True, False)
        assert "ユーザーが勉強に集中しています" in context 