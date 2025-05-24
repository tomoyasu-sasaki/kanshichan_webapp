"""
AI処理最適化モジュール
- YOLO推論の最適化
- MediaPipeパイプライン最適化
- フレームスキップ機能
- バッチ処理の導入
"""

import cv2
import numpy as np
import time
import threading
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
import psutil
import torch
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    ModelError, PerformanceError, OptimizationError, 
    ConfigError, wrap_exception
)

logger = setup_logger(__name__)


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self, window_size: int = 30):
        """
        Args:
            window_size: FPS計算のウィンドウサイズ（フレーム数）
        """
        self.frame_times = deque(maxlen=window_size)
        self.inference_times = deque(maxlen=window_size)
        self.memory_usage = deque(maxlen=window_size)
        self.last_frame_time = time.time()
        
    def record_frame(self) -> None:
        """フレーム処理時間を記録"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        self.last_frame_time = current_time
        
        # メモリ使用量も記録
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        self.memory_usage.append(memory_mb)
        
    def record_inference_time(self, inference_time: float) -> None:
        """推論時間を記録"""
        self.inference_times.append(inference_time)
        
    def get_current_fps(self) -> float:
        """現在のFPSを取得"""
        if len(self.frame_times) < 2:
            return 0.0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
        
    def get_avg_inference_time(self) -> float:
        """平均推論時間を取得（ミリ秒）"""
        if not self.inference_times:
            return 0.0
        return (sum(self.inference_times) / len(self.inference_times)) * 1000
        
    def get_memory_usage(self) -> float:
        """現在のメモリ使用量を取得（MB）"""
        if not self.memory_usage:
            return 0.0
        return self.memory_usage[-1]
        
    def get_stats(self) -> Dict[str, float]:
        """統計情報を取得"""
        return {
            'fps': self.get_current_fps(),
            'avg_inference_ms': self.get_avg_inference_time(),
            'memory_mb': self.get_memory_usage(),
            'frame_count': len(self.frame_times)
        }


class FrameSkipper:
    """フレームスキップ機能"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager
        self.skip_rate = 1  # 1 = スキップなし
        self.frame_counter = 0
        self.target_fps = 15.0
        self.min_fps = 5.0
        self.max_skip_rate = 5
        self.last_adjustment = time.time()
        self.adjustment_interval = 2.0  # 2秒ごとに調整
        
    def should_process_frame(self, current_fps: float) -> bool:
        """フレームを処理すべきかどうかを判定"""
        self.frame_counter += 1
        
        # 動的スキップレート調整
        self._adjust_skip_rate(current_fps)
        
        # スキップレートに基づいて処理判定
        return (self.frame_counter % self.skip_rate) == 0
        
    def _adjust_skip_rate(self, current_fps: float) -> None:
        """現在のFPSに基づいてスキップレートを動的調整"""
        current_time = time.time()
        
        if current_time - self.last_adjustment < self.adjustment_interval:
            return
            
        self.last_adjustment = current_time
        
        if current_fps < self.min_fps:
            # FPSが低すぎる場合はスキップレートを上げる
            self.skip_rate = min(self.skip_rate + 1, self.max_skip_rate)
            logger.debug(f"Low FPS detected ({current_fps:.1f}), increasing skip rate to {self.skip_rate}")
        elif current_fps > self.target_fps * 1.2:
            # FPSが十分高い場合はスキップレートを下げる
            self.skip_rate = max(self.skip_rate - 1, 1)
            logger.debug(f"High FPS detected ({current_fps:.1f}), decreasing skip rate to {self.skip_rate}")


class BatchProcessor:
    """バッチ処理機能"""
    
    def __init__(self, batch_size: int = 4, timeout_ms: int = 50):
        """
        Args:
            batch_size: バッチサイズ
            timeout_ms: バッチ蓄積のタイムアウト（ミリ秒）
        """
        self.batch_size = batch_size
        self.timeout_ms = timeout_ms
        self.frame_buffer = []
        self.last_batch_time = time.time()
        self.enabled = False  # デフォルトは無効（実験的機能）
        
    def add_frame(self, frame: np.ndarray) -> Optional[List[np.ndarray]]:
        """
        フレームをバッファに追加し、バッチが準備できたら返す
        
        Returns:
            バッチが準備できた場合はフレームリスト、そうでなければNone
        """
        if not self.enabled:
            return [frame]  # バッチ処理が無効の場合は即座に返す
            
        self.frame_buffer.append(frame)
        current_time = time.time()
        
        # バッチサイズに達した、またはタイムアウトした場合
        if (len(self.frame_buffer) >= self.batch_size or 
            (current_time - self.last_batch_time) * 1000 > self.timeout_ms):
            
            batch = self.frame_buffer.copy()
            self.frame_buffer.clear()
            self.last_batch_time = current_time
            return batch
            
        return None


class AIOptimizer:
    """AI処理最適化メインクラス"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Args:
            config_manager: 設定管理インスタンス
        """
        try:
            self.config_manager = config_manager
            self.performance_monitor = PerformanceMonitor()
            self.frame_skipper = FrameSkipper(config_manager)
            self.batch_processor = BatchProcessor()
            
            # 最適化設定の読み込み
            self._load_optimization_settings()
            
            logger.info("AIOptimizer initialized successfully")
            
        except Exception as e:
            optimization_error = wrap_exception(
                e, OptimizationError,
                "AIOptimizer initialization failed",
                details={'optimization_disabled': True}
            )
            logger.error(f"AIOptimizer initialization error: {optimization_error.to_dict()}")
            raise optimization_error
            
    def _load_optimization_settings(self) -> None:
        """最適化設定の読み込み"""
        if not self.config_manager:
            return
            
        try:
            # フレームスキップ設定
            self.frame_skipper.target_fps = self.config_manager.get('optimization.target_fps', 15.0)
            self.frame_skipper.min_fps = self.config_manager.get('optimization.min_fps', 5.0)
            self.frame_skipper.max_skip_rate = self.config_manager.get('optimization.max_skip_rate', 5)
            
            # バッチ処理設定
            batch_enabled = self.config_manager.get('optimization.batch_processing.enabled', False)
            self.batch_processor.enabled = batch_enabled
            self.batch_processor.batch_size = self.config_manager.get('optimization.batch_processing.batch_size', 4)
            self.batch_processor.timeout_ms = self.config_manager.get('optimization.batch_processing.timeout_ms', 50)
            
            logger.info(f"Optimization settings loaded: target_fps={self.frame_skipper.target_fps}, "
                       f"batch_enabled={batch_enabled}")
                       
        except Exception as e:
            config_error = wrap_exception(
                e, ConfigError,
                "Failed to load optimization settings",
                details={'using_defaults': True}
            )
            logger.warning(f"Using default optimization settings: {config_error.to_dict()}")
            
    def optimize_yolo_inference(self, model, frame: np.ndarray) -> Optional[Any]:
        """
        YOLO推論の最適化
        
        Args:
            model: YOLOモデル
            frame: 入力フレーム
            
        Returns:
            推論結果（最適化適用済み）
        """
        try:
            inference_start = time.time()
            
            # フレームスキップ判定
            current_fps = self.performance_monitor.get_current_fps()
            if not self.frame_skipper.should_process_frame(current_fps):
                return None
                
            # フレーム前処理の最適化
            optimized_frame = self._optimize_frame_preprocessing(frame)
            
            # YOLO推論実行
            with torch.no_grad():  # 勾配計算を無効化
                results = model(optimized_frame, verbose=False)
                
            inference_time = time.time() - inference_start
            self.performance_monitor.record_inference_time(inference_time)
            
            return results
            
        except Exception as e:
            model_error = wrap_exception(
                e, ModelError,
                "YOLO inference optimization failed",
                details={'fallback_to_standard': True}
            )
            logger.warning(f"YOLO optimization error: {model_error.to_dict()}")
            # フォールバック: 標準推論
            return model(frame, verbose=False)
            
    def optimize_mediapipe_pipeline(self, pose_model, frame: np.ndarray) -> Optional[Any]:
        """
        MediaPipeパイプライン最適化
        
        Args:
            pose_model: MediaPipe Poseモデル
            frame: 入力フレーム
            
        Returns:
            推論結果（最適化適用済み）
        """
        try:
            inference_start = time.time()
            
            # フレームサイズ最適化
            optimized_frame = self._optimize_frame_for_mediapipe(frame)
            
            # MediaPipe推論実行
            results = pose_model.process(optimized_frame)
            
            inference_time = time.time() - inference_start
            self.performance_monitor.record_inference_time(inference_time)
            
            return results
            
        except Exception as e:
            model_error = wrap_exception(
                e, ModelError,
                "MediaPipe pipeline optimization failed",
                details={'fallback_to_standard': True}
            )
            logger.warning(f"MediaPipe optimization error: {model_error.to_dict()}")
            # フォールバック: 標準推論
            return pose_model.process(frame)
            
    def _optimize_frame_preprocessing(self, frame: np.ndarray) -> np.ndarray:
        """フレーム前処理の最適化"""
        # フレームサイズの最適化（解像度を下げて処理速度向上）
        height, width = frame.shape[:2]
        
        # 解像度が高すぎる場合はリサイズ
        max_width = 640
        if width > max_width:
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
        return frame
        
    def _optimize_frame_for_mediapipe(self, frame: np.ndarray) -> np.ndarray:
        """MediaPipe用フレーム最適化"""
        # MediaPipeはRGBを期待するが、変換コストを最小化
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            # BGR to RGB変換
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame
        
    def update_performance_stats(self) -> None:
        """パフォーマンス統計を更新"""
        self.performance_monitor.record_frame()
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        stats = self.performance_monitor.get_stats()
        stats.update({
            'skip_rate': self.frame_skipper.skip_rate,
            'batch_enabled': self.batch_processor.enabled,
            'optimization_active': True
        })
        return stats
        
    def log_performance_summary(self) -> None:
        """パフォーマンス統計をログ出力"""
        stats = self.get_performance_stats()
        logger.info(
            f"Performance Stats - FPS: {stats['fps']:.1f}, "
            f"Inference: {stats['avg_inference_ms']:.1f}ms, "
            f"Memory: {stats['memory_mb']:.1f}MB, "
            f"Skip Rate: {stats['skip_rate']}"
        ) 