import os
import sys
import time

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.ai_optimizer import AIOptimizer, FrameSkipper


def test_frame_skipper_adjusts_on_low_fps():
    skipper = FrameSkipper(target_fps=15.0, min_fps=10.0, max_skip_rate=3)
    for _ in range(40):
        skipper.should_process_frame(current_fps=5.0)
    assert skipper.current_skip_rate > 1


def test_ai_optimizer_metrics_collection():
    optimizer = AIOptimizer()
    optimizer.start_inference_timer()
    time.sleep(0.01)
    optimizer.end_inference_timer()
    metrics = optimizer.get_performance_metrics()
    assert metrics['avg_inference_ms'] > 0
    assert 'fps' in metrics 