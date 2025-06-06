"""
検出結果平滑化システム - DetectionSmoother

バウンディングボックス点滅現象を抑制するため、検出結果の継続性を管理し、
前フレームとの補間やヒステリシス制御を実装します。

主要機能:
- 検出結果の時系列管理
- バウンディングボックス位置の平滑化
- 検出信頼度のヒステリシス制御
- フレームスキップ対応の結果保持
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import numpy as np
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    SmoothingError, ValidationError, ConfigError,
    wrap_exception
)

logger = setup_logger(__name__)


@dataclass
class DetectionHistory:
    """検出履歴を管理するデータクラス"""
    bbox: Tuple[int, int, int, int]
    confidence: float
    timestamp: float
    frame_count: int
    last_seen: float = field(default_factory=time.time)
    
    def age_seconds(self) -> float:
        """検出からの経過時間（秒）"""
        return time.time() - self.last_seen
        
    def is_expired(self, max_age_seconds: float) -> bool:
        """検出が期限切れかどうか"""
        return self.age_seconds() > max_age_seconds


class DetectionSmoother:
    """
    検出結果平滑化メインクラス
    
    バウンディングボックスの点滅を抑制し、検出の連続性を維持します。
    フレームスキップやAI最適化システムと連携して動作します。
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        try:
            self.config_manager = config_manager
            
            # 平滑化設定の読み込み
            self._load_smoothing_settings()
            
            # 検出履歴の管理
            self.detection_history: Dict[str, List[DetectionHistory]] = defaultdict(list)
            self.frame_counter = 0
            self.last_update_time = time.time()
            
            # パフォーマンス統計
            self.smoothing_stats = {
                'smoothed_detections': 0,
                'interpolated_detections': 0,
                'expired_cleanups': 0,
                'total_processed': 0
            }
            
            logger.info("DetectionSmoother initialized successfully")
            
        except Exception as e:
            smoothing_error = wrap_exception(
                e, SmoothingError,
                "DetectionSmoother initialization failed",
                details={'smoothing_disabled': True}
            )
            logger.error(f"DetectionSmoother error: {smoothing_error.to_dict()}")
            raise smoothing_error
            
    def _load_smoothing_settings(self) -> None:
        """平滑化設定の読み込み（AIOptimizer連携強化版）"""
        # デフォルト設定
        self.max_history_age = 2.0  # 検出履歴の最大保持時間（秒）
        self.position_smoothing_factor = 0.3  # 位置の平滑化係数
        self.confidence_hysteresis_low = 0.3  # 信頼度下限閾値
        self.confidence_hysteresis_high = 0.5  # 信頼度上限閾値
        self.max_interpolation_frames = 5  # 最大補間フレーム数（基本値）
        self.bbox_distance_threshold = 100  # バウンディングボックス距離閾値
        
        if not self.config_manager:
            return
            
        try:
            # 設定ファイルから読み込み
            smoothing_config = self.config_manager.get('detection_smoothing', {})
            
            self.max_history_age = smoothing_config.get('max_history_age', self.max_history_age)
            self.position_smoothing_factor = smoothing_config.get('position_smoothing_factor', self.position_smoothing_factor)
            self.confidence_hysteresis_low = smoothing_config.get('confidence_hysteresis_low', self.confidence_hysteresis_low)
            self.confidence_hysteresis_high = smoothing_config.get('confidence_hysteresis_high', self.confidence_hysteresis_high)
            self.max_interpolation_frames = smoothing_config.get('max_interpolation_frames', self.max_interpolation_frames)
            self.bbox_distance_threshold = smoothing_config.get('bbox_distance_threshold', self.bbox_distance_threshold)
            
            # 🆕 AIOptimizerのmax_skip_rateと連携した動的制限
            ai_max_skip_rate = self.config_manager.get('optimization.max_skip_rate', 5)
            # 最大スキップレートの1.5倍まで補間を許可
            dynamic_max_interpolation = int(ai_max_skip_rate * 1.5)
            self.max_interpolation_frames = max(self.max_interpolation_frames, dynamic_max_interpolation)
            
            # 🆕 拡張補間のための設定
            self.extended_interpolation_frames = int(self.max_interpolation_frames * 2)  # 拡張補間の最大フレーム数
            self.min_decay_confidence = 0.05  # 最小信頼度（拡張補間時）
            
            logger.info(f"Smoothing settings loaded: history_age={self.max_history_age}s, "
                       f"smoothing_factor={self.position_smoothing_factor}, "
                       f"max_interpolation={self.max_interpolation_frames}, "
                       f"extended_interpolation={self.extended_interpolation_frames}")
                       
        except Exception as e:
            config_error = wrap_exception(
                e, ConfigError,
                "Failed to load detection smoothing settings",
                details={'using_defaults': True}
            )
            logger.warning(f"Using default smoothing settings: {config_error.to_dict()}")
            
    def smooth_detections(self, current_detections: Dict[str, Any]) -> Dict[str, Any]:
        """
        検出結果を平滑化
        
        Args:
            current_detections: 現在フレームの検出結果
            
        Returns:
            平滑化済みの検出結果
        """
        try:
            self.frame_counter += 1
            current_time = time.time()
            self.last_update_time = current_time
            
            # 古い検出履歴をクリーンアップ
            self._cleanup_expired_history()
            
            # 検出結果の平滑化処理
            smoothed_detections = {}
            
            for obj_key, detections in current_detections.get('detections', {}).items():
                if not detections:
                    # 現在フレームで検出されない場合の補間処理
                    interpolated = self._interpolate_missing_detection(obj_key)
                    if interpolated:
                        smoothed_detections[obj_key] = interpolated
                    continue
                    
                # 現在フレームの検出を平滑化
                smoothed_list = []
                for detection in detections:
                    smoothed_detection = self._smooth_single_detection(obj_key, detection, current_time)
                    if smoothed_detection:
                        smoothed_list.append(smoothed_detection)
                        
                if smoothed_list:
                    smoothed_detections[obj_key] = smoothed_list
            
            # 結果を更新
            result = current_detections.copy()
            result['detections'] = smoothed_detections
            
            self.smoothing_stats['total_processed'] += 1
            
            return result
            
        except Exception as e:
            smoothing_error = wrap_exception(
                e, SmoothingError,
                "Detection smoothing failed",
                details={
                    'frame_counter': self.frame_counter,
                    'fallback_to_original': True
                }
            )
            logger.error(f"Smoothing error: {smoothing_error.to_dict()}")
            # エラー時は元の検出結果を返す
            return current_detections
            
    def _smooth_single_detection(self, obj_key: str, detection: Dict[str, Any], current_time: float) -> Optional[Dict[str, Any]]:
        """
        単一検出結果の平滑化
        
        Args:
            obj_key: オブジェクトキー
            detection: 検出結果
            current_time: 現在時刻
            
        Returns:
            平滑化済み検出結果
        """
        bbox = detection.get('bbox')
        confidence = detection.get('confidence', 0.0)
        
        if not bbox or len(bbox) != 4:
            return None
            
        try:
            x1, y1, x2, y2 = map(int, bbox)
            
            # 信頼度によるヒステリシス制御
            if not self._should_accept_detection(obj_key, confidence):
                return None
                
            # 前フレームとの位置平滑化
            smoothed_bbox = self._smooth_bbox_position(obj_key, (x1, y1, x2, y2))
            
            # 検出履歴を更新
            history_entry = DetectionHistory(
                bbox=smoothed_bbox,
                confidence=confidence,
                timestamp=current_time,
                frame_count=self.frame_counter,
                last_seen=current_time
            )
            
            self.detection_history[obj_key].append(history_entry)
            
            # 履歴サイズの制限
            if len(self.detection_history[obj_key]) > 10:
                self.detection_history[obj_key] = self.detection_history[obj_key][-10:]
                
            self.smoothing_stats['smoothed_detections'] += 1
            
            return {
                'bbox': smoothed_bbox,
                'confidence': confidence,
                'smoothed': True
            }
            
        except (ValueError, TypeError) as e:
            bbox_error = wrap_exception(
                e, ValidationError,
                "Invalid bbox format for smoothing",
                details={
                    'bbox': bbox,
                    'object_key': obj_key,
                    'detection': detection
                }
            )
            logger.warning(f"Bbox smoothing error: {bbox_error.to_dict()}")
            return None
            
    def _should_accept_detection(self, obj_key: str, confidence: float) -> bool:
        """
        ヒステリシス制御による検出受諾判定
        
        Args:
            obj_key: オブジェクトキー
            confidence: 検出信頼度
            
        Returns:
            検出を受諾するかどうか
        """
        recent_history = [h for h in self.detection_history[obj_key] 
                         if not h.is_expired(self.max_history_age)]
        
        if not recent_history:
            # 履歴がない場合は高い閾値を使用
            return confidence >= self.confidence_hysteresis_high
        else:
            # 履歴がある場合は低い閾値を使用（継続性重視）
            return confidence >= self.confidence_hysteresis_low
            
    def _smooth_bbox_position(self, obj_key: str, current_bbox: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """
        バウンディングボックス位置の平滑化
        
        Args:
            obj_key: オブジェクトキー
            current_bbox: 現在のバウンディングボックス
            
        Returns:
            平滑化済みバウンディングボックス
        """
        recent_history = [h for h in self.detection_history[obj_key] 
                         if not h.is_expired(self.max_history_age)]
        
        if not recent_history:
            return current_bbox
            
        # 最も近い履歴を取得
        latest_history = recent_history[-1]
        prev_bbox = latest_history.bbox
        
        # バウンディングボックス間の距離をチェック
        if self._bbox_distance(current_bbox, prev_bbox) > self.bbox_distance_threshold:
            # 距離が大きすぎる場合は平滑化しない（別オブジェクトの可能性）
            return current_bbox
            
        # 線形補間による平滑化
        alpha = self.position_smoothing_factor
        
        smoothed_x1 = int(prev_bbox[0] * (1 - alpha) + current_bbox[0] * alpha)
        smoothed_y1 = int(prev_bbox[1] * (1 - alpha) + current_bbox[1] * alpha)
        smoothed_x2 = int(prev_bbox[2] * (1 - alpha) + current_bbox[2] * alpha)
        smoothed_y2 = int(prev_bbox[3] * (1 - alpha) + current_bbox[3] * alpha)
        
        return (smoothed_x1, smoothed_y1, smoothed_x2, smoothed_y2)
        
    def _bbox_distance(self, bbox1: Tuple[int, int, int, int], bbox2: Tuple[int, int, int, int]) -> float:
        """
        バウンディングボックス間の距離計算
        
        Args:
            bbox1: バウンディングボックス1
            bbox2: バウンディングボックス2
            
        Returns:
            中心点間の距離
        """
        # 中心点を計算
        center1_x = (bbox1[0] + bbox1[2]) / 2
        center1_y = (bbox1[1] + bbox1[3]) / 2
        center2_x = (bbox2[0] + bbox2[2]) / 2
        center2_y = (bbox2[1] + bbox2[3]) / 2
        
        # ユークリッド距離
        return np.sqrt((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2)
        
    def _interpolate_missing_detection(self, obj_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        検出されなかった物体の補間処理（継続性強化版）
        
        Args:
            obj_key: オブジェクトキー
            
        Returns:
            補間された検出結果
        """
        recent_history = [h for h in self.detection_history[obj_key] 
                         if not h.is_expired(self.max_history_age)]
        
        if not recent_history:
            return None
            
        latest_history = recent_history[-1]
        frames_since_detection = self.frame_counter - latest_history.frame_count
        
        # 🆕 段階的な信頼度減衰による長期補間
        interpolated_confidence = None
        is_extended_interpolation = False
        
        if frames_since_detection <= self.max_interpolation_frames:
            # 通常の補間処理
            decay_factor = max(0.1, 1.0 - (frames_since_detection * 0.15))
            interpolated_confidence = latest_history.confidence * decay_factor
            
        elif frames_since_detection <= self.extended_interpolation_frames:
            # 🆕 拡張補間: より強い減衰だが継続
            decay_factor = max(self.min_decay_confidence / latest_history.confidence, 
                              0.3 - (frames_since_detection * 0.02))
            interpolated_confidence = latest_history.confidence * decay_factor
            is_extended_interpolation = True
            
        else:
            # 制限超過で補間停止
            return None
        
        # 最小信頼度のチェック
        min_threshold = self.min_decay_confidence if is_extended_interpolation else self.confidence_hysteresis_low
        if interpolated_confidence < min_threshold:
            return None
            
        # 統計更新
        if is_extended_interpolation:
            self.smoothing_stats['extended_interpolations'] = self.smoothing_stats.get('extended_interpolations', 0) + 1
            logger.debug(f"Extended interpolation for {obj_key}: frames={frames_since_detection}, confidence={interpolated_confidence:.3f}")
        else:
            self.smoothing_stats['interpolated_detections'] += 1
        
        return [{
            'bbox': latest_history.bbox,
            'confidence': interpolated_confidence,
            'interpolated': True,
            'frames_interpolated': frames_since_detection,
            'extended_interpolation': is_extended_interpolation
        }]
        
    def _cleanup_expired_history(self) -> None:
        """期限切れの検出履歴をクリーンアップ"""
        cleanup_count = 0
        
        for obj_key in list(self.detection_history.keys()):
            original_count = len(self.detection_history[obj_key])
            self.detection_history[obj_key] = [
                h for h in self.detection_history[obj_key] 
                if not h.is_expired(self.max_history_age)
            ]
            cleanup_count += original_count - len(self.detection_history[obj_key])
            
            # 空のリストは削除
            if not self.detection_history[obj_key]:
                del self.detection_history[obj_key]
                
        if cleanup_count > 0:
            self.smoothing_stats['expired_cleanups'] += cleanup_count
            logger.debug(f"Cleaned up {cleanup_count} expired detection entries")
            
    def get_smoothing_stats(self) -> Dict[str, Any]:
        """
        平滑化統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        stats = self.smoothing_stats.copy()
        stats.update({
            'frame_counter': self.frame_counter,
            'active_objects': len(self.detection_history),
            'total_history_entries': sum(len(h) for h in self.detection_history.values()),
            'settings': {
                'max_history_age': self.max_history_age,
                'position_smoothing_factor': self.position_smoothing_factor,
                'confidence_hysteresis_low': self.confidence_hysteresis_low,
                'confidence_hysteresis_high': self.confidence_hysteresis_high,
                'max_interpolation_frames': self.max_interpolation_frames,
                # 🆕 拡張補間設定も含める
                'extended_interpolation_frames': getattr(self, 'extended_interpolation_frames', self.max_interpolation_frames * 2),
                'min_decay_confidence': getattr(self, 'min_decay_confidence', 0.05)
            }
        })
        return stats
        
    def reset_history(self) -> None:
        """検出履歴をリセット"""
        self.detection_history.clear()
        self.frame_counter = 0
        logger.info("Detection history reset")
        
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """
        平滑化設定を動的更新
        
        Args:
            new_settings: 新しい設定
        """
        try:
            if 'max_history_age' in new_settings:
                self.max_history_age = new_settings['max_history_age']
            if 'position_smoothing_factor' in new_settings:
                self.position_smoothing_factor = new_settings['position_smoothing_factor']
            if 'confidence_hysteresis_low' in new_settings:
                self.confidence_hysteresis_low = new_settings['confidence_hysteresis_low']
            if 'confidence_hysteresis_high' in new_settings:
                self.confidence_hysteresis_high = new_settings['confidence_hysteresis_high']
            if 'max_interpolation_frames' in new_settings:
                self.max_interpolation_frames = new_settings['max_interpolation_frames']
                
            logger.info(f"Detection smoothing settings updated: {new_settings}")
            
        except Exception as e:
            settings_error = wrap_exception(
                e, ConfigError,
                "Failed to update smoothing settings",
                details={'rejected_settings': new_settings}
            )
            logger.error(f"Settings update error: {settings_error.to_dict()}") 