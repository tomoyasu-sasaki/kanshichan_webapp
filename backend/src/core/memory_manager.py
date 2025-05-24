"""
メモリ管理強化モジュール
- メモリ使用量監視
- キャッシュ戦略実装
- ガベージコレクション最適化
- メモリリーク検出
"""

import gc
import psutil
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from collections import deque, OrderedDict
import weakref
import numpy as np
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    MemoryError, PerformanceError, ResourceError,
    wrap_exception
)

logger = setup_logger(__name__)


class MemoryCache:
    """LRUキャッシュ実装"""
    
    def __init__(self, max_size: int = 100, max_memory_mb: float = 50.0):
        """
        Args:
            max_size: 最大キャッシュエントリ数
            max_memory_mb: 最大メモリ使用量（MB）
        """
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.cache = OrderedDict()
        self.memory_usage = 0.0
        self._lock = threading.Lock()
        
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        with self._lock:
            if key in self.cache:
                # LRU: 最近使用したアイテムを末尾に移動
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None
            
    def put(self, key: str, value: Any) -> None:
        """キャッシュに値を格納"""
        with self._lock:
            # メモリ使用量を推定
            value_size = self._estimate_size(value)
            
            # 既存のキーがある場合は削除
            if key in self.cache:
                old_size = self._estimate_size(self.cache[key])
                self.memory_usage -= old_size
                del self.cache[key]
            
            # メモリ制限チェック
            while (len(self.cache) >= self.max_size or 
                   self.memory_usage + value_size > self.max_memory_mb):
                if not self.cache:
                    break
                oldest_key, oldest_value = self.cache.popitem(last=False)
                self.memory_usage -= self._estimate_size(oldest_value)
                
            # 新しい値を追加
            self.cache[key] = value
            self.memory_usage += value_size
            
    def clear(self) -> None:
        """キャッシュをクリア"""
        with self._lock:
            self.cache.clear()
            self.memory_usage = 0.0
            
    def _estimate_size(self, obj: Any) -> float:
        """オブジェクトのメモリサイズを推定（MB）"""
        try:
            if isinstance(obj, np.ndarray):
                return obj.nbytes / (1024 * 1024)
            elif isinstance(obj, (str, bytes)):
                return len(obj) / (1024 * 1024)
            elif isinstance(obj, (list, tuple)):
                return sum(self._estimate_size(item) for item in obj)
            elif isinstance(obj, dict):
                return sum(self._estimate_size(k) + self._estimate_size(v) 
                          for k, v in obj.items())
            else:
                # 基本的なオブジェクトサイズ推定
                return 0.001  # 1KB
        except Exception:
            return 0.001


class MemoryMonitor:
    """メモリ使用量監視クラス"""
    
    def __init__(self, window_size: int = 60):
        """
        Args:
            window_size: 監視ウィンドウサイズ（秒）
        """
        self.window_size = window_size
        self.memory_history = deque(maxlen=window_size)
        self.last_check = time.time()
        self.process = psutil.Process()
        
    def update(self) -> Dict[str, float]:
        """メモリ使用量を更新して統計を返す"""
        current_time = time.time()
        
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            self.memory_history.append({
                'timestamp': current_time,
                'memory_mb': memory_mb,
                'memory_percent': self.process.memory_percent()
            })
            
            self.last_check = current_time
            
            return self.get_stats()
            
        except Exception as e:
            memory_error = wrap_exception(
                e, MemoryError,
                "Failed to update memory statistics",
                details={'monitoring_disabled': True}
            )
            logger.warning(f"Memory monitoring error: {memory_error.to_dict()}")
            return {}
            
    def get_stats(self) -> Dict[str, float]:
        """メモリ統計を取得"""
        if not self.memory_history:
            return {}
            
        recent_memory = [entry['memory_mb'] for entry in self.memory_history]
        recent_percent = [entry['memory_percent'] for entry in self.memory_history]
        
        return {
            'current_memory_mb': recent_memory[-1] if recent_memory else 0.0,
            'avg_memory_mb': sum(recent_memory) / len(recent_memory),
            'max_memory_mb': max(recent_memory),
            'min_memory_mb': min(recent_memory),
            'current_memory_percent': recent_percent[-1] if recent_percent else 0.0,
            'avg_memory_percent': sum(recent_percent) / len(recent_percent)
        }
        
    def is_memory_critical(self, threshold_percent: float = 80.0) -> bool:
        """メモリ使用量が危険レベルかチェック"""
        stats = self.get_stats()
        return stats.get('current_memory_percent', 0.0) > threshold_percent


class GarbageCollectionOptimizer:
    """ガベージコレクション最適化クラス"""
    
    def __init__(self):
        self.last_gc_time = time.time()
        self.gc_interval = 30.0  # 30秒間隔
        self.gc_stats = deque(maxlen=10)
        
    def should_run_gc(self, memory_percent: float = 0.0) -> bool:
        """ガベージコレクションを実行すべきかチェック"""
        current_time = time.time()
        
        # 時間ベースの判定
        time_based = (current_time - self.last_gc_time) > self.gc_interval
        
        # メモリ使用量ベースの判定
        memory_based = memory_percent > 70.0
        
        return time_based or memory_based
        
    def run_optimized_gc(self) -> Dict[str, Any]:
        """最適化されたガベージコレクションを実行"""
        start_time = time.time()
        
        try:
            # 世代別ガベージコレクション
            collected = {
                'generation_0': gc.collect(0),
                'generation_1': gc.collect(1),
                'generation_2': gc.collect(2)
            }
            
            gc_time = time.time() - start_time
            self.last_gc_time = time.time()
            
            stats = {
                'collected_objects': sum(collected.values()),
                'gc_time_ms': gc_time * 1000,
                'timestamp': self.last_gc_time,
                'generations': collected
            }
            
            self.gc_stats.append(stats)
            
            logger.debug(f"GC completed: {stats['collected_objects']} objects "
                        f"in {stats['gc_time_ms']:.1f}ms")
            
            return stats
            
        except Exception as e:
            gc_error = wrap_exception(
                e, PerformanceError,
                "Garbage collection optimization failed",
                details={'gc_disabled': True}
            )
            logger.error(f"GC optimization error: {gc_error.to_dict()}")
            return {}


class MemoryManager:
    """メモリ管理メインクラス"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Args:
            config_manager: 設定管理インスタンス
        """
        try:
            self.config_manager = config_manager
            
            # コンポーネント初期化
            self.monitor = MemoryMonitor()
            self.gc_optimizer = GarbageCollectionOptimizer()
            
            # キャッシュ初期化
            cache_size = 100
            cache_memory_mb = 50.0
            if config_manager:
                cache_size = config_manager.get('memory.cache.max_size', 100)
                cache_memory_mb = config_manager.get('memory.cache.max_memory_mb', 50.0)
                
            self.frame_cache = MemoryCache(cache_size, cache_memory_mb)
            self.result_cache = MemoryCache(cache_size // 2, cache_memory_mb // 2)
            
            # 設定読み込み
            self._load_memory_settings()
            
            # 監視スレッド開始
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            logger.info("MemoryManager initialized successfully")
            
        except Exception as e:
            memory_error = wrap_exception(
                e, MemoryError,
                "MemoryManager initialization failed",
                details={'memory_management_disabled': True}
            )
            logger.error(f"MemoryManager initialization error: {memory_error.to_dict()}")
            raise memory_error
            
    def _load_memory_settings(self) -> None:
        """メモリ管理設定の読み込み"""
        if not self.config_manager:
            return
            
        try:
            self.memory_threshold = self.config_manager.get('memory.threshold_percent', 80.0)
            self.gc_interval = self.config_manager.get('memory.gc_interval_seconds', 30.0)
            self.monitor_interval = self.config_manager.get('memory.monitor_interval_seconds', 5.0)
            
            self.gc_optimizer.gc_interval = self.gc_interval
            
            logger.info(f"Memory settings loaded: threshold={self.memory_threshold}%, "
                       f"gc_interval={self.gc_interval}s")
                       
        except Exception as e:
            logger.warning(f"Failed to load memory settings, using defaults: {e}")
            self.memory_threshold = 80.0
            self.gc_interval = 30.0
            self.monitor_interval = 5.0
            
    def _monitor_loop(self) -> None:
        """メモリ監視ループ"""
        while self.monitoring_active:
            try:
                # メモリ統計更新
                stats = self.monitor.update()
                
                if stats:
                    current_percent = stats.get('current_memory_percent', 0.0)
                    
                    # ガベージコレクション判定
                    if self.gc_optimizer.should_run_gc(current_percent):
                        gc_stats = self.gc_optimizer.run_optimized_gc()
                        if gc_stats:
                            logger.info(f"Auto GC: {gc_stats['collected_objects']} objects collected")
                    
                    # メモリ危険レベルチェック
                    if self.monitor.is_memory_critical(self.memory_threshold):
                        logger.warning(f"Memory usage critical: {current_percent:.1f}%")
                        self._emergency_cleanup()
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Memory monitoring loop error: {e}")
                time.sleep(self.monitor_interval)
                
    def _emergency_cleanup(self) -> None:
        """緊急メモリクリーンアップ"""
        try:
            logger.info("Performing emergency memory cleanup")
            
            # キャッシュクリア
            self.frame_cache.clear()
            self.result_cache.clear()
            
            # 強制ガベージコレクション
            self.gc_optimizer.run_optimized_gc()
            
            logger.info("Emergency cleanup completed")
            
        except Exception as e:
            cleanup_error = wrap_exception(
                e, MemoryError,
                "Emergency memory cleanup failed",
                details={'cleanup_failed': True}
            )
            logger.error(f"Emergency cleanup error: {cleanup_error.to_dict()}")
            
    def cache_frame(self, key: str, frame: np.ndarray) -> None:
        """フレームをキャッシュ"""
        self.frame_cache.put(key, frame)
        
    def get_cached_frame(self, key: str) -> Optional[np.ndarray]:
        """キャッシュからフレームを取得"""
        return self.frame_cache.get(key)
        
    def cache_result(self, key: str, result: Any) -> None:
        """結果をキャッシュ"""
        self.result_cache.put(key, result)
        
    def get_cached_result(self, key: str) -> Optional[Any]:
        """キャッシュから結果を取得"""
        return self.result_cache.get(key)
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """メモリ統計を取得"""
        stats = self.monitor.get_stats()
        stats.update({
            'frame_cache_size': len(self.frame_cache.cache),
            'frame_cache_memory_mb': self.frame_cache.memory_usage,
            'result_cache_size': len(self.result_cache.cache),
            'result_cache_memory_mb': self.result_cache.memory_usage,
            'gc_stats': list(self.gc_optimizer.gc_stats)[-3:] if self.gc_optimizer.gc_stats else []
        })
        return stats
        
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        try:
            self.monitoring_active = False
            if hasattr(self, 'monitor_thread'):
                self.monitor_thread.join(timeout=1.0)
            
            self.frame_cache.clear()
            self.result_cache.clear()
            
            logger.info("MemoryManager cleanup completed")
            
        except Exception as e:
            logger.error(f"MemoryManager cleanup error: {e}") 