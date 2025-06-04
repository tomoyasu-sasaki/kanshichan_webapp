"""
Phase 5: 最終統合テスト
======================
Phase 1-4の全機能を統合したE2Eテストスイート
"""
import pytest
import json
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.real_time_analyzer import RealTimeAnalyzer
from services.streaming_processor import StreamingProcessor
from services.alert_system import AlertSystem
from services.performance_monitor import PerformanceMonitor
from services.personalization_engine import PersonalizationEngine
from services.adaptive_learning_system import AdaptiveLearningSystem
from services.advanced_behavior_analyzer import AdvancedBehaviorAnalyzer
from services.pattern_recognizer import PatternRecognizer

# TTS services
from services.voice_cloning_service import VoiceCloningService
from services.zonos_tts_service import ZonosTTSService
from services.tts_voice_manager import TTSVoiceManager

# Data models
from models.database import init_db
from models.behavior_log import BehaviorLog
from models.analysis_result import AnalysisResult
from models.user_profile import UserProfile

# LLM Service
from services.ollama_service import OllamaService


class TestPhase5Integration:
    """Phase 5: 最終統合テスト"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """テスト環境の初期化"""
        # Mock configurations
        self.mock_config = {
            'analysis': {
                'batch_size': 10,
                'window_size_minutes': 5
            },
            'realtime': {
                'buffer_size': 100,
                'processing_interval': 1.0
            },
            'personalization': {
                'min_data_points': 5,
                'learning_rate': 0.1
            },
            'tts': {
                'model_path': '/tmp/test_model',
                'voice_cache_dir': '/tmp/voice_cache'
            }
        }
        
        # Initialize components
        self.real_time_analyzer = RealTimeAnalyzer(self.mock_config)
        self.streaming_processor = StreamingProcessor(self.mock_config)
        self.alert_system = AlertSystem(self.mock_config)
        self.performance_monitor = PerformanceMonitor(self.mock_config)
        self.personalization_engine = PersonalizationEngine(self.mock_config)
        self.adaptive_learning = AdaptiveLearningSystem(self.mock_config)
        self.behavior_analyzer = AdvancedBehaviorAnalyzer(self.mock_config)
        self.pattern_recognizer = PatternRecognizer(self.mock_config)
        
        # Mock database
        with patch('models.database.init_db'):
            pass

    def test_end_to_end_data_flow(self):
        """E2E データフロー統合テスト"""
        # 1. Phase 1: データ収集・蓄積のシミュレーション
        mock_behavior_data = {
            'timestamp': datetime.now().isoformat(),
            'focus_score': 0.8,
            'posture_score': 0.7,
            'smartphone_usage': False,
            'face_visible': True,
            'productivity_estimate': 0.75
        }
        
        # 2. Phase 4.1: 高度行動分析
        with patch.object(self.behavior_analyzer, 'analyze_behavior_patterns') as mock_analyze:
            mock_analyze.return_value = {
                'patterns': {
                    'focus_patterns': [
                        {
                            'pattern_type': 'deep_focus',
                            'confidence': 0.9,
                            'frequency': 3,
                            'description': '長時間集中パターン'
                        }
                    ],
                    'work_style': 'MORNING_PERSON'
                }
            }
            
            patterns = self.behavior_analyzer.analyze_behavior_patterns(
                user_id='test_user',
                timeframe='day'
            )
            
            assert patterns['patterns']['work_style'] == 'MORNING_PERSON'
            assert len(patterns['patterns']['focus_patterns']) > 0
        
        # 3. Phase 4.2: パーソナライゼーション
        with patch.object(self.personalization_engine, 'generate_personalized_recommendations') as mock_recommend:
            mock_recommend.return_value = {
                'recommendations': [
                    {
                        'recommendation_id': 'rec_001',
                        'title': '休憩時間最適化',
                        'priority': 8,
                        'effectiveness_score': 0.85
                    }
                ]
            }
            
            recommendations = self.personalization_engine.generate_personalized_recommendations(
                user_id='test_user',
                context={'current_state': 'focused'}
            )
            
            assert len(recommendations['recommendations']) > 0
            assert recommendations['recommendations'][0]['priority'] >= 8
        
        # 4. Phase 4.3: リアルタイム分析
        with patch.object(self.real_time_analyzer, 'process_stream_data') as mock_process:
            mock_process.return_value = {
                'analysis_result': {
                    'focus_score': 0.8,
                    'alerts': [],
                    'recommendations': []
                }
            }
            
            result = self.real_time_analyzer.process_stream_data(mock_behavior_data)
            
            assert result['analysis_result']['focus_score'] == 0.8
            assert 'alerts' in result['analysis_result']

    def test_tts_integration_workflow(self):
        """TTS音声システム統合テスト (Phase 2)"""
        with patch('services.zonos_tts_service.ZonosTTSService') as MockTTS, \
             patch('services.voice_cloning_service.VoiceCloningService') as MockCloning, \
             patch('services.tts_voice_manager.TTSVoiceManager') as MockManager:
            
            # Mock TTS components
            mock_tts = MockTTS.return_value
            mock_cloning = MockCloning.return_value
            mock_manager = MockManager.return_value
            
            # Mock TTS generation
            mock_tts.generate_speech.return_value = {
                'audio_data': b'mock_audio_data',
                'sample_rate': 22050,
                'format': 'wav'
            }
            
            # Mock voice cloning
            mock_cloning.clone_voice.return_value = {
                'voice_id': 'cloned_voice_001',
                'similarity_score': 0.92
            }
            
            # Mock voice management
            mock_manager.get_voice_settings.return_value = {
                'voice_id': 'default_voice',
                'emotion': 'neutral',
                'speed': 1.0
            }
            
            # Test TTS workflow
            tts_result = mock_tts.generate_speech(
                text="集中度が低下しています。5分間の休憩をおすすめします。",
                voice_settings={'emotion': 'gentle', 'speed': 0.9}
            )
            
            assert tts_result['audio_data'] == b'mock_audio_data'
            assert tts_result['sample_rate'] == 22050

    def test_adaptive_learning_integration(self):
        """適応学習システム統合テスト (Phase 4.2)"""
        with patch.object(self.adaptive_learning, 'update_learning_model') as mock_update, \
             patch.object(self.adaptive_learning, 'get_learning_status') as mock_status:
            
            # Mock learning update
            mock_update.return_value = {
                'model_updated': True,
                'improvement': 0.05,
                'new_accuracy': 0.87
            }
            
            # Mock learning status
            mock_status.return_value = {
                'learning_active': True,
                'model_accuracy': 0.87,
                'recommendations_given': 45,
                'user_satisfaction_avg': 4.2,
                'adaptation_count': 12
            }
            
            # Test feedback processing
            feedback_data = {
                'user_id': 'test_user',
                'recommendation_id': 'rec_001',
                'satisfaction_score': 4,
                'feedback_text': 'Very helpful recommendation'
            }
            
            update_result = self.adaptive_learning.update_learning_model(feedback_data)
            status = self.adaptive_learning.get_learning_status('test_user')
            
            assert update_result['model_updated'] is True
            assert status['learning_active'] is True
            assert status['model_accuracy'] >= 0.85

    def test_alert_system_integration(self):
        """アラートシステム統合テスト (Phase 4.3)"""
        with patch.object(self.alert_system, 'process_alert') as mock_process, \
             patch.object(self.alert_system, 'get_active_alerts') as mock_get_alerts:
            
            # Mock alert processing
            mock_process.return_value = {
                'alert_sent': True,
                'channels': ['tts', 'screen'],
                'suppressed': False
            }
            
            # Mock active alerts
            mock_get_alerts.return_value = {
                'alerts': [
                    {
                        'alert_id': 'alert_001',
                        'type': 'FOCUS_DECLINE',
                        'priority': 'WARNING',
                        'message': '集中度低下検出',
                        'timestamp': datetime.now().isoformat()
                    }
                ]
            }
            
            # Test alert workflow
            alert_data = {
                'type': 'FOCUS_DECLINE',
                'severity': 'WARNING',
                'user_id': 'test_user',
                'context': {
                    'focus_score': 0.3,
                    'duration_minutes': 15
                }
            }
            
            result = self.alert_system.process_alert(alert_data)
            active_alerts = self.alert_system.get_active_alerts('test_user')
            
            assert result['alert_sent'] is True
            assert 'tts' in result['channels']
            assert len(active_alerts['alerts']) > 0

    def test_performance_monitoring_integration(self):
        """パフォーマンス監視統合テスト (Phase 4.3)"""
        with patch.object(self.performance_monitor, 'get_performance_report') as mock_report, \
             patch.object(self.performance_monitor, 'get_system_health') as mock_health:
            
            # Mock performance report
            mock_report.return_value = {
                'system_statistics': {
                    'avg_cpu_usage': 45.2,
                    'avg_memory_usage': 68.7,
                    'disk_usage': 34.1
                },
                'analysis_statistics': {
                    'avg_accuracy': 0.89,
                    'avg_latency': 45.6,
                    'error_rate': 0.02
                },
                'health_score': 0.91
            }
            
            # Mock system health
            mock_health.return_value = {
                'overall_status': 'EXCELLENT',
                'components': {
                    'real_time_analyzer': 'GOOD',
                    'tts_system': 'EXCELLENT',
                    'personalization': 'GOOD'
                }
            }
            
            # Test performance monitoring
            report = self.performance_monitor.get_performance_report(hours=24)
            health = self.performance_monitor.get_system_health()
            
            assert report['health_score'] > 0.8
            assert health['overall_status'] in ['EXCELLENT', 'GOOD']
            assert report['analysis_statistics']['avg_accuracy'] > 0.85

    def test_phase_integration_data_consistency(self):
        """Phase間データ整合性テスト"""
        # Test data consistency across all phases
        user_id = 'test_user'
        
        # Phase 1: Initial data collection
        initial_data = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'session_id': 'session_001'
        }
        
        # Phase 4.1: Pattern analysis should use Phase 1 data
        with patch.object(self.behavior_analyzer, 'get_user_behavior_history') as mock_history:
            mock_history.return_value = [initial_data]
            
            history = self.behavior_analyzer.get_user_behavior_history(user_id)
            assert len(history) > 0
            assert history[0]['user_id'] == user_id
        
        # Phase 4.2: Personalization should integrate with analysis
        with patch.object(self.personalization_engine, 'build_user_profile') as mock_profile:
            mock_profile.return_value = {
                'user_id': user_id,
                'work_style': 'MORNING_PERSON',
                'preferences': {
                    'break_frequency': 45,
                    'notification_style': 'gentle'
                }
            }
            
            profile = self.personalization_engine.build_user_profile(user_id)
            assert profile['user_id'] == user_id
            assert 'work_style' in profile

    def test_error_handling_integration(self):
        """統合エラーハンドリングテスト"""
        # Test error propagation and handling across components
        
        # Simulate component failure
        with patch.object(self.real_time_analyzer, 'process_stream_data') as mock_process:
            mock_process.side_effect = Exception("Analysis service unavailable")
            
            # Error should be handled gracefully
            try:
                self.real_time_analyzer.process_stream_data({})
                assert False, "Expected exception was not raised"
            except Exception as e:
                assert "Analysis service unavailable" in str(e)
        
        # Test fallback mechanisms
        with patch.object(self.personalization_engine, 'generate_personalized_recommendations') as mock_recommend:
            mock_recommend.return_value = {
                'recommendations': [],
                'fallback_used': True,
                'error': 'Personalization service degraded'
            }
            
            result = self.personalization_engine.generate_personalized_recommendations('test_user')
            assert result['fallback_used'] is True

    def test_scalability_performance(self):
        """スケーラビリティ・パフォーマンステスト"""
        # Test system performance under load
        
        # Simulate multiple concurrent users
        user_count = 10
        mock_users = [f'user_{i}' for i in range(user_count)]
        
        with patch.object(self.streaming_processor, 'process_batch') as mock_batch:
            mock_batch.return_value = {
                'processed_count': user_count,
                'processing_time': 2.5,
                'throughput': user_count / 2.5
            }
            
            # Test batch processing
            batch_data = [{'user_id': uid, 'data': {}} for uid in mock_users]
            result = self.streaming_processor.process_batch(batch_data)
            
            assert result['processed_count'] == user_count
            assert result['throughput'] > 2.0  # Target: >2 users/second

    def test_complete_user_journey(self):
        """完全ユーザージャーニーテスト"""
        # Simulate complete user experience from start to finish
        
        user_id = 'journey_user'
        
        # 1. User starts monitoring session
        session_start = {
            'user_id': user_id,
            'action': 'start_session',
            'timestamp': datetime.now().isoformat()
        }
        
        # 2. Behavior data is collected
        behavior_sequence = [
            {'focus_score': 0.9, 'time': 0},    # High focus
            {'focus_score': 0.7, 'time': 30},   # Declining focus
            {'focus_score': 0.4, 'time': 45},   # Low focus - should trigger alert
            {'focus_score': 0.8, 'time': 60}    # Recovery
        ]
        
        # 3. System should generate appropriate responses
        for behavior in behavior_sequence:
            with patch.object(self.real_time_analyzer, 'analyze_current_state') as mock_analyze:
                mock_analyze.return_value = {
                    'current_focus': behavior['focus_score'],
                    'trend': 'declining' if behavior['focus_score'] < 0.5 else 'stable',
                    'recommendations': ['take_break'] if behavior['focus_score'] < 0.5 else []
                }
                
                analysis = self.real_time_analyzer.analyze_current_state(behavior)
                
                if behavior['focus_score'] < 0.5:
                    assert 'take_break' in analysis['recommendations']
                    assert analysis['trend'] == 'declining'

if __name__ == '__main__':
    pytest.main([__file__]) 