from flask import request, abort, current_app
from utils.logger import setup_logger
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3 import WebhookHandler
from typing import Optional

logger = setup_logger(__name__)

def setup_handlers(app, line_handler: Optional[WebhookHandler]):
    if not line_handler:
        logger.warning("LINE handler is None. /callback endpoint will not be configured.")
        return

    @app.route("/callback", methods=['POST'])
    def callback():
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        logger.debug(f"Request body: {body}")

        try:
            line_handler.handle(body, signature)
        except InvalidSignatureError:
            logger.warning("Invalid LINE signature received.")
            abort(400)
        except Exception as e:
            logger.error(f"Error handling webhook: {e}", exc_info=True)
            return 'OK', 200

        return 'OK', 200
