"""
スケジュール管理サービス

JSONファイルへのスケジュール保存・読み込み、検証、
通知用の音声ファイル生成を提供します。
"""

import json
import os
import uuid
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    ScheduleError, ScheduleValidationError, ScheduleExecutionError,
    JSONParsingError, FileOperationError, FileReadError, FileWriteError,
    ValidationError, AudioError, wrap_exception
)

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
        # 音声ファイル保存用ディレクトリ
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.voice_data_dir = os.path.join(backend_root, 'voice_data', 'schedules')
        os.makedirs(self.voice_data_dir, exist_ok=True)
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
            json_error = wrap_exception(
                e, JSONParsingError,
                "Failed to parse schedules JSON file",
                details={
                    'file_path': self.schedules_file,
                    'file_size': os.path.getsize(self.schedules_file) if os.path.exists(self.schedules_file) else 0
                }
            )
            logger.error(f"Schedule JSON parsing error: {json_error.to_dict()}")
            self.schedules = []
            return False
        except Exception as e:
            load_error = wrap_exception(
                e, FileReadError,
                "Error loading schedules from file",
                details={
                    'file_path': self.schedules_file,
                    'fallback_schedules': []
                }
            )
            logger.error(f"Schedule loading error: {load_error.to_dict()}")
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
            save_error = wrap_exception(
                e, FileWriteError,
                "Error saving schedules to file",
                details={
                    'file_path': self.schedules_file,
                    'schedules_count': len(self.schedules),
                    'config_dir_exists': os.path.exists(self.config_dir)
                }
            )
            logger.error(f"Schedule saving error: {save_error.to_dict()}")
            return False

    def get_schedules(self) -> List[Dict[str, str]]:
        """
        全てのスケジュールを取得する
        Returns:
            List[Dict[str, str]]: スケジュールのリスト
        """
        return self.schedules

    def create_voice_file(self, schedule_id: str, content: str) -> Optional[str]:
        """
        スケジュールの通知音声ファイルを生成する
        Args:
            schedule_id (str): スケジュールID
            content (str): スケジュール内容
        Returns:
            Optional[str]: 生成された音声ファイルのパス、失敗時はNone
        """
        try:
            from web.routes.tts_helpers import tts_service
            
            if not tts_service or not tts_service.is_initialized:
                logger.warning("TTSサービスが初期化されていないため、音声ファイルを生成できません")
                return None
            
            # 音声ファイルパス
            voice_file_path = os.path.join(self.voice_data_dir, f"{schedule_id}.wav")
            
            # 音声合成テキスト
            voice_text = f"{content}の時間です。"
            
            # デフォルト設定の取得
            default_language = self.config_manager.get('tts.default_language', 'ja')
            default_emotion = self.config_manager.get('tts.default_emotion', 'neutral')
            default_speed = self.config_manager.get('tts.default_voice_speed', 1.0)
            default_pitch = self.config_manager.get('tts.default_voice_pitch', 1.0)
            
            # サンプル音声ファイルパス
            default_voice_sample = self.config_manager.get('tts.default_voice_sample_path', None)
            
            # 音声合成実行
            logger.info(f"スケジュール通知用音声ファイル生成中: {voice_text}")
            voice_file = tts_service.generate_speech(
                text=voice_text,
                language=default_language,
                emotion=default_emotion,
                speed=default_speed,
                pitch=default_pitch,
                speaker_sample_path=default_voice_sample,
                output_path=voice_file_path
            )
            
            logger.info(f"スケジュール通知用音声ファイル生成完了: {voice_file}")
            return voice_file
        except Exception as e:
            tts_error = wrap_exception(
                e, AudioError,
                "Failed to generate voice file for schedule",
                details={
                    'schedule_id': schedule_id,
                    'content': content,
                    'voice_data_dir': self.voice_data_dir
                }
            )
            logger.error(f"Schedule voice generation error: {tts_error.to_dict()}")
            return None

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
            validation_error = ValidationError(
                "Time and content must not be empty",
                details={'time': time, 'content': content}
            )
            logger.error(f"Schedule validation error: {validation_error.to_dict()}")
            return None
        
        # 時刻のフォーマットチェック (HH:MM)
        try:
            hours, minutes = time.split(':')
            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                time_validation_error = ScheduleValidationError(
                    f"Invalid time range: {time}",
                    details={'time': time, 'hours': hours, 'minutes': minutes}
                )
                logger.error(f"Schedule time validation error: {time_validation_error.to_dict()}")
                return None
        except ValueError as e:
            time_format_error = wrap_exception(
                e, ScheduleValidationError,
                f"Invalid time format: {time}",
                details={'time': time, 'expected_format': 'HH:MM'}
            )
            logger.error(f"Schedule time format error: {time_format_error.to_dict()}")
            return None
        
        # 新しいスケジュールの作成
        schedule_id = str(uuid.uuid4())
        new_schedule = {
            'id': schedule_id,
            'time': time,
            'content': content
        }
        
        # 音声ファイルの生成
        voice_file = self.create_voice_file(schedule_id, content)
        if voice_file:
            new_schedule['voice_file'] = voice_file
        
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
            id_validation_error = ValidationError(
                "Schedule ID must not be empty",
                details={'schedule_id': schedule_id}
            )
            logger.error(f"Schedule ID validation error: {id_validation_error.to_dict()}")
            return False
        
        # 該当するスケジュールを探す
        original_length = len(self.schedules)
        schedule_to_delete = next((s for s in self.schedules if s.get('id') == schedule_id), None)
        
        # 音声ファイルの削除
        if schedule_to_delete and 'voice_file' in schedule_to_delete:
            voice_file = schedule_to_delete['voice_file']
            try:
                if os.path.exists(voice_file):
                    os.remove(voice_file)
                    logger.info(f"Deleted schedule voice file: {voice_file}")
            except Exception as e:
                logger.warning(f"Failed to delete schedule voice file {voice_file}: {e}")
        
        # スケジュールの削除
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