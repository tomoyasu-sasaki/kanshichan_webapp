# 監視ちゃん (KanshiChan)

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 目次
1. [概要](#概要)
2. [デモ](#デモ)
3. [クイックスタート](#クイックスタート)
4. [機能概要](#機能概要)
5. [使用技術](#使用技術)
6. [ディレクトリ構成](#ディレクトリ構成)
7. [主要機能](#主要機能)
8. [セットアップ](#セットアップ)
9. [設定ガイド](#設定ガイド)
10. [トラブルシューティング](#トラブルシューティング)
11. [開発ロードマップ](#開発ロードマップ)
12. [貢献ガイド](#貢献ガイド)
13. [パフォーマンス](#パフォーマンスチューニング)
14. [セキュリティ](#セキュリティ)
15. [ライセンス](#ライセンス)

## 概要
「監視ちゃん」は、学習・作業時の集中力を維持するためのAIアシスタントシステムです。カメラを使用してユーザーの姿勢や行動をリアルタイムで監視し、不適切な姿勢や長時間のスマートフォン使用を検出した際に警告を行います。直感的なWebインターフェースを通じて、監視状態の確認や各種設定の調整が可能です。

## デモ
### 監視画面
![監視画面](docs/images/monitor.png)

### 設定画面
![設定画面](docs/images/settings.png)

### アラート例
![アラート例](docs/images/alert.gif)

## クイックスタート
```bash
# リポジトリのクローン
git clone https://github.com/yourusername/KanshiChan.git
cd KanshiChan

# バックエンドの起動
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.main

# 新しいターミナルでフロントエンドの起動
cd frontend
npm install
npm run dev
```

## 機能概要
- 👀 **リアルタイム監視**: 姿勢検出と行動分析をリアルタイムで実行
- 📱 **スマートフォン検出**: 長時間の使用を検知して警告
- ⏰ **不在管理**: 設定時間以上の離席を検知してアラート
- 🎛️ **カスタマイズ**: 検出感度やアラート設定を柔軟に調整可能
- 🖥️ **Webインターフェース**: 直感的な操作と視覚的なフィードバック

## 使用技術

### バックエンド
- **Python 3.9+**: 高度な画像処理と機械学習のための強力な基盤
- **Flask**: 軽量で拡張性の高いWebフレームワーク
- **Flask-SocketIO**: リアルタイムな双方向通信を実現
- **OpenCV**: 効率的な画像処理と動画ストリーミングを提供
- **MediaPipe**: 高精度な姿勢推定を低負荷で実現
- **YOLOv8**: リアルタイムな物体検出を高精度で実行
- **playsound**: クロスプラットフォームな音声再生を実現

### フロントエンド
- **React**: 効率的なUIコンポーネント管理と再利用性を実現
- **TypeScript**: 型安全性による堅牢なコード開発を可能に
- **Material-UI**: モダンで使いやすいUIコンポーネントを提供
- **Socket.IO-client**: サーバーとのリアルタイム通信を実現

## ディレクトリ構成

```
KanshiChan/
├── backend/                        # バックエンドアプリケーション
│   ├── requirements.txt           # Pythonパッケージの依存関係
│   └── src/
│       ├── config/               # 設定ファイル
│       │   ├── __init__.py
│       │   ├── display_settings.py    # 表示設定（ランドマーク、色など）
│       │   ├── message_settings.py    # メッセージ設定（アラート、音声）
│       │   └── system_settings.py     # システム設定（検出感度など）
│       │
│       ├── core/                # 核となる機能
│       │   ├── __init__.py
│       │   ├── camera.py            # カメラ制御
│       │   ├── detector.py          # 物体検出エンジン
│       │   └── monitor.py           # 監視制御
│       │
│       ├── services/            # 各種サービス
│       │   ├── __init__.py
│       │   ├── alert_service.py     # アラート管理
│       │   ├── detection_service.py  # 検出処理
│       │   └── websocket_service.py  # WebSocket通信
│       │
│       ├── sounds/              # アラート音声ファイル
│       │   ├── alert.wav
│       │   ├── smartphone_alert.wav
│       │   └── notification.wav
│       │
│       ├── utils/               # ユーティリティ
│       │   ├── __init__.py
│       │   ├── logger.py           # ログ設定
│       │   ├── image_utils.py      # 画像処理
│       │   └── time_utils.py       # 時間管理
│       │
│       ├── web/                 # Webサーバー
│       │   ├── __init__.py
│       │   ├── api/               # REST API
│       │   │   ├── __init__.py
│       │   │   ├── routes.py
│       │   │   └── handlers.py
│       │   └── websocket/         # WebSocketハンドラ
│       │       ├── __init__.py
│       │       └── handlers.py
│       │
│       └── main.py             # アプリケーションエントリーポイント
│
├── frontend/                      # フロントエンドアプリケーション
│   ├── package.json              # npm依存関係
│   ├── tsconfig.json             # TypeScript設定
│   └── src/
│       ├── components/          # Reactコンポーネント
│       │   ├── common/            # 共通コンポーネント
│       │   │   ├── Button.tsx
│       │   │   ├── Alert.tsx
│       │   │   └── Loading.tsx
│       │   ├── monitor/           # 監視画面コンポーネント
│       │   │   ├── VideoFeed.tsx
│       │   │   └── StatusPanel.tsx
│       │   └── settings/          # 設定画面コンポーネント
│       │       ├── DetectionSettings.tsx
│       │       └── AlertSettings.tsx
│       │
│       ├── hooks/              # カスタムフック
│       │   ├── useWebSocket.ts
│       │   ├── useDetection.ts
│       │   └── useSettings.ts
│       │
│       ├── services/           # APIクライアント
│       │   ├── api.ts
│       │   ├── websocket.ts
│       │   └── storage.ts
│       │
│       ├── types/             # 型定義
│       │   ├── detection.ts
│       │   └── settings.ts
│       │
│       └── App.tsx            # ルートコンポーネント
│
├── tests/                        # テストコード
│   ├── backend/
│   │   ├── test_detector.py
│   │   ├── test_monitor.py
│   │   └── test_services.py
│   └── frontend/
│       ├── components.test.tsx
│       └── services.test.ts
│
├── docs/                         # ドキュメント
│   ├── images/                  # スクリーンショット・図解
│   └── api/                     # API仕様書
│
├── .gitignore
├── LICENSE
└── README.md
```

## 主要機能

### 1. 姿勢検出システム
- MediaPipeによる33点の姿勢ランドマーク検出
- リアルタイムな姿勢トラッキングと可視化
- 不適切な姿勢の検知と警告

### 2. インテリジェント物体検出
- YOLOv8による高精度な物体検出
- スマートフォン、PC、本などの学習関連物体の認識
- カスタマイズ可能な検出感度と警告閾値

### 3. スマートアラートシステム
- 状況に応じた段階的な警告
- カスタマイズ可能な音声アラート
- 一時的な不在時間延長機能
- WebSocket経由のリアルタイム通知

### 4. インタラクティブモニタリング
- フルスクリーム対応のリアルタイムビデオフィード
- 検出状態のリアルタイム表示
- 直感的なステータス表示
- カスタマイズ可能な表示設定

## セットアップ

### バックエンドのセットアップ
1. 依存パッケージのインストール
```bash
cd backend
pip install -r requirements.txt
```

2. サーバーの起動
```bash
python -m backend.src.main
```

### フロントエンドのセットアップ
1. 依存パッケージのインストール
```bash
cd frontend
npm install
```

2. 開発サーバーの起動
```bash
npm run dev
```

## 設定ガイド

### アラート設定
`backend/src/config/message_settings.py`
- アラート音声の設定
  ```python
  {
      "不在警告": "alert.wav",
      "スマートフォン警告": "smartphone_alert.wav"
  }
  ```
- 不在時間の延長設定
  ```python
  {
      "お風呂入ってくる": {"extension": 1200},  # 20分延長
      "うんこ": {"extension": 600}              # 10分延長
  }
  ```

### 表示設定
`backend/src/config/display_settings.py`
- ランドマーク表示のカスタマイズ
  ```python
  {
      "pose": {
          "enabled": True,
          "color": (0, 255, 0),
          "thickness": 2
      }
  }
  ```
- 検出対象の設定
  ```python
  {
      "smartphone": {
          "enabled": True,
          "confidence_threshold": 0.5,
          "alert_threshold": 3
      }
  }
  ```

## 注意事項

### 必要な権限
- ✅ カメラへのアクセス権限
- ✅ 音声出力デバイスへのアクセス権限

### 初回起動時
- 📥 YOLOv8モデル（約100MB）が自動ダウンロードされます
- ⚠️ ダウンロード中は検出機能が一時的に制限されます

### プラットフォーム固有の注意点
- 🍎 macOS: `playsound`パッケージが必要
- 🪟 Windows: `winsound`モジュールを使用
- 🐧 Linux: 追加の音声ドライバが必要な場合あり

## ライセンス

本プロジェクトは[MIT License](LICENSE)の下で公開されています。
- ✅ 商用利用可能
- ✅ 改変・再配布可能
- ✅ 著作権表示必要

## 開発者ガイド

### テスト実行
```bash
# 全テストの実行
python -m pytest tests/

# 特定のテストの実行
python -m pytest tests/test_detector.py
```

### コード品質管理
- 📝 コードフォーマット
  ```bash
  black backend/src
  ```
- 🔍 静的解析
  ```bash
  flake8 backend/src
  ```

### 新機能の追加手順
1. 設定ファイルの更新
   - 必要なパラメータの追加
   - デフォルト値の設定
2. サービスクラスの実装
   - インターフェースの定義
   - ユニットテストの作成
3. フロントエンド対応
   - コンポーネントの作成
   - API連携の実装
4. テストとドキュメントの更新
   - 結合テストの追加
   - READMEの更新
