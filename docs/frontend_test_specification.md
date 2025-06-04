# フロントエンド テスト仕様書

## 概要
KanshiChan フロントエンドアプリケーションのテスト戦略、テスト環境、テストケース、品質保証に関する仕様書です。

## テスト戦略

### テストピラミッド
```
     /\
    /  \     E2E Tests (将来実装)
   /____\    
  /      \   Integration Tests
 /________\  
/          \  Unit Tests
\__________/
```

### テストの分類

#### 1. 単体テスト（Unit Tests）
- **対象**: 個別コンポーネント、関数
- **範囲**: 70% をカバー目標
- **実行頻度**: 開発中、CI/CD

#### 2. 統合テスト（Integration Tests）
- **対象**: コンポーネント間の相互作用
- **範囲**: WebSocket通信、ユーザーフロー
- **実行頻度**: プルリクエスト時

#### 3. E2Eテスト（End-to-End Tests）
- **対象**: 完全なユーザーシナリオ
- **範囲**: 将来実装予定
- **実行頻度**: リリース前

---

## テスト環境設定

### Jest 29.7.0 設定

#### 基本設定（jest.config.js）
```javascript
export default {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapping: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/src/__mocks__/fileMock.js',
  },
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}',
  ],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts',
    '!src/**/__tests__/**',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  coverageReporters: ['text', 'lcov', 'html'],
};
```

#### セットアップファイル（setupTests.ts）
```typescript
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Chakra UI のモック
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// WebSocket のモック
global.WebSocket = vi.fn().mockImplementation(() => ({
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  send: vi.fn(),
  close: vi.fn(),
}));

// Fullscreen API のモック
Object.defineProperty(document, 'fullscreenElement', {
  writable: true,
  value: null,
});

Object.defineProperty(document, 'exitFullscreen', {
  writable: true,
  value: vi.fn().mockResolvedValue(undefined),
});

Object.defineProperty(Element.prototype, 'requestFullscreen', {
  writable: true,
  value: vi.fn().mockResolvedValue(undefined),
});
```

### React Testing Library 設定

#### レンダリングヘルパー
```typescript
// src/__tests__/test-utils.tsx
import { render, RenderOptions } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n';
import theme from '../theme';

const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  return (
    <ChakraProvider theme={theme}>
      <I18nextProvider i18n={i18n}>
        {children}
      </I18nextProvider>
    </ChakraProvider>
  );
};

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

---

## コンポーネントテスト仕様

### MonitorView コンポーネント

#### テスト対象機能
1. ビデオストリーム表示
2. ステータス表示更新
3. 全画面表示切り替え
4. WebSocket接続エラーハンドリング

#### テストケース例
```typescript
// src/components/__tests__/MonitorView.test.tsx
import { render, screen, fireEvent, waitFor } from '../../../__tests__/test-utils';
import { MonitorView } from '../MonitorView';
import { websocketManager } from '../../utils/websocket';

// WebSocketManager のモック
jest.mock('../../utils/websocket', () => ({
  websocketManager: {
    initialize: jest.fn(),
    onStatusUpdate: jest.fn((callback) => {
      // テスト用のステータスを渡す
      callback({
        personDetected: true,
        smartphoneDetected: false,
        absenceTime: 0,
        smartphoneUseTime: 0,
      });
      return jest.fn(); // unsubscribe function
    }),
    onError: jest.fn(() => jest.fn()),
  },
}));

describe('MonitorView', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('コンポーネントが正常にレンダリングされる', () => {
    render(<MonitorView />);
    
    expect(screen.getByAltText('Monitor')).toBeInTheDocument();
    expect(screen.getByLabelText('Toggle fullscreen')).toBeInTheDocument();
  });

  test('WebSocket接続が初期化される', () => {
    render(<MonitorView />);
    
    expect(websocketManager.initialize).toHaveBeenCalledTimes(1);
    expect(websocketManager.onStatusUpdate).toHaveBeenCalledTimes(1);
    expect(websocketManager.onError).toHaveBeenCalledTimes(1);
  });

  test('検出ステータスが正しく表示される', async () => {
    render(<MonitorView />);
    
    await waitFor(() => {
      expect(screen.getByText('在席中')).toBeInTheDocument();
      expect(screen.getByText('未使用')).toBeInTheDocument();
    });
  });

  test('全画面ボタンクリックで全画面表示が切り替わる', async () => {
    render(<MonitorView />);
    
    const toggleButton = screen.getByLabelText('Toggle fullscreen');
    fireEvent.click(toggleButton);
    
    await waitFor(() => {
      expect(document.querySelector('[data-testid="container"]')?.requestFullscreen)
        .toHaveBeenCalledTimes(1);
    });
  });

  test('ビデオソースが正しく設定される', () => {
    render(<MonitorView />);
    
    const video = screen.getByAltText('Monitor') as HTMLImageElement;
    expect(video.src).toBe('http://localhost:5001/api/video_feed');
  });

  test('WebSocketエラー時にトースト通知が表示される', async () => {
    const mockOnError = jest.fn();
    (websocketManager.onError as jest.Mock).mockImplementation((callback) => {
      callback(new Error('Connection failed'));
      return jest.fn();
    });

    render(<MonitorView />);
    
    await waitFor(() => {
      expect(screen.getByText('接続エラー')).toBeInTheDocument();
    });
  });
});
```

### SettingsPanel コンポーネント

#### テスト対象機能
1. 設定値の表示・編集
2. バリデーション
3. 保存機能
4. リセット機能

#### テストケース例
```typescript
// src/components/__tests__/SettingsPanel.test.tsx
describe('SettingsPanel', () => {
  test('設定フォームが正しく表示される', () => {
    render(<SettingsPanel />);
    
    expect(screen.getByLabelText('人物検出閾値')).toBeInTheDocument();
    expect(screen.getByLabelText('スマートフォン検出閾値')).toBeInTheDocument();
    expect(screen.getByLabelText('アラートを有効にする')).toBeInTheDocument();
  });

  test('スライダー値の変更が正しく反映される', () => {
    render(<SettingsPanel />);
    
    const slider = screen.getByLabelText('人物検出閾値');
    fireEvent.change(slider, { target: { value: '0.7' } });
    
    expect(slider).toHaveValue('0.7');
  });

  test('無効な値入力時にエラーメッセージが表示される', async () => {
    render(<SettingsPanel />);
    
    const input = screen.getByLabelText('不在アラート時間');
    fireEvent.change(input, { target: { value: '-10' } });
    fireEvent.blur(input);
    
    await waitFor(() => {
      expect(screen.getByText('正の値を入力してください')).toBeInTheDocument();
    });
  });

  test('保存ボタンクリックで設定が保存される', async () => {
    const mockSave = jest.fn().mockResolvedValue(true);
    render(<SettingsPanel onSave={mockSave} />);
    
    const saveButton = screen.getByText('保存');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockSave).toHaveBeenCalledTimes(1);
    });
  });

  test('リセットボタンクリックで設定がリセットされる', () => {
    render(<SettingsPanel />);
    
    // 値を変更
    const slider = screen.getByLabelText('人物検出閾値');
    fireEvent.change(slider, { target: { value: '0.8' } });
    
    // リセット
    const resetButton = screen.getByText('リセット');
    fireEvent.click(resetButton);
    
    expect(slider).toHaveValue('0.5'); // デフォルト値
  });
});
```

### ScheduleView コンポーネント

#### テスト対象機能
1. スケジュール一覧表示
2. スケジュール追加・編集・削除
3. 時刻・曜日選択
4. バリデーション

#### テストケース例
```typescript
// src/components/__tests__/ScheduleView.test.tsx
describe('ScheduleView', () => {
  test('スケジュール追加フォームが表示される', () => {
    render(<ScheduleView />);
    
    expect(screen.getByText('新しいスケジュールを追加')).toBeInTheDocument();
    expect(screen.getByLabelText('タイトル')).toBeInTheDocument();
    expect(screen.getByLabelText('時刻')).toBeInTheDocument();
  });

  test('スケジュール追加が正常に動作する', async () => {
    render(<ScheduleView />);
    
    // フォーム入力
    fireEvent.change(screen.getByLabelText('タイトル'), {
      target: { value: '朝会' },
    });
    fireEvent.change(screen.getByLabelText('時刻'), {
      target: { value: '09:00' },
    });
    fireEvent.change(screen.getByLabelText('メッセージ'), {
      target: { value: '朝会の時間です' },
    });
    
    // 曜日選択
    fireEvent.click(screen.getByLabelText('月曜日'));
    fireEvent.click(screen.getByLabelText('火曜日'));
    
    // 追加
    fireEvent.click(screen.getByText('追加'));
    
    await waitFor(() => {
      expect(screen.getByText('朝会')).toBeInTheDocument();
      expect(screen.getByText('09:00')).toBeInTheDocument();
    });
  });

  test('スケジュール削除が正常に動作する', async () => {
    // 事前データ設定付きでレンダリング
    const initialSchedules = [
      {
        id: '1',
        title: '朝会',
        time: '09:00',
        message: '朝会の時間です',
        enabled: true,
        days: ['monday'],
      },
    ];
    
    render(<ScheduleView initialSchedules={initialSchedules} />);
    
    // 削除ボタンクリック
    const deleteButton = screen.getByLabelText('削除');
    fireEvent.click(deleteButton);
    
    // 確認ダイアログで確定
    const confirmButton = screen.getByText('削除する');
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(screen.queryByText('朝会')).not.toBeInTheDocument();
    });
  });
});
```

---

## WebSocket通信テスト

### WebSocketManager テスト

#### テスト対象機能
1. シングルトンパターン
2. 接続管理
3. イベントリスナー管理
4. エラーハンドリング

#### テストケース例
```typescript
// src/utils/__tests__/websocket.test.ts
import { websocketManager } from '../websocket';
import { io } from 'socket.io-client';

// Socket.IO のモック
jest.mock('socket.io-client');
const mockIo = io as jest.MockedFunction<typeof io>;

describe('WebSocketManager', () => {
  let mockSocket: any;

  beforeEach(() => {
    mockSocket = {
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
    };
    mockIo.mockReturnValue(mockSocket);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('シングルトンインスタンスが正しく動作する', () => {
    const instance1 = websocketManager;
    const instance2 = websocketManager;
    
    expect(instance1).toBe(instance2);
  });

  test('初期化が正しく動作する', () => {
    websocketManager.initialize();
    
    expect(mockIo).toHaveBeenCalledWith('http://localhost:5001', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });
    
    expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('status_update', expect.any(Function));
  });

  test('ステータス更新リスナーが正しく動作する', () => {
    const mockCallback = jest.fn();
    
    const unsubscribe = websocketManager.onStatusUpdate(mockCallback);
    
    // status_updateイベントをシミュレート
    const statusData = {
      personDetected: true,
      smartphoneDetected: false,
      absenceTime: 0,
      smartphoneUseTime: 0,
    };
    
    // リスナーを手動で呼び出し
    mockSocket.on.mock.calls
      .find(([event]) => event === 'status_update')?.[1](statusData);
    
    expect(mockCallback).toHaveBeenCalledWith(statusData);
    
    // unsubscribe確認
    unsubscribe();
    expect(typeof unsubscribe).toBe('function');
  });

  test('エラーハンドリングが正しく動作する', () => {
    const mockErrorCallback = jest.fn();
    
    websocketManager.onError(mockErrorCallback);
    
    const error = new Error('Connection failed');
    
    // connect_errorイベントをシミュレート
    mockSocket.on.mock.calls
      .find(([event]) => event === 'connect_error')?.[1](error);
    
    expect(mockErrorCallback).toHaveBeenCalledWith(error);
  });

  test('接続切断が正しく動作する', () => {
    websocketManager.initialize();
    websocketManager.disconnect();
    
    expect(mockSocket.disconnect).toHaveBeenCalledTimes(1);
  });
});
```

---

## 統合テスト

### ユーザーフローテスト

#### 監視画面の統合テスト
```typescript
// src/__tests__/integration/MonitorFlow.test.tsx
describe('監視画面統合テスト', () => {
  test('完全な監視フローが正常に動作する', async () => {
    const mockWebSocket = setupMockWebSocket();
    
    render(<App />);
    
    // 監視タブに移動
    fireEvent.click(screen.getByText('監視'));
    
    // WebSocket接続確認
    await waitFor(() => {
      expect(mockWebSocket.initialize).toHaveBeenCalled();
    });
    
    // ステータス更新のシミュレート
    act(() => {
      mockWebSocket.simulateStatusUpdate({
        personDetected: false,
        smartphoneDetected: false,
        absenceTime: 300,
        smartphoneUseTime: 0,
      });
    });
    
    // UI更新確認
    await waitFor(() => {
      expect(screen.getByText('不在')).toBeInTheDocument();
      expect(screen.getByText('不在時間: 300秒')).toBeInTheDocument();
    });
    
    // 全画面切り替えテスト
    fireEvent.click(screen.getByLabelText('Toggle fullscreen'));
    
    await waitFor(() => {
      expect(document.requestFullscreen).toHaveBeenCalled();
    });
  });
});
```

#### 設定変更の統合テスト
```typescript
describe('設定変更統合テスト', () => {
  test('設定変更からリアルタイム反映まで', async () => {
    const mockApi = setupMockApi();
    
    render(<App />);
    
    // 設定タブに移動
    fireEvent.click(screen.getByText('設定'));
    
    // 閾値変更
    const slider = screen.getByLabelText('人物検出閾値');
    fireEvent.change(slider, { target: { value: '0.7' } });
    
    // 保存
    fireEvent.click(screen.getByText('保存'));
    
    await waitFor(() => {
      expect(mockApi.saveSettings).toHaveBeenCalledWith({
        detection: { personThreshold: 0.7 },
      });
    });
    
    // 成功通知確認
    expect(screen.getByText('設定が保存されました')).toBeInTheDocument();
  });
});
```

---

## パフォーマンステスト

### レンダリングパフォーマンス
```typescript
// src/__tests__/performance/RenderPerformance.test.tsx
describe('レンダリングパフォーマンス', () => {
  test('MonitorViewの初期レンダリング時間', () => {
    const startTime = performance.now();
    
    render(<MonitorView />);
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // 100ms以内での初期レンダリングを期待
    expect(renderTime).toBeLessThan(100);
  });

  test('ステータス更新時の再レンダリング回数', () => {
    const renderCount = trackRenderCount();
    
    const { rerender } = render(<MonitorView />);
    
    // 10回のステータス更新をシミュレート
    for (let i = 0; i < 10; i++) {
      rerender(<MonitorView key={i} />);
    }
    
    // 不要な再レンダリングが発生していないことを確認
    expect(renderCount.current).toBeLessThanOrEqual(11); // 初期 + 10回更新
  });
});
```

### メモリリークテスト
```typescript
describe('メモリリーク防止', () => {
  test('コンポーネントアンマウント時のクリーンアップ', () => {
    const mockUnsubscribe = jest.fn();
    
    jest.spyOn(websocketManager, 'onStatusUpdate')
      .mockReturnValue(mockUnsubscribe);
    
    const { unmount } = render(<MonitorView />);
    
    unmount();
    
    // クリーンアップ関数が呼ばれることを確認
    expect(mockUnsubscribe).toHaveBeenCalledTimes(1);
  });
});
```

---

## アクセシビリティテスト

### スクリーンリーダー対応テスト
```typescript
// src/__tests__/accessibility/ScreenReader.test.tsx
describe('スクリーンリーダー対応', () => {
  test('適切なARIAラベルが設定されている', () => {
    render(<MonitorView />);
    
    expect(screen.getByLabelText('Toggle fullscreen')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('キーボードナビゲーションが機能する', () => {
    render(<SettingsPanel />);
    
    const firstInput = screen.getByLabelText('人物検出閾値');
    firstInput.focus();
    
    // Tab キーでナビゲーション
    fireEvent.keyDown(firstInput, { key: 'Tab' });
    
    const nextInput = screen.getByLabelText('スマートフォン検出閾値');
    expect(nextInput).toHaveFocus();
  });
});
```

---

## カバレッジ要件

### カバレッジ目標
- **行カバレッジ**: 70% 以上
- **関数カバレッジ**: 70% 以上
- **ブランチカバレッジ**: 70% 以上
- **ステートメントカバレッジ**: 70% 以上

### カバレッジ除外対象
- `src/main.tsx`: アプリエントリーポイント
- `src/vite-env.d.ts`: 型定義ファイル
- `src/**/*.d.ts`: TypeScript宣言ファイル
- `src/**/__tests__/**`: テストファイル自体

### カバレッジレポート
```bash
npm run test -- --coverage
```

---

## CI/CD統合

### GitHub Actions設定
```yaml
# .github/workflows/frontend-test.yml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: npm ci
      working-directory: frontend
    
    - name: Run tests
      run: npm run test -- --coverage --watchAll=false
      working-directory: frontend
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        directory: frontend/coverage
```

### 品質ゲート
- **テスト成功率**: 100%
- **カバレッジ要件**: 70% 以上
- **Lintエラー**: 0件
- **TypeScriptエラー**: 0件

---

## 今後のテスト拡張

### E2Eテスト実装予定
- **Playwright**: ブラウザ自動化
- **シナリオ**: 完全なユーザージャーニー
- **環境**: 本番類似環境でのテスト

### ビジュアルリグレッションテスト
- **Chromatic**: UI変更検出
- **Storybook**: コンポーネント管理
- **スナップショット**: 視覚的差分確認

### パフォーマンス監視
- **Lighthouse**: パフォーマンススコア
- **Web Vitals**: Core Web Vitals測定
- **Bundle Analyzer**: バンドルサイズ監視 