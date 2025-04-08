import json
import os
import uuid
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger
from utils.config_manager import ConfigManager

logger = setup_logger(__name__)

class ScheduleManager:
    """
    スケジュール通知を管理するクラス。
    指定された時刻に通知を行うためのスケジュールを保存・管理します。
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        # スケジュールの保存先ディレクトリ（configディレクトリ内）
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.schedules_file = os.path.join(self.config_dir, 'schedules.json')
        self.schedules: List[Dict[str, str]] = []
        # 起動時にスケジュールを読み込む
        self.load_schedules()
        logger.info("ScheduleManager initialized.")

    def load_schedules(self) -> bool:
        """
        スケジュールをJSONファイルから読み込む
        Returns:
            bool: 読み込みが成功したかどうか
        """
        if not os.path.exists(self.schedules_file):
            # ファイルが存在しない場合は空のスケジュールリストで初期化
            self.schedules = []
            self.save_schedules()  # 空のファイルを作成
            logger.info(f"Created empty schedules file at {self.schedules_file}")
            return True

        try:
            with open(self.schedules_file, 'r', encoding='utf-8') as f:
                self.schedules = json.load(f)
            logger.info(f"Loaded {len(self.schedules)} schedules from {self.schedules_file}")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse schedules file: {e}")
            self.schedules = []
            return False
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")
            self.schedules = []
            return False

    def save_schedules(self) -> bool:
        """
        現在のスケジュールをJSONファイルに保存する
        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            # configディレクトリが存在しない場合は作成
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(self.schedules_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedules, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.schedules)} schedules to {self.schedules_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving schedules: {e}")
            return False

    def get_schedules(self) -> List[Dict[str, str]]:
        """
        全てのスケジュールを取得する
        Returns:
            List[Dict[str, str]]: スケジュールのリスト
        """
        return self.schedules

    def add_schedule(self, time: str, content: str) -> Optional[Dict[str, str]]:
        """
        新しいスケジュールを追加する
        Args:
            time (str): 時刻（HH:MM形式）
            content (str): 通知内容
        Returns:
            Optional[Dict[str, str]]: 追加されたスケジュール、エラー時はNone
        """
        # 入力値のバリデーション
        if not time or not content:
            logger.error("Time and content must not be empty")
            return None
        
        # 時刻のフォーマットチェック (HH:MM)
        try:
            hours, minutes = time.split(':')
            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                logger.error(f"Invalid time format: {time}")
                return None
        except ValueError:
            logger.error(f"Invalid time format: {time}")
            return None
        
        # 新しいスケジュールの作成
        schedule_id = str(uuid.uuid4())
        new_schedule = {
            'id': schedule_id,
            'time': time,
            'content': content
        }
        
        # スケジュールリストに追加して保存
        self.schedules.append(new_schedule)
        if self.save_schedules():
            logger.info(f"Added new schedule: {new_schedule}")
            return new_schedule
        else:
            # 保存に失敗した場合は追加を取り消す
            self.schedules.pop()
            logger.error("Failed to save after adding schedule")
            return None

    def delete_schedule(self, schedule_id: str) -> bool:
        """
        指定されたIDのスケジュールを削除する
        Args:
            schedule_id (str): 削除するスケジュールのID
        Returns:
            bool: 削除が成功したかどうか
        """
        if not schedule_id:
            logger.error("Schedule ID must not be empty")
            return False
        
        # 該当するスケジュールを探す
        original_length = len(self.schedules)
        self.schedules = [s for s in self.schedules if s.get('id') != schedule_id]
        
        # スケジュールが見つからなかった場合
        if len(self.schedules) == original_length:
            logger.warning(f"Schedule with ID {schedule_id} not found")
            return False
        
        # 変更を保存
        if self.save_schedules():
            logger.info(f"Deleted schedule with ID: {schedule_id}")
            return True
        else:
            logger.error("Failed to save after deleting schedule")
            return False 