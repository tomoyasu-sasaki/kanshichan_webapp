"""
設定APIルート

`config` バインドのSQLite上の設定テーブルを読み書きするAPI。
現行UIに合わせた集約レスポンス、および閾値/検出対象/ランドマークの更新に対応。
"""

from __future__ import annotations

from flask import Blueprint, current_app, request

from models.config_models import (
    GeneralSettings,
    ConditionsSettings,
    DetectionObject,
    LandmarkSettings,
)
from web.response_utils import success_response, error_response


settings_bp = Blueprint('settings', __name__)


@settings_bp.get('/')
def get_settings():
    """設定の集約取得。

    Returns:
        Flaskレスポンス: 集約済み設定 JSON
    """
    try:
        gs = GeneralSettings.query.get(1)
        cond = ConditionsSettings.query.get(1)
        if not gs:
            return error_response('Settings not initialized', code='NOT_INITIALIZED', status_code=500)

        # aggregate response for current UI
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
    """設定の更新を反映し保存します。"""
    try:
        data = request.get_json(silent=True) or {}
        # thresholds
        cond = ConditionsSettings.query.get(1) or ConditionsSettings(id=1)
        if 'absence_threshold' in data:
            cond.absence_threshold_seconds = float(data['absence_threshold'])
        if 'smartphone_threshold' in data:
            cond.smartphone_threshold_seconds = float(data['smartphone_threshold'])
        from models import db
        db.session.add(cond)
        # Update detection thresholds currently only within config.db tables we own
        # Current UI requests include absence/smartphone thresholds; persist them into detection_objects as needed or leave to future singleton tables.
        # Update collection tables
        det = data.get('detection_objects', {})
        for key, item in det.items():
            row = DetectionObject.query.get(key)
            if row:
                row.enabled = bool(item.get('enabled', row.enabled))
                if item.get('confidence_threshold') is not None:
                    row.confidence_threshold = float(item['confidence_threshold'])
                if item.get('alert_threshold') is not None:
                    row.alert_threshold = float(item['alert_threshold'])
        # Landmarks
        lm = data.get('landmark_settings', {})
        for key, item in lm.items():
            row = LandmarkSettings.query.get(key)
            if row:
                row.enabled = bool(item.get('enabled', row.enabled))
        db.session.commit()
        return success_response({'updated': True})
    except Exception as e:  # noqa: BLE001
        return error_response('Failed to update settings', code='INTERNAL_ERROR', details={'error': str(e)}, status_code=500)


