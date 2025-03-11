from flask import request, abort
from linebot.v3.exceptions import InvalidSignatureError
from backend.src.utils.logger import setup_logger

logger = setup_logger(__name__)

def setup_handlers(app, config):
    line_handler = config['line_handler']
    if not line_handler:
        logger.error("LINE handlerが設定されていません")
        raise ValueError("LINE handler configuration missing")

    @app.route("/callback", methods=['POST'])
    def callback():
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        logger.debug(f"Request body: {body}")

        try:
            line_handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return 'OK', 200

        return 'OK', 200
