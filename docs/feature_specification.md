# KanshiChan - 機能仕様書

## 概要
本文書は、KanshiChan（監視ちゃん）プロジェクトのバックエンドが提供する全機能の詳細仕様について記述します。

**更新日**: 2024年12月  
**バージョン**: 2.0  
**対象**: backend/ 全機能  

## 目次
1. [AI検出・分析機能](#ai検出分析機能)
2. [監視・状態管理機能](#監視状態管理機能)
3. [アラート・通知機能](#アラート通知機能)
4. [Web API・通信機能](#web-api通信機能)
5. [設定・構成管理機能](#設定構成管理機能)
6. [パフォーマンス最適化機能](#パフォーマンス最適化機能)
7. [スケジュール管理機能](#スケジュール管理機能)
8. [ログ・例外処理機能](#ログ例外処理機能)

---

## AI検出・分析機能

### 1. 物体検出エンジン（object_detector.py）
**目的**: MediaPipe + YOLOv8による高精度物体検出

#### 主要機能
- **YOLOv8物体検出**: 
  - スマートフォン、ノートPC、本の検出
  - 信頼度閾値による精度調整（デフォルト: 0.5）
  - リアルタイム推論処理
  - GPU/CPU自動切り替え

- **MediaPipe統合検出**:
  - 顔ランドマーク検出（468点）
  - 手部ランドマーク検出（21点×2手）
  - 姿勢ランドマーク検出（33点）
  - 設定可能な検出信頼度

#### 技術仕様
```python
class ObjectDetector:
    def detect_objects(self, frame: np.ndarray) -> Dict[str, Any]
    def get_detection_status(self) -> Dict[str, Any]
    def update_settings(self, settings: Dict[str, Any]) -> bool
```

#### パフォーマンス
- **処理時間**: 平均 45-60ms/フレーム
- **メモリ使用量**: 約800-1200MB
- **対応解像度**: 640x480 〜 1920x1080

### 2. 検出結果描画エンジン（detection_renderer.py）
**目的**: 検出結果の視覚的表示とオーバーレイ

#### 主要機能
- **バウンディングボックス描画**: 検出物体の枠線表示
- **ランドマーク描画**: MediaPipe検出点の描画
- **信頼度表示**: 検出精度の数値表示
- **カスタム色・厚さ設定**: 設定ファイルによる描画スタイル調整

#### 描画設定例
```yaml
detection_objects:
  smartphone:
    color: [255, 0, 0]  # 赤色
    thickness: 2
    name: "スマートフォン"
```

### 3. AI処理最適化エンジン（ai_optimizer.py）
**目的**: AI処理の動的最適化によるパフォーマンス向上

#### 主要機能
- **フレームスキップ制御**: 
  - 動的スキップ率調整（1-5フレーム）
  - CPU使用率に基づく自動調整
  - 目標FPS維持（15 FPS）

- **バッチ処理最適化**:
  - 複数フレームの一括処理
  - バッチサイズ動的調整（1-4フレーム）
  - タイムアウト制御（50ms）

#### 最適化アルゴリズム
```python
# フレームスキップ率の動的調整
if current_fps < target_fps:
    skip_rate = min(skip_rate + 1, max_skip_rate)
elif current_fps > target_fps * 1.2:
    skip_rate = max(skip_rate - 1, 1)
```

---

## 監視・状態管理機能

### 1. 監視制御エンジン（monitor.py）
**目的**: リアルタイム監視とイベント検出の中核制御

#### 主要機能
- **リアルタイム監視ループ**: 
  - 30FPS映像処理
  - AI検出結果の統合分析
  - 状態変化の検出と通知

- **イベント検出**:
  - 不在状態の検知（閾値: 1800秒）
  - スマートフォン使用検知（閾値: 600秒）
  - 姿勢異常の検知

- **システム制御**:
  - カメラの制御と管理
  - 検出器の初期化と管理
  - クリーンアップ処理

#### 処理フロー
```python
def run(self):
    while self.running:
        frame = self.camera.get_frame()
        detections = self.detector.detect(frame)
        self.state.update(detections)
        self.check_alerts()
        self.broadcast_status()
```

### 2. 状態管理システム（state.py）
**目的**: ユーザーの行動状態の追跡と管理

#### 管理する状態
- **不在状態**: 
  - 人物検出の有無
  - 不在開始時刻の記録
  - 不在継続時間の計算

- **スマートフォン使用状態**:
  - 使用開始時刻の記録
  - 継続使用時間の計算
  - グレースピリオド制御（3秒）

- **アラート状態**:
  - アラート発火状態の管理
  - クールダウン時間の制御
  - 再通知間隔の管理

#### 状態遷移
```python
class StateManager:
    def update_absence_state(self, person_detected: bool)
    def update_smartphone_state(self, phone_detected: bool)
    def get_current_state(self) -> Dict[str, Any]
```

### 3. フレーム処理エンジン（frame_processor.py）
**目的**: カメラフレームの前処理と最適化

#### 主要機能
- **フレーム前処理**: リサイズ、色空間変換、正規化
- **品質調整**: ブライトネス、コントラスト調整
- **フォーマット変換**: OpenCV ↔ PIL ↔ numpy変換
- **メモリ最適化**: フレームデータの効率的管理

---

## アラート・通知機能

### 1. アラート統合管理（alert_manager.py）
**目的**: 複数のアラート手段の統合管理

#### 主要機能
- **アラート配信制御**: 音声、LINE通知の統合配信
- **重複防止**: 同一アラートの重複配信防止
- **優先度制御**: アラートタイプによる優先度管理
- **配信履歴管理**: アラート送信履歴の記録

### 2. 音声アラートサービス（sound_service.py）
**目的**: アラート音声の再生制御

#### 主要機能
- **音声ファイル管理**: WAVファイルの読み込みと管理
- **非同期再生**: ブロッキングしない音声再生
- **音量制御**: システム音量の調整
- **エラーハンドリング**: 音声デバイスエラーの処理

#### 対応音声ファイル
```
sounds/
├── alert.wav              # 基本アラート音 (204KB)
├── alert_absence.wav      # 不在アラート音 (54KB)  
├── alert_smartphone.wav   # スマホ使用アラート音 (834KB)
```

### 3. LINE通知サービス（line_service.py）
**目的**: LINE Notifyによる外部通知

#### 主要機能
- **メッセージ送信**: 定型・カスタムメッセージ送信
- **離席時間延長**: LINEメッセージによる監視一時停止
- **設定管理**: トークン、ユーザーID管理
- **エラーリトライ**: 送信失敗時の再送制御

#### 設定項目
```yaml
line:
  enabled: true
  token: "LINE_NOTIFY_TOKEN"
  user_id: "LINE_USER_ID"
  channel_secret: "CHANNEL_SECRET"
```

### 4. LLM統合サービス（llm_service.py）
**目的**: 大規模言語モデルとの連携

#### 主要機能
- **行動分析**: AI検出結果の自然言語分析
- **インサイト生成**: 使用パターンの分析とアドバイス
- **レポート生成**: 定期的な行動レポート作成
- **自然言語処理**: ユーザー行動の言語化

---

## Web API・通信機能

### 1. Flask Web アプリケーション（app.py）
**目的**: Webサーバーの構成とルーティング

#### 主要機能
- **アプリケーション初期化**: Flask設定とミドルウェア構成
- **CORS設定**: クロスオリジンリクエスト対応
- **WebSocket統合**: Socket.IO統合設定
- **エラーハンドラー**: グローバルエラー処理

### 2. REST API エンドポイント（api.py）
**目的**: HTTP REST APIの提供

#### 提供エンドポイント
- `GET/POST /api/settings`: 設定管理
- `GET /api/video_feed`: 映像ストリーム配信
- `GET/POST /api/schedules`: スケジュール管理
- `DELETE /api/schedules/<id>`: スケジュール削除
- `GET /api/performance`: パフォーマンス統計

### 3. WebSocket 通信（websocket.py）
**目的**: リアルタイム双方向通信

#### イベント配信
- `status_update`: 状態更新通知
- `alert_triggered`: アラート発生通知
- `config_updated`: 設定変更通知
- `performance_update`: パフォーマンス情報更新

### 4. ルートハンドラー（handlers.py）
**目的**: Webルートの制御とリダイレクト処理

---

## 設定・構成管理機能

### 1. 設定管理システム（config_manager.py）
**目的**: アプリケーション設定の一元管理

#### 主要機能
- **設定読み込み**: YAML設定ファイルの解析と読み込み
- **階層設定アクセス**: ドット記法による階層設定アクセス
- **設定検証**: 型チェックと必須項目検証
- **動的設定更新**: ランタイム設定変更と保存
- **デフォルト値管理**: 設定項目のデフォルト値提供

#### 使用例
```python
config_manager = ConfigManager()
config_manager.load()

# 階層設定の取得
threshold = config_manager.get('conditions.absence.threshold_seconds', 1800.0)

# 設定の更新
config_manager.set('detector.use_mediapipe', True)
config_manager.save()
```

### 2. YAML操作ユーティリティ（yaml_utils.py）
**目的**: YAML ファイルの安全な読み書き

#### 主要機能
- **安全な読み込み**: yaml.safe_load使用
- **エンコーディング対応**: UTF-8エンコーディング
- **エラーハンドリング**: YAML構文エラーの処理
- **バックアップ機能**: 設定更新時の自動バックアップ

---

## パフォーマンス最適化機能

### 1. メモリ管理システム（memory_manager.py）
**目的**: メモリ使用量の最適化と管理

#### 主要機能
- **LRUキャッシュ**: 検出結果の効率的キャッシング
- **ガベージコレクション制御**: 
  - 定期的なGC実行（30秒間隔）
  - メモリ使用量監視（80%閾値）
  - 強制GC実行制御

- **メモリ統計**: 
  - リアルタイム使用量監視
  - プロセス別メモリ分析
  - メモリリーク検出

#### メモリ最適化設定
```yaml
memory:
  threshold_percent: 80.0
  gc_interval_seconds: 30.0
  monitor_interval_seconds: 5.0
  cache:
    max_size: 100
    max_memory_mb: 50.0
```

### 2. 閾値管理システム（threshold_manager.py）
**目的**: 動的閾値調整による精度向上

#### 主要機能
- **適応的閾値**: 環境に応じた検出閾値の自動調整
- **学習機能**: 検出パターンの学習と最適化
- **統計分析**: 検出精度の統計的分析
- **閾値履歴**: 調整履歴の記録と分析

### 3. ステータス配信システム（status_broadcaster.py）
**目的**: 効率的なステータス情報配信

#### 主要機能
- **差分配信**: 変更された情報のみ配信
- **配信間隔制御**: 適切な配信頻度の維持
- **クライアント管理**: 接続クライアントの管理
- **配信履歴**: 配信ログの記録

---

## スケジュール管理機能

### 1. スケジュール管理システム（schedule_manager.py）
**目的**: 時間ベースのタスク管理

#### 主要機能
- **スケジュール登録**: 時刻とコンテンツの登録
- **定期チェック**: 現在時刻との照合処理
- **通知配信**: スケジュール到達時の通知
- **永続化**: JSON形式でのデータ保存

#### データ構造
```json
{
  "id": "schedule_001",
  "time": "09:00",
  "content": "朝の勉強時間",
  "enabled": true,
  "created_at": "2024-12-XX 08:00:00"
}
```

### 2. スケジュールチェッカー（schedule_checker.py）
**目的**: スケジュール実行タイミングの監視

#### 主要機能
- **時刻監視**: 1分間隔でのスケジュールチェック
- **実行制御**: 重複実行の防止
- **ログ記録**: 実行履歴の記録
- **エラー処理**: スケジュール実行エラーの処理

---

## ログ・例外処理機能

### 1. ログ管理システム（logger.py）
**目的**: 統一されたログ出力

#### 主要機能
- **構造化ログ**: JSON形式のログ出力
- **ログレベル制御**: DEBUG、INFO、WARNING、ERROR、CRITICAL
- **ファイル出力**: ローテーション機能付きファイル出力
- **フォーマット統一**: タイムスタンプ、モジュール名等の統一フォーマット

#### ログ設定例
```python
import logging
from utils.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Processing started")
logger.error("Error occurred", exc_info=True)
```

### 2. 例外処理システム（exceptions.py）
**目的**: カスタム例外クラスによる詳細エラー処理

#### 定義済み例外クラス（30+）
- **APIError**: API関連エラー
- **ConfigError**: 設定ファイルエラー  
- **ValidationError**: 入力検証エラー
- **InitializationError**: 初期化エラー
- **ScheduleError**: スケジュール処理エラー
- **DetectionError**: AI検出エラー
- **CameraError**: カメラ関連エラー
- **MemoryError**: メモリ管理エラー

#### 例外処理パターン
```python
try:
    result = process_detection(frame)
except DetectionError as e:
    logger.error(f"Detection failed: {e}", exc_info=True)
    return default_result
except Exception as e:
    error = wrap_exception(e, ProcessingError, "Unexpected error")
    logger.critical(f"Critical error: {error}")
    raise
```

---

## カメラ制御機能

### 1. カメラ管理システム（camera.py）
**目的**: カメラデバイスの制御と映像取得

#### 主要機能
- **デバイス検出**: 利用可能カメラの自動検出
- **解像度設定**: 最適解像度の自動選択
- **フレーム取得**: 安定したフレーム供給
- **エラー回復**: カメラ接続エラーの自動回復
- **フォーマット変換**: BGR→RGB色空間変換

#### 対応カメラ
- USB Webカメラ
- 内蔵カメラ
- IP カメラ（将来対応予定）

---

## パフォーマンス指標

### 処理性能
- **フレームレート**: 15+ FPS（最適化時）
- **レスポンス時間**: API 200ms以下
- **メモリ使用量**: 800-1200MB
- **CPU使用率**: 30-60%（AI処理時）

### 可用性
- **稼働時間**: 24時間連続稼働対応
- **エラー回復**: 自動エラー回復機能
- **メモリリーク防止**: 定期的メモリクリーンアップ

### スケーラビリティ  
- **同時接続**: WebSocket 10接続まで
- **設定項目**: 100+ 設定項目対応
- **ログ容量**: 日次ローテーション対応

---

**注記**: 本機能仕様書は [backend_rules.yaml](../project_rules/backend_rules.yaml) の規約に準拠しています。 