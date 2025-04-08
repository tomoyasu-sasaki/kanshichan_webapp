# KanshiChan リファクタリング計画

このドキュメントは、KanshiChan プロジェクトのコードベースの可読性、保守性、拡張性を向上させるためのリファクタリング計画とその進捗を管理します。

## 目的

*   バックエンドの `Monitor` クラスの責務を適切に分割する (God Class の解消)。
*   状態管理ロジックを明確にし、集約する。
*   描画ロジックを一箇所に集約する。
*   依存関係を明確にし、テスト容易性を向上させる (依存性注入の検討)。
*   設定管理のロジックを分離する。
*   主要メソッドの可読性を向上させる。

## リファクタリング項目と進捗

各項目は段階的に進めることを推奨します。

### 1. バックエンド: 状態管理の分離 ([ ] TODO / [ ] In Progress / [x] Done)

*   [x] `StateManager` クラスを作成する。
*   [x] `Monitor` クラス内の状態変数 (`person_detected`, `smartphone_in_use`, `alert_triggered_...`, `last_seen_time`, `last_phone_detection_time` など) を `StateManager` に移動する。
*   [x] 状態遷移のロジック (`handle_person_presence`, `handle_person_absence`、スマホ使用時間チェックなど) を `StateManager` に移動する。
*   [x] `Monitor` クラスの `run` メソッドから `StateManager` のメソッドを呼び出すように修正する。
*   [x] WebSocket で送信するステータス情報を `StateManager` から取得するように修正する (`broadcast_status` 周辺)。
*   [x] `StateManager` のユニットテストを作成・実行し、パスすることを確認。
*   [x] テスト実行時のインポートエラーを修正 (conftest.py, setup.py, ソース/テスト内の import 文修正)。
*   [ ] (推奨) `Monitor.run` のテストカバレッジを確認し、`StateManager` 呼び出し部分をカバーするテストを追加。

### 2. バックエンド: 検出ロジックの分離 ([ ] TODO / [ ] In Progress / [x] Done)

*   [x] `DetectionManager` クラス (または `DetectionService`) を作成する。
*   [x] `Monitor` クラス内の検出実行ロジック (`self.detector.detect_objects(frame)`) を `DetectionManager` に移動する。
*   [x] `Detector` クラスとの連携を `DetectionManager` が担当するようにする。
*   [x] `Monitor` クラスの `run` メソッドから `DetectionManager` の検出メソッドを呼び出し、結果を受け取るように修正する。
*   [x] 検出結果を `StateManager` に渡すように修正する。

### 3. バックエンド: 描画ロジックの集約 ([ ] TODO / [ ] In Progress / [x] Done)

*   [x] 検出結果 (バウンディングボックス、テキスト等) の描画ロジックを `Detector` クラスまたは新しい `DrawingUtils` クラスに完全に集約する。
    *   [x] `Monitor` 内の `draw_detection_overlay` メソッドを削除または移動する。
    *   [x] `Monitor` 内の `get_current_frame` メソッドは、描画済みのフレームを `Detector` (または `DrawingUtils`) から取得するように修正する。
*   [x] OpenCV ウィンドウ表示 (`camera.show_frame`) に渡すフレームも、集約された描画メソッドで生成したものを使用するようにする。

### 4. バックエンド: Alert/Notification の分離 ([ ] TODO / [ ] In Progress / [x] Done)

*   [x] `AlertManager` クラス (または `NotificationService`) を作成する。
*   [x] `StateManager` からの状態変化 (例: アラートトリガー状態になった) を `AlertManager` が受け取る仕組みを実装する (Observer パターンなど)。
*   [x] `AlertManager` が `AlertService` を呼び出して実際の通知を行うようにする。
*   [x] `Monitor` クラスから直接 `AlertService` を呼び出している箇所を削除する。

### 5. バックエンド: 依存性注入の導入 ([ ] TODO / [ ] In Progress / [x] Done)

*   [x] `Monitor` クラスの Singleton パターン (`get_instance`) を廃止する。
*   [x] `main.py` で `Camera`, `Detector`, `StateManager`, `DetectionManager`, `AlertManager`, `AlertService` などの主要コンポーネントをインスタンス化する。
*   [x] `Monitor` クラスのコンストラクタ (`__init__`) で、必要なコンポーネントを引数として受け取るように変更する。
*   [x] `api.py` など、`Monitor.get_instance()` を使用している箇所を修正し、Flask アプリケーションのコンテキスト等を通じて `Monitor` インスタンス (または必要なサブコンポーネント) を取得するように変更する (例: `current_app` や Flask-Injector の利用)。

### 6. バックエンド: 設定管理の分離 ([ ] TODO / [ ] In Progress / [x] Done)

*   [x] `ConfigManager` クラスを作成する。
*   [x] `config.yaml` の読み込み、デフォルト値の設定、バリデーションのロジックを `ConfigManager` に移動する。
*   [x] `Monitor` や他のクラスは、コンストラクタで `ConfigManager` のインスタンスを受け取り、必要な設定値を取得するように変更する。
*   [x] `api.py` での設定値取得/更新ロジックも `ConfigManager` を介するように変更する。

### 7. バックエンド: `run` メソッドの可読性向上 ([ ] TODO / [ ] In Progress / [x] Done)

*   [x] `Monitor` クラスの `run` メソッド内のメインループ処理を、意味のある単位でプライベートメソッド (`_process_frame`, `_update_status`, `_check_alerts` など) に分割する。

### 8. フロントエンド: (オプション) AR機能実装に向けた準備 ([x] TODO / [ ] In Progress / [ ] Done)

*   [ ] WebSocket通信でバックエンドからより詳細な検出情報（顔ランドマーク座標など）を受け取れるようにする。
*   [ ] (必要であれば) `MonitorView` で `<canvas>` を使用する準備をする。

### 9. 安定性向上のための対応 ([ ] TODO / [x] In Progress / [ ] Done)

*   [x] **MediaPipe の再有効化と安定化:**
    *   [x] クラッシュの原因となっていた `landmark_projection_calculator` の問題を調査し、適切な設定や対策を講じて MediaPipe (Pose, Hands) を再度有効化する準備を整えた。
    *   [x] MediaPipe 関連のエラーハンドリングをさらに強化した。
    *   [x] 設定ファイル（config.yaml）から MediaPipe の有効/無効を制御できるようにした。
    *   [x] **MediaPipeによるランドマークの描画の有効化：**
        * [x] 設定ファイル（`backend/src/config/config.yaml`）を編集し、以下の設定を変更する：
          ```yaml
          detector:
            use_mediapipe: true  # MediaPipeを有効化
          landmark_settings:
            pose:
              enabled: true      # Poseランドマークの描画を有効化
          ```
        * [x] 段階的な有効化方法：
          1. まず`detector.use_mediapipe: true`のみ設定して起動し、ログでMediaPipeが正常に初期化されることを確認
          2. 正常に初期化されれば、次に`landmark_settings.pose.enabled: true`も設定
          3. 問題が発生した場合は片方ずつ無効化して原因を特定
        * [x] 安定性確認方法：
          - アプリケーションを起動し、数分間実行してクラッシュしないことを確認
          - フレームレートの低下がないか確認
          - ブラウザでの映像表示に問題がないか確認
        * [x] 問題発生時の対応策：
          - ログを確認し、MediaPipeの初期化または描画に関するエラーメッセージを特定
          - `Detector`クラスの`draw_detections`メソッド内のエラーハンドリングが機能しているか確認
          - GPU使用が問題の場合は`os.environ["MEDIAPIPE_DISABLE_GPU"]`が正しく設定されているか確認
          - MediaPipeの検出感度（`min_detection_confidence`と`min_tracking_confidence`）を調整
*   [x] **OpenCV ウィンドウ表示の再有効化と安定化:**
    *   [x] `trace trap` エラーの原因となっていた可能性のある OpenCV のウィンドウ表示 (`cv2.imshow`, `cv2.namedWindow` など) を再度有効化する準備を整えた。
    *   [x] 設定ファイル（config.yaml）から OpenCV ウィンドウ表示の有効/無効を制御できるようにした。
    *   [x] エラーハンドリングを強化し、表示機能が失敗してもアプリケーション全体がクラッシュしないようにした。

### 10. MediaPipeランドマーク機能の強化（オプション）([x] Done)

*   [x] MediaPipeの追加機能の有効化:
    * [x] Hands（手）検出の有効化とUI表示
    * [x] Face（顔）検出の有効化とUI表示
*   [x] ランドマーク表示のカスタマイズ:
    * [x] 表示色やスタイルを設定ファイルから変更可能に
    * [x] 特定のランドマークのみ表示するフィルタリング機能
*   [ ] ランドマークデータの活用:
    * [ ] 姿勢評価機能（良い姿勢/悪い姿勢の判定）
    * [ ] 長時間の姿勢維持に対する警告機能
