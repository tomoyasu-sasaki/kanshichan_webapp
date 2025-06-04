# KanshiChan - API仕様書

## 概要
本文書は、KanshiChan（監視ちゃん）プロジェクトのREST API とWebSocket通信の詳細仕様について記述します。

**更新日**: 2024年12月  
**バージョン**: 2.0  
**ベースURL**: `http://localhost:5001/api`  
**プロトコル**: HTTP/1.1, WebSocket  

## 目次
1. [認証・ヘッダー](#認証ヘッダー)
2. [エラーハンドリング](#エラーハンドリング)
3. [設定管理API](#設定管理api)
4. [映像ストリーミングAPI](#映像ストリーミングapi)
5. [スケジュール管理API](#スケジュール管理api)
6. [パフォーマンス監視API](#パフォーマンス監視api)
7. [WebSocket通信](#websocket通信)
8. [ステータスコード一覧](#ステータスコード一覧)

## 認証・ヘッダー

### リクエストヘッダー
```http
Content-Type: application/json
Accept: application/json
```

### レスポンスヘッダー
```http
Content-Type: application/json; charset=utf-8
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

## エラーハンドリング

### 標準エラーレスポンス形式
```json
{
  "status": "error",
  "error": "Human readable error message",
  "code": "MACHINE_READABLE_ERROR_CODE",
  "timestamp": "2024-12-XX-10:00:00Z",
  "details": {
    "field": "Invalid field information (optional)"
  }
}
```

### 主要エラーコード
| コード | 説明 | HTTPステータス |
|--------|------|----------------|
| `VALIDATION_ERROR` | 入力検証エラー | 400 |
| `CONFIG_ERROR` | 設定ファイルエラー | 500 |
| `INITIALIZATION_ERROR` | 初期化エラー | 500 |
| `SCHEDULE_ERROR` | スケジュール処理エラー | 400/500 |
| `MONITOR_NOT_INITIALIZED` | 監視機能未初期化 | 500 |

---

## 設定管理API

### GET /settings
現在の設定値を取得します。

#### リクエスト
```http
GET /api/settings
```

#### レスポンス
```json
{
  "absence_threshold": 1800.0,
  "smartphone_threshold": 600.0,
  "message_extensions": {
    "うんこ": 600,
    "お風呂入ってくる": 1200,
    "とりあえず離席": 600,
    "散歩してくる": 1200,
    "料理しなきゃ": 1200,
    "買い物行ってくる": 1200
  },
  "landmark_settings": {
    "face": {
      "enabled": false,
      "name": "顔",
      "color": [255, 0, 0],
      "thickness": 2
    },
    "hands": {
      "enabled": true,
      "name": "手",
      "color": [0, 0, 255],
      "thickness": 2
    },
    "pose": {
      "enabled": true,
      "name": "姿勢",
      "color": [0, 255, 0],
      "thickness": 2
    }
  },
  "detection_objects": {
    "smartphone": {
      "enabled": true,
      "name": "スマートフォン",
      "class_name": "cell phone",
      "confidence_threshold": 0.5,
      "alert_threshold": 3.0,
      "alert_message": "スマホばかり触っていないで勉強をしろ！",
      "alert_sound": "smartphone_alert.wav",
      "color": [255, 0, 0],
      "thickness": 2
    },
    "laptop": {
      "enabled": false,
      "name": "ノートパソコン",
      "class_name": "laptop",
      "confidence_threshold": 0.5,
      "alert_threshold": 3.0,
      "alert_message": "ノートパソコンの使用を検知しました",
      "alert_sound": "alert.wav",
      "color": [0, 255, 255],
      "thickness": 2
    },
    "book": {
      "enabled": false,
      "name": "本",
      "class_name": "book",
      "confidence_threshold": 0.5,
      "alert_threshold": 0.0,
      "alert_message": "",
      "alert_sound": "",
      "color": [0, 255, 0],
      "thickness": 2
    }
  }
}
```

### POST /settings
設定値を更新します。

#### リクエスト
```http
POST /api/settings
Content-Type: application/json

{
  "absence_threshold": 1500.0,
  "smartphone_threshold": 300.0,
  "message_extensions": {
    "うんこ": 300
  },
  "landmark_settings": {
    "face": {
      "enabled": true
    }
  },
  "detection_objects": {
    "smartphone": {
      "enabled": false,
      "confidence_threshold": 0.6,
      "alert_threshold": 5.0
    }
  }
}
```

#### レスポンス
```json
{
  "status": "success"
}
```

#### エラーレスポンス例
```json
{
  "status": "error",
  "error": "Invalid value for absence_threshold",
  "code": "VALIDATION_ERROR",
  "details": {
    "value": "invalid_value",
    "expected_type": "float"
  }
}
```

---

## 映像ストリーミングAPI

### GET /video_feed
リアルタイム映像ストリームを配信します。

#### リクエスト
```http
GET /api/video_feed
```

#### レスポンス
```http
Content-Type: multipart/x-mixed-replace; boundary=frame

--frame
Content-Type: image/jpeg

[JPEG画像データ]
--frame
Content-Type: image/jpeg

[JPEG画像データ]
...
```

#### 仕様詳細
- **フレームレート**: 30 FPS
- **画像フォーマット**: JPEG
- **エンコーディング**: Binary
- **境界文字列**: `frame`
- **AI処理**: MediaPipe + YOLOv8による検出結果を重畳表示

#### エラーハンドリング
```http
HTTP/1.1 500 Internal Server Error

Monitor not initialized
```

---

## スケジュール管理API

### GET /schedules
登録されているスケジュール一覧を取得します。

#### リクエスト
```http
GET /api/schedules
```

#### レスポンス
```json
[
  {
    "id": "schedule_001",
    "time": "09:00",
    "content": "朝の勉強時間",
    "enabled": true,
    "created_at": "2024-12-XX 08:00:00"
  },
  {
    "id": "schedule_002",
    "time": "15:00",
    "content": "午後の集中タイム",
    "enabled": true,
    "created_at": "2024-12-XX 08:30:00"
  }
]
```

### POST /schedules
新しいスケジュールを登録します。

#### リクエスト
```http
POST /api/schedules
Content-Type: application/json

{
  "time": "19:00",
  "content": "夜の学習時間"
}
```

#### レスポンス
```json
{
  "id": "schedule_003",
  "time": "19:00",
  "content": "夜の学習時間",
  "enabled": true,
  "created_at": "2024-12-XX 10:15:00"
}
```

#### エラーレスポンス例
```json
{
  "status": "error",
  "error": "Time and content are required",
  "code": "VALIDATION_ERROR"
}
```

### DELETE /schedules/{schedule_id}
指定されたIDのスケジュールを削除します。

#### リクエスト
```http
DELETE /api/schedules/schedule_003
```

#### レスポンス
```http
HTTP/1.1 204 No Content
```

#### エラーレスポンス例
```json
{
  "status": "error",
  "error": "Schedule not found or could not be deleted",
  "code": "SCHEDULE_ERROR"
}
```

---

## パフォーマンス監視API

### GET /performance
システムのパフォーマンス統計情報を取得します。

#### リクエスト
```http
GET /api/performance
```

#### レスポンス
```json
{
  "fps": 15.2,
  "avg_inference_ms": 45.6,
  "memory_mb": 892.3,
  "skip_rate": 2,
  "optimization_active": true,
  "timestamp": "2024-12-XX 10:30:00"
}
```

#### フィールド詳細
| フィールド | 型 | 説明 |
|------------|----|----- |
| `fps` | number | 現在のフレームレート |
| `avg_inference_ms` | number | AI推論の平均処理時間（ミリ秒） |
| `memory_mb` | number | メモリ使用量（MB） |
| `skip_rate` | integer | フレームスキップ率 |
| `optimization_active` | boolean | 最適化機能の有効状態 |

---

## WebSocket通信

### 接続エンドポイント
```
ws://localhost:5001/socket.io/
```

### イベント一覧

#### 1. status_update (サーバー → クライアント)
システム状態の更新通知

```json
{
  "event": "status_update",
  "data": {
    "is_absent": false,
    "smartphone_usage": true,
    "duration": 125.4,
    "detection_status": {
      "mediapipe_active": true,
      "yolo_active": true,
      "last_detection": "2024-12-XX 10:30:00"
    },
    "performance": {
      "fps": 15.2,
      "memory_mb": 892.3
    }
  }
}
```

#### 2. alert_triggered (サーバー → クライアント)
アラート発生通知

```json
{
  "event": "alert_triggered",
  "data": {
    "type": "smartphone_usage",
    "message": "スマホばかり触っていないで勉強をしろ！",
    "duration": 600.0,
    "sound": "smartphone_alert.wav",
    "timestamp": "2024-12-XX 10:30:00"
  }
}
```

#### 3. config_updated (サーバー → クライアント)
設定変更通知

```json
{
  "event": "config_updated",
  "data": {
    "section": "detection_objects",
    "key": "smartphone.enabled",
    "value": false,
    "timestamp": "2024-12-XX 10:30:00"
  }
}
```

#### 4. performance_update (サーバー → クライアント)
パフォーマンス情報の定期更新

```json
{
  "event": "performance_update",
  "data": {
    "fps": 14.8,
    "avg_inference_ms": 47.2,
    "memory_mb": 905.1,
    "skip_rate": 3,
    "optimization_active": true
  }
}
```

---

## ステータスコード一覧

| ステータス | 説明 | 使用エンドポイント |
|------------|------|-------------------|
| `200 OK` | 正常レスポンス | GET /settings, GET /schedules, GET /performance |
| `201 Created` | リソース作成成功 | POST /schedules |
| `204 No Content` | 削除成功 | DELETE /schedules/{id} |
| `400 Bad Request` | リクエスト形式エラー | POST /settings, POST /schedules |
| `404 Not Found` | リソース未発見 | DELETE /schedules/{id} |
| `500 Internal Server Error` | サーバー内部エラー | 全エンドポイント |

## レート制限

現在、レート制限は実装されていませんが、以下の推奨事項があります：

- **設定更新**: 1秒に1回まで
- **パフォーマンス取得**: 1秒に2回まで
- **映像ストリーム**: 同時接続1つまで

## セキュリティ考慮事項

1. **入力検証**: 全ての入力値は型・範囲チェック実施
2. **エラー情報**: 本番環境では詳細エラー情報を制限
3. **CORS**: 開発環境では全オリジン許可（本番では制限推奨）
4. **映像データ**: ローカルネットワーク内のみでの使用を推奨

## 使用例

### JavaScript fetch API
```javascript
// 設定取得
const response = await fetch('http://localhost:5001/api/settings');
const settings = await response.json();

// 設定更新
await fetch('http://localhost:5001/api/settings', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    absence_threshold: 1200.0
  })
});
```

### WebSocket接続
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:5001');

socket.on('status_update', (data) => {
  console.log('Status updated:', data);
});

socket.on('alert_triggered', (data) => {
  console.log('Alert triggered:', data);
});
```

---

**注記**: 本API仕様書は [backend_rules.yaml](../project_rules/backend_rules.yaml) の規約に準拠しています。 