from flask import request
from ...response_utils import success_response, error_response
from .blueprint import behavior_bp
from models.behavior_log import BehaviorLog
from .utils import timeframe_range, calculate_posture_alerts


@behavior_bp.route('/summary/dashboard', methods=['GET'])
def get_dashboard_summary():
    try:
        user_id = request.args.get('user_id')
        today_data = _get_daily_dashboard_data('today', user_id)
        yesterday_data = _get_daily_dashboard_data('yesterday', user_id)
        return success_response({'today': today_data, 'yesterday': yesterday_data})
    except Exception:
        return error_response('Failed to get dashboard summary', code='SUMMARY_ERROR', status_code=500)


def _empty_dashboard_data():
    return {
        'total_time': 0,
        'focus_time': 0,
        'break_time': 0,
        'absence_time': 0,
        'smartphone_usage_time': 0,
        'posture_alerts': 0,
    }


def _get_daily_dashboard_data(timeframe: str, user_id: str = None):
    try:
        start_time, end_time = timeframe_range(timeframe)
        if isinstance(start_time, dict):
            return _empty_dashboard_data()
        logs = BehaviorLog.get_logs_by_timerange(start_time, end_time, user_id)
        if not logs:
            return _empty_dashboard_data()
        total_seconds = len(logs) * 2  # 5秒間隔と仮定
        focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
        avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else 0
        presence_rate = sum(1 for log in logs if log.presence_status == 'present') / len(logs)
        smartphone_rate = sum(1 for log in logs if log.smartphone_detected) / len(logs)
        posture_alerts = calculate_posture_alerts(logs)
        dashboard_data = {
            'total_time': total_seconds,
            'focus_time': int(total_seconds * avg_focus),
            'break_time': int(total_seconds * (1 - avg_focus) * presence_rate),
            'absence_time': int(total_seconds * (1 - presence_rate)),
            'smartphone_usage_time': int(total_seconds * smartphone_rate),
            'posture_alerts': posture_alerts,
        }
        return dashboard_data
    except Exception:
        return _empty_dashboard_data()


