from datetime import datetime
from .blueprint import monitor_bp
from ...response_utils import success_response, error_response
from utils.logger import setup_logger
from models.behavior_log import BehaviorLog

logger = setup_logger(__name__)


@monitor_bp.route('/metrics', methods=['GET'])
def get_monitoring_metrics():
    try:
        from flask import request
        timeframe = request.args.get('timeframe', 'hour')
        if timeframe not in ['hour', 'day', 'week']:
            return error_response('Invalid timeframe. Must be one of: hour, day, week', code='VALIDATION_ERROR', status_code=400)
        hours_map = {'hour': 1, 'day': 24, 'week': 168}
        hours = hours_map[timeframe]
        logs = BehaviorLog.get_recent_logs(hours=hours)
        metrics = {
            'total_logs': len(logs) if logs else 0,
            'timeframe': timeframe,
            'period_hours': hours,
            'collection_rate': len(logs) / hours if logs else 0,
            'last_activity': logs[0].timestamp.isoformat() if logs else None,
            'data_coverage': {
                'has_data': len(logs) > 0 if logs else False,
                'continuous_collection': True,
            },
        }
        return success_response(metrics)
    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {e}", exc_info=True)
        return error_response('Failed to get monitoring metrics', code='METRICS_ERROR', status_code=500)


