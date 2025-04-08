# -*- coding: utf-8 -*-
import pytest
import os
import json
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from services.schedule_manager import ScheduleManager
from utils.config_manager import ConfigManager

@pytest.fixture
def mock_config_manager():
    """ConfigManagerのモックを提供するフィクスチャ"""
    mock_cm = MagicMock(spec=ConfigManager)
    return mock_cm

@pytest.fixture
def schedule_manager(mock_config_manager, tmpdir):
    """テスト用のScheduleManagerインスタンスを作成するフィクスチャ"""
    # テスト用の一時ディレクトリを使用
    with patch.object(ScheduleManager, 'config_dir', new=str(tmpdir)):
        with patch.object(ScheduleManager, 'schedules_file', new=str(tmpdir.join('schedules.json'))):
            sm = ScheduleManager(mock_config_manager)
            yield sm

@pytest.fixture
def sample_schedules():
    """テスト用のサンプルスケジュールデータ"""
    return [
        {"id": "test-id-1", "time": "09:00", "content": "朝のミーティング"},
        {"id": "test-id-2", "time": "12:30", "content": "昼食"},
        {"id": "test-id-3", "time": "17:00", "content": "退勤"}
    ]

def test_init(mock_config_manager):
    """初期化テスト"""
    with patch('os.path.exists', return_value=False):
        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()):
                with patch('json.dump'):
                    sm = ScheduleManager(mock_config_manager)
                    assert isinstance(sm, ScheduleManager)
                    assert sm.schedules == []

def test_load_schedules_file_not_exists(schedule_manager):
    """スケジュールファイルが存在しない場合のロードテスト"""
    with patch('os.path.exists', return_value=False):
        with patch('builtins.open', mock_open()):
            with patch('json.dump'):
                result = schedule_manager.load_schedules()
                assert result is True
                assert schedule_manager.schedules == []

def test_load_schedules_success(schedule_manager, sample_schedules):
    """スケジュールファイルが正常にロードできる場合のテスト"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_schedules))):
            result = schedule_manager.load_schedules()
            assert result is True
            assert schedule_manager.schedules == sample_schedules

def test_load_schedules_json_error(schedule_manager):
    """JSONデコードエラーが発生した場合のテスト"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data="Invalid JSON")):
            result = schedule_manager.load_schedules()
            assert result is False
            assert schedule_manager.schedules == []

def test_save_schedules_success(schedule_manager, sample_schedules):
    """スケジュールの保存が成功する場合のテスト"""
    schedule_manager.schedules = sample_schedules
    
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()) as mock_file:
            result = schedule_manager.save_schedules()
            assert result is True
            mock_file.assert_called_once()

def test_save_schedules_error(schedule_manager, sample_schedules):
    """スケジュールの保存でエラーが発生する場合のテスト"""
    schedule_manager.schedules = sample_schedules
    
    with patch('os.makedirs'):
        with patch('builtins.open', side_effect=Exception("Test error")):
            result = schedule_manager.save_schedules()
            assert result is False

def test_get_schedules(schedule_manager, sample_schedules):
    """スケジュール一覧取得のテスト"""
    schedule_manager.schedules = sample_schedules
    assert schedule_manager.get_schedules() == sample_schedules

def test_add_schedule_success(schedule_manager):
    """スケジュール追加が成功する場合のテスト"""
    time = "14:30"
    content = "テスト会議"
    
    with patch.object(schedule_manager, 'save_schedules', return_value=True):
        result = schedule_manager.add_schedule(time, content)
        assert result is not None
        assert result.get('time') == time
        assert result.get('content') == content
        assert 'id' in result
        assert len(schedule_manager.schedules) == 1

def test_add_schedule_empty_input(schedule_manager):
    """空の入力でスケジュール追加が失敗する場合のテスト"""
    # 空の時刻
    with patch.object(schedule_manager, 'save_schedules', return_value=True):
        result = schedule_manager.add_schedule("", "テスト")
        assert result is None
        assert len(schedule_manager.schedules) == 0
    
    # 空の内容
    with patch.object(schedule_manager, 'save_schedules', return_value=True):
        result = schedule_manager.add_schedule("14:30", "")
        assert result is None
        assert len(schedule_manager.schedules) == 0

def test_add_schedule_invalid_time(schedule_manager):
    """不正な時刻形式でスケジュール追加が失敗する場合のテスト"""
    # 不正な時刻形式
    with patch.object(schedule_manager, 'save_schedules', return_value=True):
        result = schedule_manager.add_schedule("2500", "テスト")
        assert result is None
        assert len(schedule_manager.schedules) == 0
    
    # 範囲外の時刻
    with patch.object(schedule_manager, 'save_schedules', return_value=True):
        result = schedule_manager.add_schedule("25:00", "テスト")
        assert result is None
        assert len(schedule_manager.schedules) == 0

def test_add_schedule_save_failure(schedule_manager):
    """保存失敗時のスケジュール追加テスト"""
    time = "14:30"
    content = "テスト会議"
    
    with patch.object(schedule_manager, 'save_schedules', return_value=False):
        result = schedule_manager.add_schedule(time, content)
        assert result is None
        assert len(schedule_manager.schedules) == 0

def test_delete_schedule_success(schedule_manager, sample_schedules):
    """スケジュール削除が成功する場合のテスト"""
    schedule_manager.schedules = sample_schedules.copy()
    target_id = sample_schedules[1]['id']
    
    with patch.object(schedule_manager, 'save_schedules', return_value=True):
        result = schedule_manager.delete_schedule(target_id)
        assert result is True
        assert len(schedule_manager.schedules) == 2
        assert all(s['id'] != target_id for s in schedule_manager.schedules)

def test_delete_schedule_not_found(schedule_manager, sample_schedules):
    """存在しないIDのスケジュール削除テスト"""
    schedule_manager.schedules = sample_schedules.copy()
    
    with patch.object(schedule_manager, 'save_schedules', return_value=True):
        result = schedule_manager.delete_schedule("non-existent-id")
        assert result is False
        assert len(schedule_manager.schedules) == 3

def test_delete_schedule_empty_id(schedule_manager):
    """空のIDでスケジュール削除が失敗する場合のテスト"""
    result = schedule_manager.delete_schedule("")
    assert result is False

def test_delete_schedule_save_failure(schedule_manager, sample_schedules):
    """保存失敗時のスケジュール削除テスト"""
    schedule_manager.schedules = sample_schedules.copy()
    target_id = sample_schedules[0]['id']
    
    with patch.object(schedule_manager, 'save_schedules', return_value=False):
        result = schedule_manager.delete_schedule(target_id)
        assert result is False 