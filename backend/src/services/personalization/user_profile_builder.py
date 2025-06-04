"""
User Profile Builder Service

ユーザープロファイル構築サービス - Phase 4.2実装
個人特性分析、学習履歴管理、動的プロファイル更新
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

from models.behavior_log import BehaviorLog
from models.user_profile import UserProfile
from ..ai_ml.advanced_behavior_analyzer import AdvancedBehaviorAnalyzer
from ..ai_ml.pattern_recognition import PatternRecognizer
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProfileUpdateReason(Enum):
    """プロファイル更新理由"""
    NEW_DATA = "new_data"
    BEHAVIORAL_CHANGE = "behavioral_change"
    FEEDBACK_LEARNING = "feedback_learning"
    SEASONAL_ADJUSTMENT = "seasonal_adjustment"
    MANUAL_UPDATE = "manual_update"


@dataclass
class LearningHistory:
    """学習履歴データクラス"""
    recommendation_id: str
    recommendation_type: str
    user_response: str
    effectiveness_score: float
    context: Dict[str, Any]
    timestamp: datetime


@dataclass
class PersonalCharacteristics:
    """個人特性データクラス"""
    attention_span: float
    productivity_patterns: Dict[str, float]
    stress_indicators: List[str]
    preferred_break_types: List[str]
    motivation_triggers: List[str]
    distraction_sources: List[str]
    optimal_work_environment: Dict[str, Any]


@dataclass
class AdaptationMetrics:
    """適応メトリクス"""
    profile_stability: float
    learning_rate: float
    adaptation_frequency: float
    prediction_accuracy: float
    user_satisfaction: float


class UserProfileBuilder:
    """ユーザープロファイル構築サービス
    
    個人の行動データから詳細なプロファイルを構築し、継続的に更新
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('profile_builder', {})
        
        # プロファイル構築パラメータ
        self.building_params = {
            'min_observation_days': self.config.get('min_observation_days', 7),
            'stability_threshold': self.config.get('stability_threshold', 0.8),
            'update_frequency_days': self.config.get('update_frequency_days', 3),
            'confidence_threshold': self.config.get('confidence_threshold', 0.7)
        }
        
        # 学習パラメータ
        self.learning_params = {
            'feedback_weight': self.config.get('feedback_weight', 0.6),
            'behavioral_weight': self.config.get('behavioral_weight', 0.4),
            'decay_factor': self.config.get('decay_factor', 0.95),
            'adaptation_rate': self.config.get('adaptation_rate', 0.1)
        }
        
        # プロファイルキャッシュ
        self.profile_cache = {}
        self.learning_history_cache = defaultdict(list)
        self.adaptation_metrics_cache = {}
        
        logger.info("UserProfileBuilder initialized with dynamic learning capabilities")
    
    def build_comprehensive_profile(self, user_id: str, 
                                  logs: List[BehaviorLog]) -> Dict[str, Any]:
        """包括的ユーザープロファイル構築
        
        Args:
            user_id: ユーザーID
            logs: 行動ログリスト
            
        Returns:
            Dict: 包括的ユーザープロファイル
        """
        try:
            logger.info(f"Building comprehensive profile for user {user_id}")
            
            if len(logs) < self.building_params['min_observation_days'] * 24:
                return self._create_minimal_profile(user_id)
            
            # 基本特性分析
            basic_characteristics = self._analyze_basic_characteristics(logs)
            
            # 個人特性詳細分析
            personal_characteristics = self._analyze_personal_characteristics(logs)
            
            # 時間パターン分析
            temporal_patterns = self._analyze_temporal_patterns(logs)
            
            # 学習嗜好分析
            learning_preferences = self._analyze_learning_preferences(user_id, logs)
            
            # 行動予測可能性分析
            predictability_analysis = self._analyze_behavioral_predictability(logs)
            
            # 適応能力評価
            adaptation_capacity = self._evaluate_adaptation_capacity(user_id, logs)
            
            # 統合プロファイル生成
            comprehensive_profile = {
                'user_id': user_id,
                'profile_version': self._generate_profile_version(),
                'creation_timestamp': datetime.utcnow().isoformat(),
                'confidence_score': self._calculate_profile_confidence(logs),
                'basic_characteristics': basic_characteristics,
                'personal_characteristics': asdict(personal_characteristics),
                'temporal_patterns': temporal_patterns,
                'learning_preferences': learning_preferences,
                'predictability_analysis': predictability_analysis,
                'adaptation_capacity': adaptation_capacity,
                'profile_metadata': {
                    'data_points': len(logs),
                    'observation_period_days': self._calculate_observation_period(logs),
                    'last_update': datetime.utcnow().isoformat()
                }
            }
            
            # キャッシュ更新
            self.profile_cache[user_id] = comprehensive_profile
            
            return comprehensive_profile
            
        except Exception as e:
            logger.error(f"Error building comprehensive profile: {e}", exc_info=True)
            return self._create_minimal_profile(user_id)
    
    def update_profile_from_feedback(self, user_id: str, 
                                   feedback_data: List[Dict[str, Any]]) -> bool:
        """フィードバックからプロファイル更新
        
        Args:
            user_id: ユーザーID
            feedback_data: フィードバックデータリスト
            
        Returns:
            bool: 更新成功フラグ
        """
        try:
            current_profile = self.profile_cache.get(user_id)
            if not current_profile:
                logger.warning(f"No existing profile found for user {user_id}")
                return False
            
            # フィードバック分析
            feedback_insights = self._analyze_feedback_patterns(feedback_data)
            
            # 学習履歴更新
            self._update_learning_history(user_id, feedback_data)
            
            # プロファイル調整
            updated_profile = self._adjust_profile_from_feedback(
                current_profile, feedback_insights
            )
            
            # 適応メトリクス更新
            self._update_adaptation_metrics(user_id, feedback_insights)
            
            # プロファイル保存
            self.profile_cache[user_id] = updated_profile
            
            logger.info(f"Profile updated from feedback for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating profile from feedback: {e}", exc_info=True)
            return False
    
    def detect_profile_drift(self, user_id: str, 
                           recent_logs: List[BehaviorLog]) -> Dict[str, Any]:
        """プロファイルドリフト検出
        
        Args:
            user_id: ユーザーID
            recent_logs: 最近の行動ログ
            
        Returns:
            Dict: ドリフト検出結果
        """
        try:
            current_profile = self.profile_cache.get(user_id)
            if not current_profile:
                return {'drift_detected': False, 'reason': 'No baseline profile'}
            
            # 現在の行動特性分析
            current_characteristics = self._analyze_basic_characteristics(recent_logs)
            
            # ベースライン特性取得
            baseline_characteristics = current_profile.get('basic_characteristics', {})
            
            # ドリフト計算
            drift_metrics = self._calculate_drift_metrics(
                baseline_characteristics, current_characteristics
            )
            
            # ドリフト閾値判定
            significant_drift = self._assess_drift_significance(drift_metrics)
            
            # ドリフト要因分析
            drift_factors = self._analyze_drift_factors(
                baseline_characteristics, current_characteristics
            )
            
            return {
                'drift_detected': significant_drift,
                'drift_metrics': drift_metrics,
                'drift_factors': drift_factors,
                'recommended_actions': self._recommend_drift_actions(
                    significant_drift, drift_factors
                ),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting profile drift: {e}", exc_info=True)
            return {'drift_detected': False, 'error': str(e)}
    
    def get_profile_insights(self, user_id: str) -> Dict[str, Any]:
        """プロファイルインサイト取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            Dict: プロファイルインサイト
        """
        try:
            profile = self.profile_cache.get(user_id)
            if not profile:
                return {'insights': [], 'confidence': 0.0}
            
            # インサイト生成
            insights = []
            
            # 基本特性インサイト
            basic_insights = self._generate_basic_insights(profile)
            insights.extend(basic_insights)
            
            # 時間パターンインサイト
            temporal_insights = self._generate_temporal_insights(profile)
            insights.extend(temporal_insights)
            
            # 学習パターンインサイト
            learning_insights = self._generate_learning_insights(user_id, profile)
            insights.extend(learning_insights)
            
            # 改善提案生成
            improvement_suggestions = self._generate_improvement_suggestions(profile)
            
            return {
                'insights': insights,
                'improvement_suggestions': improvement_suggestions,
                'confidence': profile.get('confidence_score', 0.0),
                'profile_maturity': self._assess_profile_maturity(profile)
            }
            
        except Exception as e:
            logger.error(f"Error getting profile insights: {e}", exc_info=True)
            return {'insights': [], 'confidence': 0.0}
    
    # ========== Private Methods ==========
    
    def _analyze_basic_characteristics(self, logs: List[BehaviorLog]) -> Dict[str, Any]:
        """基本特性分析"""
        try:
            focus_scores = [log.focus_score for log in logs if log.focus_score is not None]
            posture_scores = [log.posture_score for log in logs if log.posture_score is not None]
            
            # 基本統計
            basic_stats = {
                'avg_focus': np.mean(focus_scores) if focus_scores else 0.0,
                'focus_variability': np.std(focus_scores) if focus_scores else 0.0,
                'avg_posture': np.mean(posture_scores) if posture_scores else 0.0,
                'total_sessions': len(logs),
                'smartphone_usage_rate': sum(1 for log in logs if log.smartphone_detected) / len(logs)
            }
            
            # 時間帯別パフォーマンス
            hourly_performance = self._calculate_hourly_performance(logs)
            
            # 集中パターン分析
            focus_patterns = self._analyze_focus_patterns(logs)
            
            return {
                'basic_stats': basic_stats,
                'hourly_performance': hourly_performance,
                'focus_patterns': focus_patterns,
                'behavioral_consistency': self._calculate_behavioral_consistency(logs)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing basic characteristics: {e}")
            return {}
    
    def _analyze_personal_characteristics(self, logs: List[BehaviorLog]) -> PersonalCharacteristics:
        """個人特性詳細分析"""
        try:
            # 注意継続時間分析
            attention_span = self._calculate_attention_span(logs)
            
            # 生産性パターン
            productivity_patterns = self._analyze_productivity_patterns(logs)
            
            # ストレス指標
            stress_indicators = self._identify_stress_indicators(logs)
            
            # 休憩嗜好
            preferred_break_types = self._analyze_break_preferences(logs)
            
            # モチベーション要因
            motivation_triggers = self._identify_motivation_triggers(logs)
            
            # 注意散漫要因
            distraction_sources = self._identify_distraction_sources(logs)
            
            # 最適作業環境
            optimal_work_environment = self._analyze_optimal_environment(logs)
            
            return PersonalCharacteristics(
                attention_span=attention_span,
                productivity_patterns=productivity_patterns,
                stress_indicators=stress_indicators,
                preferred_break_types=preferred_break_types,
                motivation_triggers=motivation_triggers,
                distraction_sources=distraction_sources,
                optimal_work_environment=optimal_work_environment
            )
            
        except Exception as e:
            logger.error(f"Error analyzing personal characteristics: {e}")
            return PersonalCharacteristics(
                attention_span=25.0,
                productivity_patterns={},
                stress_indicators=[],
                preferred_break_types=[],
                motivation_triggers=[],
                distraction_sources=[],
                optimal_work_environment={}
            )
    
    def _analyze_temporal_patterns(self, logs: List[BehaviorLog]) -> Dict[str, Any]:
        """時間パターン分析"""
        try:
            # 曜日別パターン
            weekday_patterns = self._analyze_weekday_patterns(logs)
            
            # 月間パターン
            monthly_patterns = self._analyze_monthly_patterns(logs)
            
            # 季節パターン（データが十分にある場合）
            seasonal_patterns = self._analyze_seasonal_patterns(logs)
            
            return {
                'weekday_patterns': weekday_patterns,
                'monthly_patterns': monthly_patterns,
                'seasonal_patterns': seasonal_patterns,
                'optimal_time_windows': self._identify_optimal_time_windows(logs)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing temporal patterns: {e}")
            return {}
    
    def _create_minimal_profile(self, user_id: str) -> Dict[str, Any]:
        """最小限プロファイル作成"""
        return {
            'user_id': user_id,
            'profile_version': '0.1.0',
            'creation_timestamp': datetime.utcnow().isoformat(),
            'confidence_score': 0.1,
            'status': 'minimal',
            'basic_characteristics': {
                'basic_stats': {
                    'avg_focus': 0.5,
                    'focus_variability': 0.0,
                    'avg_posture': 0.5,
                    'total_sessions': 0,
                    'smartphone_usage_rate': 0.0
                }
            },
            'message': 'Insufficient data for comprehensive profiling'
        }
    
    # ========== Utility Methods ==========
    
    def _generate_profile_version(self) -> str:
        """プロファイルバージョン生成"""
        return f"1.0.{int(datetime.utcnow().timestamp())}"
    
    def _calculate_profile_confidence(self, logs: List[BehaviorLog]) -> float:
        """プロファイル信頼度計算"""
        try:
            data_points = len(logs)
            observation_days = self._calculate_observation_period(logs)
            
            # データ量ベースの信頼度
            data_confidence = min(data_points / 1000, 1.0)
            
            # 観察期間ベースの信頼度
            period_confidence = min(observation_days / 30, 1.0)
            
            # 統合信頼度
            return (data_confidence * 0.6 + period_confidence * 0.4)
            
        except Exception:
            return 0.5
    
    def _calculate_observation_period(self, logs: List[BehaviorLog]) -> int:
        """観察期間計算（日数）"""
        if not logs:
            return 0
        return (logs[0].timestamp - logs[-1].timestamp).days + 1
    
    # 以下のメソッドは段階的実装が必要
    def _calculate_hourly_performance(self, logs):
        """時間別パフォーマンス計算 - 実装予定"""
        return {}
    
    def _analyze_focus_patterns(self, logs):
        """集中パターン分析 - 実装予定"""
        return {}
    
    def _calculate_behavioral_consistency(self, logs):
        """行動一貫性計算 - 実装予定"""
        return 0.5
    
    def _calculate_attention_span(self, logs):
        """注意継続時間計算 - 実装予定"""
        return 25.0
    
    def _analyze_productivity_patterns(self, logs):
        """生産性パターン分析 - 実装予定"""
        return {}
    
    def _identify_stress_indicators(self, logs):
        """ストレス指標特定 - 実装予定"""
        return []
    
    def _analyze_break_preferences(self, logs):
        """休憩嗜好分析 - 実装予定"""
        return []
    
    def _identify_motivation_triggers(self, logs):
        """モチベーション要因特定 - 実装予定"""
        return []
    
    def _identify_distraction_sources(self, logs):
        """注意散漫要因特定 - 実装予定"""
        return []
    
    def _analyze_optimal_environment(self, logs):
        """最適環境分析 - 実装予定"""
        return {}
    
    def _analyze_weekday_patterns(self, logs):
        """曜日パターン分析 - 実装予定"""
        return {}
    
    def _analyze_monthly_patterns(self, logs):
        """月間パターン分析 - 実装予定"""
        return {}
    
    def _analyze_seasonal_patterns(self, logs):
        """季節パターン分析 - 実装予定"""
        return {}
    
    def _identify_optimal_time_windows(self, logs):
        """最適時間窓特定 - 実装予定"""
        return []
    
    def _analyze_learning_preferences(self, user_id, logs):
        """学習嗜好分析 - 実装予定"""
        return {}
    
    def _analyze_behavioral_predictability(self, logs):
        """行動予測可能性分析 - 実装予定"""
        return {}
    
    def _evaluate_adaptation_capacity(self, user_id, logs):
        """適応能力評価 - 実装予定"""
        return {}
    
    def _analyze_feedback_patterns(self, feedback_data):
        """フィードバックパターン分析 - 実装予定"""
        return {}
    
    def _update_learning_history(self, user_id, feedback_data):
        """学習履歴更新 - 実装予定"""
        pass
    
    def _adjust_profile_from_feedback(self, current_profile, feedback_insights):
        """フィードバックからプロファイル調整 - 実装予定"""
        return current_profile
    
    def _update_adaptation_metrics(self, user_id, feedback_insights):
        """適応メトリクス更新 - 実装予定"""
        pass
    
    def _calculate_drift_metrics(self, baseline, current):
        """ドリフトメトリクス計算 - 実装予定"""
        return {}
    
    def _assess_drift_significance(self, drift_metrics):
        """ドリフト重要度評価 - 実装予定"""
        return False
    
    def _analyze_drift_factors(self, baseline, current):
        """ドリフト要因分析 - 実装予定"""
        return []
    
    def _recommend_drift_actions(self, significant_drift, drift_factors):
        """ドリフト対応推奨 - 実装予定"""
        return []
    
    def _generate_basic_insights(self, profile):
        """基本インサイト生成 - 実装予定"""
        return []
    
    def _generate_temporal_insights(self, profile):
        """時間インサイト生成 - 実装予定"""
        return []
    
    def _generate_learning_insights(self, user_id, profile):
        """学習インサイト生成 - 実装予定"""
        return []
    
    def _generate_improvement_suggestions(self, profile):
        """改善提案生成 - 実装予定"""
        return []
    
    def _assess_profile_maturity(self, profile):
        """プロファイル成熟度評価 - 実装予定"""
        return "developing" 