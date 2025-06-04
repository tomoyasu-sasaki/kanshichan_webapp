# KanshiChan - バックエンドディレクトリ構造定義書

## 概要
本文書は、KanshiChan（監視ちゃん）プロジェクトのPython/Flaskバックエンドのディレクトリ構造と各ファイルの役割について詳述します。

**更新日**: 2024年12月  
**バージョン**: 2.0  
**対象**: backend/ ディレクトリ  

## 全体構成

```
backend/                          # バックエンドルートディレクトリ
├── src/                          # メインソースコード
├── tests/                        # テストコード
├── yolov8n.pt                    # YOLOv8モデルファイル (6.2MB)
└── __pycache__/                  # Python バイトコードキャッシュ
```

## 詳細構造

### 1. src/ - メインソースコード
```
src/
├── __init__.py                   # パッケージ初期化ファイル (0B)
├── main.py                       # アプリケーションエントリーポイント (4.5KB, 92行)
├── config/                       # 設定ファイル管理
├── core/                         # コア機能実装
├── services/                     # 外部サービス連携
├── web/                          # Web API と WebSocket
├── utils/                        # 共通ユーティリティ
├── sounds/                       # アラート音声ファイル
└── __pycache__/                  # Pythonバイトコードキャッシュ
```

### 2. config/ - 設定ファイル管理
**目的**: アプリケーション設定の一元管理

```
config/
├── __init__.py                   # パッケージ初期化 (36B, 2行)
├── config.yaml                   # メイン設定ファイル (2.5KB, 126行)
├── schedules.json                # スケジュール設定 (109B, 7行)
└── __pycache__/                  # Pythonバイトコードキャッシュ
```

**設定項目** (config.yaml):
- alert_sounds: アラート音声設定
- conditions: 不在・スマホ使用閾値設定
- detection_objects: 検出対象物体設定（スマートフォン、ノートPC、本）
- detector: AI検出エンジン設定（MediaPipe, YOLO使用フラグ）
- landmark_settings: ランドマーク描画設定（顔、手、姿勢）
- line: LINE Notify連携設定
- llm: LLM（大規模言語モデル）連携設定
- server: サーバー設定（ポート5001）
- optimization: パフォーマンス最適化設定
- memory: メモリ管理設定

### 3. core/ - コア機能実装
**目的**: AI検出、監視、状態管理のコア機能

```
core/
├── ai_optimizer.py               # AI処理最適化 (13KB, 343行)
├── camera.py                     # カメラ制御・フレーム取得 (9.4KB, 233行)
├── detection.py                  # 検出処理統合管理 (5.2KB, 108行)
├── detection_renderer.py         # 検出結果描画処理 (14KB, 361行)
├── detector.py                   # AI検出器（レガシー） (5.5KB, 168行)
├── frame_processor.py            # フレーム処理エンジン (7.6KB, 208行)
├── memory_manager.py             # メモリ管理強化 (14KB, 378行)
├── monitor.py                    # 監視機能メインロジック (8.8KB, 233行)
├── object_detector.py            # 統合物体検出器 (18KB, 428行)
├── schedule_checker.py           # スケジュールチェック (6.8KB, 177行)
├── state.py                      # 状態管理 (9.4KB, 169行)
├── status_broadcaster.py         # ステータス配信管理 (8.2KB, 191行)
├── threshold_manager.py          # 閾値管理システム (9.2KB, 240行)
└── __pycache__/                  # Pythonバイトコードキャッシュ
```

**主要モジュール**:
- **ai_optimizer.py**: フレームスキップ、バッチ処理による最適化
- **object_detector.py**: MediaPipe + YOLOv8の統合検出エンジン
- **memory_manager.py**: LRUキャッシュ、ガベージコレクション最適化
- **monitor.py**: 監視機能の中核制御
- **state.py**: 不在・スマホ使用状態の管理

### 4. services/ - 外部サービス連携
**目的**: アラート通知、スケジュール管理、外部API連携

```
services/
├── alert_manager.py              # アラート通知統合管理 (2.6KB, 61行)
├── alert_service.py              # アラート処理抽象化 (4.1KB, 96行)
├── line_service.py               # LINE Notify連携 (3.2KB, 84行)
├── llm_service.py                # LLM連携サービス (3.5KB, 93行)
├── schedule_manager.py           # スケジュール管理 (7.7KB, 195行)
├── sound_service.py              # 音声再生サービス (5.1KB, 116行)
└── __pycache__/                  # Pythonバイトコードキャッシュ
```

**サービス概要**:
- **alert_manager.py**: アラートの統合管理とルーティング
- **line_service.py**: LINE通知による離席時間延長機能
- **schedule_manager.py**: スケジュール登録・削除・チェック
- **sound_service.py**: アラート音声の再生管理

### 5. web/ - Web API と WebSocket
**目的**: Flask Webサーバー、REST API、WebSocket通信

```
web/
├── api.py                        # REST APIエンドポイント (12KB, 288行)
├── app.py                        # Flaskアプリケーション設定 (8.1KB, 169行)
├── handlers.py                   # ルートハンドラー (1.9KB, 52行)
├── websocket.py                  # WebSocket通信 (1.0KB, 35行)
└── __pycache__/                  # Pythonバイトコードキャッシュ
```

**Web API エンドポイント** (api.py):
- `GET/POST /settings`: 設定取得・更新
- `GET /video_feed`: 映像ストリーム
- `GET/POST /schedules`: スケジュール管理
- `DELETE /schedules/<id>`: スケジュール削除
- `GET /performance`: パフォーマンス統計

### 6. utils/ - 共通ユーティリティ
**目的**: 設定管理、ログ出力、例外処理の共通機能

```
utils/
├── __init__.py                   # パッケージ初期化 (0B)
├── config_manager.py             # 設定管理クラス (23KB, 630行)
├── exceptions.py                 # カスタム例外クラス群 (8.7KB, 400行)
├── logger.py                     # ログ設定 (893B, 28行)
├── yaml_utils.py                 # YAML操作ユーティリティ (2.6KB, 68行)
└── __pycache__/                  # Pythonバイトコードキャッシュ
```

**主要ユーティリティ**:
- **config_manager.py**: 設定ファイルの読み込み・検証・保存
- **exceptions.py**: 30+のカスタム例外クラス定義
- **logger.py**: 構造化ログ設定

### 7. sounds/ - アラート音声ファイル
**目的**: アラート通知用音声ファイルの格納

```
sounds/
├── __init__.py                   # パッケージ初期化 (0B)
├── alert.wav                     # 基本アラート音 (204KB)
├── alert_absence.wav             # 不在アラート音 (54KB)
├── alert_smartphone.wav          # スマホ使用アラート音 (834KB)
├── Copythat copy.wav             # コピー音声ファイル (204KB)
└── .DS_Store                     # macOS システムファイル (6KB)
```

### 8. tests/ - テストコード
**目的**: 単体テスト、統合テストの実装

```
tests/
├── __init__.py                   # パッケージ初期化 (30B, 4行)
├── conftest.py                   # pytest設定・フィクスチャ (1.3KB, 52行)
├── test_alert_system.py          # アラートシステムテスト (4.9KB, 110行)
├── test_flask_server.py          # Flaskサーバーテスト (2.2KB, 57行)
├── test_line_integration.py      # LINE連携テスト (2.2KB, 54行)
├── test_llm_service.py           # LLMサービステスト (2.4KB, 66行)
├── test_monitor.py               # 監視機能テスト (14KB, 321行)
├── test_schedule_manager.py      # スケジュール管理テスト (7.6KB, 176行)
├── test_state_manager.py         # 状態管理テスト (13KB, 251行)
├── test_threshold_management.py  # 閾値管理テスト (9.1KB, 203行)
├── backend/                      # テスト用バックエンドファイル
└── __pycache__/                  # Pythonバイトコードキャッシュ
```

**テストカバレッジ**: 79.13%

## ファイルサイズと行数統計

### 総計
- **総ファイル数**: 32ファイル（テスト含む）
- **総コード行数**: 約4,500行
- **平均ファイルサイズ**: 7.2KB

### モジュール別統計
| モジュール | ファイル数 | 総行数 | 平均行数 |
|------------|------------|--------|-----------|
| core/ | 13 | 2,879 | 221 |
| tests/ | 10 | 1,290 | 129 |
| utils/ | 5 | 1,126 | 225 |
| services/ | 6 | 645 | 108 |
| web/ | 4 | 544 | 136 |
| config/ | 3 | 135 | 45 |

## アーキテクチャ特徴

### 1. レイヤード・アーキテクチャ
- **プレゼンテーション層**: web/ (Flask API, WebSocket)
- **ビジネスロジック層**: core/ (AI検出, 監視制御)
- **サービス層**: services/ (外部連携, 通知)
- **インフラストラクチャ層**: utils/ (設定, ログ, 例外)

### 2. 依存性注入パターン
- ConfigManagerを中心とした設定管理
- 各モジュールへの統一された設定注入

### 3. 例外処理戦略
- 30+のカスタム例外クラス
- 階層化されたエラーハンドリング
- 詳細なエラーレポート機能

### 4. パフォーマンス最適化
- AI処理の最適化（ai_optimizer.py）
- メモリ管理強化（memory_manager.py）
- 非同期処理とキャッシュ戦略

## 規約遵守状況

### コーディング規約
- ✅ PEP 8 + Black formatting準拠
- ✅ Google style docstring
- ✅ 型ヒント（Type Hints）の活用
- ✅ isortによるimport整理

### ネーミング規約
- ✅ ファイル名: snake_case.py
- ✅ クラス名: PascalCase
- ✅ 関数名: snake_case
- ✅ 定数: UPPER_SNAKE_CASE

### ディレクトリ構造規約
- ✅ 機能別ディレクトリ分割
- ✅ パッケージ化（__init__.py）
- ✅ テストディレクトリの分離

## 拡張性・保守性

### 拡張ポイント
1. **AI検出エンジン**: 新しい検出モデルの追加
2. **通知サービス**: 新しいアラート手段の追加
3. **API機能**: 新しいエンドポイントの追加
4. **設定項目**: 新しい設定カテゴリの追加

### 保守性の特徴
- モジュール間の疎結合
- 設定の外部化
- 包括的なテストカバレッジ
- 詳細なログ出力

---

**注記**: 本文書は [backend_rules.yaml](../project_rules/backend_rules.yaml) の規約に準拠しています。 