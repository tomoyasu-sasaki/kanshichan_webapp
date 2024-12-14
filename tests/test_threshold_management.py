import pytest
import os
import yaml # type: ignore
from unittest import mock
from src.kanshichan.core.monitor import save_thresholds, CONFIG_PATH, config, absence_threshold, smartphone_threshold, threshold_lock

@pytest.fixture
def mock_config_file(tmp_path):
    mock_path = tmp_path / "config.yaml"
    mock_path.write_text(yaml.dump(config))
    with mock.patch('src.kanshichan.core.monitor.CONFIG_PATH', str(mock_path)):
        yield mock_path

def test_save_thresholds(mock_config_file):
    new_absence = 2000
    new_smartphone = 1500

    with threshold_lock:
        global absence_threshold, smartphone_threshold
        absence_threshold = new_absence
        smartphone_threshold = new_smartphone

    save_thresholds()

    with open(mock_config_file, 'r') as f:
        updated_config = yaml.safe_load(f)

    assert updated_config['conditions']['absence']['threshold_seconds'] == new_absence
    assert updated_config['conditions']['smartphone_usage']['threshold_seconds'] == new_smartphone 