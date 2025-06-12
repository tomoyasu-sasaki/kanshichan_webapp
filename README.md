## 補足
- **High**: サービス停止や致命的バグにつながる恐れがあるもの。最優先で対応。  
- **Medium**: 保守性・拡張性向上に寄与。High 完了後に着手。  
- **Low**: 品質向上や自動化など。上位タスク後に順次対応。  
- 進捗列のチェックボックス (☐ → ✅) を更新しながら管理してください。
# 📡 監視ちゃん (KanshiChan) - AIベースの作業集中支援ツール

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test Coverage](https://img.shields.io/badge/coverage-79.13%25-green.svg)](https://github.com/tomoyasu-sasaki/KanshiChan)

<div align="center">

[🏠 ホーム](https://github.com/tomoyasu-sasaki/KanshiChan) |
[📖 Wiki](https://github.com/tomoyasu-sasaki/KanshiChan/wiki) |
[🐛 Issue](https://github.com/tomoyasu-sasaki/KanshiChan/issues) |
[📝 プルリクエスト](https://github.com/tomoyasu-sasaki/KanshiChan/pulls)

</div>

## 📋 目次
1. [🎯 概要](#-概要)
2. [🎬 デモ](#-デモ)
3. [🚀 クイックスタート](#-クイックスタート)
4. [💡 機能と技術スタック](#-機能と技術スタック)
5. [📁 プロジェクト構成](#-プロジェクト構成)
6. [⚙️ 設定とカスタマイズ](#️-設定とカスタマイズ)
7. [🌍 国際化対応](#-国際化対応)
8. [📊 パフォーマンス最適化](#-パフォーマンス最適化)
9. [👥 開発ガイド](#-開発ガイド)
10. [❓ トラブルシューティング](#-トラブルシューティング)
11. [📜 ライセンス](#-ライセンス)

## 🎯 概要
「監視ちゃん」は、**最新のAI技術とリアルタイム処理**を組み合わせた高性能な作業集中支援ツールです。カメラを使ってユーザーの作業状態をリアルタイム監視し、適切なフィードバックを提供することで、作業効率の向上をサポートします。

### 🌟 **v2.0の主要アップデート**
- 🚀 **パフォーマンス最適化**: AI処理の最適化により15+ FPS の安定した動作を実現
- 💾 **メモリ管理強化**: インテリジェントなキャッシュとガベージコレクション最適化
- 🌍 **国際化対応**: 日本語・英語の動的言語切り替えに対応
- 🧪 **高品質テスト**: 79.13%のテストカバレッジで安定性を確保
- 🏗️ **堅牢なアーキテクチャ**: 30+の専門例外クラスによる詳細なエラーハンドリング

> 💪 **主な特徴**
> - **リアルタイムAI分析**: MediaPipe + YOLOv8による高精度な姿勢・物体検出
> - **インテリジェントアラート**: カスタマイズ可能なスマート通知システム  
> - **直感的なUI**: Chakra UIベースのモダンなWebインターフェース
> - **高性能処理**: フレームスキップとバッチ処理による最適化
> - **多言語対応**: 日本語・英語のシームレスな切り替え

## 🎬 デモ
### 💻 監視画面（リアルタイムパフォーマンス表示付き）
リアルタイムの姿勢検出、行動分析、パフォーマンス統計を表示
[![監視画面デモ](docs/images/monitor.png)](https://youtu.be/your-demo-video)
> 👆 画像をクリックすると動画デモをご覧いただけます

### ⚙️ 設定画面（国際化対応）
検出感度、アラート設定、言語選択をカスタマイズ可能
![設定画面](docs/images/settings.png)

### 📊 パフォーマンス統計
AI処理効率、メモリ使用量、FPSをリアルタイム監視
![パフォーマンス統計](docs/images/performance.png)

### ⚠️ アラート例
不適切な姿勢や長時間のスマートフォン使用を検知した際の警告表示
![アラート例](docs/images/alert.gif)

## 🚀 クイックスタート

### 📋 必要条件
- **Python**: 3.9以上
- **Node.js**: 16以上
- **カメラ**: USBカメラまたは内蔵カメラ
- **メモリ**: 4GB以上推奨（AI処理のため）
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### 🔧 インストール
```bash
# 1. リポジトリのクローン
git clone https://github.com/yourusername/KanshiChan.git
cd KanshiChan

# 2. バックエンドのセットアップ
cd backend
python -m venv venv
source venv/bin/activate  # Windows: `venv\Scripts\activate.bat`
pip install -r ../requirements.txt  # 最適化された依存関係のインストール
python -m backend.src.main  # サーバー起動

# 3. フロントエンドのセットアップ（新しいターミナルで実行）
cd frontend
npm install  # 国際化ライブラリを含む依存パッケージのインストール
npm run dev  # 開発サーバー起動（http://localhost:5173）
```

### 🌐 アクセス
ブラウザで `http://localhost:5173` にアクセスして監視ちゃんを開始！

> 💡 **初回起動時の注意点**
> - YOLOv8モデル（約100MB）が自動的にダウンロードされます
> - AI最適化機能により、初期化後は15+ FPSの安定した動作を実現
> - ブラウザでカメラアクセスを許可し、言語設定（日/英）を選択してください

## 💡 機能と技術スタック

### 🎯 主要機能
#### 👀 **高性能リアルタイム監視**
- **MediaPipe統合**: Pose, Hands, Faceのランドマーク検出（設定でON/OFF可能）
- **YOLOv8物体検出**: スマートフォン、ノートPC等の高精度検知
- **AI処理最適化**: フレームスキップとバッチ処理による最適化
- **パフォーマンス監視**: リアルタイムFPS・メモリ使用量表示

#### ⏰ **インテリジェントアラートシステム**
- **適応的通知**: 不適切な姿勢の検知と段階的警告
- **使用時間管理**: 長時間のスマートフォン使用検知とアラート
- **カスタマイズ可能設定**: 閾値、音声、メッセージの個別調整
- **LINE連携**: LINE通知による離席時間延長機能

#### 🎛️ **モダンなWebUI**
- **リアルタイムフィードバック**: 低遅延でのステータス表示
- **多言語対応**: 日本語・英語の動的切り替え
- **レスポンシブデザイン**: PC・タブレット対応
- **アクセシビリティ**: キーボード操作とスクリーンリーダー対応

#### 🚀 **パフォーマンス最適化機能**
- **メモリ管理**: LRUキャッシュと自動ガベージコレクション
- **プロセス最適化**: マルチスレッド処理と非同期I/O
- **リソース監視**: CPUとメモリ使用量の継続監視

### 🛠️ 技術スタック
#### バックエンド
| 技術 | バージョン | 役割 | 最適化 |
|------|------------|------|--------|
| **Python** | 3.9+ | コアロジック実装 | マルチスレッド処理 |
| **Flask** | 2.3+ | WebサーバーとREST API | WebSocket統合 |
| **OpenCV** | 4.11+ | 高速画像処理 | GPU加速対応 |
| **MediaPipe** | 0.10+ | リアルタイム姿勢推定 | パイプライン最適化 |
| **YOLOv8** | 8.3+ | 高精度物体検出 | 推論最適化 |
| **PyTorch** | 2.5+ | 深層学習フレームワーク | MPS/CUDA対応 |
| **psutil** | 7.0+ | システム監視 | メモリ最適化 |

#### フロントエンド
| 技術 | バージョン | 役割 | 機能 |
|------|------------|------|------|
| **React** | 19.0+ | モダンUI実装 | Hooks最適化 |
| **TypeScript** | 5.7+ | 型安全な開発 | 静的解析強化 |
| **Chakra UI** | 2.8+ | UIコンポーネント | レスポンシブ対応 |
| **react-i18next** | 15.5+ | 国際化フレームワーク | 動的言語切り替え |
| **Socket.IO** | 4.8+ | リアルタイム通信 | 低遅延通信 |
| **Vite** | 6.2+ | 高速ビルドツール | HMR対応 |

#### 開発・テスト環境
| 技術 | バージョン | 目的 | カバレッジ |
|------|------------|------|-----------|
| **Jest** | 29.7+ | JavaScript/TypeScript テスト | 79.13% |
| **React Testing Library** | 14.2+ | Reactコンポーネントテスト | 高品質テスト |
| **pytest** | 8.3+ | Pythonテストフレームワーク | 包括的テスト |
| **ESLint** | 9.21+ | 静的解析 | コード品質保証 |

## 📁 プロジェクト構成

### 🗂️ 全体構造
```
KanshiChan/                       # 🏠 プロジェクトルート
├── 📊 README.md                  # ★ このファイル（プロジェクト説明）
├── 📦 requirements.txt           # ★ Python依存パッケージ（104パッケージ）
├── ⚙️ setup.py                   # Python パッケージセットアップ
├── 📝 .gitignore                 # Git除外設定
│
├── 🐍 backend/                   # Pythonバックエンド（32ファイル）
│   ├── 📂 src/                   # メインソースコード
│   │   ├── 🔧 config/            # 設定関連ファイル
│   │   │   ├── config.yaml       # ★ メイン設定ファイル（最適化・メモリ・国際化設定）
│   │   │   ├── schedules.json    # スケジュール設定
│   │   │   └── __init__.py
│   │   │
│   │   ├── 🧠 core/              # コア機能（13モジュール）
│   │   │   ├── 📷 camera.py         # カメラ制御・フレーム取得
│   │   │   ├── 🔍 object_detector.py # AI最適化統合物体検出
│   │   │   ├── 🎨 detection_renderer.py # 検出結果描画処理
│   │   │   ├── 🚀 ai_optimizer.py    # ★ AI処理最適化（フレームスキップ・バッチ処理）
│   │   │   ├── 💾 memory_manager.py  # ★ メモリ管理強化（LRUキャッシュ・GC最適化）
│   │   │   ├── 👁️ monitor.py         # 監視機能のメインロジック
│   │   │   ├── 🎯 frame_processor.py # フレーム処理エンジン
│   │   │   ├── 📡 status_broadcaster.py # ステータス配信管理
│   │   │   ├── ⏰ schedule_checker.py # スケジュールチェック機能
│   │   │   ├── 📊 threshold_manager.py # 閾値管理システム
│   │   │   ├── 🔗 detection.py       # 検出処理統合管理
│   │   │   ├── 🎛️ detector.py        # 旧来検出器（互換性維持）
│   │   │   └── 📈 state.py           # 状態管理（不在・アラート状態）
│   │   │
│   │   ├── 🔧 services/          # 外部サービス連携（6モジュール）
│   │   │   ├── ⚠️ alert_manager.py   # アラート通知の統合管理
│   │   │   ├── 🚨 alert_service.py   # アラート処理の抽象化
│   │   │   ├── 📱 line_service.py    # LINE通知連携
│   │   │   ├── 🤖 llm_service.py     # LLM連携サービス
│   │   │   ├── 📅 schedule_manager.py # スケジュール管理
│   │   │   └── 🔊 sound_service.py   # 音声再生サービス
│   │   │
│   │   ├── 🔊 sounds/            # アラート音声ファイル
│   │   │   ├── alert.wav         # 基本アラート音
│   │   │   ├── alert_absence.wav # 不在アラート音
│   │   │   ├── alert_smartphone.wav # スマホ使用アラート音
│   │   │   └── 🎵 その他音声ファイル
│   │   │
│   │   ├── 🛠️ utils/             # ユーティリティ（4モジュール）
│   │   │   ├── ⚙️ config_manager.py  # 設定ファイル管理（拡張版）
│   │   │   ├── 📝 logger.py          # ロガー設定
│   │   │   ├── 📄 yaml_utils.py      # YAML操作ユーティリティ
│   │   │   └── 🚨 exceptions.py      # ★ 30+専門例外クラス
│   │   │
│   │   ├── 🌐 web/               # Web API と WebSocket（4モジュール）
│   │   │   ├── 🔌 api.py            # Flask REST API（パフォーマンス統計追加）
│   │   │   ├── 🏠 app.py            # Flask アプリケーション設定
│   │   │   ├── 🎛️ handlers.py       # ルートハンドラー
│   │   │   └── 📡 websocket.py      # WebSocket 通信ハンドラ
│   │   │
│   │   └── 🚀 main.py            # ★ アプリケーションエントリーポイント
│   │
│   └── 🧪 tests/                 # バックエンドテストコード
│       ├── 📊 test_*.py          # 包括的テストスイート
│       └── 🔧 conftest.py        # pytest 設定
│
├── ⚛️ frontend/                   # Reactフロントエンド
│   ├── 📁 public/                # 静的ファイル
│   │   └── 🖼️ アイコン・ロゴファイル
│   │
│   ├── 📂 src/                   # フロントエンドソースコード
│   │   ├── 🎨 assets/            # アセットファイル
│   │   │
│   │   ├── 🧩 components/        # React コンポーネント（6コンポーネント）
│   │   │   ├── 👁️ MonitorView.tsx    # 監視画面コンポーネント
│   │   │   ├── ⚙️ SettingsPanel.tsx  # 設定パネルコンポーネント  
│   │   │   ├── 📅 ScheduleView.tsx   # スケジュール表示コンポーネント
│   │   │   ├── 🌍 LanguageSwitcher.tsx # ★ 言語切り替えコンポーネント
│   │   │   ├── 📊 PerformanceStats.tsx # ★ パフォーマンス統計表示
│   │   │   └── 🧪 __tests__/         # コンポーネントテスト（79.13%カバレッジ）
│   │   │       ├── MonitorView.test.tsx    # 10テストケース
│   │   │       ├── SettingsPanel.test.tsx  # 12テストケース
│   │   │       └── App.test.tsx            # 7テストケース
│   │   │
│   │   ├── 🌍 i18n/              # ★ 国際化対応
│   │   │   ├── 🔧 index.ts           # 国際化設定
│   │   │   └── 📂 locales/          # 翻訳ファイル
│   │   │       ├── 🇯🇵 ja.json        # 日本語翻訳
│   │   │       └── 🇺🇸 en.json        # 英語翻訳
│   │   │
│   │   ├── 🛠️ utils/             # ユーティリティ
│   │   │   ├── 📡 websocket.ts      # WebSocket 通信ユーティリティ
│   │   │   └── 🧪 __tests__/        # ユーティリティテスト（7テストケース）
│   │   │
│   │   ├── 🎨 App.tsx            # ★ メインアプリケーション（国際化統合）
│   │   ├── 🚀 main.tsx           # ★ フロントエンドエントリーポイント
│   │   ├── 🎭 theme.ts           # Chakra UI テーマ設定
│   │   └── 🧪 __tests__/         # アプリテスト
│   │
│   ├── 📦 package.json           # ★ npm依存関係（react-i18next等追加）
│   ├── ⚙️ vite.config.ts         # Vite ビルド設定
│   ├── 📊 coverage/              # テストカバレッジレポート
│   └── 🔧 設定ファイル群
│
├── 📜 project_rules/             # ★ 開発規約・ガイドライン
│   ├── 📖 README.md              # 規約の概要と使用方法
│   ├── 🌐 main_rules.yaml        # プロジェクト全体規約
│   ├── 🐍 backend_rules.yaml     # バックエンド開発規約
│   ├── ⚛️ frontend_rules.yaml    # フロントエンド開発規約
│   └── 🤖 ai_ml_rules.yaml       # AI/ML機能開発規約
│
└── 📂 その他設定ファイル
    ├── .cursor/                  # Cursor エディタ設定  
    ├── .vscode/                  # VS Code 設定
    └── 🔧 各種設定ファイル
```

### 🔍 重要ファイルの詳細説明

#### 🚀 **新機能・最適化されたファイル**
| ファイル | 説明 | 主な機能 | Phase |
|----------|------|----------|--------|
| `backend/src/core/ai_optimizer.py` | AI処理最適化エンジン | フレームスキップ・バッチ処理・パフォーマンス監視 | Phase 3 |
| `backend/src/core/memory_manager.py` | メモリ管理システム | LRUキャッシュ・GC最適化・メモリ監視 | Phase 3 |
| `frontend/src/i18n/` | 国際化対応 | 日英翻訳・動的言語切り替え | Phase 3 |
| `frontend/src/components/PerformanceStats.tsx` | パフォーマンス統計UI | リアルタイムFPS・メモリ使用量表示 | Phase 3 |
| `backend/src/utils/exceptions.py` | 例外体系 | 30+専門例外クラス・詳細エラーハンドリング | Phase 2 |

#### 🏗️ **リファクタリングで分割されたファイル**
| ファイル | 説明 | 分割元 | 責務 |
|----------|------|--------|------|
| `backend/src/core/frame_processor.py` | フレーム処理専門 | monitor.py | AI検出とフレーム処理の分離 |
| `backend/src/core/status_broadcaster.py` | ステータス配信 | monitor.py | WebSocket通信とUI更新 |
| `backend/src/core/object_detector.py` | 物体検出統合 | detector.py | YOLO・MediaPipe統合管理 |
| `backend/src/core/detection_renderer.py` | 描画処理専門 | detector.py | 検出結果の可視化処理 |

#### 📊 **設定・依存関係ファイル**
| ファイル | 説明 | 主な内容 |
|----------|------|----------|
| `backend/src/config/config.yaml` | 統合設定ファイル | AI最適化・メモリ管理・国際化設定 |
| `requirements.txt` | Python依存関係（104パッケージ） | AI・画像処理・Web・最適化ライブラリ |
| `frontend/package.json` | npm依存関係 | React・TypeScript・国際化・テストライブラリ |

## ⚙️ 設定とカスタマイズ

### 🔧 メイン設定ファイル
すべての設定は `backend/src/config/config.yaml` に統合されています。リファクタリングにより、AI最適化・メモリ管理・国際化の設定が追加されました。

```yaml
# 🎥 カメラ設定
camera:
  device_id: 0                    # カメラデバイスID (通常は0)
  width: 640                      # 解像度 (幅)
  height: 480                     # 解像度 (高さ)
  fps: 30                         # フレームレート

# ⏱️ 状態管理の閾値設定 (秒)
conditions:
  absence:
    threshold_seconds: 1800.0     # この時間以上不在だとアラート (30分)
  smartphone_usage:
    threshold_seconds: 600.0      # この時間以上スマホ使用でアラート (10分)
    grace_period_seconds: 3.0     # 検出猶予時間

# 🤖 AI検出機能の設定
detector:
  use_mediapipe: true             # MediaPipe (Pose, Hands, Face) を使用
  use_yolo: true                  # YOLO (物体検出) を使用

# 🚀 AI処理最適化設定 (Phase 3 新機能)
optimization:
  target_fps: 15.0                # 目標FPS
  min_fps: 5.0                    # 最低FPS
  max_skip_rate: 5                # 最大フレームスキップレート
  batch_processing:
    enabled: false                # バッチ処理 (実験的機能)
    batch_size: 4                 # バッチサイズ
    timeout_ms: 50                # バッチタイムアウト

# 💾 メモリ管理設定 (Phase 3 新機能)
memory:
  threshold_percent: 80.0         # メモリ使用量警告閾値 (%)
  gc_interval_seconds: 30.0       # ガベージコレクション間隔
  monitor_interval_seconds: 5.0   # メモリ監視間隔
  cache:
    max_size: 100                 # キャッシュ最大エントリ数
    max_memory_mb: 50.0           # キャッシュ最大メモリ使用量 (MB)

# 🎨 ランドマーク表示設定
landmark_settings:
  pose:
    enabled: true                 # Poseランドマーク表示
    color: [0, 255, 0]           # BGR 色 (緑)
    thickness: 2                  # 線の太さ
  hands:
    enabled: true                 # Handsランドマーク表示
    color: [0, 0, 255]           # BGR 色 (赤)
    thickness: 2
  face:
    enabled: false                # Face Meshランドマーク表示
    color: [255, 0, 0]           # BGR 色 (青)
    thickness: 1

# 🔍 検出オブジェクトの設定
detection_objects:
  smartphone:
    enabled: true                 # スマホ検出を有効
    name: "スマートフォン"
    class_name: "cell phone"       # YOLO検出クラス名
    confidence_threshold: 0.5      # 信頼度閾値
    alert_threshold: 3.0          # アラート発動時間 (秒)
    alert_message: "スマホばかり触っていないで勉強をしろ！"
    alert_sound: "smartphone_alert.wav"
    color: [255, 0, 0]           # 検出ボックス色
  laptop:
    enabled: false                # ノートPC検出
    # ... 類似設定
  book:
    enabled: false                # 本検出
    # ... 類似設定

# 📡 LINE連携設定
line:
  enabled: true                   # LINE Bot機能
  token: "YOUR_LINE_TOKEN"        # LINE Bot トークン
  channel_secret: "YOUR_SECRET"   # チャンネルシークレット
  user_id: "YOUR_USER_ID"        # ユーザーID

# 📱 メッセージと音声マッピング
message_sound_mapping:
  "お風呂入ってくる":
    extension: 1200               # 延長時間 (秒)
    sound: "alert.wav"           # 再生音声
  "買い物行ってくる":
    extension: 1200
    sound: "alert.wav"
  "散歩してくる":
    extension: 1200
    sound: "alert.wav"
  # ... 追加メッセージ

# 🖥️ 表示設定
display:
  show_opencv_window: false       # OpenCVウィンドウ表示 (開発用)

# 🌐 サーバー設定
server:
  port: 5001                      # Flask サーバーポート
```

### 🔧 設定のカスタマイズ例

#### 🚀 パフォーマンス重視設定
```yaml
optimization:
  target_fps: 20.0                # 高FPS設定
  min_fps: 10.0
  max_skip_rate: 3                # 低スキップレート

memory:
  threshold_percent: 70.0         # 早期メモリ警告
  gc_interval_seconds: 20.0       # 頻繁なGC
```

#### 💾 省メモリ設定
```yaml
optimization:
  target_fps: 10.0                # 低FPS設定
  max_skip_rate: 8                # 高スキップレート

memory:
  cache:
    max_size: 50                  # 小さなキャッシュ
    max_memory_mb: 25.0
```

> 💡 **注意点**
> - 設定変更後はバックエンドの再起動が必要です
> - パフォーマンス設定は実際の環境に応じて調整してください
> - `landmark_settings` の `color` は BGR (青、緑、赤) の順で指定します

## 🌍 国際化対応

KanshiChan v2.0では、react-i18nextを使用した包括的な国際化対応を実装しています。

### 🌐 サポート言語
- **🇯🇵 日本語 (ja)**: デフォルト言語
- **🇺🇸 英語 (en)**: 完全翻訳対応

### 🔧 言語切り替え機能
- **動的切り替え**: アプリケーション実行中にシームレスな言語変更
- **設定保存**: ブラウザのlocalStorageに言語設定を保存
- **自動検出**: ブラウザの言語設定を自動検出

### 📁 翻訳ファイル構造
```
frontend/src/i18n/
├── index.ts                      # 国際化設定
└── locales/
    ├── ja.json                   # 日本語翻訳
    └── en.json                   # 英語翻訳
```

### 🎯 翻訳カバー範囲
| カテゴリ | 項目数 | 説明 |
|----------|--------|------|
| **アプリケーション** | 2 | タイトル・サブタイトル |
| **ナビゲーション** | 3 | タブ（監視・設定・スケジュール） |
| **監視画面** | 8 | ステータス・パフォーマンス指標 |
| **設定画面** | 15 | 各種設定項目・バリデーションメッセージ |
| **スケジュール** | 9 | スケジュール管理機能 |
| **共通要素** | 7 | ボタン・メッセージ・確認ダイアログ |

### 🔧 開発者向け国際化API
```typescript
import { useTranslation } from 'react-i18next';

const Component = () => {
  const { t, i18n } = useTranslation();
  
  // 翻訳テキストの取得
  const title = t('app.title');
  
  // 言語切り替え
  const changeLanguage = (lang: string) => {
    i18n.changeLanguage(lang);
  };
  
  return <h1>{title}</h1>;
};
```

## 📊 パフォーマンス最適化

KanshiChan v2.0では、Phase 3リファクタリングで実装された高度なパフォーマンス最適化機能を提供します。

### 🚀 AI処理最適化 (`ai_optimizer.py`)

#### 📈 動的フレームスキップ
- **適応的スキップレート**: 現在のFPSに基づいて自動調整
- **目標FPS維持**: 15+ FPSの安定した動作を保証
- **リアルタイム監視**: パフォーマンス統計の継続監視

#### 🔄 バッチ処理（実験的機能）
- **フレームバッファリング**: 複数フレームの同時処理
- **タイムアウト制御**: 遅延を最小限に抑制

#### 📊 パフォーマンス監視
```python
# パフォーマンス統計の例
{
  "fps": 15.2,                    # 現在のFPS
  "avg_inference_ms": 45.8,       # 平均推論時間
  "memory_mb": 245.6,             # メモリ使用量
  "skip_rate": 2,                 # 現在のスキップレート
  "optimization_active": true     # 最適化有効状態
}
```

### 💾 メモリ管理強化 (`memory_manager.py`)

#### 🗂️ LRUキャッシュシステム
- **フレームキャッシュ**: 処理済みフレームの効率的な保存
- **結果キャッシュ**: AI推論結果の再利用
- **メモリ制限**: 設定可能な最大メモリ使用量

#### 🔄 ガベージコレクション最適化
- **世代別GC**: Python の世代別ガベージコレクション最適化
- **自動実行**: メモリ使用量に基づく自動実行
- **統計収集**: GC実行統計の詳細収集

#### 🚨 緊急メモリクリーンアップ
- **自動発動**: メモリ使用量が80%を超えた際の自動実行
- **段階的クリーンアップ**: キャッシュクリア → 強制GC の順次実行

### 📊 リアルタイムパフォーマンス表示

#### 🖥️ フロントエンド統計画面
- **FPS表示**: 色分けされた現在FPS（緑:15+, 黄:10-15, 赤:10未満）
- **推論時間**: 平均AI推論時間（ミリ秒）
- **メモリ使用量**: 現在のメモリ使用量（MB）
- **最適化状態**: AI最適化機能の有効/無効状態

#### 🔄 自動更新
- **更新間隔**: 5秒間隔でのリアルタイム更新
- **API統合**: `/api/performance` エンドポイントからデータ取得

### ⚡ パフォーマンス目標と実績

| メトリクス | 最適化前 | Phase 3後 | 目標 |
|-----------|----------|-----------|------|
| **AI処理FPS** | ~10 FPS | **15+ FPS** ✅ | 15+ FPS |
| **API応答時間** | ~300ms | **<200ms** ✅ | <200ms |
| **メモリ効率** | 固定使用 | **動的管理** ✅ | 適応制御 |
| **安定性** | 時々クラッシュ | **高安定性** ✅ | 99%+ 稼働 |

## 👥 開発ガイド

### 📋 開発規約・ガイドライン
KanshiChanでは、プロジェクトの一貫性と品質を保つため、詳細な開発規約を [`project_rules/`](./project_rules/) ディレクトリに定義しています。

#### 🌟 主要規約ファイル
- **[メイン規約](./project_rules/main_rules.yaml)**: プロジェクト全体に適用される基本規約
- **[バックエンド規約](./project_rules/backend_rules.yaml)**: Python/Flask開発に特化した規約  
- **[フロントエンド規約](./project_rules/frontend_rules.yaml)**: React/TypeScript開発に特化した規約
- **[AI/ML規約](./project_rules/ai_ml_rules.yaml)**: AI/ML機能開発に特化した規約

#### 🔍 規約の確認方法
新機能開発や修正を行う前に、該当する規約ファイルを確認してください：
```bash
# 規約ディレクトリの概要を確認
cat project_rules/README.md

# 各領域の詳細規約を確認  
cat project_rules/main_rules.yaml      # 全体規約
cat project_rules/backend_rules.yaml   # バックエンド規約
cat project_rules/frontend_rules.yaml  # フロントエンド規約
cat project_rules/ai_ml_rules.yaml     # AI/ML規約
```

### 🧪 テスト・品質管理

#### 📊 テストカバレッジ（Phase 2-3 成果）
- **フロントエンド**: **79.13%** （目標80%にほぼ到達）
- **総テストケース**: **36ケース**追加
- **テスト分類**:
  - MonitorView.test.tsx: 10テストケース
  - SettingsPanel.test.tsx: 12テストケース  
  - App.test.tsx: 7テストケース
  - websocket.test.ts: 7テストケース

#### 🔬 テスト実行コマンド
```bash
# バックエンドテスト
cd backend
python -m pytest tests/ -v
python -m pytest --cov=src tests/ --cov-report=html

# フロントエンドテスト  
cd frontend
npm test                              # 全テスト実行
npm run test:watch                    # ウォッチモード
npm test -- --coverage               # カバレッジレポート生成
```

#### 📝 コード品質管理
```bash
# Pythonコード品質
black backend/src                     # コードフォーマット
flake8 backend/src                    # 静的解析
mypy backend/src                      # 型チェック

# TypeScriptコード品質
cd frontend
npm run lint                          # ESLint実行
npm run type-check                    # TypeScript型チェック
```

### 🏗️ アーキテクチャ設計原則

#### 🎯 Phase別リファクタリング成果
| Phase | 目標 | 成果 | 品質向上 |
|-------|------|------|----------|
| **Phase 1** | 緊急課題解決 | コード分割・ESLint解消 | 可読性 ⭐⭐⭐⭐☆ |
| **Phase 2** | 堅牢性強化 | 例外体系・設定管理・テスト | 拡張性 ⭐⭐⭐⭐⭐ |
| **Phase 3** | パフォーマンス最適化 | AI最適化・メモリ管理・国際化 | パフォーマンス ⭐⭐⭐⭐⭐ |

#### 🧩 モジュール設計原則
- **単一責任**: 各モジュールは明確に定義された単一の責任を持つ
- **依存性注入**: ConfigManagerを通じた設定の集中管理
- **例外処理**: 30+の専門例外クラスによる詳細なエラーハンドリング
- **国際化**: 全UIテキストの翻訳対応

### 🤝 貢献ガイドライン

#### 🌿 ブランチ戦略
```bash
# 機能追加
git checkout -b feature/新機能名

# バグ修正  
git checkout -b fix/バグの概要

# パフォーマンス改善
git checkout -b perf/最適化内容

# 国際化対応
git checkout -b i18n/言語コード
```

#### 📝 コミットメッセージ規則
```bash
feat: 新機能追加
fix: バグ修正
perf: パフォーマンス改善
docs: ドキュメント更新
style: コードスタイル変更
refactor: リファクタリング
test: テスト追加・修正
i18n: 国際化対応
```

#### 🔍 プルリクエストガイドライン
1. **事前チェック**: 規約遵守・テスト通過・型チェック通過
2. **説明**: 変更内容・影響範囲・テスト方法を詳細に記載
3. **レビュー**: パフォーマンス影響・国際化対応・例外処理の確認

## ❓ トラブルシューティング

### 🔧 よくある問題と解決方法

#### 🚀 パフォーマンス関連
```bash
# FPSが低い場合
# 1. 最適化設定の確認
grep -A 10 "optimization:" backend/src/config/config.yaml

# 2. メモリ使用量の確認  
curl http://localhost:5001/api/performance

# 3. フレームスキップレートの調整
# config.yaml の max_skip_rate を増加
```

#### 💾 メモリ関連
```bash
# メモリ使用量が高い場合
# 1. キャッシュサイズの縮小
# config.yaml の cache.max_memory_mb を削減

# 2. GC間隔の短縮
# config.yaml の gc_interval_seconds を削減

# 3. 手動メモリクリーンアップ
curl -X POST http://localhost:5001/api/memory/cleanup
```

#### 🌍 国際化関連
```bash
# 言語切り替えが動作しない場合
# 1. ブラウザのローカルストレージをクリア
localStorage.clear()

# 2. i18next初期化の確認
# ブラウザコンソールでエラーメッセージを確認

# 3. 翻訳ファイルの検証
cat frontend/src/i18n/locales/ja.json | jq .
```

#### 🔍 AI検出関連
```bash
# YOLOモデルのダウンロードエラー
wget https://github.com/ultralytics/yolov8/releases/download/v8.3.0/yolov8n.pt
mv yolov8n.pt backend/

# MediaPipeエラー
pip install --upgrade mediapipe opencv-python

# GPU使用時のエラー（macOS）
export MEDIAPIPE_DISABLE_GPU=1
```

#### 📱 カメラアクセス関連
```bash
# カメラアクセスエラー
# 1. ブラウザ権限の確認
# Chrome: 設定 > プライバシーとセキュリティ > サイトの設定 > カメラ

# 2. 他アプリでのカメラ使用確認
lsof | grep -i camera

# 3. カメラデバイスIDの確認・変更
# config.yaml の camera.device_id を変更 (0, 1, 2...)
```

### 🏥 診断コマンド

#### 🔍 システム状態確認
```bash
# 総合システム状態
curl http://localhost:5001/api/settings | jq .

# パフォーマンス統計
curl http://localhost:5001/api/performance | jq .

# メモリ使用状況
curl http://localhost:5001/api/memory/stats | jq .
```

#### 📊 ログ分析
```bash
# バックエンドログ確認
tail -f backend/logs/kanshichan.log

# フロントエンドテスト実行
cd frontend && npm test -- --verbose

# カバレッジレポート生成
cd frontend && npm test -- --coverage --watchAll=false
```

### 🖥️ プラットフォーム別注意点

#### 🍎 **macOS**
```bash
# 必要な追加パッケージ
brew install portaudio
export MEDIAPIPE_DISABLE_GPU=1    # GPU無効化で安定性向上
```

#### 🪟 **Windows**
```bash
# Visual C++ ビルドツール必須
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Windows Defender除外設定
# KanshiChanディレクトリをリアルタイム保護から除外
```

#### 🐧 **Linux**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-opencv portaudio19-dev

# CentOS/RHEL
sudo yum install opencv-python portaudio-devel
```

## 📜 ライセンス

本プロジェクトは[MITライセンス](LICENSE)の下で公開されています。

### ✅ 利用条件
- **商用利用可能**: 制限なく商用プロジェクトで使用可能
- **改変・再配布可能**: ソースコードの修正・配布が自由
- **著作権表示必要**: ライセンス文とコピーライト表示が必須

### 📋 サードパーティライセンス
| ライブラリ | ライセンス | 用途 |
|-----------|------------|------|
| **YOLOv8** | [AGPL-3.0](https://github.com/ultralytics/yolov8/blob/main/LICENSE) | 物体検出 |
| **MediaPipe** | [Apache-2.0](https://github.com/google/mediapipe/blob/master/LICENSE) | 姿勢推定 |
| **React** | [MIT](https://github.com/facebook/react/blob/main/LICENSE) | UI フレームワーク |
| **Flask** | [BSD-3-Clause](https://github.com/pallets/flask/blob/main/LICENSE.rst) | Web フレームワーク |
| **Chakra UI** | [MIT](https://github.com/chakra-ui/chakra-ui/blob/main/LICENSE) | UI コンポーネント |

### 🤝 コントリビューション
- プルリクエスト・Issue報告を歓迎します
- [開発規約](./project_rules/)に従った開発をお願いします
- Phase 3リファクタリング完了により、高品質で安定したコードベースを実現

### 📞 サポート・お問い合わせ
- **🐛 バグ報告**: [GitHub Issues](https://github.com/tomoyasu-sasaki/KanshiChan/issues)
- **💡 機能提案**: [GitHub Discussions](https://github.com/tomoyasu-sasaki/KanshiChan/discussions)
- **📖 ドキュメント**: [Wiki](https://github.com/tomoyasu-sasaki/KanshiChan/wiki)

---

<div align="center">

**🎉 KanshiChan v2.0 - Phase 3リファクタリング完了！**

*AIとパフォーマンス最適化で、より快適な作業環境を提供します*

[![Star this repository](https://img.shields.io/github/stars/tomoyasu-sasaki/KanshiChan?style=social)](https://github.com/tomoyasu-sasaki/KanshiChan)

</div>
