"""
DetectionSmoother モジュールのテスト

検出結果の安定化（Detection Smoother）機能のテストを実施します。
"""

import unittest
import time
import os
import sys
from unittest.mock import MagicMock, patch
from copy import deepcopy
from collections import defaultdict, deque

# テスト対象のモジュールへのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from src.core.detection_smoother import DetectionSmoother
from src.utils.config_manager import ConfigManager


class TestDetectionSmoother(unittest.TestCase):
    """検出結果平滑化機能のテストケース"""
    
    def setUp(self):
        """テスト前処理"""
        # モックConfigManagerを作成
        self.mock_config = MagicMock(spec=ConfigManager)
        
        # ConfigManager.has と get のモック
        def mock_has(path):
            return False
            
        def mock_get(path, default=None):
            return default
            
        self.mock_config.has = mock_has
        self.mock_config.get = mock_get
        
        # DetectionSmootherインスタンス作成
        self.smoother = DetectionSmoother(self.mock_config)
        
        # テスト用検出結果
        self.sample_detection = {
            'bbox': (100, 100, 200, 200),
            'confidence': 0.8,
        }
        
        self.sample_results = {
            'detections': {
                'smartphone': [self.sample_detection],
                'person': [{
                    'bbox': (300, 300, 400, 400),
                    'confidence': 0.9,
                }],
            },
            'frame_info': {
                'width': 640,
                'height': 480,
            },
            'person_detected': True,
        }
    
    def test_initialization(self):
        """初期化のテスト"""
        # 基本構造の確認
        self.assertIsNotNone(self.smoother)
        self.assertIsInstance(self.smoother.settings, dict)
        self.assertIsInstance(self.smoother.detection_buffers, defaultdict)
        self.assertIsInstance(self.smoother.last_detections, dict)
        self.assertIsInstance(self.smoother.missing_frame_counters, defaultdict)
        
        # デフォルト設定の確認
        self.assertTrue(self.smoother.settings['hysteresis']['enabled'])
        self.assertTrue(self.smoother.settings['moving_average']['enabled'])
        self.assertTrue(self.smoother.settings['interpolation']['enabled'])
        
        # ヒステリシス設定の確認
        self.assertGreater(self.smoother.settings['hysteresis']['high_threshold'], 
                          self.smoother.settings['hysteresis']['low_threshold'])
    
    def test_should_accept_detection_not_tracking(self):
        """未追跡状態での検出受諾判定テスト"""
        # 未追跡状態（デフォルト）
        self.assertFalse(self.smoother.currently_tracking['smartphone'])
        
        # 高閾値（デフォルト0.65）以上で検出受諾
        high_confidence = {
            'confidence': 0.7,  # high_threshold (0.65) より高い
        }
        self.assertTrue(self.smoother._should_accept_detection('smartphone', high_confidence))
        # 受諾後は追跡状態に変わる
        self.assertTrue(self.smoother.currently_tracking['smartphone'])
        
        # 低閾値以下は未追跡状態では拒否
        self.smoother.currently_tracking['smartphone'] = False  # 追跡状態をリセット
        low_confidence = {
            'confidence': 0.4,  # low_threshold (0.35) より高いが high_threshold (0.65) より低い
        }
        self.assertFalse(self.smoother._should_accept_detection('smartphone', low_confidence))
        # 状態は変わらない
        self.assertFalse(self.smoother.currently_tracking['smartphone'])
    
    def test_should_accept_detection_tracking(self):
        """追跡中状態での検出受諾判定テスト"""
        # 追跡中状態を設定
        self.smoother.currently_tracking['smartphone'] = True
        
        # 低閾値以上なら追跡継続
        medium_confidence = {
            'confidence': 0.4,  # low_threshold (0.35) より高い
        }
        self.assertTrue(self.smoother._should_accept_detection('smartphone', medium_confidence))
        self.assertTrue(self.smoother.currently_tracking['smartphone'])
        
        # 低閾値以下なら追跡停止
        low_confidence = {
            'confidence': 0.3,  # low_threshold (0.35) より低い
        }
        self.assertFalse(self.smoother._should_accept_detection('smartphone', low_confidence))
        self.assertFalse(self.smoother.currently_tracking['smartphone'])
    
    def test_apply_moving_average(self):
        """移動平均フィルタのテスト"""
        # バッファが空の場合は元の検出を返す
        self.assertEqual(
            self.smoother._apply_moving_average('smartphone', self.sample_detection),
            self.sample_detection
        )
        
        # 検出バッファに追加
        detection1 = {'bbox': (100, 100, 200, 200), 'confidence': 0.8}
        detection2 = {'bbox': (110, 110, 210, 210), 'confidence': 0.7}
        detection3 = {'bbox': (120, 120, 220, 220), 'confidence': 0.6}
        
        self.smoother.detection_buffers['smartphone'].append(detection1)
        self.smoother.detection_buffers['smartphone'].append(detection2)
        self.smoother.detection_buffers['smartphone'].append(detection3)
        
        # 新しい検出を追加して平滑化
        new_detection = {'bbox': (130, 130, 230, 230), 'confidence': 0.9}
        smoothed = self.smoother._apply_moving_average('smartphone', new_detection)
        
        # 平滑化された結果を検証
        self.assertIsNotNone(smoothed)
        self.assertIn('bbox', smoothed)
        self.assertIn('confidence', smoothed)
        self.assertIn('smoothed', smoothed)
        self.assertTrue(smoothed['smoothed'])
        
        # 最新の検出により近い値になっているか確認（重み付け効果）
        # 最新のbbox座標（x1座標だけ確認）
        self.assertGreater(smoothed['bbox'][0], detection3['bbox'][0])
    
    def test_interpolate_missing_detections(self):
        """欠損フレーム補間のテスト"""
        # 最後の検出がない場合は補間できない
        self.assertEqual(self.smoother._interpolate_missing_detections('smartphone'), [])
        
        # 最後の検出を設定
        self.smoother.last_detections['smartphone'] = [self.sample_detection]
        
        # 欠損フレーム数をインクリメント
        self.smoother.missing_frame_counters['smartphone'] = 1
        
        # 補間結果を取得
        interpolated = self.smoother._interpolate_missing_detections('smartphone')
        
        # 補間結果の検証
        self.assertEqual(len(interpolated), 1)
        self.assertLess(interpolated[0]['confidence'], self.sample_detection['confidence'])
        self.assertTrue(interpolated[0]['interpolated'])
        
        # 最大補間フレーム数を超えた場合は補間されない
        self.smoother.missing_frame_counters['smartphone'] = 10  # 最大値を超える
        self.assertEqual(self.smoother._interpolate_missing_detections('smartphone'), [])
    
    def test_smooth_detections_no_change(self):
        """検出結果が変わらない場合の平滑化テスト"""
        # 空の検出結果
        empty_results = {'detections': {}}
        self.assertEqual(
            self.smoother.smooth_detections(empty_results),
            empty_results
        )
        
        # ヒステリシスを無効化（全検出を受け入れる）
        self.smoother.settings['hysteresis']['enabled'] = False
        # 移動平均を無効化（元の検出をそのまま使う）
        self.smoother.settings['moving_average']['enabled'] = False
        
        # 検出結果をコピー
        results_copy = deepcopy(self.sample_results)
        
        # 平滑化を適用
        smoothed = self.smoother.smooth_detections(results_copy)
        
        # 基本的に同じ結果になるはず（smoothedフラグを除く）
        self.assertIn('smartphone', smoothed['detections'])
        self.assertEqual(len(smoothed['detections']['smartphone']), 1)
        self.assertEqual(
            smoothed['detections']['smartphone'][0]['bbox'],
            self.sample_results['detections']['smartphone'][0]['bbox']
        )
    
    def test_smooth_detections_with_filtering(self):
        """検出結果のフィルタリングテスト"""
        # ヒステリシスを有効化
        self.smoother.settings['hysteresis']['enabled'] = True
        # 低い信頼度の検出を作成
        low_conf_results = deepcopy(self.sample_results)
        low_conf_results['detections']['laptop'] = [{
            'bbox': (50, 50, 100, 100),
            'confidence': 0.3,  # high_threshold (0.65) より低い
        }]
        
        # 平滑化を適用
        smoothed = self.smoother.smooth_detections(low_conf_results)
        
        # 低信頼度の検出は除去されている
        self.assertNotIn('laptop', smoothed['detections'])
        # 高信頼度の検出はそのまま
        self.assertIn('smartphone', smoothed['detections'])
    
    def test_smooth_detections_with_interpolation(self):
        """欠損フレーム補間テスト"""
        # 最初のフレームを処理して履歴に保存
        self.smoother.smooth_detections(self.sample_results)
        
        # 次のフレームでスマートフォンが検出されない場合
        missing_smartphone = deepcopy(self.sample_results)
        del missing_smartphone['detections']['smartphone']
        
        # 補間を有効化
        self.smoother.settings['interpolation']['enabled'] = True
        
        # 平滑化を適用
        smoothed = self.smoother.smooth_detections(missing_smartphone)
        
        # 欠損フレーム補間によりスマートフォンが復活している
        self.assertIn('smartphone', smoothed['detections'])
        self.assertTrue(smoothed['detections']['smartphone'][0]['interpolated'])
    
    def test_reset_state(self):
        """状態リセットのテスト"""
        # いくつかの状態を設定
        self.smoother.detection_buffers['smartphone'].append(self.sample_detection)
        self.smoother.last_detections['smartphone'] = [self.sample_detection]
        self.smoother.missing_frame_counters['smartphone'] = 2
        self.smoother.currently_tracking['smartphone'] = True
        
        # 状態をリセット
        self.smoother.reset_state()
        
        # 全ての状態がクリアされているか確認
        self.assertEqual(len(self.smoother.detection_buffers['smartphone']), 0)
        self.assertEqual(len(self.smoother.last_detections), 0)
        self.assertEqual(self.smoother.missing_frame_counters['smartphone'], 0)
        self.assertEqual(self.smoother.currently_tracking['smartphone'], False)
    
    def test_update_settings(self):
        """設定更新のテスト"""
        # 元の設定を確認
        original_window_size = self.smoother.settings['moving_average']['window_size']
        original_high_threshold = self.smoother.settings['hysteresis']['high_threshold']
        
        # 新しい設定
        new_settings = {
            'moving_average': {
                'window_size': original_window_size + 5,
            },
            'hysteresis': {
                'high_threshold': 0.75,
            }
        }
        
        # 設定を更新
        self.smoother.update_settings(new_settings)
        
        # 設定が更新されているか確認
        self.assertEqual(
            self.smoother.settings['moving_average']['window_size'], 
            original_window_size + 5
        )
        self.assertEqual(self.smoother.settings['hysteresis']['high_threshold'], 0.75)
        
        # 未指定の設定は変更されていないか確認
        self.assertEqual(
            self.smoother.settings['hysteresis']['low_threshold'], 
            0.35  # デフォルト値
        )


if __name__ == "__main__":
    unittest.main() 