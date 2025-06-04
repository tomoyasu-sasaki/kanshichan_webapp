"""
推奨システム - 個人化推奨エンジン

ユーザーの行動履歴・嗜好・コンテキストに基づいた推奨事項生成
- 行動パターンベース推奨
- コンテキスト考慮推奨
- 適応学習推奨
- 多様性確保推奨
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging
import json
import math

from models.behavior_log import BehaviorLog
from models.user_profile import UserProfile
# 循環インポートを避けるため、必要時に遅延インポートを使用
# from .personalization_engine import PersonalizationEngine
from ..ai_ml.advanced_behavior_analyzer import AdvancedBehaviorAnalyzer
from ..ai_ml.pattern_recognition import PatternRecognizer
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RecommendationType(Enum):
    """推奨タイプ分類"""
    BREAK_TIMING = "break_timing"
    FOCUS_ENHANCEMENT = "focus_enhancement"
    POSTURE_IMPROVEMENT = "posture_improvement"
    PRODUCTIVITY_BOOST = "productivity_boost"
    HEALTH_REMINDER = "health_reminder"
    MOTIVATION_BOOST = "motivation_boost"


class ContextType(Enum):
    """コンテキストタイプ"""
    TIME_BASED = "time_based"
    BEHAVIOR_BASED = "behavior_based"
    ENVIRONMENT_BASED = "environment_based"
    GOAL_BASED = "goal_based"


@dataclass
class RecommendationRule:
    """推奨ルールデータクラス"""
    rule_id: str
    name: str
    recommendation_type: RecommendationType
    conditions: Dict[str, Any]
    actions: List[str]
    priority: int
    effectiveness_score: float
    usage_count: int


@dataclass
class ContextualRecommendation:
    """コンテキスト対応推奨データクラス"""
    recommendation_id: str
    content: str
    recommendation_type: RecommendationType
    context_score: float
    personalization_score: float
    urgency_level: str
    expected_effectiveness: float
    context_factors: List[str]
    timing_constraint: Optional[Dict[str, Any]]


class RecommendationSystem:
    """推奨システム
    
    ユーザーの状況と個人特性に基づいて最適な推奨事項を生成・配信
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('recommendation_system', {})
        
        # 推奨システムパラメータ
        self.system_params = {
            'max_concurrent_recommendations': self.config.get('max_concurrent', 3),
            'recommendation_cooldown_minutes': self.config.get('cooldown_minutes', 10),
            'effectiveness_threshold': self.config.get('effectiveness_threshold', 0.6),
            'context_weight': self.config.get('context_weight', 0.4)
        }
        
        # 推奨ルール
        self.recommendation_rules = {}
        self.rule_effectiveness = defaultdict(list)
        
        # コンテキスト管理
        self.context_history = defaultdict(list)
        self.active_recommendations = {}
        
        # 初期化
        self._initialize_default_rules()
        
        logger.info("RecommendationSystem initialized with contextual capabilities")
    
    def generate_contextual_recommendations(self, user_id: str, 
                                          current_context: Dict[str, Any],
                                          user_profile: Dict[str, Any],
                                          behavior_logs: List[BehaviorLog]) -> List[ContextualRecommendation]:
        """コンテキスト対応推奨生成
        
        Args:
            user_id: ユーザーID
            current_context: 現在のコンテキスト
            user_profile: ユーザープロファイル
            behavior_logs: 行動ログリスト
            
        Returns:
            List[ContextualRecommendation]: コンテキスト対応推奨リスト
        """
        try:
            logger.info(f"Generating contextual recommendations for user {user_id}")
            
            # コンテキスト分析
            context_analysis = self._analyze_current_context(current_context, behavior_logs)
            
            # 適用可能ルール抽出
            applicable_rules = self._find_applicable_rules(
                context_analysis, user_profile, behavior_logs
            )
            
            # 推奨候補生成
            recommendation_candidates = self._generate_recommendation_candidates(
                applicable_rules, context_analysis, user_profile
            )
            
            # コンテキストスコアリング
            scored_recommendations = self._score_recommendations_by_context(
                recommendation_candidates, context_analysis, user_profile
            )
            
            # パーソナライゼーション適用
            personalized_recommendations = self._apply_personalization(
                scored_recommendations, user_profile, context_analysis
            )
            
            # 推奨フィルタリング・ランキング
            final_recommendations = self._filter_and_rank_recommendations(
                personalized_recommendations, user_id, current_context
            )
            
            # アクティブ推奨として記録
            self._record_active_recommendations(user_id, final_recommendations)
            
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error generating contextual recommendations: {e}", exc_info=True)
            return []
    
    def evaluate_recommendation_effectiveness(self, user_id: str,
                                            recommendation_id: str,
                                            outcome: Dict[str, Any]) -> float:
        """推奨事項効果評価
        
        Args:
            user_id: ユーザーID
            recommendation_id: 推奨事項ID
            outcome: 結果データ
            
        Returns:
            float: 効果スコア
        """
        try:
            # 効果メトリクス計算
            effectiveness_metrics = self._calculate_effectiveness_metrics(outcome)
            
            # 統合効果スコア計算
            effectiveness_score = self._calculate_overall_effectiveness(effectiveness_metrics)
            
            # ルール効果履歴更新
            self._update_rule_effectiveness(recommendation_id, effectiveness_score)
            
            # ユーザー固有効果履歴更新
            self._update_user_effectiveness_history(user_id, recommendation_id, effectiveness_score)
            
            logger.info(f"Recommendation effectiveness evaluated: {effectiveness_score}")
            return effectiveness_score
            
        except Exception as e:
            logger.error(f"Error evaluating recommendation effectiveness: {e}", exc_info=True)
            return 0.0
    
    def get_optimal_recommendation_timing(self, user_id: str,
                                        recommendation_type: RecommendationType,
                                        user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """最適推奨タイミング取得
        
        Args:
            user_id: ユーザーID
            recommendation_type: 推奨タイプ
            user_profile: ユーザープロファイル
            
        Returns:
            Dict: 最適タイミング情報
        """
        try:
            # ユーザーの時間パターン分析
            temporal_patterns = user_profile.get('temporal_patterns', {})
            
            # 推奨タイプ別最適時間計算
            optimal_times = self._calculate_type_specific_optimal_times(
                recommendation_type, temporal_patterns
            )
            
            # 現在時刻からの推奨タイミング算出
            next_optimal_timing = self._calculate_next_optimal_timing(
                optimal_times, user_id
            )
            
            return {
                'next_optimal_time': next_optimal_timing,
                'optimal_time_windows': optimal_times,
                'confidence': self._calculate_timing_confidence(optimal_times, user_profile)
            }
            
        except Exception as e:
            logger.error(f"Error getting optimal recommendation timing: {e}", exc_info=True)
            return {'next_optimal_time': None, 'confidence': 0.0}
    
    def customize_recommendation_for_user(self, base_recommendation: str,
                                        user_profile: Dict[str, Any],
                                        context: Dict[str, Any]) -> str:
        """ユーザー向け推奨カスタマイズ
        
        Args:
            base_recommendation: 基本推奨内容
            user_profile: ユーザープロファイル
            context: コンテキスト情報
            
        Returns:
            str: カスタマイズされた推奨内容
        """
        try:
            # ユーザー特性抽出
            user_characteristics = self._extract_user_characteristics(user_profile)
            
            # コンテキスト要因抽出
            context_factors = self._extract_context_factors(context)
            
            # 推奨内容のパーソナライズ
            personalized_content = self._personalize_recommendation_content(
                base_recommendation, user_characteristics, context_factors
            )
            
            # トーン・スタイル調整
            customized_content = self._adjust_communication_style(
                personalized_content, user_characteristics
            )
            
            return customized_content
            
        except Exception as e:
            logger.error(f"Error customizing recommendation: {e}", exc_info=True)
            return base_recommendation
    
    # ========== Private Methods ==========
    
    def _initialize_default_rules(self):
        """デフォルト推奨ルール初期化"""
        try:
            default_rules = [
                # 休憩タイミング推奨
                RecommendationRule(
                    rule_id="break_001",
                    name="Extended focus break reminder",
                    recommendation_type=RecommendationType.BREAK_TIMING,
                    conditions={"focus_duration_minutes": ">= 45", "break_taken": False},
                    actions=["5分間の休憩を取りましょう", "目を休めて遠くを見てください"],
                    priority=8,
                    effectiveness_score=0.8,
                    usage_count=0
                ),
                
                # 集中力強化推奨
                RecommendationRule(
                    rule_id="focus_001",
                    name="Focus enhancement reminder",
                    recommendation_type=RecommendationType.FOCUS_ENHANCEMENT,
                    conditions={"focus_score": "<= 0.4", "distraction_detected": True},
                    actions=["深呼吸をして集中を取り戻しましょう", "気になることをメモして後で対処しましょう"],
                    priority=7,
                    effectiveness_score=0.7,
                    usage_count=0
                ),
                
                # 姿勢改善推奨
                RecommendationRule(
                    rule_id="posture_001",
                    name="Posture improvement reminder",
                    recommendation_type=RecommendationType.POSTURE_IMPROVEMENT,
                    conditions={"posture_score": "<= 0.3", "sitting_duration_minutes": ">= 30"},
                    actions=["背筋を伸ばして姿勢を正しましょう", "肩の力を抜いてリラックスしましょう"],
                    priority=6,
                    effectiveness_score=0.6,
                    usage_count=0
                ),
                
                # 生産性向上推奨
                RecommendationRule(
                    rule_id="productivity_001",
                    name="Productivity boost reminder",
                    recommendation_type=RecommendationType.PRODUCTIVITY_BOOST,
                    conditions={"efficiency_score": "<= 0.5", "time_of_day": "morning"},
                    actions=["最も重要なタスクから始めましょう", "タイマーを25分にセットしてポモドーロテクニックを試しましょう"],
                    priority=5,
                    effectiveness_score=0.65,
                    usage_count=0
                )
            ]
            
            for rule in default_rules:
                self.recommendation_rules[rule.rule_id] = rule
                
            logger.info(f"Initialized {len(default_rules)} default recommendation rules")
            
        except Exception as e:
            logger.error(f"Error initializing default rules: {e}")
    
    def _analyze_current_context(self, context: Dict[str, Any],
                                logs: List[BehaviorLog]) -> Dict[str, Any]:
        """現在のコンテキスト分析"""
        try:
            current_time = datetime.now()
            
            # 時間ベースコンテキスト
            time_context = {
                'hour': current_time.hour,
                'day_of_week': current_time.weekday(),
                'is_working_hours': 9 <= current_time.hour <= 17,
                'time_since_break': self._calculate_time_since_last_break(logs)
            }
            
            # 行動ベースコンテキスト
            behavior_context = {
                'current_focus_level': self._get_current_focus_level(logs),
                'recent_focus_trend': self._calculate_recent_focus_trend(logs),
                'distraction_frequency': self._calculate_distraction_frequency(logs),
                'session_duration': self._calculate_current_session_duration(logs)
            }
            
            # 環境ベースコンテキスト
            environment_context = context.get('environment', {})
            
            return {
                'time_context': time_context,
                'behavior_context': behavior_context,
                'environment_context': environment_context,
                'overall_readiness': self._assess_recommendation_readiness(
                    time_context, behavior_context
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing current context: {e}")
            return {}
    
    def _find_applicable_rules(self, context_analysis: Dict[str, Any],
                              user_profile: Dict[str, Any],
                              logs: List[BehaviorLog]) -> List[RecommendationRule]:
        """適用可能ルール抽出"""
        try:
            applicable_rules = []
            
            for rule in self.recommendation_rules.values():
                if self._evaluate_rule_conditions(rule, context_analysis, user_profile, logs):
                    applicable_rules.append(rule)
            
            # 効果性でソート
            applicable_rules.sort(key=lambda r: r.effectiveness_score, reverse=True)
            
            return applicable_rules
            
        except Exception as e:
            logger.error(f"Error finding applicable rules: {e}")
            return []
    
    def _generate_recommendation_candidates(self, rules: List[RecommendationRule],
                                          context_analysis: Dict[str, Any],
                                          user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """推奨候補生成"""
        try:
            candidates = []
            
            for rule in rules:
                for action in rule.actions:
                    candidate = {
                        'rule_id': rule.rule_id,
                        'content': action,
                        'type': rule.recommendation_type,
                        'priority': rule.priority,
                        'base_effectiveness': rule.effectiveness_score
                    }
                    candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error generating recommendation candidates: {e}")
            return []
    
    def _score_recommendations_by_context(self, candidates: List[Dict[str, Any]],
                                        context_analysis: Dict[str, Any],
                                        user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """コンテキストスコアリング"""
        try:
            scored_candidates = []
            
            for candidate in candidates:
                # 時間コンテキストスコア
                time_score = self._calculate_time_context_score(
                    candidate, context_analysis.get('time_context', {})
                )
                
                # 行動コンテキストスコア
                behavior_score = self._calculate_behavior_context_score(
                    candidate, context_analysis.get('behavior_context', {})
                )
                
                # 統合コンテキストスコア
                context_score = (time_score * 0.4 + behavior_score * 0.6)
                
                candidate['context_score'] = context_score
                scored_candidates.append(candidate)
            
            return scored_candidates
            
        except Exception as e:
            logger.error(f"Error scoring recommendations by context: {e}")
            return candidates
    
    # ========== Utility Methods ==========
    
    def _evaluate_rule_conditions(self, rule: RecommendationRule,
                                 context_analysis: Dict[str, Any],
                                 user_profile: Dict[str, Any],
                                 logs: List[BehaviorLog]) -> bool:
        """ルール条件評価"""
        try:
            conditions = rule.conditions
            
            # 簡易条件評価実装
            for condition_key, condition_value in conditions.items():
                if condition_key == "focus_duration_minutes":
                    current_duration = self._calculate_current_session_duration(logs)
                    if not self._evaluate_numeric_condition(current_duration, condition_value):
                        return False
                
                elif condition_key == "focus_score":
                    current_focus = self._get_current_focus_level(logs)
                    if not self._evaluate_numeric_condition(current_focus, condition_value):
                        return False
                
                elif condition_key == "posture_score":
                    current_posture = self._get_current_posture_score(logs)
                    if not self._evaluate_numeric_condition(current_posture, condition_value):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating rule conditions: {e}")
            return False
    
    def _evaluate_numeric_condition(self, value: float, condition: str) -> bool:
        """数値条件評価"""
        try:
            if ">=" in condition:
                threshold = float(condition.replace(">=", "").strip())
                return value >= threshold
            elif "<=" in condition:
                threshold = float(condition.replace("<=", "").strip())
                return value <= threshold
            elif ">" in condition:
                threshold = float(condition.replace(">", "").strip())
                return value > threshold
            elif "<" in condition:
                threshold = float(condition.replace("<", "").strip())
                return value < threshold
            elif "==" in condition:
                threshold = float(condition.replace("==", "").strip())
                return abs(value - threshold) < 0.01
            
            return True
            
        except Exception:
            return False
    
    # 以下のメソッドは段階的実装が必要
    def _calculate_time_since_last_break(self, logs):
        """最後の休憩からの時間計算 - 実装予定"""
        return 30
    
    def _get_current_focus_level(self, logs):
        """現在の集中度取得 - 実装予定"""
        return 0.6 if logs else 0.5
    
    def _calculate_recent_focus_trend(self, logs):
        """最近の集中トレンド計算 - 実装予定"""
        return "stable"
    
    def _calculate_distraction_frequency(self, logs):
        """注意散漫頻度計算 - 実装予定"""
        return 0.2
    
    def _calculate_current_session_duration(self, logs):
        """現在セッション時間計算 - 実装予定"""
        return 25 if logs else 0
    
    def _assess_recommendation_readiness(self, time_context, behavior_context):
        """推奨準備状況評価 - 実装予定"""
        return 0.7
    
    def _get_current_posture_score(self, logs):
        """現在の姿勢スコア取得 - 実装予定"""
        return 0.5 if logs else 0.5
    
    def _calculate_time_context_score(self, candidate, time_context):
        """時間コンテキストスコア計算 - 実装予定"""
        return 0.7
    
    def _calculate_behavior_context_score(self, candidate, behavior_context):
        """行動コンテキストスコア計算 - 実装予定"""
        return 0.6
    
    def _apply_personalization(self, scored_recommendations, user_profile, context_analysis):
        """パーソナライゼーション適用 - 実装予定"""
        return scored_recommendations
    
    def _filter_and_rank_recommendations(self, recommendations, user_id, context):
        """推奨フィルタリング・ランキング - 実装予定"""
        return recommendations[:3]
    
    def _record_active_recommendations(self, user_id, recommendations):
        """アクティブ推奨記録 - 実装予定"""
        self.active_recommendations[user_id] = recommendations
    
    def _calculate_effectiveness_metrics(self, outcome):
        """効果メトリクス計算 - 実装予定"""
        return {"user_satisfaction": 0.7, "behavior_improvement": 0.6}
    
    def _calculate_overall_effectiveness(self, metrics):
        """統合効果スコア計算 - 実装予定"""
        return 0.65
    
    def _update_rule_effectiveness(self, recommendation_id, effectiveness_score):
        """ルール効果更新 - 実装予定"""
        pass
    
    def _update_user_effectiveness_history(self, user_id, recommendation_id, effectiveness_score):
        """ユーザー効果履歴更新 - 実装予定"""
        pass
    
    def _calculate_type_specific_optimal_times(self, recommendation_type, temporal_patterns):
        """タイプ別最適時間計算 - 実装予定"""
        return [{"hour": 10, "effectiveness": 0.8}, {"hour": 14, "effectiveness": 0.7}]
    
    def _calculate_next_optimal_timing(self, optimal_times, user_id):
        """次回最適タイミング計算 - 実装予定"""
        return datetime.now() + timedelta(minutes=30)
    
    def _calculate_timing_confidence(self, optimal_times, user_profile):
        """タイミング信頼度計算 - 実装予定"""
        return 0.7
    
    def _extract_user_characteristics(self, user_profile):
        """ユーザー特性抽出 - 実装予定"""
        return {}
    
    def _extract_context_factors(self, context):
        """コンテキスト要因抽出 - 実装予定"""
        return []
    
    def _personalize_recommendation_content(self, content, characteristics, factors):
        """推奨内容パーソナライズ - 実装予定"""
        return content
    
    def _adjust_communication_style(self, content, characteristics):
        """コミュニケーションスタイル調整 - 実装予定"""
        return content 