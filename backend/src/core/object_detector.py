import cv2
import torch
from ultralytics import YOLO
import mediapipe as mp
import os
import numpy as np
import asyncio
import threading
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    ModelError, ModelInitializationError, ModelInferenceError,
    YOLOError, MediaPipeError, DetectionError, ConfigError,
    HardwareError, OptimizationError, SmoothingError, wrap_exception
)
from core.ai_optimizer import AIOptimizer
from core.detection_smoother import DetectionSmoother
import shutil
from pathlib import Path
from ultralytics.utils import SETTINGS

logger = setup_logger(__name__)


class ObjectDetector:
    """
    物体検出専門クラス
    - YOLO初期化と推論
    - MediaPipe初期化と推論
    - 検出結果の統合処理
    - 検出結果の平滑化（点滅抑制）
    - 検出結果のデータベース保存
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        try:
            self.config_manager = config_manager
            
            # 設定からランドマークと検出オブジェクトの設定を取得
            self.landmark_settings = {}
            self.detection_objects = {}
            if config_manager:
                self.landmark_settings = config_manager.get_landmark_settings()
                self.detection_objects = config_manager.get_detection_objects()
            
            # 検出システムの初期化
            self.use_mediapipe = False
            self.use_yolo = True
            
            # MediaPipe初期化
            self._setup_mediapipe()
            
            # YOLO初期化
            self._setup_yolo()
            
            # AI最適化システムの初期化
            try:
                self.ai_optimizer = AIOptimizer(config_manager)
                logger.info("AIOptimizer integrated successfully")
            except Exception as e:
                optimization_error = wrap_exception(
                    e, OptimizationError,
                    "AIOptimizer initialization failed, using standard processing",
                    details={'optimization_disabled': True}
                )
                logger.warning(f"AIOptimizer error: {optimization_error.to_dict()}")
                self.ai_optimizer = None
            
            # 検出結果平滑化システムの初期化
            try:
                self.detection_smoother = DetectionSmoother(config_manager)
                logger.info("DetectionSmoother integrated successfully")
            except Exception as e:
                smoothing_error = wrap_exception(
                    e, SmoothingError,
                    "DetectionSmoother initialization failed, disabling smoothing",
                    details={'smoothing_disabled': True}
                )
                logger.warning(f"DetectionSmoother error: {smoothing_error.to_dict()}")
                self.detection_smoother = None
            
            # 検出ログ保存設定
            self.log_detections = config_manager.get('detector.log_detections', False) if config_manager else False
            self.camera_id = config_manager.get('camera.id', 'main') if config_manager else 'main'
            self.log_queue = []
            self.log_thread = None
            self.log_thread_running = False
            self.log_interval = config_manager.get('detector.log_interval', 300) if config_manager else 300  # 5分ごと
            self.last_summary_time = datetime.utcnow()
            
            # 検出ログ保存スレッドの起動（設定が有効な場合）
            if self.log_detections:
                self._start_log_thread()
            
            logger.info("ObjectDetector initialized successfully.")
            
        except Exception as e:
            init_error = wrap_exception(
                e, ModelInitializationError,
                "ObjectDetector initialization failed, disabling all detection systems",
                details={
                    'mediapipe_disabled': True,
                    'yolo_disabled': True,
                    'fallback_mode': True
                }
            )
            logger.error(f"Critical initialization error: {init_error.to_dict()}")
            # 初期化中に予期せぬエラーがあれば両方無効にする
            self.use_mediapipe = False
            self.use_yolo = False
            logger.critical("Disabling both MediaPipe and YOLO due to critical error during initialization.")

    def _setup_mediapipe(self) -> None:
        """MediaPipeコンポーネントの初期化"""
        if self.config_manager:
            self.use_mediapipe = self.config_manager.get('detector.use_mediapipe', False)
            logger.info(f"MediaPipe status from config: {'enabled' if self.use_mediapipe else 'disabled'}")
        
        if not self.use_mediapipe:
            logger.info("MediaPipe usage is disabled in config.")
            return
            
        try:
            # MediaPipe内部の警告を抑制
            os.environ["MEDIAPIPE_DISABLE_GPU"] = "1"  # GPUを無効化して安定性向上
            
            # MediaPipe警告抑制のための追加設定
            os.environ["GLOG_minloglevel"] = "2"  # ERROR以上のログのみ表示
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # TensorFlow警告抑制
            
            self.mp_pose = mp.solutions.pose
            self.mp_hands = mp.solutions.hands
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            
            # Poseモデル初期化（警告軽減設定）
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=0,  # 軽量モデルを使用
                smooth_landmarks=True,
                min_detection_confidence=0.7,  # 信頼度閾値を上げる
                min_tracking_confidence=0.7,   # 信頼度閾値を上げる
                enable_segmentation=False
            )
            logger.info("MediaPipe Pose model initialized with warning suppression")
            
            # Handsモデル初期化（設定が有効な場合）
            if self.landmark_settings.get('hands', {}).get('enabled', False):
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                logger.info("MediaPipe Hands model initialized successfully")
            
            # Face Meshモデル初期化（設定が有効な場合）
            if self.landmark_settings.get('face', {}).get('enabled', False):
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                logger.info("MediaPipe Face Mesh model initialized successfully")
                
        except Exception as e:
            mediapipe_error = wrap_exception(
                e, MediaPipeError,
                "MediaPipe components initialization failed",
                details={
                    'component_disabled': True,
                    'gpu_disabled': True,
                    'config_settings': self.landmark_settings
                }
            )
            logger.error(f"MediaPipe initialization error: {mediapipe_error.to_dict()}")
            self.use_mediapipe = False

    def _setup_yolo(self) -> None:
        """YOLO物体検出器の初期化"""
        if self.config_manager:
            self.use_yolo = self.config_manager.get('detector.use_yolo', True)
        
        if not self.use_yolo:
            logger.info("YOLO object detector is disabled.")
            return
            
        try:
            # モデルファイルのパスを設定
            model_name = self.config_manager.get('models.yolo.model_name', 'yolov8n.pt') if self.config_manager else 'yolov8n.pt'
            
            # モデルディレクトリの設定
            if self.config_manager:
                models_dir_rel = self.config_manager.get('models.yolo.models_dir', 'models')
                # プロジェクトルートからの相対パスを絶対パスに変換
                project_root = Path(__file__).resolve().parent.parent.parent
                models_dir = project_root / models_dir_rel
            else:
                # 設定がない場合はデフォルトパスを使用
                project_root = Path(__file__).resolve().parent.parent.parent
                models_dir = project_root / "models"
            
            # モデルディレクトリが存在しない場合は作成
            os.makedirs(models_dir, exist_ok=True)
            
            # モデルの絶対パスを設定
            model_path = models_dir / model_name
            
            # モデルが存在しない場合はダウンロードして保存
            if not model_path.exists():
                logger.warning(f"YOLOモデルファイルが見つかりません: {model_path}。'{model_name}' をダウンロードします...")
                self.model = YOLO(model_name)  # ダウンロード実行

                # ダウンロードしたモデルファイルを所定の場所にコピー
                weights_dir = Path(SETTINGS['weights_dir'])
                source_model_path = weights_dir / model_name
                
                if source_model_path.exists():
                    logger.info(f"ダウンロードしたモデルをコピーします: {source_model_path} -> {model_path}")
                    shutil.copy(source_model_path, model_path)
                    logger.info(f"モデルを正常に保存しました: {model_path}")
                else:
                    logger.error(f"モデルの保存に失敗しました。ダウンロードされたモデルがキャッシュに見つかりません: {source_model_path}")

            else:
                logger.info(f"既存のYOLOモデルを読み込みます: {model_path}")

            # モデルをインスタンス化（ローカルパスから）
            self.model = YOLO(str(model_path))
            
            # YOLOモデルの最適化設定
            self.model.verbose = False
            
            # NMS処理最適化 - 警告軽減のための設定
            self.yolo_predict_args = {
                'verbose': False,           # 詳細ログ無効化
                'conf': 0.5,               # 信頼度閾値
                'iou': 0.7,                # IoU閾値（NMS処理）
                'max_det': 10,             # 最大検出数制限（NMS軽量化）
                'agnostic_nms': False,     # クラス別NMS
                'save': False,             # 結果保存無効
                'save_txt': False,         # テキスト保存無効
                'save_conf': False,        # 信頼度保存無効
                'save_crop': False,        # クロップ保存無効
                'show': False,             # 表示無効
                'half': False,             # 半精度計算（CPUでは無効）
            }
            
            # デバイスの設定
            if torch.backends.mps.is_built():
                self.device = torch.device("mps")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
            
            logger.info(f"Using device: {self.device}")
            self.model.to(self.device)
            logger.info("YOLO initialized with NMS optimization settings")
            
        except Exception as e:
            # KeyError / TypeError など入力フォーマット系は recoverable
            data_error_classes = (KeyError, AttributeError, TypeError, ValueError)
            critical = not isinstance(e, data_error_classes)

            yolo_runtime_error = wrap_exception(
                e, YOLOError,
                "YOLO object detection runtime error",
                details={
                    'frame_shape': frame.shape if frame is not None else None,
                    'model_available': hasattr(self, 'model'),
                    'device': str(self.device) if hasattr(self, 'device') else 'unknown',
                    'yolo_disabled': critical
                }
            )
            logger.error(f"YOLO runtime error: {yolo_runtime_error.to_dict()}")

            if critical:
                # モデル破損など致命的な場合のみ無効化
                self.use_yolo = False
                logger.warning("Disabling YOLO due to critical runtime error.")
            else:
                # recoverable エラーの場合は次フレームで再試行
                logger.warning("Recoverable YOLO data error; keeping YOLO enabled.")

    def detect_objects(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        フレーム内の物体を検出
        
        Args:
            frame: 検出対象の画像フレーム
            
        Returns:
            検出結果を含む辞書
        """
        if frame is None or frame.size == 0:
            logger.warning("Empty frame received for object detection")
            return self._create_empty_results()
            
        try:
            # AIオプティマイザーがある場合、最適化処理を適用
            if self.ai_optimizer:
                # フレームスキップ判定
                if self.ai_optimizer.should_skip_frame():
                    return self._create_empty_results()
                    
                # パフォーマンスモニタリング開始
                self.ai_optimizer.start_inference_timer()
                
            # 結果格納用辞書
            results = {
                'detections': {},             # クラス名 → List[detection]
                'timestamp': datetime.now().isoformat(),
                'frame_id': id(frame),
                'mediapipe_results': {},
                'yolo_results': {},
                'person_detected': False     # 人物検出フラグを明示的に初期化
            }
            
            # MediaPipe検出（有効な場合）
            if self.use_mediapipe:
                # RGB変換（MediaPipeはRGBを使用）
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self._detect_with_mediapipe(rgb_frame, results)
            
            # YOLO検出（有効な場合）
            if self.use_yolo:
                self._detect_with_yolo_bgr(frame, results)
            
            # 検出結果の平滑化処理（有効な場合）
            if self.detection_smoother:
                results = self.detection_smoother.smooth_detections(results)
            
            # AIオプティマイザーがある場合、パフォーマンス測定終了
            if self.ai_optimizer:
                self.ai_optimizer.end_inference_timer()
                
                # パフォーマンス情報を結果に追加
                performance_metrics = self.ai_optimizer.get_performance_metrics()
                results['performance'] = performance_metrics
                
            # 検出ログ保存（設定が有効な場合）
            if self.log_detections and results.get('detections'):
                self._queue_detection_logs(results)
                
            return results
            
        except Exception as e:
            detection_error = wrap_exception(
                e, DetectionError,
                "Error during object detection",
                details={'frame_shape': frame.shape if frame is not None else None}
            )
            logger.error(f"Detection error: {detection_error.to_dict()}")
            return self._create_empty_results()

    def _detect_with_mediapipe(self, rgb_frame: np.ndarray, results: Dict[str, Any]) -> None:
        """
        MediaPipeを使用した検出処理
        
        Args:
            rgb_frame: RGB形式のフレーム
            results: 検出結果を格納する辞書
        """
        # Pose検出
        if hasattr(self, 'pose'):
            try:
                # AI最適化を使用した推論
                if self.ai_optimizer:
                    pose_results = self.ai_optimizer.optimize_mediapipe_pipeline(self.pose, rgb_frame)
                else:
                    # 標準推論
                    pose_results = self.pose.process(rgb_frame)
                if pose_results and pose_results.pose_landmarks:
                    results['person_detected'] = True
                    if self.landmark_settings.get('pose', {}).get('enabled', False):
                        results['pose_landmarks'] = pose_results.pose_landmarks
                        logger.debug(f"Pose landmarks detected and added to results")
            except Exception as e:
                pose_error = wrap_exception(
                    e, MediaPipeError,
                    "MediaPipe pose detection failed",
                    details={'detection_type': 'pose'}
                )
                logger.error(f"Pose detection error: {pose_error.to_dict()}")
        
        # Hands検出
        if (hasattr(self, 'hands') and 
            self.landmark_settings.get('hands', {}).get('enabled', False)):
            try:
                hands_results = self.hands.process(rgb_frame)
                if hands_results and hands_results.multi_hand_landmarks:
                    results['hands_landmarks'] = hands_results.multi_hand_landmarks
                    logger.debug(f"Hands landmarks detected and added to results")
            except Exception as e:
                hands_error = wrap_exception(
                    e, MediaPipeError,
                    "MediaPipe hands detection failed",
                    details={'detection_type': 'hands'}
                )
                logger.error(f"Hands detection error: {hands_error.to_dict()}")
        
        # Face検出
        if (hasattr(self, 'face_mesh') and 
            self.landmark_settings.get('face', {}).get('enabled', False)):
            try:
                face_results = self.face_mesh.process(rgb_frame)
                if face_results and face_results.multi_face_landmarks:
                    results['face_landmarks'] = face_results.multi_face_landmarks
                    logger.debug(f"Face landmarks detected and added to results")
            except Exception as e:
                face_error = wrap_exception(
                    e, MediaPipeError,
                    "MediaPipe face detection failed",
                    details={'detection_type': 'face'}
                )
                logger.error(f"Face detection error: {face_error.to_dict()}")

    def _detect_with_yolo_bgr(self, frame: np.ndarray, results: Dict[str, Any]) -> None:
        """
        YOLOを使用した物体検出処理（座標統一版）
        
        Args:
            frame: BGR形式のフレーム
            results: 検出結果を格納する辞書
        """
        try:
            # オリジナルフレームサイズを保持
            original_height, original_width = frame.shape[:2]
            
            # AI最適化でフレームサイズが変更される可能性があるため、
            # YOLOでも同じ最適化を適用して座標系を統一
            yolo_frame = frame
            scale_x, scale_y = 1.0, 1.0
            
            if self.ai_optimizer:
                # MediaPipeと同じフレーム最適化を適用
                yolo_frame = self.ai_optimizer._optimize_frame_preprocessing(frame)
                # スケール比を計算
                yolo_height, yolo_width = yolo_frame.shape[:2]
                scale_x = original_width / yolo_width
                scale_y = original_height / yolo_height
                
                # YOLO推論（最適化設定適用）
                yolo_results = self.ai_optimizer.optimize_yolo_inference(self.model, yolo_frame)
                # フレームスキップされた場合はNoneが返される
                if yolo_results is None:
                    return
                yolo_results = yolo_results[0]
            else:
                # 標準推論（NMS最適化設定適用）
                yolo_results = self.model(yolo_frame, **self.yolo_predict_args)[0]
            
            # YOLOでの人物検出（MediaPipeで未検出の場合のみチェック）
            if not results['person_detected']:
                for det in yolo_results.boxes.data.tolist():
                    x1, y1, x2, y2, conf, cls = det
                    class_name = yolo_results.names[int(cls)]
                    if class_name == 'person' and conf > 0.5:
                        results['person_detected'] = True
                        break
            
            # その他の物体検出
            for obj_key, obj_settings in self.detection_objects.items():
                if not obj_settings.get('enabled', False):
                    continue
                    
                detections = []
                for det in yolo_results.boxes.data.tolist():
                    x1, y1, x2, y2, conf, cls = det
                    detected_class = yolo_results.names[int(cls)]
                    
                    if (detected_class == obj_settings.get('class_name') and 
                        conf > obj_settings.get('confidence_threshold', 0.5)):
                        
                        # 座標をオリジナルフレームサイズにスケールバック
                        scaled_x1 = int(x1 * scale_x)
                        scaled_y1 = int(y1 * scale_y)
                        scaled_x2 = int(x2 * scale_x)
                        scaled_y2 = int(y2 * scale_y)
                        
                        logger.debug(f"物体を検出: {obj_settings.get('name')} (confidence: {conf:.3f}, bbox: ({scaled_x1}, {scaled_y1}, {scaled_x2}, {scaled_y2}))")
                        
                        detections.append({
                            'bbox': (scaled_x1, scaled_y1, scaled_x2, scaled_y2),
                            'confidence': conf
                        })
                        
                if detections:
                    results['detections'][obj_key] = detections
                    
        except Exception as e:
            yolo_runtime_error = wrap_exception(
                e, YOLOError,
                "YOLO object detection runtime error",
                details={
                    'frame_shape': frame.shape if frame is not None else None,
                    'model_available': hasattr(self, 'model'),
                    'device': str(self.device) if hasattr(self, 'device') else 'unknown',
                    'yolo_disabled': True
                }
            )
            logger.error(f"YOLO runtime error: {yolo_runtime_error.to_dict()}")
            # エラーが発生したらYOLOを無効化
            self.use_yolo = False
            logger.warning("Disabling YOLO due to runtime error.")

    def get_detection_status(self) -> Dict[str, Any]:
        """
        検出システムの状態情報を取得
        
        Returns:
            Dict[str, Any]: 状態情報
        """
        status = {
            'use_mediapipe': self.use_mediapipe,
            'use_yolo': self.use_yolo,
            'has_pose_model': hasattr(self, 'pose') if self.use_mediapipe else False,
            'has_hands_model': hasattr(self, 'hands') if self.use_mediapipe else False,
            'has_face_model': hasattr(self, 'face_mesh') if self.use_mediapipe else False,
            'has_yolo_model': hasattr(self, 'model') if self.use_yolo else False,
            'device': str(self.device) if hasattr(self, 'device') else 'unknown',
            'landmark_settings': self.landmark_settings,
            'detection_objects': self.detection_objects
        }
        
        # パフォーマンス統計を追加
        if self.ai_optimizer:
            status['performance'] = self.ai_optimizer.get_performance_stats()
        
        return status

    def reload_settings(self) -> None:
        """
        設定を再読み込みして検出システムを再初期化
        """
        logger.info("Reloading ObjectDetector settings...")
        if self.config_manager:
            self.landmark_settings = self.config_manager.get_landmark_settings()
            self.detection_objects = self.config_manager.get_detection_objects()
            self.use_mediapipe = self.config_manager.get('detector.use_mediapipe', False)
            self.use_yolo = self.config_manager.get('detector.use_yolo', True)
            logger.info(f"Settings reloaded: MediaPipe={'enabled' if self.use_mediapipe else 'disabled'}, YOLO={'enabled' if self.use_yolo else 'disabled'}")
        else:
            logger.warning("ConfigManager not available, cannot reload settings.") 

    def _queue_detection_logs(self, results: Dict[str, Any]) -> None:
        """
        検出結果をログキューに追加
        
        Args:
            results: 検出結果
        """
        try:
            frame_id = results.get('frame_id', 0)
            timestamp = datetime.utcnow()
            
            # 各検出オブジェクトをキューに追加
            for detection in results.get('detections', []):
                log_entry = {
                    'timestamp': timestamp,
                    'camera_id': self.camera_id,
                    'frame_id': frame_id,
                    'object_class': detection.get('class_name', 'unknown'),
                    'confidence': detection.get('confidence', 0.0),
                    'bbox': detection.get('bbox', (0, 0, 0, 0)),
                    'is_smoothed': detection.get('is_smoothed', False),
                    'is_interpolated': detection.get('is_interpolated', False),
                    'additional_data': {
                        'performance': results.get('performance', {})
                    }
                }
                self.log_queue.append(log_entry)
                
            # キューが一定サイズを超えたら即時保存
            if len(self.log_queue) >= 100:
                self._save_detection_logs_async()
                
            # サマリー作成時間チェック
            current_time = datetime.utcnow()
            if (current_time - self.last_summary_time).total_seconds() >= self.log_interval:
                self._create_detection_summary_async()
                self.last_summary_time = current_time
                
        except Exception as e:
            logger.error(f"Error queueing detection logs: {str(e)}")
    
    def _start_log_thread(self) -> None:
        """検出ログ保存スレッドを開始"""
        if self.log_thread_running:
            return
            
        self.log_thread_running = True
        self.log_thread = threading.Thread(target=self._log_thread_worker, daemon=True)
        self.log_thread.start()
        logger.info("Detection log thread started")
    
    def _log_thread_worker(self) -> None:
        """検出ログ保存スレッドのワーカー関数"""
        try:
            while self.log_thread_running:
                # 定期的にログを保存
                if self.log_queue:
                    self._save_detection_logs_sync()
                
                # スレッド休止
                time.sleep(10)  # 10秒ごとにチェック
                
        except Exception as e:
            logger.error(f"Error in log thread worker: {str(e)}")
        finally:
            logger.info("Detection log thread stopped")
    
    def _save_detection_logs_async(self) -> None:
        """検出ログを非同期で保存（メインスレッドをブロックしない）"""
        if not self.log_queue:
            return
            
        # キューのコピーを作成して空にする
        queue_copy = self.log_queue.copy()
        self.log_queue = []
        
        # 別スレッドで保存処理を実行
        thread = threading.Thread(
            target=self._save_logs_to_db,
            args=(queue_copy,),
            daemon=True
        )
        thread.start()
    
    def _save_detection_logs_sync(self) -> None:
        """検出ログを同期的に保存（ログスレッド内で使用）"""
        if not self.log_queue:
            return
            
        # キューのコピーを作成して空にする
        queue_copy = self.log_queue.copy()
        self.log_queue = []
        
        # DBに保存
        self._save_logs_to_db(queue_copy)
    
    def _save_logs_to_db(self, log_entries: List[Dict[str, Any]]) -> None:
        """
        検出ログをデータベースに保存
        
        Args:
            log_entries: 保存する検出ログエントリのリスト
        """
        try:
            # モデルのインポート（循環インポート回避のため）
            from models.detection_log import DetectionLog
            
            # 各ログエントリをDBに保存
            for entry in log_entries:
                log = DetectionLog.create_from_detection(
                    camera_id=entry['camera_id'],
                    frame_id=entry['frame_id'],
                    object_class=entry['object_class'],
                    confidence=entry['confidence'],
                    bbox=entry['bbox'],
                    is_smoothed=entry['is_smoothed'],
                    is_interpolated=entry['is_interpolated'],
                    additional_data=entry['additional_data']
                )
                log.save()
                
            logger.debug(f"Saved {len(log_entries)} detection logs to database")
            
        except Exception as e:
            logger.error(f"Error saving detection logs to database: {str(e)}")
    
    def _create_detection_summary_async(self) -> None:
        """検出サマリーを非同期で作成"""
        # 別スレッドでサマリー作成処理を実行
        thread = threading.Thread(
            target=self._create_detection_summary,
            daemon=True
        )
        thread.start()
    
    def _create_detection_summary(self) -> None:
        """検出サマリーを作成してデータベースに保存"""
        try:
            # モデルのインポート（循環インポート回避のため）
            from models.detection_log import DetectionLog
            from models.detection_summary import DetectionSummary
            
            # 集計期間
            end_time = datetime.utcnow()
            start_time = self.last_summary_time
            
            # 期間内のログを取得
            logs = DetectionLog.query.filter(
                DetectionLog.timestamp >= start_time,
                DetectionLog.timestamp <= end_time,
                DetectionLog.camera_id == self.camera_id
            ).all()
            
            if not logs:
                logger.debug("No detection logs found for summary creation")
                return
                
            # オブジェクトクラス別の集計
            object_stats = {}
            total_frames = len(set(log.frame_id for log in logs))
            
            for log in logs:
                obj_class = log.object_class
                if obj_class not in object_stats:
                    object_stats[obj_class] = {'count': 0, 'confidence_sum': 0.0}
                    
                object_stats[obj_class]['count'] += 1
                object_stats[obj_class]['confidence_sum'] += log.confidence
            
            # 平均信頼度の計算
            for obj_class, stats in object_stats.items():
                if stats['count'] > 0:
                    stats['avg_confidence'] = stats['confidence_sum'] / stats['count']
                    del stats['confidence_sum']
                else:
                    stats['avg_confidence'] = 0.0
                    del stats['confidence_sum']
            
            # サマリーの作成と保存
            summary = DetectionSummary.create_summary(
                camera_id=self.camera_id,
                start_time=start_time,
                end_time=end_time,
                total_frames=total_frames,
                object_stats=object_stats,
                metadata={
                    'ai_optimizer_enabled': self.ai_optimizer is not None,
                    'detection_smoother_enabled': self.detection_smoother is not None
                }
            )
            summary.save()
            
            # サマリーに関連するログを関連付け
            for log in logs:
                log.summary_id = summary.id
                log.save()
                
            logger.info(f"Created detection summary for period {start_time} to {end_time}")
            
        except Exception as e:
            logger.error(f"Error creating detection summary: {str(e)}")

    def _create_empty_results(self) -> Dict[str, Any]:
        """
        空の検出結果を作成
        
        Returns:
            Dict[str, Any]: 空の検出結果
        """
        return {
            'detections': {},
            'pose_landmarks': None,
            'hands_landmarks': None,
            'face_landmarks': None,
            'person_detected': False,
            'frame_info': {
                'width': 0,
                'height': 0,
                'channels': 0
            }
        } 