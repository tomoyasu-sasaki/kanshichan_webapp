import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, Any, Optional
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    RenderingError, MediaPipeError, DetectionError,
    ValidationError, wrap_exception
)

logger = setup_logger(__name__)


class DetectionRenderer:
    """
    描画専門クラス
    - ランドマーク描画（MediaPipe）
    - バウンディングボックス描画（YOLO）
    - ステータス情報描画
    """
    
    def __init__(self, 
                 config_manager: Optional[ConfigManager] = None,
                 use_mediapipe: bool = False,
                 use_yolo: bool = True):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
            use_mediapipe: MediaPipe使用フラグ
            use_yolo: YOLO使用フラグ
        """
        self.config_manager = config_manager
        self.use_mediapipe = use_mediapipe
        self.use_yolo = use_yolo
        
        # 設定から描画設定を取得
        self.landmark_settings = {}
        self.detection_objects = {}
        if config_manager:
            self.landmark_settings = config_manager.get_landmark_settings()
            self.detection_objects = config_manager.get_detection_objects()
        
        # MediaPipe描画ユーティリティの初期化
        if self.use_mediapipe:
            self._setup_mediapipe_drawing()
        
        logger.info(f"DetectionRenderer initialized (MediaPipe: {use_mediapipe}, YOLO: {use_yolo})")

    def _setup_mediapipe_drawing(self) -> None:
        """MediaPipe描画コンポーネントの初期化"""
        try:
            self.mp_pose = mp.solutions.pose
            self.mp_hands = mp.solutions.hands
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            logger.info("MediaPipe drawing components initialized")
        except Exception as e:
            mediapipe_draw_error = wrap_exception(
                e, MediaPipeError,
                "MediaPipe drawing components initialization failed",
                details={'drawing_disabled': True}
            )
            logger.error(f"MediaPipe drawing init error: {mediapipe_draw_error.to_dict()}")
            self.use_mediapipe = False

    def draw_detections(self, frame: np.ndarray, results: Dict[str, Any]) -> np.ndarray:
        """
        検出結果とステータスを描画
        
        Args:
            frame: 入力フレーム
            results: 検出結果の辞書
            
        Returns:
            np.ndarray: 描画済みフレーム
        """
        if frame is None or frame.size == 0:
            logger.warning("Empty frame received for drawing")
            return frame
            
        try:
            frame_height, frame_width = frame.shape[:2]
            logger.debug(f"[DEBUG] Drawing results on frame: {frame_width}x{frame_height}")
            logger.debug(f"[DEBUG] Drawing results with keys: {list(results.keys())}")
            logger.debug(f"[DEBUG] MediaPipe enabled: {self.use_mediapipe}, YOLO enabled: {self.use_yolo}")
            logger.debug(f"[DEBUG] Landmarks available: pose={results.get('pose_landmarks') is not None}, "
                        f"hands={results.get('hands_landmarks') is not None}, "
                        f"face={results.get('face_landmarks') is not None}")
            logger.debug(f"[DEBUG] Detections available: {list(results.get('detections', {}).keys())}")
            
            # ランドマーク描画（MediaPipe）
            if self.use_mediapipe:
                self._draw_landmarks(frame, results)
            
            # 人物検出状態の表示
            self._draw_person_status(frame, results)
            
            # 物体検出描画（YOLO）
            if self.use_yolo:
                self._draw_object_detections(frame, results)
            
            # ステータス情報描画
            self._draw_status_info(frame, results)
            
            return frame
            
        except Exception as e:
            render_error = wrap_exception(
                e, RenderingError,
                "Error during detection drawing process",
                details={
                    'frame_shape': frame.shape if frame is not None else None,
                    'mediapipe_enabled': self.use_mediapipe,
                    'yolo_enabled': self.use_yolo,
                    'fallback_frame': True
                }
            )
            logger.error(f"Detection drawing error: {render_error.to_dict()}")
            return frame

    def _draw_landmarks(self, frame: np.ndarray, results: Dict[str, Any]) -> None:
        """
        ランドマーク描画処理
        
        Args:
            frame: 描画対象フレーム
            results: 検出結果
        """
        if not hasattr(self, 'mp_drawing'):
            return
            
        frame_height, frame_width = frame.shape[:2]
        logger.debug(f"[DEBUG] Drawing landmarks on frame: {frame_width}x{frame_height}")
            
        # Poseランドマークの描画
        if (results.get('pose_landmarks') and 
            self.landmark_settings.get('pose', {}).get('enabled', False)):
            try:
                self.mp_drawing.draw_landmarks(
                    frame,
                    results['pose_landmarks'],
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                )
                logger.debug(f"[DEBUG] Pose landmarks drawn successfully")
            except Exception as e:
                pose_draw_error = wrap_exception(
                    e, RenderingError,
                    "Error drawing pose landmarks",
                    details={'landmark_type': 'pose'}
                )
                logger.error(f"Pose landmark drawing error: {pose_draw_error.to_dict()}")
        
        # Handsランドマークの描画
        if (results.get('hands_landmarks') and 
            self.landmark_settings.get('hands', {}).get('enabled', False)):
            try:
                for hand_landmarks in results['hands_landmarks']:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
                logger.debug(f"[DEBUG] Hands landmarks drawn successfully")
            except Exception as e:
                hands_draw_error = wrap_exception(
                    e, RenderingError,
                    "Error drawing hand landmarks",
                    details={'landmark_type': 'hands'}
                )
                logger.error(f"Hands landmark drawing error: {hands_draw_error.to_dict()}")
        
        # Faceランドマークの描画
        if (results.get('face_landmarks') and 
            self.landmark_settings.get('face', {}).get('enabled', False)):
            try:
                for face_landmarks in results['face_landmarks']:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        face_landmarks,
                        self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                    )
                    # 輪郭
                    self.mp_drawing.draw_landmarks(
                        frame,
                        face_landmarks,
                        self.mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                    )
                logger.debug(f"[DEBUG] Face landmarks drawn successfully")
            except Exception as e:
                face_draw_error = wrap_exception(
                    e, RenderingError,
                    "Error drawing face landmarks",
                    details={'landmark_type': 'face'}
                )
                logger.error(f"Face landmark drawing error: {face_draw_error.to_dict()}")

    def _draw_person_status(self, frame: np.ndarray, results: Dict[str, Any]) -> None:
        """
        人物検出状態の描画
        
        Args:
            frame: 描画対象フレーム
            results: 検出結果
        """
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

    def _draw_object_detections(self, frame: np.ndarray, results: Dict[str, Any]) -> None:
        """
        物体検出結果の描画（バウンディングボックス）
        平滑化・補間結果の視覚的表示機能付き
        
        Args:
            frame: 描画対象フレーム
            results: 検出結果
        """
        frame_height, frame_width = frame.shape[:2]
        logger.debug(f"[DEBUG] Drawing object detections on frame: {frame_width}x{frame_height}")
        
        for obj_key, detections in results.get('detections', {}).items():
            if obj_key == 'person':
                continue  # 人物はテキスト表示のみ
                
            logger.debug(f"[DEBUG] 描画処理: key={obj_key}, detections_count={len(detections)}")
            obj_settings = self.detection_objects.get(obj_key)
            if not obj_settings:
                logger.debug(f"[DEBUG] No settings found for object key: {obj_key}")
                continue
                
            for i, det in enumerate(detections):
                bbox = det.get('bbox')
                if bbox is None:
                    logger.debug(f"[DEBUG] No bbox for detection {i} of {obj_key}")
                    continue
                    
                if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                    logger.debug(f"[DEBUG] Invalid bbox format for detection {i} of {obj_key}: {bbox}")
                    continue
                    
                try:
                    x1, y1, x2, y2 = map(int, bbox)
                    
                    # 座標の妥当性チェック
                    if x1 < 0 or y1 < 0 or x2 > frame_width or y2 > frame_height:
                        logger.warning(f"[DEBUG] Bbox coordinates out of frame bounds: ({x1}, {y1}, {x2}, {y2}) for frame {frame_width}x{frame_height}")
                    
                    logger.debug(f"[DEBUG] Drawing bbox for {obj_key}[{i}]: ({x1}, {y1}, {x2}, {y2}) on frame {frame_width}x{frame_height}")
                    
                    # 平滑化・補間状態の判定
                    is_smoothed = det.get('smoothed', False)
                    is_interpolated = det.get('interpolated', False)
                    frames_interpolated = det.get('frames_interpolated', 0)
                    
                    # 基本色と線の太さ
                    base_color = obj_settings.get('color', (0, 0, 255))
                    thickness = obj_settings.get('thickness', 2)
                    
                    # 補間された検出の場合は点線描画
                    if is_interpolated:
                        # 補間フレーム数に応じて透明度調整（疑似）
                        alpha_factor = max(0.3, 1.0 - (frames_interpolated * 0.2))
                        
                        # 点線バウンディングボックス描画
                        self._draw_dashed_rectangle(frame, (x1, y1), (x2, y2), base_color, thickness)
                        
                        # 補間マーカーの追加
                        cv2.putText(
                            frame,
                            f"[INT:{frames_interpolated}]",
                            (x1, y1 - 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            (0, 165, 255),  # オレンジ色
                            1
                        )
                    else:
                        # 通常のバウンディングボックス描画
                        cv2.rectangle(frame, (x1, y1), (x2, y2), base_color, thickness)
                        
                        # 平滑化マーカーの追加
                        if is_smoothed:
                            cv2.circle(frame, (x1 + 10, y1 + 10), 3, (0, 255, 0), -1)  # 緑の円
                    
                    # ラベル描画
                    confidence = det.get('confidence', 0.0)
                    label_parts = [f"{obj_settings.get('name')} ({confidence:.2f})"]
                    
                    # 状態ラベルの追加
                    if is_interpolated:
                        label_parts.append("[補間]")
                    elif is_smoothed:
                        label_parts.append("[平滑化]")
                    
                    label = " ".join(label_parts)
                    
                    cv2.putText(
                        frame, 
                        label, 
                        (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, 
                        base_color, 
                        2
                    )
                    
                except (ValueError, TypeError) as e:
                    bbox_error = wrap_exception(
                        e, ValidationError,
                        "Invalid bbox format for drawing",
                        details={
                            'bbox': bbox,
                            'object_key': obj_key,
                            'detection': det
                        }
                    )
                    logger.warning(f"Bbox validation error: {bbox_error.to_dict()}")
                    continue
                    
    def _draw_dashed_rectangle(self, frame: np.ndarray, pt1: tuple, pt2: tuple, color: tuple, thickness: int, dash_length: int = 10) -> None:
        """
        点線の矩形を描画
        
        Args:
            frame: 描画対象フレーム
            pt1: 矩形の左上角
            pt2: 矩形の右下角
            color: 線の色
            thickness: 線の太さ
            dash_length: 点線の長さ
        """
        x1, y1 = pt1
        x2, y2 = pt2
        
        # 上辺
        self._draw_dashed_line(frame, (x1, y1), (x2, y1), color, thickness, dash_length)
        # 右辺
        self._draw_dashed_line(frame, (x2, y1), (x2, y2), color, thickness, dash_length)
        # 下辺
        self._draw_dashed_line(frame, (x2, y2), (x1, y2), color, thickness, dash_length)
        # 左辺
        self._draw_dashed_line(frame, (x1, y2), (x1, y1), color, thickness, dash_length)
        
    def _draw_dashed_line(self, frame: np.ndarray, pt1: tuple, pt2: tuple, color: tuple, thickness: int, dash_length: int = 10) -> None:
        """
        点線を描画
        
        Args:
            frame: 描画対象フレーム
            pt1: 線の開始点
            pt2: 線の終了点
            color: 線の色
            thickness: 線の太さ
            dash_length: 点線の長さ
        """
        import math
        
        x1, y1 = pt1
        x2, y2 = pt2
        
        # 線の長さを計算
        line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        
        if line_length == 0:
            return
            
        # 単位ベクトルを計算
        dx = (x2 - x1) / line_length
        dy = (y2 - y1) / line_length
        
        # 点線を描画
        current_length = 0
        draw_dash = True
        
        while current_length < line_length:
            # 次の点の位置を計算
            next_length = min(current_length + dash_length, line_length)
            
            start_x = int(x1 + current_length * dx)
            start_y = int(y1 + current_length * dy)
            end_x = int(x1 + next_length * dx)
            end_y = int(y1 + next_length * dy)
            
            # 描画フラグに基づいて線を描画
            if draw_dash:
                cv2.line(frame, (start_x, start_y), (end_x, end_y), color, thickness)
            
            current_length = next_length
            draw_dash = not draw_dash  # 描画フラグを切り替え

    def _draw_status_info(self, frame: np.ndarray, results: Dict[str, Any]) -> None:
        """
        ステータス情報の描画
        
        Args:
            frame: 描画対象フレーム
            results: 検出結果（ステータス情報含む）
        """
        status_texts = []
        
        # 不在時間の表示
        absence_time = results.get('absenceTime', 0)
        absence_alert = results.get('absenceAlert', False)
        if absence_time > 0:
            text = f"Absence: {int(absence_time)}s"
            color = (0, 0, 255) if absence_alert else (0, 255, 255)
            status_texts.append({'text': text, 'color': color})
        
        # スマートフォン使用時間の表示
        smartphone_time = results.get('smartphoneUseTime', 0)
        smartphone_alert = results.get('smartphoneAlert', False)
        if smartphone_time > 0:
            text = f"Smartphone: {int(smartphone_time)}s"
            color = (0, 0, 255) if smartphone_alert else (0, 255, 255)
            status_texts.append({'text': text, 'color': color})
        
        # 検出システム無効化警告
        if not self.use_mediapipe and not self.use_yolo:
            status_texts.append({
                'text': "Detection systems disabled", 
                'color': (0, 0, 255)
            })
        
        # ステータステキストの描画
        y_offset = 60
        for status in status_texts:
            cv2.putText(
                frame, 
                status['text'], 
                (10, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                status['color'], 
                2
            )
            y_offset += 30

    def update_settings(self, use_mediapipe: bool = None, use_yolo: bool = None) -> None:
        """
        描画設定を更新
        
        Args:
            use_mediapipe: MediaPipe使用フラグ
            use_yolo: YOLO使用フラグ
        """
        if use_mediapipe is not None:
            self.use_mediapipe = use_mediapipe
            if use_mediapipe and not hasattr(self, 'mp_drawing'):
                self._setup_mediapipe_drawing()
        
        if use_yolo is not None:
            self.use_yolo = use_yolo
        
        # 設定を再読み込み
        if self.config_manager:
            self.landmark_settings = self.config_manager.get_landmark_settings()
            self.detection_objects = self.config_manager.get_detection_objects()
        
        logger.info(f"Renderer settings updated (MediaPipe: {self.use_mediapipe}, YOLO: {self.use_yolo})")

    def get_renderer_status(self) -> Dict[str, Any]:
        """
        レンダラーの状態情報を取得
        
        Returns:
            Dict[str, Any]: 状態情報
        """
        return {
            'use_mediapipe': self.use_mediapipe,
            'use_yolo': self.use_yolo,
            'has_mediapipe_drawing': hasattr(self, 'mp_drawing'),
            'landmark_settings': self.landmark_settings,
            'detection_objects': self.detection_objects
        } 