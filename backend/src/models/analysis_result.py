"""
Analysis Result Model

LLM による行動分析結果の保存モデル
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, DateTime, Float, JSON, Text, Boolean, Index
from .base_model import BaseModel


class AnalysisResult(BaseModel):
    """分析結果モデル
    
    ローカルLLMによる行動傾向分析の結果を保存
    - 行動パターン
    - トレンド分析
    - 生成されたアドバイス
    - 音声アドバイス情報
    """
    
    __tablename__ = 'analysis_results'
    
    # 分析対象期間
    analysis_start_time = Column(DateTime, nullable=False, index=True, comment="分析対象開始時刻")
    analysis_end_time = Column(DateTime, nullable=False, index=True, comment="分析対象終了時刻")
    analysis_type = Column(String(50), nullable=False, comment="分析種別 (hourly/daily/weekly/session)")
    
    # セッション・ユーザー情報
    session_id = Column(String(50), nullable=True, index=True, comment="対象セッションID")
    user_id = Column(String(50), nullable=True, index=True, comment="ユーザーID")
    
    # 行動統計データ
    total_entries = Column(Float, nullable=False, default=0, comment="総データエントリ数")
    focus_statistics = Column(JSON, nullable=True, comment="集中度統計 (平均、最大、最小)")
    presence_statistics = Column(JSON, nullable=True, comment="在席統計")
    smartphone_usage = Column(JSON, nullable=True, comment="スマートフォン使用統計")
    posture_statistics = Column(JSON, nullable=True, comment="姿勢統計")
    
    # 行動パターン分析
    behavior_patterns = Column(JSON, nullable=True, comment="検出された行動パターン")
    focus_patterns = Column(JSON, nullable=True, comment="集中度パターン")
    break_patterns = Column(JSON, nullable=True, comment="休憩パターン")
    productivity_score = Column(Float, nullable=True, comment="生産性スコア (0.0-1.0)")
    
    # トレンド分析
    trend_analysis = Column(JSON, nullable=True, comment="時系列トレンド分析")
    comparison_data = Column(JSON, nullable=True, comment="過去データとの比較")
    improvement_areas = Column(JSON, nullable=True, comment="改善領域の特定")
    
    # LLM生成アドバイス
    llm_insights = Column(Text, nullable=True, comment="LLMによる洞察")
    recommendations = Column(JSON, nullable=True, comment="推奨事項リスト")
    advice_text = Column(Text, nullable=True, comment="音声用アドバイステキスト")
    advice_priority = Column(String(20), nullable=True, comment="アドバイス優先度 (high/medium/low)")
    
    # 音声アドバイス情報
    voice_advice_generated = Column(Boolean, default=False, comment="音声アドバイス生成フラグ")
    voice_file_path = Column(String(500), nullable=True, comment="生成音声ファイルパス")
    voice_emotion = Column(String(50), nullable=True, comment="音声感情 (encouragement/reminder/alert)")
    voice_duration = Column(Float, nullable=True, comment="音声再生時間（秒）")
    
    # 実行状況
    advice_delivered = Column(Boolean, default=False, comment="アドバイス配信完了フラグ")
    delivery_timestamp = Column(DateTime, nullable=True, comment="配信実行時刻")
    user_feedback = Column(JSON, nullable=True, comment="ユーザーフィードバック")
    
    # パフォーマンス情報
    analysis_duration = Column(Float, nullable=True, comment="分析処理時間（秒）")
    llm_model_used = Column(String(100), nullable=True, comment="使用LLMモデル")
    confidence_score = Column(Float, nullable=True, comment="分析信頼度スコア (0.0-1.0)")
    
    # 複合インデックス
    __table_args__ = (
        Index('idx_analysis_period', 'analysis_start_time', 'analysis_end_time'),
        Index('idx_analysis_type_user', 'analysis_type', 'user_id'),
        Index('idx_session_analysis', 'session_id', 'analysis_type'),
        Index('idx_advice_priority', 'advice_priority', 'advice_delivered'),
    )
    
    @classmethod
    def create_analysis(cls,
                       analysis_start_time: datetime,
                       analysis_end_time: datetime,
                       analysis_type: str,
                       behavior_statistics: Dict[str, Any],
                       llm_insights: str,
                       recommendations: List[Dict],
                       session_id: Optional[str] = None,
                       user_id: Optional[str] = None,
                       **kwargs) -> 'AnalysisResult':
        """分析結果エントリを作成
        
        Args:
            analysis_start_time: 分析対象開始時刻
            analysis_end_time: 分析対象終了時刻
            analysis_type: 分析種別
            behavior_statistics: 行動統計データ
            llm_insights: LLM洞察
            recommendations: 推奨事項
            session_id: セッションID
            user_id: ユーザーID
            **kwargs: 追加フィールド
            
        Returns:
            AnalysisResult: 作成された分析結果エントリ
        """
        # 推奨事項から音声アドバイステキストを生成
        advice_text, advice_priority = cls._generate_advice_text(recommendations)
        
        # 生産性スコアの計算
        productivity_score = cls._calculate_productivity_score(behavior_statistics)
        
        return cls(
            analysis_start_time=analysis_start_time,
            analysis_end_time=analysis_end_time,
            analysis_type=analysis_type,
            session_id=session_id,
            user_id=user_id,
            focus_statistics=behavior_statistics.get('focus_statistics'),
            presence_statistics=behavior_statistics.get('presence_statistics'),
            smartphone_usage=behavior_statistics.get('smartphone_usage'),
            posture_statistics=behavior_statistics.get('posture_statistics'),
            llm_insights=llm_insights,
            recommendations=recommendations,
            advice_text=advice_text,
            advice_priority=advice_priority,
            productivity_score=productivity_score,
            **kwargs
        )
    
    @staticmethod
    def _generate_advice_text(recommendations: List[Dict]) -> tuple[str, str]:
        """推奨事項から音声アドバイステキストを生成
        
        Args:
            recommendations: 推奨事項リスト
            
        Returns:
            tuple: (アドバイステキスト, 優先度)
        """
        if not recommendations:
            return "今日もお疲れ様でした。", "low"
        
        # 最も優先度の高い推奨事項を選択
        high_priority = [r for r in recommendations if r.get('priority') == 'high']
        medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
        
        if high_priority:
            advice = high_priority[0].get('message', '重要な改善点があります。')
            return advice, 'high'
        elif medium_priority:
            advice = medium_priority[0].get('message', '改善の余地があります。')
            return advice, 'medium'
        else:
            advice = recommendations[0].get('message', '継続して頑張りましょう。')
            return advice, 'low'
    
    @staticmethod
    def _calculate_productivity_score(behavior_statistics: Dict[str, Any]) -> float:
        """生産性スコアを計算
        
        Args:
            behavior_statistics: 行動統計データ
            
        Returns:
            float: 生産性スコア (0.0-1.0)
        """
        focus_stats = behavior_statistics.get('focus_statistics', {})
        smartphone_usage = behavior_statistics.get('smartphone_usage', {})
        presence_stats = behavior_statistics.get('presence_statistics', {})
        
        # 基本スコア要素
        focus_score = focus_stats.get('average_focus', 0.5)
        presence_rate = presence_stats.get('presence_rate', 0.5)
        smartphone_penalty = min(0.3, smartphone_usage.get('usage_rate', 0) * 0.5)
        
        # 生産性スコア計算
        productivity = (focus_score * 0.5 + presence_rate * 0.3) - smartphone_penalty
        return max(0.0, min(1.0, productivity))
    
    def get_summary(self) -> Dict[str, Any]:
        """分析結果のサマリーを取得
        
        Returns:
            dict: サマリーデータ
        """
        duration_hours = (self.analysis_end_time - self.analysis_start_time).total_seconds() / 3600
        
        return {
            'analysis_period': {
                'start': self.analysis_start_time.isoformat(),
                'end': self.analysis_end_time.isoformat(),
                'duration_hours': round(duration_hours, 2)
            },
            'analysis_type': self.analysis_type,
            'productivity_score': self.productivity_score,
            'total_entries': self.total_entries,
            'key_insights': self.llm_insights[:200] if self.llm_insights else None,
            'recommendation_count': len(self.recommendations) if self.recommendations else 0,
            'advice_priority': self.advice_priority,
            'voice_generated': self.voice_advice_generated,
            'confidence_score': self.confidence_score
        }
    
    def mark_delivered(self) -> None:
        """アドバイス配信完了をマーク"""
        self.advice_delivered = True
        self.delivery_timestamp = datetime.utcnow()
        self.save()
    
    def add_user_feedback(self, feedback: Dict[str, Any]) -> None:
        """ユーザーフィードバックを追加
        
        Args:
            feedback: フィードバックデータ
        """
        if self.user_feedback is None:
            self.user_feedback = []
        
        feedback_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'feedback': feedback
        }
        
        self.user_feedback.append(feedback_entry)
        self.save()
    
    @classmethod
    def get_recent_analyses(cls,
                          hours: int = 168,  # 1週間
                          analysis_type: Optional[str] = None,
                          user_id: Optional[str] = None) -> List['AnalysisResult']:
        """最近の分析結果を取得
        
        Args:
            hours: 取得する時間範囲（時間）
            analysis_type: 分析種別でフィルタ
            user_id: ユーザーIDでフィルタ
            
        Returns:
            List[AnalysisResult]: 分析結果のリスト
        """
        from datetime import timedelta
        from . import db
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(cls.created_at >= cutoff_time)
        
        if analysis_type:
            query = query.filter(cls.analysis_type == analysis_type)
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_productivity_trend(cls,
                             days: int = 30,
                             user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """生産性トレンドを取得
        
        Args:
            days: 取得する日数
            user_id: ユーザーID
            
        Returns:
            List[Dict]: 日別生産性データ
        """
        from datetime import timedelta, date
        from sqlalchemy import func
        from . import db
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = db.session.query(
            func.date(cls.analysis_start_time).label('date'),
            func.avg(cls.productivity_score).label('avg_productivity'),
            func.count(cls.id).label('analysis_count')
        ).filter(
            func.date(cls.analysis_start_time).between(start_date, end_date),
            cls.analysis_type == 'daily',
            cls.productivity_score.isnot(None)
        )
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        results = query.group_by(func.date(cls.analysis_start_time)).all()
        
        return [
            {
                'date': result.date.isoformat(),
                'productivity_score': float(result.avg_productivity),
                'analysis_count': result.analysis_count
            }
            for result in results
        ] 