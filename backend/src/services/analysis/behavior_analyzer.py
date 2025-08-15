"""
Behavior Analyzer Service

行動パターン分析エンジン - 時系列データ解析、トレンド分析、異常検知
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import logging

from models.behavior_log import BehaviorLog
from models.analysis_result import AnalysisResult
from schemas.recommendation import RecommendationSchema
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BehaviorAnalyzer:
    """行動パターン分析エンジン
    
    監視データの時系列分析により行動パターンを特定
    - 集中度トレンド分析
    - 注意散漫パターン検出
    - 休憩タイミング最適化
    - 異常行動検知
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('behavior_analyzer', {})
        
        # 分析パラメータ
        self.focus_threshold_high = self.config.get('focus_threshold_high', 0.7)
        self.focus_threshold_low = self.config.get('focus_threshold_low', 0.3)
        self.smartphone_usage_threshold = self.config.get('smartphone_usage_threshold', 0.1)
        self.session_minimum_duration = self.config.get('session_minimum_duration', 10)  # 分
        
        logger.info("BehaviorAnalyzer initialized")
    
    def analyze_focus_pattern(self, logs: List[BehaviorLog]) -> Dict[str, Any]:
        """集中度パターンを分析
        
        Args:
            logs: 行動ログのリスト
            
        Returns:
            dict: 集中度パターン分析結果
        """
        if not logs:
            return {'error': 'No logs provided'}
        
        try:
            # 集中度データの抽出
            focus_data = self._extract_focus_data(logs)
            
            # 基本統計の計算
            basic_stats = self._calculate_basic_stats(focus_data)
            
            # トレンド分析
            trend_analysis = self._analyze_focus_trend(focus_data)
            
            # 集中度パターンの特定
            patterns = self._identify_focus_patterns(focus_data)
            
            # 時間帯別分析
            hourly_analysis = self._analyze_hourly_patterns(logs)
            
            return {
                'basic_statistics': basic_stats,
                'trend_analysis': trend_analysis,
                'focus_patterns': patterns,
                'hourly_patterns': hourly_analysis,
                'total_entries': len(logs),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing focus pattern: {e}")
            return {'error': str(e)}
    
    def detect_break_timing(self, current_session: Dict[str, Any]) -> bool:
        """休憩タイミングを検出
        
        Args:
            current_session: 現在のセッション情報
            
        Returns:
            bool: 休憩推奨フラグ
        """
        try:
            session_duration = current_session.get('duration_minutes', 0)
            recent_focus = current_session.get('recent_focus_scores', [])
            smartphone_usage = current_session.get('smartphone_usage_rate', 0)
            
            # 基本的な休憩条件
            conditions = {
                'long_session': session_duration >= 50,  # 50分以上の継続
                'declining_focus': self._is_focus_declining(recent_focus),
                'high_smartphone_usage': smartphone_usage > self.smartphone_usage_threshold,
                'low_recent_focus': np.mean(recent_focus) < self.focus_threshold_low if recent_focus else False
            }
            
            # 複数条件が満たされた場合に休憩推奨
            break_score = sum(conditions.values())
            should_break = break_score >= 2
            
            logger.debug(f"Break timing analysis: {conditions}, score: {break_score}, recommend: {should_break}")
            
            return should_break
            
        except Exception as e:
            logger.error(f"Error detecting break timing: {e}")
            return False
    
    def generate_insights(self, timeframe: str = 'daily') -> Dict[str, Any]:
        """行動インサイトを生成
        
        Args:
            timeframe: 分析期間 (hourly/daily/weekly)
            
        Returns:
            dict: 行動インサイト
        """
        try:
            # 期間に応じたデータ取得
            hours_map = {
                'hourly': 1,
                'daily': 24,
                'weekly': 168
            }
            
            hours = hours_map.get(timeframe, 24)
            logs = BehaviorLog.get_recent_logs(hours=hours)
            
            if not logs:
                return {'message': 'データが不足しています'}
            
            # 基本分析
            focus_analysis = self.analyze_focus_pattern(logs)
            distraction_analysis = self._analyze_distractions(logs)
            productivity_analysis = self._analyze_productivity(logs)
            
            # インサイト生成
            insights = self._generate_behavioral_insights(
                focus_analysis, 
                distraction_analysis, 
                productivity_analysis
            )
            
            return {
                'timeframe': timeframe,
                'period_start': logs[-1].timestamp.isoformat() if logs else None,
                'period_end': logs[0].timestamp.isoformat() if logs else None,
                'focus_analysis': focus_analysis,
                'distraction_analysis': distraction_analysis,
                'productivity_analysis': productivity_analysis,
                'key_insights': insights,
                'recommendations': self._generate_recommendations(insights)
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {'error': str(e)}
    
    def detect_anomalies(self, logs: List[BehaviorLog]) -> List[Dict[str, Any]]:
        """異常行動を検出
        
        Args:
            logs: 行動ログのリスト
            
        Returns:
            list: 検出された異常のリスト
        """
        anomalies = []
        
        try:
            # 長時間同一姿勢の検出
            posture_anomalies = self._detect_posture_anomalies(logs)
            anomalies.extend(posture_anomalies)
            
            # 異常な集中度パターンの検出
            focus_anomalies = self._detect_focus_anomalies(logs)
            anomalies.extend(focus_anomalies)
            
            # 過度なスマートフォン使用の検出
            smartphone_anomalies = self._detect_smartphone_anomalies(logs)
            anomalies.extend(smartphone_anomalies)
            
            # 長時間不在の検出
            absence_anomalies = self._detect_absence_anomalies(logs)
            anomalies.extend(absence_anomalies)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def _extract_focus_data(self, logs: List[BehaviorLog]) -> List[Tuple[datetime, float]]:
        """ログから集中度データを抽出"""
        focus_data = []
        
        for log in logs:
            if log.focus_level is not None:
                focus_data.append((log.timestamp, log.focus_level))
        
        # 時系列順にソート
        focus_data.sort(key=lambda x: x[0])
        return focus_data
    
    def _calculate_basic_stats(self, focus_data: List[Tuple[datetime, float]]) -> Dict[str, float]:
        """集中度の基本統計を計算"""
        if not focus_data:
            return {}
        
        values = [score for _, score in focus_data]
        
        return {
            'mean': np.mean(values),
            'median': np.median(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'high_focus_ratio': sum(1 for v in values if v >= self.focus_threshold_high) / len(values),
            'low_focus_ratio': sum(1 for v in values if v <= self.focus_threshold_low) / len(values)
        }
    
    def _analyze_focus_trend(self, focus_data: List[Tuple[datetime, float]]) -> Dict[str, Any]:
        """集中度のトレンドを分析"""
        if len(focus_data) < 2:
            return {'trend': 'insufficient_data'}
        
        # 時系列データから傾向を計算
        timestamps = [t.timestamp() for t, _ in focus_data]
        scores = [score for _, score in focus_data]
        
        # 線形回帰で傾向を算出
        slope = np.polyfit(timestamps, scores, 1)[0]
        
        # 変動性の計算
        variability = np.std(scores)
        
        # トレンドの判定
        if abs(slope) < 1e-7:  # ほぼ平坦
            trend = 'stable'
        elif slope > 0:
            trend = 'improving'
        else:
            trend = 'declining'
        
        return {
            'trend': trend,
            'slope': float(slope),
            'variability': float(variability),
            'trend_strength': abs(slope) * 1e6,  # 見やすくするためのスケーリング
            'stability': 'high' if variability < 0.1 else 'medium' if variability < 0.2 else 'low'
        }
    
    def _identify_focus_patterns(self, focus_data: List[Tuple[datetime, float]]) -> Dict[str, Any]:
        """集中度パターンを特定"""
        if not focus_data:
            return {}
        
        patterns = {
            'peak_times': [],
            'low_times': [],
            'focus_duration_avg': 0,
            'recovery_time_avg': 0
        }
        
        # 高集中・低集中の時間帯を特定
        for timestamp, score in focus_data:
            hour = timestamp.hour
            
            if score >= self.focus_threshold_high:
                patterns['peak_times'].append(hour)
            elif score <= self.focus_threshold_low:
                patterns['low_times'].append(hour)
        
        # 時間帯のパターン分析
        if patterns['peak_times']:
            patterns['common_peak_hours'] = list(set(patterns['peak_times']))
        
        if patterns['low_times']:
            patterns['common_low_hours'] = list(set(patterns['low_times']))
        
        return patterns
    
    def _analyze_hourly_patterns(self, logs: List[BehaviorLog]) -> Dict[str, Any]:
        """時間帯別のパターンを分析"""
        hourly_data = defaultdict(list)
        
        for log in logs:
            hour = log.timestamp.hour
            if log.focus_level is not None:
                hourly_data[hour].append(log.focus_level)
        
        hourly_stats = {}
        for hour, scores in hourly_data.items():
            if scores:
                hourly_stats[hour] = {
                    'avg_focus': np.mean(scores),
                    'count': len(scores),
                    'focus_stability': 1 - np.std(scores)  # 安定性指標
                }
        
        # 最も生産的な時間帯
        best_hours = sorted(
            hourly_stats.items(),
            key=lambda x: x[1]['avg_focus'],
            reverse=True
        )[:3]
        
        return {
            'hourly_statistics': hourly_stats,
            'most_productive_hours': [hour for hour, _ in best_hours],
            'analysis_summary': f"最も集中できる時間帯: {[hour for hour, _ in best_hours]}"
        }
    
    def _analyze_distractions(self, logs: List[BehaviorLog]) -> Dict[str, Any]:
        """注意散漫要因を分析"""
        total_logs = len(logs)
        smartphone_count = sum(1 for log in logs if log.smartphone_detected)
        low_focus_count = sum(1 for log in logs if log.focus_level and log.focus_level < self.focus_threshold_low)
        
        return {
            'smartphone_usage_rate': smartphone_count / total_logs if total_logs > 0 else 0,
            'low_focus_rate': low_focus_count / total_logs if total_logs > 0 else 0,
            'primary_distraction': 'smartphone' if smartphone_count > low_focus_count else 'focus_issues',
            'distraction_frequency': (smartphone_count + low_focus_count) / total_logs if total_logs > 0 else 0
        }
    
    def _analyze_productivity(self, logs: List[BehaviorLog]) -> Dict[str, Any]:
        """生産性指標を分析"""
        if not logs:
            return {}
        
        # 在席率の計算
        present_logs = [log for log in logs if log.presence_status == 'present']
        presence_rate = len(present_logs) / len(logs)
        
        # 平均集中度
        focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
        avg_focus = np.mean(focus_scores) if focus_scores else 0
        
        # 生産性スコア（簡易版）
        productivity_score = (presence_rate * 0.4 + avg_focus * 0.6) - (
            sum(1 for log in logs if log.smartphone_detected) / len(logs) * 0.3
        )
        
        return {
            'presence_rate': presence_rate,
            'average_focus': avg_focus,
            'productivity_score': max(0, min(1, productivity_score)),
            'active_time_ratio': len(focus_scores) / len(logs) if logs else 0
        }
    
    def _generate_behavioral_insights(self, 
                                    focus_analysis: Dict[str, Any],
                                    distraction_analysis: Dict[str, Any],
                                    productivity_analysis: Dict[str, Any]) -> List[str]:
        """行動インサイトを生成"""
        insights = []
        
        # 集中度に関するインサイト
        if focus_analysis.get('basic_statistics', {}).get('high_focus_ratio', 0) > 0.5:
            insights.append("高い集中力を維持できています")
        elif focus_analysis.get('basic_statistics', {}).get('low_focus_ratio', 0) > 0.3:
            insights.append("集中力の向上が必要です")
        
        # トレンドに関するインサイト
        trend = focus_analysis.get('trend_analysis', {}).get('trend')
        if trend == 'improving':
            insights.append("集中力が向上傾向にあります")
        elif trend == 'declining':
            insights.append("集中力が低下傾向にあります")
        
        # 注意散漫に関するインサイト
        if distraction_analysis.get('smartphone_usage_rate', 0) > 0.1:
            insights.append("スマートフォンの使用が多く検出されています")
        
        # 生産性に関するインサイト
        productivity_score = productivity_analysis.get('productivity_score', 0)
        if productivity_score > 0.7:
            insights.append("高い生産性を維持しています")
        elif productivity_score < 0.4:
            insights.append("生産性の改善が必要です")
        
        return insights
    
    def _generate_recommendations(self, insights: List[str]) -> List[RecommendationSchema]:
        """インサイトから推奨事項を生成"""
        recommendations = []
        
        for insight in insights:
            if "集中力の向上が必要" in insight:
                recommendations.append(RecommendationSchema(
                    type='focus_improvement',
                    priority='high',
                    message='短時間の集中タスクから始めて、徐々に集中時間を延ばしましょう',
                    action='focus_training',
                    source='behavior_analysis'
                ))
            
            elif "スマートフォンの使用" in insight:
                recommendations.append(RecommendationSchema(
                    type='distraction_management',
                    priority='medium',
                    message='スマートフォンを手の届かない場所に置くか、通知をオフにしてみてください',
                    action='device_management',
                    source='behavior_analysis'
                ))
            
            elif "集中力が低下傾向" in insight:
                recommendations.append(RecommendationSchema(
                    type='trend_reversal',
                    priority='high',
                    message='定期的な休憩と環境の見直しを検討しましょう',
                    action='break_scheduling',
                    source='behavior_analysis'
                ))
        
        # デフォルト推奨事項
        if not recommendations:
            recommendations.append(RecommendationSchema(
                type='general',
                priority='low',
                message='現在の作業ペースを維持しながら、更なる改善を目指しましょう',
                action='continue_current',
                source='behavior_analysis'
            ))
        
        return recommendations
    
    def _is_focus_declining(self, recent_scores: List[float]) -> bool:
        """最近の集中度が低下傾向かチェック"""
        if len(recent_scores) < 3:
            return False
        
        # 最近の3つのスコアで傾向をチェック
        recent_trend = recent_scores[-3:]
        return recent_trend[0] > recent_trend[1] > recent_trend[2]
    
    def _detect_posture_anomalies(self, logs: List[BehaviorLog]) -> List[Dict[str, Any]]:
        """姿勢異常を検出"""
        anomalies = []
        
        # 連続する悪い姿勢の検出
        bad_posture_count = 0
        
        for log in logs:
            posture_data = log.posture_data
            if posture_data and posture_data.get('posture_score', 0.5) < 0.3:
                bad_posture_count += 1
            else:
                if bad_posture_count >= 6:  # 3分間以上（30秒×6）
                    anomalies.append({
                        'type': 'poor_posture',
                        'severity': 'medium',
                        'message': '長時間の悪い姿勢が検出されました',
                        'timestamp': log.timestamp.isoformat()
                    })
                bad_posture_count = 0
        
        return anomalies
    
    def _detect_focus_anomalies(self, logs: List[BehaviorLog]) -> List[Dict[str, Any]]:
        """集中度異常を検出"""
        anomalies = []
        
        # 極端に低い集中度の連続検出
        low_focus_count = 0
        
        for log in logs:
            if log.focus_level and log.focus_level < 0.1:
                low_focus_count += 1
            else:
                if low_focus_count >= 10:  # 5分間以上
                    anomalies.append({
                        'type': 'extreme_low_focus',
                        'severity': 'high',
                        'message': '極端に低い集中度が継続しています',
                        'timestamp': log.timestamp.isoformat()
                    })
                low_focus_count = 0
        
        return anomalies
    
    def _detect_smartphone_anomalies(self, logs: List[BehaviorLog]) -> List[Dict[str, Any]]:
        """スマートフォン使用異常を検出"""
        anomalies = []
        
        smartphone_logs = [log for log in logs if log.smartphone_detected]
        total_logs = len(logs)
        
        if total_logs > 0 and len(smartphone_logs) / total_logs > 0.2:  # 20%以上
            anomalies.append({
                'type': 'excessive_smartphone_usage',
                'severity': 'medium',
                'message': 'スマートフォンの使用頻度が高すぎます',
                'usage_rate': len(smartphone_logs) / total_logs
            })
        
        return anomalies
    
    def _detect_absence_anomalies(self, logs: List[BehaviorLog]) -> List[Dict[str, Any]]:
        """長時間不在異常を検出"""
        anomalies = []
        
        absent_count = 0
        
        for log in logs:
            if log.presence_status == 'absent':
                absent_count += 1
            else:
                if absent_count >= 20:  # 10分間以上不在
                    anomalies.append({
                        'type': 'prolonged_absence',
                        'severity': 'low',
                        'message': '長時間の不在が検出されました',
                        'timestamp': log.timestamp.isoformat()
                    })
                absent_count = 0
        
        return anomalies 