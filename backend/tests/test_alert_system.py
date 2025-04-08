# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
import requests # requests をインポート
from services.alert_service import AlertService
# from services.line_service import LineService # 不要
# from services.sound_service import SoundService # 不要
from utils.config_manager import ConfigManager # ConfigManager をインポート

# config fixture を削除
# @pytest.fixture
# def config():
#     return {
#         'line': {
#             'token': 'test_token',
#             'user_id': 'test_user_id',
#             'channel_secret': 'test_secret'
#         }
#     }

# DirectExecutor クラスを削除
# class DirectExecutor:
#     def submit(self, func, *args, **kwargs):
#         return func(*args, **kwargs) # すぐに実行

# AlertService インスタンスを作成する fixture (オプション)
@pytest.fixture
def alert_service():
    # ConfigManager のモックを作成
    mock_config_manager = MagicMock(spec=ConfigManager)
    # LINE Notify が有効で、テストトークンを持つように設定
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'line.enabled': True,
        'line.token': 'test_token'
    }.get(key, default)
    # AlertService を初期化
    service = AlertService(config_manager=mock_config_manager)
    return service

# テスト関数を修正
@patch('requests.post') # requests.post を patch
def test_trigger_alert(mock_post, alert_service): # config fixture の代わりに alert_service fixture を使用
    """汎用アラートが LINE Notify (requests.post) を呼び出すかテスト"""
    test_message = "テスト汎用メッセージ"
    # 実際の AlertService.trigger_alert で使用されている絵文字とスペースに合わせる
    expected_line_message = f"🚨 アラート: {test_message}"
    alert_service.trigger_alert(test_message)

    # requests.post が呼ばれたか確認
    mock_post.assert_called_once()
    # 呼び出し引数を確認
    args, kwargs = mock_post.call_args
    assert args[0] == "https://notify-api.line.me/api/notify" # URL
    assert kwargs['headers'] == {"Authorization": "Bearer test_token"} # Headers
    assert kwargs['data'] == {"message": expected_line_message} # Data

@patch('requests.post')
def test_trigger_absence_alert(mock_post, alert_service):
    """不在アラートが LINE Notify (requests.post) を呼び出すかテスト"""
    absence_duration = 15.5 # 例
    expected_line_message = f"🚶‍♂️ 不在検知: ユーザーが席を離れて {absence_duration:.0f} 秒が経過しました。"
    alert_service.trigger_absence_alert(absence_duration)

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://notify-api.line.me/api/notify"
    assert kwargs['headers'] == {"Authorization": "Bearer test_token"}
    assert kwargs['data'] == {"message": expected_line_message}

@patch('requests.post')
def test_trigger_smartphone_alert(mock_post, alert_service):
    """スマホ使用アラートが LINE Notify (requests.post) を呼び出すかテスト"""
    usage_duration = 8.2 # 例
    expected_line_message = f"📱 スマホ使用検知: ユーザーがスマートフォンを {usage_duration:.0f} 秒間使用しています。"
    alert_service.trigger_smartphone_alert(usage_duration)

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://notify-api.line.me/api/notify"
    assert kwargs['headers'] == {"Authorization": "Bearer test_token"}
    assert kwargs['data'] == {"message": expected_line_message}

# LINE Notify が無効な場合のテスト (オプション)
@patch('requests.post')
def test_alert_service_line_disabled(mock_post):
    """LINE Notifyが無効な場合に requests.post が呼ばれないかテスト"""
    # LINE が無効な ConfigManager モックを作成
    mock_config_manager = MagicMock(spec=ConfigManager)
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'line.enabled': False, # 無効に設定
        'line.token': 'test_token'
    }.get(key, default)
    alert_service_disabled = AlertService(config_manager=mock_config_manager)

    alert_service_disabled.trigger_alert("メッセージ")
    mock_post.assert_not_called() # post が呼ばれないことを確認

# トークンがない場合のテスト (オプション)
@patch('requests.post')
def test_alert_service_no_token(mock_post):
    """LINE トークンがない場合に requests.post が呼ばれないかテスト"""
    mock_config_manager = MagicMock(spec=ConfigManager)
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'line.enabled': True,
        'line.token': None # トークンなし
    }.get(key, default)
    alert_service_no_token = AlertService(config_manager=mock_config_manager)

    alert_service_no_token.trigger_alert("メッセージ")
    mock_post.assert_not_called()