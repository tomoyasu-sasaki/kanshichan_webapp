import pytest
from unittest import mock
from src.kanshichan.core.monitor import Monitor
from src.kanshichan.utils.config import load_config, save_config, DEFAULT_CONFIG_PATH

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

def test_threshold_initialization(config):
    """閾値が正しく初期化されるかテスト"""
    monitor = Monitor(config)
    
    assert monitor.absence_threshold == 5
    assert monitor.smartphone_threshold == 3

def test_config_loading():
    """設定ファイルから正しく設定が読み込まれるかテスト"""
    mock_config = {
        'line': {
            'token': 'test_token',
            'user_id': 'test_user_id',
            'channel_secret': 'test_secret'
        },
        'conditions': {
            'absence': {'threshold_seconds': 10},
            'smartphone_usage': {'threshold_seconds': 5}
        }
    }
    
    with mock.patch('src.kanshichan.utils.config.load_yaml', return_value=mock_config) as mock_load:
        config = load_config()
        mock_load.assert_called_once()
        assert config == mock_config

def test_config_saving():
    """設定が正しく保存されるかテスト"""
    test_config = {
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
    
    with mock.patch('src.kanshichan.utils.config.save_yaml') as mock_save:
        save_config(test_config)
        mock_save.assert_called_once_with(test_config, DEFAULT_CONFIG_PATH)