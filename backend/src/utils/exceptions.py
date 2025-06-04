"""
KanshiChan カスタム例外クラス

プロジェクト専用の例外体系を提供します。
適切な例外処理により、デバッグ効率とユーザビリティを向上させます。
"""

from typing import Optional, Any, Dict


class KanshiChanError(Exception):
    """
    KanshiChan プロジェクトのベース例外クラス
    
    全てのカスタム例外の基底クラスです。
    共通的なエラー情報管理機能を提供します。
    """
    
    def __init__(self, 
                 message: str,
                 error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None,
                 original_exception: Optional[Exception] = None):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            error_code: エラーコード（ログ・追跡用）
            details: 追加詳細情報
            original_exception: 元の例外（チェイン用）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_exception = original_exception
    
    def to_dict(self) -> Dict[str, Any]:
        """例外情報を辞書形式で取得"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }


# ========== 設定・構成関連例外 ==========

class ConfigError(KanshiChanError):
    """設定関連のエラー"""
    pass


class ConfigLoadError(ConfigError):
    """設定ファイル読み込みエラー"""
    pass


class ConfigSaveError(ConfigError):
    """設定ファイル保存エラー"""
    pass


class ConfigValidationError(ConfigError):
    """設定値検証エラー"""
    pass


class YamlError(ConfigError):
    """YAML処理エラー"""
    pass


# ========== ハードウェア関連例外 ==========

class HardwareError(KanshiChanError):
    """ハードウェア関連のエラー"""
    pass


class CameraError(HardwareError):
    """カメラ関連エラー"""
    pass


class CameraInitializationError(CameraError):
    """カメラ初期化エラー"""
    pass


class CameraFrameError(CameraError):
    """カメラフレーム取得エラー"""
    pass


class AudioError(HardwareError):
    """音声関連エラー"""
    pass


class AudioPlaybackError(AudioError):
    """音声再生エラー"""
    pass


class AudioFileError(AudioError):
    """音声ファイルエラー"""
    pass


# ========== AI/ML処理関連例外 ==========

class AIProcessingError(KanshiChanError):
    """AI/ML処理関連のエラー"""
    pass


class ModelError(AIProcessingError):
    """機械学習モデル関連エラー"""
    pass


class ModelInitializationError(ModelError):
    """モデル初期化エラー"""
    pass


class ModelInferenceError(ModelError):
    """モデル推論エラー"""
    pass


class YOLOError(ModelError):
    """YOLO関連エラー"""
    pass


class MediaPipeError(ModelError):
    """MediaPipe関連エラー"""
    pass


class LLMError(ModelError):
    """LLM（大規模言語モデル）関連エラー"""
    pass


class DetectionError(AIProcessingError):
    """物体検出関連エラー"""
    pass


class RenderingError(AIProcessingError):
    """描画処理関連エラー"""
    pass


class SmoothingError(AIProcessingError):
    """検出結果平滑化関連エラー"""
    pass


# ========== ネットワーク・通信関連例外 ==========

class NetworkError(KanshiChanError):
    """ネットワーク関連のエラー"""
    pass


class APIError(NetworkError):
    """API関連エラー"""
    pass


class WebSocketError(NetworkError):
    """WebSocket関連エラー"""
    pass


class LineAPIError(APIError):
    """LINE API関連エラー"""
    pass


class HTTPError(NetworkError):
    """HTTP通信エラー"""
    pass


# ========== ファイル・データ関連例外 ==========

class FileOperationError(KanshiChanError):
    """ファイル操作関連のエラー"""
    pass


class FileNotFoundError(FileOperationError):
    """ファイルが見つからないエラー"""
    pass


class FileReadError(FileOperationError):
    """ファイル読み込みエラー"""
    pass


class FileWriteError(FileOperationError):
    """ファイル書き込みエラー"""
    pass


class DataParsingError(KanshiChanError):
    """データ解析関連のエラー"""
    pass


class JSONParsingError(DataParsingError):
    """JSON解析エラー"""
    pass


class YAMLParsingError(DataParsingError):
    """YAML解析エラー"""
    pass


class SerializationError(KanshiChanError):
    """データシリアライゼーション関連のエラー"""
    pass


# ========== バリデーション・入力関連例外 ==========

class ValidationError(KanshiChanError):
    """バリデーション関連のエラー"""
    pass


class InputValidationError(ValidationError):
    """入力値検証エラー"""
    pass


class TypeValidationError(ValidationError):
    """型検証エラー"""
    pass


class RangeValidationError(ValidationError):
    """範囲検証エラー"""
    pass


# ========== 状態・ライフサイクル関連例外 ==========

class StateError(KanshiChanError):
    """システム状態関連のエラー"""
    pass


class InitializationError(StateError):
    """初期化関連エラー"""
    pass


class ShutdownError(StateError):
    """終了処理関連エラー"""
    pass


class ResourceError(StateError):
    """リソース関連エラー"""
    pass


class ResourceUnavailableError(ResourceError):
    """リソースが利用できないエラー"""
    pass


class ServiceUnavailableError(ResourceError):
    """サービスが利用できないエラー"""
    pass


class ResourceExhaustionError(ResourceError):
    """リソース枯渇エラー"""
    pass


# ========== スケジュール・タスク関連例外 ==========

class ScheduleError(KanshiChanError):
    """スケジュール関連のエラー"""
    pass


class ScheduleValidationError(ScheduleError):
    """スケジュール検証エラー"""
    pass


class ScheduleExecutionError(ScheduleError):
    """スケジュール実行エラー"""
    pass


class TaskError(KanshiChanError):
    """タスク実行関連のエラー"""
    pass


# ========== アラート・通知関連例外 ==========

class AlertError(KanshiChanError):
    """アラート関連のエラー"""
    pass


class AlertDeliveryError(AlertError):
    """アラート配信エラー"""
    pass


class NotificationError(KanshiChanError):
    """通知関連のエラー"""
    pass


# ========== パフォーマンス・最適化関連例外 ==========

class PerformanceError(KanshiChanError):
    """パフォーマンス関連のエラー"""
    pass


class OptimizationError(PerformanceError):
    """最適化処理エラー"""
    pass


class MemoryError(PerformanceError):
    """メモリ関連エラー"""
    pass


class FrameSkipError(PerformanceError):
    """フレームスキップ処理エラー"""
    pass


class BatchProcessingError(PerformanceError):
    """バッチ処理エラー"""
    pass


# ========== 例外ヘルパー関数 ==========

def wrap_exception(original_exception: Exception, 
                   custom_exception_class: type = KanshiChanError,
                   message: Optional[str] = None,
                   error_code: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None) -> KanshiChanError:
    """
    既存の例外をKanshiChanカスタム例外でラップする
    
    Args:
        original_exception: 元の例外
        custom_exception_class: ラップ先のカスタム例外クラス
        message: カスタムメッセージ（指定されない場合は元の例外メッセージを使用）
        error_code: エラーコード
        details: 追加詳細情報
        
    Returns:
        カスタム例外インスタンス
    """
    if message is None:
        message = str(original_exception)
    
    return custom_exception_class(
        message=message,
        error_code=error_code,
        details=details,
        original_exception=original_exception
    )


def create_error_response(exception: KanshiChanError, 
                         include_details: bool = False) -> Dict[str, Any]:
    """
    例外からAPI用エラーレスポンスを生成する
    
    Args:
        exception: KanshiChanカスタム例外
        include_details: 詳細情報を含めるかどうか
        
    Returns:
        エラーレスポンス辞書
    """
    response = {
        'success': False,
        'error': {
            'type': exception.__class__.__name__,
            'code': exception.error_code,
            'message': exception.message
        }
    }
    
    if include_details and exception.details:
        response['error']['details'] = exception.details
    
    return response 