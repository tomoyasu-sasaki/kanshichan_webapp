import os
import simpleaudio as sa
import threading
from src.kanshichan.utils.logger import setup_logger

logger = setup_logger(__name__)

class SoundService:
    def __init__(self, config):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.sound_dir = os.path.join(self.base_dir, 'sounds')
        
        # サウンドディレクトリが存在しない場合は作成
        if not os.path.exists(self.sound_dir):
            os.makedirs(self.sound_dir)
            logger.info(f"Created sounds directory: {self.sound_dir}")

    def play_alert(self, sound_file='alert.wav'):
        def play():
            try:
                sound_path = os.path.join(self.sound_dir, sound_file)
                
                if not os.path.exists(sound_path):
                    logger.warning(f"Sound file not found: {sound_path}, falling back to default alert.wav")
                    sound_path = os.path.join(self.sound_dir, 'alert.wav')
                    if not os.path.exists(sound_path):
                        logger.error("Default alert sound not found.")
                        return

                wave_obj = sa.WaveObject.from_wave_file(sound_path)
                play_obj = wave_obj.play()
                play_obj.wait_done()
                logger.info(f"Sound played successfully: {sound_path}")
            except Exception as e:
                logger.error(f"Error playing sound: {e}")
        threading.Thread(target=play, daemon=True).start()

