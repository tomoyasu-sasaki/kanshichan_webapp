from flask import request, abort, current_app
from utils.logger import setup_logger
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3 import WebhookHandler
from typing import Optional
from utils.exceptions import (
    APIError, LineAPIError, ValidationError, wrap_exception
)

logger = setup_logger(__name__)

def setup_handlers(app, line_handler: Optional[WebhookHandler]):
    if not line_handler:
        logger.warning("LINE handler is None. /callback endpoint will not be configured.")
        return

    @app.route("/callback", methods=['POST'])
    def callback():
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        logger.info(f"LINE Webhook received. Request body: {body}")
        logger.info(f"LINE Webhook headers: {dict(request.headers)}")

        try:
            line_handler.handle(body, signature)
            logger.info("LINE Webhook処理完了")
        except InvalidSignatureError as e:
            signature_error = wrap_exception(
                e, ValidationError,
                "Invalid LINE signature received",
                details={
                    'signature_present': bool(signature),
                    'body_length': len(body) if body else 0
                }
            )
            logger.warning(f"LINE signature validation error: {signature_error.to_dict()}")
            abort(400)
        except Exception as e:
            webhook_error = wrap_exception(
                e, LineAPIError,
                "Error handling LINE webhook",
                details={
                    'body_length': len(body) if body else 0,
                    'signature_present': bool(signature),
                    'handler_available': line_handler is not None
                }
            )
            logger.error(f"LINE webhook handling error: {webhook_error.to_dict()}")
            return 'OK', 200

        return 'OK', 200
