"""
Data Collector Service

リアルタイムデータ収集・変換・前処理サービス
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import time
import threading
from queue import Queue, Empty
import logging
import json
import uuid

from core.camera import Camera
from core.detector import Detector
from core.state import StateManager
from models.behavior_log import BehaviorLog
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataCollector:
    """データ収集サービス
    
    監視システムからのリアルタイムデータを収集し、構造化してストレージに保存
    """
    
    def __init__(self, 
                 camera: Camera,
                 detector: Detector,
                 state_manager: StateManager,
                 collection_interval: float = 2.0,
                 flask_app=None):
        """初期化
        
        Args:
            camera: カメラインスタンス
            detector: 検出エンジンインスタンス
            state_manager: 状態管理インスタンス
            collection_interval: データ収集間隔（秒）- デフォルト2秒（リアルタイム性向上）
            flask_app: Flaskアプリケーションインスタンス（Phase 2追加）
        """
        self.camera = camera
        self.detector = detector
        self.state_manager = state_manager
        self.collection_interval = collection_interval
        self.flask_app = flask_app                   # Phase 2: Flaskアプリ保持
        
        # データ収集制御
        self._collecting = False
        self._collection_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._data_lock = threading.Lock()
        
        # セッション管理
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        
        # データ処理キューイング - リアルタイム性を重視した設定
        self._pending_data: List[Dict[str, Any]] = []
        self._batch_size = 5  # 10→5に削減（短時間でのバッチ保存）
        
        # コールバック機能
        self._data_callbacks: List[Callable] = []
        
        logger.info(f"DataCollector initialized with {collection_interval}s interval (Real-time optimized)")
        
        # Phase 2: デバッグログ追加
        logger.debug(f"DataCollector debug info - Camera: {camera}, Detector: {detector}, StateManager: {state_manager}")
    
    def start_collection(self, session_id: Optional[str] = None) -> bool:
        """データ収集を開始
        
        Args:
            session_id: 学習セッションID（None の場合は自動生成）
            
        Returns:
            bool: 開始成功フラグ
        """
        logger.info(f"start_collection called with session_id: {session_id}")
        
        if self._collecting:
            logger.warning("Data collection already running")
            return False
        
        try:
            logger.debug("Setting up session...")
            # セッション開始
            self.current_session_id = session_id or self._generate_session_id()
            self.session_start_time = datetime.utcnow()
            logger.info(f"Session setup complete: {self.current_session_id}")
            
            logger.debug("Preparing collection thread...")
            # 収集スレッド開始
            self._stop_event.clear()
            self._collecting = True
            logger.debug("Creating collection thread...")
            self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
            logger.debug("Starting collection thread...")
            self._collection_thread.start()
            logger.debug("Collection thread started")
            
            # スレッドが実際に開始されたかを確認
            time.sleep(0.1)  # 短時間待機
            if self._collection_thread.is_alive():
                logger.info("Collection thread is alive and running")
            else:
                logger.error("Collection thread failed to start or died immediately")
                self._collecting = False
                return False
            
            logger.info(f"Data collection started - Session: {self.current_session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start data collection: {e}", exc_info=True)
            self._collecting = False
            return False
    
    def stop_collection(self) -> bool:
        """データ収集を停止
        
        Returns:
            bool: 停止成功フラグ
        """
        if not self._collecting:
            logger.warning("Data collection not running")
            return False
        
        try:
            logger.info("Stopping data collection...")
            
            # Step 1: 収集停止フラグを設定
            self._collecting = False
            self._stop_event.set()
            logger.info("Stop signal sent to collection thread")
            
            # Step 2: スレッド終了を待機（タイムアウト付き）
            if self._collection_thread and self._collection_thread.is_alive():
                logger.info("Waiting for collection thread to finish...")
                self._collection_thread.join(timeout=3.0)  # 3秒に短縮
                
                # スレッドが終了しない場合の対処
                if self._collection_thread.is_alive():
                    logger.warning("Collection thread did not finish in time, but continuing...")
            
            # Step 3: 残存データの保存（デッドロック回避版）
            logger.info("Flushing remaining data...")
            self._safe_flush_pending_data()
            
            logger.info(f"Data collection stopped - Session: {self.current_session_id}")
            
            # Step 4: セッション終了
            self.current_session_id = None
            self.session_start_time = None
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop data collection: {e}", exc_info=True)
            return False
    
    def _safe_flush_pending_data(self) -> None:
        """デッドロック回避版のデータ保存"""
        try:
            # データのコピーを作成（ロック外で操作するため）
            data_to_save = []
            with self._data_lock:
                if self._pending_data:
                    data_to_save = self._pending_data.copy()
                    self._pending_data.clear()
            
            if not data_to_save:
                logger.info("No pending data to save during cleanup")
                return
            
            logger.info(f"Saving {len(data_to_save)} pending data entries during cleanup")
            
            # Flask app context内でデータベース操作を実行
            if self.flask_app:
                with self.flask_app.app_context():
                    self._save_batch_to_database(data_to_save)
            else:
                logger.error("Flask app not available for cleanup database operations")
            
        except Exception as e:
            logger.error(f"Error in safe flush: {e}", exc_info=True)
    
    def _collection_loop(self) -> None:
        """データ収集メインループ"""
        try:
            logger.info("Data collection loop started")
            logger.debug(f"Collection loop thread ID: {threading.current_thread().ident}")
            logger.debug(f"Collection flags - collecting: {self._collecting}, stop_event: {self._stop_event.is_set()}")
            
            loop_count = 0  # Phase 2: ループカウンタ追加
            
            while self._collecting and not self._stop_event.is_set():
                try:
                    loop_count += 1
                    # ループ進行はサンプリングして出力（例：100回に1回）
                    if loop_count % 100 == 0:
                        logger.info(f"Data collection loop iteration #{loop_count}")
                    
                    # データ収集実行
                    data = self._collect_single_frame()
                    
                    if data:
                        # 収集成功ログは5分間隔で出力
                        if loop_count % 150 == 0:  # 150回＝2秒×150＝5分間隔
                            logger.info(f"Collected data successfully: session_id={data.get('session_id')}, presence={data.get('presence_status')}")
                        # データ処理とキューイング
                        self._queue_data(data)
                        
                        # コールバック実行
                        self._trigger_callbacks(data)
                    else:
                        logger.debug("No data collected in this iteration")  # WARNINGからDEBUGに変更
                    
                    # 次回収集まで待機
                    self._stop_event.wait(self.collection_interval)
                    
                except Exception as e:
                    logger.error(f"Error in collection loop iteration: {e}", exc_info=True)
                    # エラー時は短めの間隔で再試行
                    self._stop_event.wait(min(5.0, self.collection_interval))
            
            logger.info("Data collection loop ended")
            
        except Exception as e:
            logger.error(f"Fatal error in collection loop: {e}", exc_info=True)
        finally:
            logger.info("Collection loop cleanup completed")
    
    def _collect_single_frame(self) -> Optional[Dict[str, Any]]:
        """単一フレームのデータ収集
        
        Returns:
            dict or None: 収集データ
        """
        start_time = time.time()
        
        try:
            # フレーム取得
            frame = self.camera.get_frame()
            if frame is None:
                logger.warning("Failed to get camera frame")
                return None
            
            # 検出実行（Phase 1修正: detect → detect_objects）
            detection_results = self.detector.detect_objects(frame)
            
            # 状態情報取得
            state_info = self.state_manager.get_status_summary()
            
            # データ構造化
            collected_data = self._structure_data(
                detection_results, 
                state_info, 
                processing_time=(time.time() - start_time) * 1000
            )
            
            return collected_data
            
        except Exception as e:
            logger.error(f"Error collecting frame data: {e}")
            return None
    
    def _structure_data(self, 
                       detection_results: Dict[str, Any],
                       state_info: Dict[str, Any],
                       processing_time: float) -> Dict[str, Any]:
        """データを構造化
        
        Args:
            detection_results: 検出結果
            state_info: 状態情報
            processing_time: 処理時間（ミリ秒）
            
        Returns:
            dict: 構造化されたデータ
        """
        timestamp = datetime.utcnow()
        
        # YOLOv8検出結果の変換
        detected_objects = self._convert_detection_results(detection_results.get('yolo', {}))
        
        # MediaPipe結果の変換
        mediapipe_results = detection_results.get('mediapipe', {})
        focus_level = self._calculate_focus_level(mediapipe_results)
        posture_data = self._extract_posture_data(mediapipe_results)
        face_landmarks = mediapipe_results.get('face_landmarks')
        
        # スマートフォン検出
        smartphone_detected = self._detect_smartphone_usage(detected_objects, mediapipe_results)
        
        # 環境データ
        environment_data = self._collect_environment_data()
        
        # 構造化データ
        structured_data = {
            'timestamp': timestamp,
            'session_id': self.current_session_id,
            'detected_objects': detected_objects,
            'focus_level': focus_level,
            'posture_data': posture_data,
            'face_landmarks': face_landmarks,
            'smartphone_detected': smartphone_detected,
            'presence_status': 'present' if state_info.get('personDetected') else 'absent',
            'environment_data': environment_data,
            'confidence_scores': detection_results.get('confidence_scores', {}),
            'processing_time': processing_time
        }
        
        return structured_data
    
    def _convert_detection_results(self, yolo_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """YOLOv8検出結果を変換
        
        Args:
            yolo_results: YOLO検出結果
            
        Returns:
            list: 変換された検出オブジェクトリスト
        """
        detected_objects = []
        
        detections = yolo_results.get('detections', [])
        for detection in detections:
            obj = {
                'class': detection.get('class_name', 'unknown'),
                'confidence': detection.get('confidence', 0.0),
                'bbox': detection.get('bbox', []),
                'area': self._calculate_bbox_area(detection.get('bbox', [])),
                'center': self._calculate_bbox_center(detection.get('bbox', []))
            }
            detected_objects.append(obj)
        
        return detected_objects
    
    def _calculate_focus_level(self, mediapipe_results: Dict[str, Any]) -> Optional[float]:
        """集中度レベルを計算
        
        Args:
            mediapipe_results: MediaPipe検出結果
            
        Returns:
            float or None: 集中度スコア (0.0-1.0)
        """
        try:
            # Phase 5.1: デバッグログ追加 - 実際のデータ構造を確認
            logger.debug(f"MediaPipe results structure: {list(mediapipe_results.keys()) if mediapipe_results else 'Empty'}")
            
            # 実際のデータ構造に対応した取得方法に修正
            pose_data = mediapipe_results.get('pose_landmarks')  # pose → pose_landmarks
            face_data = mediapipe_results.get('face_landmarks')  # face → face_landmarks
            hands_data = mediapipe_results.get('hand_landmarks') # hands 追加
            
            # デバッグ情報の追加
            logger.debug(f"Pose data available: {pose_data is not None}")
            logger.debug(f"Face data available: {face_data is not None}")
            logger.debug(f"Hands data available: {hands_data is not None}")
            
            # データが何もない場合はデフォルト値を返す（None ではなく）
            if not pose_data and not face_data:
                logger.debug("No pose or face data available, returning default focus level 0.5")
                return 0.5  # Phase 5.1: デフォルト値を設定（None → 0.5）
            
            focus_factors = []
            
            # 顔の向き（正面度）- 実際のface_landmarksデータを使用
            if face_data:
                # 実際のランドマークからの推定（簡易版）
                frontal_score = 0.7  # 暫定的な固定値、後で実装改善
                focus_factors.append(frontal_score * 0.4)
                logger.debug(f"Face factor added: {frontal_score * 0.4}")
            
            # 姿勢の安定性 - 実際のpose_landmarksデータを使用
            if pose_data:
                # 実際のランドマークからの推定（簡易版）
                posture_stability = 0.6  # 暫定的な固定値、後で実装改善
                focus_factors.append(posture_stability * 0.3)
                logger.debug(f"Posture factor added: {posture_stability * 0.3}")
            
            # 動きの少なさ（集中時は動きが少ない）
            movement_score = self._calculate_movement_score(mediapipe_results)
            if movement_score is not None:
                movement_factor = (1.0 - movement_score) * 0.3
                focus_factors.append(movement_factor)
                logger.debug(f"Movement factor added: {movement_factor}")
            
            # 集中度計算
            if focus_factors:
                calculated_focus = min(1.0, max(0.0, sum(focus_factors)))
                logger.debug(f"Calculated focus level: {calculated_focus} from factors: {focus_factors}")
                return calculated_focus
            
            # フォールバック値
            logger.debug("No focus factors calculated, returning default 0.5")
            return 0.5
            
        except Exception as e:
            logger.error(f"Error calculating focus level: {e}", exc_info=True)
            return 0.5  # Phase 5.1: エラー時もデフォルト値を返す
    
    def _extract_posture_data(self, mediapipe_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """姿勢データを抽出
        
        Args:
            mediapipe_results: MediaPipe検出結果
            
        Returns:
            dict or None: 姿勢データ
        """
        try:
            # Phase 5.1: 実際のデータ構造に対応
            pose_data = mediapipe_results.get('pose_landmarks')
            
            if not pose_data:
                logger.debug("No pose landmarks available for posture data")
                # Phase 5.1: デフォルト姿勢データを返す
                return {
                    'head_position': 0.0,
                    'shoulder_alignment': 0.0,
                    'spine_alignment': 0.0,
                    'posture_score': 0.5  # デフォルト値
                }
            
            # Phase 5.1: 実際のランドマークからの推定（簡易版）
            posture_data = {
                'head_position': 0.0,  # 暫定値、後で実装改善
                'shoulder_alignment': 0.0,  # 暫定値
                'spine_alignment': 0.0,  # 暫定値
                'posture_score': 0.6  # 暫定値、後でランドマーク解析実装
            }
            
            logger.debug(f"Extracted posture data: {posture_data}")
            return posture_data
            
        except Exception as e:
            logger.error(f"Error extracting posture data: {e}", exc_info=True)
            # Phase 5.1: エラー時もデフォルト値を返す
            return {
                'head_position': 0.0,
                'shoulder_alignment': 0.0,
                'spine_alignment': 0.0,
                'posture_score': 0.5
            }
    
    def _detect_smartphone_usage(self, 
                                detected_objects: List[Dict],
                                mediapipe_results: Dict[str, Any]) -> bool:
        """スマートフォン使用を検出
        
        Args:
            detected_objects: 検出オブジェクト
            mediapipe_results: MediaPipe結果
            
        Returns:
            bool: スマートフォン使用フラグ
        """
        try:
            # YOLOでのスマートフォン検出
            for obj in detected_objects:
                if obj['class'] in ['cell phone', 'smartphone', 'mobile']:
                    logger.debug(f"Smartphone detected via YOLO: {obj['class']}")
                    return True
            
            # Phase 5.1: 実際のデータ構造に対応した手の位置と顔の向きからの推定
            hands_data = mediapipe_results.get('hand_landmarks')
            face_data = mediapipe_results.get('face_landmarks')
            
            logger.debug(f"Smartphone detection - Hands: {hands_data is not None}, Face: {face_data is not None}")
            
            if hands_data and face_data:
                # Phase 5.1: 簡易的な推定（後で改善）
                # 実際のランドマーク解析は複雑なため、暫定的にFalseを返す
                logger.debug("Hand and face landmarks available, but smartphone detection logic needs implementation")
                return False  # 暫定的にFalse
            
            logger.debug("No smartphone usage detected")
            return False
            
        except Exception as e:
            logger.error(f"Error detecting smartphone usage: {e}", exc_info=True)
            return False
    
    def _collect_environment_data(self) -> Dict[str, Any]:
        """環境データを収集
        
        Returns:
            dict: 環境データ
        """
        # 基本的な環境情報（将来的にセンサー追加可能）
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'lighting': None,  # 将来的に照度センサー
            'noise_level': None,  # 将来的に音量センサー
            'temperature': None,  # 将来的に温度センサー
        }
    
    def _calculate_movement_score(self, mediapipe_results: Dict[str, Any]) -> Optional[float]:
        """動きスコアを計算
        
        Args:
            mediapipe_results: MediaPipe結果
            
        Returns:
            float or None: 動きスコア (0.0-1.0)
        """
        try:
            # Phase 5.1: 実際のデータ構造に対応
            pose_data = mediapipe_results.get('pose_landmarks')
            
            logger.debug(f"Movement calculation - Pose data available: {pose_data is not None}")
            
            # Phase 5.1: 簡易的な動き検出（将来的に時系列データでの詳細計算）
            if pose_data:
                # 暫定的に低い動きスコアを返す（実際のランドマーク解析は後で実装）
                movement_score = 0.1  # 最小動きレベル
                logger.debug(f"Movement score calculated: {movement_score}")
                return movement_score
            
            # ポーズデータがない場合のデフォルト値
            logger.debug("No pose data available, returning default movement score 0.2")
            return 0.2
            
        except Exception as e:
            logger.error(f"Error calculating movement score: {e}", exc_info=True)
            return 0.1  # エラー時は最小動きレベル
    
    def _calculate_bbox_area(self, bbox: List[float]) -> float:
        """バウンディングボックスの面積計算"""
        if len(bbox) >= 4:
            return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        return 0.0
    
    def _calculate_bbox_center(self, bbox: List[float]) -> List[float]:
        """バウンディングボックスの中心計算"""
        if len(bbox) >= 4:
            return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
        return [0.0, 0.0]
    
    def _queue_data(self, data: Dict[str, Any]) -> None:
        """データをキューに追加
        
        Args:
            data: 収集データ
        """
        should_flush = False
        
        with self._data_lock:
            logger.debug(f"Adding data to queue. Current queue size: {len(self._pending_data)}")
            self._pending_data.append(data)
            logger.debug(f"Data added to queue. New queue size: {len(self._pending_data)}")
            logger.debug(f"Batch size threshold: {self._batch_size}")
            
            # バッチサイズに達したかチェック（ロック内）
            if len(self._pending_data) >= self._batch_size:
                logger.info(f"Batch size reached ({len(self._pending_data)}>={self._batch_size}). Will trigger flush.")
                should_flush = True
            else:
                logger.debug(f"Batch size not reached yet ({len(self._pending_data)}<{self._batch_size}). Waiting for more data.")
        
        # フラッシュをロック外で実行（デッドロック回避）
        if should_flush:
            logger.debug("Executing flush outside of data lock")
            self._flush_pending_data()
    
    def _flush_pending_data(self) -> None:
        """待機中のデータを保存"""
        with self._data_lock:
            if not self._pending_data:
                logger.debug("No pending data to flush")
                return
            
            # バッチサイズでデータを分割
            batch_size = min(len(self._pending_data), self._batch_size)
            if batch_size == 0:
                logger.debug("Batch size is 0, nothing to flush")
                return
            
            batch = self._pending_data[:batch_size]
            logger.info(f"データベースにバッチ保存開始: {batch_size}件")
            logger.debug(f"Flask app available: {self.flask_app is not None}")
            
            try:
                # Flask app context内でデータベース操作を実行
                if self.flask_app:
                    logger.debug("Entering Flask app context for database operations")
                    with self.flask_app.app_context():
                        logger.debug("Flask app context entered successfully")
                        self._save_batch_to_database(batch)
                        logger.debug("Batch save completed successfully")
                else:
                    # Flask appが利用できない場合の警告
                    logger.error("Flask app not available for database operations")
                    return
                    
                # キューをクリア
                self._pending_data = self._pending_data[batch_size:]
                logger.info(f"Pending data queue cleared, remaining: {len(self._pending_data)} items")
                
            except Exception as e:
                logger.error(f"バッチ保存エラー: {e}", exc_info=True)
                logger.error(f"Error details - Flask app: {self.flask_app}, batch size: {batch_size}")
                logger.error(f"First batch item keys: {list(batch[0].keys()) if batch else 'No batch data'}")
    
    def _save_batch_to_database(self, batch):
        """Flask app context内でバッチデータをデータベースに保存"""
        logger.debug(f"Starting database save operation for {len(batch)} items")
        
        from models import db
        logger.debug("Successfully imported db from models")
        
        saved_count = 0
        
        try:
            logger.debug("Starting batch processing loop")
            for i, data in enumerate(batch):
                try:
                    logger.debug(f"Processing batch item {i+1}/{len(batch)}")
                    # 直接BehaviorLogインスタンスを作成
                    from models.behavior_log import BehaviorLog
                    from datetime import datetime
                    
                    logger.debug(f"Creating BehaviorLog instance with data keys: {list(data.keys())}")
                    
                    behavior_log = BehaviorLog(
                        timestamp=data.get('timestamp') or datetime.utcnow(),
                        detected_objects=data.get('detected_objects'),
                        focus_level=data.get('focus_level'),
                        posture_data=data.get('posture_data'),
                        smartphone_detected=data.get('smartphone_detected', False),
                        presence_status=data.get('presence_status'),
                        session_id=data.get('session_id'),
                        face_landmarks=data.get('face_landmarks'),
                        environment_data=data.get('environment_data'),
                        confidence_scores=data.get('confidence_scores'),
                        processing_time=data.get('processing_time')
                    )
                    
                    logger.debug(f"BehaviorLog instance created successfully for item {i+1}")
                    db.session.add(behavior_log)
                    logger.debug(f"Added BehaviorLog to session for item {i+1}")
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error creating BehaviorLog entry for item {i+1}: {e}", exc_info=True)
                    continue
            
            logger.debug(f"Attempting to commit {saved_count} items to database")
            # 一括コミット
            db.session.commit()
            logger.info(f"データベース保存完了: {saved_count}件")
            
        except Exception as e:
            logger.error(f"データベース保存処理エラー: {e}", exc_info=True)
            logger.error(f"Database session state: {db.session}")
            # ロールバック
            try:
                logger.debug("Attempting database rollback")
                db.session.rollback()
                logger.debug("Database rollback completed")
            except Exception as rollback_error:
                logger.error(f"ロールバックエラー: {rollback_error}")
    
    def _trigger_callbacks(self, data: Dict[str, Any]) -> None:
        """データコールバックを実行
        
        Args:
            data: 収集データ
        """
        for callback in self._data_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in data callback: {e}")
    
    def add_data_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """データコールバックを追加
        
        Args:
            callback: コールバック関数
        """
        self._data_callbacks.append(callback)
    
    def remove_data_callback(self, callback: Callable) -> None:
        """データコールバックを削除
        
        Args:
            callback: 削除するコールバック関数
        """
        if callback in self._data_callbacks:
            self._data_callbacks.remove(callback)
    
    def get_session_summary(self) -> Optional[Dict[str, Any]]:
        """現在のセッションサマリーを取得
        
        Returns:
            dict or None: セッションサマリー
        """
        if not self.current_session_id or not self.session_start_time:
            return None
        
        try:
            # セッション期間のログを取得
            logs = BehaviorLog.get_recent_logs(
                hours=24,  # 最大24時間
                session_id=self.current_session_id
            )
            
            if not logs:
                return None
            
            # 統計計算
            focus_scores = [log.focus_level for log in logs if log.focus_level is not None]
            smartphone_usage_count = sum(1 for log in logs if log.smartphone_detected)
            
            duration = datetime.utcnow() - self.session_start_time
            
            summary = {
                'session_id': self.current_session_id,
                'start_time': self.session_start_time.isoformat(),
                'duration_minutes': duration.total_seconds() / 60,
                'total_entries': len(logs),
                'average_focus': sum(focus_scores) / len(focus_scores) if focus_scores else None,
                'smartphone_usage_rate': smartphone_usage_count / len(logs) if logs else 0,
                'presence_rate': len([log for log in logs if log.presence_status == 'present']) / len(logs) if logs else 0
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return None
    
    def _generate_session_id(self) -> str:
        """セッションIDを生成
        
        Returns:
            str: セッションID
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_id}"
    
    @property
    def is_collecting(self) -> bool:
        """データ収集中かどうか
        
        Returns:
            bool: 収集中フラグ
        """
        return self._collecting
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """データ収集統計を取得
        
        Returns:
            dict: 収集統計
        """
        return {
            'is_collecting': self._collecting,
            'current_session_id': self.current_session_id,
            'session_start_time': self.session_start_time.isoformat() if self.session_start_time else None,
            'collection_interval': self.collection_interval,
            'pending_data_count': len(self._pending_data),
            'callbacks_count': len(self._data_callbacks)
        } 