"""
Base Model Class

全てのモデルクラスが継承する基底クラス
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

from . import db

class BaseModel(db.Model):
    """全モデルクラスの基底クラス
    
    共通フィールド:
        - id: プライマリキー
        - created_at: 作成日時
        - updated_at: 更新日時
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self) -> None:
        """データベースに保存
        
        Raises:
            SQLAlchemyError: データベース操作エラー
        """
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self) -> None:
        """データベースから削除
        
        Raises:
            SQLAlchemyError: データベース操作エラー
        """
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def to_dict(self) -> dict:
        """辞書形式に変換
        
        Returns:
            dict: モデルの辞書表現
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

