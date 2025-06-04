import threading
import time
from datetime import datetime
from flask import current_app
from web.app import create_app # create_app をインポート
from core.monitor import Monitor
from core.camera import Camera
from core.detector import Detector
from core.detection import DetectionManager
from core.state import StateManager
from services.communication.alert_manager import AlertManager
from services.communication.alert_service import AlertService
from services.tts.sound_service import SoundService
from services.automation.schedule_manager import ScheduleManager
from services.data.data_collector import DataCollector
from services.data.storage_service import StorageService
from services.analysis.behavior_analyzer import BehaviorAnalyzer
from utils.config_manager import ConfigManager
from utils.logger import setup_logger
from models import init_db

def start_monitor_thread(monitor_instance):
    """モニターを別スレッドで実行"""
    monitor_thread = threading.Thread(target=monitor_instance.run, daemon=True)
    monitor_thread.start()
    return monitor_thread

# Phase 3.3: 定期分析実行関数
def run_periodic_analysis(app_instance):
    """定期分析実行関数"""
    
    while True:
        try:
            with app_instance.app_context():
                analyzer = current_app.config.get('behavior_analyzer')
                if analyzer:
                    # 最近1時間のログを取得
                    from models.behavior_log import BehaviorLog
                    recent_logs = BehaviorLog.get_recent_logs(hours=1)
                    
                    if recent_logs and len(recent_logs) > 5:
                        # インサイト生成
                        insights = analyzer.generate_insights('hourly')
                        # app_loggerを取得してログ出力
                        logger = setup_logger(__name__ + ".periodic_analysis")
                        logger.info(f"Periodic analysis completed: {len(insights.get('key_insights', []))} insights generated")
                        
                        # 異常検知も実行
                        anomalies = analyzer.detect_anomalies(recent_logs)
                        if anomalies:
                            logger.warning(f"Anomalies detected: {len(anomalies)} issues found")
                    else:
                        logger = setup_logger(__name__ + ".periodic_analysis")
                        logger.debug(f"Insufficient data for analysis: {len(recent_logs) if recent_logs else 0} logs")
                else:
                    logger = setup_logger(__name__ + ".periodic_analysis")
                    logger.warning("BehaviorAnalyzer not available for periodic analysis")
                    
        except Exception as e:
            logger = setup_logger(__name__ + ".periodic_analysis")
            logger.error(f"Periodic analysis error: {e}", exc_info=True)
        
        # 1時間間隔
        time.sleep(3600)

if __name__ == '__main__':
    try:
        # 初期ログメッセージは削除（app_logger初期化後に出力）
        # logger.info("アプリケーションを開始します...")
        
        # --- ConfigManager の初期化と設定読み込み ---
        config_manager = ConfigManager()
        config_manager.load() # 設定ファイルを読み込む
        
        # 設定読み込み後にロガーを初期化（1回のみ）
        app_logger = setup_logger(__name__, config_manager.get_all())
        app_logger.info("アプリケーションを開始します...")
        app_logger.info("設定を ConfigManager で読み込みました。")
        app_logger.info("ログ設定を config.yaml から適用しました。")
        # ---------------------------------------

        # --- Flask アプリケーションの作成 ---
        # create_app に config_manager を渡す
        app, socketio = create_app(config_manager)
        app_logger.info("Flask アプリケーションを作成しました。")
        # --- ここまで ---

        # --- データベース初期化 ---
        app_logger.info("データベースを初期化中...")
        init_db(app)
        app_logger.info("データベース初期化が完了しました。")

        # --- 依存コンポーネントのインスタンス化 (ConfigManager を渡す) ---
        app_logger.info("依存コンポーネントを初期化中...")
        camera = Camera(config_manager) # Cameraにも ConfigManager を渡す
        detector = Detector(config_manager) # Detector に ConfigManager を渡す
        detection = DetectionManager(detector)
        # AlertService と StateManager に config_manager を渡す
        alert_service = AlertService(config_manager)
        alert_manager = AlertManager(alert_service)
        state = StateManager(config_manager, alert_manager)
        # ScheduleManagerのインスタンス化
        schedule_manager = ScheduleManager(config_manager)
        app_logger.info("ScheduleManager を初期化しました。")
        # --- ここまで ---

        # Phase 1.1: DataCollector の初期化
        app_logger.info("DataCollector を初期化しています...")
        data_collector = DataCollector(
            camera=camera,
            detector=detector,
            state_manager=state,
            collection_interval=2.0,  # 2秒間隔
            flask_app=app             # Phase 2: Flaskアプリを追加
        )
        
        # StorageService の初期化
        storage_service = StorageService()
        app_logger.info("StorageService を初期化しました")

        # Phase 3.1: BehaviorAnalyzer の初期化
        app_logger.info("BehaviorAnalyzer を初期化しています...")
        behavior_analyzer = BehaviorAnalyzer(config_manager.get_all())
        app_logger.info("BehaviorAnalyzer を初期化しました")

        # Monitor インスタンスの作成 (ConfigManager を渡す)
        monitor = Monitor(
            config_manager=config_manager, # config の代わりに config_manager を渡す
            camera=camera,
            detector=detector,
            detection=detection,
            state=state,
            alert_manager=alert_manager,
            schedule_manager=schedule_manager,  # ScheduleManager を追加
            data_collector=data_collector,      # Phase 1.2: 追加
            storage_service=storage_service,    # Phase 1.2: 追加
            flask_app=app                       # Phase 4.2: Flask app を追加
        )
        app_logger.info("Monitor インスタンスを作成しました。")

        # --- Flask アプリケーションに Monitor と ConfigManager を設定 ---
        # ConfigManager は create_app に渡したので、ここで再度設定する必要はないかも？
        # ただし、他の場所で app.config['config_manager'] を参照しているなら設定しておく。
        app.config['monitor_instance'] = monitor
        app.config['config_manager'] = config_manager # 念のため設定
        app.config['schedule_manager'] = schedule_manager # ScheduleManagerを設定
        # Phase 3.1: BehaviorAnalyzer をアプリケーション設定に追加
        app.config['behavior_analyzer'] = behavior_analyzer
        app_logger.info("Flask アプリケーションに Monitor, ConfigManager, ScheduleManager, BehaviorAnalyzer を設定しました。")
        # --- ここまで ---

        # モニターを別スレッドで開始
        app_logger.info("モニタリングを別スレッドで開始します...")
        monitor_thread = start_monitor_thread(monitor)
        app_logger.info("モニタリングスレッドを開始しました。")

        # Phase 3.3: 定期分析スレッドの開始
        app_logger.info("定期分析スレッドを開始します...")
        analysis_thread = threading.Thread(target=run_periodic_analysis, args=(app,), daemon=True)
        analysis_thread.start()
        app_logger.info("定期分析スレッドを開始しました - 1時間間隔で実行されます")

        # Flask サーバーの起動
        app_logger.info("Flask サーバーを起動します...")
        # port を config_manager から取得
        port = config_manager.get('server.port', 8000)
        socketio.run(app, host='0.0.0.0', port=port, debug=False, use_reloader=False)

    except Exception as e:
        # アプリケーション開始前のエラーの場合はsetup_loggerを直接使用
        error_logger = setup_logger(__name__)
        error_logger.critical(f"アプリケーションの起動中に致命的なエラーが発生しました: {e}", exc_info=True)
    finally:
        # アプリケーション終了時のクリーンアップ
        if 'app_logger' in locals():
            app_logger.info("アプリケーションを終了します...")
            if 'monitor' in locals() and isinstance(monitor, Monitor):
                app_logger.info("Monitor クリーンアップ処理を実行します...")
                monitor.cleanup()
            app_logger.info("クリーンアップ完了。")
        else:
            # app_loggerが初期化される前のエラーの場合
            final_logger = setup_logger(__name__)
            final_logger.info("アプリケーションを終了します...")
