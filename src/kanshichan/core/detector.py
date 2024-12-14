import mediapipe as mp
import cv2
import torch
from ultralytics import YOLO
from src.kanshichan.utils.logger import setup_logger

logger = setup_logger(__name__)

class Detector:
    def __init__(self):
        self.setup_pose_detector()
        self.setup_phone_detector()

    def setup_pose_detector(self):
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
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        
        self.model = YOLO("yolov8n.pt")
        self.model.to(self.device)

    def detect_person(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        return bool(results.pose_landmarks)

    def detect_phone(self, frame):
        results = self.model.predict(
            frame,
            conf=0.3,
            iou=0.45,
            device=self.device,
            verbose=False,
            imgsz=(640, 640)
        )
        
        detections = results[0].boxes
        class_names = self.model.names
        
        for box in detections:
            cls_id = int(box.cls[0].item()) if hasattr(box.cls[0], 'item') else int(box.cls[0])
            class_name = class_names.get(cls_id, "").lower()
            
            if class_name in ["cell phone", "smartphone", "phone", "mobile phone", "remote"]:
                return True
        
        return False
