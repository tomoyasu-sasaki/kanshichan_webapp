import cv2
import torch
from ultralytics import YOLO
import mediapipe as mp
import os
import numpy as np
from typing import Dict, Any, Optional
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    ModelError, ModelInitializationError, ModelInferenceError,
    YOLOError, MediaPipeError, DetectionError, ConfigError,
    HardwareError, OptimizationError, SmoothingError, wrap_exception
)
from core.ai_optimizer import AIOptimizer
from core.detection_smoother import DetectionSmoother

logger = setup_logger(__name__)


class ObjectDetector:
    """
    物体検出専門クラス
    - YOLO初期化と推論
    - MediaPipe初期化と推論
    - 検出結果の統合処理
    - 検出結果の平滑化（点滅抑制）
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
            model_path = "yolov8n.pt"
            
            # モデルが存在しない場合はダウンロード
            if not os.path.exists(model_path):
                logger.warning("YOLOモデルをダウンロードします...")
                self.model = YOLO("yolov8n.pt")
            else:
                self.model = YOLO(model_path)
            
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
            yolo_error = wrap_exception(
                e, YOLOError,
                "YOLO object detector initialization failed",
                details={
                    'model_path': model_path,
                    'device': str(self.device) if hasattr(self, 'device') else 'unknown',
                    'torch_available': torch.cuda.is_available() if hasattr(torch, 'cuda') else False,
                    'mps_available': torch.backends.mps.is_built() if hasattr(torch.backends, 'mps') else False
                }
            )
            logger.error(f"YOLO initialization error: {yolo_error.to_dict()}")
            self.use_yolo = False
            logger.warning("YOLO object detector is disabled due to initialization error.")

    def detect_objects(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        フレーム内の物体を検出
        
        Args:
            frame: 入力フレーム（BGR形式）
            
        Returns:
            Dict[str, Any]: 検出結果の辞書
        """
        results = {
            'detections': {},
            'pose_landmarks': None,
            'hands_landmarks': None,
            'face_landmarks': None,
            'person_detected': False,
            'frame_info': {
                'width': frame.shape[1] if frame is not None else 0,
                'height': frame.shape[0] if frame is not None else 0,
                'channels': frame.shape[2] if frame is not None and len(frame.shape) > 2 else 0
            }
        }
        
        if frame is None or frame.size == 0:
            logger.warning("Empty frame received for detection")
            return results
            
        try:
            if self.use_yolo or self.use_mediapipe:
                logger.debug(f"Starting object detection on frame {results['frame_info']['width']}x{results['frame_info']['height']} - MediaPipe: {self.use_mediapipe}, YOLO: {self.use_yolo}")
            
            # BGR形式からRGB形式に変換（MediaPipe用）
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # MediaPipeでの検出
            if self.use_mediapipe:
                self._detect_with_mediapipe(rgb_frame, results)
            
            # YOLO物体検出（元のBGRフレームを使用）
            if self.use_yolo and hasattr(self, 'model'):
                self._detect_with_yolo_bgr(frame, results)
            
            # 検出システムが全て無効な場合、強制的に人を検出したことにする
            if not self.use_mediapipe and not self.use_yolo:
                results['person_detected'] = True
            
            # パフォーマンス統計の更新
            if self.ai_optimizer:
                self.ai_optimizer.update_performance_stats()
            
            # 検出結果の平滑化処理（点滅抑制）
            if self.detection_smoother:
                try:
                    results = self.detection_smoother.smooth_detections(results)
                    logger.debug("Detection smoothing applied successfully")
                except Exception as e:
                    smoothing_error = wrap_exception(
                        e, SmoothingError,
                        "Detection smoothing failed, using original results",
                        details={
                            'frame_info': results.get('frame_info', {}),
                            'detection_count': len(results.get('detections', {})),
                            'fallback_to_original': True
                        }
                    )
                    logger.warning(f"Smoothing error: {smoothing_error.to_dict()}")
                    # エラー時は元の結果をそのまま使用
            
            # 結果要約のログ
            logger.debug(f"Detection completed - Person: {results['person_detected']}, "
                        f"Pose: {results['pose_landmarks'] is not None}, "
                        f"Hands: {results['hands_landmarks'] is not None}, "
                        f"Face: {results['face_landmarks'] is not None}, "
                        f"Objects: {list(results['detections'].keys())}")
            
            return results
        
        except Exception as e:
            detection_error = wrap_exception(
                e, DetectionError,
                "Unexpected error during object detection processing",
                details={
                    'frame_shape': frame.shape if frame is not None else None,
                    'mediapipe_enabled': self.use_mediapipe,
                    'yolo_enabled': self.use_yolo,
                    'fallback_result': True
                }
            )
            logger.error(f"Detection processing error: {detection_error.to_dict()}")
            return results

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
        if self.config_manager:
            self.landmark_settings = self.config_manager.get_landmark_settings()
            self.detection_objects = self.config_manager.get_detection_objects()
            logger.info("Detection settings reloaded.")
        else:
            logger.warning("Cannot reload settings: ConfigManager not available.") 