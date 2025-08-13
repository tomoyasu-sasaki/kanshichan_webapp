"""
アドバイス生成サービス

LLMを活用したパーソナライズドアドバイス生成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import json

from models.behavior_log import BehaviorLog
from models.user_profile import UserProfile
from models.analysis_result import AnalysisResult
from .llm_service import LLMService
from ..analysis.behavior_analyzer import BehaviorAnalyzer
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AdviceGenerator:
    """アドバイス生成エンジン
    
    行動分析結果とユーザープロファイルに基づく
    パーソナライズされたアドバイス生成
    - コンテキスト対応アドバイス生成
    - 時間帯別最適化
    - 個人パターン学習
    - 感情トーン調整
    """
    
    def __init__(self, 
                 llm_service: LLMService,
                 behavior_analyzer: BehaviorAnalyzer,
                 config: Dict[str, Any]):
        """初期化
        
        Args:
            llm_service: LLMサービスインスタンス
            behavior_analyzer: 行動分析エンジンインスタンス
            config: 設定辞書
        """
        self.llm_service = llm_service
        self.behavior_analyzer = behavior_analyzer
        self.config = config.get('advice_generator', {})
        
        # アドバイス生成パラメータ
        self.max_advice_length = self.config.get('max_advice_length', 150)
        self.personalization_weight = self.config.get('personalization_weight', 0.7)
        self.context_retention_hours = self.config.get('context_retention_hours', 24)
        
        # 定型アドバイステンプレート
        self.advice_templates = self._load_advice_templates()
        
        logger.info("AdviceGenerator initialized")
    
    def generate_contextual_advice(self,
                                  behavior_data: Dict[str, Any],
                                  user_id: Optional[str] = None) -> Dict[str, Any]:
        """コンテキスト対応アドバイスを生成
        
        Args:
            behavior_data: 最新の行動データ
            user_id: ユーザーID
            
        Returns:
            dict: 生成されたアドバイス
        """
        try:
            # ユーザープロファイルの取得
            user_profile = None
            if user_id:
                user_profile = UserProfile.get_by_user_id(user_id)
            
            # 現在の状況を分析
            current_context = self._analyze_current_context(behavior_data, user_profile)
            
            # アドバイスタイプを決定
            advice_type = self._determine_advice_type(current_context)
            
            # 時間帯を考慮したコンテキスト調整
            time_context = self._get_time_context()
            current_context.update(time_context)
            
            # LLMを使用してアドバイス生成
            llm_advice = self.llm_service.generate_advice(
                {'structured_analysis': current_context},
                user_profile.get_personalization_data() if user_profile else None
            )
            
            # アドバイスの後処理
            processed_advice = self._post_process_advice(
                llm_advice, advice_type, current_context, user_profile
            )
            
            return {
                'advice_text': processed_advice['advice_text'],
                'priority': processed_advice['priority'],
                'emotion': processed_advice['emotion'],
                'advice_type': advice_type,
                'context': current_context,
                'personalized': user_profile is not None,
                'generation_timestamp': datetime.now().astimezone().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating contextual advice: {e}")
            return self._generate_fallback_advice(behavior_data)
    
    def generate_personalized_advice(self,
                                   analysis_result: AnalysisResult,
                                   user_profile: UserProfile) -> Dict[str, Any]:
        """個人パターンに基づくアドバイス生成
        
        Args:
            analysis_result: 分析結果
            user_profile: ユーザープロファイル
            
        Returns:
            dict: パーソナライズされたアドバイス
        """
        try:
            # 個人の行動パターンを分析
            personal_patterns = self._analyze_personal_patterns(analysis_result, user_profile)
            
            # 学習スタイルに基づく調整
            learning_context = self._adapt_to_learning_style(personal_patterns, user_profile)
            
            # モチベーションスタイルの考慮
            motivation_context = self._apply_motivation_style(learning_context, user_profile)
            
            # LLMでアドバイス生成
            llm_result = self.llm_service.generate_advice(
                analysis_result.get_summary(),
                user_profile.get_personalization_data()
            )
            
            # 個人設定に基づく調整
            personalized_advice = self._personalize_advice_content(
                llm_result, motivation_context, user_profile
            )
            
            return {
                'advice_text': personalized_advice['text'],
                'priority': personalized_advice['priority'],
                'emotion': personalized_advice['emotion'],
                'personalization_score': personal_patterns.get('personalization_score', 0.5),
                'learning_adapted': True,
                'motivation_style': user_profile.motivation_style,
                'generation_timestamp': datetime.now().astimezone().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating personalized advice: {e}")
            return self._generate_fallback_advice({})
    
    def generate_time_optimized_advice(self,
                                     behavior_data: Dict[str, Any],
                                     target_time: Optional[datetime] = None) -> Dict[str, Any]:
        """時間帯別最適化アドバイス生成
        
        Args:
            behavior_data: 行動データ
            target_time: 対象時刻（None の場合は現在時刻）
            
        Returns:
            dict: 時間最適化されたアドバイス
        """
        try:
            target_time = target_time or datetime.now()
            
            # 時間帯の特性を分析
            time_characteristics = self._analyze_time_characteristics(target_time)
            
            # 時間帯別の行動パターン
            hourly_patterns = self._get_hourly_behavior_patterns(target_time.hour)
            
            # 時間帯に適したアドバイス生成
            time_context = {
                'current_hour': target_time.hour,
                'time_characteristics': time_characteristics,
                'hourly_patterns': hourly_patterns,
                'day_of_week': target_time.weekday()
            }
            
            # LLMアドバイス生成
            llm_advice = self.llm_service.generate_advice(
                {'structured_analysis': behavior_data},
                {'time_context': time_context}
            )
            
            # 時間帯に応じた調整
            optimized_advice = self._optimize_for_time(llm_advice, time_context)
            
            return {
                'advice_text': optimized_advice['text'],
                'priority': optimized_advice['priority'],
                'emotion': optimized_advice['emotion'],
                'time_optimized': True,
                'target_hour': target_time.hour,
                'time_characteristics': time_characteristics,
                'generation_timestamp': datetime.now().astimezone().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating time-optimized advice: {e}")
            return self._generate_fallback_advice(behavior_data)
    
    def adjust_emotion_tone(self,
                           advice_text: str,
                           target_emotion: str,
                           user_profile: Optional[UserProfile] = None) -> str:
        """感情トーン調整
        
        Args:
            advice_text: 元のアドバイステキスト
            target_emotion: 目標感情 (encouraging/gentle/alert/celebration)
            user_profile: ユーザープロファイル
            
        Returns:
            str: 調整されたアドバイステキスト
        """
        try:
            # ユーザーの好みを考慮
            preferred_tone = 'friendly'
            if user_profile:
                preferred_tone = user_profile.preferred_advice_tone
            
            # 感情トーンテンプレートの適用
            emotion_templates = self._get_emotion_templates(target_emotion, preferred_tone)
            
            # トーン調整の実行
            adjusted_text = self._apply_emotion_adjustment(
                advice_text, emotion_templates, target_emotion
            )
            
            # 長さ調整
            if len(adjusted_text) > self.max_advice_length:
                adjusted_text = self._truncate_advice(adjusted_text)
            
            return adjusted_text
            
        except Exception as e:
            logger.error(f"Error adjusting emotion tone: {e}")
            return advice_text
    
    def _analyze_current_context(self,
                               behavior_data: Dict[str, Any],
                               user_profile: Optional[UserProfile]) -> Dict[str, Any]:
        """現在のコンテキストを分析"""
        
        context = {
            'focus_level': behavior_data.get('focus_level', 0.5),
            'smartphone_detected': behavior_data.get('smartphone_detected', False),
            'presence_status': behavior_data.get('presence_status', 'unknown'),
            'session_duration': behavior_data.get('session_duration_minutes', 0)
        }
        
        # 集中度状態の判定
        if context['focus_level'] >= 0.7:
            context['focus_state'] = 'high'
        elif context['focus_level'] >= 0.4:
            context['focus_state'] = 'medium'
        else:
            context['focus_state'] = 'low'
        
        # 注意散漫要因の特定
        distractions = []
        if context['smartphone_detected']:
            distractions.append('smartphone')
        if context['focus_level'] < 0.3:
            distractions.append('low_concentration')
        
        context['distractions'] = distractions
        
        # ユーザー固有の要因
        if user_profile:
            context['user_work_style'] = user_profile.work_style
            context['preferred_break_interval'] = user_profile.preferred_break_interval
            context['is_quiet_hours'] = user_profile.is_quiet_hours()
        
        return context
    
    def _determine_advice_type(self, context: Dict[str, Any]) -> str:
        """アドバイスタイプを決定"""
        
        focus_state = context.get('focus_state', 'medium')
        distractions = context.get('distractions', [])
        session_duration = context.get('session_duration', 0)
        
        # 緊急度の高いアドバイス
        if 'smartphone' in distractions and session_duration > 0:
            return 'distraction_alert'
        
        # 休憩推奨
        if session_duration > 50:
            return 'break_recommendation'
        
        # 集中度に基づく分類
        if focus_state == 'low':
            return 'focus_improvement'
        elif focus_state == 'high':
            return 'encouragement'
        else:
            return 'general_guidance'
    
    def _get_time_context(self) -> Dict[str, Any]:
        """時間帯コンテキストを取得"""
        
        now = datetime.now()
        hour = now.hour
        
        # 時間帯の分類
        if 6 <= hour < 12:
            time_period = 'morning'
        elif 12 <= hour < 18:
            time_period = 'afternoon'
        elif 18 <= hour < 22:
            time_period = 'evening'
        else:
            time_period = 'night'
        
        # 一般的な活動レベル
        activity_level = {
            'morning': 'high',
            'afternoon': 'medium',
            'evening': 'low',
            'night': 'very_low'
        }[time_period]
        
        return {
            'time_period': time_period,
            'hour': hour,
            'activity_level': activity_level
        }
    
    def _post_process_advice(self,
                           llm_advice: Dict[str, Any],
                           advice_type: str,
                           context: Dict[str, Any],
                           user_profile: Optional[UserProfile]) -> Dict[str, Any]:
        """アドバイスの後処理"""
        
        advice_text = llm_advice.get('advice_text', '')
        
        # 長さ調整
        if len(advice_text) > self.max_advice_length:
            advice_text = self._truncate_advice(advice_text)
        
        # 優先度の調整
        priority = llm_advice.get('priority', 'medium')
        if advice_type == 'distraction_alert':
            priority = 'high'
        elif advice_type == 'encouragement':
            priority = 'low'
        
        # 感情の調整
        emotion = llm_advice.get('emotion', 'encouraging')
        if context.get('is_quiet_hours', False):
            emotion = 'gentle'
        
        return {
            'advice_text': advice_text,
            'priority': priority,
            'emotion': emotion
        }
    
    def _analyze_personal_patterns(self,
                                 analysis_result: AnalysisResult,
                                 user_profile: UserProfile) -> Dict[str, Any]:
        """個人パターンを分析"""
        
        # 過去の分析結果から学習
        recent_analyses = AnalysisResult.get_recent_analyses(
            hours=self.context_retention_hours,
            user_id=user_profile.user_id
        )
        
        patterns = {
            'avg_productivity': 0.5,
            'common_distractions': [],
            'peak_performance_hours': [],
            'improvement_trends': [],
            'personalization_score': 0.7
        }
        
        if recent_analyses:
            productivity_scores = [
                a.productivity_score for a in recent_analyses 
                if a.productivity_score is not None
            ]
            
            if productivity_scores:
                patterns['avg_productivity'] = sum(productivity_scores) / len(productivity_scores)
        
        return patterns
    
    def _adapt_to_learning_style(self,
                               patterns: Dict[str, Any],
                               user_profile: UserProfile) -> Dict[str, Any]:
        """学習スタイルに適応"""
        
        learning_context = patterns.copy()
        work_style = user_profile.work_style
        
        if work_style == 'focused':
            learning_context['approach'] = 'structured'
            learning_context['detail_level'] = 'high'
        elif work_style == 'flexible':
            learning_context['approach'] = 'adaptive'
            learning_context['detail_level'] = 'medium'
        elif work_style == 'creative':
            learning_context['approach'] = 'inspirational'
            learning_context['detail_level'] = 'low'
        
        return learning_context
    
    def _apply_motivation_style(self,
                              context: Dict[str, Any],
                              user_profile: UserProfile) -> Dict[str, Any]:
        """モチベーションスタイルを適用"""
        
        motivation_context = context.copy()
        motivation_style = user_profile.motivation_style
        
        motivation_context['motivation_approach'] = motivation_style
        
        # スタイル別の調整
        if motivation_style == 'encouraging':
            motivation_context['tone'] = 'positive'
            motivation_context['focus'] = 'achievements'
        elif motivation_style == 'challenging':
            motivation_context['tone'] = 'motivating'
            motivation_context['focus'] = 'goals'
        elif motivation_style == 'supportive':
            motivation_context['tone'] = 'gentle'
            motivation_context['focus'] = 'progress'
        
        return motivation_context
    
    def _personalize_advice_content(self,
                                  llm_result: Dict[str, Any],
                                  context: Dict[str, Any],
                                  user_profile: UserProfile) -> Dict[str, Any]:
        """アドバイス内容のパーソナライズ"""
        
        advice_text = llm_result.get('advice_text', '')
        
        # ユーザー名の挿入（設定されている場合）
        if user_profile.user_name:
            if not any(name in advice_text for name in [user_profile.user_name, 'さん']):
                advice_text = f"{user_profile.user_name}さん、{advice_text}"
        
        # アチーブメントへの言及
        achievements_count = len(user_profile.achievements) if user_profile.achievements else 0
        if achievements_count > 5 and 'achievements' in context.get('focus', ''):
            advice_text += f" これまでの{achievements_count}個の達成を誇りに思ってください！"
        
        return {
            'text': advice_text,
            'priority': llm_result.get('priority', 'medium'),
            'emotion': llm_result.get('emotion', 'encouraging')
        }
    
    def _analyze_time_characteristics(self, target_time: datetime) -> Dict[str, Any]:
        """時間帯の特性を分析"""
        
        hour = target_time.hour
        
        characteristics = {
            'energy_level': 'medium',
            'concentration_potential': 'medium',
            'break_likelihood': 'medium'
        }
        
        # 時間帯別の特性
        if 9 <= hour <= 11:  # 午前の集中時間
            characteristics.update({
                'energy_level': 'high',
                'concentration_potential': 'high',
                'break_likelihood': 'low'
            })
        elif 14 <= hour <= 16:  # 午後の生産性時間
            characteristics.update({
                'energy_level': 'medium',
                'concentration_potential': 'high',
                'break_likelihood': 'medium'
            })
        elif hour in [12, 13]:  # ランチタイム
            characteristics.update({
                'energy_level': 'low',
                'concentration_potential': 'low',
                'break_likelihood': 'high'
            })
        
        return characteristics
    
    def _get_hourly_behavior_patterns(self, hour: int) -> Dict[str, Any]:
        """時間別の行動パターンを取得"""
        
        # 過去データから同じ時間帯のパターンを分析
        # (簡易版 - 実際は統計データベースから取得)
        
        return {
            'typical_focus_level': 0.6,
            'common_activities': ['work', 'study'],
            'distraction_probability': 0.3
        }
    
    def _optimize_for_time(self,
                         llm_advice: Dict[str, Any],
                         time_context: Dict[str, Any]) -> Dict[str, Any]:
        """時間帯に応じた最適化"""
        
        advice_text = llm_advice.get('advice_text', '')
        time_period = time_context.get('time_characteristics', {}).get('energy_level', 'medium')
        
        # 時間帯別の調整
        if time_period == 'high':
            # 高エネルギー時間帯
            advice_text = advice_text.replace('休憩', '短い休憩')
        elif time_period == 'low':
            # 低エネルギー時間帯
            advice_text = advice_text.replace('集中', 'ゆっくり集中')
        
        return {
            'text': advice_text,
            'priority': llm_advice.get('priority', 'medium'),
            'emotion': llm_advice.get('emotion', 'encouraging')
        }
    
    def _get_emotion_templates(self, emotion: str, tone: str) -> Dict[str, List[str]]:
        """感情テンプレートを取得"""
        
        templates = {
            'encouraging': {
                'friendly': ['頑張っていますね！', 'その調子です！', '素晴らしい集中力です！'],
                'formal': ['良い調子で進んでいます', '継続して取り組んでください', '効果的な学習ができています']
            },
            'gentle': {
                'friendly': ['無理しないでくださいね', 'ゆっくりで大丈夫ですよ', '自分のペースで進みましょう'],
                'formal': ['適度な休憩をお取りください', 'ペースを調整することをお勧めします', '無理のない範囲で継続してください']
            },
            'alert': {
                'friendly': ['ちょっと注意が必要です', '気をつけてくださいね', '少し休憩しませんか？'],
                'formal': ['注意が必要な状況です', '対策を検討してください', '改善が必要です']
            }
        }
        
        return templates.get(emotion, {}).get(tone, ['頑張ってください'])
    
    def _apply_emotion_adjustment(self,
                                advice_text: str,
                                templates: List[str],
                                emotion: str) -> str:
        """感情調整の適用"""
        
        if not templates:
            return advice_text
        
        # 適切なテンプレートを選択
        template = templates[0]  # 簡易版
        
        # テキストの調整
        if emotion == 'gentle' and '必要' in advice_text:
            advice_text = advice_text.replace('必要', 'おすすめ')
        elif emotion == 'encouraging':
            advice_text = f"{template} {advice_text}"
        
        return advice_text
    
    def _truncate_advice(self, advice_text: str) -> str:
        """アドバイステキストの短縮"""
        
        if len(advice_text) <= self.max_advice_length:
            return advice_text
        
        # 文の境界で短縮
        sentences = advice_text.split('。')
        truncated = ''
        
        for sentence in sentences:
            if len(truncated + sentence + '。') <= self.max_advice_length:
                truncated += sentence + '。'
            else:
                break
        
        return truncated.rstrip('。') + '。'
    
    def _load_advice_templates(self) -> Dict[str, List[str]]:
        """定型アドバイステンプレートをロード"""
        
        return {
            'break_recommendation': [
                '少し休憩を取って、リフレッシュしてください。',
                '目を休めて、軽くストレッチしませんか？',
                '短い休憩で、集中力を回復させましょう。'
            ],
            'focus_improvement': [
                '深呼吸をして、もう一度集中してみてください。',
                '環境を整えて、集中できる状態を作りましょう。',
                '短時間から始めて、集中力を高めていきましょう。'
            ],
            'encouragement': [
                'とても良い集中力です！この調子で続けてください。',
                '素晴らしいペースで進んでいます。',
                '順調に取り組めていますね。'
            ]
        }
    
    def _generate_fallback_advice(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバックアドバイス生成"""
        
        session_duration = behavior_data.get('session_duration_minutes', 0)
        
        if session_duration > 60:
            advice_text = '長時間お疲れ様です。少し休憩を取ってくださいね。'
            priority = 'medium'
        elif session_duration > 30:
            advice_text = 'いい調子で続いています。この調子で頑張ってください。'
            priority = 'low'
        else:
            advice_text = '学習・作業を始めましょう。集中してやっていきましょう。'
            priority = 'low'
        
        return {
            'advice_text': advice_text,
            'priority': priority,
            'emotion': 'encouraging',
            'fallback': True,
            'generation_timestamp': datetime.now().astimezone().isoformat()
        } 