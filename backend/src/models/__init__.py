"""
KanshiChan Models Package

行動ログ、分析結果、ユーザープロファイル、検出ログの管理
"""

from flask_sqlalchemy import SQLAlchemy

# データベースインスタンス
db = SQLAlchemy()

def _seed_config_defaults(app) -> None:
    """config.db に最低限の初期行を投入（未存在時のみ）。

    - general_settings(id=1)
    - conditions_settings(id=1)
    - detection_objects / landmark_settings をコード定義のデフォルトで補完
    """
    try:
        from .config_models import (
            GeneralSettings,
            ConditionsSettings,
            DetectionObject,
            LandmarkSettings,
        )
        with app.app_context():
            cfgm = app.config.get('config_manager')
            # general_settings
            if not GeneralSettings.query.get(1):
                server_port = 8000
                if cfgm:
                    try:
                        server_port = int(cfgm.get('server.port', 8000))
                    except Exception:
                        server_port = 8000
                db.session.add(GeneralSettings(id=1, server_port=server_port))

            # conditions_settings（未存在時のみ、コード定義のデフォルトを投入）
            cond = ConditionsSettings.query.get(1)
            if not cond:
                db.session.add(ConditionsSettings(
                    id=1,
                    absence_threshold_seconds=60.0,
                    smartphone_threshold_seconds=60.0,
                    smartphone_grace_period_seconds=3.0,
                ))

            # detection_objects（未存在キーのみ、コード定義デフォルトを投入）
            DEFAULT_DETECTION_OBJECTS = {
                'book': {
                    'name': '本',
                    'class_name': 'book',
                    'alert_message': '',
                    'alert_sound': '',
                    'alert_threshold': 0.0,
                    'confidence_threshold': 0.5,
                    'enabled': False,
                    'thickness': 2,
                    'color': [0, 255, 0],
                },
                'laptop': {
                    'name': 'laptop',
                    'class_name': 'laptop',
                    'alert_message': 'ノートパソコンの使用を検知しました',
                    'alert_sound': 'alert.wav',
                    'alert_threshold': 3.0,
                    'confidence_threshold': 0.5,
                    'enabled': False,
                    'thickness': 2,
                    'color': [0, 255, 255],
                },
                'smartphone': {
                    'name': 'smartphone',
                    'class_name': 'cell phone',
                    'alert_message': 'スマホばかり触っていないで勉強をしろ！',
                    'alert_sound': 'smartphone_alert.wav',
                    'alert_threshold': 3.0,
                    'confidence_threshold': 0.4,
                    'enabled': True,
                    'thickness': 3,
                    'color': [0, 255, 255],
                },
            }

            for key, item in DEFAULT_DETECTION_OBJECTS.items():
                if not DetectionObject.query.get(key):
                    db.session.add(DetectionObject(
                        key=key,
                        name=item['name'],
                        class_name=item['class_name'],
                        alert_message=item['alert_message'],
                        alert_sound=item['alert_sound'],
                        alert_threshold=item['alert_threshold'],
                        confidence_threshold=item['confidence_threshold'],
                        enabled=bool(item['enabled']),
                        thickness=item['thickness'],
                        color_r=item['color'][0],
                        color_g=item['color'][1],
                        color_b=item['color'][2],
                    ))

            # landmark_settings（未存在キーのみ、コード定義デフォルトを投入）
            DEFAULT_LANDMARK_SETTINGS = {
                'face': {
                    'name': '顔',
                    'enabled': False,
                    'thickness': 2,
                    'color': [255, 0, 0],
                },
                'hands': {
                    'name': '手',
                    'enabled': True,
                    'thickness': 2,
                    'color': [0, 0, 255],
                },
                'pose': {
                    'name': '姿勢',
                    'enabled': True,
                    'thickness': 2,
                    'color': [0, 255, 0],
                },
            }

            for key, item in DEFAULT_LANDMARK_SETTINGS.items():
                if not LandmarkSettings.query.get(key):
                    db.session.add(LandmarkSettings(
                        key=key,
                        name=item['name'],
                        enabled=item['enabled'],
                        thickness=item['thickness'],
                        color_r=item['color'][0],
                        color_g=item['color'][1],
                        color_b=item['color'][2],
                    ))

            db.session.commit()
    except Exception:
        # 初期投入失敗は致命ではない（後続のAPIで上書き可能）
        pass

def init_db(app):
    """データベースの初期化
    
    Args:
        app: Flask アプリケーションインスタンス
    """
    db.init_app(app)
    
    # モデルのインポート（循環インポート回避のため）
    from . import behavior_log, analysis_result, user_profile, detection_log, detection_summary
    # 設定用モデル（configバインド）
    try:
        from . import config_models  # noqa: F401
    except Exception:
        # 存在しなくても致命的ではない（段階移行のため）
        pass
    
    with app.app_context():
        # 既存（デフォルトバインド）
        db.create_all()
        # 設定DB（configバインド）
        try:
            db.create_all(bind_key='config')
        except TypeError:
            # FSA 3.0 では bind_key=['config'] も可
            db.create_all(bind_key=['config'])
        # 最低限のデフォルトを投入（未存在時のみ）
        _seed_config_defaults(app)

__all__ = ['db', 'init_db'] 