"""
Behavior Log Model

監視データの記録モデル - YOLOv8検出結果、MediaPipe集中度、姿勢データを保存
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import Column, String, DateTime, Float, JSON, Text, Boolean, Index
from .base import BaseModel


class BehaviorLog(BaseModel):
    """行動ログモデル
    
    監視システムが取得したリアルタイムデータを記録
    - 検出オブジェクト（YOLOv8結果）
    - 集中度データ（MediaPipe）
    - 姿勢データ
    - 画面アクティビティ
    """
    
    __tablename__ = 'behavior_logs'
    
    # タイムスタンプ（インデックス付き）
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # YOLOv8検出結果
    detected_objects = Column(JSON, nullable=True, comment="YOLOv8で検出されたオブジェクト一覧")
    object_count = Column(JSON, nullable=True, comment="オブジェクト種別ごとの検出数")
    
    # MediaPipe集中度・姿勢データ
    focus_level = Column(Float, nullable=True, comment="集中度スコア (0.0-1.0)")
    posture_data = Column(JSON, nullable=True, comment="姿勢データ（顔向き、体の傾き等）")
    face_landmarks = Column(JSON, nullable=True, comment="顔のランドマーク座標")
    
    # スマートフォン使用状況
    smartphone_detected = Column(Boolean, default=False, comment="スマートフォン検出フラグ")
    smartphone_duration = Column(Float, nullable=True, comment="スマートフォン使用継続時間（秒）")
    
    # 画面・環境アクティビティ
    screen_activity = Column(JSON, nullable=True, comment="画面アクティビティデータ")
    environment_data = Column(JSON, nullable=True, comment="環境データ（明度、音量等）")
    
    # 状態判定結果
    presence_status = Column(String(20), nullable=True, comment="在席状況 (present/absent/break)")
    attention_status = Column(String(20), nullable=True, comment="注意状況 (focused/distracted/unknown)")
    
    # セッション情報
    session_id = Column(String(50), nullable=True, index=True, comment="学習セッションID")
    work_category = Column(String(50), nullable=True, comment="作業カテゴリ")
    
    # 追加メタデータ
    confidence_scores = Column(JSON, nullable=True, comment="各検出の信頼度スコア")
    processing_time = Column(Float, nullable=True, comment="処理時間（ミリ秒）")
    notes = Column(Text, nullable=True, comment="追加メモ・コメント")
    
    # 複合インデックス（パフォーマンス最適化）
    __table_args__ = (
        Index('idx_timestamp_session', 'timestamp', 'session_id'),
        Index('idx_presence_attention', 'presence_status', 'attention_status'),
        Index('idx_smartphone_usage', 'smartphone_detected', 'timestamp'),
        Index('idx_focus_analysis', 'timestamp', 'focus_level', 'attention_status'),
        Index('idx_timeframe_presence', 'timestamp', 'presence_status', 'session_id'),
        Index('idx_recent_activity', 'timestamp', 'smartphone_detected', 'focus_level'),
        # 日次データアクセス最適化用インデックス（SQLite互換）
        Index('idx_daily_timestamp', 'timestamp'),
    )
    
    @classmethod
    def create_log(cls, 
                   timestamp: datetime,
                   detected_objects: Optional[List[Dict]] = None,
                   focus_level: Optional[float] = None,
                   posture_data: Optional[Dict] = None,
                   smartphone_detected: bool = False,
                   presence_status: Optional[str] = None,
                   session_id: Optional[str] = None,
                   **kwargs) -> 'BehaviorLog':
        """行動ログエントリを作成
        
        Args:
            timestamp: ログのタイムスタンプ
            detected_objects: YOLOv8検出結果
            focus_level: 集中度スコア (0.0-1.0)
            posture_data: 姿勢データ
            smartphone_detected: スマートフォン検出フラグ
            presence_status: 在席状況
            session_id: セッションID
            **kwargs: 追加のフィールド
            
        Returns:
            BehaviorLog: 作成されたログエントリ
        """
        # オブジェクト検出数の集計
        object_count = {}
        if detected_objects:
            for obj in detected_objects:
                obj_class = obj.get('class', 'unknown')
                object_count[obj_class] = object_count.get(obj_class, 0) + 1
        
        # 注意状況の判定
        attention_status = cls._determine_attention_status(
            focus_level, smartphone_detected, detected_objects
        )
        
        return cls(
            timestamp=timestamp,
            detected_objects=detected_objects,
            object_count=object_count,
            focus_level=focus_level,
            posture_data=posture_data,
            smartphone_detected=smartphone_detected,
            presence_status=presence_status,
            attention_status=attention_status,
            session_id=session_id,
            **kwargs
        )
    
    @staticmethod
    def _determine_attention_status(focus_level: Optional[float],
                                  smartphone_detected: bool,
                                  detected_objects: Optional[List[Dict]]) -> str:
        """注意状況を判定
        
        Args:
            focus_level: 集中度スコア
            smartphone_detected: スマートフォン検出フラグ
            detected_objects: 検出オブジェクト
            
        Returns:
            str: 注意状況 (focused/distracted/unknown)
        """
        if smartphone_detected:
            return 'distracted'
        
        if focus_level is not None:
            if focus_level >= 0.7:
                return 'focused'
            elif focus_level <= 0.3:
                return 'distracted'
        
        return 'unknown'
    
    def get_analysis_data(self) -> Dict[str, Any]:
        """分析用データを取得
        
        Returns:
            dict: 分析に使用するデータ
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'focus_level': self.focus_level,
            'smartphone_detected': self.smartphone_detected,
            'presence_status': self.presence_status,
            'attention_status': self.attention_status,
            'object_count': self.object_count,
            'posture_score': self._calculate_posture_score(),
            'session_id': self.session_id
        }
    
    def _calculate_posture_score(self) -> Optional[float]:
        """姿勢スコアを計算
        
        Returns:
            float: 姿勢スコア (0.0-1.0) または None
        """
        if not self.posture_data:
            return None
        
        # 簡単な姿勢評価ロジック
        # 実際は MediaPipe の pose landmark を使用して詳細計算
        head_position = self.posture_data.get('head_position')
        shoulder_alignment = self.posture_data.get('shoulder_alignment')
        
        if head_position and shoulder_alignment:
            # 正面向き、肩の水平度合いから姿勢スコアを算出
            return min(1.0, (head_position + shoulder_alignment) / 2.0)
        
        return None
    
    @classmethod
    def get_recent_logs(cls, 
                       hours: int = 24, 
                       user_id: Optional[str] = None,
                       session_id: Optional[str] = None) -> List['BehaviorLog']:
        """最近のログを取得（拡張版）
        
        Args:
            hours: 取得する時間範囲（時間）
            user_id: ユーザーID（オプション）
            session_id: 特定のセッションのみ取得
            
        Returns:
            List[BehaviorLog]: ログエントリのリスト
        """
        from datetime import timedelta
        from . import db
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(cls.timestamp >= cutoff_time)
        
        if user_id:
            query = query.filter(cls.session_id == user_id)
        
        if session_id:
            query = query.filter(cls.session_id == session_id)
        
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_focus_statistics(cls, 
                           start_time: datetime, 
                           end_time: datetime) -> Dict[str, float]:
        """集中度統計を取得
        
        Args:
            start_time: 開始時刻
            end_time: 終了時刻
            
        Returns:
            dict: 集中度統計データ
        """
        from sqlalchemy import func
        from . import db
        
        query = db.session.query(
            func.avg(cls.focus_level).label('avg_focus'),
            func.max(cls.focus_level).label('max_focus'),
            func.min(cls.focus_level).label('min_focus'),
            func.count(cls.id).label('total_entries')
        ).filter(
            cls.timestamp.between(start_time, end_time),
            cls.focus_level.isnot(None)
        )
        
        result = query.first()
        
        return {
            'average_focus': float(result.avg_focus) if result.avg_focus else 0.0,
            'max_focus': float(result.max_focus) if result.max_focus else 0.0,
            'min_focus': float(result.min_focus) if result.min_focus else 0.0,
            'total_entries': result.total_entries
        }
    
    @classmethod
    def get_logs_by_timerange(cls,
                            start_time: datetime,
                            end_time: datetime,
                            user_id: Optional[str] = None) -> List['BehaviorLog']:
        """時間範囲でログを取得
        
        Args:
            start_time: 開始時刻
            end_time: 終了時刻
            user_id: ユーザーID（オプション）
            
        Returns:
            List[BehaviorLog]: ログエントリのリスト
        """
        from . import db
        
        query = cls.query.filter(
            cls.timestamp.between(start_time, end_time)
        )
        
        # user_id フィルタ（将来的にユーザー管理が実装された場合）
        if user_id:
            # 現在は session_id でフィルタする仮実装
            query = query.filter(cls.session_id == user_id)
        
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_logs_with_pagination(cls,
                               page: int = 1,
                               per_page: int = 20,
                               filters: Optional[Dict[str, Any]] = None,
                               order_by: str = 'timestamp_desc') -> Tuple[List['BehaviorLog'], int]:
        """ページング付きでログを取得
        
        Args:
            page: ページ番号（1から開始）
            per_page: 1ページあたりの件数
            filters: フィルタ条件の辞書
            order_by: ソート順 (timestamp_asc/timestamp_desc)
            
        Returns:
            Tuple[List[BehaviorLog], int]: (ログリスト, 総件数)
        """
        from . import db
        
        query = cls.query
        
        # フィルタ適用
        if filters:
            if filters.get('start_time'):
                query = query.filter(cls.timestamp >= filters['start_time'])
            
            if filters.get('end_time'):
                query = query.filter(cls.timestamp <= filters['end_time'])
            
            if filters.get('user_id'):
                query = query.filter(cls.session_id == filters['user_id'])
            
            if filters.get('focus_min') is not None:
                query = query.filter(cls.focus_level >= filters['focus_min'])
            
            if filters.get('focus_max') is not None:
                query = query.filter(cls.focus_level <= filters['focus_max'])
            
            if filters.get('smartphone_detected') is not None:
                query = query.filter(cls.smartphone_detected == filters['smartphone_detected'])
            
            if filters.get('presence_status'):
                query = query.filter(cls.presence_status == filters['presence_status'])
        
        # ソート順の適用
        if order_by == 'timestamp_asc':
            query = query.order_by(cls.timestamp.asc())
        else:  # timestamp_desc がデフォルト
            query = query.order_by(cls.timestamp.desc())
        
        # ページング実行
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return paginated.items, paginated.total

    @classmethod 
    def get_optimized_focus_trends(cls,
                                  start_time: datetime,
                                  end_time: datetime,
                                  interval_minutes: int = 30) -> List[Dict[str, Any]]:
        """最適化された集中度トレンド取得（SQLite互換版）
        
        Args:
            start_time: 開始時刻
            end_time: 終了時刻
            interval_minutes: 集計間隔（分）
            
        Returns:
            List[Dict]: 時間間隔ごとの集中度統計
        """
        from sqlalchemy import func, cast, Integer
        from . import db
        
        # SQLite互換の時間グループ化（1時間間隔）
        # strftime関数を使用してSQLite互換に
        query = db.session.query(
            func.strftime('%Y-%m-%d %H:00:00', cls.timestamp).label('time_bucket'),
            func.avg(cls.focus_level).label('avg_focus'),
            func.count(cls.id).label('entry_count'),
            func.sum(cast(cls.smartphone_detected, Integer)).label('smartphone_count')
        ).filter(
            cls.timestamp.between(start_time, end_time),
            cls.focus_level.isnot(None)
        ).group_by('time_bucket').order_by('time_bucket')
        
        results = []
        for row in query.all():
            results.append({
                'timestamp': row.time_bucket,
                'average_focus': float(row.avg_focus or 0),
                'entry_count': row.entry_count,
                'smartphone_usage_rate': (row.smartphone_count / row.entry_count) if row.entry_count > 0 else 0
            })
        
        return results
    
    @classmethod
    def get_performance_metrics(cls, hours: int = 24) -> Dict[str, Any]:
        """システムパフォーマンス指標を取得
        
        Args:
            hours: 監視時間範囲
            
        Returns:
            Dict: パフォーマンス指標
        """
        from datetime import timedelta
        from sqlalchemy import func
        from . import db
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 基本統計
        stats_query = db.session.query(
            func.count(cls.id).label('total_records'),
            func.avg(cls.processing_time).label('avg_processing_time'),
            func.max(cls.processing_time).label('max_processing_time'),
            func.count(cls.focus_level).label('valid_focus_records')
        ).filter(cls.timestamp >= cutoff_time)
        
        stats = stats_query.first()
        
        # 集中度分布
        focus_distribution = db.session.query(
            func.count(cls.id).label('count')
        ).filter(
            cls.timestamp >= cutoff_time,
            cls.focus_level >= 0.7
        ).scalar() or 0
        
        return {
            'total_records': stats.total_records or 0,
            'avg_processing_time_ms': float(stats.avg_processing_time or 0),
            'max_processing_time_ms': float(stats.max_processing_time or 0),
            'data_quality_rate': (stats.valid_focus_records / stats.total_records) if stats.total_records > 0 else 0,
            'high_focus_records': focus_distribution,
            'records_per_hour': (stats.total_records / hours) if hours > 0 else 0
        }
    
    @classmethod
    def cleanup_old_data(cls, days_to_keep: int = 90) -> int:
        """古いデータのクリーンアップ
        
        Args:
            days_to_keep: 保持する日数
            
        Returns:
            int: 削除されたレコード数
        """
        from datetime import timedelta
        from . import db
        
        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 古いレコードを削除
        deleted_count = db.session.query(cls).filter(
            cls.timestamp < cutoff_time
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return deleted_count 