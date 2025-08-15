"""
Analysis Helper Functions - 分析用ヘルパー関数集

分析APIで共通して使用されるヘルパー関数群
データ処理、サマリー生成、インサイト生成などの共通機能を提供
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def generate_comprehensive_insights(analysis_data: Dict[str, Any], 
                                  timeframe: str = 'daily') -> Dict[str, Any]:
    """包括的インサイト生成
    
    複数の分析結果を統合して包括的なインサイトを生成
    
    Args:
        analysis_data: 分析データ辞書
        timeframe: 時間枠 ('hourly', 'daily', 'weekly')
        
    Returns:
        包括的インサイト辞書
    """
    try:
        insights = {
            'timeframe': timeframe,
            'key_findings': [],
            'trends': [],
            'recommendations': [],
            'risk_factors': [],
            'positive_indicators': [],
            'data_quality': 0.0,
            'confidence_score': 0.0
        }
        
        # 基本統計から洞察抽出
        if 'basic_statistics' in analysis_data:
            basic_stats = analysis_data['basic_statistics']
            insights['key_findings'].extend(_extract_basic_insights(basic_stats))
        
        # トレンド分析から洞察抽出
        if 'trend_analysis' in analysis_data:
            trend_data = analysis_data['trend_analysis']
            insights['trends'].extend(_extract_trend_insights(trend_data))
        
        # 異常検知から洞察抽出
        if 'anomalies' in analysis_data:
            anomaly_data = analysis_data['anomalies']
            insights['risk_factors'].extend(_extract_anomaly_insights(anomaly_data))
        
        # 全体的な信頼度計算
        insights['confidence_score'] = _calculate_overall_confidence(analysis_data)
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating comprehensive insights: {e}")
        return {
            'timeframe': timeframe,
            'error': 'インサイト生成中にエラーが発生しました',
            'confidence_score': 0.0
        }


def calculate_behavior_score(logs: list, 
                           focus_weight: float = 0.4,
                           presence_weight: float = 0.3,
                           posture_weight: float = 0.3) -> Dict[str, float]:
    """行動スコア計算
    
    行動ログから総合的な行動スコアを計算
    
    Args:
        logs: 行動ログリスト
        focus_weight: 集中度の重み
        presence_weight: 在席率の重み
        posture_weight: 姿勢スコアの重み
        
    Returns:
        行動スコア辞書
    """
    try:
        if not logs:
            return {
                'overall_score': 0.0,
                'focus_score': 0.0,
                'presence_score': 0.0,
                'posture_score': 0.0,
                'data_points': 0
            }
        
        # 各スコア計算
        focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
        presence_scores = [1.0 if log.presence_status == 'present' else 0.0 for log in logs]
        posture_scores = [log.posture_score for log in logs if hasattr(log, 'posture_score') and log.posture_score is not None]
        
        # 平均スコア計算
        avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else 0.0
        avg_presence = sum(presence_scores) / len(presence_scores) if presence_scores else 0.0
        avg_posture = sum(posture_scores) / len(posture_scores) if posture_scores else 0.5
        
        # 正規化（0-1範囲）
        normalized_focus = min(max(avg_focus / 100.0, 0.0), 1.0) if avg_focus > 1 else avg_focus
        normalized_presence = avg_presence
        normalized_posture = avg_posture
        
        # 総合スコア計算
        overall_score = (
            normalized_focus * focus_weight +
            normalized_presence * presence_weight +
            normalized_posture * posture_weight
        )
        
        return {
            'overall_score': round(overall_score, 3),
            'focus_score': round(normalized_focus, 3),
            'presence_score': round(normalized_presence, 3),
            'posture_score': round(normalized_posture, 3),
            'data_points': len(logs)
        }
        
    except Exception as e:
        logger.error(f"Error calculating behavior score: {e}")
        return {
            'overall_score': 0.0,
            'focus_score': 0.0,
            'presence_score': 0.0,
            'posture_score': 0.0,
            'data_points': 0,
            'error': 'スコア計算エラー'
        }


def detect_behavioral_patterns(logs: list, 
                             window_size: int = 10) -> Dict[str, Any]:
    """行動パターン検出
    
    行動ログから繰り返しパターンや傾向を検出
    
    Args:
        logs: 行動ログリスト
        window_size: 分析ウィンドウサイズ
        
    Returns:
        検出されたパターン情報
    """
    try:
        patterns = {
            'cyclical_patterns': [],
            'focus_peaks': [],
            'distraction_periods': [],
            'break_patterns': [],
            'consistency_score': 0.0
        }
        
        if len(logs) < window_size:
            return patterns
        
        # 集中度パターン検出
        focus_values = [log.focus_level for log in logs if log.focus_level is not None]
        if focus_values:
            patterns['focus_peaks'] = _detect_focus_peaks(focus_values, window_size)
            patterns['distraction_periods'] = _detect_distraction_periods(focus_values, window_size)
        
        # 一貫性スコア計算
        patterns['consistency_score'] = _calculate_consistency_score(logs)
        
        # 休憩パターン検出
        patterns['break_patterns'] = _detect_break_patterns(logs)
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error detecting behavioral patterns: {e}")
        return {
            'cyclical_patterns': [],
            'focus_peaks': [],
            'distraction_periods': [],
            'break_patterns': [],
            'consistency_score': 0.0,
            'error': 'パターン検出エラー'
        }


def generate_contextual_recommendations(current_state: Dict[str, Any],
                                      historical_data: Dict[str, Any],
                                      user_preferences: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """コンテキスト別推奨事項生成
    
    現在の状態と履歴データから適切な推奨事項を生成
    
    Args:
        current_state: 現在の状態情報
        historical_data: 履歴データ
        user_preferences: ユーザー設定
        
    Returns:
        推奨事項リスト
    """
    try:
        recommendations = []
        
        # 集中度ベースの推奨
        focus_level = current_state.get('focus_level', 0)
        if focus_level < 0.3:
            recommendations.append({
                'type': 'focus_improvement',
                'priority': 'high',
                'message': '集中度が低下しています。5分間の休憩を取ることをお勧めします。',
                'action': 'take_break',
                'duration_minutes': 5
            })
        elif focus_level > 0.8:
            recommendations.append({
                'type': 'maintain_focus',
                'priority': 'medium',
                'message': '素晴らしい集中状態です！この調子を維持しましょう。',
                'action': 'continue',
                'duration_minutes': 25
            })
        
        # 姿勢ベースの推奨
        if current_state.get('posture_score', 0.5) < 0.4:
            recommendations.append({
                'type': 'posture_correction',
                'priority': 'medium',
                'message': '姿勢を正してください。背筋を伸ばし、画面との距離を調整しましょう。',
                'action': 'adjust_posture',
                'duration_minutes': 1
            })
        
        # スマートフォン使用警告
        if current_state.get('smartphone_detected', False):
            recommendations.append({
                'type': 'distraction_alert',
                'priority': 'high',
                'message': 'スマートフォンの使用が検出されました。作業に集中しましょう。',
                'action': 'put_away_phone',
                'duration_minutes': 0
            })
        
        # 履歴データベースの推奨
        if historical_data:
            historical_recs = _generate_historical_recommendations(historical_data)
            recommendations.extend(historical_recs)
        
        # ユーザー設定ベースの推奨
        if user_preferences:
            preference_recs = _generate_preference_recommendations(user_preferences, current_state)
            recommendations.extend(preference_recs)
        
        # 優先度順にソート
        recommendations.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x.get('priority', 'low'), 2))
        
        return recommendations[:5]  # 最大5個まで
        
    except Exception as e:
        logger.error(f"Error generating contextual recommendations: {e}")
        return [{
            'type': 'error',
            'priority': 'low',
            'message': '推奨事項の生成中にエラーが発生しました。',
            'action': 'none',
            'duration_minutes': 0
        }]


def calculate_data_quality_metrics(logs: list) -> Dict[str, float]:
    """データ品質メトリクス計算
    
    行動ログのデータ品質を評価
    
    Args:
        logs: 行動ログリスト
        
    Returns:
        データ品質メトリクス
    """
    try:
        if not logs:
            return {
                'completeness': 0.0,
                'consistency': 0.0,
                'freshness': 0.0,
                'overall_quality': 0.0
            }
        
        total_logs = len(logs)
        
        # 完全性評価
        complete_logs = sum(1 for log in logs if _is_complete_log(log))
        completeness = complete_logs / total_logs
        
        # 一貫性評価
        consistency = _evaluate_data_consistency(logs)
        
        # 新鮮度評価
        freshness = _evaluate_data_freshness(logs)
        
        # 総合品質スコア
        overall_quality = (completeness * 0.4 + consistency * 0.3 + freshness * 0.3)
        
        return {
            'completeness': round(completeness, 3),
            'consistency': round(consistency, 3),
            'freshness': round(freshness, 3),
            'overall_quality': round(overall_quality, 3)
        }
        
    except Exception as e:
        logger.error(f"Error calculating data quality metrics: {e}")
        return {
            'completeness': 0.0,
            'consistency': 0.0,
            'freshness': 0.0,
            'overall_quality': 0.0
        }


# ========== プライベートヘルパー関数 ==========

def _extract_basic_insights(basic_stats: Dict[str, Any]) -> List[str]:
    """基本統計からインサイト抽出"""
    insights = []
    
    mean_focus = basic_stats.get('mean', 0)
    std_focus = basic_stats.get('std', 0)
    
    if mean_focus > 70:
        insights.append("平均集中度が高く、良好な作業状態を維持しています")
    elif mean_focus < 30:
        insights.append("平均集中度が低く、作業環境の改善が必要です")
    
    if std_focus > 20:
        insights.append("集中度のばらつきが大きく、一貫性の向上が必要です")
    elif std_focus < 5:
        insights.append("安定した集中状態を維持しています")
    
    return insights


def _extract_trend_insights(trend_data: Dict[str, Any]) -> List[str]:
    """トレンドデータからインサイト抽出"""
    insights = []
    
    trend_direction = trend_data.get('trend', 'stable')
    if trend_direction == 'increasing':
        insights.append("集中度が向上傾向にあります")
    elif trend_direction == 'decreasing':
        insights.append("集中度が低下傾向にあります")
    else:
        insights.append("集中度は安定しています")
    
    return insights


def _extract_anomaly_insights(anomaly_data: List[Dict[str, Any]]) -> List[str]:
    """異常データからインサイト抽出"""
    insights = []
    
    if len(anomaly_data) > 5:
        insights.append("異常な行動パターンが多く検出されました")
    elif len(anomaly_data) > 0:
        insights.append("いくつかの異常パターンが検出されました")
    
    return insights


def _calculate_overall_confidence(analysis_data: Dict[str, Any]) -> float:
    """全体的な信頼度計算"""
    try:
        confidence_scores = []
        
        if 'data_quality' in analysis_data:
            confidence_scores.append(analysis_data['data_quality'])
        
        if 'basic_statistics' in analysis_data:
            # サンプル数ベースの信頼度
            sample_count = analysis_data['basic_statistics'].get('count', 0)
            sample_confidence = min(sample_count / 100.0, 1.0)
            confidence_scores.append(sample_confidence)
        
        return sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
    except Exception:
        return 0.5


def _detect_focus_peaks(focus_values: List[float], window_size: int) -> List[Dict[str, Any]]:
    """集中度ピーク検出"""
    peaks = []
    
    try:
        for i in range(window_size, len(focus_values) - window_size):
            current = focus_values[i]
            if current > 80:  # 高集中状態の閾値
                window = focus_values[i-window_size:i+window_size]
                if current == max(window):
                    peaks.append({
                        'index': i,
                        'value': current,
                        'duration': _calculate_peak_duration(focus_values, i)
                    })
    except Exception:
        pass
    
    return peaks


def _detect_distraction_periods(focus_values: List[float], window_size: int) -> List[Dict[str, Any]]:
    """集中力散漫期間検出"""
    distractions = []
    
    try:
        low_focus_threshold = 30
        current_period = None
        
        for i, value in enumerate(focus_values):
            if value < low_focus_threshold:
                if current_period is None:
                    current_period = {'start': i, 'min_value': value}
                else:
                    current_period['min_value'] = min(current_period['min_value'], value)
            else:
                if current_period is not None:
                    current_period['end'] = i - 1
                    current_period['duration'] = current_period['end'] - current_period['start'] + 1
                    if current_period['duration'] >= 3:  # 最低3ポイント以上
                        distractions.append(current_period)
                    current_period = None
    except Exception:
        pass
    
    return distractions


def _calculate_consistency_score(logs: list) -> float:
    """一貫性スコア計算"""
    try:
        if len(logs) < 2:
            return 0.0
        
        focus_values = [log.focus_level for log in logs if log.focus_level is not None]
        if not focus_values:
            return 0.0
        
        # 変動係数を使用
        mean_focus = sum(focus_values) / len(focus_values)
        variance = sum((x - mean_focus) ** 2 for x in focus_values) / len(focus_values)
        std_dev = variance ** 0.5
        
        if mean_focus == 0:
            return 0.0
        
        cv = std_dev / mean_focus
        # 低い変動係数ほど高い一貫性
        consistency = max(0.0, 1.0 - cv)
        
        return min(consistency, 1.0)
        
    except Exception:
        return 0.0


def _detect_break_patterns(logs: list) -> List[Dict[str, Any]]:
    """休憩パターン検出"""
    breaks = []
    
    try:
        absence_periods = []
        current_absence = None
        
        for i, log in enumerate(logs):
            if log.presence_status != 'present':
                if current_absence is None:
                    current_absence = {'start': i, 'start_time': log.timestamp}
                current_absence['end'] = i
                current_absence['end_time'] = log.timestamp
            else:
                if current_absence is not None:
                    duration_minutes = (current_absence['end'] - current_absence['start']) * 0.5  # 30秒間隔想定
                    if 2 <= duration_minutes <= 30:  # 2分〜30分の不在を休憩と判定
                        breaks.append({
                            'start_index': current_absence['start'],
                            'end_index': current_absence['end'],
                            'duration_minutes': duration_minutes,
                            'start_time': current_absence['start_time'].isoformat(),
                            'end_time': current_absence['end_time'].isoformat()
                        })
                    current_absence = None
    except Exception:
        pass
    
    return breaks


def _calculate_peak_duration(focus_values: List[float], peak_index: int) -> int:
    """ピーク持続時間計算"""
    try:
        threshold = 70
        duration = 1
        
        # 左方向
        i = peak_index - 1
        while i >= 0 and focus_values[i] >= threshold:
            duration += 1
            i -= 1
        
        # 右方向
        i = peak_index + 1
        while i < len(focus_values) and focus_values[i] >= threshold:
            duration += 1
            i += 1
        
        return duration
    except Exception:
        return 1


def _generate_historical_recommendations(historical_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """履歴データベースの推奨事項生成"""
    recommendations = []
    
    try:
        avg_score = historical_data.get('average_score', 0.5)
        if avg_score < 0.4:
            recommendations.append({
                'type': 'improvement_needed',
                'priority': 'medium',
                'message': '過去のデータから、作業効率の改善が必要です。',
                'action': 'review_workspace',
                'duration_minutes': 10
            })
    except Exception:
        pass
    
    return recommendations


def _generate_preference_recommendations(preferences: Dict[str, Any], 
                                       current_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """ユーザー設定ベースの推奨事項生成"""
    recommendations = []
    
    try:
        # 休憩頻度設定
        break_frequency = preferences.get('break_frequency_minutes', 30)
        session_duration = current_state.get('session_duration_minutes', 0)
        
        if session_duration >= break_frequency:
            recommendations.append({
                'type': 'scheduled_break',
                'priority': 'medium',
                'message': f'{break_frequency}分が経過しました。休憩を取りましょう。',
                'action': 'take_break',
                'duration_minutes': preferences.get('break_duration_minutes', 5)
            })
    except Exception:
        pass
    
    return recommendations


def _is_complete_log(log) -> bool:
    """ログの完全性チェック"""
    try:
        required_fields = ['timestamp', 'presence_status']
        return all(hasattr(log, field) and getattr(log, field) is not None for field in required_fields)
    except Exception:
        return False


def _evaluate_data_consistency(logs: list) -> float:
    """データ一貫性評価"""
    try:
        if len(logs) < 2:
            return 1.0
        
        # タイムスタンプの一貫性チェック
        timestamps = [log.timestamp for log in logs if hasattr(log, 'timestamp')]
        timestamps.sort()
        
        consistent_intervals = 0
        total_intervals = len(timestamps) - 1
        
        for i in range(len(timestamps) - 1):
            interval = (timestamps[i + 1] - timestamps[i]).total_seconds()
            if 25 <= interval <= 35:  # 30秒間隔の許容範囲
                consistent_intervals += 1
        
        return consistent_intervals / total_intervals if total_intervals > 0 else 1.0
        
    except Exception:
        return 0.5


def _evaluate_data_freshness(logs: list) -> float:
    """データ新鮮度評価"""
    try:
        if not logs:
            return 0.0
        
        latest_log = max(logs, key=lambda x: x.timestamp)
        time_diff = (datetime.now(timezone.utc) - latest_log.timestamp.replace(tzinfo=None)).total_seconds()
        
        # 5分以内なら完全に新鮮、30分以上なら新鮮度0
        if time_diff <= 300:  # 5分
            return 1.0
        elif time_diff >= 1800:  # 30分
            return 0.0
        else:
            return 1.0 - (time_diff - 300) / (1800 - 300)
            
    except Exception:
        return 0.5


