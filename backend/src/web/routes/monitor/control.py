from datetime import datetime
from flask import request
from .blueprint import monitor_bp, monitor_instance
from ...response_utils import success_response, error_response
from utils.logger import setup_logger

logger = setup_logger(__name__)


@monitor_bp.route('/toggle', methods=['POST'])
def toggle_monitoring():
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        if not monitor_instance:
            return error_response('Monitor service not available', code='SERVICE_UNAVAILABLE', status_code=503)
        if hasattr(monitor_instance, 'start') and hasattr(monitor_instance, 'stop'):
            if enabled:
                monitor_instance.start()
                action = 'started'
            else:
                monitor_instance.stop()
                action = 'stopped'
        else:
            action = 'started' if enabled else 'stopped'
            logger.info(f"Monitor service {action} (simulated)")
        return success_response({
            'monitoring_enabled': enabled,
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error toggling monitoring: {e}", exc_info=True)
        return error_response('Failed to toggle monitoring', code='TOGGLE_ERROR', status_code=500)


