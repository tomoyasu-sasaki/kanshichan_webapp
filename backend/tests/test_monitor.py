import pytest
from unittest.mock import MagicMock, patch, PropertyMock, ANY
import time
from datetime import datetime
from core.monitor import Monitor
from services.alert_service import AlertService
# 依存コンポーネントのクラスをインポート
from core.camera import Camera
from core.detector import Detector
from core.detection_manager import DetectionManager
from core.state_manager import StateManager
from services.alert_manager import AlertManager
from utils.config_manager import ConfigManager # ConfigManager をインポート
from services.object_detection_service import ObjectDetectionService
from services.schedule_manager import ScheduleManager  # 追加
from utils.constants import DetectionStatus

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

# スケジュール関連のテストを追加
def test_check_schedules_match_found(monkeypatch):
    """時刻が一致するスケジュールが見つかった場合のテスト"""
    # 現在時刻のモック
    current_time = "14:30"
    mock_now = MagicMock()
    mock_now.strftime.return_value = current_time
    monkeypatch.setattr(datetime, 'now', MagicMock(return_value=mock_now))
    
    # 依存関係のモック
    mock_config = MagicMock(spec=ConfigManager)
    mock_alert = MagicMock(spec=AlertService)
    mock_detector = MagicMock(spec=ObjectDetectionService)
    mock_state = MagicMock(spec=StateManager)
    mock_schedule = MagicMock(spec=ScheduleManager)
    
    # スケジュール一覧を設定
    mock_schedule.get_schedules.return_value = [
        {"id": "test-id-1", "time": "09:00", "content": "朝のミーティング"},
        {"id": "test-id-2", "time": current_time, "content": "定期報告"},
        {"id": "test-id-3", "time": "17:00", "content": "退勤"}
    ]
    
    # ソケットのモック
    mock_socket = MagicMock()
    
    # Monitorインスタンスを作成
    monitor = Monitor(
        config_manager=mock_config,
        alert_service=mock_alert,
        object_detection_service=mock_detector,
        state_manager=mock_state,
        schedule_manager=mock_schedule
    )
    
    # _socketフィールドをセット
    monitor._socket = mock_socket
    
    # テスト対象メソッドを実行
    monitor._check_schedules()
    
    # アラート音が再生されたことを確認
    mock_alert.play_alert.assert_called_once()
    
    # WebSocketで通知が送信されたことを確認
    mock_socket.emit.assert_called_with('schedule_alert', {
        'time': current_time,
        'content': '定期報告'
    })

def test_check_schedules_no_match(monkeypatch):
    """時刻が一致するスケジュールがない場合のテスト"""
    # 現在時刻のモック
    current_time = "14:30"
    mock_now = MagicMock()
    mock_now.strftime.return_value = current_time
    monkeypatch.setattr(datetime, 'now', MagicMock(return_value=mock_now))
    
    # 依存関係のモック
    mock_config = MagicMock(spec=ConfigManager)
    mock_alert = MagicMock(spec=AlertService)
    mock_detector = MagicMock(spec=ObjectDetectionService)
    mock_state = MagicMock(spec=StateManager)
    mock_schedule = MagicMock(spec=ScheduleManager)
    
    # スケジュール一覧を設定（現在時刻と一致するものはない）
    mock_schedule.get_schedules.return_value = [
        {"id": "test-id-1", "time": "09:00", "content": "朝のミーティング"},
        {"id": "test-id-2", "time": "12:00", "content": "昼食"},
        {"id": "test-id-3", "time": "17:00", "content": "退勤"}
    ]
    
    # ソケットのモック
    mock_socket = MagicMock()
    
    # Monitorインスタンスを作成
    monitor = Monitor(
        config_manager=mock_config,
        alert_service=mock_alert,
        object_detection_service=mock_detector,
        state_manager=mock_state,
        schedule_manager=mock_schedule
    )
    
    # _socketフィールドをセット
    monitor._socket = mock_socket
    
    # テスト対象メソッドを実行
    monitor._check_schedules()
    
    # アラート音が再生されないことを確認
    mock_alert.play_alert.assert_not_called()
    
    # WebSocketで通知が送信されないことを確認
    assert not mock_socket.emit.called or not any(call[0][0] == 'schedule_alert' for call in mock_socket.emit.call_args_list)

def test_check_schedules_multiple_matches(monkeypatch):
    """同じ時刻に複数のスケジュールがある場合のテスト"""
    # 現在時刻のモック
    current_time = "14:30"
    mock_now = MagicMock()
    mock_now.strftime.return_value = current_time
    monkeypatch.setattr(datetime, 'now', MagicMock(return_value=mock_now))
    
    # 依存関係のモック
    mock_config = MagicMock(spec=ConfigManager)
    mock_alert = MagicMock(spec=AlertService)
    mock_detector = MagicMock(spec=ObjectDetectionService)
    mock_state = MagicMock(spec=StateManager)
    mock_schedule = MagicMock(spec=ScheduleManager)
    
    # スケジュール一覧を設定（同じ時刻に複数のスケジュール）
    mock_schedule.get_schedules.return_value = [
        {"id": "test-id-1", "time": "09:00", "content": "朝のミーティング"},
        {"id": "test-id-2", "time": current_time, "content": "定期報告1"},
        {"id": "test-id-3", "time": current_time, "content": "定期報告2"},
        {"id": "test-id-4", "time": "17:00", "content": "退勤"}
    ]
    
    # ソケットのモック
    mock_socket = MagicMock()
    
    # Monitorインスタンスを作成
    monitor = Monitor(
        config_manager=mock_config,
        alert_service=mock_alert,
        object_detection_service=mock_detector,
        state_manager=mock_state,
        schedule_manager=mock_schedule
    )
    
    # _socketフィールドをセット
    monitor._socket = mock_socket
    
    # モニターの既に通知済みスケジュールIDセットをクリア
    monitor._notified_schedule_ids = set()
    
    # テスト対象メソッドを実行
    monitor._check_schedules()
    
    # アラート音が複数回再生されたことを確認
    assert mock_alert.play_alert.call_count == 2
    
    # WebSocketで複数の通知が送信されたことを確認
    assert mock_socket.emit.call_count >= 2
    
    # 両方のスケジュールが通知されたことを確認
    found_notifications = []
    for call in mock_socket.emit.call_args_list:
        if call[0][0] == 'schedule_alert':
            found_notifications.append(call[0][1]['content'])
    
    assert "定期報告1" in found_notifications
    assert "定期報告2" in found_notifications

def test_check_schedules_already_notified(monkeypatch):
    """既に通知済みのスケジュールがある場合のテスト"""
    # 現在時刻のモック
    current_time = "14:30"
    mock_now = MagicMock()
    mock_now.strftime.return_value = current_time
    monkeypatch.setattr(datetime, 'now', MagicMock(return_value=mock_now))
    
    # 依存関係のモック
    mock_config = MagicMock(spec=ConfigManager)
    mock_alert = MagicMock(spec=AlertService)
    mock_detector = MagicMock(spec=ObjectDetectionService)
    mock_state = MagicMock(spec=StateManager)
    mock_schedule = MagicMock(spec=ScheduleManager)
    
    # スケジュール一覧を設定
    test_schedule = {"id": "test-id-2", "time": current_time, "content": "定期報告"}
    mock_schedule.get_schedules.return_value = [
        {"id": "test-id-1", "time": "09:00", "content": "朝のミーティング"},
        test_schedule,
        {"id": "test-id-3", "time": "17:00", "content": "退勤"}
    ]
    
    # ソケットのモック
    mock_socket = MagicMock()
    
    # Monitorインスタンスを作成
    monitor = Monitor(
        config_manager=mock_config,
        alert_service=mock_alert,
        object_detection_service=mock_detector,
        state_manager=mock_state,
        schedule_manager=mock_schedule
    )
    
    # _socketフィールドをセット
    monitor._socket = mock_socket
    
    # 既に通知済みとしてスケジュールIDを設定
    monitor._notified_schedule_ids = {test_schedule["id"]}
    
    # テスト対象メソッドを実行
    monitor._check_schedules()
    
    # アラート音が再生されないことを確認
    mock_alert.play_alert.assert_not_called()
    
    # WebSocketで通知が送信されないことを確認
    assert not mock_socket.emit.called or not any(call[0][0] == 'schedule_alert' for call in mock_socket.emit.call_args_list) 