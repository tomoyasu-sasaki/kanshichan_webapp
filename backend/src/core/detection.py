# backend/src/core/detection.py

from typing import Any, Dict, List
import numpy as np

# Detectorクラスのインポート (依存関係を明確にするため)
# 実際のパスはプロジェクト構造に合わせて調整が必要な場合があります
from .detector import Detector
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DetectionManager:
    """
    物体検出の実行と結果の管理を担当するクラス。
    """
    def __init__(self, detector: Detector):
        """
        DetectionManagerを初期化します。

        Args:
            detector (Detector): 物体検出を実行するためのDetectorインスタンス。
        """
        if detector is None:
            logger.error("Detector instance is required for DetectionManager.")
            raise ValueError("Detector instance cannot be None.")
        self.detector = detector
        logger.info("DetectionManager initialized.")

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        与えられたフレームに対して物体検出を実行し、リスト形式で結果を返します。

        Args:
            frame (np.ndarray): 処理対象の画像フレーム。

        Returns:
            List[Dict[str, Any]]: 検出結果のリスト。
                                   例: [{'label': 'person', 'confidence': 0.95, 'box': [x1, y1, x2, y2]},
                                        {'label': 'smartphone', 'confidence': 0.8, 'box': [x1, y1, x2, y2]}, ...]
                                   検出がない場合は空のリスト。
        """
        if frame is None:
            logger.warning("Received None frame for detection.")
            return []

        unified_detections_list = []
        try:
            # Detectorを使用して辞書形式の検出結果を取得
            detector_results = self.detector.detect_objects(frame)

            # --- 結果をリスト形式に変換 ---
            # 1. 人物検出結果を追加 (MediaPipeまたはYOLOで検出された場合)
            if detector_results.get('person_detected'):
                # person の bbox は detector_results から直接は取れないため、
                # 必要であれば detect_objects 内で bbox を抽出して返すようにするか、
                # ここでは bbox なしの情報を追加する。今回は label のみ追加。
                 unified_detections_list.append({'label': 'person', 'confidence': None, 'box': None}) # box情報は不明

            # 2. その他の物体検出結果を追加 (YOLOの結果)
            if 'detections' in detector_results and isinstance(detector_results['detections'], dict):
                for label, detections in detector_results['detections'].items():
                    # label は 'smartphone' などのキー名
                    for det in detections:
                         # detector.py の detect_objects は bbox と confidence を返す
                         unified_detections_list.append({
                             'label': label, # 'smartphone' など
                             'confidence': det.get('confidence'),
                             'bbox': det.get('bbox') # FrameProcessorとの互換性のため'bbox'キーを使用
                         })
                         logger.info(f"[DEBUG] Added {label} detection with bbox: {det.get('bbox')}")

            # 3. ランドマーク情報をリストに追加（個別エントリとして）
            # FrameProcessorとの互換性のため、各ランドマークタイプを個別のエントリとして追加
            if detector_results.get('pose_landmarks'):
                unified_detections_list.append({
                    'label': 'landmarks',
                    'type': 'pose',
                    'landmarks': detector_results.get('pose_landmarks')
                })
                logger.info(f"[DEBUG] Added pose landmarks to detections list")
                
            if detector_results.get('hands_landmarks'):
                unified_detections_list.append({
                    'label': 'landmarks',
                    'type': 'hands', 
                    'landmarks': detector_results.get('hands_landmarks')
                })
                logger.info(f"[DEBUG] Added hands landmarks to detections list")
                
            if detector_results.get('face_landmarks'):
                unified_detections_list.append({
                    'label': 'landmarks',
                    'type': 'face',
                    'landmarks': detector_results.get('face_landmarks')
                })
                logger.info(f"[DEBUG] Added face landmarks to detections list")

            # logger.debug(f"Unified detections list: {unified_detections_list}")
            return unified_detections_list
            # --- 変換ここまで ---

        except Exception as e:
            logger.error(f"Error during object detection or formatting: {e}", exc_info=True)
            return [] # エラー発生時は空の結果を返す

    # 将来的に、検出結果に基づいた追加処理（例：特定のオブジェクトの追跡など）
    # を担うメソッドを追加することも考えられます。 