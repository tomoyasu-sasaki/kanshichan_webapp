from flask import Blueprint, jsonify, request, Response
import cv2
import time
from backend.src.core.monitor import Monitor
from backend.src.utils.logger import setup_logger
from backend.src.config.message_settings import message_sound_mapping
from backend.src.config.display_settings import landmark_settings, detection_objects

logger = setup_logger(__name__)
api = Blueprint('api', __name__)

@api.route('/settings', methods=['GET'])
def get_settings():
    monitor = Monitor.get_instance()
    if monitor is None:
        return jsonify({'error': 'Monitor not initialized'}), 500
    
    return jsonify({
        'absence_threshold': monitor.absence_threshold,
        'smartphone_threshold': monitor.smartphone_threshold,
        'message_extensions': {
            message: data['extension']
            for message, data in message_sound_mapping.items()
        },
        'landmark_settings': landmark_settings,
        'detection_objects': detection_objects
    })

@api.route('/settings', methods=['POST'])
def update_settings():
    monitor = Monitor.get_instance()
    if monitor is None:
        return jsonify({'error': 'Monitor not initialized'}), 500
    
    data = request.get_json()
    
    if 'absence_threshold' in data:
        monitor.absence_threshold = float(data['absence_threshold'])
    if 'smartphone_threshold' in data:
        monitor.smartphone_threshold = float(data['smartphone_threshold'])
    
    # メッセージ延長時間の更新
    if 'message_extensions' in data:
        for message, extension in data['message_extensions'].items():
            if message in message_sound_mapping:
                message_sound_mapping[message]['extension'] = int(extension)
    
    # ランドマーク設定の更新
    if 'landmark_settings' in data:
        for key, settings in data['landmark_settings'].items():
            if key in landmark_settings:
                landmark_settings[key]['enabled'] = settings['enabled']
    
    # 検出対象物体設定の更新
    if 'detection_objects' in data:
        for key, settings in data['detection_objects'].items():
            if key in detection_objects:
                detection_objects[key].update({
                    'enabled': settings['enabled'],
                    'confidence_threshold': float(settings['confidence_threshold']),
                    'alert_threshold': float(settings['alert_threshold'])
                })
    
    return jsonify({'status': 'success'})

@api.route('/video_feed')
def video_feed():
    """映像ストリームのエンドポイント"""
    def generate():
        monitor = Monitor.get_instance()
        if monitor is None:
            return
        
        while True:
            frame = monitor.get_current_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(1/30)  # 30fps制限

    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame') 