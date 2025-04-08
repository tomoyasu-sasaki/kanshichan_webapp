import pytest
from unittest.mock import MagicMock, patch
import time
from core.monitor import Monitor
from services.alert_service import AlertService
# 依存コンポーネントのクラスをインポート
from core.camera import Camera
from core.detector import Detector
from core.detection_manager import DetectionManager
from core.state_manager import StateManager
from services.alert_manager import AlertManager
from utils.config_manager import ConfigManager # ConfigManager をインポート

# Monitor インスタンスをリセットするヘルパーフィクスチャ
@pytest.fixture(autouse=True)
def reset_monitor_state():
    # Monitor._instance = None # Monitor はシングルトンではないので不要
    # 代わりに依存するシングルトンなどがあればここでリセット
    yield
    # Monitor._instance = None

# 依存コンポーネントのモックを作成する fixture
@pytest.fixture
def mock_dependencies(tmp_path):
    """Monitor および関連クラスのモック依存関係を作成する"""
    # ConfigManager のモック (デフォルト値を使用)
    mock_config_manager = MagicMock(spec=ConfigManager)
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'conditions.absence.threshold_seconds': 5,
        'conditions.smartphone_usage.threshold_seconds': 3,
        'line.enabled': True,
        'line.token': 'fake_token'
    }.get(key, default)

    # AlertService, AlertManager のモック (必要に応じて)
    # AlertService は実際のインスタンスを使う（内部の LINE 送信などは mock で潰す）
    mock_alert_service = AlertService(config_manager=mock_config_manager)
    alert_manager = AlertManager(alert_service=mock_alert_service)

    # StateManager は実際のインスタンスを使う
    state_manager = StateManager(config_manager=mock_config_manager, alert_manager=alert_manager)

    # その他のモック
    mock_camera = MagicMock(spec='core.camera.Camera')
    mock_detector = MagicMock(spec='core.detector.Detector')
    mock_detection_manager = MagicMock(spec='core.detection_manager.DetectionManager')

    deps = {
        'config_manager': mock_config_manager,
        'camera': mock_camera,
        'detector': mock_detector,
        'detection_manager': mock_detection_manager,
        'state_manager': state_manager,
        'alert_manager': alert_manager,
    }
    return deps # alert_service を含まない辞書を返す

# Monitor インスタンスを作成する fixture
@pytest.fixture
def monitor_instance(mock_dependencies):
    """テスト用の Monitor インスタンスを作成する"""
    # Monitor インスタンスを実際のクラスから生成し、依存性を注入
    return Monitor(**mock_dependencies)

def test_monitor_initialization(monitor_instance, mock_dependencies):
    """Monitor が依存関係とともに正しく初期化されるかテスト"""
    assert monitor_instance.config_manager == mock_dependencies['config_manager']
    assert monitor_instance.camera == mock_dependencies['camera']
    assert monitor_instance.detector == mock_dependencies['detector']
    assert monitor_instance.detection_manager == mock_dependencies['detection_manager']
    assert monitor_instance.state_manager == mock_dependencies['state_manager']
    assert monitor_instance.alert_manager == mock_dependencies['alert_manager']

def test_handle_person_absence(monitor_instance, mock_dependencies):
    """不在検知が正しく動作するかテスト (StateManager経由)"""
    # StateManager の alert_manager の trigger_absence_alert をモック化
    with patch.object(monitor_instance.state_manager.alert_manager, 'trigger_absence_alert') as mock_trigger:
        # ★★★ 事前条件: person_detected を True に設定 ★★★
        monitor_instance.state_manager.person_detected = True
        assert not monitor_instance.state_manager.alert_triggered_absence
        # 閾値超えの状態にする
        monitor_instance.state_manager.last_seen_time = time.time() - (monitor_instance.state_manager.absence_threshold + 1)
        # StateManager のメソッドを呼び出す
        monitor_instance.state_manager.handle_person_absence()
        # モックが呼ばれたか確認
        mock_trigger.assert_called_once()

def test_handle_phone_detection(monitor_instance, mock_dependencies):
    """スマートフォン検知のテスト修正版 (StateManager経由)"""
    # StateManager の alert_manager の trigger_smartphone_alert をモック化
    with patch.object(monitor_instance.state_manager.alert_manager, 'trigger_smartphone_alert') as mock_trigger:
        assert not monitor_instance.state_manager.alert_triggered_smartphone
        monitor_instance.state_manager.smartphone_in_use = True
        # 閾値超えの状態にする
        # monitor_instance.state_manager.last_phone_detection_time = time.time() - (monitor_instance.state_manager.smartphone_threshold + 1)
        # StateManager のメソッドを呼び出す (smartphone_detected=True は不要かも？ handle_smartphone_usage は内部で時間をチェックする)
        # monitor_instance.state_manager.handle_smartphone_usage(smartphone_detected=True)
        # 代わりに、時間経過をシミュレートして再度 handle_smartphone_usage を呼ぶか、
        # または内部状態を直接設定する
        monitor_instance.state_manager.smartphone_start_time = time.time() - (monitor_instance.state_manager.smartphone_threshold + 1)
        monitor_instance.state_manager.handle_smartphone_usage(smartphone_detected=True) # 再度呼び出し
        # モックが呼ばれたか確認
        mock_trigger.assert_called_once()

def test_analyze_behavior(monitor_instance, mock_dependencies):
    """行動分析機能が正しく動作するかテスト (要リファクタリング)"""
    pass

@pytest.mark.asyncio
async def test_create_context(monitor_instance, mock_dependencies):
    """コンテキスト生成テスト（非同期対応）(要リファクタリング)"""
    pass 