"""
ストリーミング処理サービス

リアルタイムデータストリーミング・バッファリング・配信
- データストリーミング
- バッファ管理
- 配信制御
- レート制限
"""

from typing import Dict, Any, List, Optional, Callable, Generator, AsyncGenerator
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import asyncio
import threading
import time
import queue
import weakref

from models.behavior_log import BehaviorLog
from .real_time_analyzer import RealTimeAnalyzer, StreamAnalysisResult, StreamEvent
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StreamType(Enum):
    """ストリームタイプ"""
    BEHAVIOR_DATA = "behavior_data"
    SENSOR_DATA = "sensor_data"
    USER_INTERACTION = "user_interaction"
    SYSTEM_METRICS = "system_metrics"


class ProcessingStrategy(Enum):
    """処理戦略"""
    IMMEDIATE = "immediate"
    BUFFERED = "buffered"
    BATCH = "batch"
    WINDOWED = "windowed"


@dataclass
class StreamingConfig:
    """ストリーミング設定"""
    buffer_size: int = 1000
    batch_size: int = 10
    window_size_ms: int = 5000
    max_latency_ms: int = 100
    websocket_port: int = 8765
    enable_compression: bool = True


@dataclass
class DataPacket:
    """データパケット"""
    packet_id: str
    stream_type: StreamType
    timestamp: datetime
    data: Dict[str, Any]
    sequence_number: int
    source: str
    priority: int = 5


@dataclass
class ProcessingResult:
    """処理結果"""
    packet_id: str
    processed_at: datetime
    processing_time_ms: float
    result_data: Dict[str, Any]
    events_generated: List[StreamAnalysisResult]
    status: str


class StreamBuffer:
    """ストリームバッファ管理"""
    
    def __init__(self, config: StreamingConfig):
        """初期化"""
        self.config = config
        self.buffers = defaultdict(lambda: deque(maxlen=config.buffer_size))
        self.metrics = defaultdict(int)
        self.last_cleanup = datetime.utcnow()
        
    def add_packet(self, stream_type: StreamType, packet: DataPacket) -> bool:
        """パケット追加"""
        try:
            self.buffers[stream_type].append(packet)
            self.metrics[f"{stream_type.value}_packets"] += 1
            return True
        except Exception as e:
            logger.error(f"Error adding packet to buffer: {e}")
            return False
    
    def get_packets(self, stream_type: StreamType, count: int = None) -> List[DataPacket]:
        """パケット取得"""
        try:
            buffer = self.buffers[stream_type]
            if count is None:
                packets = list(buffer)
                buffer.clear()
            else:
                packets = []
                for _ in range(min(count, len(buffer))):
                    if buffer:
                        packets.append(buffer.popleft())
            return packets
        except Exception as e:
            logger.error(f"Error getting packets from buffer: {e}")
            return []
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """バッファ統計取得"""
        return {
            'buffer_sizes': {stream_type.value: len(buffer) 
                           for stream_type, buffer in self.buffers.items()},
            'total_packets_processed': dict(self.metrics),
            'last_cleanup': self.last_cleanup.isoformat()
        }


class WebSocketHandler:
    """WebSocketハンドラー"""
    
    def __init__(self, streaming_processor):
        """初期化"""
        self.streaming_processor = streaming_processor
        self.connected_clients = set()
        self.client_subscriptions = defaultdict(set)
        
    async def handle_client(self, websocket, path):
        """クライアント接続処理"""
        try:
            self.connected_clients.add(websocket)
            logger.info(f"WebSocket client connected: {websocket.remote_address}")
            
            async for message in websocket:
                await self._handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"Error handling WebSocket client: {e}")
        finally:
            self.connected_clients.discard(websocket)
            # 購読情報削除
            for stream_type in list(self.client_subscriptions.keys()):
                self.client_subscriptions[stream_type].discard(websocket)
    
    async def _handle_message(self, websocket, message: str):
        """メッセージ処理"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                await self._handle_subscription(websocket, data)
            elif message_type == 'data':
                await self._handle_data_message(websocket, data)
            elif message_type == 'ping':
                await websocket.send(json.dumps({'type': 'pong'}))
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket client")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def _handle_subscription(self, websocket, data: Dict[str, Any]):
        """購読処理"""
        try:
            stream_types = data.get('stream_types', [])
            for stream_type_str in stream_types:
                try:
                    stream_type = StreamType(stream_type_str)
                    self.client_subscriptions[stream_type].add(websocket)
                    logger.info(f"Client subscribed to {stream_type}")
                except ValueError:
                    logger.warning(f"Invalid stream type: {stream_type_str}")
            
            # 確認メッセージ送信
            await websocket.send(json.dumps({
                'type': 'subscription_confirmed',
                'stream_types': stream_types
            }))
            
        except Exception as e:
            logger.error(f"Error handling subscription: {e}")
    
    async def _handle_data_message(self, websocket, data: Dict[str, Any]):
        """データメッセージ処理"""
        try:
            # データパケット作成
            packet = DataPacket(
                packet_id=data.get('packet_id', f"ws_{datetime.utcnow().timestamp()}"),
                stream_type=StreamType(data.get('stream_type', 'behavior_data')),
                timestamp=datetime.utcnow(),
                data=data.get('payload', {}),
                sequence_number=data.get('sequence_number', 0),
                source='websocket',
                priority=data.get('priority', 5)
            )
            
            # ストリーミングプロセッサーに送信
            await self.streaming_processor.process_packet(packet)
            
        except Exception as e:
            logger.error(f"Error handling data message: {e}")
    
    async def broadcast_to_subscribers(self, stream_type: StreamType, 
                                     result: ProcessingResult):
        """購読者にブロードキャスト"""
        try:
            subscribers = self.client_subscriptions.get(stream_type, set())
            if not subscribers:
                return
            
            message = {
                'type': 'stream_data',
                'stream_type': stream_type.value,
                'packet_id': result.packet_id,
                'timestamp': result.processed_at.isoformat(),
                'data': result.result_data,
                'events': [asdict(event) for event in result.events_generated]
            }
            
            # 非同期で全ての購読者に送信
            tasks = []
            for websocket in subscribers.copy():
                tasks.append(self._safe_send(websocket, json.dumps(message)))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Error broadcasting to subscribers: {e}")
    
    async def _safe_send(self, websocket, message: str):
        """安全なメッセージ送信"""
        try:
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            # 接続が閉じられている場合は無視
            self.connected_clients.discard(websocket)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket client: {e}")


class StreamingProcessor:
    """ストリーミングデータ処理エンジン
    
    リアルタイムデータストリームの処理とイベント配信
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('streaming_processor', {})
        
        # ストリーミング設定
        self.streaming_config = StreamingConfig(
            buffer_size=self.config.get('buffer_size', 1000),
            batch_size=self.config.get('batch_size', 10),
            window_size_ms=self.config.get('window_size_ms', 5000),
            max_latency_ms=self.config.get('max_latency_ms', 100),
            websocket_port=self.config.get('websocket_port', 8765)
        )
        
        # コンポーネント初期化
        self.stream_buffer = StreamBuffer(self.streaming_config)
        self.websocket_handler = WebSocketHandler(self)
        
        # 処理戦略
        self.processing_strategies = {
            StreamType.BEHAVIOR_DATA: ProcessingStrategy.IMMEDIATE,
            StreamType.SENSOR_DATA: ProcessingStrategy.BUFFERED,
            StreamType.USER_INTERACTION: ProcessingStrategy.IMMEDIATE,
            StreamType.SYSTEM_METRICS: ProcessingStrategy.BATCH
        }
        
        # リアルタイム分析器
        self.real_time_analyzer = None
        
        # 非同期処理管理
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.processing_tasks = {}
        self.is_running = False
        
        # WebSocketサーバー
        self.websocket_server = None
        
        # パフォーマンス監視
        self.processing_metrics = {
            'packets_processed': 0,
            'processing_errors': 0,
            'average_latency_ms': 0.0,
            'throughput_packets_per_second': 0.0
        }
        
        logger.info("StreamingProcessor initialized with WebSocket support")
    
    async def start(self, real_time_analyzer: RealTimeAnalyzer):
        """ストリーミング処理開始
        
        Args:
            real_time_analyzer: リアルタイム分析器
        """
        try:
            if self.is_running:
                logger.warning("Streaming processor is already running")
                return
            
            self.real_time_analyzer = real_time_analyzer
            self.is_running = True
            
            # WebSocketサーバー開始
            await self._start_websocket_server()
            
            # 処理タスク開始
            for stream_type in StreamType:
                self.processing_tasks[stream_type] = asyncio.create_task(
                    self._process_stream(stream_type)
                )
            
            logger.info("Streaming processor started successfully")
            
        except Exception as e:
            logger.error(f"Error starting streaming processor: {e}", exc_info=True)
            self.is_running = False
    
    async def stop(self):
        """ストリーミング処理停止"""
        try:
            self.is_running = False
            
            # 処理タスク停止
            for task in self.processing_tasks.values():
                task.cancel()
            
            # WebSocketサーバー停止
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            logger.info("Streaming processor stopped")
            
        except Exception as e:
            logger.error(f"Error stopping streaming processor: {e}")
    
    async def process_packet(self, packet: DataPacket) -> bool:
        """パケット処理
        
        Args:
            packet: データパケット
            
        Returns:
            bool: 処理成功フラグ
        """
        try:
            # バッファに追加
            success = self.stream_buffer.add_packet(packet.stream_type, packet)
            
            if success:
                # 処理戦略に応じて即座処理または後で処理
                strategy = self.processing_strategies.get(packet.stream_type, ProcessingStrategy.BUFFERED)
                
                if strategy == ProcessingStrategy.IMMEDIATE:
                    # 即座処理
                    await self._process_packet_immediately(packet)
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
            return False
    
    async def get_stream_status(self) -> Dict[str, Any]:
        """ストリーム状態取得"""
        try:
            buffer_stats = self.stream_buffer.get_buffer_stats()
            
            return {
                'is_running': self.is_running,
                'connected_clients': len(self.websocket_handler.connected_clients),
                'buffer_stats': buffer_stats,
                'processing_metrics': self.processing_metrics,
                'active_subscriptions': {
                    stream_type.value: len(clients)
                    for stream_type, clients in self.websocket_handler.client_subscriptions.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting stream status: {e}")
            return {}
    
    # ========== Private Methods ==========
    
    async def _start_websocket_server(self):
        """WebSocketサーバー開始"""
        try:
            self.websocket_server = await websockets.serve(
                self.websocket_handler.handle_client,
                "localhost",
                self.streaming_config.websocket_port
            )
            
            logger.info(f"WebSocket server started on port {self.streaming_config.websocket_port}")
            
        except Exception as e:
            logger.error(f"Error starting WebSocket server: {e}")
            raise
    
    async def _process_stream(self, stream_type: StreamType):
        """ストリーム処理ループ"""
        try:
            strategy = self.processing_strategies.get(stream_type, ProcessingStrategy.BUFFERED)
            
            while self.is_running:
                try:
                    if strategy == ProcessingStrategy.BATCH:
                        await self._process_batch(stream_type)
                    elif strategy == ProcessingStrategy.BUFFERED:
                        await self._process_buffered(stream_type)
                    
                    # 少し待機
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error in stream processing loop for {stream_type}: {e}")
                    await asyncio.sleep(1.0)  # エラー時は長めに待機
                    
        except Exception as e:
            logger.error(f"Critical error in stream processing for {stream_type}: {e}")
    
    async def _process_packet_immediately(self, packet: DataPacket):
        """即座パケット処理"""
        try:
            start_time = time.time()
            
            # リアルタイム分析実行
            result = await self._analyze_packet(packet)
            
            # 処理時間計算
            processing_time = (time.time() - start_time) * 1000
            
            # 結果作成
            processing_result = ProcessingResult(
                packet_id=packet.packet_id,
                processed_at=datetime.utcnow(),
                processing_time_ms=processing_time,
                result_data=result.get('analysis', {}),
                events_generated=result.get('events', []),
                status='completed'
            )
            
            # WebSocket配信
            await self.websocket_handler.broadcast_to_subscribers(
                packet.stream_type, processing_result
            )
            
            # メトリクス更新
            self._update_metrics(processing_time)
            
        except Exception as e:
            logger.error(f"Error processing packet immediately: {e}")
    
    async def _process_batch(self, stream_type: StreamType):
        """バッチ処理"""
        try:
            packets = self.stream_buffer.get_packets(
                stream_type, self.streaming_config.batch_size
            )
            
            if not packets:
                return
            
            # バッチ分析実行
            batch_results = await self._analyze_batch(packets)
            
            # 結果配信
            for result in batch_results:
                await self.websocket_handler.broadcast_to_subscribers(stream_type, result)
                
        except Exception as e:
            logger.error(f"Error processing batch for {stream_type}: {e}")
    
    async def _process_buffered(self, stream_type: StreamType):
        """バッファ処理"""
        try:
            packets = self.stream_buffer.get_packets(stream_type, 1)
            
            for packet in packets:
                await self._process_packet_immediately(packet)
                
        except Exception as e:
            logger.error(f"Error processing buffered packets for {stream_type}: {e}")
    
    async def _analyze_packet(self, packet: DataPacket) -> Dict[str, Any]:
        """パケット分析"""
        try:
            if not self.real_time_analyzer:
                return {'analysis': {}, 'events': []}
            
            # リアルタイム分析器にデータ追加
            await self.real_time_analyzer.add_data_point(packet.data)
            
            # 特徴量抽出
            features = self.real_time_analyzer.extract_realtime_features(packet.data)
            
            return {
                'analysis': {
                    'packet_id': packet.packet_id,
                    'features': features,
                    'timestamp': packet.timestamp.isoformat()
                },
                'events': []  # イベントは別途コールバックで処理
            }
            
        except Exception as e:
            logger.error(f"Error analyzing packet: {e}")
            return {'analysis': {}, 'events': []}
    
    async def _analyze_batch(self, packets: List[DataPacket]) -> List[ProcessingResult]:
        """バッチ分析"""
        try:
            results = []
            
            for packet in packets:
                start_time = time.time()
                analysis_result = await self._analyze_packet(packet)
                processing_time = (time.time() - start_time) * 1000
                
                result = ProcessingResult(
                    packet_id=packet.packet_id,
                    processed_at=datetime.utcnow(),
                    processing_time_ms=processing_time,
                    result_data=analysis_result.get('analysis', {}),
                    events_generated=analysis_result.get('events', []),
                    status='completed'
                )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing batch: {e}")
            return []
    
    def _update_metrics(self, processing_time_ms: float):
        """メトリクス更新"""
        try:
            self.processing_metrics['packets_processed'] += 1
            
            # 移動平均でレイテンシ更新
            current_latency = self.processing_metrics['average_latency_ms']
            self.processing_metrics['average_latency_ms'] = (
                current_latency * 0.9 + processing_time_ms * 0.1
            )
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}") 