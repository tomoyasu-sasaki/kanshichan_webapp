from typing import Dict, Any, Optional
import cv2
import torch
from ultralytics import YOLO
import mediapipe as mp
import os
import numpy as np
from utils.logger import setup_logger
from utils.config_manager import ConfigManager

# 新しく分割されたクラスをインポート
from core.object_detector import ObjectDetector
from core.detection_renderer import DetectionRenderer

logger = setup_logger(__name__)

class Detector:
    """
    検出・描画統合クラス（リファクタリング済み）
    - ObjectDetectorとDetectionRendererの統合管理
    - 既存APIの互換性維持
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        try:
            self.config_manager = config_manager
            
            # ObjectDetectorの初期化
            self.object_detector = ObjectDetector(config_manager)
            
            # 検出システムの状態を取得
            detection_status = self.object_detector.get_detection_status()
            use_mediapipe = detection_status['use_mediapipe']
            use_yolo = detection_status['use_yolo']
            
            # DetectionRendererの初期化
            self.detection_renderer = DetectionRenderer(
                config_manager=config_manager,
                use_mediapipe=use_mediapipe,
                use_yolo=use_yolo
            )
            
            # 互換性のための属性設定
            self.use_mediapipe = use_mediapipe
            self.use_yolo = use_yolo
            
            logger.info("Detector initialized with refactored architecture.")
            
        except Exception as e:
            logger.error(f"Error initializing Detector: {e}", exc_info=True)

    def setup_object_detector(self):
        """物体検出器の初期化（互換性のため）"""
        # 新しいアーキテクチャでは初期化時に実行済み
        logger.info("Object detector setup completed (already initialized in new architecture)")

    def detect_objects(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        フレーム内の物体を検出（互換性のため）
        
        Args:
            frame: 入力フレーム
            
        Returns:
            Dict[str, Any]: 検出結果
        """
        return self.object_detector.detect_objects(frame)

    def draw_detections(self, frame: np.ndarray, results: Dict[str, Any]) -> np.ndarray:
        """
        検出結果とステータスを描画（互換性のため）
        
        Args:
            frame: 入力フレーム
            results: 検出結果
            
        Returns:
            np.ndarray: 描画済みフレーム
        """
        return self.detection_renderer.draw_detections(frame, results)

    def get_detection_status(self) -> Dict[str, Any]:
        """
        検出システムの統合状態情報を取得
        
        Returns:
            Dict[str, Any]: 統合状態情報
        """
        detector_status = self.object_detector.get_detection_status()
        renderer_status = self.detection_renderer.get_renderer_status()
        
        return {
            'detector': detector_status,
            'renderer': renderer_status,
            'use_mediapipe': self.use_mediapipe,
            'use_yolo': self.use_yolo
        }

    def reload_settings(self) -> None:
        """
        設定を再読み込みして検出・描画システムを更新
        """
        # ObjectDetectorの設定更新
        self.object_detector.reload_settings()
        
        # 検出システムの状態を再取得
        detection_status = self.object_detector.get_detection_status()
        use_mediapipe = detection_status['use_mediapipe']
        use_yolo = detection_status['use_yolo']
        
        # DetectionRendererの設定更新
        self.detection_renderer.update_settings(
            use_mediapipe=use_mediapipe,
            use_yolo=use_yolo
        )
        
        # 互換性のための属性更新
        self.use_mediapipe = use_mediapipe
        self.use_yolo = use_yolo
        
        logger.info("Detector settings reloaded successfully.")

    def update_detection_flags(self, use_mediapipe: bool = None, use_yolo: bool = None) -> None:
        """
        検出フラグを動的に更新
        
        Args:
            use_mediapipe: MediaPipe使用フラグ
            use_yolo: YOLO使用フラグ
        """
        if use_mediapipe is not None:
            self.use_mediapipe = use_mediapipe
            
        if use_yolo is not None:
            self.use_yolo = use_yolo
            
        # DetectionRendererの設定更新
        self.detection_renderer.update_settings(
            use_mediapipe=self.use_mediapipe,
            use_yolo=self.use_yolo
        )
        
        logger.info(f"Detection flags updated (MediaPipe: {self.use_mediapipe}, YOLO: {self.use_yolo})")

    def get_landmark_settings(self) -> Dict[str, Any]:
        """
        ランドマーク設定を取得（互換性のため）
        
        Returns:
            Dict[str, Any]: ランドマーク設定
        """
        return self.object_detector.landmark_settings

    def get_detection_objects(self) -> Dict[str, Any]:
        """
        検出オブジェクト設定を取得（互換性のため）
        
        Returns:
            Dict[str, Any]: 検出オブジェクト設定
        """
        return self.object_detector.detection_objects
