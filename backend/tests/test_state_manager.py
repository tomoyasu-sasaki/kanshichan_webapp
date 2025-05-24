import pytest
import time
from unittest.mock import MagicMock, patch
from core.state import StateManager
from services.alert_manager import AlertManager
from services.alert_service import AlertService
from utils.config_manager import ConfigManager

# モックの AlertManager fixture を修正 (実 AlertManager + 実 AlertService(Mock Config) を使う)
@pytest.fixture
def mock_alert_manager():
    # ConfigManager のモックを作成 (AlertService用)
    mock_config_manager_for_service = MagicMock(spec=ConfigManager)
    # AlertService が使う可能性のある設定をモック (ここでは get は呼ばれない前提でも良いかも)
    mock_config_manager_for_service.get.side_effect = lambda key, default=None: {
        'line.enabled': False,
        'line.token': 'dummy_token'
    }.get(key, default)

    # AlertService の実インスタンスを作成 (ただし内部で Mock ConfigManager を使用)
    alert_service_instance = AlertService(config_manager=mock_config_manager_for_service)
    # AlertManager の実インスタンスを作成 (テスト対象の StateManager に渡す用)
    alert_manager_instance = AlertManager(alert_service=alert_service_instance)
    # テストで AlertService のメソッド呼び出しを検証したいので、
    # AlertManager が持つ AlertService インスタンスを patch する方が良い場合もある。
    # ここでは AlertManager 経由での呼び出しを見るため、この構成にする。
    # 必要なら patch.object で alert_service_instance のメソッドをモック化する。
    return alert_manager_instance

# StateManager インスタンス fixture を修正
@pytest.fixture
def state(mock_alert_manager): # mock_config を削除
    # StateManager 用の ConfigManager モックを作成
    mock_config_manager = MagicMock(spec=ConfigManager)
    # StateManager の初期化 (__init__) で get が呼ばれることを想定し、閾値を返すように設定
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'conditions.absence.threshold_seconds': 5.0, # テストで使われる値
        'conditions.smartphone_usage.threshold_seconds': 3.0 # テストで使われる値
    }.get(key, default) # キーが見つからない場合は default を返す

    # StateManager に mock_config_manager と mock_alert_manager を渡す
    manager = StateManager(mock_config_manager, mock_alert_manager)
    # テスト関数内で AlertManager のメソッド呼び出しを検証できるように、
    # manager が持つ alert_manager のメソッドを patch することが多い。
    # 例: patch.object(manager.alert_manager.alert_service, 'trigger_absence_alert')
    return manager

# --- update_detection_state のテスト ---
def test_update_detection_state_person_detected(state):
    detections_with_person = [{'label': 'person', 'confidence': 0.9, 'box': [10, 10, 50, 50]}]
    state.update_detection_state(detections_with_person)
    assert state.person_detected is True

def test_update_detection_state_person_not_detected(state):
    detections_without_person = []
    state.update_detection_state(detections_without_person)
    assert state.person_detected is False

def test_update_detection_state_person_not_detected_other_object(state):
    detections_other_object = [{'label': 'smartphone', 'confidence': 0.8, 'box': [60, 60, 80, 80]}]
    state.update_detection_state(detections_other_object)
    assert state.person_detected is False

# --- handle_person_presence のテスト ---
def test_handle_person_presence_resets_alert(state):
    state.alert_triggered_absence = True
    initial_time = state.last_seen_time
    time.sleep(0.01)
    state.handle_person_presence()
    assert state.alert_triggered_absence is False
    assert state.last_seen_time > initial_time

def test_handle_person_presence_no_alert(state):
    state.alert_triggered_absence = False
    initial_time = state.last_seen_time
    time.sleep(0.01)
    state.handle_person_presence()
    assert state.alert_triggered_absence is False
    assert state.last_seen_time > initial_time

# --- handle_person_absence のテスト ---
# mock_alert_manager が実インスタンスになったが、内部の alert_service は
# mock_alert_manager fixture 内で設定されているので、patch 対象は変わらないはず。
@patch('core.state.time.time')
def test_handle_person_absence_below_threshold(mock_time, state, mock_alert_manager):
    start_time = 1000.0
    mock_time.return_value = start_time
    # 事前条件: person_detected = True, last_seen_time = start_time
    state.person_detected = True
    state.last_seen_time = start_time
    state.person_absence_start_time = None
    # 1回目: 不在になる
    state.handle_person_absence()
    assert state.person_detected is False
    assert state.person_absence_start_time == start_time

    # 2回目: 閾値未満
    with patch.object(mock_alert_manager.alert_service, 'trigger_absence_alert') as mock_trigger:
        mock_time.return_value = start_time + state.absence_threshold - 1
        state.handle_person_absence()
        assert state.alert_triggered_absence is False
        mock_trigger.assert_not_called()

@patch('core.state.time.time')
def test_handle_person_absence_above_threshold_first_time(mock_time, state, mock_alert_manager):
    start_time = 1000.0
    mock_time.return_value = start_time
    # 事前条件: person_detected = True, last_seen_time = start_time
    state.person_detected = True
    state.last_seen_time = start_time
    state.person_absence_start_time = None
    state.alert_triggered_absence = False
    # 1回目: 不在になる -> person_detected=False, person_absence_start_time = start_time
    state.handle_person_absence()
    assert state.person_detected is False
    assert state.person_absence_start_time == start_time

    # 2回目: 閾値を超える
    with patch.object(mock_alert_manager.alert_service, 'trigger_absence_alert') as mock_trigger:
        mock_time.return_value = start_time + state.absence_threshold + 1
        state.handle_person_absence()
        # アサーション: alert_triggered_absence が True になること
        assert state.alert_triggered_absence is True
        mock_trigger.assert_called_once() # アラートが呼ばれること

@patch('core.state.time.time')
def test_handle_person_absence_above_threshold_already_alerted(mock_time, state, mock_alert_manager):
    start_time = 1000.0
    mock_time.return_value = start_time
    # 事前条件: 不在中 (person_detected = False), 既にアラート済み
    state.person_detected = False
    state.person_absence_start_time = start_time - 10 # 既に不在開始している
    state.alert_triggered_absence = True # すでにアラート状態
    with patch.object(mock_alert_manager.alert_service, 'trigger_absence_alert') as mock_trigger:
        mock_time.return_value = start_time + state.absence_threshold + 1
        state.handle_person_absence()
        assert state.alert_triggered_absence is True
        mock_trigger.assert_not_called() # 再度アラートは呼ばれない

# --- handle_smartphone_usage のテスト ---
def test_handle_smartphone_usage_detected_first_time(state, mock_alert_manager):
    state.smartphone_in_use = False
    state.alert_triggered_smartphone = False
    state.smartphone_start_time = None # 初期状態を明確に
    initial_time = time.time() # time.time() を使う

    with patch.object(mock_alert_manager.alert_service, 'trigger_smartphone_alert') as mock_trigger:
        # handle_smartphone_usage を呼ぶ前に時間を進めない (中で time() を使う想定)
        state.handle_smartphone_usage(smartphone_detected=True)
        assert state.smartphone_in_use is True
        # assert state.last_phone_detection_time > initial_time # 厳密な比較は難しい
        # smartphone_start_time が設定されていることを確認 (None でない)
        assert state.smartphone_start_time is not None
        # 必要なら時刻がおおよそ正しいか確認 (誤差を許容)
        assert abs(state.smartphone_start_time - time.time()) < 0.1
        assert state.alert_triggered_smartphone is False
        mock_trigger.assert_not_called()

@patch('core.state.time.time')
def test_handle_smartphone_usage_detected_below_threshold(mock_time, state, mock_alert_manager):
    start_time = 1000.0
    mock_time.return_value = start_time
    state.smartphone_in_use = True # すでに使用中
    state.smartphone_start_time = start_time # 使用開始時間
    state.alert_triggered_smartphone = False
    with patch.object(mock_alert_manager.alert_service, 'trigger_smartphone_alert') as mock_trigger:
        # 閾値 (3.0) より短い時間
        mock_time.return_value = start_time + state.smartphone_threshold - 1
        state.handle_smartphone_usage(smartphone_detected=True)
        assert state.alert_triggered_smartphone is False
        mock_trigger.assert_not_called()

@patch('core.state.time.time')
def test_handle_smartphone_usage_detected_above_threshold_first_time(mock_time, state, mock_alert_manager):
    start_time = 1000.0
    mock_time.return_value = start_time
    state.smartphone_in_use = True
    state.smartphone_start_time = start_time # 開始時刻を設定済みとする
    state.alert_triggered_smartphone = False
    state.smartphone_threshold = 3.0 # テスト用に閾値を設定
    with patch.object(mock_alert_manager, 'trigger_smartphone_alert') as mock_trigger:
        # 閾値 (3.0) を超える時間
        trigger_time = start_time + state.smartphone_threshold + 1
        mock_time.return_value = trigger_time
        state.handle_smartphone_usage(smartphone_detected=True)
        # アサーション: alert_triggered_smartphone が True になること
        assert state.alert_triggered_smartphone is True
        # アラートが正しい引数で呼ばれること
        expected_duration = trigger_time - start_time
        mock_trigger.assert_called_once_with(expected_duration)

@patch('core.state.time.time')
def test_handle_smartphone_usage_detected_above_threshold_already_alerted(mock_time, state, mock_alert_manager):
    start_time = 1000.0
    mock_time.return_value = start_time
    state.smartphone_in_use = True
    state.smartphone_start_time = start_time
    state.alert_triggered_smartphone = True # すでにアラート中
    with patch.object(mock_alert_manager.alert_service, 'trigger_smartphone_alert') as mock_trigger:
        mock_time.return_value = start_time + state.smartphone_threshold + 1
        state.handle_smartphone_usage(smartphone_detected=True)
        assert state.alert_triggered_smartphone is True
        mock_trigger.assert_not_called() # 再度アラートは呼ばれない

def test_handle_smartphone_usage_not_detected_was_in_use(state, mock_alert_manager):
    state.smartphone_in_use = True
    state.smartphone_start_time = time.time() - 1
    state.alert_triggered_smartphone = False
    with patch.object(mock_alert_manager.alert_service, 'trigger_smartphone_alert') as mock_trigger:
        state.handle_smartphone_usage(smartphone_detected=False)
        assert state.smartphone_in_use is False
        # アサーション: smartphone_start_time が None にリセットされること
        assert state.smartphone_start_time is None
        assert state.alert_triggered_smartphone is False
        mock_trigger.assert_not_called()

def test_handle_smartphone_usage_not_detected_was_in_use_and_alerted(state, mock_alert_manager):
    state.smartphone_in_use = True
    state.smartphone_start_time = time.time() - 10
    state.alert_triggered_smartphone = True
    with patch.object(mock_alert_manager.alert_service, 'trigger_smartphone_alert') as mock_trigger:
        state.handle_smartphone_usage(smartphone_detected=False)
        assert state.smartphone_in_use is False
        # アサーション: smartphone_start_time が None にリセットされること
        assert state.smartphone_start_time is None
        # アサーション: alert_triggered_smartphone が False にリセットされること
        assert state.alert_triggered_smartphone is False
        mock_trigger.assert_not_called()

# --- get_status_summary のテスト ---
def test_get_status_summary(state):
    state.person_detected = True
    state.smartphone_in_use = False
    state.alert_triggered_absence = False
    state.alert_triggered_smartphone = True
    state.person_absence_start_time = None
    state.smartphone_start_time = None # スマホ使用中でないので None
    # 閾値は fixture で設定されている (5.0, 3.0)

    summary = state.get_status_summary()

    # キー名を修正 (get_status_summary の実装に合わせる)
    assert summary['personDetected'] is True
    assert summary['smartphoneDetected'] is False # smartphone_in_use を反映
    assert summary['absenceTime'] == 0
    assert summary['smartphoneUseTime'] == 0 # smartphone_start_time が None なので 0
    assert summary['absenceAlert'] is False
    assert summary['smartphoneAlert'] is True
    # 閾値も確認
    assert summary['absenceThreshold'] == 5.0
    assert summary['smartphoneThreshold'] == 3.0 