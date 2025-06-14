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
    """
    動的フレームスキップ機構
    
    現在のFPSに基づいて処理するフレームを動的に調整します。
    """
    
    def __init__(self, 
                 target_fps: float = 15.0,
                 min_fps: float = 10.0, 
                 max_skip_rate: int = 5,
                 adjustment_interval: float = 2.0,
                 adaptive_mode: bool = True):
        """
        初期化
        
        Args:
            target_fps: 目標FPS
            min_fps: 最小許容FPS
            max_skip_rate: 最大スキップレート
            adjustment_interval: 調整間隔（秒）
            adaptive_mode: 適応モードの有効/無効
        """
        self.target_fps = target_fps
        self.min_fps = min_fps
        self.max_skip_rate = max_skip_rate
        self.adjustment_interval = adjustment_interval
        self.adaptive_mode = adaptive_mode
        
        # 現在の設定
        self.current_skip_rate = 1  # 初期値は1（全フレーム処理）
        self.frame_counter = 0
        self.last_adjustment_time = time.time()
        
        logger.info(f"FrameSkipper initialized: target_fps={target_fps}, min_fps={min_fps}, "
                   f"max_skip_rate={max_skip_rate}")
        
    def should_process_frame(self, current_fps: float) -> bool:
        """
        現在のフレームを処理すべきかどうかを判定
        
        Args:
            current_fps: 現在のFPS
            
        Returns:
            bool: 処理すべきならTrue、スキップすべきならFalse
        """
        # 適応モードが無効の場合は、現在のカウンター値で判定してからインクリメント
        if not self.adaptive_mode:
            should_process = (self.frame_counter % self.current_skip_rate == 0)
            self.frame_counter += 1
            return should_process
        
        # 適応モードではインクリメントしてから適応調整
        self.frame_counter += 1
        
        # 定期的にスキップレートを調整
        current_time = time.time()
        if current_time - self.last_adjustment_time > self.adjustment_interval:
            self._adjust_skip_rate(current_fps)
            self.last_adjustment_time = current_time
        
        # カウンターに基づくスキップ
        return self.frame_counter % self.current_skip_rate == 0
    
    def _adjust_skip_rate(self, current_fps: float) -> None:
        """
        現在のFPSに基づいてスキップレートを調整
        
        Args:
            current_fps: 現在のFPS
        """
        if current_fps <= 0:
            return  # 有効なFPSがない場合は調整しない
        
        old_skip_rate = self.current_skip_rate
        
        if current_fps < self.min_fps:
            # FPSが低すぎる場合はスキップレートを上げる
            self.current_skip_rate = min(self.current_skip_rate + 1, self.max_skip_rate)
        elif current_fps > self.target_fps * 1.2:
            # FPSが十分高い場合はスキップレートを下げる
            self.current_skip_rate = max(self.current_skip_rate - 1, 1)
        
        # スキップレートが変化した場合にログ出力
        if old_skip_rate != self.current_skip_rate:
            logger.info(f"Skip rate adjusted: {old_skip_rate} -> {self.current_skip_rate} "
                      f"(current FPS: {current_fps:.1f}, target: {self.target_fps})")
    
    def reset(self) -> None:
        """状態をリセット"""
        self.current_skip_rate = 1
        self.frame_counter = 0
        self.last_adjustment_time = time.time()
        logger.info("FrameSkipper reset to initial state")


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
    """
    AI処理最適化クラス
    
    システムリソース・パフォーマンスを監視し、推論処理を最適化します：
    1. FPSカウンター: 推論速度を常時監視
    2. 動的フレームスキップ: 負荷に応じて自動的にフレーム処理率を調整
    3. 推論前処理最適化: メモリ使用量削減・処理速度向上
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        
        # デフォルト設定
        self.settings = {
            # FPSカウンター設定
            'fps_counter': {
                'window_size': 30,  # 移動平均のウィンドウサイズ
                'enabled': True,
            },
            
            # フレームスキップ設定
            'frame_skipper': {
                'target_fps': 15.0,  # 目標FPS（高すぎると点滅する可能性）
                'min_fps': 10.0,     # 最小FPS（これを下回るとスキップ率上昇）
                'max_skip_rate': 5,  # 最大スキップ率（1:処理、5:5フレームごとに1回処理）
                'adjustment_interval': 2.0,  # 調整間隔（秒）
                'adaptive_mode': True,  # 適応モード（システム負荷に応じて自動調整）
                'enabled': True,
            },
            
            # フレーム前処理設定
            'preprocessing': {
                'resize_enabled': True,  # リサイズ有効（低解像度で推論）
                'resize_width': 640,     # リサイズ幅
                'resize_height': 480,    # リサイズ高さ
                'normalize_enabled': True,  # 正規化有効（高速推論）
                'roi_enabled': False,    # 関心領域処理（実験的）
            },
        }
        
        # パフォーマンスモニタリング（設定読み込み前に初期化）
        self.fps_times = deque(maxlen=self.settings['fps_counter']['window_size'])
        self.inference_times = deque(maxlen=self.settings['fps_counter']['window_size'])
        self.last_fps_update = time.time()
        self.current_fps = 0.0
        self.frame_counter = 0
        
        # 設定の読み込み（属性初期化後に実行）
        if config_manager:
            self._load_settings()
        
        # フレームスキッパー
        self.frame_skipper = FrameSkipper(
            target_fps=self.settings['frame_skipper']['target_fps'],
            min_fps=self.settings['frame_skipper']['min_fps'],
            max_skip_rate=self.settings['frame_skipper']['max_skip_rate'],
            adjustment_interval=self.settings['frame_skipper']['adjustment_interval'],
            adaptive_mode=self.settings['frame_skipper']['adaptive_mode']
        )
        
        # システムモニタリング（メモリ、CPU、GPU）
        self.system_stats = {
            'memory_percent': 0.0,
            'cpu_percent': 0.0,
            'gpu_percent': 0.0,
            'total_memory_mb': 0,
            'used_memory_mb': 0,
            'last_update': time.time()
        }
        self._update_system_stats()
        
        logger.info("AIOptimizer initialized successfully")
    
    def _load_settings(self) -> None:
        """設定を読み込む"""
        try:
            # FPSカウンター設定
            if self.config_manager.has('optimization.fps_counter'):
                fps_config = self.config_manager.get('optimization.fps_counter', {})
                self.settings['fps_counter'].update(fps_config)
                
                # バッファサイズの更新
                new_window_size = self.settings['fps_counter']['window_size']
                if new_window_size != len(self.fps_times):
                    self.fps_times = deque(list(self.fps_times)[-new_window_size:] if self.fps_times else [], 
                                        maxlen=new_window_size)
                    self.inference_times = deque(list(self.inference_times)[-new_window_size:] if self.inference_times else [], 
                                             maxlen=new_window_size)
            
            # フレームスキップ設定
            if self.config_manager.has('optimization.frame_skipper'):
                skip_config = self.config_manager.get('optimization.frame_skipper', {})
                self.settings['frame_skipper'].update(skip_config)
                
                # フレームスキッパーの設定更新
                if hasattr(self, 'frame_skipper'):
                    self.frame_skipper.target_fps = self.settings['frame_skipper']['target_fps']
                    self.frame_skipper.min_fps = self.settings['frame_skipper']['min_fps']
                    self.frame_skipper.max_skip_rate = self.settings['frame_skipper']['max_skip_rate']
                    self.frame_skipper.adjustment_interval = self.settings['frame_skipper']['adjustment_interval']
                    self.frame_skipper.adaptive_mode = self.settings['frame_skipper']['adaptive_mode']
            
            # 前処理設定
            if self.config_manager.has('optimization.preprocessing'):
                preproc_config = self.config_manager.get('optimization.preprocessing', {})
                self.settings['preprocessing'].update(preproc_config)
                
            logger.info("AI optimizer settings loaded successfully")
            
        except Exception as e:
            config_error = wrap_exception(
                e, OptimizationError, 
                "Failed to load AI optimizer settings",
                details={'using_default_settings': True}
            )
            logger.warning(f"Configuration error: {config_error.to_dict()}")
    
    def optimize_yolo_inference(self, model: Any, frame: np.ndarray) -> Optional[Any]:
        """
        YOLO推論の最適化
        
        フレームスキップ判定とGPU最適化を適用したYOLO推論を実行します。
        
        Args:
            model: YOLOモデル
            frame: 入力フレーム（BGR形式）
            
        Returns:
            推論結果、フレームスキップ時はNone
        """
        if not self.settings['frame_skipper']['enabled'] or not hasattr(self, 'frame_skipper'):
            # フレームスキップが無効の場合は全フレーム処理
            return self._run_inference(model, frame)
        
        # フレームスキップ判定（FPSに基づく動的スキップ）
        should_process = self.frame_skipper.should_process_frame(self.current_fps)
        if not should_process:
            # スマホ検出のためのフレームスキップ状況をログに出力
            logger.debug(f"⏭️ フレームスキップ: FPS={self.current_fps:.1f}, skip_rate={self.frame_skipper.current_skip_rate}, frame_counter={self.frame_skipper.frame_counter}")
            return None
        
        # 推論実行と統計更新
        start_time = time.time()
        results = self._run_inference(model, frame)
        inference_time = time.time() - start_time
        
        # 統計更新
        self._update_fps_stats()
        self.inference_times.append(inference_time)
        
        return results
    
    def _run_inference(self, model: Any, frame: np.ndarray) -> Any:
        """
        最適化設定を適用した推論実行
        
        Args:
            model: 推論モデル
            frame: 入力フレーム
            
        Returns:
            推論結果
        """
        try:
            # フレーム前処理
            preprocessed_frame = self._optimize_frame_preprocessing(frame)
            
            # 対応するバックエンドを判定して適切な推論を実行
            if hasattr(model, '__class__') and model.__class__.__name__ == 'YOLO':
                # YOLO推論
                results = model(preprocessed_frame, verbose=False)
                return results
            else:
                # 一般的なモデル推論
                return model(preprocessed_frame)
                
        except Exception as e:
            inference_error = wrap_exception(
                e, OptimizationError,
                "Optimized inference failed",
                details={
                    'model_type': str(type(model)),
                    'frame_shape': frame.shape if frame is not None else None
                }
            )
            logger.error(f"Inference optimization error: {inference_error.to_dict()}")
            
            # エラー時は元のフレームで直接推論を試みる
            try:
                return model(frame)
            except Exception as fallback_error:
                raise wrap_exception(
                    fallback_error, OptimizationError,
                    "Fallback inference also failed",
                    details={'original_error': str(e)}
                )
    
    def _optimize_frame_preprocessing(self, frame: np.ndarray, *, for_mediapipe: bool = False) -> np.ndarray:
        """
        フレーム前処理の最適化
        
        Args:
            frame: 入力フレーム
            for_mediapipe: MediaPipe用のフラグ
            
        Returns:
            前処理済みフレーム
        """
        if frame is None or frame.size == 0:
            return frame
            
        try:
            optimized_frame = frame
            preprocessing = self.settings['preprocessing']
            
            # MediaPipe 用の場合はリサイズのみ適用し、正規化は行わない
            if for_mediapipe:
                preprocessing = preprocessing.copy()
                preprocessing['normalize_enabled'] = False  # dtype を維持
            
            # リサイズ処理
            if preprocessing['resize_enabled']:
                target_width = preprocessing['resize_width']
                target_height = preprocessing['resize_height']
                
                # 元のサイズが既に小さい場合はリサイズしない
                if frame.shape[1] > target_width or frame.shape[0] > target_height:
                    optimized_frame = cv2.resize(
                        optimized_frame, 
                        (target_width, target_height), 
                        interpolation=cv2.INTER_AREA
                    )
            
            # 正規化処理
            if preprocessing['normalize_enabled'] and not for_mediapipe:
                # 0-255 -> 0-1の範囲に正規化
                if optimized_frame.dtype != np.float32:
                    optimized_frame = optimized_frame.astype(np.float32) / 255.0
            
            # 関心領域処理（実験的）
            if preprocessing['roi_enabled']:
                # 画像の中央部分を抽出（例: 中央70%）
                h, w = optimized_frame.shape[:2]
                roi_w, roi_h = int(w * 0.7), int(h * 0.7)
                start_x = (w - roi_w) // 2
                start_y = (h - roi_h) // 2
                optimized_frame = optimized_frame[start_y:start_y+roi_h, start_x:start_x+roi_w]
                
            # MediaPipe 用の場合は必ず uint8 形式で返す
            if for_mediapipe and optimized_frame.dtype != np.uint8:
                optimized_frame = np.clip(optimized_frame * 255.0, 0, 255).astype(np.uint8)
            return optimized_frame
        
        except Exception as e:
            preproc_error = wrap_exception(
                e, OptimizationError,
                "Frame preprocessing optimization failed",
                details={'frame_shape': frame.shape if frame is not None else None}
            )
            logger.warning(f"Preprocessing error: {preproc_error.to_dict()}")
            return frame  # エラー時は元のフレームを返す
    
    def optimize_mediapipe_pipeline(self, mediapipe_component: Any, frame: np.ndarray) -> Any:
        """
        MediaPipe推論パイプラインの最適化
        
        Args:
            mediapipe_component: MediaPipeコンポーネント
            frame: 入力フレーム（RGB形式）
            
        Returns:
            MediaPipe推論結果
        """
        if not self.settings['frame_skipper']['enabled'] or not hasattr(self, 'frame_skipper'):
            # フレームスキップが無効の場合は全フレーム処理
            return mediapipe_component.process(frame)
        
        # フレームスキップ判定
        if not self.frame_skipper.should_process_frame(self.current_fps):
            return None
        
        # 推論実行と統計更新
        start_time = time.time()
        
        # フレーム前処理
        preprocessed_frame = self._optimize_frame_preprocessing(frame, for_mediapipe=True)
        
        results = mediapipe_component.process(preprocessed_frame)
        
        inference_time = time.time() - start_time
        
        # 統計更新
        self._update_fps_stats()
        self.inference_times.append(inference_time)
        
        return results
    
    def _update_fps_stats(self) -> None:
        """FPS統計を更新"""
        if not self.settings['fps_counter']['enabled']:
            return
        
        current_time = time.time()
        self.fps_times.append(current_time)
        self.frame_counter += 1
        
        # FPSを計算（直近のframesのフレーム間隔から）
        if len(self.fps_times) >= 2:
            time_diff = self.fps_times[-1] - self.fps_times[0]
            if time_diff > 0:
                self.current_fps = (len(self.fps_times) - 1) / time_diff
        
        # 定期的にログに出力
        fps_log_interval = 5.0  # 5秒ごと
        if current_time - self.last_fps_update > fps_log_interval:
            avg_inference_time = sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0
            logger.info(f"Performance stats: FPS={self.current_fps:.2f}, "
                      f"Inference Time={avg_inference_time*1000:.1f}ms, "
                      f"Skip Rate={self.frame_skipper.current_skip_rate if hasattr(self, 'frame_skipper') else 1}, "
                      f"Memory={self.system_stats['memory_percent']:.1f}%, "
                      f"CPU={self.system_stats['cpu_percent']:.1f}%")
            self.last_fps_update = current_time
            
            # システム統計も更新
            self._update_system_stats()
    
    def _update_system_stats(self) -> None:
        """システムリソース使用状況を更新"""
        try:
            # メモリ使用率
            memory = psutil.virtual_memory()
            self.system_stats['memory_percent'] = memory.percent
            self.system_stats['total_memory_mb'] = memory.total / (1024 * 1024)
            self.system_stats['used_memory_mb'] = memory.used / (1024 * 1024)
            
            # CPU使用率
            self.system_stats['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            
            # GPU使用率（Torch経由で取得を試みる）
            if torch.cuda.is_available():
                try:
                    # NVIDIAのGPUの場合
                    self.system_stats['gpu_percent'] = float(torch.cuda.utilization())
                except (AttributeError, RuntimeError):
                    # 取得できない場合はPyTorchのメモリ使用量を取得
                    if torch.cuda.is_initialized():
                        gpu_mem_allocated = torch.cuda.memory_allocated() / (1024 * 1024)
                        gpu_mem_reserved = torch.cuda.memory_reserved() / (1024 * 1024)
                        self.system_stats['gpu_memory_allocated_mb'] = gpu_mem_allocated
                        self.system_stats['gpu_memory_reserved_mb'] = gpu_mem_reserved
            
            self.system_stats['last_update'] = time.time()
            
        except Exception as e:
            stats_error = wrap_exception(
                e, PerformanceError,
                "Failed to update system stats",
                details={'error_type': str(type(e))}
            )
            logger.warning(f"System stats update error: {stats_error.to_dict()}")
    
    def update_performance_stats(self) -> None:
        """パフォーマンス統計を更新（外部からの定期呼び出し用）"""
        self._update_fps_stats()
        
        # 一定間隔でシステム統計を更新
        current_time = time.time()
        stats_update_interval = 10.0  # 10秒ごと
        if current_time - self.system_stats['last_update'] > stats_update_interval:
            self._update_system_stats()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        パフォーマンス統計を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        avg_inference_time = sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0
        
        stats = {
            'fps': self.current_fps,
            'frame_count': self.frame_counter,
            'inference_time_ms': avg_inference_time * 1000,
            'skip_rate': self.frame_skipper.current_skip_rate if hasattr(self, 'frame_skipper') else 1,
            'memory_percent': self.system_stats['memory_percent'],
            'cpu_percent': self.system_stats['cpu_percent'],
            'gpu_percent': self.system_stats['gpu_percent'],
            'used_memory_mb': self.system_stats['used_memory_mb'],
            'total_memory_mb': self.system_stats['total_memory_mb'],
            'settings': self.get_settings()
        }
        
        return stats
    
    def get_settings(self) -> Dict[str, Any]:
        """
        現在の設定を取得
        
        Returns:
            Dict[str, Any]: 設定内容
        """
        return self.settings.copy()
    
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
            
            # FPSカウンターの更新
            if 'fps_counter' in new_settings:
                window_size = self.settings['fps_counter']['window_size']
                self.fps_times = deque(list(self.fps_times)[-window_size:] if self.fps_times else [], maxlen=window_size)
                self.inference_times = deque(list(self.inference_times)[-window_size:] if self.inference_times else [], maxlen=window_size)
            
            # フレームスキッパーの更新
            if hasattr(self, 'frame_skipper') and 'frame_skipper' in new_settings:
                self.frame_skipper.target_fps = self.settings['frame_skipper']['target_fps']
                self.frame_skipper.min_fps = self.settings['frame_skipper']['min_fps']
                self.frame_skipper.max_skip_rate = self.settings['frame_skipper']['max_skip_rate']
                self.frame_skipper.adjustment_interval = self.settings['frame_skipper']['adjustment_interval']
                self.frame_skipper.adaptive_mode = self.settings['frame_skipper']['adaptive_mode']
            
            logger.info("AIOptimizer settings updated successfully")
            
        except Exception as e:
            update_error = wrap_exception(
                e, OptimizationError,
                "Failed to update AI optimizer settings",
                details={'settings': new_settings}
            )
            logger.error(f"Settings update error: {update_error.to_dict()}")
            raise update_error

    def should_skip_frame(self) -> bool:
        """
        現在のフレームをスキップすべきかどうかを判定
        
        Returns:
            bool: スキップすべきならTrue、処理すべきならFalse
        """
        if not self.settings['frame_skipper']['enabled']:
            return False
        
        # フレームスキッパーがあればそのロジックを使用
        if hasattr(self, 'frame_skipper'):
            return not self.frame_skipper.should_process_frame(self.current_fps)
        
        return False

    def start_inference_timer(self) -> None:
        """
        推論時間計測を開始
        """
        self.inference_start_time = time.time()
        
    def end_inference_timer(self) -> None:
        """
        推論時間計測を終了し、統計を更新
        """
        if hasattr(self, 'inference_start_time'):
            inference_time = time.time() - self.inference_start_time
            self.inference_times.append(inference_time)
            self._update_fps_stats()
            
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        パフォーマンスメトリクスを取得
        
        Returns:
            Dict[str, Any]: パフォーマンス指標
        """
        avg_inference_time = sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0
        
        metrics = {
            'fps': self.current_fps,
            'inference_time_ms': avg_inference_time * 1000,
            'skip_rate': self.frame_skipper.current_skip_rate if hasattr(self, 'frame_skipper') else 1,
            'memory_percent': self.system_stats['memory_percent'],
            'cpu_percent': self.system_stats['cpu_percent']
        }
        
        return metrics 