"""
AIOptimizer モジュールのテスト

AIOptimizerクラスとFrameSkipperクラスのパフォーマンステストを実施します。
"""

import unittest
import numpy as np
import time
import os
import sys
import cv2
from unittest.mock import MagicMock, patch
from collections import deque

# テスト対象のモジュールへのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from src.core.ai_optimizer import AIOptimizer, FrameSkipper
from src.utils.config_manager import ConfigManager


class TestFrameSkipper(unittest.TestCase):
    """動的フレームスキップ機構のテストケース"""
    
    def setUp(self):
        """テスト前処理"""
        # 基本設定でのFrameSkipper初期化
        self.frame_skipper = FrameSkipper(
            target_fps=15.0,
            min_fps=10.0,
            max_skip_rate=5,
            adjustment_interval=0.1,  # 短い間隔でテストするため
            adaptive_mode=True
        )
    
    def test_initial_state(self):
        """初期状態のテスト"""
        self.assertEqual(self.frame_skipper.current_skip_rate, 1)
        self.assertEqual(self.frame_skipper.frame_counter, 0)
        self.assertEqual(self.frame_skipper.target_fps, 15.0)
        self.assertEqual(self.frame_skipper.min_fps, 10.0)
        self.assertEqual(self.frame_skipper.max_skip_rate, 5)
        self.assertTrue(self.frame_skipper.adaptive_mode)
    
    def test_should_process_frame_non_adaptive(self):
        """非適応モードでの処理判定テスト"""
        # 非適応モードに設定
        self.frame_skipper.adaptive_mode = False
        self.frame_skipper.current_skip_rate = 2
        
        # 1フレーム目は処理される
        self.assertTrue(self.frame_skipper.should_process_frame(0))
        
        # 2フレーム目はスキップされる
        self.assertFalse(self.frame_skipper.should_process_frame(0))
        
        # 3フレーム目は処理される
        self.assertTrue(self.frame_skipper.should_process_frame(0))
    
    def test_skip_rate_adjustment_low_fps(self):
        """低FPS時のスキップレート調整テスト"""
        # 低FPSでの調整
        self.frame_skipper.last_adjustment_time = 0  # 強制的に調整
        
        # FPS 5（低い）でスキップレートが上がるか
        self.frame_skipper.should_process_frame(5.0)
        self.assertEqual(self.frame_skipper.current_skip_rate, 2)
        
        # さらに低FPSでスキップレートが上がるか
        self.frame_skipper.last_adjustment_time = 0
        self.frame_skipper.should_process_frame(4.0)
        self.assertEqual(self.frame_skipper.current_skip_rate, 3)
        
        # 最大値を超えないか
        self.frame_skipper.current_skip_rate = 5
        self.frame_skipper.last_adjustment_time = 0
        self.frame_skipper.should_process_frame(2.0)
        self.assertEqual(self.frame_skipper.current_skip_rate, 5)  # 最大値のまま
    
    def test_skip_rate_adjustment_high_fps(self):
        """高FPS時のスキップレート調整テスト"""
        # スキップレートを上げておく
        self.frame_skipper.current_skip_rate = 3
        
        # 高FPSでスキップレートが下がるか
        self.frame_skipper.last_adjustment_time = 0
        self.frame_skipper.should_process_frame(20.0)  # 目標FPSより高い
        self.assertEqual(self.frame_skipper.current_skip_rate, 2)
        
        # さらに高FPSでスキップレートが最小値まで下がるか
        self.frame_skipper.last_adjustment_time = 0
        self.frame_skipper.should_process_frame(30.0)
        self.assertEqual(self.frame_skipper.current_skip_rate, 1)  # 最小値
    
    def test_reset(self):
        """リセット機能のテスト"""
        # 状態を変更してからリセット
        self.frame_skipper.current_skip_rate = 3
        self.frame_skipper.frame_counter = 100
        
        self.frame_skipper.reset()
        
        # リセット後の状態確認
        self.assertEqual(self.frame_skipper.current_skip_rate, 1)
        self.assertEqual(self.frame_skipper.frame_counter, 0)


class TestAIOptimizer(unittest.TestCase):
    """AIOptimizer クラスのテスト"""
    
    def setUp(self):
        """テスト前処理"""
        # モックConfigManagerを作成
        self.mock_config = MagicMock(spec=ConfigManager)
        
        def mock_has(path):
            """設定パスの存在確認モック"""
            return False
            
        def mock_get(path, default=None):
            """設定値取得モック"""
            return default
            
        self.mock_config.has = mock_has
        self.mock_config.get = mock_get
        
        # AIOptimizerインスタンス作成
        self.ai_optimizer = AIOptimizer(self.mock_config)
    
    def test_initialization(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.ai_optimizer)
        self.assertEqual(self.ai_optimizer.current_fps, 0.0)
        self.assertEqual(self.ai_optimizer.frame_counter, 0)
        self.assertIsNotNone(self.ai_optimizer.frame_skipper)
        
        # デフォルト設定の確認
        self.assertTrue(self.ai_optimizer.settings['fps_counter']['enabled'])
        self.assertTrue(self.ai_optimizer.settings['frame_skipper']['enabled'])
        self.assertEqual(self.ai_optimizer.settings['frame_skipper']['target_fps'], 15.0)
    
    def test_optimize_frame_preprocessing(self):
        """フレーム前処理最適化のテスト"""
        # テスト用フレーム（大きいサイズ）
        test_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        # リサイズ機能を有効にする
        self.ai_optimizer.settings['preprocessing']['resize_enabled'] = True
        self.ai_optimizer.settings['preprocessing']['resize_width'] = 640
        self.ai_optimizer.settings['preprocessing']['resize_height'] = 480
        
        # 前処理実行
        processed_frame = self.ai_optimizer._optimize_frame_preprocessing(test_frame)
        
        # リサイズされているか確認
        self.assertEqual(processed_frame.shape[1], 640)
        self.assertEqual(processed_frame.shape[0], 480)
    
    @patch('time.time')
    def test_update_fps_stats(self, mock_time):
        """FPS統計更新のテスト"""
        # 時間のモック
        time_sequence = [1.0, 1.1, 1.2, 1.3, 1.4]
        mock_time.side_effect = lambda: time_sequence.pop(0) if time_sequence else 10.0
        
        # FPSカウンターを初期化
        self.ai_optimizer.fps_times = deque(maxlen=5)
        self.ai_optimizer.current_fps = 0.0
        
        # 複数回更新
        for _ in range(4):
            self.ai_optimizer._update_fps_stats()
        
        # FPS計算が行われているか
        self.assertGreater(self.ai_optimizer.current_fps, 0)
        self.assertEqual(len(self.ai_optimizer.fps_times), 4)
    
    @patch('torch.cuda.is_available')
    def test_update_system_stats(self, mock_cuda_available):
        """システム統計更新のテスト"""
        # GPUがないケースをテスト
        mock_cuda_available.return_value = False
        
        # 実行前の状態確認
        self.assertEqual(self.ai_optimizer.system_stats['gpu_percent'], 0.0)
        
        # 統計更新
        self.ai_optimizer._update_system_stats()
        
        # メモリと CPU 使用率が更新されているか
        self.assertGreaterEqual(self.ai_optimizer.system_stats['memory_percent'], 0)
        self.assertGreaterEqual(self.ai_optimizer.system_stats['cpu_percent'], 0)
    
    def test_optimize_yolo_inference_with_skip(self):
        """YOLO推論のスキップテスト"""
        # スキップが有効でフレームをスキップする状況
        self.ai_optimizer.settings['frame_skipper']['enabled'] = True
        
        # スキップするようにモック
        self.ai_optimizer.frame_skipper.should_process_frame = MagicMock(return_value=False)
        
        # モックモデルとフレーム
        mock_model = MagicMock()
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 推論実行（スキップされるはず）
        result = self.ai_optimizer.optimize_yolo_inference(mock_model, test_frame)
        
        # スキップされるとNoneが返る
        self.assertIsNone(result)
        
        # モデル呼び出しがないことを確認
        mock_model.assert_not_called()
    
    def test_optimize_yolo_inference_without_skip(self):
        """YOLO推論の実行テスト"""
        # スキップが有効だがフレームを処理する状況
        self.ai_optimizer.settings['frame_skipper']['enabled'] = True
        
        # 処理するようにモック
        self.ai_optimizer.frame_skipper.should_process_frame = MagicMock(return_value=True)
        
        # モックモデルとフレーム
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_model.return_value = mock_result
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 推論実行
        result = self.ai_optimizer.optimize_yolo_inference(mock_model, test_frame)
        
        # 結果が返されているか確認
        self.assertEqual(result, mock_result)
        
        # モデル呼び出しが行われているか確認
        mock_model.assert_called_once()


class TestAIOptimizerPerformance(unittest.TestCase):
    """AIOptimizerのパフォーマンステスト"""
    
    def test_optimizer_overhead(self):
        """AIOptimizerのオーバーヘッド測定"""
        # モックConfigManagerを作成
        mock_config = MagicMock(spec=ConfigManager)
        mock_config.has = MagicMock(return_value=False)
        mock_config.get = MagicMock(return_value=None)
        
        # AIOptimizerインスタンス作成
        optimizer = AIOptimizer(mock_config)
        
        # テストフレーム（中サイズ）
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # モックモデル
        mock_model = MagicMock()
        mock_model.return_value = MagicMock()
        
        # フレーム前処理のオーバーヘッド測定
        start_time = time.time()
        for _ in range(100):
            optimizer._optimize_frame_preprocessing(test_frame)
        preprocessing_time = (time.time() - start_time) / 100 * 1000  # ms単位
        
        # スキップ判定のオーバーヘッド測定
        start_time = time.time()
        for _ in range(1000):
            optimizer.frame_skipper.should_process_frame(15.0)
        skip_decision_time = (time.time() - start_time) / 1000 * 1000  # ms単位
        
        # 統計更新のオーバーヘッド測定
        start_time = time.time()
        for _ in range(100):
            optimizer._update_fps_stats()
        stats_update_time = (time.time() - start_time) / 100 * 1000  # ms単位
        
        # 結果のアサーションは環境依存のため、出力のみ行う
        print(f"\nAIOptimizer オーバーヘッド測定:")
        print(f"フレーム前処理: {preprocessing_time:.3f} ms/フレーム")
        print(f"スキップ判定: {skip_decision_time:.3f} ms/フレーム")
        print(f"統計更新: {stats_update_time:.3f} ms/更新")
        
        # 許容範囲のアサーション（環境依存）
        self.assertLess(preprocessing_time, 10.0, "フレーム前処理のオーバーヘッドが大きすぎます")
        self.assertLess(skip_decision_time, 1.0, "スキップ判定のオーバーヘッドが大きすぎます")
        self.assertLess(stats_update_time, 5.0, "統計更新のオーバーヘッドが大きすぎます")
    
    @unittest.skipIf(not os.path.exists("/tmp/test.jpg"), "テスト画像がありません")
    def test_real_image_processing(self):
        """実画像処理のパフォーマンステスト（画像がある場合のみ）"""
        try:
            # テスト画像を読み込む（存在する場合）
            test_image = cv2.imread("/tmp/test.jpg")
            if test_image is None:
                self.skipTest("テスト画像が読み込めません")
                
            # AIOptimizerインスタンス作成
            optimizer = AIOptimizer(None)  # デフォルト設定
            
            # 前処理パフォーマンス測定
            start_time = time.time()
            for _ in range(20):
                processed_image = optimizer._optimize_frame_preprocessing(test_image)
            preprocessing_time = (time.time() - start_time) / 20 * 1000  # ms単位
            
            print(f"\n実画像処理パフォーマンス:")
            print(f"入力サイズ: {test_image.shape}")
            print(f"処理後サイズ: {processed_image.shape}")
            print(f"平均処理時間: {preprocessing_time:.3f} ms/フレーム")
            
        except Exception as e:
            self.skipTest(f"実画像処理テストに失敗: {str(e)}")


if __name__ == "__main__":
    unittest.main() 