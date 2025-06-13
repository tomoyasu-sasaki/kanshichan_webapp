import os
import sys
import pytest
import time

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.config_manager import ConfigManager
from web.app import create_app


@pytest.fixture(scope="module")
def flask_test_client():
    """Flask テストクライアントを共有フィクスチャとして提供"""
    cfg = ConfigManager()
    cfg.load()
    app, _ = create_app(cfg)
    app.testing = True
    with app.test_client() as client:
        yield client


def test_system_metrics_endpoint(flask_test_client):
    """/api/monitor/system-metrics が 200 を返し CPU キーを含むこと"""
    resp = flask_test_client.get("/api/monitor/system-metrics")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert "cpu" in data["data"]


def test_rate_limit_exceeded_returns_429(flask_test_client):
    """100リクエストを超過した場合に 429 が返ること (簡易テスト)"""
    # 101回連続で呼び出しレートリミットを誘発
    exceeded = False
    for i in range(110):
        resp = flask_test_client.get("/api/monitor/system-metrics")
        if resp.status_code == 429:
            exceeded = True
            break
    assert exceeded, "Expected at least one 429 Too Many Requests response" 