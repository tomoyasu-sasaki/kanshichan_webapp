"""
パフォーマンス監視サービス

システム全体のパフォーマンス・リソース使用状況・負荷の監視
- CPUメモリ監視
- 処理速度計測
- スループット監視
- ボトルネック検出
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import asdict, dataclass, field
from enum import Enum
import logging
import threading
import time
import asyncio
import psutil
import numpy as np

from models.behavior_log import BehaviorLog
from .alert_system import AlertSystem
from utils.logger import setup_logger

# 実在ファイルへのimport復活（Priority 3）
from ..streaming.real_time_analyzer import RealTimeAnalyzer, RealTimeMetrics
from ..streaming.streaming_processor import StreamingProcessor

logger = setup_logger(__name__)


class MetricType(Enum):
    """メトリクスタイプ"""
    SYSTEM_RESOURCE = "system_resource"
    ANALYSIS_PERFORMANCE = "analysis_performance"
    USER_EXPERIENCE = "user_experience"
    NETWORK_PERFORMANCE = "network_performance"


class PerformanceLevel(Enum):
    """パフォーマンスレベル"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """システムメトリクス"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_io_read_mb_s: float
    disk_io_write_mb_s: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    gpu_usage_percent: Optional[float] = None
    gpu_memory_usage_percent: Optional[float] = None


@dataclass
class AnalysisMetrics:
    """分析パフォーマンスメトリクス"""
    timestamp: datetime
    processing_latency_ms: float
    throughput_fps: float
    analysis_accuracy: float
    prediction_confidence: float
    error_rate: float
    queue_depth: int
    feature_extraction_time_ms: float
    model_inference_time_ms: float


@dataclass
class UserExperienceMetrics:
    """ユーザー体験メトリクス"""
    timestamp: datetime
    response_time_ms: float
    ui_responsiveness_score: float
    alert_delivery_success_rate: float
    user_satisfaction_score: float
    feature_availability_percent: float
    data_freshness_seconds: float


@dataclass
class PerformanceAlert:
    """パフォーマンスアラート"""
    alert_id: str
    metric_type: MetricType
    alert_level: PerformanceLevel
    threshold_value: float
    current_value: float
    message: str
    timestamp: datetime
    recommendations: List[str]


class ResourceMonitor:
    """システムリソース監視"""
    
    def __init__(self, config: Dict[str, Any]):
        """初期化"""
        self.config = config.get('resource_monitor', {})
        self.monitoring_interval = self.config.get('interval_seconds', 5)
        
        # 閾値設定
        self.thresholds = {
            'cpu_warning': self.config.get('cpu_warning_percent', 80),
            'cpu_critical': self.config.get('cpu_critical_percent', 95),
            'memory_warning': self.config.get('memory_warning_percent', 85),
            'memory_critical': self.config.get('memory_critical_percent', 95),
            'disk_warning': self.config.get('disk_warning_percent', 85),
            'disk_critical': self.config.get('disk_critical_percent', 95)
        }
        
        # メトリクス履歴
        self.metrics_history = deque(maxlen=1000)
        self.is_monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """監視開始"""
        if self.is_monitoring:
            logger.warning("Resource monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """監視停止"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("Resource monitoring stopped")
    
    def get_current_metrics(self) -> SystemMetrics:
        """現在のシステムメトリクス取得"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # ディスクI/O
            disk_io = psutil.disk_io_counters()
            disk_io_read = 0.0  # 簡易実装
            disk_io_write = 0.0
            
            # ネットワーク
            network = psutil.net_io_counters()
            network_sent = network.bytes_sent
            network_recv = network.bytes_recv
            
            # プロセス数
            process_count = len(psutil.pids())
            
            # GPU使用率（可能な場合）
            gpu_usage, gpu_memory = self._get_gpu_metrics()
            
            metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory_usage,
                memory_available_gb=memory_available,
                disk_usage_percent=disk_usage,
                disk_io_read_mb_s=disk_io_read,
                disk_io_write_mb_s=disk_io_write,
                network_bytes_sent=network_sent,
                network_bytes_recv=network_recv,
                process_count=process_count,
                gpu_usage_percent=gpu_usage,
                gpu_memory_usage_percent=gpu_memory
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return self._create_default_metrics()
    
    def _monitor_loop(self):
        """監視ループ"""
        try:
            while self.is_monitoring:
                try:
                    metrics = self.get_current_metrics()
                    self.metrics_history.append(metrics)
                    
                    # 閾値チェック
                    self._check_thresholds(metrics)
                    
                    time.sleep(self.monitoring_interval)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(self.monitoring_interval)
                    
        except Exception as e:
            logger.error(f"Critical error in monitoring loop: {e}")
    
    def _get_gpu_metrics(self) -> Tuple[Optional[float], Optional[float]]:
        """GPU メトリクス取得"""
        try:
            # GPU監視実装 - 将来実装
            return None, None
        except Exception:
            return None, None
    
    def _check_thresholds(self, metrics: SystemMetrics):
        """閾値チェック"""
        try:
            # CPU使用率チェック
            if metrics.cpu_usage_percent > self.thresholds['cpu_critical']:
                logger.critical(f"Critical CPU usage: {metrics.cpu_usage_percent}%")
            elif metrics.cpu_usage_percent > self.thresholds['cpu_warning']:
                logger.warning(f"High CPU usage: {metrics.cpu_usage_percent}%")
            
            # メモリ使用率チェック
            if metrics.memory_usage_percent > self.thresholds['memory_critical']:
                logger.critical(f"Critical memory usage: {metrics.memory_usage_percent}%")
            elif metrics.memory_usage_percent > self.thresholds['memory_warning']:
                logger.warning(f"High memory usage: {metrics.memory_usage_percent}%")
            
            # ディスク使用率チェック
            if metrics.disk_usage_percent > self.thresholds['disk_critical']:
                logger.critical(f"Critical disk usage: {metrics.disk_usage_percent}%")
            elif metrics.disk_usage_percent > self.thresholds['disk_warning']:
                logger.warning(f"High disk usage: {metrics.disk_usage_percent}%")
                
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")
    
    def _create_default_metrics(self) -> SystemMetrics:
        """デフォルトメトリクス作成"""
        return SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage_percent=0.0,
            memory_usage_percent=0.0,
            memory_available_gb=0.0,
            disk_usage_percent=0.0,
            disk_io_read_mb_s=0.0,
            disk_io_write_mb_s=0.0,
            network_bytes_sent=0,
            network_bytes_recv=0,
            process_count=0
        )


class AnalysisPerformanceMonitor:
    """分析パフォーマンス監視"""
    
    def __init__(self, config: Dict[str, Any]):
        """初期化"""
        self.config = config.get('analysis_monitor', {})
        
        # パフォーマンス履歴
        self.metrics_history = deque(maxlen=1000)
        self.accuracy_history = deque(maxlen=100)
        
        # ベンチマーク値
        self.benchmarks = {
            'target_latency_ms': self.config.get('target_latency_ms', 100),
            'target_throughput_fps': self.config.get('target_throughput_fps', 2.0),
            'target_accuracy': self.config.get('target_accuracy', 0.85),
            'max_error_rate': self.config.get('max_error_rate', 0.05)
        }
    
    def record_analysis_metrics(self, real_time_analyzer: RealTimeAnalyzer):
        """分析メトリクス記録
        
        リアルタイム分析器からメトリクス情報を取得し、
        パフォーマンス履歴として記録・評価します。
        
        Args:
            real_time_analyzer: リアルタイム分析器インスタンス
                RealTimeAnalyzerクラスのインスタンスであり、
                get_realtime_metrics()メソッドを提供する必要があります。
                
        Note:
            取得したメトリクスは以下の項目を含みます：
            - processing_latency_ms: 処理遅延時間
            - throughput_fps: スループット（フレーム/秒）
            - error_rate: エラー率
            - queue_depth: キューの深さ
            
        Raises:
            Exception: メトリクス取得・記録時のエラー
        """
        try:
            # リアルタイム分析器からメトリクス取得
            rt_metrics = real_time_analyzer.get_realtime_metrics()
            
            # 分析メトリクス構築
            analysis_metrics = AnalysisMetrics(
                timestamp=datetime.utcnow(),
                processing_latency_ms=rt_metrics.processing_latency_ms,
                throughput_fps=rt_metrics.throughput_fps,
                analysis_accuracy=self._calculate_analysis_accuracy(),
                prediction_confidence=self._calculate_prediction_confidence(),
                error_rate=rt_metrics.error_rate,
                queue_depth=rt_metrics.queue_depth,
                feature_extraction_time_ms=self._estimate_feature_extraction_time(),
                model_inference_time_ms=self._estimate_model_inference_time()
            )
            
            # 履歴に追加
            self.metrics_history.append(analysis_metrics)
            
            # パフォーマンス評価
            self._evaluate_performance(analysis_metrics)
            
            # 精度履歴更新（直近10件維持）
            self.accuracy_history.append(analysis_metrics.analysis_accuracy)
            
            logger.debug(f"Analysis metrics recorded: "
                        f"latency={rt_metrics.processing_latency_ms}ms, "
                        f"throughput={rt_metrics.throughput_fps}fps, "
                        f"accuracy={analysis_metrics.analysis_accuracy:.3f}")
            
        except AttributeError as e:
            logger.error(f"RealTimeAnalyzer missing required method: {e}")
        except Exception as e:
            logger.error(f"Error recording analysis metrics: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンス要約取得"""
        try:
            if not self.metrics_history:
                return {'status': 'no_data'}
            
            recent_metrics = list(self.metrics_history)[-10:]  # 直近10件
            
            avg_latency = np.mean([m.processing_latency_ms for m in recent_metrics])
            avg_throughput = np.mean([m.throughput_fps for m in recent_metrics])
            avg_accuracy = np.mean([m.analysis_accuracy for m in recent_metrics])
            avg_error_rate = np.mean([m.error_rate for m in recent_metrics])
            
            # パフォーマンスレベル判定
            performance_level = self._determine_performance_level(
                avg_latency, avg_throughput, avg_accuracy, avg_error_rate
            )
            
            return {
                'performance_level': performance_level.value,
                'average_latency_ms': avg_latency,
                'average_throughput_fps': avg_throughput,
                'average_accuracy': avg_accuracy,
                'average_error_rate': avg_error_rate,
                'benchmarks': self.benchmarks,
                'recommendations': self._generate_performance_recommendations(performance_level)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _calculate_analysis_accuracy(self) -> float:
        """分析精度計算 - 実装予定"""
        # 簡易実装：履歴ベース推定
        if len(self.accuracy_history) > 0:
            return np.mean(list(self.accuracy_history))
        return 0.85  # デフォルト値
    
    def _calculate_prediction_confidence(self) -> float:
        """予測信頼度計算 - 実装予定"""
        return 0.8  # デフォルト値
    
    def _estimate_feature_extraction_time(self) -> float:
        """特徴量抽出時間推定 - 実装予定"""
        return 20.0  # デフォルト値（ms）
    
    def _estimate_model_inference_time(self) -> float:
        """モデル推論時間推定 - 実装予定"""
        return 30.0  # デフォルト値（ms）
    
    def _evaluate_performance(self, metrics: AnalysisMetrics):
        """パフォーマンス評価"""
        try:
            # レイテンシチェック
            if metrics.processing_latency_ms > self.benchmarks['target_latency_ms'] * 2:
                logger.warning(f"High analysis latency: {metrics.processing_latency_ms}ms")
            
            # スループットチェック
            if metrics.throughput_fps < self.benchmarks['target_throughput_fps'] * 0.5:
                logger.warning(f"Low analysis throughput: {metrics.throughput_fps} FPS")
            
            # 精度チェック
            if metrics.analysis_accuracy < self.benchmarks['target_accuracy'] * 0.8:
                logger.warning(f"Low analysis accuracy: {metrics.analysis_accuracy}")
            
            # エラー率チェック
            if metrics.error_rate > self.benchmarks['max_error_rate']:
                logger.warning(f"High error rate: {metrics.error_rate}")
                
        except Exception as e:
            logger.error(f"Error evaluating performance: {e}")
    
    def _determine_performance_level(self, latency: float, throughput: float, 
                                   accuracy: float, error_rate: float) -> PerformanceLevel:
        """パフォーマンスレベル判定"""
        try:
            score = 0
            
            # レイテンシスコア
            if latency <= self.benchmarks['target_latency_ms']:
                score += 25
            elif latency <= self.benchmarks['target_latency_ms'] * 1.5:
                score += 15
            elif latency <= self.benchmarks['target_latency_ms'] * 2:
                score += 5
            
            # スループットスコア
            if throughput >= self.benchmarks['target_throughput_fps']:
                score += 25
            elif throughput >= self.benchmarks['target_throughput_fps'] * 0.8:
                score += 15
            elif throughput >= self.benchmarks['target_throughput_fps'] * 0.5:
                score += 5
            
            # 精度スコア
            if accuracy >= self.benchmarks['target_accuracy']:
                score += 25
            elif accuracy >= self.benchmarks['target_accuracy'] * 0.9:
                score += 15
            elif accuracy >= self.benchmarks['target_accuracy'] * 0.8:
                score += 5
            
            # エラー率スコア
            if error_rate <= self.benchmarks['max_error_rate']:
                score += 25
            elif error_rate <= self.benchmarks['max_error_rate'] * 2:
                score += 15
            elif error_rate <= self.benchmarks['max_error_rate'] * 3:
                score += 5
            
            # スコアからレベル判定
            if score >= 80:
                return PerformanceLevel.EXCELLENT
            elif score >= 60:
                return PerformanceLevel.GOOD
            elif score >= 40:
                return PerformanceLevel.FAIR
            elif score >= 20:
                return PerformanceLevel.POOR
            else:
                return PerformanceLevel.CRITICAL
                
        except Exception:
            return PerformanceLevel.FAIR
    
    def _generate_performance_recommendations(self, level: PerformanceLevel) -> List[str]:
        """パフォーマンス改善推奨"""
        recommendations = []
        
        if level == PerformanceLevel.CRITICAL:
            recommendations.extend([
                "システムリソースの確認と最適化を実施してください",
                "アナライザーの設定を見直してください",
                "バッチサイズや処理間隔の調整を検討してください"
            ])
        elif level == PerformanceLevel.POOR:
            recommendations.extend([
                "処理負荷の分散を検討してください",
                "モデルの軽量化を検討してください"
            ])
        elif level == PerformanceLevel.FAIR:
            recommendations.extend([
                "定期的なパフォーマンス監視を継続してください"
            ])
        
        return recommendations


class PerformanceMonitor:
    """統合パフォーマンス監視システム
    
    システムリソース、分析パフォーマンス、ユーザー体験の統合監視
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('performance_monitor', {})
        
        # 各監視コンポーネント
        self.resource_monitor = ResourceMonitor(config)
        self.analysis_monitor = AnalysisPerformanceMonitor(config)
        
        # 統合メトリクス
        self.integrated_metrics = deque(maxlen=500)
        
        # パフォーマンスアラート
        self.performance_alerts = []
        
        # 監視状態
        self.is_monitoring = False
        self.monitoring_task = None
        
        logger.info("PerformanceMonitor initialized with integrated monitoring")
    
    async def start_monitoring(self, real_time_analyzer: RealTimeAnalyzer):
        """統合監視開始
        
        システムリソース監視、分析パフォーマンス監視、
        統合評価ループを開始します。
        
        Args:
            real_time_analyzer: リアルタイム分析器インスタンス
                RealTimeAnalyzerクラスのインスタンス。
                分析メトリクスの取得に使用されます。
                
        Note:
            監視処理は以下の内容を含みます：
            - システムリソース監視（CPU、メモリ、ディスク等）
            - 分析パフォーマンス監視（レイテンシ、スループット等）
            - 統合評価とアラート生成
            - 30秒間隔での継続監視
            
        Raises:
            Exception: 監視開始時のエラー
        """
        try:
            if self.is_monitoring:
                logger.warning("Performance monitoring is already running")
                return
            
            # リアルタイム分析器設定
            self.real_time_analyzer = real_time_analyzer
            self.is_monitoring = True
            
            # リソース監視開始
            self.resource_monitor.start_monitoring()
            
            # 統合監視タスク開始
            self.monitoring_task = asyncio.create_task(self._integrated_monitoring_loop())
            
            logger.info("Performance monitoring started with real-time analyzer integration")
            
        except Exception as e:
            logger.error(f"Error starting performance monitoring: {e}", exc_info=True)
            self.is_monitoring = False
    
    async def stop_monitoring(self):
        """統合監視停止"""
        try:
            self.is_monitoring = False
            
            # リソース監視停止
            self.resource_monitor.stop_monitoring()
            
            # 統合監視タスク停止
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Performance monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping performance monitoring: {e}")
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """包括的状態取得"""
        try:
            # システムメトリクス
            system_metrics = self.resource_monitor.get_current_metrics()
            
            # 分析パフォーマンス
            analysis_summary = self.analysis_monitor.get_performance_summary()
            
            # ユーザー体験メトリクス
            user_experience = self._get_user_experience_metrics()
            
            # 統合評価
            overall_health = self._calculate_overall_health(
                system_metrics, analysis_summary, user_experience
            )
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_health': overall_health,
                'system_metrics': asdict(system_metrics),
                'analysis_performance': analysis_summary,
                'user_experience': user_experience,
                'active_alerts': len(self.performance_alerts),
                'monitoring_status': 'active' if self.is_monitoring else 'inactive'
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """パフォーマンスレポート生成
        
        Args:
            hours: レポート対象時間（時間）
            
        Returns:
            Dict: パフォーマンスレポート
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 期間内メトリクス取得
            recent_system_metrics = [
                m for m in self.resource_monitor.metrics_history
                if m.timestamp > cutoff_time
            ]
            
            recent_analysis_metrics = [
                m for m in self.analysis_monitor.metrics_history
                if m.timestamp > cutoff_time
            ]
            
            # 統計計算
            system_stats = self._calculate_system_stats(recent_system_metrics)
            analysis_stats = self._calculate_analysis_stats(recent_analysis_metrics)
            
            # 推奨事項生成
            recommendations = self._generate_comprehensive_recommendations(
                system_stats, analysis_stats
            )
            
            return {
                'report_period_hours': hours,
                'generation_time': datetime.utcnow().isoformat(),
                'system_statistics': system_stats,
                'analysis_statistics': analysis_stats,
                'performance_trends': self._analyze_performance_trends(),
                'recommendations': recommendations,
                'alert_summary': self._summarize_alerts()
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {'status': 'error', 'error': str(e)}
    
    # ========== Private Methods ==========
    
    async def _integrated_monitoring_loop(self):
        """統合監視ループ
        
        システムリソース、分析パフォーマンス、統合評価を
        定期的に実行する監視ループです。
        
        Note:
            監視ループの処理内容：
            - リアルタイム分析器からのメトリクス記録
            - 統合評価の実行（アラート生成含む）
            - 30秒間隔での継続実行
            - エラー発生時の自動復旧
            
        Raises:
            Exception: 監視ループ内での重大なエラー
        """
        try:
            while self.is_monitoring:
                try:
                    # 分析パフォーマンス記録
                    if self.real_time_analyzer:
                        self.analysis_monitor.record_analysis_metrics(self.real_time_analyzer)
                    
                    # 統合評価実行
                    await self._perform_integrated_evaluation()
                    
                    # 30秒待機
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error in integrated monitoring loop: {e}")
                    await asyncio.sleep(30)
                    
        except Exception as e:
            logger.error(f"Critical error in integrated monitoring: {e}")
    
    async def _perform_integrated_evaluation(self):
        try:
            # 包括的状態取得（簡易版）
            status = self.get_comprehensive_status()
            
            # アラート条件チェック
            alerts = self._check_performance_alerts(status)
            
            # アラート記録
            self.performance_alerts.extend(alerts)
            
            # 統合メトリクス記録
            self.integrated_metrics.append({
                'timestamp': datetime.utcnow(),
                'overall_health': status.get('overall_health', 'unknown'),
                'system_score': self._calculate_system_score(status.get('system_metrics', {})),
                'analysis_score': self._calculate_analysis_score(status.get('analysis_performance', {}))
            })
            
        except Exception as e:
            logger.error(f"Error performing integrated evaluation: {e}")
    
    def _get_user_experience_metrics(self) -> Dict[str, Any]:
        """ユーザー体験メトリクス取得 - 実装予定"""
        return {
            'response_time_ms': 150.0,
            'ui_responsiveness_score': 0.9,
            'alert_delivery_success_rate': 0.95,
            'user_satisfaction_score': 0.85,
            'feature_availability_percent': 98.5,
            'data_freshness_seconds': 2.0
        }
    
    def _calculate_overall_health(self, system_metrics: SystemMetrics,
                                 analysis_summary: Dict[str, Any],
                                 user_experience: Dict[str, Any]) -> str:
        """総合健康度計算"""
        try:
            # システムスコア（0-100）
            system_score = 100
            if system_metrics.cpu_usage_percent > 80:
                system_score -= 20
            if system_metrics.memory_usage_percent > 85:
                system_score -= 20
            if system_metrics.disk_usage_percent > 85:
                system_score -= 10
            
            # 分析スコア（0-100）
            analysis_level = analysis_summary.get('performance_level', 'fair')
            analysis_score = {
                'excellent': 100,
                'good': 80,
                'fair': 60,
                'poor': 40,
                'critical': 20
            }.get(analysis_level, 60)
            
            # ユーザー体験スコア（0-100）
            ux_score = user_experience.get('ui_responsiveness_score', 0.8) * 100
            
            # 総合スコア
            overall_score = (system_score * 0.4 + analysis_score * 0.4 + ux_score * 0.2)
            
            if overall_score >= 85:
                return 'excellent'
            elif overall_score >= 70:
                return 'good'
            elif overall_score >= 50:
                return 'fair'
            elif overall_score >= 30:
                return 'poor'
            else:
                return 'critical'
                
        except Exception:
            return 'unknown'
    
    def _check_performance_alerts(self, status: Dict[str, Any]) -> List[PerformanceAlert]:
        """パフォーマンスアラートチェック"""
        alerts = []
        
        try:
            # システムメトリクスアラート
            system_metrics = status.get('system_metrics', {})
            
            if system_metrics.get('cpu_usage_percent', 0) > 90:
                alerts.append(PerformanceAlert(
                    alert_id=f"cpu_alert_{datetime.utcnow().timestamp()}",
                    metric_type=MetricType.SYSTEM_RESOURCE,
                    alert_level=PerformanceLevel.CRITICAL,
                    threshold_value=90.0,
                    current_value=system_metrics['cpu_usage_percent'],
                    message="Critical CPU usage detected",
                    timestamp=datetime.utcnow(),
                    recommendations=["Check for runaway processes", "Consider scaling resources"]
                ))
            
            # 分析パフォーマンスアラート
            analysis_perf = status.get('analysis_performance', {})
            if analysis_perf.get('performance_level') == 'critical':
                alerts.append(PerformanceAlert(
                    alert_id=f"analysis_alert_{datetime.utcnow().timestamp()}",
                    metric_type=MetricType.ANALYSIS_PERFORMANCE,
                    alert_level=PerformanceLevel.CRITICAL,
                    threshold_value=0.0,
                    current_value=0.0,
                    message="Critical analysis performance degradation",
                    timestamp=datetime.utcnow(),
                    recommendations=["Review analysis configuration", "Check model performance"]
                ))
            
        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}")
        
        return alerts
    
    # 以下のメソッドは段階的実装が必要
    def _calculate_system_score(self, system_metrics):
        """システムスコア計算 - 実装予定"""
        return 75.0
    
    def _calculate_analysis_score(self, analysis_performance):
        """分析スコア計算 - 実装予定"""
        return 80.0
    
    def _calculate_system_stats(self, metrics_list):
        """システム統計計算 - 実装予定"""
        return {}
    
    def _calculate_analysis_stats(self, metrics_list):
        """分析統計計算 - 実装予定"""
        return {}
    
    def _analyze_performance_trends(self):
        """パフォーマンストレンド分析 - 実装予定"""
        return {}
    
    def _generate_comprehensive_recommendations(self, system_stats, analysis_stats):
        """包括的推奨事項生成 - 実装予定"""
        return []
    
    def _summarize_alerts(self):
        """アラート要約 - 実装予定"""
        return {} 

@dataclass
class RealTimeMetrics:
    """リアルタイムメトリクス代替定義"""
    processing_latency_ms: float = 0.0
    throughput_fps: float = 0.0
    queue_depth: int = 0
    error_rate: float = 0.0
    active_streams: int = 0 