import logging
from logging import getLogger, StreamHandler, FileHandler, Formatter
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import werkzeug
import absl.logging
import time
from typing import Dict, Any, Optional
from functools import wraps
import json
from datetime import datetime

# 頻繁なログの抑制用グローバル辞書
_log_suppression_cache: Dict[str, Dict[str, Any]] = {}

class FrequentLogFilter(logging.Filter):
    """頻繁なログメッセージを抑制するフィルタ"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self.suppress_enabled = self.config.get('suppress_frequent_logs', False)
        self.frame_log_interval = self.config.get('frame_log_interval', 300)  # 5分
        self.detection_sampling = self.config.get('detection_log_sampling', 50)
        self.max_duplicates = self.config.get('max_duplicate_suppression', 10)
        
        # 抑制カウンタ
        self.suppression_counters = {}
        self.last_log_times = {}
        self.detection_counter = 0
        
    def filter(self, record) -> bool:
        """ログレコードをフィルタリング"""
        if not self.suppress_enabled:
            return True
            
        message = record.getMessage()
        current_time = time.time()
        
        # フレーム処理ログの抑制（5分間隔）
        if any(keyword in message for keyword in [
            'Starting object detection',
            'Detection completed',
            'Added pose landmarks',
            'Added hands landmarks',
            'Added face landmarks'
        ]):
            # 検出ログのサンプリング
            self.detection_counter += 1
            if self.detection_counter % self.detection_sampling != 0:
                return False
                
            # 時間間隔チェック
            key = f"detection_{record.name}"
            if key in self.last_log_times:
                if current_time - self.last_log_times[key] < self.frame_log_interval:
                    return False
            self.last_log_times[key] = current_time
            
        # 重複メッセージの抑制
        if self._is_duplicate_message(message, record.name, current_time):
            return False
            
        return True
        
    def _is_duplicate_message(self, message: str, logger_name: str, current_time: float) -> bool:
        """重複メッセージをチェック"""
        # メッセージの要約（数値部分を除去）
        import re
        normalized_msg = re.sub(r'\d+', 'N', message)
        key = f"{logger_name}:{normalized_msg}"
        
        if key not in self.suppression_counters:
            self.suppression_counters[key] = {'count': 1, 'last_time': current_time}
            return False
            
        counter_info = self.suppression_counters[key]
        counter_info['count'] += 1
        
        # 最大抑制回数を超えた場合は通す
        if counter_info['count'] > self.max_duplicates:
            counter_info['count'] = 1  # リセット
            counter_info['last_time'] = current_time
            return False
            
        # 短時間での重複は抑制
        if current_time - counter_info['last_time'] < 1.0:  # 1秒以内の重複
            return True
            
        counter_info['last_time'] = current_time
        return False

class JSONFormatter(logging.Formatter):
    """シンプルなJSONフォーマッタ（追加依存なし）"""

    def __init__(self) -> None:
        super().__init__()

    def _safe(self, value: Any) -> Any:
        try:
            json.dumps(value)
            return value
        except Exception:
            return repr(value)

    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 代表的な属性を抽出して付与（存在するものだけ）
        for attr in ("pathname", "lineno", "funcName", "process", "threadName"):
            if hasattr(record, attr):
                base[attr] = getattr(record, attr)

        # 例外情報
        if record.exc_info:
            try:
                base["exc_info"] = self.formatException(record.exc_info)
            except Exception:
                base["exc_info"] = "<unavailable>"

        # 任意のextra（辞書）を拾う（存在しない場合は無視）
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            try:
                base["extra"] = {k: self._safe(v) for k, v in record.extra.items()}
            except Exception:
                base["extra"] = {"_error": "failed to serialize extra"}

        # 最終的にすべてをJSONに
        try:
            return json.dumps(base, ensure_ascii=False)
        except Exception:
            # フォールバック（最低限メッセージは出す）
            return json.dumps({"message": record.getMessage()}, ensure_ascii=False)

def setup_logger(name, config=None):
    """ロガーを設定
    
    Args:
        name: ロガー名
        config: 設定辞書（オプション）
    """
    # absログの出力を抑制（MediaPipe用）
    absl.logging.set_verbosity(absl.logging.ERROR)
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Flaskのアクセスログを抑制
        werkzeug.serving.WSGIRequestHandler.log = lambda *args, **kwargs: None
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        
        # MediaPipeのログを抑制
        logging.getLogger('mediapipe').setLevel(logging.ERROR)
        
        # サードパーティライブラリのログレベル調整
        logging.getLogger('ultralytics').setLevel(logging.WARNING)
        logging.getLogger('torch').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        
        # 設定からログ設定を取得
        log_config = config.get('logging', {}) if config else {}
        
        enable_file_output = log_config.get('enable_file_output', True)
        enable_console_output = log_config.get('enable_console_output', True)
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        console_level = getattr(logging, log_config.get('console_level', 'INFO'))
        file_level = getattr(logging, log_config.get('file_level', 'INFO'))  # DEBUG→INFO
        log_dir_config = log_config.get('log_dir', 'logs')
        max_file_size_mb = log_config.get('max_file_size_mb', 50)  # 10→50MB
        backup_count = log_config.get('backup_count', 3)  # 5→3
        # JSON構造化ログの有効化フラグ（env優先）
        json_enabled_env = str(os.environ.get('KANSHICHAN_LOG_JSON', '0')).lower() in ('1', 'true', 'yes')
        json_enabled_cfg = bool(log_config.get('json_format', False))
        json_enabled = json_enabled_env or json_enabled_cfg
        
        # 絶対パス解決：プロジェクトルート（backend）のlogsディレクトリに統一
        current_file = Path(__file__)  # backend/src/utils/logger.py
        backend_root = current_file.parent.parent.parent  # backend/
        log_dir_path = backend_root / log_dir_config  # backend/logs
        
        # ログディレクトリの作成
        log_dir_path.mkdir(exist_ok=True)
        
        # ログファイルパス
        log_file = log_dir_path / "kanshichan.log"
        
        # 頻繁なログ抑制フィルタの初期化
        log_filter = FrequentLogFilter(log_config)
        
        # コンソールハンドラー
        if enable_console_output:
            console_handler = StreamHandler()
            if json_enabled:
                console_handler.setFormatter(JSONFormatter())
            else:
                console_formatter = Formatter('[%(asctime)s] [%(levelname)s] %(name)s: %(message)s')
                console_handler.setFormatter(console_formatter)
            console_handler.setLevel(console_level)
            console_handler.addFilter(log_filter)
            logger.addHandler(console_handler)
        
        # ファイルハンドラー（ローテーション付き）
        if enable_file_output:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size_mb*1024*1024,  # MB→バイト変換
                backupCount=backup_count,
                encoding='utf-8'
            )
            if json_enabled:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_formatter = Formatter('[%(asctime)s] [%(levelname)s] %(name)s: %(message)s')
                file_handler.setFormatter(file_formatter)
            file_handler.setLevel(file_level)
            file_handler.addFilter(log_filter)
            logger.addHandler(file_handler)
        
        # ロガーレベル設定
        logger.setLevel(log_level)
    
    return logger

def log_performance_metric(logger, metric_name: str, value: Any, extra_data: Optional[Dict] = None):
    """パフォーマンスメトリクスのログ出力（抑制対応）
    
    Args:
        logger: ロガーインスタンス
        metric_name: メトリクス名
        value: 値
        extra_data: 追加データ
    """
    # パフォーマンスログは5分間隔で出力
    global _log_suppression_cache
    current_time = time.time()
    cache_key = f"performance_{metric_name}"
    
    if cache_key in _log_suppression_cache:
        last_time = _log_suppression_cache[cache_key]['last_time']
        if current_time - last_time < 300:  # 5分間隔
            return
    
    _log_suppression_cache[cache_key] = {'last_time': current_time}
    
    extra_info = f", extra={extra_data}" if extra_data else ""
    logger.info(f"Performance metric - {metric_name}: {value}{extra_info}")

def suppress_frequent_logs(interval_seconds: int = 300):
    """頻繁なログを抑制するデコレータ
    
    Args:
        interval_seconds: 抑制間隔（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global _log_suppression_cache
            current_time = time.time()
            cache_key = f"function_{func.__name__}"
            
            if cache_key in _log_suppression_cache:
                last_time = _log_suppression_cache[cache_key]['last_time']
                if current_time - last_time < interval_seconds:
                    return  # ログ出力をスキップ
            
            _log_suppression_cache[cache_key] = {'last_time': current_time}
            return func(*args, **kwargs)
        return wrapper
    return decorator
