import cv2
from src.kanshichan.utils.logger import setup_logger

logger = setup_logger(__name__)

class Camera:
    def __init__(self):
        """カメラの初期化とウィンドウのセットアップを行う"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("Error: Could not open camera.")
        
        # 画面サイズの設定
        self.screen_width, self.screen_height = self._get_screen_dimensions()
        self._setup_camera()
        self._setup_window()

    def _get_screen_dimensions(self):
        """画面サイズを取得する"""
        try:
            from AppKit import NSScreen
            screen_width = int(NSScreen.mainScreen().frame().size.width)
            screen_height = int(NSScreen.mainScreen().frame().size.height)
            logger.info("Using macOS screen dimensions")
        except ImportError:
            screen_width = 1280
            screen_height = 720
            logger.info("Using default screen dimensions")
        return screen_width, screen_height

    def _setup_camera(self):
        """カメラのプロパテ��を設定する"""
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.screen_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.screen_height)
        self.cap.set(cv2.CAP_PROP_FPS, 15)
        logger.info("Camera properties set successfully")

    def _setup_window(self):
        """表示ウィンドウの設定を行う"""
        self.window_name = 'Monitor'
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(
            self.window_name,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN
        )
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