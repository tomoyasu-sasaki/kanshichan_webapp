"""
Detection Summary Model - 検出サマリーモデル

検出ログの集計結果を保存するモデル
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, func
from sqlalchemy.orm import relationship

from .base import BaseModel
from . import db


class DetectionSummary(BaseModel):
    """
    検出サマリーモデル
    
    一定期間の検出結果を集計したサマリー情報
    オブジェクトタイプごとの出現頻度、信頼度平均などを保存
    """
    
    __tablename__ = 'detection_summary'
    
    # サマリー期間情報
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=False)
    
    # カメラ情報
    camera_id = Column(String(50), nullable=False, index=True)
    
    # 集計情報
    total_frames = Column(Integer, nullable=False)
    total_detections = Column(Integer, nullable=False)
    
    # オブジェクトクラス別集計（JSON形式）
    # {
    #   "person": {"count": 120, "avg_confidence": 0.92},
    #   "smartphone": {"count": 45, "avg_confidence": 0.87}
    # }
    object_stats = Column(JSON, nullable=False)
    
    # 追加メタデータ
    metadata = Column(JSON, nullable=True)
    
    # 関連付け
    logs = relationship("DetectionLog", back_populates="summary")
    
    @classmethod
    def create_summary(
        cls,
        camera_id: str,
        start_time: datetime,
        end_time: datetime,
        total_frames: int,
        object_stats: Dict[str, Dict[str, float]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'DetectionSummary':
        """
        検出サマリーを作成
        
        Args:
            camera_id: カメラID
            start_time: 集計開始時間
            end_time: 集計終了時間
            total_frames: 処理されたフレーム総数
            object_stats: オブジェクトクラス別統計情報
            metadata: 追加メタデータ
            
        Returns:
            DetectionSummaryインスタンス
        """
        duration = int((end_time - start_time).total_seconds())
        total_detections = sum(stats.get("count", 0) for stats in object_stats.values())
        
        return cls(
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            camera_id=camera_id,
            total_frames=total_frames,
            total_detections=total_detections,
            object_stats=object_stats,
            metadata=metadata
        )
    
    @classmethod
    def get_recent_summaries(
        cls,
        hours: int = 24,
        camera_id: Optional[str] = None
    ) -> List['DetectionSummary']:
        """
        最近のサマリーを取得
        
        Args:
            hours: 取得する時間範囲（時間単位）
            camera_id: フィルタするカメラID（オプション）
            
        Returns:
            DetectionSummaryのリスト
        """
        query = cls.query.filter(
            cls.end_time >= datetime.utcnow() - timedelta(hours=hours)
        ).order_by(cls.end_time.desc())
        
        if camera_id:
            query = query.filter(cls.camera_id == camera_id)
            
        return query.all()
    
    @classmethod
    def get_hourly_detection_counts(
        cls,
        days: int = 1,
        object_class: Optional[str] = None,
        camera_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        時間帯別の検出数を取得
        
        Args:
            days: 取得する日数
            object_class: フィルタするオブジェクトクラス（オプション）
            camera_id: フィルタするカメラID（オプション）
            
        Returns:
            時間帯別検出数のリスト
        """
        from .detection_log import DetectionLog
        
        # 期間指定
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # クエリ構築
        query = db.session.query(
            func.date_trunc('hour', DetectionLog.timestamp).label('hour'),
            func.count().label('count')
        ).filter(
            DetectionLog.timestamp >= start_date
        )
        
        # フィルタ適用
        if object_class:
            query = query.filter(DetectionLog.object_class == object_class)
            
        if camera_id:
            query = query.filter(DetectionLog.camera_id == camera_id)
            
        # グループ化
        query = query.group_by(func.date_trunc('hour', DetectionLog.timestamp))
        query = query.order_by(func.date_trunc('hour', DetectionLog.timestamp))
        
        # 結果整形
        results = []
        for row in query.all():
            results.append({
                'hour': row.hour.isoformat(),
                'count': row.count
            })
            
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換
        
        Returns:
            辞書形式のサマリー情報
        """
        result = super().to_dict()
        
        # 検出率の計算
        result['detection_rate'] = self.total_detections / self.total_frames if self.total_frames > 0 else 0
        
        # 主要オブジェクトの特定
        if self.object_stats:
            top_objects = sorted(
                self.object_stats.items(),
                key=lambda x: x[1].get('count', 0),
                reverse=True
            )[:3]
            
            result['top_objects'] = [
                {'class': obj_class, 'count': stats.get('count', 0), 'avg_confidence': stats.get('avg_confidence', 0)}
                for obj_class, stats in top_objects
            ]
        
        return result 