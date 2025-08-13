import cv2
import time
import platform
import numpy as np
from screeninfo import get_monitors
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.exceptions import (
    CameraError, CameraInitializationError, CameraFrameError,
    ConfigError, HardwareError, wrap_exception
)
import threading
import os

logger = setup_logger(__name__)

class Camera:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_manager=None):
        """カメラの初期化とウィンドウのセットアップを行う"""
        with self._lock:
            if hasattr(self, '_initialized') and self._initialized:
                return
            
            self.frame_lock = threading.Lock()

            try:
                # 設定の読み込み
                self.config_manager = config_manager
                self.show_window = False
                self.device_index = 0  # デフォルト値
                if config_manager:
                    self.show_window = config_manager.get('display.show_opencv_window', False)
                    self.device_index = config_manager.get('camera.device_index', 0)
                
                # カメラの初期化を試みる
                self.cap = self._initialize_camera()
                if not self.cap or not self.cap.isOpened():
                    logger.error(f"Error: Could not open camera (index: {self.device_index}). Using dummy camera.")
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
                # カスタム例外としてリログ（ダミーモードで継続するため、raiseはしない）
                camera_error = wrap_exception(
                    e, CameraInitializationError,
                    "Camera initialization failed, falling back to dummy mode",
                    details={'dummy_mode': True, 'screen_size': (640, 480), 'device_index': self.device_index}
                )
                logger.warning(f"Camera error details: {camera_error.to_dict()}")

            self._initialized = True

    def _initialize_camera(self):
        """OSに応じたカメラの初期化"""
        system = platform.system()
        try:
            if system == "Windows":
                return cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)  # DirectShowを使用
            elif system == "Darwin":  # macOS
                # macOS Sonoma以降の問題に対応するため、設定ファイルから読み込んだインデックスを使用
                logger.info(f"Initializing camera for macOS with device index: {self.device_index}")
                return cv2.VideoCapture(self.device_index, cv2.CAP_AVFOUNDATION)
            else:  # Linux等
                return cv2.VideoCapture(self.device_index)
        except Exception as e:
            logger.error(f"Camera initialization error with index {self.device_index}: {e}")
            # フォールバックを試みる
            try:
                if self.device_index != 0:
                    logger.warning("Falling back to camera index 0")
                    return cv2.VideoCapture(0)
                raise e # 0でも失敗した場合は再raise
            except Exception as e2:
                logger.error(f"Fallback camera initialization also failed: {e2}")
                # 詳細なエラー情報をログ
                fallback_error = wrap_exception(
                    e2, CameraInitializationError,
                    "Both primary and fallback camera initialization failed",
                    details={
                        'primary_index': self.device_index,
                        'fallback_index': 0,
                        'primary_error': str(e),
                        'fallback_error': str(e2),
                        'platform': platform.system()
                    }
                )
                logger.error(f"Complete camera failure: {fallback_error.to_dict()}")
                # ダミーモードを使用
                return None

    def _get_screen_dimensions(self):
        """クロスプラットフォーム対応の画面サイズ取得"""
        try:
            monitors = get_monitors()
            if monitors:
                primary = monitors[0]
                return primary.width, primary.height
        except Exception as e:
            screen_error = wrap_exception(
                e, HardwareError,
                "Failed to get screen dimensions, using defaults",
                details={'default_size': (1280, 720)}
            )
            logger.warning(f"Screen dimension error: {screen_error.to_dict()}")
        
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
            # ヘッドレスモードやスレッド状況に応じて安全に無効化
            headless = os.environ.get('KANSHICHAN_HEADLESS', '0').lower() in ('1', 'true', 'yes') or \
                       os.environ.get('KANSHICHAN_DISABLE_OPENCV_WINDOW', '0').lower() in ('1', 'true', 'yes')
            if headless:
                logger.info("OpenCV window disabled due to headless environment variables")
                self.show_window = False
                logger.info("Display window setup disabled per configuration")
                return
            if threading.current_thread() is not threading.main_thread():
                # macOS などで非メインスレッドからのUI操作はクラッシュ要因
                logger.warning("OpenCV window requested but not on main thread; disabling to avoid crash")
                self.show_window = False
                logger.info("Display window setup disabled per configuration")
                return
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
                window_error = wrap_exception(
                    e, CameraError,
                    "Error setting up camera display window",
                    details={'window_disabled': True}
                )
                logger.error(f"Window setup error: {window_error.to_dict()}")
                self.show_window = False
        else:
            logger.info("Display window setup disabled per configuration")

    def get_frame(self):
        """カメラからフレームを取得する"""
        with self.frame_lock:
            if self._use_dummy_camera:
                # ダミーモード - 黒い画像を生成
                frame = self._create_dummy_frame()
                return True, frame

            if not self.cap or not self.cap.isOpened():
                logger.error("Camera is not available.")
                return False, self._create_dummy_frame()
            
            try:
                ret, frame = self.cap.read()
                if not ret:
                    logger.error("Failed to grab frame from camera")
                    return False, self._create_dummy_frame()

                # アスペクト比を維持しながらリサイズ
                resized_frame = self._resize_frame(frame)
                return True, resized_frame
            except Exception as e:
                frame_error = wrap_exception(
                    e, CameraFrameError,
                    "Error capturing frame from camera",
                    details={'fallback_to_dummy': True}
                )
                logger.error(f"Frame capture error: {frame_error.to_dict()}")
                return False, self._create_dummy_frame()

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
            if self.show_window and threading.current_thread() is threading.main_thread():
                # ウィンドウのサイズに合わせてリサイズ
                window_width = int(self.screen_width * 0.8)
                window_height = int(self.screen_height * 0.8)
                display_frame = cv2.resize(frame, (window_width, window_height))
                cv2.imshow(self.window_name, display_frame)
                cv2.waitKey(1)  # UIの更新に必要
            elif self.show_window and threading.current_thread() is not threading.main_thread():
                # 非メインスレッドからのUI操作は避ける
                logger.debug("Skipping cv2.imshow from non-main thread to avoid crash")
            else:
                # 表示なし（waitKeyも不要）
                pass
        except Exception as e:
            display_error = wrap_exception(
                e, CameraError,
                "Error displaying frame",
                details={'show_window': self.show_window}
            )
            logger.error(f"Frame display error: {display_error.to_dict()}")

    def release(self):
        """カメラリソースを解放する"""
        with self.frame_lock:
            try:
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None
                # 非メインスレッドでの破棄は避ける
                if self.show_window and threading.current_thread() is threading.main_thread():
                    cv2.destroyAllWindows()
                logger.info("Camera resources released")
            except Exception as e:
                release_error = wrap_exception(
                    e, CameraError,
                    "Error releasing camera resources",
                    details={'cleanup_partial': True}
                )
                logger.error(f"Resource release error: {release_error.to_dict()}")

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