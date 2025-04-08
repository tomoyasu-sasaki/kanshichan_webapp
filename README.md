# 📡 監視ちゃん (KanshiChan) - AIベースの作業集中支援ツール

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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
7. [👥 開発ガイド](#-開発ガイド)
8. [❓ トラブルシューティング](#-トラブルシューティング)
9. [📜 ライセンス](#-ライセンス)

## 🎯 概要
「監視ちゃん」は、カメラを使ってユーザーの作業状態をリアルタイム監視し、適切なフィードバックを提供するAIアシスタントです。姿勢の乱れやスマートフォンの過度な使用を検知し、作業効率の向上をサポートします。

> 💪 **主な特徴**
> - リアルタイムな姿勢検出と行動分析
> - カスタマイズ可能なアラート設定
> - 直感的なWebインターフェース

## 🎬 デモ
### 💻 監視画面
リアルタイムの姿勢検出と行動分析を表示
[![監視画面デモ](docs/images/monitor.png)](https://youtu.be/your-demo-video)
> 👆 画像をクリックすると動画デモをご覧いただけます

### ⚙️ 設定画面
検出感度やアラート設定をカスタマイズ可能
![設定画面](docs/images/settings.png)

### ⚠️ アラート例
不適切な姿勢や長時間のスマートフォン使用を検知した際の警告表示
![アラート例](docs/images/alert.gif)

## 🚀 クイックスタート

### 📋 必要条件
- Python 3.9以上
- Node.js 16以上
- カメラへのアクセス権限
- 音声出力デバイス

### 🔧 インストール
```bash
# 1. リポジトリのクローン
git clone https://github.com/yourusername/KanshiChan.git
cd KanshiChan

# 2. バックエンドのセットアップ
cd backend
python -m venv venv
source venv/bin/activate  # Windows: `venv\Scripts\activate.bat`
pip install -r requirements.txt  # 依存関係のインストール
python -m backend.src.main  # サーバー起動

# 3. フロントエンドのセットアップ（新しいターミナルで実行）
cd frontend
npm install  # 依存パッケージのインストール
npm run dev  # 開発サーバー起動
```

> 💡 **初回起動時の注意点**
> - YOLOv8モデル（約100MB）が自動的にダウンロードされます
> - ダウンロード中は検出機能が一時的に制限されます
> - ブラウザでカメラへのアクセスを許可する必要があります

## 💡 機能と技術スタック

### 🎯 主要機能
- 👀 **リアルタイム監視**
  - MediaPipeによる**Pose, Hands, Face**のランドマーク検出と表示（設定でON/OFF可能）
  - YOLOv8を使用したスマートフォン等の物体検知
- ⏰ **インテリジェントアラート**
  - 不適切な姿勢の検知と警告（将来実装予定）
  - 長時間のスマートフォン使用検知
  - カスタマイズ可能な不在管理
- 🎛️ **直感的なUI**
  - リアルタイムフィードバック
  - 柔軟な設定調整
  - ステータス可視化

### 🛠️ 技術スタック
#### バックエンド
| 技術 | バージョン | 説明 | ドキュメント |
|------|------------|------|--------------|
| Python | 3.9+ | コアロジック実装 | [公式サイト](https://www.python.org/) |
| Flask | 2.0+ | Webサーバー | [ドキュメント](https://flask.palletsprojects.com/) |
| OpenCV | 4.5+ | 画像処理 | [ドキュメント](https://docs.opencv.org/) |
| MediaPipe | 0.8+ | 姿勢推定 | [ドキュメント](https://mediapipe.dev/) |
| YOLOv8 | 最新 | 物体検出 | [ドキュメント](https://docs.ultralytics.com/) |

#### フロントエンド
| 技術 | バージョン | 説明 | ドキュメント |
|------|------------|------|--------------|
| React | 18+ | UI実装 | [公式サイト](https://reactjs.org/) |
| TypeScript | 4.5+ | 型安全な開発 | [ドキュメント](https://www.typescriptlang.org/) |
| Material-UI | 5.0+ | UIコンポーネント | [ドキュメント](https://mui.com/) |

## 📁 プロジェクト構成
```
KanshiChan/
├── backend/                      # Pythonバックエンド
│   ├── src/
│   │   ├── config/             # デフォルト設定ファイル (config.yaml) が格納されるディレクトリ (現在は未使用)
│   │   ├── core/               # コア機能 (カメラ、検出、状態管理)
│   │   │   ├── camera.py
│   │   │   ├── detector.py     # YOLOv8, MediaPipe 検出ロジック、描画ロジック
│   │   │   ├── detection_manager.py # 検出処理の管理
│   │   │   └── state_manager.py     # 状態管理 (不在、スマホ使用)
│   │   ├── services/           # 外部サービス連携 (アラート)
│   │   │   ├── alert_manager.py # アラート通知の管理
│   │   │   └── alert_service.py   # (将来的な具体的な通知処理: 音声、LINEなど)
│   │   ├── web/                # Web API (Flask) と WebSocket
│   │   │   ├── api.py          # Flask API エンドポイント
│   │   │   └── websocket.py    # WebSocket 通信ハンドラ
│   │   ├── utils/              # ユーティリティ (ロガー、設定管理)
│   │   │   ├── logger.py
│   │   │   └── config_manager.py # 設定ファイル (config.yaml) の読み込み・管理
│   │   ├── __init__.py
│   │   └── main.py             # アプリケーションエントリーポイント
│   ├── logs/                   # ログファイル出力先
│   ├── config.yaml             # ★ アプリケーション設定ファイル ★
│   ├── requirements.txt        # Python 依存パッケージ
│   └── venv/                   # Python 仮想環境 (Git管理外)
│
├── frontend/                     # Reactフロントエンド
│   ├── public/
│   ├── src/
│   │   ├── assets/             # 画像、音声ファイル
│   │   ├── components/         # React コンポーネント (MonitorView, SettingsPanel など)
│   │   ├── hooks/              # カスタムフック
│   │   ├── services/           # API/WebSocket 通信
│   │   ├── styles/             # スタイル関連
│   │   ├── types/              # TypeScript 型定義
│   │   ├── App.tsx             # アプリケーションメインコンポーネント
│   │   └── main.tsx            # フロントエンドエントリーポイント
│   ├── index.html
│   ├── package.json            # npm 設定
│   ├── tsconfig.json           # TypeScript 設定
│   └── vite.config.ts        # Vite 設定
│
├── docs/                         # ドキュメント、画像
├── tests/                        # テストコード
├── .gitignore
├── LICENSE
├── README.md                     # このファイル
└── REFACTORING.md                # リファクタリング計画・進捗

```

## ⚙️ 設定とカスタマイズ

### 設定ファイル
すべての設定はルートディレクトリ直下の `config.yaml` に集約されています。このファイルを編集することで、アプリケーションの挙動をカスタマイズできます。

```yaml
# カメラ設定
camera:
  device_id: 0       # カメラデバイスID (通常は0)
  width: 640         # 解像度 (幅)
  height: 480        # 解像度 (高さ)
  fps: 30            # フレームレート

# 状態管理の閾値設定 (秒)
conditions:
  absence:
    threshold_seconds: 600.0  # この時間以上不在だとアラート
  smartphone_usage:
    threshold_seconds: 600.0  # この時間以上スマホを使っているとアラート

# 検出機能の設定
detector:
  use_mediapipe: true   # MediaPipe (Pose, Hands, Face) を使用するか
  use_yolo: true         # YOLO (物体検出) を使用するか
  # MediaPipe 検出設定 (値域: 0.0 ~ 1.0)
  mediapipe_options:
    pose:
      min_detection_confidence: 0.5
      min_tracking_confidence: 0.5
    hands:
      min_detection_confidence: 0.5
      min_tracking_confidence: 0.5
    face:
      min_detection_confidence: 0.5
      min_tracking_confidence: 0.5 # Face Mesh は tracking confidence がない場合がある

# 各ランドマークの表示設定
landmark_settings:
  pose:
    enabled: true      # Poseランドマークを表示するか
    color: [0, 255, 0]   # BGR 色 (緑)
    thickness: 2       # 線の太さ
  hands:
    enabled: true      # Handsランドマークを表示するか
    color: [0, 0, 255]   # BGR 色 (赤)
    thickness: 2
  face:
    enabled: true      # Face Meshランドマークを表示するか
    color: [255, 0, 0]   # BGR 色 (青)
    thickness: 1

# 検出オブジェクトの設定
detection_objects:
  smartphone:
    enabled: true        # スマホ検出を有効にするか
    alert_message: "スマホの使用時間が長すぎます！"
    alert_sound: "alert.wav" # frontend/public/sounds/ 内のファイル
  # 他の検出対象オブジェクト (例: book, laptop) を追加可能
  # book:
  #   enabled: false
  #   alert_message: ""
  #   alert_sound: ""

# 表示関連の設定
display:
  show_opencv_window: true # 開発用に OpenCV のウィンドウを表示するか
  draw_bounding_boxes: true # YOLO の検出ボックスを描画するか
  draw_labels: true        # YOLO の検出ラベルを描画するか

# アラート通知設定
alert:
  sound_enabled: true    # アラート音を有効にするか
  line_notify_enabled: false # LINE Notify を有効にするか
  line_notify_token: "YOUR_LINE_NOTIFY_TOKEN" # LINE Notify のトークン

# メッセージ表示時間等の設定 (フロントエンド用)
message_extensions:
  info_duration: 3000       # 情報メッセージの表示時間 (ms)
  warning_duration: 5000    # 警告メッセージの表示時間 (ms)
  error_duration: 7000      # エラーメッセージの表示時間 (ms)
  alert_cooldown: 10000     # アラートのクールダウン時間 (ms)
  threshold_extension_options: # 不在時間延長オプション (UI表示名: 秒数)
    "5分休憩": 300
    "10分休憩": 600
    "昼休憩": 3600

```

> 💡 **注意点**
> - 設定変更後はバックエンドの再起動が必要です。
> - `landmark_settings` の `color` は BGR (青、緑、赤) の順で指定します。
> - アラート音ファイルは `frontend/public/sounds/` ディレクトリに配置してください。

## 👥 開発ガイド
### 🔬 テスト実行
```bash
# ユニットテスト実行
python -m pytest tests/
# カバレッジレポート生成
python -m pytest --cov=src tests/ --cov-report=html
```

### 📝 コード品質管理
```bash
# コードフォーマット
black backend/src
# 静的解析
flake8 backend/src
# 型チェック
mypy backend/src
```

### 🤝 貢献ガイドライン
1. Issueの作成
   - バグ報告は再現手順を詳細に
   - 機能提案は目的と実装案を明確に
2. ブランチ命名規則
   - 機能追加: `feature/機能名`
   - バグ修正: `fix/問題の概要`
3. コミットメッセージ
   - 先頭に種類を記載: `feat:`, `fix:`, `docs:`, `test:`
4. プルリクエスト
   - テンプレートに従って作成
   - レビュー前にセルフレビューを実施

## ❓ トラブルシューティング
### よくある問題と解決方法
- 🔍 **YOLOモデルのダウンロードエラー**
  ```bash
  # 手動でモデルをダウンロード
  wget https://github.com/ultralytics/yolov8/releases/download/v8.0.0/yolov8n.pt
  ```
- 🎥 **カメラアクセスエラー**
  - ブラウザの権限設定を確認
  - 他のアプリでカメラが使用中でないか確認
- 📦 **依存関係エラー**
  ```bash
  # pipのアップグレード
  pip install --upgrade pip
  # 個別インストール
  pip install -r requirements.txt --no-deps
  pip install <問題のパッケージ>
  ```

### プラットフォーム別の注意点
- 🍎 **macOS**
  - `brew install portaudio` が必要
- 🪟 **Windows**
  - Visual C++ ビルドツールが必要
- 🐧 **Linux**
  - `sudo apt-get install python3-opencv` が必要

## 📜 ライセンス
本プロジェクトは[MITライセンス](LICENSE)の下で公開されています。

### 利用条件
- ✅ 商用利用可能
- ✅ 改変・再配布可能
- ✅ 著作権表示必要

### サードパーティライセンス
- YOLOv8: [AGPL-3.0](https://github.com/ultralytics/yolov8/blob/main/LICENSE)
- MediaPipe: [Apache-2.0](https://github.com/google/mediapipe/blob/master/LICENSE)
