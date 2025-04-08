from flask import Blueprint, jsonify, request, Response, current_app
import cv2
import time
from utils.logger import setup_logger
# 古いインポートを削除
# from config.message_settings import message_sound_mapping
# from config.display_settings import landmark_settings, detection_objects

logger = setup_logger(__name__)
api = Blueprint('api', __name__)

@api.route('/settings', methods=['GET'])
def get_settings():
    state_manager = current_app.config.get('monitor_instance', {}).state_manager
    config_manager = current_app.config.get('config_manager')

    if state_manager is None or config_manager is None:
        logger.error("StateManager or ConfigManager not found in app config.")
        return jsonify({'error': 'StateManager or ConfigManager not initialized'}), 500

    # 設定をすべてConfigManagerから取得する
    message_sound_mapping = config_manager.get_message_sound_mapping()
    landmark_settings = config_manager.get_landmark_settings()
    detection_objects = config_manager.get_detection_objects()

    return jsonify({
        'absence_threshold': config_manager.get('conditions.absence.threshold_seconds'),
        'smartphone_threshold': config_manager.get('conditions.smartphone_usage.threshold_seconds'),
        'message_extensions': {
            message: data['extension']
            for message, data in message_sound_mapping.items()
        },
        'landmark_settings': landmark_settings,
        'detection_objects': detection_objects
    })

@api.route('/settings', methods=['POST'])
def update_settings():
    state_manager = current_app.config.get('monitor_instance', {}).state_manager
    config_manager = current_app.config.get('config_manager')

    if state_manager is None or config_manager is None:
        logger.error("StateManager or ConfigManager not found in app config.")
        return jsonify({'error': 'StateManager or ConfigManager not initialized'}), 500

    data = request.get_json()
    config_updated = False

    if 'absence_threshold' in data:
        try:
            new_threshold = float(data['absence_threshold'])
            config_manager.set('conditions.absence.threshold_seconds', new_threshold)
            state_manager.absence_threshold = new_threshold
            config_updated = True
            logger.info(f"Absence threshold updated to {new_threshold} (memory & StateManager)")
        except ValueError:
            return jsonify({'error': 'Invalid value for absence_threshold'}), 400
    if 'smartphone_threshold' in data:
        try:
            new_threshold = float(data['smartphone_threshold'])
            config_manager.set('conditions.smartphone_usage.threshold_seconds', new_threshold)
            state_manager.smartphone_threshold = new_threshold
            config_updated = True
            logger.info(f"Smartphone threshold updated to {new_threshold} (memory & StateManager)")
        except ValueError:
            return jsonify({'error': 'Invalid value for smartphone_threshold'}), 400
    
    if 'message_extensions' in data:
        message_sound_mapping = config_manager.get_message_sound_mapping()
        for message, extension in data['message_extensions'].items():
            if message in message_sound_mapping:
                try:
                    # 設定をConfigManagerを通じて更新
                    new_extension = int(extension)
                    config_manager.set(f'message_sound_mapping.{message}.extension', new_extension)
                    config_updated = True
                except ValueError:
                    logger.warning(f"Invalid extension value for {message}: {extension}")
    
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

    return jsonify({'status': 'success'})

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