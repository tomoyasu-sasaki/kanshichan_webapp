# フロントエンド API 通信仕様書

## 概要
KanshiChan フロントエンドアプリケーションのAPI通信に関する仕様書です。WebSocket通信、HTTP通信、エラーハンドリングについて定義します。

## 通信方式

### 1. WebSocket通信（リアルタイム）
**用途**: リアルタイムデータ更新、双方向通信

- **ライブラリ**: Socket.IO Client 4.8.1
- **エンドポイント**: `http://localhost:5001`
- **プロトコル**: WebSocket
- **接続管理**: シングルトンパターン

### 2. HTTP通信（設定・管理）
**用途**: 設定の保存・読み込み、ファイル操作

- **ライブラリ**: Axios 1.8.2
- **ベースURL**: `http://localhost:5001/api`
- **プロキシ**: Vite開発サーバーによるプロキシ設定

---

## WebSocket通信仕様

### 接続管理クラス: WebSocketManager

#### シングルトンパターン実装
```typescript
class WebSocketManager {
  private static instance: WebSocketManager;
  private socket: Socket | null = null;
  
  public static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }
}
```

#### 接続設定
```typescript
const socket = io('http://localhost:5001', {
  transports: ['websocket'],
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000
});
```

### 受信イベント

#### 1. status_update
**用途**: 検出ステータスのリアルタイム更新

```typescript
interface DetectionStatus {
  personDetected: boolean;        // 人物検出状態
  smartphoneDetected: boolean;    // スマートフォン検出状態
  absenceTime: number;           // 不在時間（秒）
  smartphoneUseTime: number;     // スマートフォン使用時間（秒）
  absenceAlert?: boolean;        // 不在アラート状態
  smartphoneAlert?: boolean;     // スマートフォンアラート状態
}
```

**サンプルデータ**:
```json
{
  "personDetected": false,
  "smartphoneDetected": false,
  "absenceTime": 125.5,
  "smartphoneUseTime": 0,
  "absenceAlert": true,
  "smartphoneAlert": false
}
```

#### 2. schedule_alert
**用途**: スケジュールベースのアラート通知

```typescript
interface ScheduleAlert {
  type: 'schedule_alert';
  content: string;               // アラート内容
  time: string;                  // 実行時刻
}
```

**サンプルデータ**:
```json
{
  "type": "schedule_alert",
  "content": "会議の時間です",
  "time": "14:00"
}
```

#### 3. 接続関連イベント
- **connect**: WebSocket接続成功
- **disconnect**: WebSocket接続断
- **connect_error**: 接続エラー

### イベントリスナー管理

#### リスナー登録
```typescript
// ステータス更新リスナー
const unsubscribe = websocketManager.onStatusUpdate((status) => {
  setStatus(status);
});

// エラーリスナー
const errorUnsubscribe = websocketManager.onError((error) => {
  toast({
    title: '接続エラー',
    description: 'サーバーとの接続に失敗しました',
    status: 'error',
    duration: 3000,
    isClosable: true,
  });
});
```

#### リスナー解除
```typescript
useEffect(() => {
  // リスナー登録
  const unsubscribe = websocketManager.onStatusUpdate(handleStatusUpdate);
  
  // クリーンアップ
  return () => {
    unsubscribe();
  };
}, []);
```

---

## HTTP通信仕様

### ベース設定

#### Viteプロキシ設定
```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
});
```

#### Axios設定（将来実装）
```typescript
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### API エンドポイント

#### 1. 設定管理API（将来実装）

##### GET /api/settings
**用途**: 現在の設定を取得

**レスポンス**:
```json
{
  "status": "success",
  "data": {
    "detection": {
      "personThreshold": 0.5,
      "smartphoneThreshold": 0.7
    },
    "alerts": {
      "enableAlerts": true,
      "absenceAlertTime": 300,
      "smartphoneAlertTime": 600
    },
    "ui": {
      "language": "ja",
      "theme": "light"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

##### POST /api/settings
**用途**: 設定を保存

**リクエスト**:
```json
{
  "detection": {
    "personThreshold": 0.6,
    "smartphoneThreshold": 0.8
  },
  "alerts": {
    "enableAlerts": false,
    "absenceAlertTime": 240,
    "smartphoneAlertTime": 480
  }
}
```

**レスポンス**:
```json
{
  "status": "success",
  "message": "設定が保存されました",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 2. スケジュール管理API（将来実装）

##### GET /api/schedules
**用途**: スケジュール一覧を取得

**レスポンス**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "1",
      "title": "朝会",
      "time": "09:00",
      "message": "朝会の時間です",
      "enabled": true,
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
    }
  ]
}
```

##### POST /api/schedules
**用途**: 新しいスケジュールを追加

##### PUT /api/schedules/:id
**用途**: スケジュールを更新

##### DELETE /api/schedules/:id
**用途**: スケジュールを削除

#### 3. ビデオストリームAPI

##### GET /api/video_feed
**用途**: MJPEGビデオストリーム

**特徴**:
- Content-Type: `multipart/x-mixed-replace`
- リアルタイムストリーミング
- フロントエンドでは`<img>`タグのsrcに直接指定

**実装例**:
```typescript
useEffect(() => {
  if (videoRef.current) {
    videoRef.current.src = 'http://localhost:5001/api/video_feed';
  }
}, []);
```

---

## エラーハンドリング

### WebSocketエラー

#### 接続エラー
```typescript
websocketManager.onError((error) => {
  console.error('WebSocket error:', error);
  
  // ユーザーへの通知
  toast({
    title: '接続エラー',
    description: 'サーバーとの接続に失敗しました',
    status: 'error',
    duration: 5000,
    isClosable: true,
  });
});
```

#### 再接続ロジック
```typescript
// Socket.IOの自動再接続設定
const socket = io(url, {
  reconnection: true,           // 自動再接続有効
  reconnectionAttempts: 5,      // 最大再試行回数
  reconnectionDelay: 1000,      // 再試行間隔（ms）
  reconnectionDelayMax: 5000,   // 最大再試行間隔
});
```

### HTTPエラー（将来実装）

#### エラーレスポンス形式
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が無効です",
    "details": {
      "field": "personThreshold",
      "reason": "値は0.0から1.0の間である必要があります"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### エラーハンドリング実装
```typescript
const handleApiError = (error: AxiosError) => {
  if (error.response) {
    // サーバーエラーレスポンス
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        toast({
          title: 'リクエストエラー',
          description: data.error?.message || '無効なリクエストです',
          status: 'error',
        });
        break;
      case 500:
        toast({
          title: 'サーバーエラー',
          description: 'サーバーで問題が発生しました',
          status: 'error',
        });
        break;
      default:
        toast({
          title: 'エラー',
          description: '予期しないエラーが発生しました',
          status: 'error',
        });
    }
  } else if (error.request) {
    // ネットワークエラー
    toast({
      title: 'ネットワークエラー',
      description: 'サーバーに接続できません',
      status: 'error',
    });
  }
};
```

---

## 型定義

### 共通型定義
```typescript
// API レスポンス基本形
export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

// WebSocketイベント型
export interface WebSocketEvents {
  status_update: DetectionStatus;
  schedule_alert: ScheduleAlert;
  connect: void;
  disconnect: void;
  connect_error: Error;
}

// 設定型
export interface AppSettings {
  detection: {
    personThreshold: number;
    smartphoneThreshold: number;
  };
  alerts: {
    enableAlerts: boolean;
    absenceAlertTime: number;
    smartphoneAlertTime: number;
  };
  ui: {
    language: string;
    theme: string;
  };
}
```

---

## セキュリティ考慮事項

### CORS設定
- 開発環境：Viteプロキシによる回避
- 本番環境：適切なCORS設定が必要

### データ検証
- フロントエンドでの入力値検証
- TypeScriptによる型安全性
- バックエンドでの再検証

### 認証・認可（将来実装）
- JWTトークンベース認証
- リフレッシュトークン対応
- セッション管理

---

## パフォーマンス最適化

### WebSocket最適化
- 接続プールの効率的な利用
- 不要なイベントリスナーの適切な解除
- メモリリーク防止

### HTTP通信最適化
- リクエストキャッシュ
- 適切なタイムアウト設定
- レスポンスサイズの最適化

### データ管理
- 状態更新の最適化
- 不要な再レンダリング防止
- メモ化による計算結果キャッシュ

---

## 開発・テスト

### モック実装
```typescript
// WebSocketモック（テスト用）
const mockWebSocketManager = {
  initialize: jest.fn(),
  onStatusUpdate: jest.fn((callback) => {
    callback({
      personDetected: true,
      smartphoneDetected: false,
      absenceTime: 0,
      smartphoneUseTime: 0,
    });
    return jest.fn(); // unsubscribe function
  }),
  onError: jest.fn(() => jest.fn()),
};
```

### APIテスト
- WebSocket通信のモック
- HTTP通信のモック
- エラー状態のテスト
- 接続状態のテスト

## 今後の実装予定

### 機能拡張
- リアルタイムログ表示
- 設定のエクスポート・インポート
- パフォーマンス統計のAPI
- 履歴データの取得

### 技術改善
- Service Worker対応
- オフライン機能
- キャッシュ戦略の実装
- GraphQL導入検討 