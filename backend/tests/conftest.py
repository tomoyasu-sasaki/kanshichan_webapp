"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys
from unittest import mock

# backend/src をPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

@pytest.fixture
def mock_line_event():
    """LINEメッセージイベントのモックを提供するフィクスチャ"""
    event = mock.Mock()
    event.message.text = "お風呂入ってくる"
    event.reply_token = "test_token"
    return event

@pytest.fixture
def config():
    """共通の設定フィクスチャ"""
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

@pytest.fixture
def mock_camera():
    """カメラのモックフィクスチャ"""
    class MockCamera:
        def read(self):
            return True, None
        def release(self):
            pass
    return MockCamera()

@pytest.fixture
def mock_detector():
    """検出器のモックフィクスチャ"""
    class MockDetector:
        def detect_objects(self, frame):
            return {"person_detected": True, "objects": []}
    return MockDetector()