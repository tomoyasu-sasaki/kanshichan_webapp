import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import datetime
import cv2

from core.monitor import Monitor
from utils.config_manager import ConfigManager


class TestMonitorBehavior(unittest.TestCase):
    """Monitor.analyze_behaviorのテスト"""
    
    def setUp(self):
        """テストの前準備"""
        # 依存オブジェクトのモック
        self.config_manager = MagicMock(spec=ConfigManager)
        self.camera = MagicMock()
        self.detector = MagicMock()
        self.detection = MagicMock()
        self.state = MagicMock()
        self.alert_manager = MagicMock()
        self.flask_app = MagicMock()
        
        # テスト対象オブジェクトの作成
        self.monitor = Monitor(
            config_manager=self.config_manager,
            camera=self.camera,
            detector=self.detector,
            detection=self.detection,
            state=self.state,
            alert_manager=self.alert_manager,
            flask_app=self.flask_app
        )
        
        # テスト用のダミーフレームを作成（黒い画像）
        self.test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    @patch('core.monitor.socketio')
    @patch('models.db.session')
    @patch('models.behavior_log.BehaviorLog')
    def test_analyze_behavior_person_detected(self, mock_behavior_log, mock_db_session, mock_socketio):
        """人物検出時の行動分析テスト"""
        # モックの設定
        mock_behavior_log.get_recent_logs.return_value = []
        mock_behavior_log.create_log.return_value = MagicMock()
        
        # 行動分析実行
        result = self.monitor.analyze_behavior(
            frame=self.test_frame,
            person_detected=True,
            smartphone_in_use=False
        )
        
        # 結果の検証
        self.assertIsNotNone(result)
        self.assertIn('focus_level', result)
        self.assertIn('posture_quality', result)
        self.assertEqual(result['presence_status'], 'present')
        self.assertEqual(result['smartphone_usage'], False)
        
        # DBへの保存が呼ばれたことを確認
        mock_behavior_log.create_log.assert_called_once()
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        # WebSocket配信が呼ばれたことを確認
        mock_socketio.emit.assert_called()
    
    @patch('core.monitor.socketio')
    @patch('models.db.session')
    @patch('models.behavior_log.BehaviorLog')
    def test_analyze_behavior_smartphone_detected(self, mock_behavior_log, mock_db_session, mock_socketio):
        """スマートフォン検出時の行動分析テスト"""
        # モックの設定
        mock_behavior_log.get_recent_logs.return_value = []
        mock_behavior_log.create_log.return_value = MagicMock()
        
        # 行動分析実行
        result = self.monitor.analyze_behavior(
            frame=self.test_frame,
            person_detected=True,
            smartphone_in_use=True
        )
        
        # 結果の検証
        self.assertIsNotNone(result)
        self.assertIn('focus_level', result)
        self.assertEqual(result['presence_status'], 'present')
        self.assertEqual(result['smartphone_usage'], True)
        
        # DBへの保存が呼ばれたことを確認
        mock_behavior_log.create_log.assert_called_once()
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @patch('core.monitor.socketio')
    @patch('models.db.session')
    @patch('models.behavior_log.BehaviorLog')
    def test_analyze_behavior_no_person(self, mock_behavior_log, mock_db_session, mock_socketio):
        """人物未検出時の行動分析テスト"""
        # モックの設定
        mock_behavior_log.get_recent_logs.return_value = []
        mock_behavior_log.create_log.return_value = MagicMock()
        
        # 行動分析実行
        result = self.monitor.analyze_behavior(
            frame=self.test_frame,
            person_detected=False,
            smartphone_in_use=False
        )
        
        # 結果の検証
        self.assertIsNotNone(result)
        self.assertIn('focus_level', result)
        self.assertEqual(result['presence_status'], 'absent')
        self.assertEqual(result['posture_quality'], 'unknown')
        
        # DBへの保存が呼ばれたことを確認
        mock_behavior_log.create_log.assert_called_once()
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_extract_focus_and_posture(self):
        """集中度と姿勢データ抽出テスト"""
        # 人物検出あり
        focus_level, posture_data = self.monitor._extract_focus_and_posture(
            frame=self.test_frame,
            person_detected=True
        )
        
        # 結果の検証
        self.assertIsNotNone(focus_level)
        self.assertIsNotNone(posture_data)
        self.assertGreaterEqual(focus_level, 0.3)
        self.assertLessEqual(focus_level, 0.9)
        self.assertIn('head_position', posture_data)
        self.assertIn('shoulder_alignment', posture_data)
        
        # 人物検出なし
        focus_level, posture_data = self.monitor._extract_focus_and_posture(
            frame=self.test_frame,
            person_detected=False
        )
        
        # 結果の検証
        self.assertEqual(focus_level, 0.0)
        self.assertIsNone(posture_data)
    
    def test_evaluate_posture(self):
        """姿勢評価テスト"""
        # 良い姿勢
        good_posture = {
            'head_position': 0.9,
            'shoulder_alignment': 0.85,
            'back_straight': True
        }
        self.assertEqual(self.monitor._evaluate_posture(good_posture), 'good')
        
        # 普通の姿勢
        fair_posture = {
            'head_position': 0.7,
            'shoulder_alignment': 0.6,
            'back_straight': False
        }
        self.assertEqual(self.monitor._evaluate_posture(fair_posture), 'fair')
        
        # 悪い姿勢
        poor_posture = {
            'head_position': 0.5,
            'shoulder_alignment': 0.4,
            'back_straight': False
        }
        self.assertEqual(self.monitor._evaluate_posture(poor_posture), 'poor')
        
        # データなし
        self.assertEqual(self.monitor._evaluate_posture(None), 'unknown')
    
    def test_generate_recommendations(self):
        """推奨事項生成テスト"""
        # 集中度低
        recommendations = self.monitor._generate_recommendations(
            focus_level=0.3,
            presence_ratio=0.8,
            smartphone_ratio=0.1
        )
        self.assertIsInstance(recommendations, list)
        self.assertTrue(any("集中力が低下" in rec for rec in recommendations))
        
        # スマホ使用率高
        recommendations = self.monitor._generate_recommendations(
            focus_level=0.5,
            presence_ratio=0.8,
            smartphone_ratio=0.4
        )
        self.assertTrue(any("スマートフォンの使用頻度" in rec for rec in recommendations))
        
        # 在席率低
        recommendations = self.monitor._generate_recommendations(
            focus_level=0.5,
            presence_ratio=0.4,
            smartphone_ratio=0.1
        )
        self.assertTrue(any("離席が多く" in rec for rec in recommendations))
        
        # すべて良好
        recommendations = self.monitor._generate_recommendations(
            focus_level=0.9,
            presence_ratio=0.9,
            smartphone_ratio=0.1
        )
        self.assertTrue(any("高い集中状態" in rec for rec in recommendations))


if __name__ == '__main__':
    unittest.main() 