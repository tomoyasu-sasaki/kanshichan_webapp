import threading
import sys
from backend.src.utils.logger import setup_logger
from backend.src.utils.config import load_config
from backend.src.core.monitor import Monitor
from backend.src.web.app import create_app

logger = setup_logger(__name__)

def main():
    try:
        # 設定の読み込み
        config = load_config()
        logger.debug(f"Loaded configuration: {config}")  # 設定内容を確認
        
        # Flaskアプリケーションの作成と実行
        app = create_app(config)
        flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=5001, debug=False),
            daemon=True
        )
        flask_thread.start()
        logger.info("Flask server started on port 5001")

        # モニターの初期化と実行
        monitor = Monitor(config)
        monitor.run()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down gracefully.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
