from flask import Blueprint, jsonify, request, Response, current_app
import cv2
import time
from utils.logger import setup_logger
from utils.exceptions import (
    APIError, ConfigError, ValidationError, ScheduleError,
    InitializationError, wrap_exception
)
from web.response_utils import success_response, error_response, error_from_exception

logger = setup_logger(__name__)
api = Blueprint('api', __name__)

@api.route('/settings', methods=['GET'])
def get_settings():
    state = current_app.config.get('monitor_instance', {}).state
    config_manager = current_app.config.get('config_manager')

    if state is None or config_manager is None:
        init_error = InitializationError(
            "StateManager or ConfigManager not found in app config",
            details={'state_available': state is not None, 'config_manager_available': config_manager is not None}
        )
        logger.error(f"API initialization error: {init_error.to_dict()}")
        return error_from_exception(init_error, status_code=500, include_details=True)

    # 設定をすべてConfigManagerから取得する
    landmark_settings = config_manager.get_landmark_settings()
    detection_objects = config_manager.get_detection_objects()

    return success_response({
        'absence_threshold': config_manager.get('conditions.absence.threshold_seconds'),
        'smartphone_threshold': config_manager.get('conditions.smartphone_usage.threshold_seconds'),
        'landmark_settings': landmark_settings,
        'detection_objects': detection_objects
    })

@api.route('/settings', methods=['POST'])
def update_settings():
    state = current_app.config.get('monitor_instance', {}).state
    config_manager = current_app.config.get('config_manager')

    if state is None or config_manager is None:
        init_error = InitializationError(
            "StateManager or ConfigManager not found in app config",
            details={'state_available': state is not None, 'config_manager_available': config_manager is not None}
        )
        logger.error(f"API initialization error: {init_error.to_dict()}")
        return error_from_exception(init_error, status_code=500, include_details=True)

    data = request.get_json()
    config_updated = False

    if 'absence_threshold' in data:
        try:
            new_threshold = float(data['absence_threshold'])
            config_manager.set('conditions.absence.threshold_seconds', new_threshold)
            state.absence_threshold = new_threshold
            config_updated = True
            logger.info(f"Absence threshold updated to {new_threshold} (memory & StateManager)")
        except ValueError as e:
            validation_error = wrap_exception(
                e, ValidationError,
                "Invalid value for absence_threshold",
                details={'value': data['absence_threshold'], 'expected_type': 'float'}
            )
            logger.error(f"Absence threshold validation error: {validation_error.to_dict()}")
            return error_from_exception(validation_error, status_code=400)
    if 'smartphone_threshold' in data:
        try:
            new_threshold = float(data['smartphone_threshold'])
            config_manager.set('conditions.smartphone_usage.threshold_seconds', new_threshold)
            state.smartphone_threshold = new_threshold
            config_updated = True
            logger.info(f"Smartphone threshold updated to {new_threshold} (memory & StateManager)")
        except ValueError as e:
            validation_error = wrap_exception(
                e, ValidationError,
                "Invalid value for smartphone_threshold",
                details={'value': data['smartphone_threshold'], 'expected_type': 'float'}
            )
            logger.error(f"Smartphone threshold validation error: {validation_error.to_dict()}")
            return error_from_exception(validation_error, status_code=400)
    
    if 'landmark_settings' in data:
        for key, settings in data['landmark_settings'].items():
            if isinstance(settings, dict) and 'enabled' in settings:
                # 設定をConfigManagerを通じて更新
                enabled = bool(settings['enabled'])
                config_manager.set(f'landmark_settings.{key}.enabled', enabled)
                config_updated = True
            else:
                logger.warning(f"Invalid landmark settings for {key}: {settings}")
    
    # 検出対象物体設定の更新
    if 'detection_objects' in data:
        for key, settings in data['detection_objects'].items():
            if isinstance(settings, dict):
                try:
                    # 設定をConfigManagerを通じて更新
                    if 'enabled' in settings:
                        config_manager.set(f'detection_objects.{key}.enabled', bool(settings['enabled']))
                        config_updated = True
                    if 'confidence_threshold' in settings:
                        config_manager.set(f'detection_objects.{key}.confidence_threshold', float(settings['confidence_threshold']))
                        config_updated = True
                    if 'alert_threshold' in settings:
                        config_manager.set(f'detection_objects.{key}.alert_threshold', float(settings['alert_threshold']))
                        config_updated = True
                except ValueError:
                    logger.warning(f"Invalid detection object settings for {key}: {settings}")
                except KeyError as e:
                    logger.warning(f"Missing key in detection object settings for {key}: {e}")
    
    if config_updated:
        if config_manager.save():
            logger.info("Configuration saved to file successfully after update.")
        else:
            logger.error("Failed to save configuration after update.")
            # 500 エラーを返しても良いかもしれないが、一旦ログのみ
            # return jsonify({'status': 'success', 'warning': 'Failed to save config'}), 200

    return success_response({'updated': config_updated})

@api.route('/video_feed')
def video_feed():
    """映像ストリームのエンドポイント"""
    monitor = current_app.config.get('monitor_instance')
    if monitor is None:
        logger.error("Monitor instance not found in app config for video_feed.")
        return Response("Monitor not initialized", status=500)

    def generate():
        if monitor is None:
            return
        logger.info("Starting video stream generation...")
        try:
            while True:
                frame_bytes = monitor.get_current_frame()
                if frame_bytes is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    pass
                time.sleep(1/30)
        except GeneratorExit:
            logger.info("Video stream generator closed.")
        except Exception as e:
            logger.error(f"Error in video stream generator: {e}", exc_info=True)
        finally:
            logger.info("Video stream generation finished.")

    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

# スケジュール関連のAPIエンドポイント
@api.route('/schedules', methods=['GET'])
def get_schedules():
    """登録されているスケジュール一覧を取得する"""
    schedule_manager = current_app.config.get('schedule_manager')
    
    if schedule_manager is None:
        logger.error("ScheduleManager not found in app config")
        return error_response('ScheduleManager not initialized', code='SERVICE_UNAVAILABLE', status_code=500)
    
    try:
        schedules = schedule_manager.get_schedules()
        return success_response({'schedules': schedules})
    except Exception as e:
        logger.error(f"Error getting schedules: {e}", exc_info=True)
        return error_response(str(e), code='INTERNAL_ERROR', status_code=500)

@api.route('/schedules', methods=['POST'])
def add_schedule():
    """新しいスケジュールを登録する"""
    schedule_manager = current_app.config.get('schedule_manager')
    
    if schedule_manager is None:
        logger.error("ScheduleManager not found in app config")
        return error_response('ScheduleManager not initialized', code='SERVICE_UNAVAILABLE', status_code=500)
    
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided', code='VALIDATION_ERROR', status_code=400)
            
        time = data.get('time')
        content = data.get('content')
        
        if not time or not content:
            return error_response('Time and content are required', code='VALIDATION_ERROR', status_code=400)
        
        new_schedule = schedule_manager.add_schedule(time, content)
        if not new_schedule:
            return error_response('Failed to add schedule', code='SCHEDULE_ADD_FAILED', status_code=500)
        
        return success_response({'schedule': new_schedule}, status_code=201)
    except Exception as e:
        logger.error(f"Error adding schedule: {e}", exc_info=True)
        return error_response(str(e), code='INTERNAL_ERROR', status_code=500)

@api.route('/performance', methods=['GET'])
def get_performance_stats():
    """パフォーマンス統計を取得する"""
    monitor = current_app.config.get('monitor_instance')
    
    if monitor is None:
        logger.error("Monitor instance not found in app config for performance stats")
        return error_response('Monitor not initialized', code='SERVICE_UNAVAILABLE', status_code=500)
    
    try:
        # ObjectDetectorからパフォーマンス統計を取得
        if hasattr(monitor, 'detector') and hasattr(monitor.detector, 'get_detection_status'):
            status = monitor.detector.get_detection_status()
            performance_data = status.get('performance', {})
            
            # デフォルト値を設定
            default_stats = {
                'fps': 0.0,
                'avg_inference_ms': 0.0,
                'memory_mb': 0.0,
                'skip_rate': 1,
                'optimization_active': False
            }
            
            # 実際のデータで更新
            default_stats.update(performance_data)
            
            return success_response(default_stats)
        else:
            logger.warning("Detector or performance stats not available")
            return success_response({
                'fps': 0.0,
                'avg_inference_ms': 0.0,
                'memory_mb': 0.0,
                'skip_rate': 1,
                'optimization_active': False
            })
            
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}", exc_info=True)
        return error_response('Failed to get performance stats', code='INTERNAL_ERROR', status_code=500)

@api.route('/schedules/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """指定されたIDのスケジュールを削除する"""
    schedule_manager = current_app.config.get('schedule_manager')
    
    if schedule_manager is None:
        logger.error("ScheduleManager not found in app config")
        return error_response('ScheduleManager not initialized', code='SERVICE_UNAVAILABLE', status_code=500)
    
    try:
        if not schedule_id:
            return error_response('Schedule ID is required', code='VALIDATION_ERROR', status_code=400)
        
        success = schedule_manager.delete_schedule(schedule_id)
        if not success:
            return error_response('Schedule not found or could not be deleted', code='SCHEDULE_DELETE_FAILED', status_code=404)
        
        return success_response({'deleted': True}, status_code=200)
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}", exc_info=True)
        return error_response(str(e), code='INTERNAL_ERROR', status_code=500)