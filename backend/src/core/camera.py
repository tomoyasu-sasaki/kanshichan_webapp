import cv2
import time
import platform
import numpy as np
from screeninfo import get_monitors
from utils.logger import setup_logger
from utils.config_manager import ConfigManager

logger = setup_logger(__name__)

class Camera:
    def __init__(self, config_manager=None):
        """カメラの初期化とウィンドウのセットアップを行う"""
        try:
            # 設定の読み込み
            self.config_manager = config_manager
            self.show_window = False
            if config_manager:
                self.show_window = config_manager.get('display.show_opencv_window', False)
                
            # カメラの初期化を試みる
            self.cap = self._initialize_camera()
            if not self.cap.isOpened():
                logger.error("Error: Could not open camera. Using dummy camera.")
                self._use_dummy_camera = True
            else:
                self._use_dummy_camera = False
                # 画面サイズの設定
                self.screen_width, self.screen_height = self._get_screen_dimensions()
                self._setup_camera()
                
            # ウィンドウのセットアップは共通
            self._setup_window()
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            # ダミーカメラモードを有効化
            self._use_dummy_camera = True
            self.screen_width, self.screen_height = 640, 480
            # OpenCVのVideoCaptureをダミーで初期化
            self.cap = None

    def _initialize_camera(self):
        """OSに応じたカメラの初期化"""
        system = platform.system()
        try:
            if system == "Windows":
                return cv2.VideoCapture(0, cv2.CAP_DSHOW)  # DirectShowを使用
            elif system == "Darwin":  # macOS
                return cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
            else:  # Linux等
                return cv2.VideoCapture(0)
        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            # フォールバックを試みる
            try:
                return cv2.VideoCapture(0)
            except Exception as e2:
                logger.error(f"Fallback camera initialization also failed: {e2}")
                # ダミーモードを使用
                return cv2.VideoCapture()

    def _get_screen_dimensions(self):
        """クロスプラットフォーム対応の画面サイズ取得"""
        try:
            monitors = get_monitors()
            if monitors:
                primary = monitors[0]
                return primary.width, primary.height
        except Exception as e:
            logger.warning(f"Failed to get screen dimensions: {e}")
        
        # デフォルト値
        return 1280, 720

    def _setup_camera(self):
        """カメラのプロパティを設定する"""
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.screen_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.screen_height)
        self.cap.set(cv2.CAP_PROP_FPS, 15)
        logger.info("Camera properties set successfully")

    def _setup_window(self):
        """表示ウィンドウの設定を行う"""
        self.window_name = 'KanshiChan Monitor'
        
        # 設定に基づいてウィンドウ表示を制御
        if self.show_window:
            try:
                # ウィンドウ表示の有効化
                cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                
                # ウィンドウサイズを設定（画面の80%）
                window_width = int(self.screen_width * 0.8)
                window_height = int(self.screen_height * 0.8)
                cv2.resizeWindow(self.window_name, window_width, window_height)
                
                # ウィンドウを画面中央に配置
                cv2.moveWindow(self.window_name, 
                              (self.screen_width - window_width) // 2,
                              (self.screen_height - window_height) // 2)
                
                logger.info("Display window setup enabled per configuration")
            except Exception as e:
                logger.error(f"Error setting up window: {e}")
                self.show_window = False
        else:
            logger.info("Display window setup disabled per configuration")

    def get_frame(self):
        """カメラからフレームを取得する"""
        if self._use_dummy_camera:
            # ダミーモード - 黒い画像を生成
            frame = self._create_dummy_frame()
            return frame
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to grab frame from camera")
                # 一時的にダミーフレームを返す
                return self._create_dummy_frame()

            # アスペクト比を維持しながらリサイズ
            frame = self._resize_frame(frame)
            return frame
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            return self._create_dummy_frame()

    def _resize_frame(self, frame):
        """フレームをアスペクト比を維持しながらリサイズする"""
        aspect_ratio = frame.shape[1] / frame.shape[0]
        if self.screen_width / self.screen_height > aspect_ratio:
            new_width = int(self.screen_height * aspect_ratio)
            new_height = self.screen_height
        else:
            new_width = self.screen_width
            new_height = int(self.screen_width / aspect_ratio)
        
        return cv2.resize(frame, (new_width, new_height))

    def show_frame(self, frame):
        """フレームを表示する"""
        if frame is None:
            return
            
        try:
            # 設定に基づいて表示を制御
            if self.show_window:
                # ウィンドウのサイズに合わせてリサイズ
                window_width = int(self.screen_width * 0.8)
                window_height = int(self.screen_height * 0.8)
                display_frame = cv2.resize(frame, (window_width, window_height))
                cv2.imshow(self.window_name, display_frame)
                cv2.waitKey(1)  # UIの更新に必要
            else:
                # 表示せずにUI更新だけ行う
                cv2.waitKey(1)
        except Exception as e:
            logger.error(f"Error processing frame: {e}")

    def release(self):
        """カメラリソースを解放する"""
        try:
            if self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()
            logger.info("Camera resources released")
        except Exception as e:
            logger.error(f"Error releasing camera resources: {e}")

    def _create_dummy_frame(self):
        """カメラが使用できない場合のダミーフレームを生成"""
        # 黒い画像
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # テキストを追加
        cv2.putText(
            dummy_frame,
            "Camera not available",
            (100, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        return dummy_frame 