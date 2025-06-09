"""
Adaptive Learning System Service

適応学習システム
フィードバック学習、A/Bテスト機能、学習効果測定
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict, deque
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
import json
import random

from models.behavior_log import BehaviorLog
from models.user_profile import UserProfile
from ..ai_ml.advanced_behavior_analyzer import AdvancedBehaviorAnalyzer
from ..ai_ml.pattern_recognition import PatternRecognizer
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LearningStrategy(Enum):
    """学習戦略タイプ"""
    SUPERVISED = "supervised"
    REINFORCEMENT = "reinforcement"
    COLLABORATIVE = "collaborative"
    ADAPTIVE = "adaptive"


class ABTestStatus(Enum):
    """A/Bテストステータス"""
    PLANNING = "planning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FeedbackRecord:
    """フィードバック記録"""
    feedback_id: str
    user_id: str
    recommendation_id: str
    feedback_type: str
    rating: Optional[float]
    text_feedback: Optional[str]
    behavioral_outcome: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime


@dataclass
class ABTestExperiment:
    """A/Bテスト実験データ"""
    experiment_id: str
    name: str
    description: str
    control_algorithm: str
    test_algorithm: str
    start_date: datetime
    end_date: Optional[datetime]
    target_metrics: List[str]
    participant_count: int
    status: ABTestStatus
    results: Optional[Dict[str, Any]]


@dataclass
class LearningMetrics:
    """学習メトリクス"""
    accuracy_score: float
    precision: float
    recall: float
    f1_score: float
    improvement_rate: float
    confidence_level: float
    stability_score: float


class AdaptiveLearningSystem:
    """適応学習システム
    
    ユーザーフィードバックから学習し、推奨システムを継続的に改善
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('adaptive_learning', {})
        
        # 学習パラメータ
        self.learning_params = {
            'learning_rate': self.config.get('learning_rate', 0.01),
            'batch_size': self.config.get('batch_size', 32),
            'feedback_weight': self.config.get('feedback_weight', 0.7),
            'behavioral_weight': self.config.get('behavioral_weight', 0.3),
            'min_feedback_count': self.config.get('min_feedback_count', 10)
        }
        
        # A/Bテストパラメータ
        self.ab_test_params = {
            'min_experiment_duration_days': self.config.get('min_duration_days', 7),
            'min_participants': self.config.get('min_participants', 20),
            'significance_level': self.config.get('significance_level', 0.05),
            'power': self.config.get('power', 0.8)
        }
        
        # データストレージ
        self.feedback_history = defaultdict(list)
        self.learning_models = {}
        self.ab_experiments = {}
        self.performance_metrics = defaultdict(list)
        
        logger.info("AdaptiveLearningSystem initialized with ML capabilities")
    
    def process_user_feedback(self, feedback: FeedbackRecord) -> bool:
        """ユーザーフィードバック処理
        
        Args:
            feedback: フィードバック記録
            
        Returns:
            bool: 処理成功フラグ
        """
        try:
            logger.info(f"Processing feedback for user {feedback.user_id}")
            
            # フィードバック記録
            self.feedback_history[feedback.user_id].append(feedback)
            
            # フィードバック品質評価
            feedback_quality = self._evaluate_feedback_quality(feedback)
            
            # 学習データ更新
            self._update_learning_data(feedback, feedback_quality)
            
            # モデル更新判定
            if self._should_update_model(feedback.user_id):
                self._trigger_model_update(feedback.user_id)
            
            # パターン検出
            patterns = self._detect_feedback_patterns(feedback.user_id)
            
            # 学習効果測定
            learning_effectiveness = self._measure_learning_effectiveness(feedback.user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing user feedback: {e}", exc_info=True)
            return False
    
    def create_ab_test(self, experiment_config: Dict[str, Any]) -> str:
        """A/Bテスト作成
        
        Args:
            experiment_config: 実験設定
            
        Returns:
            str: 実験ID
        """
        try:
            experiment_id = f"ab_{datetime.utcnow().timestamp()}"
            
            # 実験設定検証
            validation_result = self._validate_experiment_config(experiment_config)
            if not validation_result['valid']:
                raise ValueError(f"Invalid experiment config: {validation_result['errors']}")
            
            # 実験作成
            experiment = ABTestExperiment(
                experiment_id=experiment_id,
                name=experiment_config['name'],
                description=experiment_config.get('description', ''),
                control_algorithm=experiment_config['control_algorithm'],
                test_algorithm=experiment_config['test_algorithm'],
                start_date=datetime.utcnow(),
                end_date=None,
                target_metrics=experiment_config['target_metrics'],
                participant_count=0,
                status=ABTestStatus.PLANNING,
                results=None
            )
            
            # 実験登録
            self.ab_experiments[experiment_id] = experiment
            
            # 参加者割り当て準備
            self._prepare_participant_assignment(experiment_id, experiment_config)
            
            logger.info(f"Created A/B test experiment: {experiment_id}")
            return experiment_id
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}", exc_info=True)
            return ""
    
    def run_ab_test(self, experiment_id: str) -> bool:
        """A/Bテスト実行
        
        Args:
            experiment_id: 実験ID
            
        Returns:
            bool: 実行成功フラグ
        """
        try:
            experiment = self.ab_experiments.get(experiment_id)
            if not experiment:
                raise ValueError(f"Experiment not found: {experiment_id}")
            
            if experiment.status != ABTestStatus.PLANNING:
                raise ValueError(f"Experiment {experiment_id} is not in planning state")
            
            # 実験開始
            experiment.status = ABTestStatus.RUNNING
            experiment.start_date = datetime.utcnow()
            
            # 参加者ランダム割り当て
            self._assign_participants_randomly(experiment_id)
            
            # 実験監視開始
            self._start_experiment_monitoring(experiment_id)
            
            logger.info(f"Started A/B test experiment: {experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error running A/B test: {e}", exc_info=True)
            return False
    
    def analyze_ab_test_results(self, experiment_id: str) -> Dict[str, Any]:
        """A/Bテスト結果分析
        
        Args:
            experiment_id: 実験ID
            
        Returns:
            Dict: 分析結果
        """
        try:
            experiment = self.ab_experiments.get(experiment_id)
            if not experiment:
                raise ValueError(f"Experiment not found: {experiment_id}")
            
            # データ収集
            control_data = self._collect_experiment_data(experiment_id, 'control')
            test_data = self._collect_experiment_data(experiment_id, 'test')
            
            # 統計検定実行
            statistical_results = self._perform_statistical_tests(
                control_data, test_data, experiment.target_metrics
            )
            
            # 効果サイズ計算
            effect_sizes = self._calculate_effect_sizes(control_data, test_data)
            
            # 信頼区間計算
            confidence_intervals = self._calculate_confidence_intervals(
                control_data, test_data, experiment.target_metrics
            )
            
            # 結論生成
            conclusion = self._generate_experiment_conclusion(
                statistical_results, effect_sizes, confidence_intervals
            )
            
            # 結果保存
            results = {
                'experiment_id': experiment_id,
                'control_group_size': len(control_data),
                'test_group_size': len(test_data),
                'statistical_results': statistical_results,
                'effect_sizes': effect_sizes,
                'confidence_intervals': confidence_intervals,
                'conclusion': conclusion,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            experiment.results = results
            experiment.status = ABTestStatus.COMPLETED
            experiment.end_date = datetime.utcnow()
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing A/B test results: {e}", exc_info=True)
            return {'error': str(e)}
    
    def adapt_learning_parameters(self, user_id: str, 
                                performance_data: Dict[str, Any]) -> bool:
        """学習パラメータ適応
        
        Args:
            user_id: ユーザーID
            performance_data: パフォーマンスデータ
            
        Returns:
            bool: 適応成功フラグ
        """
        try:
            # 現在のパフォーマンス評価
            current_performance = self._evaluate_current_performance(user_id, performance_data)
            
            # パラメータ調整戦略決定
            adjustment_strategy = self._determine_adjustment_strategy(current_performance)
            
            # パラメータ更新
            updated_params = self._adjust_learning_parameters(user_id, adjustment_strategy)
            
            # 更新効果予測
            predicted_improvement = self._predict_parameter_impact(updated_params)
            
            # パラメータ適用
            self._apply_parameter_updates(user_id, updated_params)
            
            logger.info(f"Adapted learning parameters for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adapting learning parameters: {e}", exc_info=True)
            return False
    
    def measure_learning_effectiveness(self, user_id: str, 
                                     time_window_days: int = 30) -> LearningMetrics:
        """学習効果測定
        
        Args:
            user_id: ユーザーID
            time_window_days: 測定期間（日数）
            
        Returns:
            LearningMetrics: 学習メトリクス
        """
        try:
            # 期間内フィードバック取得
            feedback_data = self._get_feedback_in_timeframe(user_id, time_window_days)
            
            if len(feedback_data) < self.learning_params['min_feedback_count']:
                return self._create_default_metrics()
            
            # 精度メトリクス計算
            accuracy_metrics = self._calculate_accuracy_metrics(feedback_data)
            
            # 改善率計算
            improvement_rate = self._calculate_improvement_rate(user_id, feedback_data)
            
            # 信頼度レベル計算
            confidence_level = self._calculate_confidence_level(feedback_data)
            
            # 安定性スコア計算
            stability_score = self._calculate_stability_score(feedback_data)
            
            return LearningMetrics(
                accuracy_score=accuracy_metrics['accuracy'],
                precision=accuracy_metrics['precision'],
                recall=accuracy_metrics['recall'],
                f1_score=accuracy_metrics['f1'],
                improvement_rate=improvement_rate,
                confidence_level=confidence_level,
                stability_score=stability_score
            )
            
        except Exception as e:
            logger.error(f"Error measuring learning effectiveness: {e}", exc_info=True)
            return self._create_default_metrics()
    
    # ========== Private Methods ==========
    
    def _evaluate_feedback_quality(self, feedback: FeedbackRecord) -> float:
        """フィードバック品質評価"""
        try:
            quality_score = 0.0
            
            # 評価の存在
            if feedback.rating is not None:
                quality_score += 0.3
            
            # テキストフィードバックの存在
            if feedback.text_feedback:
                quality_score += 0.2
                # テキスト長による品質評価
                text_length = len(feedback.text_feedback)
                if text_length > 10:
                    quality_score += 0.1
            
            # 行動結果の詳細度
            if feedback.behavioral_outcome:
                quality_score += 0.3
                if len(feedback.behavioral_outcome) > 3:
                    quality_score += 0.1
            
            return min(quality_score, 1.0)
            
        except Exception:
            return 0.5
    
    def _update_learning_data(self, feedback: FeedbackRecord, quality: float):
        """学習データ更新"""
        try:
            # 重み付きフィードバックとして追加
            weighted_feedback = {
                'feedback': asdict(feedback),
                'quality_weight': quality,
                'processed_timestamp': datetime.utcnow()
            }
            
            # ユーザー別学習データに追加
            if feedback.user_id not in self.learning_models:
                self.learning_models[feedback.user_id] = {
                    'training_data': [],
                    'model_version': '1.0',
                    'last_update': datetime.utcnow()
                }
            
            self.learning_models[feedback.user_id]['training_data'].append(weighted_feedback)
            
            # データサイズ制限
            max_data_points = 1000
            if len(self.learning_models[feedback.user_id]['training_data']) > max_data_points:
                # 古いデータを削除
                self.learning_models[feedback.user_id]['training_data'] = \
                    self.learning_models[feedback.user_id]['training_data'][-max_data_points:]
                    
        except Exception as e:
            logger.error(f"Error updating learning data: {e}")
    
    def _should_update_model(self, user_id: str) -> bool:
        """モデル更新判定"""
        try:
            if user_id not in self.learning_models:
                return False
            
            training_data = self.learning_models[user_id]['training_data']
            last_update = self.learning_models[user_id]['last_update']
            
            # データ量による判定
            if len(training_data) < self.learning_params['min_feedback_count']:
                return False
            
            # 時間による判定
            time_since_update = datetime.utcnow() - last_update
            if time_since_update.days < 1:
                return False
            
            # 新規フィードバック率による判定
            recent_feedback_count = sum(
                1 for item in training_data
                if (datetime.utcnow() - item['processed_timestamp']).hours < 24
            )
            
            return recent_feedback_count >= 3
            
        except Exception as e:
            logger.error(f"Error checking model update condition: {e}")
            return False
    
    def _trigger_model_update(self, user_id: str):
        """モデル更新実行"""
        try:
            # 簡易的なモデル更新実装
            training_data = self.learning_models[user_id]['training_data']
            
            # 特徴量抽出
            features = self._extract_features_from_feedback(training_data)
            
            # モデル訓練（簡易実装）
            updated_model = self._train_simple_model(features)
            
            # モデル保存
            self.learning_models[user_id]['model'] = updated_model
            self.learning_models[user_id]['last_update'] = datetime.utcnow()
            self.learning_models[user_id]['model_version'] = self._increment_version(
                self.learning_models[user_id]['model_version']
            )
            
            logger.info(f"Updated model for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
    
    # ========== Utility Methods ==========
    
    def _create_default_metrics(self) -> LearningMetrics:
        """デフォルトメトリクス作成"""
        return LearningMetrics(
            accuracy_score=0.5,
            precision=0.5,
            recall=0.5,
            f1_score=0.5,
            improvement_rate=0.0,
            confidence_level=0.3,
            stability_score=0.5
        )
    
    # 以下のメソッドは段階的実装が必要
    def _detect_feedback_patterns(self, user_id):
        """フィードバックパターン検出 - 実装予定"""
        return []
    
    def _measure_learning_effectiveness(self, user_id):
        """学習効果測定 - 実装予定"""
        return 0.7
    
    def _validate_experiment_config(self, config):
        """実験設定検証 - 実装予定"""
        return {'valid': True, 'errors': []}
    
    def _prepare_participant_assignment(self, experiment_id, config):
        """参加者割り当て準備 - 実装予定"""
        pass
    
    def _assign_participants_randomly(self, experiment_id):
        """参加者ランダム割り当て - 実装予定"""
        pass
    
    def _start_experiment_monitoring(self, experiment_id):
        """実験監視開始 - 実装予定"""
        pass
    
    def _collect_experiment_data(self, experiment_id, group):
        """実験データ収集 - 実装予定"""
        return []
    
    def _perform_statistical_tests(self, control_data, test_data, metrics):
        """統計検定実行 - 実装予定"""
        return {}
    
    def _calculate_effect_sizes(self, control_data, test_data):
        """効果サイズ計算 - 実装予定"""
        return {}
    
    def _calculate_confidence_intervals(self, control_data, test_data, metrics):
        """信頼区間計算 - 実装予定"""
        return {}
    
    def _generate_experiment_conclusion(self, statistical_results, effect_sizes, confidence_intervals):
        """実験結論生成 - 実装予定"""
        return "実験完了"
    
    def _evaluate_current_performance(self, user_id, performance_data):
        """現在パフォーマンス評価 - 実装予定"""
        return {}
    
    def _determine_adjustment_strategy(self, performance):
        """調整戦略決定 - 実装予定"""
        return {}
    
    def _adjust_learning_parameters(self, user_id, strategy):
        """学習パラメータ調整 - 実装予定"""
        return {}
    
    def _predict_parameter_impact(self, params):
        """パラメータ影響予測 - 実装予定"""
        return 0.05
    
    def _apply_parameter_updates(self, user_id, params):
        """パラメータ更新適用 - 実装予定"""
        pass
    
    def _get_feedback_in_timeframe(self, user_id, days):
        """期間内フィードバック取得 - 実装予定"""
        return self.feedback_history.get(user_id, [])
    
    def _calculate_accuracy_metrics(self, feedback_data):
        """精度メトリクス計算 - 実装予定"""
        return {"accuracy": 0.7, "precision": 0.6, "recall": 0.7, "f1": 0.65}
    
    def _calculate_improvement_rate(self, user_id, feedback_data):
        """改善率計算 - 実装予定"""
        return 0.05
    
    def _calculate_confidence_level(self, feedback_data):
        """信頼度レベル計算 - 実装予定"""
        return 0.8
    
    def _calculate_stability_score(self, feedback_data):
        """安定性スコア計算 - 実装予定"""
        return 0.7
    
    def _extract_features_from_feedback(self, training_data):
        """フィードバックから特徴量抽出 - 実装予定"""
        return []
    
    def _train_simple_model(self, features):
        """簡易モデル訓練 - 実装予定"""
        return {"model_type": "simple", "accuracy": 0.7}
    
    def _increment_version(self, version):
        """バージョンインクリメント - 実装予定"""
        try:
            parts = version.split('.')
            minor = int(parts[-1]) + 1
            return f"{'.'.join(parts[:-1])}.{minor}"
        except:
            return "1.0.1" 