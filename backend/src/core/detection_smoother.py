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
from copy import deepcopy

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
            
            # デフォルト設定
            self.settings = {
                # ヒステリシス制御設定
                'hysteresis': {
                    'high_threshold': 0.65,  # 検出を開始する高い閾値
                    'low_threshold': 0.35,   # 検出を維持する低い閾値
                    'enabled': True,
                },
                
                # 移動平均フィルタ設定
                'moving_average': {
                    'window_size': 5,  # 移動平均のウィンドウサイズ
                    'weight_recent': 2.0,  # 最新フレームの重み（通常の2倍）
                    'enabled': True,
                },
                
                # 欠損フレーム補間設定
                'interpolation': {
                    'max_missing_frames': 3,  # 補間する最大欠損フレーム数
                    'fade_out_factor': 0.85,  # 信頼度の減衰係数（フェードアウト）
                    'enabled': True,
                },
            }
            
            # 設定の読み込み
            if config_manager:
                self._load_settings()
            
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
            
            # 移動平均用バッファ（オブジェクト種別ごと）
            self.detection_buffers = defaultdict(lambda: deque(maxlen=self.settings['moving_average']['window_size']))
            
            # 最後の検出状態（欠損フレーム補間用）
            self.last_detections = {}
            self.missing_frame_counters = defaultdict(int)
            
            # 特殊フラグ状態
            self.currently_tracking = defaultdict(bool)  # 現在追跡中かどうか
            
            logger.info("DetectionSmoother initialized successfully")
            
        except Exception as e:
            smoothing_error = wrap_exception(
                e, SmoothingError,
                "DetectionSmoother initialization failed",
                details={'smoothing_disabled': True}
            )
            logger.error(f"DetectionSmoother error: {smoothing_error.to_dict()}")
            raise smoothing_error
            
    def _load_settings(self) -> None:
        """設定を読み込む"""
        try:
            # ヒステリシス設定
            if self.config_manager.has('detection_smoother.hysteresis'):
                hysteresis_config = self.config_manager.get('detection_smoother.hysteresis', {})
                self.settings['hysteresis'].update(hysteresis_config)
            
            # 移動平均フィルタ設定
            if self.config_manager.has('detection_smoother.moving_average'):
                ma_config = self.config_manager.get('detection_smoother.moving_average', {})
                self.settings['moving_average'].update(ma_config)
                
                # バッファサイズの更新
                new_window_size = self.settings['moving_average']['window_size']
                for obj_key in self.detection_buffers:
                    self.detection_buffers[obj_key] = deque(
                        list(self.detection_buffers[obj_key])[-new_window_size:] 
                        if self.detection_buffers[obj_key] else [], 
                        maxlen=new_window_size
                    )
            
            # 欠損フレーム補間設定
            if self.config_manager.has('detection_smoother.interpolation'):
                interp_config = self.config_manager.get('detection_smoother.interpolation', {})
                self.settings['interpolation'].update(interp_config)
                
            logger.info("Detection smoother settings loaded successfully")
            
        except Exception as e:
            config_error = wrap_exception(
                e, ConfigError,
                "Failed to load detection smoother settings",
                details={'using_default_settings': True}
            )
            logger.warning(f"Configuration error: {config_error.to_dict()}")
    
    def smooth_detections(self, detection_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        検出結果を平滑化
        
        Args:
            detection_results: 元の検出結果
            
        Returns:
            Dict[str, Any]: 平滑化された検出結果
        """
        # 結果のディープコピーを作成
        smoothed_results = deepcopy(detection_results)
        
        # detections が存在しない場合は処理しない
        if 'detections' not in smoothed_results:
            return smoothed_results
            
        # 各オブジェクトタイプに対して処理
        for obj_key, detections in list(smoothed_results['detections'].items()):
            if not detections:
                # 欠損フレーム補間処理
                interpolated_detections = self._interpolate_missing_detections(obj_key)
                if interpolated_detections:
                    smoothed_results['detections'][obj_key] = interpolated_detections
                    logger.debug(f"Interpolated missing detections for {obj_key}")
                else:
                    # 補間できない場合は削除
                    if obj_key in smoothed_results['detections']:
                        del smoothed_results['detections'][obj_key]
                continue
                
            # 検出が存在する場合、移動平均フィルタと信頼度ヒステリシス処理を適用
            filtered_detections = []
            
            for detection in detections:
                # 信頼度ヒステリシス制御（検出を受け入れるかどうか判断）
                if self._should_accept_detection(obj_key, detection):
                    # 検出バウンディングボックスの移動平均フィルタ適用
                    smoothed_detection = self._apply_moving_average(obj_key, detection)
                    filtered_detections.append(smoothed_detection)
                    
                    # 欠損フレームカウンタをリセット
                    self.missing_frame_counters[obj_key] = 0
                    
                    # 最新の検出を保存（補間用）
                    self.last_detections[obj_key] = detections
            
            if filtered_detections:
                smoothed_results['detections'][obj_key] = filtered_detections
            else:
                # 平滑化後に検出が消えた場合は欠損フレーム補間を試みる
                interpolated_detections = self._interpolate_missing_detections(obj_key)
                if interpolated_detections:
                    smoothed_results['detections'][obj_key] = interpolated_detections
                else:
                    # 補間できない場合は削除
                    if obj_key in smoothed_results['detections']:
                        del smoothed_results['detections'][obj_key]
        
        return smoothed_results
    
    def _should_accept_detection(self, obj_key: str, detection: Dict[str, Any]) -> bool:
        """
        信頼度ヒステリシス制御による検出フィルタリング
        
        Args:
            obj_key: オブジェクト種別キー
            detection: 検出結果
            
        Returns:
            bool: 検出を受け入れるかどうか
        """
        if not self.settings['hysteresis']['enabled']:
            return True
            
        confidence = detection.get('confidence', 0.0)
        high_threshold = self.settings['hysteresis']['high_threshold']
        low_threshold = self.settings['hysteresis']['low_threshold']
        
        # 現在追跡中かどうかで閾値を変える（ヒステリシス制御）
        if self.currently_tracking[obj_key]:
            # 追跡中なら低い閾値でも検出を維持
            accept = confidence >= low_threshold
            if not accept:
                logger.debug(f"Dropping {obj_key} detection: confidence {confidence:.3f} < low_threshold {low_threshold}")
                self.currently_tracking[obj_key] = False
        else:
            # 未追跡なら高い閾値で検出を開始
            accept = confidence >= high_threshold
            if accept:
                logger.debug(f"Starting tracking {obj_key}: confidence {confidence:.3f} >= high_threshold {high_threshold}")
                self.currently_tracking[obj_key] = True
                
        return accept
    
    def _apply_moving_average(self, obj_key: str, detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        検出バウンディングボックスに移動平均フィルタを適用
        
        Args:
            obj_key: オブジェクト種別キー
            detection: 検出結果
            
        Returns:
            Dict[str, Any]: 平滑化された検出結果
        """
        if not self.settings['moving_average']['enabled']:
            return detection
            
        # 検出バッファを更新
        self.detection_buffers[obj_key].append(detection)
        
        # バッファが空の場合は元の検出をそのまま返す
        if not self.detection_buffers[obj_key]:
            return detection
            
        # 最新のフレームに大きな重みを与える重み付き移動平均
        weight_recent = self.settings['moving_average']['weight_recent']
        bboxes = []
        confidences = []
        total_weight = 0
        
        # バッファ内の検出に対して処理
        buffer = list(self.detection_buffers[obj_key])
        for i, det in enumerate(buffer):
            # 最新フレームには大きな重みを付与
            weight = weight_recent if i == len(buffer) - 1 else 1.0
            total_weight += weight
            
            bbox = det.get('bbox', (0, 0, 0, 0))
            confidence = det.get('confidence', 0.0)
            
            bboxes.append((bbox[0] * weight, bbox[1] * weight, 
                           bbox[2] * weight, bbox[3] * weight))
            confidences.append(confidence * weight)
        
        # 正規化
        if total_weight > 0:
            avg_bbox = (
                int(sum(bbox[0] for bbox in bboxes) / total_weight),
                int(sum(bbox[1] for bbox in bboxes) / total_weight),
                int(sum(bbox[2] for bbox in bboxes) / total_weight),
                int(sum(bbox[3] for bbox in bboxes) / total_weight)
            )
            avg_confidence = sum(confidences) / total_weight
        else:
            # 重みがゼロの場合は元の検出を使用
            avg_bbox = detection.get('bbox', (0, 0, 0, 0))
            avg_confidence = detection.get('confidence', 0.0)
        
        # 平滑化された検出結果を作成
        smoothed_detection = deepcopy(detection)
        smoothed_detection['bbox'] = avg_bbox
        smoothed_detection['confidence'] = avg_confidence
        smoothed_detection['smoothed'] = True
        
        return smoothed_detection
    
    def _interpolate_missing_detections(self, obj_key: str) -> List[Dict[str, Any]]:
        """
        欠損フレームの検出結果を補間
        
        Args:
            obj_key: オブジェクト種別キー
            
        Returns:
            List[Dict[str, Any]]: 補間された検出結果のリスト（空の場合は補間不可）
        """
        if not self.settings['interpolation']['enabled']:
            return []
            
        # 欠損フレームカウンタを増加
        self.missing_frame_counters[obj_key] += 1
        
        # 欠損フレーム数が上限を超えたら補間しない
        max_missing = self.settings['interpolation']['max_missing_frames']
        if self.missing_frame_counters[obj_key] > max_missing:
            logger.debug(f"Object {obj_key} missing for {self.missing_frame_counters[obj_key]} frames, stopping interpolation")
            self.currently_tracking[obj_key] = False
            return []
            
        # 過去の検出が無ければ補間できない
        if obj_key not in self.last_detections:
            return []
            
        # 最後の検出をコピーして信頼度を下げる
        fade_factor = self.settings['interpolation']['fade_out_factor']
        interpolated_detections = []
        
        for det in self.last_detections[obj_key]:
            interpolated = deepcopy(det)
            # フレーム欠損に応じて信頼度を下げる（フェードアウト効果）
            missing_count = self.missing_frame_counters[obj_key]
            fade_multiplier = fade_factor ** missing_count
            interpolated['confidence'] = interpolated.get('confidence', 0.0) * fade_multiplier
            interpolated['interpolated'] = True
            interpolated_detections.append(interpolated)
        
        logger.debug(f"Interpolated {obj_key} detection for {self.missing_frame_counters[obj_key]} missing frames")
        return interpolated_detections
    
    def reset_state(self) -> None:
        """状態をリセット"""
        self.detection_buffers.clear()
        self.last_detections.clear()
        self.missing_frame_counters.clear()
        self.currently_tracking.clear()
        logger.info("DetectionSmoother state reset completed")
    
    def get_settings(self) -> Dict[str, Any]:
        """
        現在の設定を取得
        
        Returns:
            Dict[str, Any]: 設定内容
        """
        return deepcopy(self.settings)
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """
        設定を更新
        
        Args:
            new_settings: 新しい設定
        """
        try:
            # 既存の設定を更新（階層的）
            for section, section_settings in new_settings.items():
                if section in self.settings and isinstance(section_settings, dict):
                    self.settings[section].update(section_settings)
            
            # 移動平均バッファサイズの更新
            new_window_size = self.settings['moving_average']['window_size']
            for obj_key in self.detection_buffers:
                self.detection_buffers[obj_key] = deque(
                    list(self.detection_buffers[obj_key])[-new_window_size:] 
                    if self.detection_buffers[obj_key] else [], 
                    maxlen=new_window_size
                )
                
            logger.info("DetectionSmoother settings updated successfully")
            
        except Exception as e:
            update_error = wrap_exception(
                e, SmoothingError,
                "Failed to update detection smoother settings",
                details={'settings': new_settings}
            )
            logger.error(f"Settings update error: {update_error.to_dict()}")
            raise update_error
        
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
            'settings': self.get_settings()
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