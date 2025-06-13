"""
Detection Log Model - 検出ログモデル

物体検出の詳細ログを保存するモデル
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel
from . import db


class DetectionLog(BaseModel):
    """
    検出ログモデル
    
    物体検出の詳細情報を記録するモデル
    検出オブジェクト、信頼度、位置情報などを保存
    """
    
    __tablename__ = 'detection_log'
    
    # 検出情報
    timestamp = Column(DateTime, nullable=False, index=True)
    camera_id = Column(String(50), nullable=False, index=True)
    frame_id = Column(Integer, nullable=False)
    
    # 検出オブジェクト情報
    object_class = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    
    # バウンディングボックス
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_width = Column(Float, nullable=False)
    bbox_height = Column(Float, nullable=False)
    
    # 追加情報
    is_smoothed = Column(Boolean, default=False)
    is_interpolated = Column(Boolean, default=False)
    additional_data = Column(JSON, nullable=True)
    
    # 関連付け
    summary_id = Column(Integer, ForeignKey('detection_summary.id'), nullable=True)
    summary = relationship("DetectionSummary", back_populates="logs")
    
    @classmethod
    def create_from_detection(
        cls, 
        camera_id: str, 
        frame_id: int, 
        object_class: str, 
        confidence: float,
        bbox: tuple,
        is_smoothed: bool = False,
        is_interpolated: bool = False,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> 'DetectionLog':
        """
        検出結果からDetectionLogインスタンスを作成
        
        Args:
            camera_id: カメラID
            frame_id: フレームID
            object_class: 検出オブジェクトのクラス名
            confidence: 検出信頼度
            bbox: バウンディングボックス (x, y, width, height)
            is_smoothed: スムージング適用済みか
            is_interpolated: 補間されたデータか
            additional_data: 追加データ（JSON形式）
            
        Returns:
            DetectionLogインスタンス
        """
        return cls(
            timestamp=datetime.utcnow(),
            camera_id=camera_id,
            frame_id=frame_id,
            object_class=object_class,
            confidence=confidence,
            bbox_x=bbox[0],
            bbox_y=bbox[1],
            bbox_width=bbox[2],
            bbox_height=bbox[3],
            is_smoothed=is_smoothed,
            is_interpolated=is_interpolated,
            additional_data=additional_data
        )
    
    @classmethod
    def get_recent_logs(
        cls, 
        hours: int = 24, 
        camera_id: Optional[str] = None,
        object_class: Optional[str] = None
    ) -> List['DetectionLog']:
        """
        最近の検出ログを取得
        
        Args:
            hours: 取得する時間範囲（時間単位）
            camera_id: フィルタするカメラID（オプション）
            object_class: フィルタするオブジェクトクラス（オプション）
            
        Returns:
            DetectionLogのリスト
        """
        query = cls.query.filter(
            cls.timestamp >= datetime.utcnow() - datetime.timedelta(hours=hours)
        ).order_by(cls.timestamp.desc())
        
        if camera_id:
            query = query.filter(cls.camera_id == camera_id)
            
        if object_class:
            query = query.filter(cls.object_class == object_class)
            
        return query.all()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換
        
        Returns:
            辞書形式の検出ログ
        """
        result = super().to_dict()
        
        # バウンディングボックスを単一のフィールドにまとめる
        result['bbox'] = (
            result.pop('bbox_x'),
            result.pop('bbox_y'),
            result.pop('bbox_width'),
            result.pop('bbox_height')
        )
        
        return result 