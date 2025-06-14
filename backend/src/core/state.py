import time
from collections import defaultdict
from utils.logger import setup_logger
from typing import Any, Dict, List
# AlertManager をインポート
from services.communication.alert_manager import AlertManager
from utils.config_manager import ConfigManager # ConfigManager をインポート

logger = setup_logger(__name__)

class StateManager:
    """
    人物検出、スマホ使用などの状態を管理し、状態遷移に基づいてアラートをトリガーするクラス。
    ConfigManager を介して設定を管理する。
    """
    def __init__(self, config_manager: ConfigManager, alert_manager: AlertManager): # 引数を config_manager に変更
        self.config_manager = config_manager # インスタンス変数名を変更
        if alert_manager is None:
            # AlertManager は必須とする
            logger.error("AlertManager instance is required for StateManager.")
            raise ValueError("AlertManager instance cannot be None.")
        self.alert_manager = alert_manager # AlertManager を保持
        # Monitor から移動してくる状態変数を初期化
        self.person_detected = False
        self.smartphone_in_use = False
        # self.alert_triggered_absence = False # __init__で設定済み
        # self.alert_triggered_smartphone = False # __init__で設定済み
        self.last_seen_time = time.time()
        self.last_phone_detection_time = time.time()
        self.smartphone_start_time: float | None = None # スマホ使用開始時刻
        self.person_absence_start_time: float | None = None # 不在開始時刻

        # アラート状態 (重複しているので削除しても良いが、明示的に残す)
        self.alert_triggered_absence: bool = False
        self.alert_triggered_smartphone: bool = False

        # 閾値 (ConfigManager から取得)
        self.absence_threshold = self.config_manager.get('conditions.absence.threshold_seconds', 10) # デフォルト10秒
        self.smartphone_threshold = self.config_manager.get('conditions.smartphone_usage.threshold_seconds', 5) # デフォルト5秒
        self.smartphone_grace_period = self.config_manager.get('conditions.smartphone_usage.grace_period_seconds', 3.0) # スマホ検知猶予時間
        logger.info("StateManager initialized with ConfigManager.")
        logger.info(f"Absence threshold: {self.absence_threshold}s, Smartphone threshold: {self.smartphone_threshold}s, Smartphone grace period: {self.smartphone_grace_period}s")

    def update_detection_state(self, detections_list: List[Dict[str, Any]]):
        """検出結果リストに基づいて人物検出状態を更新する"""
        # リストを走査して人物が検出されたか確認
        person_found = any(det.get('label') == 'person' for det in detections_list)
        # self.person_detected = person_found # ここでは設定しない
        # logger.debug(f"Updated state: person_detected={self.person_detected}") # 必要ならコメント解除

        # スマートフォンが検出されたかどうかのフラグもここで決定
        smartphone_found = any(det.get('label') == 'smartphone' for det in detections_list)

        # Person 状態更新
        if person_found:
            self.handle_person_presence()
        else:
            self.handle_person_absence() # 内部で person_absence_start_time を管理

        # Smartphone 状態更新
        self.handle_smartphone_usage(smartphone_found) # 内部で smartphone_start_time を管理

    def handle_person_presence(self):
        """人物が検出された場合の処理"""
        if not self.person_detected:
            logger.debug("Person detected.") # ログレベル変更
        self.person_detected = True
        self.last_seen_time = time.time()
        self.person_absence_start_time = None # 不在状態をリセット
        if self.alert_triggered_absence:
            logger.debug("Absence alert reset.") # ログレベル変更
            self.alert_triggered_absence = False

    def handle_person_absence(self):
        """人物が検出されなかった場合の処理"""
        current_time = time.time()
        if self.person_detected:
            # 初めて不在になった瞬間
            logger.debug("Person lost.") # ログレベル変更
            self.person_absence_start_time = self.last_seen_time # 不在開始は最後に検出された時刻
        self.person_detected = False # 状態を更新

        # 不在時間が閾値を超えたかチェック
        # 不在開始時刻が記録されていて、かつまだアラートが発動していない場合
        if self.person_absence_start_time and not self.alert_triggered_absence:
            absence_duration = current_time - self.person_absence_start_time
            if absence_duration > self.absence_threshold:
                logger.warning(f"Absence detected for {absence_duration:.0f} seconds (Threshold: {self.absence_threshold}s). Triggering alert.")
                # AlertManager を介して AlertService のメソッドを呼ぶ
                self.alert_manager.trigger_absence_alert(absence_duration)
                self.alert_triggered_absence = True

    def handle_smartphone_usage(self, smartphone_detected: bool):
        """スマホ使用状態の処理（猶予時間付き）"""
        current_time = time.time()

        if smartphone_detected:
            # スマホが検出された場合
            self.last_phone_detection_time = current_time # 最後に検出された時刻を更新
            if not self.smartphone_in_use:
                # 初めて検出された（使用開始）
                logger.info("🔍 スマートフォン検出: 使用開始を検知しました") # INFOレベルに変更・日本語メッセージ追加
                self.smartphone_in_use = True
                self.smartphone_start_time = current_time # 開始時刻を記録 ★修正
            # else: すでに使用中の場合は何もしない (開始時刻は維持)

            # 使用時間が閾値を超えたかチェック
            # 使用が開始されていて、かつまだアラートが発動していない場合
            if self.smartphone_start_time and not self.alert_triggered_smartphone:
                usage_duration = current_time - self.smartphone_start_time
                if usage_duration > self.smartphone_threshold:
                    logger.warning(f"Smartphone used for {usage_duration:.0f} seconds (Threshold: {self.smartphone_threshold}s). Triggering alert.")
                    # AlertManager を介して AlertService のメソッドを呼ぶ
                    self.alert_manager.trigger_smartphone_alert(usage_duration)
                    self.alert_triggered_smartphone = True
        else:
            # スマホが検出されなかった場合
            if self.smartphone_in_use:
                # 直前まで使用していた場合 - 猶予時間をチェック
                time_since_last_detection = current_time - self.last_phone_detection_time
                if time_since_last_detection > self.smartphone_grace_period:
                    # 猶予時間を超えて検出されない場合のみ使用終了
                    logger.info(f"🔍 スマートフォン検出終了: 猶予時間経過後に使用停止 ({time_since_last_detection:.1f}s > {self.smartphone_grace_period}s)") # INFOレベルに変更
                    self.smartphone_in_use = False
                    self.smartphone_start_time = None # 開始時刻をリセット ★修正
                    if self.alert_triggered_smartphone:
                        # アラートもリセット
                        logger.debug("Smartphone alert reset.") # ログレベル変更
                        self.alert_triggered_smartphone = False
                # else: 猶予時間内なので使用継続と見なす（何もしない）
            # else: 元々使用していなかった場合は何もしない

    def get_status_summary(self):
        """現在の状態サマリーを返す"""
        current_time = time.time()
        absence_time = 0
        # 不在状態の場合のみ計算
        if not self.person_detected and self.person_absence_start_time:
            absence_time = current_time - self.person_absence_start_time

        smartphone_use_time = 0
        # スマホ使用中の場合のみ計算
        if self.smartphone_in_use and self.smartphone_start_time:
            smartphone_use_time = current_time - self.smartphone_start_time

        # キー名を WebSocket や フロントエンドに合わせて修正
        return {
            "personDetected": self.person_detected, # キャメルケースに変更
            "smartphoneDetected": self.smartphone_in_use, # キー名と値を変更
            "absenceTime": absence_time,
            "smartphoneUseTime": smartphone_use_time,
            "absenceAlert": self.alert_triggered_absence,
            "smartphoneAlert": self.alert_triggered_smartphone,
            "absenceThreshold": self.absence_threshold,
            "smartphoneThreshold": self.smartphone_threshold,
            "smartphoneGracePeriod": self.smartphone_grace_period,
            # detected_objects の状態も必要に応じて追加
        }

    # --- 以下、将来的に追加される可能性のあるメソッド --- (コメントは削除)
    # def reset_alerts(self):
    #     self.alert_triggered_absence = False
    #     self.alert_triggered_smartphone = False

    # def set_absence_threshold(self, threshold):
    #     self.absence_threshold = threshold

    # def set_smartphone_threshold(self, threshold):
    #     self.smartphone_threshold = threshold 