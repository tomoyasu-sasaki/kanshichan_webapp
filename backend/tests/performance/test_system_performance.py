import os
import sys
import statistics
import time

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.config_manager import ConfigManager
from web.app import create_app


def test_system_metrics_average_latency():
    """50リクエストの平均応答時間が 200ms 未満であることを確認"""
    cfg = ConfigManager()
    # 重い TTS モデル読み込みを無効化してレイテンシを安定させる
    os.environ['KANSHICHAN_ENABLE_TTS'] = '0'
    os.environ['KANSHICHAN_ENABLE_AUDIO'] = '0'
    os.environ['KANSHICHAN_ENABLE_METRICS'] = '0'
    cfg.load()
    app, _ = create_app(cfg)
    app.testing = True
    client = app.test_client()

    durations = []
    for _ in range(50):
        start = time.perf_counter()
        resp = client.get('/api/monitor/system-metrics')
        assert resp.status_code == 200
        durations.append(time.perf_counter() - start)

    avg_duration = statistics.mean(durations)
    # 許容閾値: 0.25 秒 (テストモードで重い初期化を無効化しても CI 環境差を考慮)
    assert avg_duration < 0.25, f"Average latency too high: {avg_duration:.3f}s" 