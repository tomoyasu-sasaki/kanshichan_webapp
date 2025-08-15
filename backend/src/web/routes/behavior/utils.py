from typing import Dict, Any, List
from datetime import datetime, timedelta
from models.behavior_log import BehaviorLog
from utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_posture_alerts(logs: List[BehaviorLog]) -> int:
    try:
        alert_count = 0
        for log in logs:
            if hasattr(log, 'posture_data') and log.posture_data:
                posture_score = log.posture_data.get('score', 1.0)
                if posture_score < 0.6:
                    alert_count += 1
        return alert_count
    except Exception as e:
        logger.error(f"Error calculating posture alerts: {e}")
        return 0


def calculate_productivity_score(logs: List[BehaviorLog]) -> float:
    try:
        if not logs:
            return 0.0
        focus_weight = 0.6
        presence_weight = 0.3
        smartphone_penalty = 0.1
        focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
        avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else 0.0
        presence_rate = sum(1 for log in logs if log.presence_status == 'present') / len(logs)
        smartphone_penalty_rate = sum(1 for log in logs if log.smartphone_detected) / len(logs)
        score = (avg_focus * focus_weight + presence_rate * presence_weight - smartphone_penalty_rate * smartphone_penalty)
        return max(0.0, min(1.0, score))
    except Exception as e:
        logger.error(f"Error calculating productivity score: {e}")
        return 0.0


def basic_summary(logs: List[BehaviorLog], timeframe: str) -> Dict[str, Any]:
    if not logs:
        return {
            'timeframe': timeframe,
            'total_entries': 0,
            'message': 'No data available for the specified period'
        }
    total_logs = len(logs)
    focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
    smartphone_count = sum(1 for log in logs if log.smartphone_detected)
    present_count = sum(1 for log in logs if log.presence_status == 'present')
    posture_alerts = calculate_posture_alerts(logs)
    productivity_score = calculate_productivity_score(logs)
    return {
        'timeframe': timeframe,
        'period_start': logs[-1].timestamp.isoformat(),
        'period_end': logs[0].timestamp.isoformat(),
        'total_entries': total_logs,
        'average_focus': sum(focus_scores) / len(focus_scores) if focus_scores else 0,
        'smartphone_usage_rate': smartphone_count / total_logs,
        'presence_rate': present_count / total_logs,
        'active_time_minutes': total_logs * 0.5,
        'data_completeness': len(focus_scores) / total_logs if total_logs > 0 else 0,
        'posture_alerts': posture_alerts,
        'productivity_score': productivity_score
    }


def timeframe_range(timeframe: str, start_date: str = None, end_date: str = None):
    now_local = datetime.now()
    now_utc = datetime.utcnow()
    offset = now_local - now_utc

    def local_to_utc_naive(dt_local: datetime) -> datetime:
        return dt_local - offset

    if timeframe == 'today':
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = start_local + timedelta(days=1)  # type: ignore[name-defined]
        start_time = local_to_utc_naive(start_local)
        end_time = local_to_utc_naive(end_local)
    elif timeframe == 'yesterday':
        start_local = (now_local - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)  # type: ignore[name-defined]
        end_local = start_local + timedelta(days=1)  # type: ignore[name-defined]
        start_time = local_to_utc_naive(start_local)
        end_time = local_to_utc_naive(end_local)
    elif timeframe == 'week':
        start_local = (now_local - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)  # type: ignore[name-defined]
        end_local = now_local
        start_time = local_to_utc_naive(start_local)
        end_time = local_to_utc_naive(end_local)
    elif timeframe == 'month':
        start_local = (now_local - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)  # type: ignore[name-defined]
        end_local = now_local
        start_time = local_to_utc_naive(start_local)
        end_time = local_to_utc_naive(end_local)
    elif timeframe == 'custom':
        if not start_date or not end_date:
            return {'error': 'start_date and end_date required for custom timeframe', 'code': 'VALIDATION_ERROR'}, None
        try:
            start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            return {'error': 'Invalid date format', 'code': 'VALIDATION_ERROR'}, None
    else:
        return {'error': 'Invalid timeframe', 'code': 'VALIDATION_ERROR'}, None
    return start_time, end_time


