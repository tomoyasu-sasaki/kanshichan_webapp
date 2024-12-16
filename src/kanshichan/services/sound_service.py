import os
import platform
import threading
from src.kanshichan.utils.logger import setup_logger

logger = setup_logger(__name__)

class SoundService:
    def __init__(self, config):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.sound_dir = os.path.join(self.base_dir, 'src', 'kanshichan', 'sounds')
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
            logger.error(f"Error playing sound on Windows: {e}")

    def _play_sound_unix(self, sound_path):
        """Unix系OS用の音声再生"""
        from playsound import playsound
        try:
            playsound(sound_path)
            logger.info(f"Sound played successfully (Unix): {sound_path}")
        except Exception as e:
            logger.error(f"Error playing sound on Unix: {e}")

    def play_alert(self, sound_file='alert.wav'):
        def play():
            try:
                sound_path = os.path.join(self.sound_dir, sound_file)
                if not os.path.exists(sound_path):
                    logger.warning(f"Sound file not found: {sound_path}")
                    sound_path = os.path.join(self.sound_dir, 'alert.wav')
                    if not os.path.exists(sound_path):
                        logger.error("Default alert sound not found.")
                        return

                self.play_sound(sound_path)
            except Exception as e:
                logger.error(f"Error playing sound: {e}")

        thread = threading.Thread(target=play, daemon=True)
        thread.start()
