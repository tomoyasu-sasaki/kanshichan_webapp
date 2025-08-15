from flask import Blueprint, request
from ...response_utils import success_response, error_response
from models.config_models import (
    GeneralSettings,
    ConditionsSettings,
    DetectionObject,
    LandmarkSettings,
)


settings_bp = Blueprint('settings', __name__)


@settings_bp.get('/')
def get_settings():
    try:
        gs = GeneralSettings.query.get(1)
        cond = ConditionsSettings.query.get(1)
        if not gs:
            return error_response('Settings not initialized', code='NOT_INITIALIZED', status_code=500)
        detection_objects = {
            obj.key: {
                'enabled': bool(obj.enabled),
                'name': obj.name,
                'confidence_threshold': obj.confidence_threshold or 0.5,
                'alert_threshold': obj.alert_threshold or 0.0,
            }
            for obj in DetectionObject.query.all()
        }
        landmark = {
            ls.key: {
                'enabled': bool(ls.enabled) if ls.enabled is not None else False,
                'name': ls.name or ls.key,
            }
            for ls in LandmarkSettings.query.all()
        }
        return success_response({
            'absence_threshold': (cond.absence_threshold_seconds if cond else None),
            'smartphone_threshold': (cond.smartphone_threshold_seconds if cond else None),
            'landmark_settings': landmark,
            'detection_objects': detection_objects,
        })
    except Exception as e:  # noqa: BLE001
        return error_response('Failed to fetch settings', code='INTERNAL_ERROR', details={'error': str(e)}, status_code=500)


@settings_bp.post('/')
def update_settings():
    try:
        data = request.get_json(silent=True) or {}
        cond = ConditionsSettings.query.get(1) or ConditionsSettings(id=1)
        if 'absence_threshold' in data:
            cond.absence_threshold_seconds = float(data['absence_threshold'])
        if 'smartphone_threshold' in data:
            cond.smartphone_threshold_seconds = float(data['smartphone_threshold'])
        from models import db
        db.session.add(cond)
        det = data.get('detection_objects', {})
        for key, item in det.items():
            row = DetectionObject.query.get(key)
            if row:
                row.enabled = bool(item.get('enabled', row.enabled))
                if item.get('confidence_threshold') is not None:
                    row.confidence_threshold = float(item['confidence_threshold'])
                if item.get('alert_threshold') is not None:
                    row.alert_threshold = float(item['alert_threshold'])
        lm = data.get('landmark_settings', {})
        for key, item in lm.items():
            row = LandmarkSettings.query.get(key)
            if row:
                row.enabled = bool(item.get('enabled', row.enabled))
        db.session.commit()
        return success_response({'updated': True})
    except Exception as e:  # noqa: BLE001
        return error_response('Failed to update settings', code='INTERNAL_ERROR', details={'error': str(e)}, status_code=500)


