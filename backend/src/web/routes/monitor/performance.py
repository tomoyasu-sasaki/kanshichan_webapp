from ...response_utils import success_response, error_response
from .blueprint import monitor_bp
from utils.logger import setup_logger

logger = setup_logger(__name__)


@monitor_bp.route('/performance', methods=['GET'])
def get_monitor_performance():
    try:
        from flask import current_app
        monitor = current_app.config.get('monitor_instance')
        if monitor is None:
            logger.error("Monitor instance not found in app config for monitor/performance")
            return error_response('Monitor not initialized', code='SERVICE_UNAVAILABLE', status_code=503)
        if hasattr(monitor, 'detector') and hasattr(monitor.detector, 'get_detection_status'):
            status = monitor.detector.get_detection_status()
            performance = status.get('performance', {})
            default_stats = {
                'fps': 0.0,
                'avg_inference_ms': 0.0,
                'memory_mb': 0.0,
                'skip_rate': 1,
                'optimization_active': False,
            }
            default_stats.update(performance)
            return success_response(default_stats)
        else:
            logger.warning("Detector or performance stats not available (monitor/performance)")
            return success_response({
                'fps': 0.0,
                'avg_inference_ms': 0.0,
                'memory_mb': 0.0,
                'skip_rate': 1,
                'optimization_active': False,
            })
    except Exception as e:
        logger.error(f"Error getting monitor performance: {e}", exc_info=True)
        return error_response('Failed to get monitor performance', code='MONITOR_PERFORMANCE_ERROR', status_code=500)


