"""
レスポンスユーティリティ

Flask 用の標準化された成功/エラーレスポンスを生成します。
フロントエンドとバックエンド間のレスポンス形式を一貫化し、
タイムスタンプや処理時間などの共通メタ情報を付与します。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from flask import jsonify

from utils.exceptions import KanshiChanError


def _now_iso() -> str:
    """現在のUTC時刻をISO 8601文字列で返します。"""
    return datetime.utcnow().isoformat()


def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    *,
    status_code: int = 200,
    processing_time_ms: Optional[float] = None,
):
    """成功レスポンスを生成します。

    Args:
        data: 返却するデータ辞書。未指定時は空辞書。
        message: 追加のメッセージ（任意）。
        status_code: HTTP ステータスコード（デフォルト: 200）。
        processing_time_ms: 処理時間ミリ秒（任意）。

    Returns:
        tuple: (Flask JSONレスポンス, HTTPステータスコード)
    """
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
    """エラーレスポンスを生成します。

    Args:
        message: エラーメッセージ。
        code: アプリ内エラーコード（デフォルト: "ERROR"）。
        error_type: エラー種別（例: ValidationError）。
        details: 追加の詳細情報（任意）。
        status_code: HTTP ステータスコード（デフォルト: 400）。

    Returns:
        tuple: (Flask JSONレスポンス, HTTPステータスコード)
    """
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
    """ドメイン例外から標準化エラーレスポンスを生成します。

    Args:
        exc: `KanshiChanError` 派生例外。
        status_code: HTTP ステータスコード（デフォルト: 400）。
        include_details: 例外の詳細情報を含めるか。

    Returns:
        tuple: (Flask JSONレスポンス, HTTPステータスコード)
    """
    details = exc.details if include_details else None
    return error_response(
        message=exc.message,
        code=exc.error_code or exc.__class__.__name__,
        error_type=exc.__class__.__name__,
        details=details,
        status_code=status_code,
    )


