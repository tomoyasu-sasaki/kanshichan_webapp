"""
Service Loader - サービスローダーモジュール

分析サービスのシングルトンインスタンス管理を提供
スレッドセーフな実装とエラーハンドリングを含む
"""

import logging
import threading
from typing import Dict, Any, Optional, TypeVar, Type

from flask import current_app
from utils.logger import setup_logger
from utils.exceptions import ServiceUnavailableError

logger = setup_logger(__name__)

T = TypeVar('T')

class ThreadSafeSingleton:
    """スレッドセーフなシングルトンベースクラス"""
    _instances: Dict[str, Any] = {}
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, service_class: Type[T], config: Optional[Dict[str, Any]] = None) -> Optional[T]:
        """シングルトンインスタンスを取得

        Args:
            service_class: サービスクラス
            config: 設定辞書（オプション）

        Returns:
            サービスインスタンス、または None（エラー時）
        """
        service_name = service_class.__name__
        
        if service_name not in cls._instances:
            with cls._lock:
                if service_name not in cls._instances:
                    try:
                        instance = service_class(config)
                        cls._instances[service_name] = instance
                        logger.info(f"{service_name} initialized successfully")
                    except Exception as e:
                        logger.error(f"Failed to initialize {service_name}: {e}")
                        return None
                        
        return cls._instances.get(service_name)


def get_advanced_behavior_analyzer() -> Optional[Any]:
    """AdvancedBehaviorAnalyzerインスタンスを取得（シングルトン）
    
    Flask アプリケーションコンテキストから設定を取得し、
    スレッドセーフなシングルトンインスタンスを返します。
    
    Returns:
        Optional[Any]: AdvancedBehaviorAnalyzerインスタンス、
                      またはNone（エラー時）
        
    Raises:
        ServiceUnavailableError: サービス初期化に失敗した場合
    """
    try:
        from services.ai.advanced_behavior_analyzer import AdvancedBehaviorAnalyzer
        
        # 設定取得
        config_manager = current_app.config.get('config_manager')
        if not config_manager:
            raise ServiceUnavailableError(
                "ConfigManager not available",
                details={'service': 'AdvancedBehaviorAnalyzer'}
            )
            
        config = config_manager.get_all()
        
        # シングルトンインスタンス取得
        instance = ThreadSafeSingleton.get_instance(AdvancedBehaviorAnalyzer, config)
        if not instance:
            raise ServiceUnavailableError(
                "Failed to initialize AdvancedBehaviorAnalyzer",
                details={'service': 'AdvancedBehaviorAnalyzer'}
            )
            
        return instance
        
    except ImportError as e:
        logger.error(f"Failed to import AdvancedBehaviorAnalyzer: {e}")
        raise ServiceUnavailableError(
            "AdvancedBehaviorAnalyzer module not available",
            details={'error': str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_advanced_behavior_analyzer: {e}")
        raise ServiceUnavailableError(
            "Failed to get AdvancedBehaviorAnalyzer instance",
            details={'error': str(e)}
        )


def get_pattern_recognizer() -> Optional[Any]:
    """PatternRecognizerインスタンスを取得（シングルトン）
    
    Flask アプリケーションコンテキストから設定を取得し、
    スレッドセーフなシングルトンインスタンスを返します。
    
    Returns:
        Optional[Any]: PatternRecognizerインスタンス、
                      またはNone（エラー時）
        
    Raises:
        ServiceUnavailableError: サービス初期化に失敗した場合
    """
    try:
        from services.ai.pattern_recognition import PatternRecognizer
        
        # 設定取得
        config_manager = current_app.config.get('config_manager')
        if not config_manager:
            raise ServiceUnavailableError(
                "ConfigManager not available",
                details={'service': 'PatternRecognizer'}
            )
            
        config = config_manager.get_all()
        
        # シングルトンインスタンス取得
        instance = ThreadSafeSingleton.get_instance(PatternRecognizer, config)
        if not instance:
            raise ServiceUnavailableError(
                "Failed to initialize PatternRecognizer",
                details={'service': 'PatternRecognizer'}
            )
            
        return instance
        
    except ImportError as e:
        logger.error(f"Failed to import PatternRecognizer: {e}")
        raise ServiceUnavailableError(
            "PatternRecognizer module not available",
            details={'error': str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_pattern_recognizer: {e}")
        raise ServiceUnavailableError(
            "Failed to get PatternRecognizer instance",
            details={'error': str(e)}
        ) 