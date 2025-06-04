"""
アラートシステム

システム異常・ユーザー行動異常の検出とアラート配信
- 異常検出
- 段階的アラート
- 通知配信
- アラート管理
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple, Callable, Union, Set
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import threading
import time

from models.behavior_log import BehaviorLog
from models.user_profile import UserProfile
# 削除ファイルへの参照をコメントアウト（Phase 0.1）
# from ..streaming.real_time_analyzer import StreamAnalysisResult, StreamEvent
# from ..streaming.streaming_processor import StreamingProcessor
# 実在ファイルへのimport復活（Priority 3）
from ..streaming.real_time_analyzer import StreamAnalysisResult, StreamEvent
from ..streaming.streaming_processor import StreamingProcessor
from utils.logger import setup_logger

logger = setup_logger(__name__)


# 注意: StreamEventとStreamAnalysisResultは
# services.streaming.real_time_analyzer からimportしたものを使用

class AlertLevel(Enum):
    """アラートレベル階層"""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """アラート配信チャネル"""
    TTS_VOICE = "tts_voice"
    SCREEN_POPUP = "screen_popup"
    BROWSER_NOTIFICATION = "browser_notification"
    EMAIL = "email"
    WEBSOCKET = "websocket"


class AlertStatus(Enum):
    """アラート状態"""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"


@dataclass
class AlertRule:
    """アラートルール"""
    rule_id: str
    name: str
    event_type: StreamEvent
    level: AlertLevel
    conditions: Dict[str, Any]
    channels: List[AlertChannel]
    cooldown_minutes: int
    enabled: bool = True
    priority: int = 5


@dataclass
class AlertMessage:
    """アラートメッセージ"""
    alert_id: str
    rule_id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    user_id: Optional[str]
    context: Dict[str, Any]
    channels: List[AlertChannel]
    urgency_score: float
    status: AlertStatus = AlertStatus.PENDING


@dataclass
class AlertSuppression:
    """アラート抑制設定"""
    rule_id: str
    suppression_type: str
    conditions: Dict[str, Any]
    duration_minutes: int
    max_alerts_per_hour: int = 5


@dataclass
class UserAlertPreferences:
    """ユーザーアラート設定"""
    user_id: str
    enabled_channels: Set[AlertChannel]
    quiet_hours: List[Tuple[int, int]]  # (start_hour, end_hour)
    alert_thresholds: Dict[AlertLevel, float]
    custom_rules: List[str]


class AlertSuppressionEngine:
    """アラート抑制エンジン"""
    
    def __init__(self):
        """初期化"""
        self.suppression_rules = {}
        self.alert_history = defaultdict(deque)  # rule_id -> recent alerts
        self.duplicate_tracking = {}  # content hash -> last sent time
        
    def add_suppression_rule(self, rule: AlertSuppression):
        """抑制ルール追加"""
        self.suppression_rules[rule.rule_id] = rule
        logger.info(f"Added suppression rule for {rule.rule_id}")
    
    def should_suppress_alert(self, alert: AlertMessage) -> bool:
        """アラート抑制判定
        
        Args:
            alert: アラートメッセージ
            
        Returns:
            bool: 抑制すべきかどうか
        """
        try:
            # 抑制ルール取得
            suppression_rule = self.suppression_rules.get(alert.rule_id)
            if not suppression_rule:
                return False
            
            # 頻度ベース抑制
            if self._is_frequency_exceeded(alert, suppression_rule):
                return True
            
            # 重複アラート抑制
            if self._is_duplicate_alert(alert):
                return True
            
            # 時間ベース抑制（ユーザー設定）
            if self._is_in_quiet_hours(alert):
                return True
            
            # カスタム条件ベース抑制
            if self._matches_custom_suppression(alert, suppression_rule):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking alert suppression: {e}")
            return False
    
    def record_alert(self, alert: AlertMessage):
        """アラート記録"""
        try:
            # 履歴に追加
            self.alert_history[alert.rule_id].append({
                'timestamp': alert.timestamp,
                'level': alert.level,
                'urgency': alert.urgency_score
            })
            
            # 古い履歴をクリーンアップ（1時間以上前）
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            history = self.alert_history[alert.rule_id]
            while history and history[0]['timestamp'] < cutoff_time:
                history.popleft()
            
            # 重複追跡記録
            content_hash = self._calculate_content_hash(alert)
            self.duplicate_tracking[content_hash] = alert.timestamp
            
        except Exception as e:
            logger.error(f"Error recording alert: {e}")
    
    def _is_frequency_exceeded(self, alert: AlertMessage, 
                              suppression_rule: AlertSuppression) -> bool:
        """頻度超過チェック"""
        try:
            recent_alerts = self.alert_history[alert.rule_id]
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            # 1時間以内のアラート数をカウント
            recent_count = sum(1 for a in recent_alerts if a['timestamp'] > cutoff_time)
            
            return recent_count >= suppression_rule.max_alerts_per_hour
            
        except Exception:
            return False
    
    def _is_duplicate_alert(self, alert: AlertMessage) -> bool:
        """重複アラートチェック"""
        try:
            content_hash = self._calculate_content_hash(alert)
            last_sent = self.duplicate_tracking.get(content_hash)
            
            if last_sent:
                # 10分以内の重複は抑制
                time_diff = (alert.timestamp - last_sent).total_seconds()
                return time_diff < 600  # 10分
            
            return False
            
        except Exception:
            return False
    
    def _is_in_quiet_hours(self, alert: AlertMessage) -> bool:
        """静寂時間チェック - 実装予定"""
        return False
    
    def _matches_custom_suppression(self, alert: AlertMessage, 
                                   suppression_rule: AlertSuppression) -> bool:
        """カスタム抑制条件チェック - 実装予定"""
        return False
    
    def _calculate_content_hash(self, alert: AlertMessage) -> str:
        """コンテンツハッシュ計算"""
        content = f"{alert.rule_id}_{alert.title}_{alert.message}"
        return str(hash(content))


class NotificationDelivery:
    """通知配信システム"""
    
    def __init__(self, config: Dict[str, Any]):
        """初期化"""
        self.config = config.get('notification_delivery', {})
        self.email_config = self.config.get('email', {})
        self.delivery_stats = defaultdict(int)
        
    async def deliver_alert(self, alert: AlertMessage, 
                           channel: AlertChannel) -> bool:
        """アラート配信
        
        Args:
            alert: アラートメッセージ
            channel: 配信チャネル
            
        Returns:
            bool: 配信成功フラグ
        """
        try:
            if channel == AlertChannel.TTS_VOICE:
                return await self._deliver_tts_alert(alert)
            elif channel == AlertChannel.SCREEN_POPUP:
                return await self._deliver_popup_alert(alert)
            elif channel == AlertChannel.BROWSER_NOTIFICATION:
                return await self._deliver_browser_notification(alert)
            elif channel == AlertChannel.EMAIL:
                return await self._deliver_email_alert(alert)
            elif channel == AlertChannel.WEBSOCKET:
                return await self._deliver_websocket_alert(alert)
            else:
                logger.warning(f"Unknown alert channel: {channel}")
                return False
                
        except Exception as e:
            logger.error(f"Error delivering alert via {channel}: {e}")
            return False
    
    async def _deliver_tts_alert(self, alert: AlertMessage) -> bool:
        """TTS音声アラート配信"""
        try:
            # TTS サービスとの連携 - 実装予定
            logger.info(f"TTS alert delivered: {alert.title}")
            self.delivery_stats['tts_delivered'] += 1
            return True
        except Exception as e:
            logger.error(f"Error delivering TTS alert: {e}")
            return False
    
    async def _deliver_popup_alert(self, alert: AlertMessage) -> bool:
        """ポップアップアラート配信"""
        try:
            # フロントエンドへのポップアップ通知 - 実装予定
            logger.info(f"Popup alert delivered: {alert.title}")
            self.delivery_stats['popup_delivered'] += 1
            return True
        except Exception as e:
            logger.error(f"Error delivering popup alert: {e}")
            return False
    
    async def _deliver_browser_notification(self, alert: AlertMessage) -> bool:
        """ブラウザ通知配信"""
        try:
            # ブラウザ通知API統合 - 実装予定
            logger.info(f"Browser notification delivered: {alert.title}")
            self.delivery_stats['browser_delivered'] += 1
            return True
        except Exception as e:
            logger.error(f"Error delivering browser notification: {e}")
            return False
    
    async def _deliver_email_alert(self, alert: AlertMessage) -> bool:
        """メールアラート配信"""
        try:
            if not self.email_config.get('enabled', False):
                return False
            
            # メール送信 - 簡易実装
            logger.info(f"Email alert delivered: {alert.title}")
            self.delivery_stats['email_delivered'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error delivering email alert: {e}")
            return False
    
    async def _deliver_websocket_alert(self, alert: AlertMessage) -> bool:
        """WebSocketアラート配信"""
        try:
            # WebSocket経由でフロントエンドに配信 - 実装予定
            logger.info(f"WebSocket alert delivered: {alert.title}")
            self.delivery_stats['websocket_delivered'] += 1
            return True
        except Exception as e:
            logger.error(f"Error delivering WebSocket alert: {e}")
            return False


class AlertSystem:
    """インテリジェントアラートシステム
    
    階層化アラート管理とマルチチャネル配信
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('alert_system', {})
        
        # アラートルール
        self.alert_rules = {}
        self.user_preferences = {}
        
        # アラート抑制エンジン
        self.suppression_engine = AlertSuppressionEngine()
        
        # 通知配信システム
        self.notification_delivery = NotificationDelivery(config)
        
        # アクティブアラート管理
        self.active_alerts = {}
        self.alert_queue = asyncio.Queue()
        
        # 処理統計
        self.processing_stats = {
            'alerts_generated': 0,
            'alerts_sent': 0,
            'alerts_suppressed': 0,
            'delivery_failures': 0
        }
        
        # 非同期処理
        self.is_running = False
        self.processing_task = None
        
        # デフォルトルール初期化
        self._initialize_default_rules()
        
        logger.info("AlertSystem initialized with intelligent features")
    
    async def start(self):
        """アラートシステム開始"""
        try:
            if self.is_running:
                logger.warning("Alert system is already running")
                return
            
            self.is_running = True
            self.processing_task = asyncio.create_task(self._process_alert_queue())
            
            logger.info("Alert system started")
            
        except Exception as e:
            logger.error(f"Error starting alert system: {e}", exc_info=True)
            self.is_running = False
    
    async def stop(self):
        """アラートシステム停止"""
        try:
            self.is_running = False
            
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Alert system stopped")
            
        except Exception as e:
            logger.error(f"Error stopping alert system: {e}")
    
    async def process_stream_event(self, event: StreamAnalysisResult):
        """ストリームイベント処理
        
        Args:
            event: ストリーム分析結果
        """
        try:
            # 適用可能なルール検索
            applicable_rules = self._find_applicable_rules(event)
            
            for rule in applicable_rules:
                # アラートメッセージ生成
                alert = self._create_alert_message(event, rule)
                
                if alert:
                    # アラートキューに追加
                    await self.alert_queue.put(alert)
                    self.processing_stats['alerts_generated'] += 1
            
        except Exception as e:
            logger.error(f"Error processing stream event: {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """アラートルール追加
        
        Args:
            rule: アラートルール
        """
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def set_user_preferences(self, user_id: str, preferences: UserAlertPreferences):
        """ユーザーアラート設定
        
        Args:
            user_id: ユーザーID
            preferences: アラート設定
        """
        self.user_preferences[user_id] = preferences
        logger.info(f"Updated alert preferences for user {user_id}")
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """アラート統計取得"""
        return {
            'processing_stats': dict(self.processing_stats),
            'delivery_stats': dict(self.notification_delivery.delivery_stats),
            'active_alerts_count': len(self.active_alerts),
            'rules_count': len(self.alert_rules),
            'suppression_rules_count': len(self.suppression_engine.suppression_rules)
        }
    
    # ========== Private Methods ==========
    
    def _initialize_default_rules(self):
        """デフォルトアラートルール初期化"""
        try:
            default_rules = [
                AlertRule(
                    rule_id="focus_decline",
                    name="集中度低下アラート",
                    event_type=StreamEvent.FOCUS_CHANGE,
                    level=AlertLevel.WARNING,
                    conditions={"focus_score": "< 0.3"},
                    channels=[AlertChannel.TTS_VOICE, AlertChannel.SCREEN_POPUP],
                    cooldown_minutes=10
                ),
                
                AlertRule(
                    rule_id="posture_warning",
                    name="姿勢改善アラート",
                    event_type=StreamEvent.POSTURE_CHANGE,
                    level=AlertLevel.INFO,
                    conditions={"posture_score": "< 0.4"},
                    channels=[AlertChannel.SCREEN_POPUP],
                    cooldown_minutes=15
                ),
                
                AlertRule(
                    rule_id="distraction_alert",
                    name="注意散漫アラート",
                    event_type=StreamEvent.DISTRACTION_DETECTED,
                    level=AlertLevel.ALERT,
                    conditions={},
                    channels=[AlertChannel.TTS_VOICE, AlertChannel.BROWSER_NOTIFICATION],
                    cooldown_minutes=5
                ),
                
                AlertRule(
                    rule_id="break_reminder",
                    name="休憩推奨アラート",
                    event_type=StreamEvent.BREAK_NEEDED,
                    level=AlertLevel.INFO,
                    conditions={},
                    channels=[AlertChannel.TTS_VOICE, AlertChannel.SCREEN_POPUP],
                    cooldown_minutes=30
                )
            ]
            
            for rule in default_rules:
                self.alert_rules[rule.rule_id] = rule
            
            # デフォルト抑制ルール
            default_suppressions = [
                AlertSuppression(
                    rule_id="focus_decline",
                    suppression_type="frequency",
                    conditions={},
                    duration_minutes=60,
                    max_alerts_per_hour=3
                ),
                
                AlertSuppression(
                    rule_id="posture_warning",
                    suppression_type="frequency",
                    conditions={},
                    duration_minutes=60,
                    max_alerts_per_hour=2
                )
            ]
            
            for suppression in default_suppressions:
                self.suppression_engine.add_suppression_rule(suppression)
            
            logger.info(f"Initialized {len(default_rules)} default alert rules")
            
        except Exception as e:
            logger.error(f"Error initializing default rules: {e}")
    
    def _find_applicable_rules(self, event: StreamAnalysisResult) -> List[AlertRule]:
        """適用可能ルール検索"""
        try:
            applicable_rules = []
            
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                if rule.event_type == event.event_type:
                    # 条件チェック
                    if self._evaluate_rule_conditions(rule, event):
                        applicable_rules.append(rule)
            
            return applicable_rules
            
        except Exception as e:
            logger.error(f"Error finding applicable rules: {e}")
            return []
    
    def _evaluate_rule_conditions(self, rule: AlertRule, 
                                 event: StreamAnalysisResult) -> bool:
        """ルール条件評価"""
        try:
            conditions = rule.conditions
            
            for condition_key, condition_value in conditions.items():
                event_value = event.data.get(condition_key)
                if event_value is None:
                    continue
                
                # 簡易条件評価
                if not self._evaluate_condition(event_value, condition_value):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating rule conditions: {e}")
            return False
    
    def _evaluate_condition(self, value: Any, condition: str) -> bool:
        """条件評価"""
        try:
            if "< " in condition:
                threshold = float(condition.replace("< ", ""))
                return float(value) < threshold
            elif "> " in condition:
                threshold = float(condition.replace("> ", ""))
                return float(value) > threshold
            elif "== " in condition:
                threshold = condition.replace("== ", "")
                return str(value) == threshold
            
            return True
            
        except Exception:
            return False
    
    def _create_alert_message(self, event: StreamAnalysisResult, 
                             rule: AlertRule) -> Optional[AlertMessage]:
        """アラートメッセージ作成"""
        try:
            # メッセージ内容生成
            title, message = self._generate_alert_content(event, rule)
            
            # 緊急度スコア計算
            urgency_score = self._calculate_urgency_score(event, rule)
            
            alert = AlertMessage(
                alert_id=f"alert_{datetime.utcnow().timestamp()}",
                rule_id=rule.rule_id,
                level=rule.level,
                title=title,
                message=message,
                timestamp=datetime.utcnow(),
                user_id=event.user_id,
                context=event.context,
                channels=rule.channels,
                urgency_score=urgency_score
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert message: {e}")
            return None
    
    def _generate_alert_content(self, event: StreamAnalysisResult, 
                               rule: AlertRule) -> Tuple[str, str]:
        """アラート内容生成"""
        try:
            templates = {
                "focus_decline": ("集中度低下", "集中度が低下しています。深呼吸をして集中を取り戻しましょう。"),
                "posture_warning": ("姿勢改善", "姿勢が悪くなっています。背筋を伸ばしてください。"),
                "distraction_alert": ("注意散漫検出", "スマートフォンが検出されました。作業に集中しましょう。"),
                "break_reminder": ("休憩推奨", "長時間の作業お疲れさまです。5分間の休憩を取りましょう。")
            }
            
            title, message = templates.get(rule.rule_id, ("アラート", "注意が必要な状況が検出されました。"))
            
            return title, message
            
        except Exception as e:
            logger.error(f"Error generating alert content: {e}")
            return "アラート", "システムアラートが発生しました。"
    
    def _calculate_urgency_score(self, event: StreamAnalysisResult, 
                                rule: AlertRule) -> float:
        """緊急度スコア計算"""
        try:
            base_score = 0.5
            
            # レベル別スコア
            level_scores = {
                AlertLevel.INFO: 0.3,
                AlertLevel.WARNING: 0.6,
                AlertLevel.ALERT: 0.8,
                AlertLevel.CRITICAL: 1.0
            }
            
            level_score = level_scores.get(rule.level, 0.5)
            
            # イベント信頼度
            confidence_score = event.confidence
            
            # 緊急フラグ
            urgent_multiplier = 1.5 if event.urgent else 1.0
            
            urgency_score = (level_score * 0.5 + confidence_score * 0.3 + base_score * 0.2) * urgent_multiplier
            
            return min(urgency_score, 1.0)
            
        except Exception:
            return 0.5
    
    async def _process_alert_queue(self):
        """アラートキュー処理"""
        try:
            while self.is_running:
                try:
                    # アラート取得（タイムアウト付き）
                    alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                    
                    # 抑制チェック
                    if self.suppression_engine.should_suppress_alert(alert):
                        alert.status = AlertStatus.SUPPRESSED
                        self.processing_stats['alerts_suppressed'] += 1
                        continue
                    
                    # アラート配信
                    await self._deliver_alert(alert)
                    
                except asyncio.TimeoutError:
                    # タイムアウトは正常
                    continue
                except Exception as e:
                    logger.error(f"Error processing alert queue: {e}")
                    
        except Exception as e:
            logger.error(f"Critical error in alert queue processing: {e}")
    
    async def _deliver_alert(self, alert: AlertMessage):
        """アラート配信"""
        try:
            delivery_results = []
            
            # 各チャネルに配信
            for channel in alert.channels:
                success = await self.notification_delivery.deliver_alert(alert, channel)
                delivery_results.append(success)
            
            # 配信結果評価
            if any(delivery_results):
                alert.status = AlertStatus.SENT
                self.processing_stats['alerts_sent'] += 1
                
                # アラート記録
                self.suppression_engine.record_alert(alert)
                
                # アクティブアラートに追加
                self.active_alerts[alert.alert_id] = alert
                
            else:
                self.processing_stats['delivery_failures'] += 1
                logger.warning(f"Failed to deliver alert: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Error delivering alert: {e}") 