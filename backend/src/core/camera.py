import cv2
import platform
from screeninfo import get_monitors
from backend.src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Camera:
    def __init__(self):
        """カメラの初期化とウィンドウのセットアップを行う"""
        self.cap = self._initialize_camera()
        if not self.cap.isOpened():
            raise Exception("Error: Could not open camera.")
        
        # 画面サイズの設定
        self.screen_width, self.screen_height = self._get_screen_dimensions()
        self._setup_camera()
        self._setup_window()

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
            return cv2.VideoCapture(0)  # フォールバック

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
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        # ウィンドウサイズを設定（画面の80%）
        window_width = int(self.screen_width * 0.8)
        window_height = int(self.screen_height * 0.8)
        cv2.resizeWindow(self.window_name, window_width, window_height)
        
        # ウィンドウを画面中央に配置
        cv2.moveWindow(self.window_name, 
                      (self.screen_width - window_width) // 2,
                      (self.screen_height - window_height) // 2)
        
        logger.info("Display window setup completed")

    def get_frame(self):
        """カメラからフレームを取得する"""
        ret, frame = self.cap.read()
        if not ret:
            logger.error("Failed to grab frame from camera")
            return None

        # アスペクト比を維持しながらリサイズ
        frame = self._resize_frame(frame)
        return frame

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
        if frame is not None:
            display_frame = cv2.resize(frame, (self.screen_width, self.screen_height))
            cv2.imshow(self.window_name, display_frame)

    def release(self):
        """カメラリソースを解放する"""
        self.cap.release()
        cv2.destroyAllWindows()
        logger.info("Camera resources released") 