import pytest
from unittest.mock import patch, MagicMock, call
import time
from core.monitor import Monitor
from core.state_manager import StateManager
from flask import json, Flask
from services.alert_manager import AlertManager
from services.alert_service import AlertService
from utils.config_manager import ConfigManager, DEFAULT_CONFIG_PATH
from copy import deepcopy

# Monitor インスタンスをリセットするヘルパーフィクスチャ
@pytest.fixture(autouse=True)
def reset_monitor_singleton():
    # Monitor はシングルトンではなくなったので、この fixture は不要かも
    # Monitor._instance = None
    yield
    # Monitor._instance = None
    pass # 何もしない

# テスト用の Flask アプリケーション設定
@pytest.fixture
def app(tmp_path):
    app = Flask(__name__)
    # api blueprint をインポートして登録
    # from src.web.api import api as web_api_blueprint # src. を削除
    from web.api import api as web_api_blueprint
    app.register_blueprint(web_api_blueprint, url_prefix='/api')
    app.config['TESTING'] = True

    # --- テスト用 ConfigManager の設定 ---
    # 一時ディレクトリにテスト用の config.yaml を作成
    test_config_path = tmp_path / "test_config.yaml"
    # テスト用のデフォルト設定 (必要に応じて調整)
    initial_test_config = {
        'conditions': {
            'absence': {'threshold_seconds': 5.0},
            'smartphone_usage': {'threshold_seconds': 3.0}
        },
        'line': { 'enabled': False, 'token': 'test_token' },
        'server': {'port': 5001},
        'display': {'show_opencv_window': False}
        # 他の必要なデフォルト設定
    }
    # ConfigManager をテスト用パスで初期化
    config_manager = ConfigManager(config_path=str(test_config_path))
    # 初期設定を ConfigManager に設定し、ファイルにも保存しておく
    config_manager._config = deepcopy(initial_test_config) # メモリに設定
    config_manager.save() # ファイルに保存

    app.config['config_manager'] = config_manager # Flask アプリに設定
    # --- ConfigManager 設定ここまで ---

    # --- 他の依存性の設定 (StateManager, Monitor など) ---
    # AlertManager, AlertService のモック/インスタンス化 (test_monitor.py と同様)
    mock_alert_service = AlertService(config_manager=config_manager) # ConfigManager を渡す
    alert_manager = AlertManager(alert_service=mock_alert_service)
    # StateManager のインスタンス化 (ConfigManager を渡す)
    state_manager = StateManager(config_manager=config_manager, alert_manager=alert_manager)
    # Monitor のインスタンス化 (テストによっては不要かもしれない)
    mock_camera = MagicMock(spec='core.camera.Camera') # spec を文字列で指定
    mock_detector = MagicMock(spec='core.detector.Detector')
    mock_detection_manager = MagicMock(spec='core.detection_manager.DetectionManager')
    monitor = Monitor(
        config_manager=config_manager,
        camera=mock_camera,
        detector=mock_detector,
        detection_manager=mock_detection_manager,
        state_manager=state_manager,
        alert_manager=alert_manager
    )
    app.config['monitor_instance'] = monitor # Monitor インスタンスも設定
    # --- 他の依存性の設定ここまで ---

    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_threshold_initialization(app):
    """StateManager の閾値が ConfigManager から正しく初期化されるかテスト"""
    state_manager = app.config['monitor_instance'].state_manager
    # app fixture で設定された値を確認 (initial_test_config の値)
    assert state_manager.absence_threshold == 5.0
    assert state_manager.smartphone_threshold == 3.0

def test_config_loading(tmp_path):
    """ConfigManager が設定ファイルを正しく読み込むかテスト"""
    test_config_path = tmp_path / "load_test.yaml"
    config_data = {'test': 'data', 'nested': {'value': 1}}
    # テスト用 YAML ファイルを作成 (utils.yaml_utils が必要)
    from utils.yaml_utils import save_yaml
    save_yaml(config_data, str(test_config_path))

    config_manager = ConfigManager(config_path=str(test_config_path))
    loaded = config_manager.load()

    assert loaded is True
    # get メソッドで値を取得できるか確認
    assert config_manager.get('test') == 'data'
    assert config_manager.get('nested.value') == 1
    # 存在しないキー
    assert config_manager.get('nonexistent.key', 'default') == 'default'
    # マージされたデフォルト値も確認 (必要なら DEFAULT_CONFIG と比較)

def test_config_saving(tmp_path):
    """ConfigManager が設定を正しく保存するかテスト"""
    test_config_path = tmp_path / "save_test.yaml"
    config_manager = ConfigManager(config_path=str(test_config_path))
    config_manager._config = {'save': 'this', 'level': {'one': 1}} # 直接メモリに設定

    saved = config_manager.save()
    assert saved is True
    assert test_config_path.exists()

    # 保存されたファイルを読み込んで内容を確認 (utils.yaml_utils が必要)
    from utils.yaml_utils import load_yaml
    loaded_data = load_yaml(str(test_config_path))
    assert loaded_data == {'save': 'this', 'level': {'one': 1}}

# get_settings API のテストを修正 (ConfigManager からの値取得を確認)
def test_get_settings_api(client, app):
    """/api/settings GET が ConfigManager から値を取得して返すかテスト"""
    # app fixture で設定された config_manager を使う
    config_manager = app.config['config_manager']
    # config_manager の get が呼ばれることを確認したい場合、spy を使うか、
    # ここで再度 config_manager のモックを設定し直す必要がある。
    # 今回は、正しい値が返ってくるかで確認する。
    # initial_test_config の値が返るはず
    expected_absence = config_manager.get('conditions.absence.threshold_seconds')
    expected_smartphone = config_manager.get('conditions.smartphone_usage.threshold_seconds')

    response = client.get('/api/settings')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['absence_threshold'] == expected_absence # 5.0
    assert data['smartphone_threshold'] == expected_smartphone # 3.0
    # 他のキーの存在確認はそのまま
    assert 'message_extensions' in data
    assert 'landmark_settings' in data
    assert 'detection_objects' in data

# update_settings API のテストを修正
def test_update_settings_api(client, app):
    """/api/settings POST が ConfigManager と StateManager を更新し、保存するかテスト"""
    state_manager = app.config['monitor_instance'].state_manager
    config_manager = app.config['config_manager']
    
    # 重要: patch の順序を変更し、ConfigManager.save を直接パッチする
    with patch.object(config_manager, 'save', return_value=True) as mock_save:
        with patch('utils.config_manager.ConfigManager.set') as mock_set:
            update_data = {
                'absence_threshold': 10.5,
                'smartphone_threshold': 7.2
            }
            response = client.post('/api/settings', data=json.dumps(update_data), content_type='application/json')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'

            # StateManager の値を確認
            assert state_manager.absence_threshold == 10.5
            assert state_manager.smartphone_threshold == 7.2

            # ConfigManager.set が正しい引数で呼ばれたか確認
            expected_calls = [
                call('conditions.absence.threshold_seconds', 10.5),
                call('conditions.smartphone_usage.threshold_seconds', 7.2)
            ]
            mock_set.assert_has_calls(expected_calls, any_order=True)
            assert mock_set.call_count == 2

            # ConfigManager.save が呼ばれたか確認
            mock_save.assert_called_once()

# 不正な値での更新テスト
def test_update_settings_api_invalid_value(client):
    update_data = {'absence_threshold': 'invalid'}
    response = client.post('/api/settings', data=json.dumps(update_data), content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

# キーが存在しない場合のテスト
def test_update_settings_api_missing_key(client, app):
    config_manager = app.config['config_manager']
    state_manager = app.config['monitor_instance'].state_manager
    initial_absence = state_manager.absence_threshold
    initial_smartphone = state_manager.smartphone_threshold

    with patch.object(config_manager, 'save') as mock_save:
        update_data = {'other_setting': 123}
        response = client.post('/api/settings', data=json.dumps(update_data), content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        # 値が変わっていないことを確認
        assert state_manager.absence_threshold == initial_absence
        assert state_manager.smartphone_threshold == initial_smartphone
        # save が呼ばれていないことを確認
        mock_save.assert_not_called()