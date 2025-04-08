import cv2
import torch
from ultralytics import YOLO
import mediapipe as mp
import os
import numpy as np
from utils.logger import setup_logger
from utils.config_manager import ConfigManager

logger = setup_logger(__name__)

class Detector:
    def __init__(self, config_manager=None):
        try:
            self.config_manager = config_manager
            # 設定からランドマークと検出オブジェクトの設定を取得
            self.landmark_settings = {}
            self.detection_objects = {}
            if config_manager:
                self.landmark_settings = config_manager.get_landmark_settings()
                self.detection_objects = config_manager.get_detection_objects()
            
            # MediaPipe使用フラグ - 設定やエラー状況に応じて決定
            self.use_mediapipe = False # デフォルトは無効化
            if config_manager:
                # 設定ファイルから明示的に指定された場合のみ有効化
                self.use_mediapipe = config_manager.get('detector.use_mediapipe', False)
                logger.info(f"MediaPipe status from config: {'enabled' if self.use_mediapipe else 'disabled'}")
            
            # MediaPipeコンポーネント初期化 (有効な場合)
            if self.use_mediapipe:
                try:
                    # MediaPipe内部の警告を抑制
                    os.environ["MEDIAPIPE_DISABLE_GPU"] = "1"  # GPUを無効化して安定性向上
                    
                    self.mp_pose = mp.solutions.pose
                    self.mp_hands = mp.solutions.hands
                    self.mp_face_mesh = mp.solutions.face_mesh
                    self.mp_drawing = mp.solutions.drawing_utils
                    self.mp_drawing_styles = mp.solutions.drawing_styles
                    
                    # Poseモデル初期化
                    self.pose = self.mp_pose.Pose(
                        static_image_mode=False,
                        model_complexity=0, # 軽量モデルを使用
                        smooth_landmarks=True,
                        min_detection_confidence=0.7, # 信頼度閾値を上げる
                        min_tracking_confidence=0.7, # 信頼度閾値を上げる
                        enable_segmentation=False
                    )
                    logger.info("MediaPipe Pose model initialized successfully")
                    
                    # Handsモデル初期化 (設定が有効な場合)
                    if self.landmark_settings.get('hands', {}).get('enabled', False):
                        self.hands = self.mp_hands.Hands(
                            static_image_mode=False,
                            max_num_hands=2,
                            min_detection_confidence=0.5,
                            min_tracking_confidence=0.5
                        )
                        logger.info("MediaPipe Hands model initialized successfully")
                    
                    # Face Meshモデル初期化 (設定が有効な場合)
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
                    logger.error(f"Failed to initialize MediaPipe components: {e}", exc_info=True)
                    self.use_mediapipe = False # 初期化失敗時は無効化
            else:
                logger.info("MediaPipe usage is disabled in config or due to previous error.")

            # YOLOを使うかどうかの設定
            self.use_yolo = True
            if config_manager:
                self.use_yolo = config_manager.get('detector.use_yolo', True)
            
            # YOLO物体検出器のセットアップ（有効な場合のみ）
            if self.use_yolo:
                self.setup_object_detector()
            else:
                logger.info("YOLO object detector is disabled.")
                
        except Exception as e:
            logger.error(f"Error initializing Detector: {e}", exc_info=True)
            # 初期化中に予期せぬエラーがあれば両方無効にする可能性も
            self.use_mediapipe = False
            self.use_yolo = False
            logger.critical("Disabling both MediaPipe and YOLO due to critical error during Detector initialization.")

    def setup_object_detector(self):
        """物体検出器の初期化"""
        try:
            # モデルファイルのパスを設定
            model_path = "yolov8n.pt"
            
            # モデルが存在しない場合はダウンロード
            if not os.path.exists(model_path):
                logger.warning("YOLOモデルをダウンロードします...")
                self.model = YOLO("yolov8n.pt")
            else:
                self.model = YOLO(model_path)
            
            self.model.verbose = False
            
            # デバイスの設定
            if torch.backends.mps.is_built():
                self.device = torch.device("mps")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
            
            logger.info(f"Using device: {self.device}")
            self.model.to(self.device)
            
        except Exception as e:
            logger.error(f"Error initializing object detector: {e}", exc_info=True)
            self.use_yolo = False
            logger.warning("YOLO object detector is disabled due to initialization error.")

    def detect_objects(self, frame):
        """フレーム内の物体を検出"""
        results = {
            'detections': {},
            'pose_landmarks': None,
            'hands_landmarks': None,
            'face_landmarks': None,
            'person_detected': False
        }
        
        if frame is None or frame.size == 0:
            logger.warning("Empty frame received for detection")
            return results
            
        try:
            # RGB形式に変換
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # MediaPipeでの検出（有効な場合のみ）
            if self.use_mediapipe:
                # Pose検出
                if hasattr(self, 'pose'):
                    try:
                        pose_results = self.pose.process(rgb_frame)
                        if pose_results and pose_results.pose_landmarks:
                            results['person_detected'] = True
                            if self.landmark_settings.get('pose', {}).get('enabled', False):
                                results['pose_landmarks'] = pose_results.pose_landmarks
                    except Exception as e:
                        logger.error(f"Error during MediaPipe pose detection: {e}", exc_info=True)
                
                # Hands検出
                if hasattr(self, 'hands') and self.landmark_settings.get('hands', {}).get('enabled', False):
                    try:
                        hands_results = self.hands.process(rgb_frame)
                        if hands_results and hands_results.multi_hand_landmarks:
                            results['hands_landmarks'] = hands_results.multi_hand_landmarks
                    except Exception as e:
                        logger.error(f"Error during MediaPipe hands detection: {e}", exc_info=True)
                
                # Face検出
                if hasattr(self, 'face_mesh') and self.landmark_settings.get('face', {}).get('enabled', False):
                    try:
                        face_results = self.face_mesh.process(rgb_frame)
                        if face_results and face_results.multi_face_landmarks:
                            results['face_landmarks'] = face_results.multi_face_landmarks
                    except Exception as e:
                        logger.error(f"Error during MediaPipe face detection: {e}", exc_info=True)
            
            # 物体検出（YOLO）- 有効な場合のみ
            if self.use_yolo and hasattr(self, 'model'):
                try:
                    yolo_results = self.model(rgb_frame, verbose=False)[0]
                    
                    # YOLOでの人物検出
                    # (MediaPipeが無効でもYOLOで人物を検出できるようにする)
                    if not results['person_detected']: # MediaPipeで未検出の場合のみチェック
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
                                logger.debug(f"物体を検出: {obj_settings.get('name')} (confidence: {conf})")
                                detections.append({
                                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                    'confidence': conf
                                })
                        if detections:
                            results['detections'][obj_key] = detections
                except Exception as e:
                    logger.error(f"Error during YOLO object detection: {e}", exc_info=True)
                    # エラーが発生したらYOLOを無効化
                    self.use_yolo = False
                    logger.warning("Disabling YOLO due to runtime error.")
            
            # 検出システムが全て無効な場合、強制的に人を検出したことにする
            if not self.use_mediapipe and not self.use_yolo:
                # logger.warning("All detection systems are disabled. Forcing person_detected=True for functionality.") # ログは既に出ているはず
                results['person_detected'] = True
            
            return results
        
        except Exception as e:
            logger.error(f"Unexpected error during object detection processing: {e}", exc_info=True)
            return results # エラーでも空の結果を返す

    def draw_detections(self, frame, results):
        """検出結果とステータスを描画"""
        if frame is None or frame.size == 0:
            logger.warning("Empty frame received for drawing")
            return frame
            
        try:
            # Poseランドマークの描画
            if self.use_mediapipe and hasattr(self, 'mp_drawing') and results.get('pose_landmarks') and self.landmark_settings.get('pose', {}).get('enabled', False):
                try:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        results['pose_landmarks'],
                        self.mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                    )
                except Exception as e:
                    logger.error(f"Error drawing pose landmarks: {e}", exc_info=True)
            
            # Handsランドマークの描画
            if self.use_mediapipe and hasattr(self, 'mp_drawing') and results.get('hands_landmarks') and self.landmark_settings.get('hands', {}).get('enabled', False):
                try:
                    for hand_landmarks in results['hands_landmarks']:
                        self.mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style()
                        )
                except Exception as e:
                    logger.error(f"Error drawing hand landmarks: {e}", exc_info=True)
            
            # Faceランドマークの描画
            if self.use_mediapipe and hasattr(self, 'mp_drawing') and results.get('face_landmarks') and self.landmark_settings.get('face', {}).get('enabled', False):
                try:
                    for face_landmarks in results['face_landmarks']:
                        self.mp_drawing.draw_landmarks(
                            frame,
                            face_landmarks,
                            self.mp_face_mesh.FACEMESH_TESSELATION,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                        )
                        # 輪郭（任意）
                        self.mp_drawing.draw_landmarks(
                            frame,
                            face_landmarks,
                            self.mp_face_mesh.FACEMESH_CONTOURS,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                        )
                except Exception as e:
                    logger.error(f"Error drawing face landmarks: {e}", exc_info=True)
            
            # 人物検出状態の表示 ("Person" テキスト)
            # (YOLOでも検出されるので MediaPipe 有効無効に関わらず表示)
            if results.get('person_detected'):
                cv2.putText(frame, "Person", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # 物体検出の描画 (bbox とラベル) - YOLOが有効な場合のみ
            if self.use_yolo and hasattr(self, 'model'):
                for obj_key, detections in results.get('detections', {}).items():
                    if obj_key == 'person': continue # 人物はテキスト表示のみ
                    logger.debug(f"描画処理: key={obj_key}")
                    obj_settings = self.detection_objects.get(obj_key)
                    if not obj_settings: continue
                    for det in detections:
                        bbox = det.get('bbox')
                        if bbox is None: continue
                        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4: continue
                        try: 
                            x1, y1, x2, y2 = map(int, bbox)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), obj_settings.get('color', (0, 0, 0)), obj_settings.get('thickness', 2))
                            label = f"{obj_settings.get('name')} ({det.get('confidence', 0.0):.2f})"
                            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, obj_settings.get('color', (0, 0, 0)), 2)
                        except (ValueError, TypeError) as e: 
                            logger.warning(f"Invalid bbox format for drawing: {bbox}, error: {e}")
                            continue

            # --- ステータス情報の描画処理 ---
            status_texts = []
            absence_time = results.get('absenceTime', 0)
            smartphone_time = results.get('smartphoneUseTime', 0)
            absence_alert = results.get('absenceAlert', False)
            smartphone_alert = results.get('smartphoneAlert', False)
            if absence_time > 0:
                text = f"Absence: {int(absence_time)}s"
                color = (0, 0, 255) if absence_alert else (0, 255, 255)
                status_texts.append({'text': text, 'color': color})
            if smartphone_time > 0:
                text = f"Smartphone: {int(smartphone_time)}s"
                color = (0, 0, 255) if smartphone_alert else (0, 255, 255)
                status_texts.append({'text': text, 'color': color})
            if not self.use_mediapipe and not self.use_yolo:
                status_texts.append({'text': "Detection systems disabled", 'color': (0, 0, 255)})
            y_offset = 60
            for status in status_texts:
                cv2.putText(frame, status['text'], (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status['color'], 2)
                y_offset += 30
            # --- ステータス描画ここまで ---

            return frame
        except Exception as e:
            logger.error(f"Error during detection drawing: {e}", exc_info=True)
            return frame
