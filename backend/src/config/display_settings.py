# ランドマークの表示設定
landmark_settings = {
    'pose': {
        'enabled': True,
        'name': '姿勢',
        'color': (0, 255, 0),  # BGR形式
        'thickness': 2
    },
    'face': {
        'enabled': True,
        'name': '顔',
        'color': (255, 0, 0),
        'thickness': 2
    },
    'hands': {
        'enabled': True,
        'name': '手',
        'color': (0, 0, 255),
        'thickness': 2
    }
}

# 検出対象物体の設定
detection_objects = {
    'smartphone': {
        'enabled': True,
        'name': 'スマートフォン',
        'class_name': 'cell phone',  # YOLOv8のクラス名
        'confidence_threshold': 0.5,
        'color': (255, 0, 0),
        'thickness': 2,
        'alert_threshold': 3,  # 警告を出すまでの時間（秒）
        'alert_message': 'スマホばかり触っていないで勉強をしろ！',
        'alert_sound': 'smartphone_alert.wav'
    },
    'laptop': {
        'enabled': False,
        'name': 'ノートパソコン',
        'class_name': 'laptop',
        'confidence_threshold': 0.5,
        'color': (0, 255, 255),
        'thickness': 2,
        'alert_threshold': 3,
        'alert_message': 'ノートパソコンの使用を検知しました',
        'alert_sound': 'alert.wav'
    },
    'book': {
        'enabled': False,
        'name': '本',
        'class_name': 'book',
        'confidence_threshold': 0.5,
        'color': (0, 255, 0),
        'thickness': 2,
        'alert_threshold': 0,  # 0の場合は警告を出さない
        'alert_message': '',
        'alert_sound': ''
    }
} 