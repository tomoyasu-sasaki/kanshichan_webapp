# KanshiChan 機能追加・改善計画

このドキュメントは、KanshiChan プロジェクトの機能追加と改善計画、およびその進捗を管理します。

## 機能: スケジュール通知機能

**目的:** 設定された時刻に指定された作業内容を通知（アラート音再生と画面表示）することで、ユーザーのタスク実行を支援する。

**概要:**
*   フロントエンドの「スケジュール」タブで、通知したい時刻（HH:MM）と作業内容を設定できる。
*   設定されたスケジュールはバックエンドで管理・保存される。
*   バックエンドは定期的に現在時刻とスケジュールを比較し、一致した場合にアラート音を鳴らし、WebSocket経由でフロントエンドに通知する。
*   フロントエンドは通知を受け取り、画面に作業内容を表示する。

---

## 実装項目と進捗

### フェーズ 1: 基本機能の実装

#### 1. フロントエンド: UI基礎 ([ ] TODO / [ ] In Progress / [x] Done)
*   [x] **`frontend/src/App.tsx`**:
    *   [x] Chakra UI `Tabs` に「スケジュール」タブを追加する。
    *   [x] 新しいコンポーネント `ScheduleView.tsx` を作成し、スケジュールタブの `TabPanel` 内に配置する。
*   [x] **`frontend/src/components/ScheduleView.tsx` (新規作成)**:
    *   [x] コンポーネントの基本的な枠組みを作成する (`React.FC`)。
    *   [x] Chakra UI コンポーネント (`Box`, `Heading`, `VStack` など) をインポートする。
    *   [x] 本日の日付 (`YYYY/MM/DD` 形式) を取得し、 `Heading` で `"${本日のYYYY/MM/DD}スケジュール"` と表示するロジックを実装する (`useEffect`, `useState` を使用)。
    *   [x] スケジュール設定フォームのエリアと、スケジュール一覧表示のエリアを `VStack` などでレイアウトする。

#### 2. バックエンド: APIエンドポイント ([ ] TODO / [ ] In Progress / [x] Done)
*   [x] **`backend/src/services/schedule_manager.py` (新規作成)**:
    *   [x] `ScheduleManager` クラスを作成する。
    *   [x] スケジュールデータ構造を定義する (例: `List[Dict[str, str]]`、各辞書は `{'id': 'uuid', 'time': 'HH:MM', 'content': '作業内容'}`)。
    *   [x] スケジュールデータを保存/読み込みするためのファイルパスを定義する (例: `config/schedules.json`)。
    *   [x] ファイルが存在しない場合に初期化する処理を追加する。
    *   [x] `load_schedules()`: JSONファイルからスケジュールを読み込むメソッドを実装する。
    *   [x] `save_schedules()`: 現在のスケジュールリストをJSONファイルに書き込むメソッドを実装する。
    *   [x] `get_schedules()`: スケジュール一覧を返すメソッドを実装する。
    *   [x] `add_schedule(time: str, content: str)`: 新しいスケジュールを追加し、IDを付与して保存するメソッドを実装する (`uuid` を使用)。
    *   [x] `delete_schedule(schedule_id: str)`: 指定されたIDのスケジュールを削除して保存するメソッドを実装する。
*   [x] **`backend/src/web/api.py` (または関連ファイル)**:
    *   [x] `ScheduleManager` のインスタンスを作成する (依存性注入を考慮)。
    *   [x] APIエンドポイント `/api/schedules` を作成する:
        *   [x] `GET`: `schedule_manager.get_schedules()` を呼び出し、スケジュール一覧をJSONで返す。
        *   [x] `POST`: リクエストボディ (`{ time: "HH:MM", content: "作業内容" }`) を受け取り、`schedule_manager.add_schedule()` を呼び出して新しいスケジュールを追加する。成功ステータス (例: 201 Created) と追加されたスケジュール情報を返す。
        *   [x] `DELETE /api/schedules/<schedule_id>`: URLパスから `schedule_id` を受け取り、`schedule_manager.delete_schedule()` を呼び出してスケジュールを削除する。成功ステータス (例: 204 No Content) を返す。
    *   [x] エラーハンドリングを追加する (バリデーションエラー、ファイルI/Oエラーなど)。
*   [x] **`backend/src/main.py` (または依存性注入設定箇所)**:
    *   [x] `ScheduleManager` のインスタンスを生成し、Flaskアプリや `Monitor` に適切に渡すように設定する。

#### 3. フロントエンド: API連携 (フォームと一覧) ([ ] TODO / [ ] In Progress / [x] Done)
*   [x] **`frontend/src/components/ScheduleView.tsx`**:
    *   [x] 時刻入力 (`Input type="time"`) と内容入力 (`Input type="text"`)、追加ボタン (`Button`) を含むフォームを作成する。
    *   [x] フォームの入力値を管理するための `useState` を追加する。
    *   [x] 「追加」ボタンのクリックハンドラを実装する:
        *   [x] 入力値を取得し、バリデーションを行う (空でないかなど)。
        *   [x] `POST /api/schedules` を呼び出してバックエンドにデータを送信する (`fetch` or `axios`)。
        *   [x] 成功したら、フォームをクリアし、スケジュール一覧を再取得または更新する。
        *   [x] エラーハンドリング (APIエラー表示など) を実装する。
    *   [x] スケジュール一覧表示エリアを実装する:
        *   [x] コンポーネントのマウント時 (`useEffect`) に `GET /api/schedules` を呼び出してスケジュール一覧を取得し、`useState` で管理する。
        *   [x] 取得したスケジュールデータをリスト形式 (`List`, `ListItem` or `Table`) で表示する。各項目には時刻、内容、削除ボタンを表示する。
    *   [x] 「削除」ボタンのクリックハンドラを実装する:
        *   [x] 該当するスケジュールのIDを取得する。
        *   [x] `DELETE /api/schedules/<schedule_id>` を呼び出す。
        *   [x] 成功したら、スケジュール一覧を再取得または更新する。
        *   [x] エラーハンドリングを実装する。

#### 4. バックエンド: スケジュール実行ロジック ([ ] TODO / [ ] In Progress / [x] Done)
*   [x] **依存ライブラリの追加 (必要な場合)**:
    *   [x] スケジューリングに既存の仕組みを活用（Monitor クラス内の定期チェック）
*   [x] **`backend/src/monitor.py` (またはスケジューリング担当箇所)**:
    *   [x] `ScheduleManager` と `AlertService` (または通知担当サービス) のインスタンスを取得する (コンストラクタ経由など)。
    *   [x] WebSocket 送信用の関数またはメソッドを取得/参照できるようにする。
    *   [x] スケジュールチェック関数 `_check_schedules()` を実装する:
        *   [x] 現在の時刻 (`HH:MM` 形式) を取得する。
        *   [x] `schedule_manager.get_schedules()` でスケジュール一覧を取得する。
        *   [x] 取得したスケジュールの中から、現在の時刻と一致するものを見つける。
        *   [x] 一致したスケジュールが見つかった場合:
            *   [x] `alert_service.play_alert()` (または同等のメソッド) を呼び出して固定アラート音を再生する。
            *   [x] WebSocket を通じてフロントエンドに通知を送信する (例: `{'type': 'schedule_alert', 'content': schedule['content']}`)。
            *   [x] 同じスケジュールが複数回実行されないようにセット管理を実装。
    *   [x] 定期実行の仕組みをセットアップする:
        *   [x] `Monitor` クラスの `run` メソッド内のループで、`_check_schedules()` を呼び出す。実行間隔を制御。

#### 5. フロントエンド: 通知受信と表示 ([ ] TODO / [ ] In Progress / [x] Done)
*   [x] **`frontend/src/utils/websocket.ts` (WebSocket接続管理)**:
    *   [x] WebSocketマネージャークラスを作成し、単一のWebSocket接続を管理。
    *   [x] 各種イベント（接続、切断、エラー、ステータス更新、スケジュールアラート）のリスナー登録メソッドを実装。
    *   [x] シングルトンパターンを採用し、アプリケーション全体で一貫したWebSocket接続を提供。
*   [x] **`frontend/src/components/ScheduleView.tsx` (通知表示担当コンポーネント)**:
    *   [x] WebSocketマネージャーを初期化し、スケジュール通知イベントのリスナーをセットアップ。
    *   [x] 通知を受け取ったら、Chakra UI の `useToast` を使って画面上部に作業内容を表示。
    *   [x] コンポーネントのアンマウント時にリスナーを適切に解除。

### フェーズ 2: 改善とテスト (オプション)

*   [x] **バックエンド:**
    *   [x] `ScheduleManager` のユニットテストを作成する。
    *   [x] スケジュール実行ロジックのテストを追加する (モックを使用)。
    *   [ ] APIエンドポイントのテストを作成する。
    *   [ ] より堅牢なエラーハンドリングとロギングを追加する。
*   [x] **フロントエンド:**
    *   [x] `ScheduleView` コンポーネントのテストを作成する (React Testing Library)。
    *   [ ] UI/UXの改善（日付フォーマット、フォームバリデーションの強化など）。
    *   [ ] ローディング状態やエラーステートの表示を改善する。

---

## 注意事項

*   既存の `AlertService` および WebSocket 通信の仕組みを最大限活用する。
*   APIの設計やデータ構造は、実装を進める中で必要に応じて調整する。
*   エラーハンドリングとユーザーへのフィードバックを丁寧に行う。
*   設定ファイルのパスや形式は環境に合わせて確認・調整する。
