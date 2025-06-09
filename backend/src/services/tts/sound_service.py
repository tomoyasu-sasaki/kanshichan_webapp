import platform
import os
import threading
from utils.logger import setup_logger
from utils.exceptions import (
    AudioError, AudioPlaybackError, AudioFileError,
    HardwareError, FileNotFoundError, wrap_exception
)
from pathlib import Path

logger = setup_logger(__name__)

class SoundService:
    def __init__(self):
        # プロジェクトのルートディレクトリを基準に絶対パスを構築
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.sound_dir = project_root / 'src' / 'sounds'
        
        logger.info(f"Sound directory set to: {self.sound_dir}")
        self._initialize_sound_system()

    def _initialize_sound_system(self):
        """OSに応じたサウンドシステムの初期化"""
        system = platform.system()
        if system == "Windows":
            import winsound
            self.play_sound = self._play_sound_windows
        else:
            from playsound import playsound
            self.play_sound = self._play_sound_unix

    def _play_sound_windows(self, sound_path):
        """Windows用の音声再生"""
        import winsound
        try:
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            logger.info(f"Sound played successfully (Windows): {sound_path}")
        except Exception as e:
            windows_audio_error = wrap_exception(
                e, AudioPlaybackError,
                "Error playing sound on Windows",
                details={
                    'sound_path': sound_path,
                    'platform': 'Windows',
                    'file_exists': Path(sound_path).exists() if sound_path else False
                }
            )
            logger.error(f"Windows audio error: {windows_audio_error.to_dict()}")

    def _play_sound_unix(self, sound_path):
        """Unix系OS用の音声再生"""
        from playsound import playsound
        try:
            # 音声ファイルの存在確認
            if not os.path.exists(sound_path):
                logger.error(f"Sound file not found: {sound_path}")
                return
            playsound(sound_path)
            logger.info(f"Sound played successfully (Unix): {sound_path}")
        except Exception as e:
            unix_audio_error = wrap_exception(
                e, AudioPlaybackError,
                "Error playing sound on Unix",
                details={
                    'sound_path': sound_path,
                    'platform': platform.system(),
                    'file_exists': Path(sound_path).exists() if sound_path else False
                }
            )
            logger.error(f"Unix audio error: {unix_audio_error.to_dict()}")

    def play_alert(self, sound_file='alert.wav'):
        def play():
            try:
                sound_path = self.sound_dir / sound_file
                logger.info(f"Attempting to play sound: {sound_path}")
                
                if not sound_path.exists():
                    logger.warning(f"音声ファイルが見つかりません: {sound_path}")
                    
                    # ファイル名の検索を改善 - スペースや大文字小文字の違いを無視
                    # ディレクトリ内のすべてのファイルをリスト
                    files_in_dir = [f.name for f in self.sound_dir.iterdir() if f.is_file()]
                    logger.info(f"利用可能な音声ファイル: {files_in_dir}")
                    
                    # ファイル名の類似性でマッチングを試みる
                    normalized_sound_file = sound_file.lower().replace(" ", "")
                    for file_name in files_in_dir:
                        normalized_file = file_name.lower().replace(" ", "")
                        if normalized_sound_file in normalized_file:
                            sound_path = self.sound_dir / file_name
                            logger.info(f"類似の音声ファイルが見つかりました: {file_name}")
                            break
                    
                    # それでも見つからなければデフォルト音声を使用
                    if not sound_path.exists():
                        logger.warning(f"類似の音声ファイルも見つかりません。デフォルトの音声を使用します")
                        sound_path = self.sound_dir / 'alert.wav'
                        if not sound_path.exists():
                            logger.error("デフォルトのアラート音も見つかりません")
                            return

                self.play_sound(str(sound_path))
            except Exception as e:
                audio_play_error = wrap_exception(
                    e, AudioError,
                    "音声再生中にエラーが発生しました",
                    details={
                        'sound_file': sound_file,
                        'sound_dir': self.sound_dir,
                        'platform': platform.system(),
                        'thread_mode': True
                    }
                )
                logger.error(f"Audio playback error: {audio_play_error.to_dict()}")

        thread = threading.Thread(target=play, daemon=True)
        thread.start()
