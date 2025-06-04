# KanshiChan - バックエンドセットアップ・運用ガイド

## 概要
本文書は、KanshiChan（監視ちゃん）バックエンドのセットアップ、設定、運用に関する詳細ガイドです。

**更新日**: 2024年12月  
**バージョン**: 2.0  
**対象**: Python/Flask バックエンド  

## 目次
1. [システム要件](#システム要件)
2. [インストール手順](#インストール手順)
3. [設定ファイル詳細](#設定ファイル詳細)
4. [起動・停止手順](#起動停止手順)
5. [運用・監視](#運用監視)
6. [トラブルシューティング](#トラブルシューティング)
7. [パフォーマンス最適化](#パフォーマンス最適化)
8. [バックアップ・復旧](#バックアップ復旧)

---

## システム要件

### ハードウェア要件
| 項目 | 最小要件 | 推奨要件 |
|------|----------|----------|
| **CPU** | Intel Core i3 / AMD Ryzen 3 | Intel Core i5 / AMD Ryzen 5 以上 |
| **メモリ** | 4GB RAM | 8GB RAM 以上 |
| **ストレージ** | 5GB 空き容量 | 10GB 空き容量 |
| **GPU** | なし（CPU推論） | NVIDIA GPU（CUDA対応）|
| **カメラ** | USB 2.0 Webカメラ | USB 3.0 以上 / 1080p対応 |

### ソフトウェア要件
| 項目 | バージョン | 備考 |
|------|------------|------|
| **Python** | 3.9+ | 3.11 推奨 |
| **pip** | 21.0+ | 最新版推奨 |
| **OpenCV** | 4.11+ | システムレベルインストール推奨 |
| **OS** | Windows 10+, macOS 10.15+, Ubuntu 18.04+ | |

---

## インストール手順

### 1. 環境準備

#### Python仮想環境の作成
```bash
# プロジェクトディレクトリに移動
cd KanshiChan

# Python仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

#### 依存パッケージのインストール
```bash
# 最新のpipに更新
pip install --upgrade pip

# 依存パッケージのインストール（104パッケージ）
pip install -r requirements.txt

# インストール確認
pip list | grep -E "(torch|opencv|mediapipe|ultralytics|flask)"
```

### 2. 必要ファイルの確認
```bash
# バックエンドディレクトリ構造の確認
cd backend
tree -L 3  # または ls -la で確認

# 必須ファイルの存在確認
ls -la src/config/config.yaml
ls -la src/config/schedules.json
ls -la yolov8n.pt  # YOLOモデルファイル（自動ダウンロード）
```

### 3. 初期設定

#### 設定ファイルのカスタマイズ
```bash
# 設定ファイルのバックアップ
cp src/config/config.yaml src/config/config.yaml.backup

# 設定ファイルの編集
nano src/config/config.yaml  # または任意のエディタ
```

#### カメラテスト
```bash
# カメラ接続確認
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK:', cap.isOpened()); cap.release()"
```

#### GPU利用可能性確認
```bash
# PyTorch GPU確認
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# MediaPipe GPU確認
python -c "import mediapipe as mp; print('MediaPipe installed successfully')"
```

---

## 設定ファイル詳細

### config.yaml 設定項目

#### 1. AI検出設定
```yaml
# AI検出エンジンの有効/無効
detector:
  use_mediapipe: true      # MediaPipe使用フラグ
  use_yolo: true          # YOLO使用フラグ

# 検出対象物体の設定
detection_objects:
  smartphone:
    enabled: true          # 検出有効フラグ
    confidence_threshold: 0.5  # 信頼度閾値（0.0-1.0）
    alert_threshold: 3.0   # アラート発火閾値（秒）
    alert_message: "スマホばかり触っていないで勉強をしろ！"
    alert_sound: "smartphone_alert.wav"
    color: [255, 0, 0]     # RGB描画色
    thickness: 2           # 描画線の太さ
```

#### 2. ランドマーク検出設定
```yaml
landmark_settings:
  pose:
    enabled: true          # 姿勢検出有効フラグ
    name: "姿勢"
    color: [0, 255, 0]     # RGB描画色
    thickness: 2
  hands:
    enabled: true          # 手検出有効フラグ
    name: "手"
    color: [0, 0, 255]
    thickness: 2
  face:
    enabled: false         # 顔検出有効フラグ
    name: "顔"
    color: [255, 0, 0]
    thickness: 2
```

#### 3. 状態判定設定
```yaml
conditions:
  absence:
    threshold_seconds: 1800.0    # 不在判定閾値（30分）
  smartphone_usage:
    threshold_seconds: 600.0     # スマホ使用判定閾値（10分）
    grace_period_seconds: 3.0    # グレースピリオド（3秒）
```

#### 4. パフォーマンス最適化設定
```yaml
optimization:
  target_fps: 15.0              # 目標FPS
  min_fps: 5.0                  # 最小FPS
  max_skip_rate: 5              # 最大フレームスキップ率
  batch_processing:
    enabled: false              # バッチ処理有効フラグ
    batch_size: 4               # バッチサイズ
    timeout_ms: 50              # タイムアウト時間

memory:
  threshold_percent: 80.0       # メモリ使用量閾値（80%）
  gc_interval_seconds: 30.0     # GC実行間隔（30秒）
  monitor_interval_seconds: 5.0 # 監視間隔（5秒）
  cache:
    max_size: 100               # キャッシュ最大サイズ
    max_memory_mb: 50.0         # キャッシュ最大メモリ使用量
```

#### 5. 外部サービス設定
```yaml
# LINE Notify設定
line:
  enabled: true
  token: "YOUR_LINE_NOTIFY_TOKEN"
  user_id: "YOUR_LINE_USER_ID"
  channel_secret: "YOUR_CHANNEL_SECRET"

# LLM連携設定
llm:
  enabled: false
  model_name: "huggingface.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:latest"
  analysis_interval_seconds: 300
  temperature: 0.7

# サーバー設定
server:
  port: 5001
```

### schedules.json 設定項目
```json
[
  {
    "id": "morning_study",
    "time": "09:00",
    "content": "朝の勉強時間",
    "enabled": true
  }
]
```

---

## 起動・停止手順

### 開発環境での起動

#### 1. 手動起動
```bash
# バックエンドディレクトリに移動
cd backend

# 仮想環境の有効化
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate.bat  # Windows

# アプリケーション起動
python src/main.py
```

#### 2. 起動確認
```bash
# サーバー起動確認
curl http://localhost:5001/api/settings

# ログ出力確認
tail -f logs/kanshichan.log  # ログファイルが作成される場合
```

### 本番環境での起動

#### 1. systemd サービス（Linux）
```ini
# /etc/systemd/system/kanshichan.service
[Unit]
Description=KanshiChan Backend Service
After=network.target

[Service]
Type=simple
User=kanshichan
WorkingDirectory=/opt/kanshichan/backend
Environment=PATH=/opt/kanshichan/venv/bin
ExecStart=/opt/kanshichan/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# サービス有効化と起動
sudo systemctl enable kanshichan
sudo systemctl start kanshichan

# 状態確認
sudo systemctl status kanshichan
```

#### 2. プロセス管理（PM2）
```bash
# PM2インストール
npm install -g pm2

# PM2設定ファイル作成
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'kanshichan-backend',
    script: 'src/main.py',
    interpreter: 'python',
    cwd: './backend',
    env: {
      PYTHONPATH: '.'
    },
    max_restarts: 3,
    min_uptime: '10s'
  }]
}
EOF

# 起動
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 停止手順
```bash
# 開発環境
Ctrl + C  # プロセス停止

# systemd
sudo systemctl stop kanshichan

# PM2
pm2 stop kanshichan-backend
```

---

## 運用・監視

### 1. ログ監視

#### ログファイルの場所
```bash
# アプリケーションログ（標準出力）
journalctl -u kanshichan -f  # systemd使用時

# エラーログ
grep ERROR /var/log/kanshichan/error.log
```

#### 重要なログパターン
```bash
# 起動成功
grep "Flask サーバーを起動します" logs/

# AI検出エラー
grep "Detection failed" logs/

# メモリ不足警告
grep "Memory usage" logs/

# カメラエラー
grep "Camera error" logs/
```

### 2. パフォーマンス監視

#### リアルタイム監視
```bash
# CPU・メモリ使用量
top -p $(pgrep -f "python.*main.py")

# ネットワーク使用量
netstat -i

# ディスク使用量
df -h

# APIレスポンス時間
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5001/api/performance
```

#### curl-format.txt
```
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
```

### 3. ヘルスチェック

#### 基本ヘルスチェック
```bash
#!/bin/bash
# health_check.sh

API_URL="http://localhost:5001/api/settings"
TIMEOUT=10

if curl -f -s --max-time $TIMEOUT $API_URL > /dev/null; then
    echo "✅ Backend is healthy"
    exit 0
else
    echo "❌ Backend is not responding"
    exit 1
fi
```

#### 詳細ヘルスチェック
```python
# health_check.py
import requests
import json
import sys

def check_backend_health():
    try:
        # API応答確認
        response = requests.get('http://localhost:5001/api/performance', timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # パフォーマンス指標確認
            fps = data.get('fps', 0)
            memory_mb = data.get('memory_mb', 0)
            
            if fps < 5:
                print(f"⚠️  Low FPS: {fps}")
                return False
                
            if memory_mb > 2000:
                print(f"⚠️  High memory usage: {memory_mb}MB")
                return False
                
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    if not check_backend_health():
        sys.exit(1)
```

---

## トラブルシューティング

### 1. 起動時エラー

#### カメラアクセスエラー
```bash
# 症状: "Camera not found" エラー
# 解決策:
lsusb  # USB デバイス確認
ls /dev/video*  # ビデオデバイス確認

# カメラ権限確認
sudo usermod -a -G video $USER
```

#### ポート使用中エラー
```bash
# 症状: "Port 5001 is already in use"
# 解決策:
lsof -i :5001  # ポート使用プロセス確認
kill -9 <PID>  # プロセス終了

# または設定変更
# config.yamlで別ポート指定
server:
  port: 5002
```

#### 依存パッケージエラー
```bash
# 症状: モジュールインポートエラー
# 解決策:
pip install --force-reinstall torch torchvision
pip install --force-reinstall opencv-python
pip install --force-reinstall mediapipe
```

### 2. 実行時エラー

#### GPU メモリ不足
```bash
# 症状: "CUDA out of memory"
# 解決策: CPU推論に切り替え
export CUDA_VISIBLE_DEVICES=""

# または設定ファイルでバッチサイズ削減
optimization:
  batch_processing:
    batch_size: 1
```

#### メモリリーク
```bash
# 症状: メモリ使用量が増加し続ける
# 解決策: GC間隔短縮
memory:
  gc_interval_seconds: 10.0  # デフォルト30秒から短縮
```

#### フレームレート低下
```bash
# 症状: FPS が目標値を下回る
# 解決策: 最適化設定調整
optimization:
  target_fps: 10.0           # 目標FPS低下
  max_skip_rate: 10          # スキップ率増加
```

### 3. 設定関連エラー

#### 設定ファイル読み込みエラー
```bash
# 症状: "Config file not found"
# 解決策:
ls -la src/config/config.yaml  # ファイル存在確認

# ファイル復元
cp src/config/config.yaml.backup src/config/config.yaml
```

#### LINE 通知エラー
```bash
# 症状: LINE通知が送信されない
# 解決策: トークン確認
curl -X POST https://notify-api.line.me/api/notify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "message=Test"
```

---

## パフォーマンス最適化

### 1. AI処理最適化

#### GPU利用最適化
```python
# CUDA最適化設定
export CUDA_LAUNCH_BLOCKING=1
export TORCH_CUDA_ARCH_LIST="7.0;7.5;8.0;8.6"
```

#### モデル量子化
```python
# YOLOv8 量子化（設定例）
# config.yamlで量子化モデル指定
detector:
  model_path: "yolov8n-quantized.onnx"
```

### 2. メモリ最適化

#### キャッシュ設定調整
```yaml
memory:
  cache:
    max_size: 50              # キャッシュサイズ削減
    max_memory_mb: 25.0       # メモリ使用量制限
```

#### ガベージコレクション最適化
```yaml
memory:
  gc_interval_seconds: 15.0   # GC頻度増加
  threshold_percent: 70.0     # メモリ閾値低下
```

### 3. ネットワーク最適化

#### WebSocket設定
```python
# 大容量データの送信最適化
socketio_config = {
    'ping_timeout': 60,
    'ping_interval': 25,
    'max_http_buffer_size': 10000000  # 10MB
}
```

---

## バックアップ・復旧

### 1. 設定ファイルバックアップ

#### 自動バックアップスクリプト
```bash
#!/bin/bash
# backup_config.sh

BACKUP_DIR="/backup/kanshichan/$(date +%Y%m%d)"
CONFIG_DIR="backend/src/config"

mkdir -p $BACKUP_DIR

# 設定ファイルバックアップ
cp $CONFIG_DIR/config.yaml $BACKUP_DIR/
cp $CONFIG_DIR/schedules.json $BACKUP_DIR/

# 圧縮
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR/
rm -rf $BACKUP_DIR

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

#### crontab設定
```bash
# 毎日午前2時にバックアップ実行
0 2 * * * /path/to/backup_config.sh
```

### 2. データベース・ログバックアップ

#### ログローテーション
```bash
# logrotate設定
/var/log/kanshichan/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 644 kanshichan kanshichan
}
```

### 3. 復旧手順

#### 設定復旧
```bash
# バックアップファイル展開
tar -xzf backup_20241201.tar.gz

# 設定復旧
cp backup_20241201/config.yaml backend/src/config/
cp backup_20241201/schedules.json backend/src/config/

# サービス再起動
sudo systemctl restart kanshichan
```

---

## 運用チェックリスト

### 日次確認項目
- [ ] サービス起動状態確認
- [ ] エラーログチェック
- [ ] メモリ使用量確認
- [ ] FPS パフォーマンス確認
- [ ] ディスク容量確認

### 週次確認項目
- [ ] ログローテーション実行
- [ ] 設定バックアップ確認
- [ ] パフォーマンス統計レビュー
- [ ] セキュリティアップデート確認

### 月次確認項目
- [ ] 依存パッケージ更新チェック
- [ ] 設定最適化見直し
- [ ] 容量プランニング
- [ ] 災害復旧テスト

---

**注記**: 本運用ガイドは [backend_rules.yaml](../project_rules/backend_rules.yaml) の規約に準拠しています。 