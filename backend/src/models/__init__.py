"""
KanshiChan Models Package

行動ログ、分析結果、ユーザープロファイル、検出ログの管理
"""

from flask_sqlalchemy import SQLAlchemy

# データベースインスタンス
db = SQLAlchemy()

def init_db(app):
    """データベースの初期化
    
    Args:
        app: Flask アプリケーションインスタンス
    """
    db.init_app(app)
    
    # モデルのインポート（循環インポート回避のため）
    from . import behavior_log, analysis_result, user_profile, detection_log, detection_summary
    
    with app.app_context():
        db.create_all()

__all__ = ['db', 'init_db'] 