import logging
from logging import getLogger, StreamHandler, Formatter
import werkzeug
import absl.logging

def setup_logger(name):
    # absログの出力を抑制（MediaPipe用）
    absl.logging.set_verbosity(absl.logging.ERROR)
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Flaskのアクセスログを抑制
        werkzeug.serving.WSGIRequestHandler.log = lambda *args, **kwargs: None
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        
        # MediaPipeのログを抑制
        logging.getLogger('mediapipe').setLevel(logging.ERROR)
        
        # ロガーの設定
        handler = StreamHandler()
        formatter = Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
    
    return logger
