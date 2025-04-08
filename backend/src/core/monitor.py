import time
import cv2
import threading
from utils.logger import setup_logger
from core.camera import Camera
from core.detector import Detector
from services.alert_manager import AlertManager
from core.state_manager import StateManager
from core.detection_manager import DetectionManager
from web.websocket import broadcast_status
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import platform
import os
from utils.config_manager import ConfigManager

logger = setup_logger(__name__)

class Monitor:
    def __init__(self,
                 config_manager: ConfigManager,
                 camera: Camera,
                 detector: Detector,
                 detection_manager: DetectionManager,
                 state_manager: StateManager,
                 alert_manager: AlertManager):
        """モニターの初期化 (依存性注入・ConfigManager 版)"""
        self.config_manager = config_manager
        self.camera = camera
        self.detector = detector
        self.detection_manager = detection_manager
        self.state_manager = state_manager
        self.alert_manager = alert_manager
        
        # 延長時間を管理する変数
        self.extension_display_time = 0
        self.extension_applied_at = None
        
        # フレームバッファの初期化
        self.frame_buffer = None
        self.frame_lock = threading.Lock()
        
        # 検出結果の初期化
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
        logger.info("Monitor initialized with dependency injection and ConfigManager.")

    def update_detection_results(self, results):
        """検出結果を更新"""
        with self.detection_lock:
            self.detection_results = results

    def get_current_frame(self):
        """WebUIで使用する描画済みのフレームを取得"""
        frame_to_encode = None
        with self.frame_lock:
            if self.frame_buffer is not None:
                # 現在のフレームバッファをコピー
                frame_copy = self.frame_buffer.copy()
                # 最新の検出/ステータス結果を取得
                with self.detection_lock:
                    results_copy = self.detection_results.copy()

                # self.detection_results['landmarks'] からランドマークデータを取得し、
                # detector.py が認識できるキー (pose_landmarks など) に戻す
                landmarks = results_copy.get('landmarks', {}) # これは {'pose': ..., 'hands': ..., 'face': ...}
                if isinstance(landmarks, dict):
                    if 'pose' in landmarks:
                        results_copy['pose_landmarks'] = landmarks.get('pose')
                    if 'hands' in landmarks:
                        results_copy['hands_landmarks'] = landmarks.get('hands')
                    if 'face' in landmarks:
                        results_copy['face_landmarks'] = landmarks.get('face')
                # 不要になった 'landmarks' キーは削除してもよい（任意）
                # if 'landmarks' in results_copy:
                #     del results_copy['landmarks']

                # Detectorに描画を依頼 (修正済みの results_copy を使用)
                frame_to_encode = self.detector.draw_detections(frame_copy, results_copy)

        if frame_to_encode is not None:
            # JPEG形式にエンコード
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            _, buffer = cv2.imencode('.jpg', frame_to_encode, encode_param)
            return buffer.tobytes()
        else:
            # フレームがない場合は空のバイト列などを返すか、Noneを返す
            return None

    def extend_absence_threshold(self, extension_time):
        """absence_thresholdを延長するメソッド"""
        try:
            self.state_manager.absence_threshold += extension_time
            self.extension_display_time = extension_time
            self.extension_applied_at = time.time()
            logger.info(f"Absence threshold updated to: {self.state_manager.absence_threshold}")
            logger.info(f"Extension time set to: {self.extension_display_time}")
            
        except Exception as e:
            logger.error(f"Error extending threshold: {e}")

    def _process_frame(self):
        """フレームを取得し、検出を実行、StateManager を更新する"""
        frame = self.camera.get_frame()
        if frame is None:
            return None

        # 検出処理の実行 (DetectionManagerを使用)
        detections_list = self.detection_manager.detect(frame)

        # StateManager への情報連携
        self.state_manager.update_detection_state(detections_list)

        # StateManager を使った状態更新とアラートチェック
        person_now_detected = self.state_manager.person_detected
        if person_now_detected:
            self.state_manager.handle_person_presence()
        else:
            self.state_manager.handle_person_absence()

        smartphone_found_in_current_frame = any(det.get('label') == 'smartphone' for det in detections_list)
        self.state_manager.handle_smartphone_usage(smartphone_found_in_current_frame)
        
        return frame, detections_list

    def _update_monitor_results(self, detections_list):
        """Monitor 内部の検出結果を更新する"""
        # StateManager から最新の状態を取得 (描画用)
        person_now_detected = self.state_manager.person_detected
        smartphone_now_in_use_for_drawing = self.state_manager.smartphone_in_use
        # StateManagerからステータスサマリーを取得
        status_summary = self.state_manager.get_status_summary()

        # detections_list を draw_detections が期待する形式 (クラス名ごとの辞書) に変換
        detections_dict_for_draw = {}
        for det in detections_list:
            label = det.get('label')
            if label == 'landmarks': continue
            if label:
                if label not in detections_dict_for_draw:
                    detections_dict_for_draw[label] = []
                det_info = {'bbox': det.get('box'), 'confidence': det.get('confidence')}
                det_info = {k: v for k, v in det_info.items() if v is not None and k in ['bbox', 'confidence']}
                if 'bbox' in det_info:
                     detections_dict_for_draw[label].append(det_info)

        # detections_list からランドマーク情報を抽出
        current_landmarks = None
        for item in detections_list:
            if item.get('label') == 'landmarks':
                # シンプルにデータを取得
                current_landmarks = item.get('data')
                break

        with self.detection_lock:
            self.detection_results = {
                'person_detected': person_now_detected,
                'smartphone_detected': smartphone_now_in_use_for_drawing,
                'person_bbox': None,
                'phone_bbox': None,
                'landmarks': current_landmarks,
                'detections': detections_dict_for_draw,
                'absenceTime': status_summary.get('absenceTime', 0),
                'smartphoneUseTime': status_summary.get('smartphoneUseTime', 0),
                'absenceAlert': status_summary.get('absenceAlert', False),
                'smartphoneAlert': status_summary.get('smartphoneAlert', False)
            }

    def _update_frame_buffer(self, frame):
        """フレームバッファを更新する"""
        if frame is not None:
            with self.frame_lock:
                self.frame_buffer = frame.copy()
                
    def _broadcast_status(self):
        """現在のステータスをWebSocketでブロードキャストする"""
        status = self.state_manager.get_status_summary()
        broadcast_status(status)

    def _display_frame(self, frame):
        """OpenCVウィンドウにフレームを表示する（設定が有効な場合）"""
        if self.config_manager.get('display.show_opencv_window', True):
            display_frame = frame.copy()
            # 更新された self.detection_results を使って描画
            with self.detection_lock:
                 results_for_draw = self.detection_results.copy()
                 
                 # self.detection_results['landmarks'] からランドマークデータを取得し、
                 # detector.py が認識できるキー (pose_landmarks など) に戻す
                 landmarks = results_for_draw.get('landmarks', {}) # これは {'pose': ..., 'hands': ..., 'face': ...}
                 if isinstance(landmarks, dict):
                     if 'pose' in landmarks:
                         results_for_draw['pose_landmarks'] = landmarks.get('pose')
                     if 'hands' in landmarks:
                         results_for_draw['hands_landmarks'] = landmarks.get('hands')
                     if 'face' in landmarks:
                         results_for_draw['face_landmarks'] = landmarks.get('face')
                 # 不要になった 'landmarks' キーは削除してもよい（任意）
                 # if 'landmarks' in results_for_draw:
                 #     del results_for_draw['landmarks']
                 
            # draw_detections にステータス情報が含まれたデータを渡す (修正済みの results_for_draw を使用)
            self.detector.draw_detections(display_frame, results_for_draw)
            # 再度有効化
            self.camera.show_frame(display_frame)
            
            # q キーでの終了処理も復活
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("'q' key pressed, stopping monitor.")
                # スレッドを安全に停止させるためのフラグなどを設定する
                # (現状は直接ループを抜ける仕組みがないため、ログ表示のみ)
                # raise KeyboardInterrupt # 強制的に例外を発生させて終了させる場合
                # self.stop_requested = True # フラグを使う場合 (runループ側でチェック)

    def run(self):
        try:
            while True:
                # フレーム処理と状態更新
                processed_data = self._process_frame()
                if processed_data is None:
                    continue
                frame, detections_list = processed_data

                # Monitor内部結果の更新
                self._update_monitor_results(detections_list)

                # フレームバッファ更新とステータスブロードキャスト
                self._update_frame_buffer(frame)
                self._broadcast_status()

                # OpenCVウィンドウ表示 (現在無効化中)
                self._display_frame(frame)

        finally:
            self.cleanup()

    def cleanup(self):
        self.camera.release()
        cv2.destroyAllWindows()

    def draw_detection_results(self, frame):
        """検出結果を画面に描画する"""
        # PILイメージに変換
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # フォントの設定（システムにインストールされているフォントのパスを指定）
        try:
            font_path = self._get_system_font()
            font = ImageFont.truetype(font_path, 32)
        except Exception:
            font = ImageFont.load_default()  # デフォルトフォント
        
        # 状態テキストのリスト
        status_text = []
        
        # 基本的な状態表示
        if self.state_manager.person_detected:
            status_text.append("人物検出中")
        else:
            status_text.append("人物未検出")
        
        if self.state_manager.smartphone_in_use:
            status_text.append("スマホ使用中")
        
        # 警告状態
        if self.state_manager.alert_triggered_absence:
            status_text.append("不在警告中")
        if self.state_manager.alert_triggered_smartphone:
            status_text.append("スマホ使用警告中")

        # 延長時間の表示（閾値の更新状態）
        current_time = time.time()
        if self.extension_applied_at is not None:
            display_duration = 5
            if current_time - self.extension_applied_at < display_duration:
                status_text.append(f"しきい値延長: +{self.extension_display_time}秒")
                logger.info(f"表示中の延長時間: {self.extension_display_time}秒")
            else:
                # 表示期間が終了したらリセット
                logger.info("延長時間の表示期間が終了")
                self.extension_display_time = 0
                self.extension_applied_at = None

        # テキストを描画
        for i, text in enumerate(status_text):
            draw.text((10, 30 + i * 40), text, font=font, fill=(255, 0, 0))
        
        # OpenCV形式に戻す
        frame[:] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _get_system_font(self):
        """OSに応じたフォントパスを返す"""
        system = platform.system()
        try:
            if system == "Windows":
                font_paths = [
                    "C:\\Windows\\Fonts\\msgothic.ttc",  # MSゴシック
                    "C:\\Windows\\Fonts\\meiryo.ttc",    # メイリオ
                    "C:\\Windows\\Fonts\\yugothic.ttf"   # 游ゴシック
                ]
            elif system == "Darwin":  # macOS
                font_paths = [
                    "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
                    "/System/Library/Fonts/AppleGothic.ttf"
                ]
            else:  # Linux
                font_paths = [
                    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
                ]

            # 利用可能なフォントを探す
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return font_path

        except Exception as e:
            logger.warning(f"Error loading system font: {e}")
        
        return None

    def analyze_behavior(self, frame, person_detected, smartphone_in_use):
        """行動分析と適切なアドバイスの生成"""
        current_time = time.time()
        if current_time - self.last_analysis_time < self.analysis_interval:
            return

        try:
            # コンテキストの生成
            context = self._create_context(person_detected, smartphone_in_use)
            # LLMからの応答を取得
            response = self.llm_service.generate_response(context)
            
            if response:
                logger.info(f"LLM Response: {response}")  # デバッグ用ログ
                self.current_llm_response = response
                # 重要なメッセージの場合のみ通知
                if "警告" in response or "注意" in response:
                    self.alert_manager.trigger_alert(response)
            
            self.last_analysis_time = current_time
            
        except Exception as e:
            logger.error(f"行動分析中にエラーが発生: {e}")

    def _create_context(self, person_detected, smartphone_in_use):
        context = []
        if not person_detected:
            context.append("ユーザーが席を離れています")
        elif smartphone_in_use:
            context.append("ユーザーがスマートフォンを使用しています")
        else:
            context.append("ユーザーが勉強に集中しています")

        return " ".join(context)
