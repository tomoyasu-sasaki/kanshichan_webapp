from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from flask import jsonify

from utils.exceptions import KanshiChanError


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    *,
    status_code: int = 200,
    processing_time_ms: Optional[float] = None,
):
    payload: Dict[str, Any] = {
        "success": True,
        "status": "success",
        "data": data if data is not None else {},
        "timestamp": _now_iso(),
    }
    if message is not None:
        payload["message"] = message
    if processing_time_ms is not None:
        payload["processing_time_ms"] = processing_time_ms

    return jsonify(payload), status_code


def error_response(
    message: str,
    *,
    code: str = "ERROR",
    error_type: str = "Error",
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400,
):
    payload: Dict[str, Any] = {
        "success": False,
        "status": "error",
        "error": {
            "type": error_type,
            "code": code,
            "message": message,
        },
        "timestamp": _now_iso(),
    }
    if details:
        payload["error"]["details"] = details

    return jsonify(payload), status_code


def error_from_exception(
    exc: KanshiChanError,
    *,
    status_code: int = 400,
    include_details: bool = False,
):
    details = exc.details if include_details else None
    return error_response(
        message=exc.message,
        code=exc.error_code or exc.__class__.__name__,
        error_type=exc.__class__.__name__,
        details=details,
        status_code=status_code,
    )


