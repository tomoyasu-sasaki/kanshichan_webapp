"""
フレーム処理モジュール

カメラからのフレーム取得、検出実行、検出結果の形式変換と
StateManager への状態伝播を行います。
"""

import time
import threading
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from utils.logger import setup_logger
# 循環インポートを避けるため遅延インポート
# from core.monitoring import Camera
# 循環インポートを避けるため遅延インポート
# from core.detection import DetectionManager
from core.management import StateManager
from utils.exceptions import (
    CameraError, DetectionError, StateError,
    HardwareError, AIProcessingError, wrap_exception
)

logger = setup_logger(__name__)


class FrameProcessor:
    """
    フレーム処理専門クラス
    - フレーム取得と検出処理
    - 検出結果の更新と形式変換
    - StateManagerとの連携
    """
    
    def __init__(self,
                 camera,  # Camera型注釈を削除
                 detection_manager,  # DetectionManager型注釈を削除
                 state_manager: StateManager):
        """
        初期化
        
        Args:
            camera: カメラインスタンス
            detection_manager: 検出管理インスタンス
            state_manager: 状態管理インスタンス
        """
        self.camera = camera
        self.detection_manager = detection_manager
        self.state_manager = state_manager
        
        # 検出結果の管理
        self.detection_results = {
            'person_detected': False,
            'smartphone_detected': False,
            'person_bbox': None,
            'phone_bbox': None,
            'landmarks': None,
            'detections': {},
            'absenceTime': 0,
            'smartphoneUseTime': 0,
            'absenceAlert': False,
            'smartphoneAlert': False
        }
        self.detection_lock = threading.Lock()
        
        logger.info("FrameProcessor initialized.")

    def process_frame(self) -> Optional[Tuple[Any, List[Dict[str, Any]]]]:
        """
        フレームを取得し、検出を実行、StateManagerを更新する
        
        Returns:
            Optional[Tuple[frame, detections_list]]: 処理結果のタプル、失敗時はNone
        """
        ret, frame = self.camera.get_frame()
        if not ret or frame is None:
            return None

        # 検出処理の実行 (DetectionManagerを使用)
        detections_list = self.detection_manager.detect(frame)

        # StateManager への情報連携（内部で安定化処理を行う）
        self.state_manager.update_detection_state(detections_list)
        
        return frame, detections_list

    def update_detection_results(self, detections_list: List[Dict[str, Any]]) -> None:
        """
        Monitor内部の検出結果を更新する
        
        Args:
            detections_list: 検出結果のリスト
        """
        # StateManager から最新の状態を取得 (描画用)
        person_now_detected = self.state_manager.person_detected
        smartphone_now_in_use_for_drawing = self.state_manager.smartphone_in_use
        # StateManagerからステータスサマリーを取得
        status_summary = self.state_manager.get_status_summary()

        # detections_list を draw_detections が期待する形式 (クラス名ごとの辞書) に変換
        detections_dict_for_draw = {}
        for det in detections_list:
            label = det.get('label')
            if label == 'landmarks': 
                continue
            if label:
                if label not in detections_dict_for_draw:
                    detections_dict_for_draw[label] = []
                detections_dict_for_draw[label].append(det)

        # ランドマーク情報の処理
        landmarks_dict = {}
        for det in detections_list:
            if det.get('label') == 'landmarks':
                landmark_type = det.get('type')  # 'pose', 'hands', 'face'
                landmark_data = det.get('landmarks')
                if landmark_type and landmark_data is not None:
                    landmarks_dict[landmark_type] = landmark_data
                    logger.debug(f"Processed landmark: type={landmark_type}, data_available={landmark_data is not None}")
        
        logger.debug(f"Final landmarks_dict: {list(landmarks_dict.keys())}")

        # 検出結果の更新
        with self.detection_lock:
            self.detection_results = {
                'person_detected': person_now_detected,
                'smartphone_detected': smartphone_now_in_use_for_drawing,
                'person_bbox': self._extract_person_bbox(detections_list),
                'phone_bbox': self._extract_smartphone_bbox(detections_list),
                'landmarks': landmarks_dict,
                'detections': detections_dict_for_draw,
                'absenceTime': status_summary.get('absenceTime', 0),
                'smartphoneUseTime': status_summary.get('smartphoneUseTime', 0),
                'absenceAlert': status_summary.get('absenceAlert', False),
                'smartphoneAlert': status_summary.get('smartphoneAlert', False)
            }

    def get_detection_results(self) -> Dict[str, Any]:
        """
        現在の検出結果を取得
        
        Returns:
            Dict[str, Any]: 検出結果の辞書
        """
        with self.detection_lock:
            return self.detection_results.copy()

    def update_stored_detection_results(self, results: Dict[str, Any]) -> None:
        """
        外部から検出結果を更新
        
        Args:
            results: 新しい検出結果
        """
        with self.detection_lock:
            self.detection_results = results

    def _extract_person_bbox(self, detections_list: List[Dict[str, Any]]) -> Optional[Dict]:
        """
        検出結果から人物のバウンディングボックスを抽出
        
        Args:
            detections_list: 検出結果のリスト
            
        Returns:
            Optional[Dict]: 人物のバウンディングボックス情報
        """
        for det in detections_list:
            if det.get('label') == 'person':
                return {
                    'bbox': det.get('bbox'),
                    'confidence': det.get('confidence')
                }
        return None

    def _extract_smartphone_bbox(self, detections_list: List[Dict[str, Any]]) -> Optional[Dict]:
        """
        検出結果からスマートフォンのバウンディングボックスを抽出
        
        Args:
            detections_list: 検出結果のリスト
            
        Returns:
            Optional[Dict]: スマートフォンのバウンディングボックス情報
        """
        for det in detections_list:
            if det.get('label') == 'smartphone':
                return {
                    'bbox': det.get('bbox'),
                    'confidence': det.get('confidence')
                }
        return None 