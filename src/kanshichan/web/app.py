from flask import Flask
from linebot.v3 import WebhookHandler
from src.kanshichan.web.handlers import setup_handlers
from src.kanshichan.utils.logger import setup_logger

logger = setup_logger(__name__)

def create_app(config):
    app = Flask(__name__)
    
    # LINE Handlerの初期化
    line_handler = WebhookHandler(config['line']['channel_secret'])
    
    # configにline_handlerを追加
    config['line_handler'] = line_handler
    
    app.config.from_mapping(config)
    setup_handlers(app, config)
    
    return app
