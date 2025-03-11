# KanshiChan (監視ちゃん)

## 概要
KanshiChan（監視ちゃん）は、Pythonベースの監視システムで、カメラを使用して人物の不在や不適切な行動（スマートフォンの使用など）を検出し、アラートを発します。主に学習や作業の環境を監視・管理するためのツールとして設計されています。

## 使用技術
- **言語**: Python
- **画像処理・物体検出**: OpenCV, YOLO v8, MediaPipe
- **機械学習フレームワーク**: PyTorch
- **Webフレームワーク**: Flask
- **通知サービス**: LINE Messaging API, Twilio
- **音声再生**: playsound (macOS/Linux), winsound (Windows)
- **その他ライブラリ**: Pillow, PyYAML, screeninfo

## ディレクトリ構成
```
KanshiChan/
├── .kanshichan/         # アプリケーションデータディレクトリ
├── src/                 # ソースコード
│   └── kanshichan/      # メインパッケージ
│       ├── config/      # 設定ファイル
│       ├── core/        # コア機能
│       │   ├── camera.py        # カメラ管理
│       │   ├── detector.py      # 検出アルゴリズム
│       │   └── monitor.py       # 監視メインロジック
│       ├── services/    # 各種サービス
│       │   ├── alert_service.py    # アラート統合サービス
│       │   ├── line_service.py     # LINE通知
│       │   ├── sound_service.py    # 音声アラート
│       │   └── twilio_service.py   # Twilio SMS通知
│       ├── sounds/      # 音声ファイル
│       ├── utils/       # ユーティリティ
│       ├── web/         # Webインターフェース
│       │   ├── app.py           # Flaskアプリケーション
│       │   └── handlers.py      # Webハンドラー
│       ├── __init__.py
│       └── main.py      # アプリケーションエントリーポイント
├── tests/               # テストコード
├── requirements.txt     # 依存ライブラリ
├── setup.py             # パッケージングスクリプト
└── yolov8n.pt           # YOLOv8モデルファイル
```

## 主要機能
### 1. 人物検出/不在検知
- カメラを使って人物の存在を検出し、指定された時間（デフォルト5秒）以上不在の場合にアラートを発します
- LINE通知やサウンドアラートでユーザーに警告します

### 2. スマートフォン使用検知
- 人物がスマートフォンを使用している場合に検出
- 指定された時間以上の使用でアラートを発します

### 3. LINE連携
- LINEメッセージによる遠隔操作
- 予め設定されたメッセージ（「お風呂入ってくる」など）に応じて不在閾値を自動調整
- 音声確認応答でコマンド受信を通知

### 4. Webインターフェース
- Flask製のWebアプリケーションでシステム状態を確認・制御
- LINEボットのWebhookエンドポイントを提供

## インストール方法
### 1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/KanshiChan.git
cd KanshiChan
```

### 2. 依存関係のインストール
```bash
pip install -e .
```
または
```bash
pip install -r requirements.txt
```

### 3. 設定ファイルの作成
`src/kanshichan/config/config.yaml` に以下の内容を参考に設定ファイルを作成してください：

```yaml
camera:
  source: 0  # カメラのソース（通常はデフォルトカメラの場合0）

detection:
  confidence_threshold: 0.5

conditions:
  absence:
    threshold_seconds: 5  # 不在と判断するまでの秒数
  smartphone_usage:
    threshold_seconds: 3  # スマホ使用と判断するまでの秒数

line:
  channel_secret: "YOUR_LINE_CHANNEL_SECRET"
  token: "YOUR_LINE_CHANNEL_ACCESS_TOKEN"
```

## 使用方法
### アプリケーションの起動
```bash
python -m src.kanshichan.main
```

### LINEボットの設定
1. LINE Developersでチャネルを作成
2. Messaging APIの設定
3. Webhook URLを設定（例：`https://your-domain/webhook`）
4. チャネルシークレットとアクセストークンを設定ファイルに追加

### LINE経由での操作
以下のメッセージを送信することで、不在時間の閾値を自動調整できます：
- 「お風呂入ってくる」：20分（1200秒）延長
- 「買い物行ってくる」：20分（1200秒）延長
- 「料理しなきゃ」：20分（1200秒）延長
- 「散歩してくる」：20分（1200秒）延長
- 「うんこ」：10分（600秒）延長
- 「とりあえず離席」：10分（600秒）延長

## トラブルシューティング
- カメラが見つからない場合、設定ファイルのカメラソースを確認してください
- 音声が再生されない場合、OSに適したライブラリがインストールされているか確認してください
- LINEメッセージが送信されない場合、トークンと設定を確認してください

## 開発情報
- YOLOv8モデルを使用して物体検出を行っています
- MediaPipeを使用して人物の姿勢推定を行っています
- マルチスレッドで通知とアラートを処理しています
