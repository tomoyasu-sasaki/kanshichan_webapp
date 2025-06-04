"""
シリアライゼーションユーティリティ

MediaPipeオブジェクトなどのカスタムオブジェクトを
JSON安全な形式に変換するためのユーティリティ
"""

from typing import Any, Dict, List, Optional, Union
import json
import numpy as np
from utils.logger import setup_logger
from utils.exceptions import SerializationError, wrap_exception

logger = setup_logger(__name__)


def serialize_landmarks(landmarks_data: Any) -> Optional[List[Dict[str, float]]]:
    """MediaPipeランドマークデータをJSON安全な形式に変換
    
    Args:
        landmarks_data: MediaPipeのNormalizedLandmarkListまたはLandmarkListオブジェクト
        
    Returns:
        Optional[List[Dict]]: シリアライズされたランドマークデータ、失敗時はNone
    """
    if landmarks_data is None:
        return None
        
    try:
        # MediaPipeのNormalizedLandmarkListの場合
        if hasattr(landmarks_data, 'landmark'):
            return [
                {
                    'x': float(landmark.x),
                    'y': float(landmark.y),
                    'z': float(landmark.z) if hasattr(landmark, 'z') else 0.0,
                    'visibility': float(landmark.visibility) if hasattr(landmark, 'visibility') else 1.0
                }
                for landmark in landmarks_data.landmark
            ]
        
        # リスト形式のランドマーク（複数の手など）
        elif isinstance(landmarks_data, list):
            serialized_list = []
            for landmark_set in landmarks_data:
                if hasattr(landmark_set, 'landmark'):
                    serialized_landmarks = [
                        {
                            'x': float(landmark.x),
                            'y': float(landmark.y),
                            'z': float(landmark.z) if hasattr(landmark, 'z') else 0.0,
                            'visibility': float(landmark.visibility) if hasattr(landmark, 'visibility') else 1.0
                        }
                        for landmark in landmark_set.landmark
                    ]
                    serialized_list.append(serialized_landmarks)
            return serialized_list
        
        # 既にシリアライズ済みの場合
        elif isinstance(landmarks_data, (list, dict)):
            return landmarks_data
            
        else:
            logger.warning(f"Unknown landmark data type: {type(landmarks_data)}")
            return None
            
    except Exception as e:
        serialization_error = wrap_exception(
            e, SerializationError,
            "Failed to serialize landmark data",
            details={
                'data_type': str(type(landmarks_data)),
                'has_landmark_attr': hasattr(landmarks_data, 'landmark') if landmarks_data else False
            }
        )
        logger.error(f"Landmark serialization error: {serialization_error.to_dict()}")
        return None


def serialize_detection_results(detection_results: Dict[str, Any]) -> Dict[str, Any]:
    """検出結果を完全にJSON安全な形式に変換
    
    Args:
        detection_results: 検出結果の辞書
        
    Returns:
        Dict[str, Any]: シリアライズされた検出結果
    """
    try:
        serialized_results = {}
        
        for key, value in detection_results.items():
            if key in ['pose_landmarks', 'hands_landmarks', 'face_landmarks']:
                # MediaPipeランドマークの変換
                serialized_results[key] = serialize_landmarks(value)
            elif key == 'landmarks' and isinstance(value, dict):
                # 統合ランドマーク辞書の変換
                serialized_landmarks = {}
                for landmark_type, landmark_data in value.items():
                    serialized_landmarks[landmark_type] = serialize_landmarks(landmark_data)
                serialized_results[key] = serialized_landmarks
            elif isinstance(value, np.ndarray):
                # NumPy配列の変換
                serialized_results[key] = value.tolist()
            elif isinstance(value, (np.integer, np.floating)):
                # NumPyスカラーの変換
                serialized_results[key] = value.item()
            else:
                # その他のデータは通常のJSON処理
                try:
                    json.dumps(value)  # JSON変換可能性をテスト
                    serialized_results[key] = value
                except (TypeError, ValueError):
                    # JSON変換不可能な場合は文字列に変換
                    serialized_results[key] = str(value)
                    logger.debug(f"Converted non-serializable value to string: {key}")
        
        logger.debug(f"Successfully serialized detection results with {len(serialized_results)} keys")
        return serialized_results
        
    except Exception as e:
        serialization_error = wrap_exception(
            e, SerializationError,
            "Failed to serialize detection results",
            details={
                'original_keys': list(detection_results.keys()) if detection_results else [],
                'fallback_serialization': True
            }
        )
        logger.error(f"Detection results serialization error: {serialization_error.to_dict()}")
        
        # フォールバック: 基本的な情報のみ保持
        return {
            'person_detected': detection_results.get('person_detected', False),
            'smartphone_detected': detection_results.get('smartphone_detected', False),
            'error': 'serialization_failed',
            'timestamp': detection_results.get('timestamp')
        }


def safe_json_serialize(data: Any) -> str:
    """オブジェクトを安全にJSONにシリアライズ
    
    Args:
        data: シリアライズするデータ
        
    Returns:
        str: JSON文字列
    """
    try:
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    except Exception as e:
        logger.error(f"Safe JSON serialization failed: {e}")
        return json.dumps({
            'error': 'serialization_failed',
            'type': str(type(data)),
            'message': str(e)
        })


class MediaPipeJSONEncoder(json.JSONEncoder):
    """MediaPipeオブジェクト対応のカスタムJSONエンコーダー"""
    
    def default(self, obj):
        """カスタムオブジェクトのエンコーディング処理
        
        Args:
            obj: エンコード対象オブジェクト
            
        Returns:
            エンコード結果
        """
        # MediaPipeランドマークオブジェクト
        if hasattr(obj, 'landmark'):
            return serialize_landmarks(obj)
        
        # NumPy配列
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        
        # NumPyスカラー
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        
        # その他のオブジェクトはデフォルト処理
        else:
            return super().default(obj)


def create_websocket_safe_status(status_data: Dict[str, Any]) -> Dict[str, Any]:
    """WebSocket送信に安全なステータスデータを作成
    
    Args:
        status_data: 元のステータスデータ
        
    Returns:
        Dict[str, Any]: WebSocket送信可能なステータスデータ
    """
    try:
        # 検出結果の安全化
        safe_status = serialize_detection_results(status_data.copy())
        
        # タイムスタンプの追加
        if 'timestamp' not in safe_status:
            from datetime import datetime
            safe_status['timestamp'] = datetime.now().isoformat()
        
        # WebSocket送信サイズの最適化
        if len(json.dumps(safe_status)) > 100000:  # 100KB制限
            logger.warning("Status data too large for WebSocket, applying compression")
            # 大きすぎる場合は重要な情報のみ保持
            safe_status = {
                'person_detected': safe_status.get('person_detected', False),
                'smartphone_detected': safe_status.get('smartphone_detected', False),
                'presence_status': safe_status.get('presence_status', 'unknown'),
                'timestamp': safe_status.get('timestamp'),
                'compressed': True
            }
        
        return safe_status
        
    except Exception as e:
        logger.error(f"Failed to create WebSocket safe status: {e}")
        return {
            'error': 'status_creation_failed',
            'timestamp': status_data.get('timestamp')
        } 