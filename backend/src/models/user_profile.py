"""
User Profile Model

ユーザー設定・音声サンプル管理モデル
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, DateTime, Float, JSON, Text, Boolean, Integer
from .base import BaseModel


class UserProfile(BaseModel):
    """ユーザープロファイルモデル
    
    ユーザー個人の設定と音声クローン用サンプルを管理
    - 音声サンプルファイルパス
    - 個人設定（音量、通知頻度等）
    - 学習スタイル・習慣
    """
    
    __tablename__ = 'user_profiles'
    
    # ユーザー基本情報
    user_id = Column(String(50), nullable=False, unique=True, index=True, comment="ユーザーID")
    user_name = Column(String(100), nullable=True, comment="ユーザー名")
    email = Column(String(200), nullable=True, comment="メールアドレス")
    
    # 音声クローン設定
    voice_sample_path = Column(String(500), nullable=True, comment="音声サンプルファイルパス")
    voice_sample_duration = Column(Float, nullable=True, comment="音声サンプル長さ（秒）")
    voice_sample_quality = Column(Float, nullable=True, comment="音声サンプル品質スコア (0.0-1.0)")
    voice_clone_enabled = Column(Boolean, default=False, comment="音声クローン有効フラグ")
    voice_clone_last_updated = Column(DateTime, nullable=True, comment="音声クローン最終更新日時")
    
    # 音声アドバイス設定
    voice_advice_enabled = Column(Boolean, default=True, comment="音声アドバイス有効フラグ")
    voice_volume = Column(Float, default=0.7, comment="音声音量 (0.0-1.0)")
    voice_speed = Column(Float, default=1.0, comment="音声再生速度 (0.5-2.0)")
    
    # 通知・アドバイス設定
    advice_frequency = Column(String(20), default='normal', comment="アドバイス頻度 (low/normal/high)")
    notification_enabled = Column(Boolean, default=True, comment="通知有効フラグ")
    urgent_alerts_only = Column(Boolean, default=False, comment="緊急アラートのみフラグ")
    quiet_hours_start = Column(String(5), nullable=True, comment="静寂時間開始 (HH:MM)")
    quiet_hours_end = Column(String(5), nullable=True, comment="静寂時間終了 (HH:MM)")
    
    # 学習・作業スタイル設定
    work_style = Column(String(50), nullable=True, comment="作業スタイル (focused/flexible/creative)")
    preferred_break_interval = Column(Integer, default=50, comment="希望休憩間隔（分）")
    break_reminder_enabled = Column(Boolean, default=True, comment="休憩リマインダー有効フラグ")
    focus_goal_duration = Column(Integer, default=120, comment="集中目標時間（分）")
    
    # パーソナライゼーション設定
    personality_type = Column(String(50), nullable=True, comment="パーソナリティタイプ")
    motivation_style = Column(String(50), default='encouraging', comment="モチベーションスタイル")
    preferred_advice_tone = Column(String(50), default='friendly', comment="希望アドバイストーン")
    
    # 学習履歴・統計
    total_sessions = Column(Integer, default=0, comment="総セッション数")
    total_focus_hours = Column(Float, default=0.0, comment="総集中時間（時間）")
    average_session_duration = Column(Float, nullable=True, comment="平均セッション時間（分）")
    best_focus_score = Column(Float, nullable=True, comment="最高集中度スコア")
    current_streak = Column(Integer, default=0, comment="現在の連続記録（日）")
    longest_streak = Column(Integer, default=0, comment="最長連続記録（日）")
    
    # 目標・チャレンジ設定
    daily_focus_goal = Column(Integer, default=240, comment="1日の集中目標（分）")
    weekly_focus_goal = Column(Integer, default=1680, comment="週の集中目標（分）")
    current_challenge = Column(JSON, nullable=True, comment="現在のチャレンジ設定")
    achievements = Column(JSON, nullable=True, comment="達成したアチーブメント")
    
    # 健康・ウェルビーイング設定
    posture_monitoring = Column(Boolean, default=True, comment="姿勢監視有効フラグ")
    eye_strain_alerts = Column(Boolean, default=True, comment="眼精疲労アラート有効フラグ")
    movement_reminders = Column(Boolean, default=True, comment="動作リマインダー有効フラグ")
    
    # 詳細設定・メタデータ
    custom_settings = Column(JSON, nullable=True, comment="カスタム設定JSON")
    preferences = Column(JSON, nullable=True, comment="その他の個人設定")
    notes = Column(Text, nullable=True, comment="ユーザーメモ")
    
    # 最終アクティビティ
    last_login = Column(DateTime, nullable=True, comment="最終ログイン日時")
    last_session_id = Column(String(50), nullable=True, comment="最後のセッションID")
    
    @classmethod
    def create_profile(cls,
                      user_id: str,
                      user_name: Optional[str] = None,
                      **kwargs) -> 'UserProfile':
        """ユーザープロファイルを作成
        
        Args:
            user_id: ユーザーID
            user_name: ユーザー名
            **kwargs: 追加設定
            
        Returns:
            UserProfile: 作成されたプロファイル
        """
        return cls(
            user_id=user_id,
            user_name=user_name,
            achievements=[],
            **kwargs
        )
    
    def update_voice_sample(self, 
                           file_path: str, 
                           duration: float, 
                           quality_score: float) -> None:
        """音声サンプルを更新
        
        Args:
            file_path: 音声ファイルパス
            duration: 音声の長さ（秒）
            quality_score: 品質スコア (0.0-1.0)
        """
        self.voice_sample_path = file_path
        self.voice_sample_duration = duration
        self.voice_sample_quality = quality_score
        self.voice_clone_last_updated = datetime.utcnow()
        
        # 品質スコアが基準以上なら音声クローンを有効化
        if quality_score >= 0.7:
            self.voice_clone_enabled = True
        
        self.save()
    
    def update_session_stats(self, 
                           session_duration: float, 
                           focus_score: float,
                           session_id: str) -> None:
        """セッション統計を更新
        
        Args:
            session_duration: セッション時間（分）
            focus_score: 集中度スコア (0.0-1.0)
            session_id: セッションID
        """
        self.total_sessions += 1
        self.total_focus_hours += session_duration / 60.0
        self.last_session_id = session_id
        
        # 平均セッション時間の更新
        self.average_session_duration = (self.total_focus_hours * 60) / self.total_sessions
        
        # 最高集中度スコアの更新
        if self.best_focus_score is None or focus_score > self.best_focus_score:
            self.best_focus_score = focus_score
        
        self.save()
    
    def update_streak(self, is_goal_achieved: bool) -> None:
        """連続記録を更新
        
        Args:
            is_goal_achieved: 今日の目標達成フラグ
        """
        if is_goal_achieved:
            self.current_streak += 1
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
        else:
            self.current_streak = 0
        
        self.save()
    
    def add_achievement(self, achievement: Dict[str, Any]) -> None:
        """アチーブメントを追加
        
        Args:
            achievement: アチーブメントデータ
        """
        if self.achievements is None:
            self.achievements = []
        
        achievement_entry = {
            'id': achievement.get('id'),
            'name': achievement.get('name'),
            'description': achievement.get('description'),
            'earned_at': datetime.utcnow().isoformat(),
            'type': achievement.get('type', 'general')
        }
        
        # 重複チェック
        existing_ids = [a.get('id') for a in self.achievements]
        if achievement_entry['id'] not in existing_ids:
            self.achievements.append(achievement_entry)
            self.save()
    
    def get_voice_settings(self) -> Dict[str, Any]:
        """音声設定を取得
        
        Returns:
            dict: 音声関連設定
        """
        return {
            'voice_clone_enabled': self.voice_clone_enabled,
            'voice_sample_available': bool(self.voice_sample_path),
            'voice_sample_quality': self.voice_sample_quality,
            'voice_advice_enabled': self.voice_advice_enabled,
            'voice_volume': self.voice_volume,
            'voice_speed': self.voice_speed,
            'notification_enabled': self.notification_enabled,
            'advice_frequency': self.advice_frequency
        }
    
    def get_personalization_data(self) -> Dict[str, Any]:
        """パーソナライゼーション用データを取得
        
        Returns:
            dict: パーソナライゼーションデータ
        """
        return {
            'user_id': self.user_id,
            'work_style': self.work_style,
            'personality_type': self.personality_type,
            'motivation_style': self.motivation_style,
            'preferred_advice_tone': self.preferred_advice_tone,
            'preferred_break_interval': self.preferred_break_interval,
            'focus_goal_duration': self.focus_goal_duration,
            'average_session_duration': self.average_session_duration,
            'best_focus_score': self.best_focus_score,
            'current_streak': self.current_streak,
            'achievements_count': len(self.achievements) if self.achievements else 0
        }
    
    def is_quiet_hours(self) -> bool:
        """現在が静寂時間内かチェック
        
        Returns:
            bool: 静寂時間内の場合True
        """
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        from datetime import time
        now_time = datetime.now().time()
        start_time = time.fromisoformat(self.quiet_hours_start)
        end_time = time.fromisoformat(self.quiet_hours_end)
        
        if start_time <= end_time:
            return start_time <= now_time <= end_time
        else:
            # 日を跨ぐ場合
            return now_time >= start_time or now_time <= end_time
    
    def should_send_advice(self, advice_priority: str) -> bool:
        """アドバイス送信判定
        
        Args:
            advice_priority: アドバイス優先度 (high/medium/low)
            
        Returns:
            bool: 送信する場合True
        """
        if not self.voice_advice_enabled:
            return False
        
        if self.is_quiet_hours():
            return advice_priority == 'high' and not self.urgent_alerts_only
        
        if self.advice_frequency == 'low' and advice_priority == 'low':
            return False
        
        return True
    
    @classmethod
    def get_by_user_id(cls, user_id: str) -> Optional['UserProfile']:
        """ユーザーIDでプロファイル取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            UserProfile or None: プロファイル
        """
        return cls.query.filter_by(user_id=user_id).first()
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """ダッシュボード用サマリーを取得
        
        Returns:
            dict: サマリーデータ
        """
        return {
            'user_name': self.user_name,
            'total_sessions': self.total_sessions,
            'total_focus_hours': round(self.total_focus_hours, 1),
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'best_focus_score': self.best_focus_score,
            'voice_clone_enabled': self.voice_clone_enabled,
            'achievements_count': len(self.achievements) if self.achievements else 0,
            'daily_goal': self.daily_focus_goal,
            'weekly_goal': self.weekly_focus_goal
        } 