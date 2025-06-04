import time
from datetime import datetime, timedelta
from typing import Set, Optional, Dict, Any
from utils.logger import setup_logger
from services.communication.alert_manager import AlertManager
from services.automation.schedule_manager import ScheduleManager
from web.websocket import socketio
from utils.exceptions import (
    ScheduleError, ScheduleExecutionError, NetworkError,
    AlertError, wrap_exception
)

logger = setup_logger(__name__)


class ScheduleChecker:
    """
    スケジュール管理専門クラス
    - スケジュールの定期チェック
    - スケジュール実行管理
    - 通知送信
    """
    
    def __init__(self,
                 schedule_manager: Optional[ScheduleManager],
                 alert_manager: Optional[AlertManager],
                 check_interval: int = 10):
        """
        初期化
        
        Args:
            schedule_manager: スケジュール管理インスタンス
            alert_manager: アラート管理インスタンス  
            check_interval: チェック間隔（秒）
        """
        self.schedule_manager = schedule_manager
        self.alert_manager = alert_manager
        self.check_interval = check_interval
        
        # スケジュールチェック用の変数
        self.last_schedule_check_time = 0
        self.executed_schedules: Set[str] = set()  # 実行済みスケジュールを記録
        
        logger.info(f"ScheduleChecker initialized with check_interval={check_interval}s.")

    def check_schedules(self) -> bool:
        """
        現在時刻に実行すべきスケジュールがあるかチェックし、
        該当するスケジュールがあれば通知を送信する
        
        Returns:
            bool: 通知を送信したかどうか
        """
        if not self.schedule_manager:
            return False  # スケジュールマネージャーが設定されていない場合は何もしない
        
        # 現在時刻を取得（HH:MM形式）
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_minute = now.strftime("%H:%M")  # 分単位で記録
        
        # 同じ分に既にチェック済みなら処理をスキップ
        if current_minute in self.executed_schedules:
            return False
        
        # スケジュール一覧を取得
        schedules = self.schedule_manager.get_schedules()
        notification_sent = False
        
        for schedule in schedules:
            schedule_time = schedule.get("time")
            
            # 時刻が一致するスケジュールを探す
            if schedule_time == current_time:
                logger.info(f"Schedule triggered: {schedule}")
                
                # アラート音を再生（AlertManagerを使用）
                if self.alert_manager:
                    try:
                        self.alert_manager.alert_service.trigger_alert(
                            f"スケジュール通知: {schedule.get('content')}"
                        )
                    except Exception as e:
                        alert_error = wrap_exception(
                            e, AlertError,
                            "Error triggering schedule alert",
                            details={
                                'schedule_content': schedule.get('content'),
                                'schedule_time': schedule_time,
                                'alert_manager_available': self.alert_manager is not None
                            }
                        )
                        logger.error(f"Schedule alert error: {alert_error.to_dict()}")
                
                # WebSocketで通知を送信
                notification_data = {
                    "type": "schedule_alert",
                    "content": schedule.get("content"),
                    "time": schedule_time
                }
                
                try:
                    socketio.emit("schedule_alert", notification_data)
                    logger.info(f"Schedule notification sent via WebSocket: {notification_data}")
                    notification_sent = True
                except Exception as e:
                    websocket_error = wrap_exception(
                        e, NetworkError,
                        "Error sending schedule notification via WebSocket",
                        details={
                            'notification_data': notification_data,
                            'socketio_available': socketio is not None
                        }
                    )
                    logger.error(f"Schedule WebSocket notification error: {websocket_error.to_dict()}")
        
        # 実行済みとして記録
        if notification_sent:
            self.executed_schedules.add(current_minute)
            
            # 翌日に備えて、セットのサイズが大きくなりすぎないように古い記録をクリア
            if len(self.executed_schedules) > 100:
                self.executed_schedules.clear()
        
        return notification_sent

    def should_check_now(self) -> bool:
        """
        現在スケジュールチェックを実行すべき時刻かどうかを判定
        
        Returns:
            bool: チェックすべき時刻かどうか
        """
        current_time = time.time()
        return (current_time - self.last_schedule_check_time) >= self.check_interval

    def update_last_check_time(self) -> None:
        """
        最後のチェック時刻を現在時刻に更新
        """
        self.last_schedule_check_time = time.time()

    def check_if_needed(self) -> bool:
        """
        必要に応じてスケジュールチェックを実行
        
        Returns:
            bool: チェックを実行し、通知を送信したかどうか
        """
        if self.should_check_now():
            result = self.check_schedules()
            self.update_last_check_time()
            return result
        return False

    def get_status(self) -> dict:
        """
        スケジュールチェッカーの状態情報を取得
        
        Returns:
            dict: 状態情報
        """
        return {
            'has_schedule_manager': self.schedule_manager is not None,
            'has_alert_manager': self.alert_manager is not None,
            'check_interval': self.check_interval,
            'last_check_time': self.last_schedule_check_time,
            'executed_schedules_count': len(self.executed_schedules),
            'time_until_next_check': max(0, self.check_interval - (time.time() - self.last_schedule_check_time))
        }

    def clear_executed_schedules(self) -> None:
        """
        実行済みスケジュール記録をクリア
        """
        self.executed_schedules.clear()
        logger.info("Executed schedules cleared.") 