# フロントエンド コンポーネント仕様書

## 概要
KanshiChan フロントエンドアプリケーションの各Reactコンポーネントの仕様と実装詳細を定義した文書です。

## アプリケーション構成

### App.tsx（メインアプリケーション）
**役割**: アプリケーション全体のレイアウトとタブナビゲーション管理

#### 主要機能
- タブベースのナビゲーション（監視・スケジュール・設定）
- 多言語対応（i18next）
- グローバルレイアウト管理

#### Props
なし（ルートコンポーネント）

#### State
- 現在のタブ状態（Chakra UIのTabsで管理）

#### 依存関係
- `@chakra-ui/react`: UI コンポーネント
- `react-i18next`: 国際化

#### コード例
```typescript
function App() {
  const { t } = useTranslation();
  
  return (
    <Container maxW="container.xl" py={4}>
      <Flex mb={4} align="center">
        <Heading size="lg">{t('app.title')}</Heading>
        <Spacer />
        <LanguageSwitcher />
      </Flex>
      <Tabs>
        <TabList>
          <Tab>{t('tabs.monitor')}</Tab>
          <Tab>{t('tabs.schedule')}</Tab>
          <Tab>{t('tabs.settings')}</Tab>
        </TabList>
        <TabPanels>
          <TabPanel px={0}><MonitorView /></TabPanel>
          <TabPanel px={0}><ScheduleView /></TabPanel>
          <TabPanel px={0}><SettingsPanel /></TabPanel>
        </TabPanels>
      </Tabs>
    </Container>
  );
}
```

---

## コンポーネント詳細仕様

### 1. MonitorView.tsx
**役割**: リアルタイム監視画面の表示と制御

#### 主要機能
- MJPEGビデオストリーム表示
- リアルタイム検出ステータス表示
- 全画面表示切り替え
- WebSocket接続管理

#### Props
なし

#### State
```typescript
interface State {
  isFullscreen: boolean;          // 全画面表示状態
  status: DetectionStatus;        // 検出ステータス
}

interface DetectionStatus {
  personDetected: boolean;        // 人物検出状態
  smartphoneDetected: boolean;    // スマートフォン検出状態
  absenceTime: number;           // 不在時間（秒）
  smartphoneUseTime: number;     // スマートフォン使用時間（秒）
}
```

#### 主要メソッド
- `toggleFullscreen()`: 全画面表示切り替え
- WebSocketイベントハンドラー（接続、ステータス更新、エラー）

#### レンダリング要素
- ビデオストリーム表示エリア
- ステータスオーバーレイ（在席状態、検出時間）
- 全画面切り替えボタン

#### WebSocket通信
- エンドポイント: `http://localhost:5001`
- イベント: `status_update`, `connect_error`
- 自動再接続機能

#### スタイリング
- 全画面時: `100vh`
- 通常時: `calc(100vh - 100px)`
- オーバーレイ: 半透明背景、右上配置

---

### 2. SettingsPanel.tsx
**役割**: システム設定の管理と保存

#### 主要機能
- 検出設定の調整
- アラート設定の管理
- 設定の保存・復元
- リアルタイム設定反映

#### Props
なし

#### State
```typescript
interface SettingsState {
  // 検出設定
  personThreshold: number;        // 人物検出閾値
  smartphoneThreshold: number;    // スマートフォン検出閾値
  
  // アラート設定
  enableAlerts: boolean;          // アラート有効/無効
  absenceAlertTime: number;       // 不在アラート時間
  smartphoneAlertTime: number;    // スマートフォンアラート時間
  
  // UI設定
  language: string;               // 言語設定
  displayMode: string;            // 表示モード
  
  // フォーム状態
  isLoading: boolean;             // 保存中状態
  hasUnsavedChanges: boolean;     // 未保存変更
}
```

#### 主要メソッド
- `handleSave()`: 設定保存
- `handleReset()`: 設定リセット
- `handleInputChange()`: 入力値変更ハンドラー
- `loadSettings()`: 設定読み込み

#### フォーム要素
- スライダー：閾値設定
- スイッチ：アラート有効/無効
- 数値入力：時間設定
- セレクト：言語・表示モード

#### バリデーション
- 閾値範囲チェック（0.0-1.0）
- 時間設定チェック（正の整数）
- 必須項目チェック

---

### 3. ScheduleView.tsx
**役割**: スケジュール管理とアラート設定

#### 主要機能
- スケジュールアイテムの追加・編集・削除
- 時間ベースのアラート設定
- スケジュールの有効/無効切り替え
- スケジュール一覧表示

#### Props
なし

#### State
```typescript
interface ScheduleState {
  schedules: ScheduleItem[];      // スケジュール一覧
  editingSchedule: ScheduleItem | null;  // 編集中アイテム
  isAddMode: boolean;             // 追加モード
  selectedSchedule: string | null; // 選択中ID
}

interface ScheduleItem {
  id: string;                     // 一意ID
  title: string;                  // タイトル
  time: string;                   // 時刻（HH:MM）
  message: string;                // アラートメッセージ
  enabled: boolean;               // 有効/無効
  days: string[];                 // 曜日配列
}
```

#### 主要メソッド
- `addSchedule()`: スケジュール追加
- `editSchedule()`: スケジュール編集
- `deleteSchedule()`: スケジュール削除
- `toggleSchedule()`: 有効/無効切り替え
- `saveSchedules()`: スケジュール保存

#### UI コンポーネント
- スケジュール一覧テーブル
- 追加・編集フォーム
- 時刻ピッカー
- 曜日選択チェックボックス

---

### 4. PerformanceStats.tsx
**役割**: システムパフォーマンス統計の表示

#### 主要機能
- CPU・メモリ使用率表示
- 検出精度統計
- フレームレート表示
- システム稼働時間

#### Props
なし

#### State
```typescript
interface PerformanceState {
  cpuUsage: number;               // CPU使用率
  memoryUsage: number;            // メモリ使用率
  fps: number;                    // フレームレート
  uptime: number;                 // 稼働時間
  detectionAccuracy: number;      // 検出精度
  lastUpdated: Date;              // 最終更新時刻
}
```

#### 表示要素
- 進行バー：使用率表示
- 数値表示：統計値
- グラフ：時系列データ（将来実装）

---

### 5. LanguageSwitcher.tsx
**役割**: 言語切り替えUI

#### 主要機能
- 対応言語の表示と切り替え
- 現在の言語状態表示
- 言語設定の永続化

#### Props
なし

#### State
```typescript
interface LanguageState {
  currentLanguage: string;        // 現在の言語
  availableLanguages: Language[]; // 対応言語一覧
}

interface Language {
  code: string;                   // 言語コード（ja, en）
  label: string;                  // 表示名
  flag: string;                   // フラグ絵文字
}
```

#### 主要メソッド
- `changeLanguage()`: 言語変更
- i18nextとの連携

---

## 共通仕様

### 型定義（TypeScript）
```typescript
// 共通インターフェース
export interface DetectionStatus {
  personDetected: boolean;
  smartphoneDetected: boolean;
  absenceTime: number;
  smartphoneUseTime: number;
  absenceAlert?: boolean;
  smartphoneAlert?: boolean;
}

export interface ScheduleAlert {
  type: 'schedule_alert';
  content: string;
  time: string;
}

// コンポーネントProps型
export interface ComponentProps {
  children?: React.ReactNode;
  className?: string;
}
```

### エラーハンドリング
- WebSocket接続エラー：Toast通知で表示
- フォーム入力エラー：インライン検証メッセージ
- APIエラー：統一されたエラー処理

### アクセシビリティ
- ARIA属性の適切な設定
- キーボードナビゲーション対応
- スクリーンリーダー対応
- コントラスト比の確保

### パフォーマンス最適化
- React.memo による不要な再レンダリング防止
- useCallback/useMemo による計算結果キャッシュ
- 適切な依存配列の設定

### テスト仕様
- 各コンポーネントに対応するテストファイル
- ユーザーインタラクションのテスト
- WebSocket通信のモック
- エラー状態のテスト

## 国際化対応

### サポート言語
- 日本語（ja）：デフォルト
- 英語（en）

### 翻訳キー構造
```json
{
  "app": {
    "title": "アプリケーション名"
  },
  "tabs": {
    "monitor": "監視",
    "schedule": "スケジュール", 
    "settings": "設定"
  },
  "monitor": {
    "status": "状態",
    "fullscreen": "全画面"
  }
}
```

### 言語切り替え
- ブラウザ言語の自動検出
- ローカルストレージでの設定保存
- 動的な言語切り替え

## 今後の拡張予定

### 新機能
- ダークモード対応
- モバイルレスポンシブ対応
- PWA機能
- オフライン対応

### コンポーネント追加予定
- `ErrorBoundary`: エラー境界
- `LoadingSpinner`: ローディング表示
- `Notification`: 通知システム
- `Chart`: データ可視化 