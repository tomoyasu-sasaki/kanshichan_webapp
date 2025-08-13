## KanshiChan 設定のSQLite移行手順書（進捗管理）

目的: `backend/src/config/config.yaml` の設定値を `backend/instance/config.db` に移行し、バックエンドはDBから設定を取得、フロントは新API経由で表示・更新できるようにする。DB管理に適した正規化を行い、YAML表現への準拠ではなくドメインモデルに沿ったスキーマとする。

進行ルール:
- 各セクションのTaskは最大10件。必ず次の3固定Taskを含める: 「動作確認」「テスト実行」「実装漏れチェック」。
- チェックボックスは進捗管理用（[ ] 未着手 / [x] 完了）。

---

### Phase 1: 分析・計画

#### Section 1.1: 対象範囲と影響調査
- [ ] 既存設定の読込経路を洗い出し（`ConfigManager.load/get/save`、利用箇所）
- [ ] 設定参照の主要箇所を把握（`web/app.py` 初期化、`services/*`、`core/*` 等）
- [ ] API/フロントの設定取得・表示箇所の洗い出し（`SettingsPanel.tsx` ほか）
- [ ] 書込頻度/同時実行の見積り（SQLite並行性影響の整理）
- [ ] 既存バックアップ/復元フローとの整合（Storage/バックアップに追加する範囲）
- [ ] 動作確認
- [ ] テスト実行
- [ ] 実装漏れチェック

結果メモ（Context7/コード調査）
- 既存読込経路:
  - `backend/src/utils/config_manager.py` が単一の設定窓口。`load_yaml()` で `backend/src/config/config.yaml` を読み込み、`_apply_env_overrides()` にて `KANSHICHAN_` プレフィックスの環境変数で上書き（例: `KANSHICHAN_SERVER_PORT` → `server.port`）。`save_yaml()` でYAML保存。
  - 代表的呼び出し: `config_manager.get('server.port', 8000)`（`backend/src/main.py` 起動ポート）、`get_all()`（`web/app.py`、分析系で利用）。
- 主要参照箇所（抜粋）:
  - サーバ/最適化: `server.port`（`main.py`）、`optimization.*`（`core/status_broadcaster.py`, `core/ai_optimizer.py`）
  - 検出/描画: `detector.*`, `detection_smoother.*`, `display.show_opencv_window`, `models.yolo.*`（`core/object_detector.py`, `core/detection_smoother.py`, `core/detection_renderer.py`）
  - TTS/音声: `tts.*`, `voice_manager.*`（`web/routes/tts_system_routes.py` ほか）
- 設定更新（書込）箇所:
  - `backend/src/web/tts_system_routes.py` の保存処理（多くの `tts.*` キーに対する `config_manager.set()` → `config_manager.save()`）。
  - `backend/src/web/api.py` の更新後保存（`config_updated` → `config_manager.save()`）。
  - `backend/src/core/threshold_manager.py`（離席閾値更新後 `save()`）。
  - いずれもユーザー操作トリガーで低頻度。DB側の同時書き込み衝突リスクは小。
- フロント/API:
  - `frontend/src/components/settings/SettingsPanel.tsx` は `GET/POST /api/v1/settings` を呼ぶが、現状バックエンドの該当ルートは未実装（要追加）。
- バックアップ/復元:
  - 既存 `StorageService` はアプリDB（行動/分析）JSONバックアップ/復元を実装。設定は対象外。`config.db` 追加後は設定バックアップ（ダンプ/リストア）手順の拡充が必要。
- 環境変数上書き:
  - `KANSHICHAN_` プレフィックス（例: `KANSHICHAN_ENABLE_TTS`、`KANSHICHAN_LOG_JSON`）。DB化後も「読込→環境変数上書き」の順序を維持すること。
- 同時実行/トランザクション:
  - SQLiteはDB単位で同時書込1。`config.db` は低頻度更新のため影響軽微。Flask‑SQLAlchemyの複数バインドで `kanshichan.db` と独立に運用可能（Context7: Flask‑SQLAlchemy binds, SQLite concurrency）。

#### Section 1.2: データモデル設計方針
- [ ] 正規化レベルと方針の決定（ドメイン別テーブル + 型付きKV最小限）
- [ ] 型付けルール（int/float/bool/text/json）とバリデーション方針
- [ ] 参照整合性（PK/FK/一意制約）
- [ ] 変更容易性（将来のキー追加に備えた拡張余地）
- [ ] マイグレーション方式（初回のみcreate_all、以後は手動管理）
- [ ] 動作確認
- [ ] テスト実行
- [ ] 実装漏れチェック

結果メモ（提案）
- 正規化方針:
  - 大項目は単一行テーブル（`id=1`）で型付き列を用意（例: `general_settings`, `logging_settings`, `detector_settings`, `tts_settings` 等）。
  - 可変集合は行ベース（`detection_objects`、`landmark_settings(key in face/hands/pose)`）。色は `color_r/g/b` に分解。
  - 将来の自由形式は型付きKV補助テーブル追加で拡張（今回は不要）。
- 型付け/バリデーション:
  - `INTEGER`（boolは0/1）、`REAL`、`TEXT` を基本。既存 `ConfigManager.add_validation_rule` を継承し、DB読み出し時に検証/型補正。
- 参照整合/制約:
  - 各カテゴリは `id=1` の一意行。`detection_objects.key` はPK、`landmark_settings.key` はCHECK制約（face/hands/pose）。
- 変更容易性:
  - 列追加は後方互換で対応。列の存在確認→デフォルト適用の移行スクリプトを別途用意可能。
- マイグレーション方式:
  - Flask‑SQLAlchemyの複数バインド（`SQLALCHEMY_BINDS['config']`）+ モデル `__bind_key__='config'`。初回 `db.create_all()` で作成、以後は明示的DDL/スクリプト管理（Alembic未導入のため）。
  - 読み出しはストア層（SQLiteStore）で正規化テーブル→ネスト辞書へ組み立て、`get_all()` 互換を維持。環境変数上書きは現行と同順序で適用。

---

### Phase 2: スキーマ設計・DB作成

#### Section 2.1: スキーマ定義（案）
SQL（DDLイメージ）とエンティティ例。最終版は実装時に型・制約をプロジェクト規約に合わせ微調整。

```sql
-- SQLite (config.db)
CREATE TABLE IF NOT EXISTS general_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  server_port INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS logging_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  enable_file_output INTEGER NOT NULL,
  file_level TEXT NOT NULL,
  console_level TEXT NOT NULL,
  level TEXT NOT NULL,
  log_dir TEXT NOT NULL,
  max_file_size_mb INTEGER,
  backup_count INTEGER,
  suppress_frequent_logs INTEGER,
  frame_log_interval INTEGER,
  detection_log_sampling INTEGER
);

CREATE TABLE IF NOT EXISTS models_yolo (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  model_name TEXT NOT NULL,
  models_dir TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS detector_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  use_mediapipe INTEGER NOT NULL,
  use_yolo INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS detection_smoother_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  enabled INTEGER NOT NULL,
  hysteresis_enabled INTEGER,
  hysteresis_high REAL,
  hysteresis_low REAL,
  interpolation_enabled INTEGER,
  interpolation_fade_out REAL,
  interpolation_max_missing INTEGER,
  moving_avg_enabled INTEGER,
  moving_avg_window INTEGER,
  moving_avg_weight_recent REAL
);

CREATE TABLE IF NOT EXISTS detection_objects (
  key TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  class_name TEXT NOT NULL,
  alert_message TEXT,
  alert_sound TEXT,
  alert_threshold REAL,
  confidence_threshold REAL,
  enabled INTEGER NOT NULL,
  thickness INTEGER,
  color_r INTEGER,
  color_g INTEGER,
  color_b INTEGER
);

CREATE TABLE IF NOT EXISTS landmark_settings (
  key TEXT PRIMARY KEY CHECK (key IN ('face','hands','pose')),
  name TEXT,
  enabled INTEGER,
  thickness INTEGER,
  color_r INTEGER,
  color_g INTEGER,
  color_b INTEGER
);

CREATE TABLE IF NOT EXISTS tts_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  cache_dir TEXT,
  cache_ttl_hours INTEGER,
  enable_audio_cache INTEGER,
  enable_voice_cloning INTEGER,
  enable_mps INTEGER,
  mps_half_precision INTEGER,
  mps_memory_fraction REAL,
  gpu_memory_optimization INTEGER,
  default_language TEXT,
  default_voice_mode TEXT,
  default_voice_sample_id TEXT,
  default_voice_sample_path TEXT,
  default_audio_quality REAL,
  default_voice_pitch REAL,
  default_voice_speed REAL,
  default_voice_volume REAL,
  default_vq_score REAL,
  default_cfg_scale REAL,
  default_min_p REAL,
  default_max_frequency INTEGER,
  default_use_seed INTEGER,
  default_seed INTEGER,
  default_fast_mode INTEGER,
  default_use_breath_style INTEGER,
  default_use_noise_reduction INTEGER,
  default_use_streaming_playback INTEGER,
  default_use_whisper_style INTEGER,
  default_emotion TEXT,
  emotion_anger REAL,
  emotion_disgust REAL,
  emotion_fear REAL,
  emotion_happiness REAL,
  emotion_neutral REAL,
  emotion_other REAL,
  emotion_sadness REAL,
  emotion_surprise REAL,
  model TEXT,
  verbose_logging INTEGER,
  debug_mps INTEGER,
  suppress_warnings INTEGER,
  use_hybrid INTEGER,
  max_worker_threads INTEGER,
  max_cache_size_mb INTEGER,
  max_generation_length INTEGER
);

CREATE TABLE IF NOT EXISTS voice_manager_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  base_dir TEXT,
  auto_cleanup_hours INTEGER,
  enable_compression INTEGER,
  compression_quality REAL,
  max_cache_size_mb INTEGER
);

CREATE TABLE IF NOT EXISTS memory_cache_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  threshold_percent REAL,
  gc_interval_seconds REAL,
  monitor_interval_seconds REAL,
  cache_max_memory_mb REAL,
  cache_max_size INTEGER
);

CREATE TABLE IF NOT EXISTS optimization_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  target_fps REAL,
  min_fps REAL,
  max_skip_rate INTEGER,
  fps_smoothing_enabled INTEGER,
  fps_window_size INTEGER,
  frame_skipper_enabled INTEGER,
  frame_skipper_adaptive INTEGER,
  frame_skipper_adjust_interval REAL,
  batch_enabled INTEGER,
  batch_size INTEGER,
  batch_timeout_ms INTEGER,
  preprocess_resize_enabled INTEGER,
  preprocess_resize_width INTEGER,
  preprocess_resize_height INTEGER,
  preprocess_normalize_enabled INTEGER,
  preprocess_roi_enabled INTEGER
);
```

- [x] 実体/カラム最終決定（YAMLキーからの完全マッピング）
- [x] インデックス/一意制約の付与方針の決定
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

#### Section 2.2: DBファイル作成とアプリ設定
- [x] `backend/instance/config.db` を新規作成（存在しなければ）
- [x] Flask設定にバインド追加（`app.config['SQLALCHEMY_BINDS']['config'] = sqlite:////.../config.db`）
- [x] `models` に設定系モデルを実装（`__bind_key__='config'`）
- [x] `models/__init__.py` に設定系モデルをインポートし `db.create_all()` で作成
- [x] `web/app.py` でBINDS設定/初期化のログ出力
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

---

### Phase 3: データ移行（config.yaml → config.db）

#### Section 3.1: 変換ロジック実装
- [x] YAML読込→正規化テーブルへのマッピング変換関数を実装
- [x] 既存値クリア/Upsert 戦略（設定ID=1の単一行テーブル群）
- [x] 型変換とデフォルト値の適用（バリデーション）
- [x] 変換スクリプト（ワンショット/再実行可）とログ整備
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

#### Section 3.2: 初期データ投入と検証
- [x] スクリプト実行で `config.db` に投入
- [x] テーブル別レコード件数・主要キーの一致検証
- [x] 差分レポート（YAML vs DB）生成（重要キーのみ）
- [x] バックアップ取得（YAML原本・DBコピー）
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

---

### Phase 4: バックエンド切替

#### Section 4.1: ConfigManager のストア抽象化
- [x] `ConfigManager` にストア層（YAMLStore / SQLiteStore）を追加
- [x] `load()/get()/save()` の実体を SQLiteStore に切替（フラグでYAMLへフォールバック可）
- [x] バリデーション/既存ルール再利用（`add_validation_rule`）
- [x] 変更影響の最小化（呼出し側のAPI不変）
- [x] 環境変数オーバーライドの適用順序維持
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

#### Section 4.2: 設定APIの追加/更新
- [x] 読取API新設（例: `GET /api/v1/settings`）
- [x] 更新API検討（必要なら PATCH/PUT 単位キー更新）
- [x] `web/app.py` へのBlueprint登録
- [x] エラーレスポンス/スキーマ定義
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

---

### Phase 5: フロントエンド対応

#### Section 5.1: 取得先切替とUI
- [x] `SettingsPanel.tsx` 等の取得先を新APIへ切替
- [x] 型（`frontend/src/types/*`）更新とバリデーション
- [x] 表示文言/i18n反映（`i18n/locales/*.json`）
- [x] 大項目/詳細項目の表示ロジック見直し（正規化後の項目構成に対応）
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

#### Section 5.2: 変更系UI（任意）
- [x] 将来的な設定編集UIの下準備（フォームレイアウト/バリデーション方針）
- [x] 差分プレビュー/保存確認ダイアログの設計
- [x] 設定の部分更新API連携（必要に応じて）
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

---

### Phase 6: テスト・品質保証

#### Section 6.1: バックエンドテスト
- [x] SQLiteStore単体テスト（読取/書込/バリデーション）
- [x] 設定APIの統合テスト（200/400/404 等）
- [x] 競合/同時実行の軽負荷テスト（設定更新が他処理に影響しないこと）
- [x] 既存機能の回帰確認（DBバインド追加の副作用無）
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

#### Section 6.2: フロントテスト
- [x] 画面表示の回帰・スナップショット（型チェック・ビルド確認で代替）
- [x] APIモックでのフロー確認（ローディング/エラー）
- [x] E2E（設定閲覧の主要パス）（最小サーバでのGET/POST確認）
- [x] 動作確認
- [x] テスト実行
- [x] 実装漏れチェック

---

### Phase 7: リリース準備・ロールバック

#### Section 7.1: リリース手順
- [ ] 事前チェック（DB作成/初期データ投入/API疎通）
- [ ] 環境変数・構成（BINDS・パス）確認
- [ ] デプロイ順序とリードオンリー時間の最小化
- [ ] ロールバック手順（YAMLStoreへ戻す手順・切替フラグ）
- [ ] 動作確認
- [ ] テスト実行
- [ ] 実装漏れチェック

---

### Phase 8: 運用・改善

#### Section 8.1: 運用監視と最適化
- [ ] WALモード/チェックポイント運用の検討（必要時）
- [ ] VACUUM/REINDEXスケジュール（DBサイズ管理）
- [ ] インデックス/クエリ見直し（ボトルネック時）
- [ ] バックアップ/復元の手順書更新
- [ ] 動作確認
- [ ] テスト実行
- [ ] 実装漏れチェック

---

### 付録A: YAML→DB マッピング案（抜粋）

- `server.port` → `general_settings.server_port`
- `logging.*` → `logging_settings.*`
- `models.yolo.*` → `models_yolo.*`
- `detector.*` → `detector_settings.*`
- `detection_smoother.*` → `detection_smoother_settings.*`
- `detection_objects.{key}.*` → `detection_objects`（key=スマホ等, colorをr/g/bに分割）
- `landmark_settings.{face|hands|pose}.*` → `landmark_settings`（key列）
- `tts.*` → `tts_settings`（emotion_* は列分割、既定の多数フラグ/数値も列化）
- `voice_manager.*` → `voice_manager_settings.*`
- `memory.*` → `memory_cache_settings.*`
- `optimization.*` → `optimization_settings.*`

備考: 上記以外の新規キーは将来行追加/列追加で拡張。頻繁に変動する自由形式は型付きKVテーブル追加で吸収可。

### 付録B: バックエンド変更ポイント（目安）

- `backend/src/web/app.py`:
  - `SQLALCHEMY_BINDS['config'] = 'sqlite:////.../config.db'` を追加
  - 初期化ログ出力
- `backend/src/models/`:
  - 設定系モデル群（`__bind_key__ = 'config'`）を作成
  - `__init__.py` でインポートし `db.create_all()`
- `backend/src/utils/config_manager.py`:
  - SQLiteStore 実装・切替ロジック
- `backend/src/web/routes/`:
  - `settings` APIの追加/登録

### 付録C: リスクと緩和

- SQLite同時書込制限: 設定更新は低頻度想定のため実影響小。必要なら更新APIを直列化。
- スキーマ変更: 初回は `create_all` で対応。将来的な変更は手順書化（新列追加→移行→コード切替）。
- フロント既存表示ズレ: 型の差異を型定義・整形層で吸収。


