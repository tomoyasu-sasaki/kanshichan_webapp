import os
import logging
import threading
import simpleaudio as sa

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SoundService:
    def __init__(self, sound_dir):
        self.sound_dir = sound_dir

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
        thread = threading.Thread(target=play)
        thread.start()



class AlertSystem:
    def __init__(self, sound_service):
        self.sound_service = sound_service
        self.executor = threading.Thread

    def trigger_alert(self, message, sound_file='alert.wav'):
        """非同期で通知と音声再生を実行"""
        logger.info(f"Triggering alert: {message}")
        self.executor(target=self.sound_service.play_alert, args=(sound_file,), daemon=True).start()

    def trigger_smartphone_alert(self):
        self.trigger_alert("スマホばかり触っていないで勉強をしろ！", 'smartphone_alert.wav')


if __name__ == "__main__":
    # サウンドディレクトリのパスを指定
    sound_dir = "/Users/tmys-sasaki/Projects/Private/KanshiChan/src/kanshichan/sounds/"

    # サウンドサービスとアラートシステムの初期化
    sound_service = SoundService(sound_dir)
    alert_system = AlertSystem(sound_service)

    # サウンドファイルの確認
    if not os.path.exists(os.path.join(sound_dir, 'alert.wav')):
        logger.error("Default alert.wav not found in the sounds directory.")
    if not os.path.exists(os.path.join(sound_dir, 'smartphone_alert.wav')):
        logger.error("smartphone_alert.wav not found in the sounds directory.")

    # アラートのテスト
    logger.info("Testing trigger_alert...")
    alert_system.trigger_alert("これはテストメッセージです", 'alert.wav')

    logger.info("Testing trigger_smartphone_alert...")
    alert_system.trigger_smartphone_alert()


import simpleaudio as sa

wave_obj = sa.WaveObject.from_wave_file('/Users/tmys-sasaki/Projects/Private/KanshiChan/src/kanshichan/sounds/alert.wav')
play_obj = wave_obj.play()
play_obj.wait_done()
print("Sound played successfully.")
