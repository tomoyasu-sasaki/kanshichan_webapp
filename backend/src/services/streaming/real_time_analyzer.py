"""
リアルタイム分析サービス

リアルタイムデータストリーミング・即座分析・即座フィードバック
- ストリーミングデータ処理
- リアルタイム行動分析
- 即座アラート生成
- パフォーマンス監視
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import deque, defaultdict
import logging
import json
import asyncio
import threading
import time

from models.behavior_log import BehaviorLog
from ..ai_ml.advanced_behavior_analyzer import AdvancedBehaviorAnalyzer
from ..ai_ml.pattern_recognition import PatternRecognizer
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StreamEvent(Enum):
    """ストリームイベントタイプ"""
    FOCUS_CHANGE = "focus_change"
    POSTURE_CHANGE = "posture_change"
    DISTRACTION_DETECTED = "distraction_detected"
    BREAK_NEEDED = "break_needed"
    PRODUCTIVITY_SHIFT = "productivity_shift"
    ALERT_TRIGGERED = "alert_triggered"


class WindowType(Enum):
    """ウィンドウタイプ"""
    SLIDING = "sliding"
    TUMBLING = "tumbling"
    SESSION = "session"


@dataclass
class StreamAnalysisResult:
    """ストリーム分析結果"""
    event_type: StreamEvent
    timestamp: datetime
    confidence: float
    data: Dict[str, Any]
    context: Dict[str, Any]
    user_id: Optional[str] = None
    urgent: bool = False


@dataclass
class RealTimeMetrics:
    """リアルタイムメトリクス"""
    timestamp: datetime
    processing_latency_ms: float
    throughput_fps: float
    queue_depth: int
    error_rate: float
    active_streams: int


@dataclass
class SlidingWindowConfig:
    """滑動ウィンドウ設定"""
    window_size_seconds: int = 60
    slide_interval_seconds: int = 5
    max_data_points: int = 1000
    enable_compression: bool = True


class StreamAnalyzer:
    """ストリーム分析エンジン"""
    
    def __init__(self, config: Dict[str, Any]):
        """初期化"""
        self.config = config.get('stream_analyzer', {})
        
        # 滑動ウィンドウ設定
        self.window_config = SlidingWindowConfig(
            window_size_seconds=self.config.get('window_size_seconds', 60),
            slide_interval_seconds=self.config.get('slide_interval_seconds', 5),
            max_data_points=self.config.get('max_data_points', 1000)
        )
        
        # データストリーム管理
        self.data_streams = defaultdict(deque)
        self.stream_metadata = {}
        
        # 分析エンジン
        self.behavior_analyzer = None
        self.pattern_recognizer = None
        
        # イベントリスナー
        self.event_listeners = []
        
        # パフォーマンス追跡
        self.metrics = {
            'total_processed': 0,
            'total_events': 0,
            'processing_times': deque(maxlen=100),
            'error_count': 0
        }
        
        logger.info("StreamAnalyzer initialized")
    
    def add_data_point(self, stream_id: str, data: Dict[str, Any], 
                      timestamp: Optional[datetime] = None):
        """データポイント追加
        
        Args:
            stream_id: ストリームID
            data: データ
            timestamp: タイムスタンプ
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            # データポイント作成
            data_point = {
                'timestamp': timestamp,
                'data': data,
                'processed': False
            }
            
            # ストリームに追加
            stream = self.data_streams[stream_id]
            stream.append(data_point)
            
            # サイズ制限
            if len(stream) > self.window_config.max_data_points:
                stream.popleft()
            
            # メタデータ更新
            self.stream_metadata[stream_id] = {
                'last_update': timestamp,
                'data_count': len(stream),
                'stream_active': True
            }
            
            self.metrics['total_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error adding data point to stream {stream_id}: {e}")
            self.metrics['error_count'] += 1
    
    def analyze_stream(self, stream_id: str) -> List[StreamAnalysisResult]:
        """ストリーム分析実行
        
        Args:
            stream_id: ストリームID
            
        Returns:
            List[StreamAnalysisResult]: 分析結果リスト
        """
        try:
            start_time = time.time()
            
            # ストリームデータ取得
            stream_data = self._get_window_data(stream_id)
            
            if not stream_data:
                return []
            
            # 分析実行
            results = []
            
            # 集中度変化分析
            focus_events = self._analyze_focus_changes(stream_data)
            results.extend(focus_events)
            
            # 姿勢変化分析
            posture_events = self._analyze_posture_changes(stream_data)
            results.extend(posture_events)
            
            # 注意散漫検出
            distraction_events = self._analyze_distractions(stream_data)
            results.extend(distraction_events)
            
            # 休憩推奨分析
            break_events = self._analyze_break_needs(stream_data)
            results.extend(break_events)
            
            # 処理時間記録
            processing_time = (time.time() - start_time) * 1000
            self.metrics['processing_times'].append(processing_time)
            
            # イベント通知
            for result in results:
                self._notify_event_listeners(result)
                self.metrics['total_events'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing stream {stream_id}: {e}")
            self.metrics['error_count'] += 1
            return []
    
    def add_event_listener(self, listener: Callable[[StreamAnalysisResult], None]):
        """イベントリスナー追加
        
        Args:
            listener: イベントリスナー関数
        """
        self.event_listeners.append(listener)
        logger.info("Event listener added")
    
    def get_stream_status(self) -> Dict[str, Any]:
        """ストリーム状態取得"""
        try:
            active_streams = {
                stream_id: metadata 
                for stream_id, metadata in self.stream_metadata.items()
                if metadata.get('stream_active', False)
            }
            
            # 平均処理時間計算
            avg_processing_time = 0.0
            if self.metrics['processing_times']:
                avg_processing_time = np.mean(list(self.metrics['processing_times']))
            
            return {
                'active_streams': len(active_streams),
                'total_data_points': sum(
                    len(stream) for stream in self.data_streams.values()
                ),
                'metrics': {
                    'total_processed': self.metrics['total_processed'],
                    'total_events': self.metrics['total_events'],
                    'average_processing_time_ms': avg_processing_time,
                    'error_count': self.metrics['error_count'],
                    'error_rate': (
                        self.metrics['error_count'] / max(self.metrics['total_processed'], 1)
                    )
                },
                'stream_details': active_streams
            }
            
        except Exception as e:
            logger.error(f"Error getting stream status: {e}")
            return {}
    
    # ========== Private Methods ==========
    
    def _get_window_data(self, stream_id: str) -> List[Dict[str, Any]]:
        """ウィンドウデータ取得"""
        try:
            stream = self.data_streams.get(stream_id)
            if not stream:
                return []
            
            # 時間ウィンドウ計算
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(
                seconds=self.window_config.window_size_seconds
            )
            
            # ウィンドウ内データ抽出
            window_data = [
                point for point in stream
                if point['timestamp'] >= window_start
            ]
            
            return window_data
            
        except Exception as e:
            logger.error(f"Error getting window data: {e}")
            return []
    
    def _analyze_focus_changes(self, data: List[Dict[str, Any]]) -> List[StreamAnalysisResult]:
        """集中度変化分析"""
        try:
            results = []
            
            if len(data) < 2:
                return results
            
            # 集中度データ抽出
            focus_scores = [
                point['data'].get('focus_score', 0.5) 
                for point in data 
                if 'focus_score' in point['data']
            ]
            
            if len(focus_scores) < 2:
                return results
            
            # 変化量計算
            recent_focus = np.mean(focus_scores[-5:]) if len(focus_scores) >= 5 else focus_scores[-1]
            previous_focus = np.mean(focus_scores[-10:-5]) if len(focus_scores) >= 10 else focus_scores[0]
            
            focus_change = recent_focus - previous_focus
            
            # 閾値チェック
            if abs(focus_change) > 0.2:  # 20%以上の変化
                event_type = StreamEvent.FOCUS_CHANGE
                confidence = min(abs(focus_change) * 2, 1.0)
                
                result = StreamAnalysisResult(
                    event_type=event_type,
                    timestamp=datetime.utcnow(),
                    confidence=confidence,
                    data={
                        'focus_change': focus_change,
                        'current_focus': recent_focus,
                        'previous_focus': previous_focus,
                        'focus_score': recent_focus
                    },
                    context={'analysis_type': 'focus_change'},
                    urgent=recent_focus < 0.3
                )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing focus changes: {e}")
            return []
    
    def _analyze_posture_changes(self, data: List[Dict[str, Any]]) -> List[StreamAnalysisResult]:
        """姿勢変化分析"""
        try:
            results = []
            
            # 姿勢データ抽出
            posture_scores = [
                point['data'].get('posture_score', 0.5) 
                for point in data 
                if 'posture_score' in point['data']
            ]
            
            if len(posture_scores) < 3:
                return results
            
            # 最近の姿勢スコア
            recent_posture = np.mean(posture_scores[-3:])
            
            # 悪い姿勢の継続チェック
            if recent_posture < 0.4:  # 40%以下で警告
                result = StreamAnalysisResult(
                    event_type=StreamEvent.POSTURE_CHANGE,
                    timestamp=datetime.utcnow(),
                    confidence=0.8,
                    data={
                        'posture_score': recent_posture,
                        'status': 'poor_posture'
                    },
                    context={'analysis_type': 'posture_change'},
                    urgent=recent_posture < 0.3
                )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing posture changes: {e}")
            return []
    
    def _analyze_distractions(self, data: List[Dict[str, Any]]) -> List[StreamAnalysisResult]:
        """注意散漫分析"""
        try:
            results = []
            
            # 注意散漫指標検索
            for point in data[-5:]:  # 直近5ポイント
                point_data = point['data']
                
                # スマートフォン検出
                if point_data.get('smartphone_detected', False):
                    result = StreamAnalysisResult(
                        event_type=StreamEvent.DISTRACTION_DETECTED,
                        timestamp=point['timestamp'],
                        confidence=0.9,
                        data={
                            'distraction_type': 'smartphone',
                            'detected': True
                        },
                        context={'analysis_type': 'distraction_detection'},
                        urgent=True
                    )
                    results.append(result)
                
                # 視線分散検出
                if point_data.get('gaze_dispersion', 0) > 0.7:
                    result = StreamAnalysisResult(
                        event_type=StreamEvent.DISTRACTION_DETECTED,
                        timestamp=point['timestamp'],
                        confidence=0.7,
                        data={
                            'distraction_type': 'gaze_dispersion',
                            'dispersion_score': point_data['gaze_dispersion']
                        },
                        context={'analysis_type': 'distraction_detection'},
                        urgent=False
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing distractions: {e}")
            return []
    
    def _analyze_break_needs(self, data: List[Dict[str, Any]]) -> List[StreamAnalysisResult]:
        """休憩必要性分析"""
        try:
            results = []
            
            if len(data) < 10:
                return results
            
            # 作業時間計算（分）
            work_duration = (data[-1]['timestamp'] - data[0]['timestamp']).total_seconds() / 60
            
            # 疲労度指標
            fatigue_scores = [
                point['data'].get('fatigue_score', 0.0) 
                for point in data 
                if 'fatigue_score' in point['data']
            ]
            
            # 休憩推奨条件
            break_needed = False
            confidence = 0.5
            
            # 長時間作業チェック
            if work_duration > 45:  # 45分以上
                break_needed = True
                confidence = 0.8
            
            # 疲労度チェック
            if fatigue_scores and np.mean(fatigue_scores[-3:]) > 0.7:
                break_needed = True
                confidence = max(confidence, 0.9)
            
            if break_needed:
                result = StreamAnalysisResult(
                    event_type=StreamEvent.BREAK_NEEDED,
                    timestamp=datetime.utcnow(),
                    confidence=confidence,
                    data={
                        'work_duration_minutes': work_duration,
                        'fatigue_level': np.mean(fatigue_scores[-3:]) if fatigue_scores else 0.0,
                        'recommendation': 'take_break'
                    },
                    context={'analysis_type': 'break_recommendation'},
                    urgent=work_duration > 60  # 1時間以上で緊急
                )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing break needs: {e}")
            return []
    
    def _notify_event_listeners(self, result: StreamAnalysisResult):
        """イベントリスナー通知"""
        try:
            for listener in self.event_listeners:
                try:
                    listener(result)
                except Exception as e:
                    logger.error(f"Error in event listener: {e}")
        except Exception as e:
            logger.error(f"Error notifying event listeners: {e}")


class RealTimeAnalyzer:
    """リアルタイム分析エンジン
    
    統合リアルタイム分析とイベント処理
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('real_time_analyzer', {})
        
        # コンポーネント初期化
        self.stream_analyzer = StreamAnalyzer(config)
        
        # 高度分析エンジン統合
        self.behavior_analyzer = None
        self.pattern_recognizer = None
        
        # 分析状態管理
        self.is_running = False
        self.analysis_tasks = {}
        
        # メトリクス収集
        self.realtime_metrics = RealTimeMetrics(
            timestamp=datetime.utcnow(),
            processing_latency_ms=0.0,
            throughput_fps=0.0,
            queue_depth=0,
            error_rate=0.0,
            active_streams=0
        )
        
        # 非同期処理管理
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("RealTimeAnalyzer initialized")
    
    async def start(self, behavior_analyzer: AdvancedBehaviorAnalyzer,
                   pattern_recognizer: PatternRecognizer):
        """リアルタイム分析開始
        
        Args:
            behavior_analyzer: 高度行動分析器
            pattern_recognizer: パターン認識器
        """
        try:
            if self.is_running:
                logger.warning("Real-time analyzer is already running")
                return
            
            # 分析エンジン設定
            self.behavior_analyzer = behavior_analyzer
            self.pattern_recognizer = pattern_recognizer
            self.stream_analyzer.behavior_analyzer = behavior_analyzer
            self.stream_analyzer.pattern_recognizer = pattern_recognizer
            
            self.is_running = True
            
            # 分析タスク開始
            self.analysis_tasks['stream_processing'] = asyncio.create_task(
                self._stream_processing_loop()
            )
            
            self.analysis_tasks['metrics_collection'] = asyncio.create_task(
                self._metrics_collection_loop()
            )
            
            logger.info("Real-time analyzer started")
            
        except Exception as e:
            logger.error(f"Error starting real-time analyzer: {e}", exc_info=True)
            self.is_running = False
    
    async def stop(self):
        """リアルタイム分析停止"""
        try:
            self.is_running = False
            
            # 分析タスク停止
            for task_name, task in self.analysis_tasks.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Analysis task {task_name} cancelled")
            
            logger.info("Real-time analyzer stopped")
            
        except Exception as e:
            logger.error(f"Error stopping real-time analyzer: {e}")
    
    async def add_data_point(self, data: Dict[str, Any], user_id: str = "default"):
        """データポイント追加
        
        Args:
            data: 分析データ
            user_id: ユーザーID
        """
        try:
            # ストリーム分析器にデータ追加
            self.stream_analyzer.add_data_point(f"user_{user_id}", data)
            
        except Exception as e:
            logger.error(f"Error adding data point: {e}")
    
    def extract_realtime_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """リアルタイム特徴量抽出
        
        Args:
            data: 入力データ
            
        Returns:
            Dict: 抽出された特徴量
        """
        try:
            features = {}
            
            # 基本特徴量
            features['timestamp'] = datetime.utcnow().isoformat()
            features['data_quality'] = self._assess_data_quality(data)
            
            # 行動特徴量
            if 'eye_movement' in data:
                features.update(self._extract_eye_features(data['eye_movement']))
            
            if 'pose_data' in data:
                features.update(self._extract_pose_features(data['pose_data']))
            
            if 'environment' in data:
                features.update(self._extract_environment_features(data['environment']))
            
            # 統合特徴量
            features.update(self._calculate_integrated_features(features))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting realtime features: {e}")
            return {}
    
    def get_realtime_metrics(self) -> RealTimeMetrics:
        """リアルタイムメトリクス取得"""
        try:
            stream_status = self.stream_analyzer.get_stream_status()
            metrics = stream_status.get('metrics', {})
            
            # メトリクス更新
            self.realtime_metrics = RealTimeMetrics(
                timestamp=datetime.utcnow(),
                processing_latency_ms=metrics.get('average_processing_time_ms', 0.0),
                throughput_fps=self._calculate_throughput(),
                queue_depth=stream_status.get('total_data_points', 0),
                error_rate=metrics.get('error_rate', 0.0),
                active_streams=stream_status.get('active_streams', 0)
            )
            
            return self.realtime_metrics
            
        except Exception as e:
            logger.error(f"Error getting realtime metrics: {e}")
            return self.realtime_metrics
    
    def add_event_listener(self, listener: Callable[[StreamAnalysisResult], None]):
        """イベントリスナー追加"""
        self.stream_analyzer.add_event_listener(listener)
    
    # ========== Private Methods ==========
    
    async def _stream_processing_loop(self):
        """ストリーム処理ループ"""
        try:
            while self.is_running:
                try:
                    # アクティブストリーム取得
                    stream_status = self.stream_analyzer.get_stream_status()
                    active_streams = stream_status.get('stream_details', {})
                    
                    # 各ストリーム分析
                    for stream_id in active_streams.keys():
                        try:
                            results = self.stream_analyzer.analyze_stream(stream_id)
                            # 結果は自動的にイベントリスナーに通知される
                        except Exception as e:
                            logger.error(f"Error analyzing stream {stream_id}: {e}")
                    
                    # 分析間隔（5秒）
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error in stream processing loop: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Critical error in stream processing: {e}")
    
    async def _metrics_collection_loop(self):
        """メトリクス収集ループ"""
        try:
            while self.is_running:
                try:
                    # メトリクス更新
                    self.get_realtime_metrics()
                    
                    # 30秒間隔
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error in metrics collection: {e}")
                    await asyncio.sleep(30)
                    
        except Exception as e:
            logger.error(f"Critical error in metrics collection: {e}")
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> float:
        """データ品質評価"""
        try:
            quality_score = 1.0
            
            # 必須フィールドチェック
            required_fields = ['timestamp', 'user_id']
            missing_fields = [f for f in required_fields if f not in data]
            quality_score -= len(missing_fields) * 0.2
            
            # データ完整性チェック
            if 'eye_movement' in data and not data['eye_movement']:
                quality_score -= 0.1
            
            if 'pose_data' in data and not data['pose_data']:
                quality_score -= 0.1
            
            return max(quality_score, 0.0)
            
        except Exception:
            return 0.5
    
    def _extract_eye_features(self, eye_data: Dict[str, Any]) -> Dict[str, Any]:
        """視線特徴量抽出"""
        try:
            features = {}
            
            if 'gaze_points' in eye_data:
                gaze_points = eye_data['gaze_points']
                if gaze_points:
                    features['gaze_stability'] = 1.0 - np.std([p.get('x', 0) for p in gaze_points[-10:]])
                    features['focus_score'] = eye_data.get('focus_score', 0.5)
            
            if 'blink_rate' in eye_data:
                features['blink_rate'] = eye_data['blink_rate']
                # 疲労度推定
                features['estimated_fatigue'] = max(0, min(1, (eye_data['blink_rate'] - 15) / 10))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting eye features: {e}")
            return {}
    
    def _extract_pose_features(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        """姿勢特徴量抽出"""
        try:
            features = {}
            
            if 'posture_score' in pose_data:
                features['posture_score'] = pose_data['posture_score']
            
            if 'head_angle' in pose_data:
                head_angle = pose_data['head_angle']
                # 良い姿勢範囲判定
                features['good_posture'] = -15 <= head_angle <= 15
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting pose features: {e}")
            return {}
    
    def _extract_environment_features(self, env_data: Dict[str, Any]) -> Dict[str, Any]:
        """環境特徴量抽出"""
        try:
            features = {}
            
            if 'objects_detected' in env_data:
                objects = env_data['objects_detected']
                features['smartphone_detected'] = 'smartphone' in objects
                features['distractions_count'] = len([obj for obj in objects if obj in ['smartphone', 'tablet']])
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting environment features: {e}")
            return {}
    
    def _calculate_integrated_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """統合特徴量計算"""
        try:
            integrated = {}
            
            # 総合集中スコア
            focus_score = features.get('focus_score', 0.5)
            posture_score = features.get('posture_score', 0.5)
            distraction_penalty = features.get('distractions_count', 0) * 0.1
            
            integrated['overall_focus'] = max(0, (focus_score * 0.6 + posture_score * 0.4) - distraction_penalty)
            
            # 作業効率推定
            integrated['productivity_estimate'] = integrated['overall_focus'] * 0.8
            
            return integrated
            
        except Exception as e:
            logger.error(f"Error calculating integrated features: {e}")
            return {}
    
    def _calculate_throughput(self) -> float:
        """スループット計算"""
        try:
            stream_status = self.stream_analyzer.get_stream_status()
            total_processed = stream_status.get('metrics', {}).get('total_processed', 0)
            
            # 簡易FPS計算（実際の実装では時間ベース計算が必要）
            return min(total_processed / 60.0, 5.0)  # 最大5FPS
            
        except Exception:
            return 0.0 