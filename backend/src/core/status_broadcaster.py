import threading
import cv2
from typing import Any, Dict, Optional
import numpy as np
from utils.logger import setup_logger
from core.camera import Camera
from core.detector import Detector
from core.state import StateManager
from web.websocket import broadcast_status
from utils.config_manager import ConfigManager
from utils.exceptions import (
    NetworkError, RenderingError, StateError,
    HardwareError, AIProcessingError, wrap_exception
)

logger = setup_logger(__name__)


class StatusBroadcaster:
    """
    ステータス配信専門クラス
    - フレームバッファ管理
    - WebSocket通信
    - 描画済みフレーム提供
    """
    
    def __init__(self,
                 detector: Detector,
                 state_manager: StateManager,
                 camera: Camera,
                 config_manager: ConfigManager):
        """
        初期化
        
        Args:
            detector: 検出・描画処理インスタンス
            state_manager: 状態管理インスタンス
            camera: カメラインスタンス
            config_manager: 設定管理インスタンス
        """
        self.detector = detector
        self.state = state_manager
        self.camera = camera
        self.config_manager = config_manager
        
        # フレームバッファの初期化
        self.frame_buffer = None
        self.frame_lock = threading.Lock()
        
        logger.info("StatusBroadcaster initialized.")

    def update_frame_buffer(self, frame: np.ndarray) -> None:
        """
        フレームバッファを更新する
        
        Args:
            frame: 新しいフレーム
        """
        if frame is not None:
            with self.frame_lock:
                self.frame_buffer = frame.copy()

    def broadcast_status(self) -> None:
        """
        現在のステータスをWebSocketでブロードキャストする
        """
        try:
            status = self.state.get_status_summary()
            broadcast_status(status)
        except Exception as e:
            broadcast_error = wrap_exception(
                e, NetworkError,
                "Error broadcasting status via WebSocket",
                details={
                    'state_manager_available': self.state is not None,
                    'status_available': hasattr(self.state, 'get_status_summary')
                }
            )
            logger.error(f"Status broadcast error: {broadcast_error.to_dict()}")

    def get_current_frame(self, detection_results: Dict[str, Any]) -> Optional[bytes]:
        """
        WebUIで使用する描画済みのフレームを取得
        
        Args:
            detection_results: 検出結果の辞書
            
        Returns:
            Optional[bytes]: JPEG形式のフレームデータ、失敗時はNone
        """
        frame_to_encode = None
        with self.frame_lock:
            if self.frame_buffer is not None:
                # 現在のフレームバッファをコピー
                frame_copy = self.frame_buffer.copy()
                # 最新の検出/ステータス結果を取得
                results_copy = detection_results.copy()

                # detection_results['landmarks'] からランドマークデータを取得し、
                # detector.py が認識できるキー (pose_landmarks など) に戻す
                landmarks = results_copy.get('landmarks', {})
                logger.info(f"[DEBUG] Original landmarks data: {landmarks}")
                if isinstance(landmarks, dict):
                    if 'pose' in landmarks:
                        results_copy['pose_landmarks'] = landmarks.get('pose')
                        logger.info(f"[DEBUG] Converted pose landmarks: {landmarks.get('pose') is not None}")
                    if 'hands' in landmarks:
                        results_copy['hands_landmarks'] = landmarks.get('hands')
                        logger.info(f"[DEBUG] Converted hands landmarks: {landmarks.get('hands') is not None}")
                    if 'face' in landmarks:
                        results_copy['face_landmarks'] = landmarks.get('face')
                        logger.info(f"[DEBUG] Converted face landmarks: {landmarks.get('face') is not None}")
                logger.info(f"[DEBUG] Final results_copy keys: {list(results_copy.keys())}")

                # Detectorに描画を依頼 (修正済みの results_copy を使用)
                frame_to_encode = self.detector.draw_detections(frame_copy, results_copy)

        if frame_to_encode is not None:
            try:
                # JPEG形式にエンコード
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                _, buffer = cv2.imencode('.jpg', frame_to_encode, encode_param)
                return buffer.tobytes()
            except Exception as e:
                encoding_error = wrap_exception(
                    e, RenderingError,
                    "Error encoding frame to JPEG",
                    details={
                        'frame_shape': frame_to_encode.shape if frame_to_encode is not None else None,
                        'encoding_quality': 90
                    }
                )
                logger.error(f"Frame encoding error: {encoding_error.to_dict()}")
                return None
        else:
            # フレームがない場合は空のバイト列などを返すか、Noneを返す
            return None

    def display_frame(self, frame: np.ndarray, detection_results: Dict[str, Any]) -> None:
        """
        OpenCVウィンドウにフレームを表示する（設定が有効な場合）
        
        Args:
            frame: 表示するフレーム
            detection_results: 検出結果の辞書
        """
        if self.config_manager.get('display.show_opencv_window', True):
            display_frame = frame.copy()
            # 更新された detection_results を使って描画
            results_for_draw = detection_results.copy()
                 
            # detection_results['landmarks'] からランドマークデータを取得し、
            # detector.py が認識できるキー (pose_landmarks など) に戻す
            landmarks = results_for_draw.get('landmarks', {})
            logger.debug(f"Display frame landmarks data: {landmarks}")
            if isinstance(landmarks, dict):
                if 'pose' in landmarks:
                    results_for_draw['pose_landmarks'] = landmarks.get('pose')
                    logger.debug(f"Display pose landmarks converted: {landmarks.get('pose') is not None}")
                if 'hands' in landmarks:
                    results_for_draw['hands_landmarks'] = landmarks.get('hands')
                    logger.debug(f"Display hands landmarks converted: {landmarks.get('hands') is not None}")
                if 'face' in landmarks:
                    results_for_draw['face_landmarks'] = landmarks.get('face')
                    logger.debug(f"Display face landmarks converted: {landmarks.get('face') is not None}")
            logger.debug(f"Display frame results keys: {list(results_for_draw.keys())}")
                 
            # draw_detections にステータス情報が含まれたデータを渡す
            display_frame = self.detector.draw_detections(display_frame, results_for_draw)
            # 再度有効化
            self.camera.show_frame(display_frame)
            
            # q キーでの終了処理も復活
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("'q' key pressed, stopping monitor.")
                # スレッドを安全に停止させるためのフラグなどを設定する
                # (現状は直接ループを抜ける仕組みがないため、ログ表示のみ)

    def get_frame_buffer_status(self) -> Dict[str, Any]:
        """
        フレームバッファの状態情報を取得
        
        Returns:
            Dict[str, Any]: フレームバッファの状態情報
        """
        with self.frame_lock:
            return {
                'has_frame': self.frame_buffer is not None,
                'frame_shape': self.frame_buffer.shape if self.frame_buffer is not None else None,
                'buffer_size': self.frame_buffer.nbytes if self.frame_buffer is not None else 0
            } 