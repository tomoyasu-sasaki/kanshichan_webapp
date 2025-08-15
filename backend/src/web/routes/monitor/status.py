from datetime import datetime
from .blueprint import monitor_bp, monitor_instance
from ...response_utils import success_response, error_response
from utils.logger import setup_logger
from models.behavior_log import BehaviorLog

logger = setup_logger(__name__)


@monitor_bp.route('/status', methods=['GET'])
def get_monitor_status():
    try:
        monitor_status = 'active' if monitor_instance and monitor_instance.is_active else 'inactive'
        try:
            recent_logs = BehaviorLog.get_recent_logs(hours=1)
            data_collection_status = 'active' if recent_logs else 'inactive'
            logs_count = len(recent_logs) if recent_logs else 0
        except Exception:
            data_collection_status = 'error'
            logs_count = 0
        camera_status = 'unknown'
        device_status = 'unknown'
        if monitor_instance:
            try:
                camera_status = monitor_instance.get_camera_status()
                device_status = monitor_instance.get_device_status()
            except Exception:
                pass
        active_services = sum([1 for status in [monitor_status, data_collection_status] if status == 'active'])
        health_score = active_services / 2.0
        return success_response({
            'overall_status': 'healthy' if health_score >= 0.75 else 'degraded' if health_score >= 0.5 else 'critical',
            'health_score': health_score,
            'services': {
                'monitor_service': monitor_status,
                'data_collection': data_collection_status,
                'camera': camera_status,
                'device': device_status,
            },
            'metrics': {
                'recent_logs_count': logs_count,
                'last_log_time': recent_logs[0].timestamp.isoformat() if recent_logs else None,
            },
            'last_check': datetime.utcnow().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error checking monitor status: {e}", exc_info=True)
        return error_response('Failed to check monitor system status', code='STATUS_CHECK_ERROR', status_code=500)


