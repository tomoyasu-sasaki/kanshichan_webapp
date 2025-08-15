from flask import request
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .blueprint import behavior_bp
from ...response_utils import success_response, error_response
from models.behavior_log import BehaviorLog
from .utils import basic_summary, timeframe_range


@behavior_bp.route('/summary', methods=['GET'])
def get_behavior_summary():
    try:
        timeframe = request.args.get('timeframe', 'today')
        user_id = request.args.get('user_id')
        include_details = request.args.get('include_details', 'false').lower() == 'true'
        start_time, end_time = timeframe_range(
            timeframe,
            request.args.get('start_date'),
            request.args.get('end_date'),
        )
        if isinstance(start_time, dict) and 'error' in start_time:
            return error_response(start_time.get('error', 'Invalid timeframe'), code=start_time.get('code', 'VALIDATION_ERROR'), status_code=400)
        logs = BehaviorLog.get_logs_by_timerange(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
        )
        summary = basic_summary(logs, timeframe)
        if include_details:
            summary['detailed_stats'] = _calculate_detailed_stats(logs)
            summary['hourly_breakdown'] = _calculate_hourly_breakdown(logs)
            summary['focus_distribution'] = _calculate_focus_distribution(logs)
        return success_response(summary)
    except Exception:
        return error_response('Failed to generate behavior summary', code='SUMMARY_GENERATION_ERROR', status_code=500)


@behavior_bp.route('/stats', methods=['GET'])
def get_behavior_stats():
    try:
        period = request.args.get('period', 'day')
        limit = int(request.args.get('limit', 7))
        user_id = request.args.get('user_id')
        metrics_str = request.args.get('metrics', 'focus,smartphone,presence')
        if period not in ['hour', 'day', 'week', 'month']:
            return error_response('Invalid period. Must be one of: hour, day, week, month', code='VALIDATION_ERROR', status_code=400)
        if limit < 1 or limit > 365:
            return error_response('Limit must be between 1 and 365', code='VALIDATION_ERROR', status_code=400)
        requested_metrics = [m.strip() for m in metrics_str.split(',')]
        valid_metrics = ['focus', 'smartphone', 'presence', 'activity']
        metrics = [m for m in requested_metrics if m in valid_metrics]
        stats_data = _get_period_statistics(period, limit, user_id, metrics)
        return success_response({
            'period': period,
            'limit': limit,
            'metrics': metrics,
            'statistics': stats_data,
            'generated_at': datetime.utcnow().isoformat(),
        })
    except ValueError as e:
        return error_response(f'Invalid parameter: {str(e)}', code='VALIDATION_ERROR', status_code=400)
    except Exception:
        return error_response('Failed to calculate behavior statistics', code='STATISTICS_ERROR', status_code=500)


def _calculate_detailed_stats(logs: List[BehaviorLog]) -> Dict[str, Any]:
    if not logs:
        return {}
    focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
    if not focus_scores:
        return {'message': 'No focus data available'}
    import numpy as np
    return {
        'focus_statistics': {
            'mean': float(np.mean(focus_scores)),
            'median': float(np.median(focus_scores)),
            'std': float(np.std(focus_scores)),
            'min': float(np.min(focus_scores)),
            'max': float(np.max(focus_scores)),
            'q25': float(np.percentile(focus_scores, 25)),
            'q75': float(np.percentile(focus_scores, 75)),
        }
    }


def _calculate_hourly_breakdown(logs: List[BehaviorLog]) -> Dict[str, Any]:
    hourly_data = {}
    for log in logs:
        hour = log.timestamp.hour
        if hour not in hourly_data:
            hourly_data[hour] = {'count': 0, 'focus_sum': 0, 'smartphone_count': 0}
        hourly_data[hour]['count'] += 1
        if log.focus_level is not None:
            hourly_data[hour]['focus_sum'] += log.focus_level
        if log.smartphone_detected:
            hourly_data[hour]['smartphone_count'] += 1
    hourly_stats = {}
    for hour, data in hourly_data.items():
        hourly_stats[str(hour)] = {
            'entry_count': data['count'],
            'average_focus': data['focus_sum'] / data['count'] if data['count'] > 0 else 0,
            'smartphone_rate': data['smartphone_count'] / data['count'] if data['count'] > 0 else 0,
        }
    return hourly_stats


def _calculate_focus_distribution(logs: List[BehaviorLog]) -> Dict[str, Any]:
    focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
    if not focus_scores:
        return {}
    ranges = {
        'very_low': [0.0, 0.2],
        'low': [0.2, 0.4],
        'medium': [0.4, 0.6],
        'high': [0.6, 0.8],
        'very_high': [0.8, 1.0],
    }
    distribution = {}
    total = len(focus_scores)
    for range_name, (min_val, max_val) in ranges.items():
        count = sum(1 for score in focus_scores if min_val <= score < max_val or (range_name == 'very_high' and score == 1.0))
        distribution[range_name] = {
            'count': count,
            'percentage': (count / total) * 100 if total > 0 else 0,
        }
    return distribution


def _get_period_statistics(period: str, limit: int, user_id: str, metrics: List[str]) -> List[Dict[str, Any]]:
    stats = []
    now = datetime.now()
    for i in range(limit):
        if period == 'hour':
            period_start = now - timedelta(hours=i+1)
            period_end = now - timedelta(hours=i)
        elif period == 'day':
            period_start = (now - timedelta(days=i+1)).replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif period == 'week':
            period_start = now - timedelta(weeks=i+1)
            period_end = now - timedelta(weeks=i)
        else:
            period_start = now - timedelta(days=(i+1)*30)
            period_end = now - timedelta(days=i*30)
        logs = BehaviorLog.get_logs_by_timerange(start_time=period_start, end_time=period_end, user_id=user_id)
        period_stats = {
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'data_count': len(logs),
        }
        if 'focus' in metrics:
            focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
            period_stats['average_focus'] = sum(focus_scores) / len(focus_scores) if focus_scores else 0
        if 'smartphone' in metrics:
            period_stats['smartphone_usage_rate'] = sum(1 for log in logs if log.smartphone_detected) / len(logs) if logs else 0
        if 'presence' in metrics:
            period_stats['presence_rate'] = sum(1 for log in logs if log.presence_status == 'present') / len(logs) if logs else 0
        if 'activity' in metrics:
            period_stats['activity_time_minutes'] = len(logs) * 0.5
        stats.append(period_stats)
    return stats


