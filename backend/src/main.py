import threading
import time
import sys
import os
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
from utils.exceptions import ConfigError
from models import init_db
import faulthandler

faulthandler.enable()

def start_monitor_thread(monitor_instance):
    """モニターを別スレッドで実行"""
    monitor_thread = threading.Thread(target=monitor_instance.run, daemon=True)
    monitor_thread.start()
    return monitor_thread

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

def initialize_config_manager():
    """
    ConfigManagerを初期化して返します。
    設定ファイルが見つからない場合は例外を発生させます。
    
    Returns:
        ConfigManager: 初期化されたConfigManagerインスタンス
        
    Raises:
        ConfigError: 設定ファイルが見つからない、またはロードできない場合
    """
    # 環境変数から環境を取得（デフォルトはprod）
    environment = os.environ.get("KANSHICHAN_ENV", "prod")
    
    # 設定がない場合は失敗させる（Fail-fast）
    config_manager = ConfigManager(
        environment=environment, 
        fail_on_missing=(environment != "dev")  # 開発環境以外では設定必須
    )
    
    # 設定を読み込み、失敗したら例外を投げる
    try:
        config_manager.load()
    except ConfigError as e:
        logger = setup_logger(__name__)
        logger.critical(f"設定ファイルの読み込みに失敗しました: {e}")
        # 開発環境以外または明示的にfail_on_missingが有効な場合は起動失敗
        if environment != "dev" or config_manager.fail_on_missing:
            raise
    
    # 読み込まれたかどうかを確認
    if not config_manager.is_loaded() and environment != "dev":
        error_msg = "設定ファイルが正しく読み込まれませんでした"
        logger = setup_logger(__name__)
        logger.critical(error_msg)
        raise ConfigError(error_msg)
        
    return config_manager

if __name__ == '__main__':
    try:
        # ConfigManagerの初期化を別関数に分離
        try:
            config_manager = initialize_config_manager()
        except ConfigError as e:
            # 設定読み込み失敗時は致命的エラーとして終了
            error_logger = setup_logger(__name__)
            error_logger.critical(f"設定初期化に失敗したため、アプリケーションを終了します: {e}", exc_info=True)
            sys.exit(1)
        
        # 設定読み込み後にロガーを初期化（1回のみ）
        app_logger = setup_logger(__name__, config_manager.get_all())
        app_logger.info("アプリケーションを開始します...")
        app_logger.info(f"環境 '{config_manager.environment}' 用の設定を読み込みました: {config_manager.config_path}")
        app_logger.info("ログ設定を config から適用しました。")

        # --- Flask アプリケーションの作成 ---
        # create_app に config_manager を渡す
        app, socketio = create_app(config_manager)
        app_logger.info("Flask アプリケーションを作成しました。")
        # --- ここまで ---

        # ConfigManagerがアプリケーションに注入されたか確認（Fail-fast）
        if 'config_manager' not in app.config:
            error_msg = "ConfigManagerがFlaskアプリケーションに正しく注入されていません"
            app_logger.critical(error_msg)
            raise ConfigError(error_msg)

        # --- データベース初期化 ---
        app_logger.info("データベースを初期化中...")
        init_db(app)
        app_logger.info("データベース初期化が完了しました。")
        
        # --- 依存コンポーネントのインスタンス化 (ConfigManager を渡す) ---
        # ヘッドレスでの安定動作のため、OpenCVウィンドウはデフォルト無効化
        os.environ.setdefault('KANSHICHAN_HEADLESS', '1')
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

        app_logger.info("DataCollector を初期化しています...")
        data_collector = DataCollector(
            camera=camera,
            detector=detector,
            state_manager=state,
            collection_interval=2.0,  # 2秒間隔
            flask_app=app
        )
        
        # StorageService の初期化
        storage_service = StorageService()
        app_logger.info("StorageService を初期化しました")

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
            data_collector=data_collector,     
            storage_service=storage_service,   
            flask_app=app                      
        )
        app_logger.info("Monitor インスタンスを作成しました。")

        # --- Flask アプリケーションに Monitor と ConfigManager を設定 ---
        # 他のコンポーネントも設定
        app.config['monitor_instance'] = monitor
        app.config['config_manager'] = config_manager # Flaskアプリに注入
        app.config['schedule_manager'] = schedule_manager # ScheduleManagerを設定
        app.config['behavior_analyzer'] = behavior_analyzer
        app_logger.info("Flask アプリケーションに Monitor, ConfigManager, ScheduleManager, BehaviorAnalyzer を設定しました。")

        # モニターを別スレッドで開始
        app_logger.info("モニタリングを別スレッドで開始します...")
        monitor_thread = start_monitor_thread(monitor)
        app_logger.info("モニタリングスレッドを開始しました。")

        app_logger.info("定期分析スレッドを開始します...")
        analysis_thread = threading.Thread(target=run_periodic_analysis, args=(app,), daemon=True)
        analysis_thread.start()
        app_logger.info("定期分析スレッドを開始しました - 1時間間隔で実行されます")

        # Flask サーバーの起動
        app_logger.info("Flask サーバーを起動します...")
        # port を config_manager から取得
        port = config_manager.get('server.port', 8000)
        # macOSでのOpenCV UIとSocketIOの相性問題を避けるため、環境変数でヘッドレス起動を許容
        # ヘッドレス時はフレーム表示を行わない
        os.environ.setdefault('KANSHICHAN_HEADLESS', '1')
        socketio.run(app, host='0.0.0.0', port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

    except Exception as e:
        # アプリケーション開始前のエラーの場合はsetup_loggerを直接使用
        error_logger = setup_logger(__name__)
        error_logger.critical(f"アプリケーションの起動中に致命的なエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
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
