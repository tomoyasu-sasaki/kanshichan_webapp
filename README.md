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
  - MediaPipeによる33点の姿勢ランドマーク検出
  - YOLOv8を使用したスマートフォン等の物体検知
- ⏰ **インテリジェントアラート**
  - 不適切な姿勢の検知と警告
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
│   │   ├── config/             # アプリケーション設定
│   │   │   ├── display.py     # 表示設定
│   │   │   └── alert.py       # アラート設定
│   │   ├── core/              # 検出エンジン
│   │   │   ├── pose.py       # 姿勢検出
│   │   │   └── object.py     # 物体検出
│   │   ├── services/          # ビジネスロジック
│   │   │   ├── monitor.py    # 監視サービス
│   │   │   └── alert.py      # アラートサービス
│   │   ├── web/               # Web API
│   │   │   ├── routes.py     # エンドポイント
│   │   │   └── socket.py     # WebSocket
│   │   └── main.py           # エントリーポイント
│   └── requirements.txt        # 依存パッケージ
│
├── frontend/                    # Reactフロントエンド
│   ├── src/
│   │   ├── components/        # UIコンポーネント
│   │   │   ├── Monitor/      # 監視画面
│   │   │   └── Settings/     # 設定画面
│   │   └── assets/           # 静的リソース
│   └── package.json           # npm設定
│
├── .kanshichan/                # アプリ設定
├── setup.py                    # パッケージ設定
└── yolov8n.pt                  # YOLOモデル
```

## ⚙️ 設定とカスタマイズ
### アラート設定
```python
{
    "不在警告": {
        "sound": "alert.wav",      # 警告音ファイル名
        "threshold": 300,          # 警告までの時間（秒）
        "extensions": {            # 延長オプション
            "休憩": 600,           # 10分延長
            "お昼休み": 3600       # 1時間延長
        }
    },
    "姿勢警告": {
        "sound": "posture.wav",    # 警告音ファイル名
        "threshold": 0.7,          # 検出閾値（0-1）
        "interval": 60             # 警告間隔（秒）
    }
}
```

### 表示設定
```python
{
    "camera": {
        "width": 640,             # カメラ解像度（横）
        "height": 480,            # カメラ解像度（縦）
        "fps": 30                 # フレームレート
    },
    "overlay": {
        "landmarks": True,        # 姿勢ランドマーク表示
        "boxes": True,            # 検出ボックス表示
        "stats": True            # 統計情報表示
    }
}
```

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
