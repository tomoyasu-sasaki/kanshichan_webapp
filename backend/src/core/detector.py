import mediapipe as mp
import cv2
import torch
from ultralytics import YOLO
import os
from backend.src.utils.logger import setup_logger
from backend.src.config.display_settings import landmark_settings, detection_objects

logger = setup_logger(__name__)

class Detector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # MediaPipeモデルの初期化
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        if landmark_settings['hands']['enabled']:
            self.hands = self.mp_hands.Hands(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        
        self.setup_object_detector()
        
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
            logger.error(f"Error initializing object detector: {e}")
            raise

    def detect_objects(self, frame):
        """フレーム内の物体を検出"""
        results = {
            'detections': {},
            'landmarks': None,
            'person_detected': False
        }
        
        # RGB形式に変換
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 人物検出（MediaPipe）
        pose_results = self.pose.process(rgb_frame)
        if pose_results.pose_landmarks:
            results['person_detected'] = True
            if landmark_settings['pose']['enabled']:
                results['landmarks'] = pose_results.pose_landmarks
        
        # 物体検出（YOLO）
        try:
            yolo_results = self.model(rgb_frame, verbose=False)[0]
            
            # YOLOでの人物検出も確認
            for det in yolo_results.boxes.data.tolist():
                x1, y1, x2, y2, conf, cls = det
                class_name = yolo_results.names[int(cls)]
                logger.info(f"検出されたクラス: {class_name}, 信頼度: {conf}")
                
                if class_name == 'person' and conf > 0.5:
                    results['person_detected'] = True
                    break
            
            # その他の物体検出
            for obj_key, obj_settings in detection_objects.items():
                if not obj_settings['enabled']:
                    continue
                    
                logger.info(f"検出設定: key={obj_key}, name={obj_settings['name']}, class_name={obj_settings['class_name']}")
                
                detections = []
                for det in yolo_results.boxes.data.tolist():
                    x1, y1, x2, y2, conf, cls = det
                    detected_class = yolo_results.names[int(cls)]
                    if (detected_class == obj_settings['class_name'] and 
                        conf > obj_settings['confidence_threshold']):
                        logger.info(f"物体を検出: {obj_settings['name']} (confidence: {conf})")
                        detections.append({
                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                            'confidence': conf
                        })
                
                if detections:
                    results['detections'][obj_key] = detections
        
        except Exception as e:
            logger.error(f"Error during object detection: {e}")
        
        logger.info(f"検出結果: {results}")
        return results

    def draw_detections(self, frame, results):
        """検出結果を描画"""
        # ランドマークの描画（表示が有効な場合のみ）
        if results.get('landmarks') and landmark_settings['pose']['enabled']:
            self.mp_drawing.draw_landmarks(
                frame,
                results['landmarks'],
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
            )
        
        # 人物検出状態の表示
        if results.get('person_detected'):
            cv2.putText(
                frame,
                "Person",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
        
        # 物体検出の描画
        for obj_key, detections in results.get('detections', {}).items():
            logger.info(f"描画処理: key={obj_key}")
            obj_settings = detection_objects.get(obj_key)
            if not obj_settings:
                logger.warning(f"設定が見つかりません: {obj_key}")
                continue
            
            logger.info(f"描画設定: class_name={obj_settings['class_name']}, color={obj_settings['color']}")
            
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                # バウンディングボックスの描画
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    obj_settings['color'],
                    obj_settings['thickness']
                )
                # ラベルの描画（class_nameを使用）
                label = f"{obj_settings['class_name']} ({det['confidence']:.2f})"
                logger.info(f"ラベル描画: {label}")
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    obj_settings['color'],
                    2
                )
        
        return frame
