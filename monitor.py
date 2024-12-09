import os
import sys
import time
import yaml
import threading
import logging
import cv2
import mediapipe as mp
import torch
import simpleaudio as sa
from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    MessagingApi,
    ApiClient,
    PushMessageRequest,
    ApiException,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from twilio.rest import Client
from concurrent.futures import ThreadPoolExecutor
from ultralytics import YOLO

try:
    from AppKit import NSScreen  # macOS用
    MAC_OS = True
except ImportError:
    MAC_OS = False

# ----------------------------------------
# ロギング設定
# ----------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ----------------------------------------
# 設定ファイル読み込み
# ----------------------------------------
BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# ----------------------------------------
# 閾値の設定
# ----------------------------------------
absence_threshold = config['conditions']['absence']['threshold_seconds']
smartphone_threshold = config['conditions']['smartphone_usage']['threshold_seconds']

MAX_ABSENCE_THRESHOLD = 3600   # 不在最大閾値（秒）
MAX_SMARTPHONE_THRESHOLD = 1800  # スマホ使用最大閾値（秒）

initial_thresholds = {
    "absence": absence_threshold,
    "smartphone_usage": smartphone_threshold
}

threshold_lock = threading.Lock()

# ----------------------------------------
# LINE・Twilio設定
# ----------------------------------------
line_token = config['line']['token']
line_user_id = config['line']['user_id']
line_channel_secret = config['line']['channel_secret']
line_bot_api = WebhookHandler(line_token)
line_handler = WebhookHandler(line_channel_secret)

twilio_settings = config['twilio']
account_sid = twilio_settings['account_sid']
auth_token = twilio_settings['auth_token']
to_number = twilio_settings['to_number']
from_number = twilio_settings['from_number']

# ----------------------------------------
# Mediapipe・YOLO設定
# ----------------------------------------
mp_pose = mp.solutions.pose
FRAME_SKIP = 3
PROCESS_INTERVAL = 0.1
SMARTPHONE_RESET_BUFFER = 5.0
PHONE_DETECTION_CONFIDENCE = 0.3

# デバイスの設定
if torch.backends.mps.is_available():
    device = torch.device("mps")
    logger.info("MPS is available. Using MPS backend.")
elif torch.cuda.is_available():
    device = torch.device("cuda")
    logger.info("CUDA is available. Using GPU.")
else:
    device = torch.device("cpu")
    logger.info("Using CPU.")

model = YOLO("yolov8n.pt")
model.to(device)

# ----------------------------------------
# 活動内容と閾値変動マッピング
# ----------------------------------------
activity_threshold_map = {
    "お風呂入ってくる": {"type": "absence", "additional_time": 600, "sound_file": "bath.wav"},
    "買い物行ってくる": {"type": "smartphone", "additional_time": 1200, "sound_file": "shopping.wav"},
    "料理しなきゃ": {"type": "absence", "additional_time": 900, "sound_file": "cooking.wav"},
    "散歩してくる": {"type": "absence", "additional_time": 1200, "sound_file": "walking.wav"},
    "シコってくる": {"type": "absence", "additional_time": 600, "sound_file": "alone.wav"},
    "とりあえず席外す": {"type": "absence", "additional_time": 600, "sound_file": "leaving_seat.wav"},
}

# ----------------------------------------
# スレッドプール設定
# ----------------------------------------
executor = ThreadPoolExecutor(max_workers=4)

# ----------------------------------------
# Flask設定（LINE Webhook用）
# ----------------------------------------
app = Flask(__name__)

# ----------------------------------------
# 関数定義
# ----------------------------------------
def save_thresholds():
    """現在の閾値をconfig.yamlに保存する。"""
    with threshold_lock:
        config['conditions']['absence']['threshold_seconds'] = absence_threshold
        config['conditions']['smartphone_usage']['threshold_seconds'] = smartphone_threshold
    try:
        with open(CONFIG_PATH, 'w') as f:
            yaml.safe_dump(config, f)
        logger.info("Thresholds saved to config.yaml")
    except Exception as e:
        logger.error(f"Error saving thresholds to config.yaml: {e}")

def play_sound_alert(sound_file='alert.wav'):
    """音声アラートを別スレッドで非同期再生する。"""
    def play():
        try:
            sound_dir = os.path.join(BASE_DIR, 'sounds')
            sound_path = os.path.join(sound_dir, sound_file)

            if not os.path.exists(sound_path):
                logger.warning(f"Sound file not found: {sound_path}, falling back to default alert.wav")
                sound_path = os.path.join(sound_dir, 'alert.wav')
                if not os.path.exists(sound_path):
                    logger.error("Default alert sound not found.")
                    return

            wave_obj = sa.WaveObject.from_wave_file(sound_path)
            play_obj = wave_obj.play()
            play_obj.wait_done()
            logger.info(f"Sound played successfully: {sound_path}")
        except Exception as e:
            logger.error(f"Error playing sound: {e}")

    threading.Thread(target=play, daemon=True).start()

def send_line_message(message):
    """LINEへプッシュメッセージを送信する。"""
    try:
        line_bot_api.push_message_with_http_info(
            PushMessageRequest(
                to='送信先のID',
                messages=[message]
            )
        )
        logger.info("LINE message sent successfully.")
    except Exception as e:
        logger.error(f"Error sending LINE message: {e}")

def send_sms(message):
    """Twilioを介してSMSを送信する。"""
    client = Client(account_sid, auth_token)
    try:
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        logger.info(f"SMS sent successfully. SID: {msg.sid}")
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")

def trigger_alert(message, sound_file='alert.wav'):
    """非同期で通知と音声再生を実行する。"""
    executor.submit(send_line_message, TextMessage(message))
    executor.submit(play_sound_alert, sound_file)

# ----------------------------------------
# LINEメッセージイベントハンドラ
# ----------------------------------------
@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global absence_threshold, smartphone_threshold
    user_message = event.message.text.strip()

    logger.info(f"Received message from LINE: {user_message}")

    if user_message in activity_threshold_map:
        activity = activity_threshold_map[user_message]
        logger.debug(f"Activity matched: {activity}")

        try:
            with threshold_lock:
                # 閾値更新
                if activity["type"] == "absence":
                    new_threshold = min(absence_threshold + activity["additional_time"], MAX_ABSENCE_THRESHOLD)
                    if new_threshold != absence_threshold:
                        absence_threshold = new_threshold
                        response = f"{user_message}のため不在閾値を{activity['additional_time']}秒延長しました。\n現在の不在閾値: {absence_threshold}秒"
                    else:
                        response = f"不在閾値の最大値{MAX_ABSENCE_THRESHOLD}秒を超えるためこれ以上延長できません。\n現在の不在閾値: {absence_threshold}秒"
                elif activity["type"] == "smartphone":
                    new_threshold = min(smartphone_threshold + activity["additional_time"], MAX_SMARTPHONE_THRESHOLD)
                    if new_threshold != smartphone_threshold:
                        smartphone_threshold = new_threshold
                        response = f"{user_message}のためスマホ使用閾値を{activity['additional_time']}秒延長しました。\n現在のスマホ使用閾値: {smartphone_threshold}秒"
                    else:
                        response = f"スマホ使用閾値の最大値{MAX_SMARTPHONE_THRESHOLD}秒を超えるためこれ以上延長できません。\n現在のスマホ使用閾値: {smartphone_threshold}秒"
                else:
                    response = "設定エラーが発生しました。"

                # 閾値保存
                save_thresholds()
                sound_file = activity.get("sound_file", "alert.wav")

        except Exception as e:
            logger.error(f"Error in handle_message: {e}")
            response = "エラーが発生しました。"
            sound_file = "error.wav"

        # 応答メッセージ送信
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
            logger.info(f"LINE response sent: {response}")
        except Exception as e:
            logger.error(f"Error sending LINE reply: {e}")

        # 音声アラート再生
        play_sound_alert(sound_file)

    elif user_message == "リセット":
        with threshold_lock:
            absence_threshold = initial_thresholds["absence"]
            smartphone_threshold = initial_thresholds["smartphone_usage"]
            response = "閾値を初期値にリセットしました。"
            save_thresholds()

        # 応答メッセージ送信
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
            logger.info(response)
        except Exception as e:
            logger.error(f"Error sending LINE reply: {e}")

        # リセット音再生（必要なら）
        play_sound_alert("reset.wav")

    else:
        # 未知コマンド
        response = "申し訳ありませんが、そのコマンドは認識できません。"
        play_sound_alert("unknown_command.wav")
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
            logger.info(response)
        except Exception as e:
            logger.error(f"Error sending LINE reply: {e}")

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhookコールバックエンドポイント。"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    logger.debug(f"Request body: {body}")

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        # エラーが発生しても200を返す（LINE側の再送を防止）
        return 'OK', 200

    return 'OK', 200

def run_flask():
    """Flaskサーバーを実行する。"""
    app.run(host='0.0.0.0', port=5001, debug=False)

# ----------------------------------------
# メイン処理
# ----------------------------------------
if __name__ == "__main__":
    # Flaskサーバースレッド開始
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server started on port 5001")

    # Mediapipe初期化
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # カメラ初期化
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Error: Could not open camera.")

    # 画面サイズ取得
    if MAC_OS:
        screen_width = int(NSScreen.mainScreen().frame().size.width)
        screen_height = int(NSScreen.mainScreen().frame().size.height)
    else:
        screen_width = 1280
        screen_height = 720

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, screen_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, screen_height)
    cap.set(cv2.CAP_PROP_FPS, 15)

    window_name = 'Monitor'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    last_seen_time = time.time()
    alert_triggered_absence = False
    smartphone_in_use = False
    alert_triggered_smartphone = False
    last_phone_detection_time = time.time()
    frame_count = 0
    last_process_time = time.time()

    try:
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.error("Failed to grab frame from camera.")
                    break

                frame_count += 1
                current_time = time.time()

                # フレームスキップとインターバル
                if frame_count % FRAME_SKIP != 0 or (current_time - last_process_time) < PROCESS_INTERVAL:
                    continue
                last_process_time = current_time

                # フレームリサイズ（フルスクリーン表示用）
                aspect_ratio = frame.shape[1] / frame.shape[0]
                if screen_width / screen_height > aspect_ratio:
                    new_width = int(screen_height * aspect_ratio)
                    new_height = screen_height
                else:
                    new_width = screen_width
                    new_height = int(screen_width / aspect_ratio)
                frame = cv2.resize(frame, (new_width, new_height))

                # Mediapipe Pose検出
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(frame_rgb)

                person_detected = bool(results.pose_landmarks)
                if person_detected:
                    last_seen_time = current_time
                    if alert_triggered_absence:
                        alert_triggered_absence = False
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS
                    )

                # 不在時間計測
                absence_time = current_time - last_seen_time

                # 不在アラート判定
                if absence_time > absence_threshold and not alert_triggered_absence:
                    msg = "早く監視範囲に戻れ～！"
                    trigger_alert(msg, 'person_alert.wav')
                    alert_triggered_absence = True

                # スマホ検出（人がいるときのみ実施）
                if person_detected:
                    yolo_results = model.predict(
                        frame,
                        conf=PHONE_DETECTION_CONFIDENCE,
                        iou=0.45,
                        device=device,
                        verbose=False,
                        imgsz=(640, 640)
                    )
                    detections = yolo_results[0].boxes
                    class_names = model.names

                    cell_phone_detected = False
                    for box in detections:
                        cls_id = int(box.cls[0].item()) if hasattr(box.cls[0], 'item') else int(box.cls[0])
                        class_name = class_names.get(cls_id, "").lower()

                        if class_name in ["cell phone", "smartphone", "phone", "mobile phone", "remote"]:
                            cell_phone_detected = True
                            last_phone_detection_time = current_time
                            break

                    if cell_phone_detected:
                        if not smartphone_in_use:
                            smartphone_in_use = True
                            last_seen_smartphone_time = current_time
                        else:
                            smartphone_usage_time = current_time - last_seen_smartphone_time
                            if smartphone_usage_time > smartphone_threshold and not alert_triggered_smartphone:
                                msg = "スマホばかり触っていないで勉強をしろ！"
                                trigger_alert(msg, 'smartphone_alert.wav')
                                alert_triggered_smartphone = True
                    else:
                        # スマホ未検出が一定時間続いたらリセット
                        if current_time - last_phone_detection_time > SMARTPHONE_RESET_BUFFER:
                            smartphone_in_use = False
                            alert_triggered_smartphone = False
                else:
                    # 人がいない場合はスマホ状態もリセット
                    smartphone_in_use = False
                    alert_triggered_smartphone = False

                # 情報表示（デバッグ用）
                cv2.putText(frame, f"Absence Time: {int(absence_time)}s", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                if smartphone_in_use:
                    smartphone_usage_time = int(current_time - last_seen_smartphone_time)
                    cv2.putText(frame, f"Smartphone: {smartphone_usage_time}s", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                else:
                    cv2.putText(frame, "Smartphone: No", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                # フルスクリーン表示
                display_frame = cv2.resize(frame, (screen_width, screen_height))
                cv2.imshow(window_name, display_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Quit signal received.")
                    break

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Shutting down gracefully.")
            # ここでbreakすることでfinally節に移行
            pass

    finally:
        # リソースの解放処理
        cap.release()
        cv2.destroyAllWindows()
        pose.close()
        executor.shutdown(wait=True)
        logger.info("Resources released and executor shutdown completed.")
        sys.exit(0)