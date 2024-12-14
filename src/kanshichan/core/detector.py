import mediapipe as mp
import cv2
import torch
from ultralytics import YOLO
from src.kanshichan.utils.logger import setup_logger

logger = setup_logger(__name__)

class Detector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.setup_phone_detector()
        
    def setup_pose_detector(self):
        """姿勢検出器の初期化"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
    def setup_phone_detector(self):
        """スマートフォン検出器の初期化"""
        try:
            # YOLOモデルの初期化（verbose=Falseで出力を抑制）
            self.model = YOLO("yolov8n.pt")
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
            logger.error(f"Error initializing phone detector: {e}")
            raise

    def detect_person(self, frame):
        """人物を検出する"""
        # BGRからRGBに変換
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        # 検出結果の判定
        detected = results.pose_landmarks is not None
        
        return {
            'detected': bool(detected),  # 明示的にbool型に変換
            'landmarks': results.pose_landmarks if detected else None
        }

    def detect_phone(self, frame):
        """スマートフォンを検出する"""
        try:
            # YOLOv8で検出を実行
            results = self.model(frame, verbose=False)
            
            # 'cell phone' (クラス67) の検出結果をフィルタリング
            phone_detections = []
            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    # クラス67（cell phone）かつ信頼度が0.5以上の場合
                    if cls == 67 and conf >= 0.4:
                        phone_detections.append({
                            'bbox': box.xyxy[0].cpu().numpy(),  # バウンディングボックス
                            'confidence': conf
                        })
            
            return {
                'detected': len(phone_detections) > 0,
                'detections': phone_detections if phone_detections else None
            }
            
        except Exception as e:
            logger.error(f"スマートフォン検出中にエラーが発生: {e}")
            return {
                'detected': False,
                'detections': None
            }

    def draw_landmarks(self, frame, detections):
        """検出結果を描画する"""
        try:
            if detections is None:
                return
            
            # 人物のランドマークを描画
            if 'landmarks' in detections and detections['landmarks'] is not None:
                self.mp_drawing.draw_landmarks(
                    frame,
                    detections['landmarks'],
                    self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                )
            
            # スマートフォンの検出結果を描画
            if 'detections' in detections and detections['detections'] is not None:
                for detection in detections['detections']:
                    bbox = detection['bbox']
                    conf = detection['confidence']
                    
                    # バウンディングボックスを描画
                    cv2.rectangle(
                        frame,
                        (int(bbox[0]), int(bbox[1])),
                        (int(bbox[2]), int(bbox[3])),
                        (0, 0, 255),  # 赤色
                        2
                    )
                    
                    # 信頼度を表示
                    cv2.putText(
                        frame,
                        f'Phone: {conf:.2f}',
                        (int(bbox[0]), int(bbox[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        2
                    )
                
        except Exception as e:
            logger.error(f"描画処理中にエラーが発生: {e}")
