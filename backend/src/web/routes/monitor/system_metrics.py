from datetime import datetime
import psutil
from .blueprint import monitor_bp
from ...response_utils import success_response, error_response
from utils.logger import setup_logger

logger = setup_logger(__name__)


@monitor_bp.route('/system-metrics', methods=['GET'])
def get_system_metrics():
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count()
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent
        memory_used = memory_info.used
        memory_total = memory_info.total
        disk_info = psutil.disk_usage('/')
        disk_percent = disk_info.percent
        disk_used = disk_info.used
        disk_total = disk_info.total
        gpu_info = {
            'available': False,
            'usage_percent': 0,
            'memory_used': 0,
            'memory_total': 0,
        }
        system_metrics = {
            'cpu': {
                'usage_percent': cpu_percent,
                'cores': cpu_cores,
                'per_core_usage': cpu_per_core,
            },
            'memory': {
                'usage_percent': memory_percent,
                'used_bytes': memory_used,
                'total_bytes': memory_total,
                'used_gb': round(memory_used / (1024 ** 3), 2),
                'total_gb': round(memory_total / (1024 ** 3), 2),
            },
            'disk': {
                'usage_percent': disk_percent,
                'used_bytes': disk_used,
                'total_bytes': disk_total,
                'used_gb': round(disk_used / (1024 ** 3), 2),
                'total_gb': round(disk_total / (1024 ** 3), 2),
            },
            'gpu': gpu_info,
            'timestamp': datetime.utcnow().isoformat(),
        }
        return success_response(system_metrics)
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}", exc_info=True)
        return error_response('Failed to get system metrics', code='SYSTEM_METRICS_ERROR', status_code=500)


