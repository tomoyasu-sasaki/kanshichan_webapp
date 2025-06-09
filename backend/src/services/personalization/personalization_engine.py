"""
Personalization Engine Service

パーソナライゼーションエンジン
個人最適化、適応学習、コンテキスト対応推奨システム
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import logging
import json

from models.behavior_log import BehaviorLog
from models.user_profile import UserProfile
from ..ai_ml.advanced_behavior_analyzer import AdvancedBehaviorAnalyzer
from ..ai_ml.pattern_recognition import PatternRecognizer
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WorkStyle(Enum):
    """作業スタイル分類"""
    MORNING_PERSON = "morning_person"
    NIGHT_PERSON = "night_person"
    FOCUSED_WORKER = "focused_worker"
    DISTRIBUTED_WORKER = "distributed_worker"
    FLEXIBLE_WORKER = "flexible_worker"


class PersonalizationLevel(Enum):
    """パーソナライゼーションレベル"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class PersonalizedRecommendation:
    """パーソナライズ推奨データクラス"""
    recommendation_id: str
    type: str
    priority: str
    message: str
    personalization_score: float
    context_factors: List[str]
    expected_impact: float
    timing: Dict[str, Any]
    action_required: bool


@dataclass
class UserPersonalityProfile:
    """ユーザー性格プロファイル"""
    work_style: WorkStyle
    focus_duration_avg: float
    optimal_break_frequency: int
    stress_tolerance: float
    distraction_sensitivity: float
    learning_preference: str
    motivation_factors: List[str]


class PersonalizationEngine:
    """パーソナライゼーションエンジン
    
    ユーザーの行動パターンを学習し、個人に最適化された推奨事項とアドバイスを生成
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('personalization', {})
        
        # パーソナライゼーションパラメータ
        self.learning_params = {
            'min_data_points': self.config.get('min_data_points', 100),
            'adaptation_rate': self.config.get('adaptation_rate', 0.1),
            'confidence_threshold': self.config.get('confidence_threshold', 0.7),
            'context_weight': self.config.get('context_weight', 0.3)
        }
        
        # 推奨システムパラメータ
        self.recommendation_params = {
            'max_recommendations': self.config.get('max_recommendations', 5),
            'diversity_factor': self.config.get('diversity_factor', 0.4),
            'recency_weight': self.config.get('recency_weight', 0.6),
            'effectiveness_weight': self.config.get('effectiveness_weight', 0.8)
        }
        
        # 個人プロファイルキャッシュ
        self.user_profiles = {}
        self.recommendation_history = defaultdict(list)
        self.learning_cache = {}
        
        logger.info("PersonalizationEngine initialized with adaptive learning capabilities")
    
    def get_personalized_recommendations(self, user_id: str, logs: List[BehaviorLog],
                                       context: Dict[str, Any]) -> List[PersonalizedRecommendation]:
        """個人最適化推奨事項生成
        
        Args:
            user_id: ユーザーID
            logs: 行動ログリスト
            context: コンテキスト情報（時間、環境など）
            
        Returns:
            List[PersonalizedRecommendation]: パーソナライズド推奨事項リスト
        """
        try:
            logger.info(f"Generating personalized recommendations for user {user_id}")
            
            # ユーザープロファイル取得/構築
            user_profile = self._get_or_build_user_profile(user_id, logs)
            
            # コンテキスト分析
            context_analysis = self._analyze_current_context(context, logs)
            
            # 基本推奨事項生成
            base_recommendations = self._generate_base_recommendations(
                user_profile, context_analysis, logs
            )
            
            # パーソナライゼーション適用
            personalized_recommendations = self._apply_personalization(
                base_recommendations, user_profile, context_analysis
            )
            
            # 推奨事項ランキング
            ranked_recommendations = self._rank_recommendations(
                personalized_recommendations, user_profile, context_analysis
            )
            
            # 履歴記録
            self._record_recommendations(user_id, ranked_recommendations)
            
            return ranked_recommendations[:self.recommendation_params['max_recommendations']]
            
        except Exception as e:
            logger.error(f"Error generating personalized recommendations: {e}", exc_info=True)
            return []
    
    def update_recommendation_feedback(self, user_id: str, recommendation_id: str,
                                     feedback: Dict[str, Any]) -> bool:
        """推奨事項フィードバック更新
        
        Args:
            user_id: ユーザーID
            recommendation_id: 推奨事項ID
            feedback: フィードバック情報
            
        Returns:
            bool: 更新成功フラグ
        """
        try:
            # フィードバック記録
            feedback_record = {
                'recommendation_id': recommendation_id,
                'feedback': feedback,
                'timestamp': datetime.utcnow(),
                'user_id': user_id
            }
            
            # ユーザープロファイル更新
            self._update_user_profile_from_feedback(user_id, feedback_record)
            
            # 学習モデル更新
            self._update_learning_model(user_id, feedback_record)
            
            logger.info(f"Updated recommendation feedback for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating recommendation feedback: {e}", exc_info=True)
            return False
    
    def adapt_to_behavioral_changes(self, user_id: str, logs: List[BehaviorLog]) -> Dict[str, Any]:
        """行動変化への適応
        
        Args:
            user_id: ユーザーID
            logs: 最新の行動ログリスト
            
        Returns:
            Dict: 適応結果
        """
        try:
            # 既存プロファイル取得
            current_profile = self.user_profiles.get(user_id)
            if not current_profile:
                return {'adapted': False, 'reason': 'No existing profile'}
            
            # 行動変化検出
            behavior_changes = self._detect_behavioral_changes(user_id, logs)
            
            # 適応必要性評価
            adaptation_needed = self._assess_adaptation_need(behavior_changes)
            
            if adaptation_needed:
                # プロファイル更新
                updated_profile = self._adapt_user_profile(
                    current_profile, behavior_changes, logs
                )
                self.user_profiles[user_id] = updated_profile
                
                # 学習パラメータ調整
                self._adjust_learning_parameters(user_id, behavior_changes)
                
                return {
                    'adapted': True,
                    'changes_detected': behavior_changes,
                    'adaptation_score': self._calculate_adaptation_score(behavior_changes)
                }
            
            return {'adapted': False, 'reason': 'No significant changes detected'}
            
        except Exception as e:
            logger.error(f"Error adapting to behavioral changes: {e}", exc_info=True)
            return {'adapted': False, 'error': str(e)}
    
    def get_optimal_timing_recommendations(self, user_id: str,
                                         recommendation_type: str) -> Dict[str, Any]:
        """最適タイミング推奨
        
        Args:
            user_id: ユーザーID
            recommendation_type: 推奨タイプ
            
        Returns:
            Dict: 最適タイミング情報
        """
        try:
            user_profile = self.user_profiles.get(user_id)
            if not user_profile:
                return {'optimal_times': [], 'confidence': 0.0}
            
            # 時間帯別効果分析
            timing_analysis = self._analyze_timing_effectiveness(user_id, recommendation_type)
            
            # 最適時間帯特定
            optimal_times = self._identify_optimal_times(timing_analysis, user_profile)
            
            return {
                'optimal_times': optimal_times,
                'confidence': timing_analysis.get('confidence', 0.0),
                'factors': timing_analysis.get('key_factors', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting optimal timing recommendations: {e}", exc_info=True)
            return {'optimal_times': [], 'confidence': 0.0}
    
    # ========== Private Methods ==========
    
    def _get_or_build_user_profile(self, user_id: str,
                                  logs: List[BehaviorLog]) -> UserPersonalityProfile:
        """ユーザープロファイル取得または構築"""
        try:
            if user_id in self.user_profiles:
                # 既存プロファイルの更新チェック
                last_update = getattr(self.user_profiles[user_id], 'last_update', None)
                if last_update and (datetime.utcnow() - last_update).days < 7:
                    return self.user_profiles[user_id]
            
            # 新規プロファイル構築
            profile = self._build_user_profile(user_id, logs)
            self.user_profiles[user_id] = profile
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return self._create_default_profile()
    
    def _build_user_profile(self, user_id: str, logs: List[BehaviorLog]) -> UserPersonalityProfile:
        """ユーザープロファイル構築"""
        try:
            if len(logs) < self.learning_params['min_data_points']:
                return self._create_default_profile()
            
            # 作業スタイル分析
            work_style = self._analyze_work_style(logs)
            
            # 集中継続時間分析
            focus_duration = self._calculate_average_focus_duration(logs)
            
            # 最適休憩頻度計算
            break_frequency = self._calculate_optimal_break_frequency(logs)
            
            # ストレス耐性分析
            stress_tolerance = self._analyze_stress_tolerance(logs)
            
            # 注意散漫感度分析
            distraction_sensitivity = self._analyze_distraction_sensitivity(logs)
            
            # 学習嗜好分析
            learning_preference = self._analyze_learning_preference(user_id)
            
            # モチベーション要因分析
            motivation_factors = self._identify_motivation_factors(logs)
            
            return UserPersonalityProfile(
                work_style=work_style,
                focus_duration_avg=focus_duration,
                optimal_break_frequency=break_frequency,
                stress_tolerance=stress_tolerance,
                distraction_sensitivity=distraction_sensitivity,
                learning_preference=learning_preference,
                motivation_factors=motivation_factors
            )
            
        except Exception as e:
            logger.error(f"Error building user profile: {e}")
            return self._create_default_profile()
    
    def _analyze_current_context(self, context: Dict[str, Any],
                                logs: List[BehaviorLog]) -> Dict[str, Any]:
        """現在のコンテキスト分析"""
        try:
            current_time = datetime.now()
            
            return {
                'time_of_day': current_time.hour,
                'day_of_week': current_time.weekday(),
                'recent_focus_trend': self._calculate_recent_focus_trend(logs),
                'session_duration': self._calculate_current_session_duration(logs),
                'distraction_level': self._assess_current_distraction_level(logs),
                'environmental_factors': context.get('environment', {}),
                'user_state': context.get('state', 'normal')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing current context: {e}")
            return {'time_of_day': 12, 'day_of_week': 1}
    
    def _generate_base_recommendations(self, user_profile: UserPersonalityProfile,
                                     context_analysis: Dict[str, Any],
                                     logs: List[BehaviorLog]) -> List[Dict[str, Any]]:
        """基本推奨事項生成"""
        try:
            recommendations = []
            
            # 集中度ベース推奨
            focus_recommendations = self._generate_focus_recommendations(
                user_profile, context_analysis, logs
            )
            recommendations.extend(focus_recommendations)
            
            # 休憩ベース推奨
            break_recommendations = self._generate_break_recommendations(
                user_profile, context_analysis, logs
            )
            recommendations.extend(break_recommendations)
            
            # 健康ベース推奨
            health_recommendations = self._generate_health_recommendations(
                user_profile, context_analysis, logs
            )
            recommendations.extend(health_recommendations)
            
            # 生産性ベース推奨
            productivity_recommendations = self._generate_productivity_recommendations(
                user_profile, context_analysis, logs
            )
            recommendations.extend(productivity_recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating base recommendations: {e}")
            return []
    
    def _apply_personalization(self, recommendations: List[Dict[str, Any]],
                              user_profile: UserPersonalityProfile,
                              context_analysis: Dict[str, Any]) -> List[PersonalizedRecommendation]:
        """パーソナライゼーション適用"""
        try:
            personalized = []
            
            for i, rec in enumerate(recommendations):
                # パーソナライゼーションスコア計算
                personalization_score = self._calculate_personalization_score(
                    rec, user_profile, context_analysis
                )
                
                # コンテキスト要因抽出
                context_factors = self._extract_context_factors(
                    rec, context_analysis
                )
                
                # 期待インパクト計算
                expected_impact = self._calculate_expected_impact(
                    rec, user_profile, personalization_score
                )
                
                # タイミング最適化
                optimal_timing = self._optimize_recommendation_timing(
                    rec, user_profile, context_analysis
                )
                
                personalized_rec = PersonalizedRecommendation(
                    recommendation_id=f"pers_{datetime.utcnow().timestamp()}_{i}",
                    type=rec.get('type', 'general'),
                    priority=rec.get('priority', 'medium'),
                    message=self._personalize_message(rec.get('message', ''), user_profile),
                    personalization_score=personalization_score,
                    context_factors=context_factors,
                    expected_impact=expected_impact,
                    timing=optimal_timing,
                    action_required=rec.get('action_required', False)
                )
                
                personalized.append(personalized_rec)
            
            return personalized
            
        except Exception as e:
            logger.error(f"Error applying personalization: {e}")
            return []
    
    def _rank_recommendations(self, recommendations: List[PersonalizedRecommendation],
                             user_profile: UserPersonalityProfile,
                             context_analysis: Dict[str, Any]) -> List[PersonalizedRecommendation]:
        """推奨事項ランキング"""
        try:
            def ranking_score(rec: PersonalizedRecommendation) -> float:
                # 基本スコア計算
                base_score = rec.personalization_score * 0.4
                
                # 期待インパクト
                impact_score = rec.expected_impact * 0.3
                
                # 優先度スコア
                priority_scores = {'high': 1.0, 'medium': 0.7, 'low': 0.4}
                priority_score = priority_scores.get(rec.priority, 0.5) * 0.2
                
                # タイミング適合度
                timing_score = self._calculate_timing_score(rec, context_analysis) * 0.1
                
                return base_score + impact_score + priority_score + timing_score
            
            # スコア順でソート
            recommendations.sort(key=ranking_score, reverse=True)
            
            # 多様性考慮
            diversified = self._apply_diversity_filter(recommendations)
            
            return diversified
            
        except Exception as e:
            logger.error(f"Error ranking recommendations: {e}")
            return recommendations
    
    # ========== Utility Methods ==========
    
    def _create_default_profile(self) -> UserPersonalityProfile:
        """デフォルトプロファイル作成"""
        return UserPersonalityProfile(
            work_style=WorkStyle.FLEXIBLE_WORKER,
            focus_duration_avg=25.0,
            optimal_break_frequency=4,
            stress_tolerance=0.5,
            distraction_sensitivity=0.5,
            learning_preference="balanced",
            motivation_factors=["productivity", "health"]
        )
    
    def _analyze_work_style(self, logs: List[BehaviorLog]) -> WorkStyle:
        """作業スタイル分析"""
        try:
            # 時間帯別集中度分析
            hourly_focus = defaultdict(list)
            for log in logs:
                hour = log.timestamp.hour
                if log.focus_score:
                    hourly_focus[hour].append(log.focus_score)
            
            # 平均集中度計算
            hourly_avg = {h: np.mean(scores) for h, scores in hourly_focus.items() if scores}
            
            if not hourly_avg:
                return WorkStyle.FLEXIBLE_WORKER
            
            # ピーク時間帯特定
            peak_hour = max(hourly_avg, key=hourly_avg.get)
            
            # 分類
            if peak_hour < 12:
                return WorkStyle.MORNING_PERSON
            elif peak_hour > 18:
                return WorkStyle.NIGHT_PERSON
            else:
                # 集中持続性分析
                avg_session_length = self._calculate_average_session_length(logs)
                if avg_session_length > 45:
                    return WorkStyle.FOCUSED_WORKER
                else:
                    return WorkStyle.DISTRIBUTED_WORKER
                    
        except Exception as e:
            logger.error(f"Error analyzing work style: {e}")
            return WorkStyle.FLEXIBLE_WORKER
    
    # 以下のメソッドは段階的実装が必要
    def _calculate_average_focus_duration(self, logs):
        """平均集中継続時間計算 - 実装予定"""
        return 25.0
    
    def _calculate_optimal_break_frequency(self, logs):
        """最適休憩頻度計算 - 実装予定"""
        return 4
    
    def _analyze_stress_tolerance(self, logs):
        """ストレス耐性分析 - 実装予定"""
        return 0.5
    
    def _analyze_distraction_sensitivity(self, logs):
        """注意散漫感度分析 - 実装予定"""
        return 0.5
    
    def _analyze_learning_preference(self, user_id):
        """学習嗜好分析 - 実装予定"""
        return "balanced"
    
    def _identify_motivation_factors(self, logs):
        """モチベーション要因特定 - 実装予定"""
        return ["productivity", "health"]
    
    def _calculate_recent_focus_trend(self, logs):
        """最近の集中トレンド計算 - 実装予定"""
        return "stable"
    
    def _calculate_current_session_duration(self, logs):
        """現在セッション時間計算 - 実装予定"""
        return 20
    
    def _assess_current_distraction_level(self, logs):
        """現在の注意散漫レベル評価 - 実装予定"""
        return 0.3
    
    def _generate_focus_recommendations(self, user_profile, context_analysis, logs):
        """集中推奨事項生成 - 実装予定"""
        return [{"type": "focus", "priority": "medium", "message": "深呼吸で集中力を高めましょう"}]
    
    def _generate_break_recommendations(self, user_profile, context_analysis, logs):
        """休憩推奨事項生成 - 実装予定"""
        return [{"type": "break", "priority": "high", "message": "5分間の休憩を取りましょう"}]
    
    def _generate_health_recommendations(self, user_profile, context_analysis, logs):
        """健康推奨事項生成 - 実装予定"""
        return [{"type": "health", "priority": "medium", "message": "姿勢を正してください"}]
    
    def _generate_productivity_recommendations(self, user_profile, context_analysis, logs):
        """生産性推奨事項生成 - 実装予定"""
        return [{"type": "productivity", "priority": "low", "message": "タスクを整理しましょう"}]
    
    def _calculate_personalization_score(self, rec, user_profile, context_analysis):
        """パーソナライゼーションスコア計算 - 実装予定"""
        return 0.7
    
    def _extract_context_factors(self, rec, context_analysis):
        """コンテキスト要因抽出 - 実装予定"""
        return ["time_of_day", "focus_level"]
    
    def _calculate_expected_impact(self, rec, user_profile, personalization_score):
        """期待インパクト計算 - 実装予定"""
        return 0.6
    
    def _optimize_recommendation_timing(self, rec, user_profile, context_analysis):
        """推奨タイミング最適化 - 実装予定"""
        return {"immediate": True, "optimal_delay": 0}
    
    def _personalize_message(self, message, user_profile):
        """メッセージパーソナライズ - 実装予定"""
        return message
    
    def _calculate_timing_score(self, rec, context_analysis):
        """タイミングスコア計算 - 実装予定"""
        return 0.8
    
    def _apply_diversity_filter(self, recommendations):
        """多様性フィルタ適用 - 実装予定"""
        return recommendations
    
    def _calculate_average_session_length(self, logs):
        """平均セッション長計算 - 実装予定"""
        return 30.0
    
    def _record_recommendations(self, user_id, recommendations):
        """推奨履歴記録 - 実装予定"""
        self.recommendation_history[user_id].extend(recommendations)
    
    def _update_user_profile_from_feedback(self, user_id, feedback_record):
        """フィードバックからプロファイル更新 - 実装予定"""
        pass
    
    def _update_learning_model(self, user_id, feedback_record):
        """学習モデル更新 - 実装予定"""
        pass
    
    def _detect_behavioral_changes(self, user_id, logs):
        """行動変化検出 - 実装予定"""
        return []
    
    def _assess_adaptation_need(self, behavior_changes):
        """適応必要性評価 - 実装予定"""
        return False
    
    def _adapt_user_profile(self, current_profile, behavior_changes, logs):
        """ユーザープロファイル適応 - 実装予定"""
        return current_profile
    
    def _adjust_learning_parameters(self, user_id, behavior_changes):
        """学習パラメータ調整 - 実装予定"""
        pass
    
    def _calculate_adaptation_score(self, behavior_changes):
        """適応スコア計算 - 実装予定"""
        return 0.5
    
    def _analyze_timing_effectiveness(self, user_id, recommendation_type):
        """タイミング効果分析 - 実装予定"""
        return {"confidence": 0.7, "key_factors": ["time_of_day"]}
    
    def _identify_optimal_times(self, timing_analysis, user_profile):
        """最適時間特定 - 実装予定"""
        return [{"hour": 10, "effectiveness": 0.8}, {"hour": 14, "effectiveness": 0.7}] 