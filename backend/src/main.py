import threading
# from web.server import app # 古い import を削除
from web.app import create_app # create_app をインポート
from core.monitor import Monitor
from core.camera import Camera
from core.detector import Detector
from core.detection_manager import DetectionManager
from core.state_manager import StateManager
from services.alert_service import AlertService
from services.alert_manager import AlertManager
from services.schedule_manager import ScheduleManager  # ScheduleManagerをインポート
from utils.config_manager import ConfigManager # ConfigManager をインポート
from utils.logger import setup_logger

logger = setup_logger(__name__)

def start_monitor_thread(monitor_instance):
    """モニターを別スレッドで実行"""
    monitor_thread = threading.Thread(target=monitor_instance.run, daemon=True)
    monitor_thread.start()
    return monitor_thread

if __name__ == '__main__':
    try:
        logger.info("アプリケーションを開始します...")
        # --- ConfigManager の初期化と設定読み込み ---
        config_manager = ConfigManager()
        config_manager.load() # 設定ファイルを読み込む
        logger.info("設定を ConfigManager で読み込みました。")
        # ---------------------------------------

        # --- Flask アプリケーションの作成 ---
        # create_app に config_manager を渡す
        app = create_app(config_manager)
        logger.info("Flask アプリケーションを作成しました。")
        # --- ここまで ---

        # --- 依存コンポーネントのインスタンス化 (ConfigManager を渡す) ---
        logger.info("依存コンポーネントを初期化中...")
        camera = Camera(config_manager) # Cameraにも ConfigManager を渡す
        detector = Detector(config_manager) # Detector に ConfigManager を渡す
        detection_manager = DetectionManager(detector)
        # AlertService と StateManager に config_manager を渡す
        alert_service = AlertService(config_manager)
        alert_manager = AlertManager(alert_service)
        state_manager = StateManager(config_manager, alert_manager)
        # ScheduleManagerのインスタンス化
        schedule_manager = ScheduleManager(config_manager)
        logger.info("ScheduleManager を初期化しました。")
        # --- ここまで ---

        # Monitor インスタンスの作成 (ConfigManager を渡す)
        monitor = Monitor(
            config_manager=config_manager, # config の代わりに config_manager を渡す
            camera=camera,
            detector=detector,
            detection_manager=detection_manager,
            state_manager=state_manager,
            alert_manager=alert_manager,
            schedule_manager=schedule_manager  # ScheduleManager を追加
        )
        logger.info("Monitor インスタンスを作成しました。")

        # --- Flask アプリケーションに Monitor と ConfigManager を設定 ---
        # ConfigManager は create_app に渡したので、ここで再度設定する必要はないかも？
        # ただし、他の場所で app.config['config_manager'] を参照しているなら設定しておく。
        app.config['monitor_instance'] = monitor
        app.config['config_manager'] = config_manager # 念のため設定
        app.config['schedule_manager'] = schedule_manager # ScheduleManagerを設定
        logger.info("Flask アプリケーションに Monitor, ConfigManager, ScheduleManager を設定しました。")
        # --- ここまで ---

        # モニターを別スレッドで開始
        logger.info("モニタリングを別スレッドで開始します...")
        monitor_thread = start_monitor_thread(monitor)
        logger.info("モニタリングスレッドを開始しました。")

        # Flask サーバーの起動
        logger.info("Flask サーバーを起動します...")
        # port を config_manager から取得
        port = config_manager.get('server.port', 5001)
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

    except Exception as e:
        logger.critical(f"アプリケーションの起動中に致命的なエラーが発生しました: {e}", exc_info=True)
    finally:
        logger.info("アプリケーションを終了します...")
        if 'monitor' in locals() and isinstance(monitor, Monitor):
             logger.info("Monitor クリーンアップ処理を実行します...")
             monitor.cleanup()
        logger.info("クリーンアップ完了。")
