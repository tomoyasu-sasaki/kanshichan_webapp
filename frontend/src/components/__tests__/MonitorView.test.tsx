import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChakraProvider, useToast } from '@chakra-ui/react';
import { MonitorView } from '../MonitorView';
import { websocketManager } from '../../utils/websocket';

// WebSocketマネージャーをモック化
jest.mock('../../utils/websocket', () => {
  const originalModule = jest.requireActual('../../utils/websocket');
  return {
    ...originalModule,
    websocketManager: {
      initialize: jest.fn(),
      onError: jest.fn(() => jest.fn()), // アンサブスクライブ関数を返す
      onStatusUpdate: jest.fn(() => jest.fn()), // アンサブスクライブ関数を返す
    },
  };
});

// Chakra UIのuseToastをモック化
jest.mock('@chakra-ui/react', () => {
  const originalModule = jest.requireActual('@chakra-ui/react');
  return {
    ...originalModule,
    useToast: jest.fn(() => jest.fn()),
  };
});

// HTMLImageElementのsrcプロパティをモック化
Object.defineProperty(HTMLImageElement.prototype, 'src', {
  set: jest.fn(),
  get: jest.fn(() => 'http://localhost:5001/api/video_feed'),
});

// 全画面API関連のモック
Object.defineProperty(document, 'fullscreenElement', {
  writable: true,
  value: null,
});

Object.defineProperty(document, 'exitFullscreen', {
  writable: true,
  value: jest.fn(() => Promise.resolve()),
});

// HTMLDivElementのrequestFullscreenをモック化
Object.defineProperty(HTMLDivElement.prototype, 'requestFullscreen', {
  writable: true,
  value: jest.fn(() => Promise.resolve()),
});

describe('MonitorView Component', () => {
  const mockToast = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useToast as jest.Mock).mockImplementation(() => mockToast);
    
    // fullscreenElementを初期状態に戻す
    Object.defineProperty(document, 'fullscreenElement', {
      writable: true,
      value: null,
    });
  });

  test('コンポーネントが正しくレンダリングされる', () => {
    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    // 動画が表示されることを確認
    const image = screen.getByAltText('Monitor');
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute('src', 'http://localhost:5001/api/video_feed');

    // 全画面ボタンが表示されることを確認
    const fullscreenButton = screen.getByLabelText('Toggle fullscreen');
    expect(fullscreenButton).toBeInTheDocument();

    // ステータス情報が表示されることを確認
    expect(screen.getByText('在席状態:')).toBeInTheDocument();
    expect(screen.getByText('スマートフォン:')).toBeInTheDocument();
  });

  test('WebSocketマネージャーが初期化される', () => {
    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    expect(websocketManager.initialize).toHaveBeenCalled();
    expect(websocketManager.onError).toHaveBeenCalled();
    expect(websocketManager.onStatusUpdate).toHaveBeenCalled();
  });

  test('初期状態で正しいステータスが表示される', () => {
    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    // 初期状態では不在とスマートフォン未使用が表示される
    expect(screen.getByText('不在')).toBeInTheDocument();
    expect(screen.getByText('未使用')).toBeInTheDocument();
    expect(screen.getByText('不在時間: 0秒')).toBeInTheDocument();
  });

  test('ステータス更新が正しく反映される', async () => {
    interface DetectionStatus {
      personDetected: boolean;
      smartphoneDetected: boolean;
      absenceTime: number;
      smartphoneUseTime: number;
    }
    
    let statusUpdateCallback: (status: DetectionStatus) => void = () => {};
    
    // onStatusUpdateのモックを設定してコールバックを取得
    (websocketManager.onStatusUpdate as jest.Mock).mockImplementation((callback) => {
      statusUpdateCallback = callback;
      return jest.fn(); // アンサブスクライブ関数
    });

    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    // ステータス更新をシミュレート
    await act(async () => {
      statusUpdateCallback({
        personDetected: true,
        smartphoneDetected: true,
        absenceTime: 0,
        smartphoneUseTime: 30
      });
    });

    // 更新されたステータスが表示されることを確認
    expect(screen.getByText('在席中')).toBeInTheDocument();
    expect(screen.getByText('使用中')).toBeInTheDocument();
    expect(screen.getByText('使用時間: 30秒')).toBeInTheDocument();
  });

  test('全画面表示の切り替えが動作する', async () => {
    const user = userEvent.setup();
    const mockRequestFullscreen = jest.fn(() => Promise.resolve());
    
    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    // requestFullscreenをモック化
    const container = screen.getByLabelText('Toggle fullscreen').closest('[data-testid]')?.parentElement;
    if (container) {
      (container as HTMLElement & { requestFullscreen: () => Promise<void> }).requestFullscreen = mockRequestFullscreen;
    }

    const fullscreenButton = screen.getByLabelText('Toggle fullscreen');
    
    // 全画面モードに切り替え
    await user.click(fullscreenButton);
    
    // requestFullscreenが呼ばれることを確認
    expect(mockRequestFullscreen).toHaveBeenCalled();
  });

  test('全画面解除が動作する', async () => {
    const user = userEvent.setup();
    
    // 全画面状態をシミュレート
    Object.defineProperty(document, 'fullscreenElement', {
      writable: true,
      value: document.createElement('div'),
    });

    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    const fullscreenButton = screen.getByLabelText('Toggle fullscreen');
    
    // 全画面解除
    await user.click(fullscreenButton);
    
    // exitFullscreenが呼ばれることを確認
    expect(document.exitFullscreen).toHaveBeenCalled();
  });

  test('全画面切り替え中のエラーハンドリング', async () => {
    const user = userEvent.setup();
    const mockRequestFullscreen = jest.fn(() => Promise.reject(new Error('Fullscreen error')));
    
    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    // requestFullscreenでエラーが発生するようにモック化
    const container = screen.getByLabelText('Toggle fullscreen').closest('[data-testid]')?.parentElement;
    if (container) {
      (container as HTMLElement & { requestFullscreen: () => Promise<void> }).requestFullscreen = mockRequestFullscreen;
    }

    const fullscreenButton = screen.getByLabelText('Toggle fullscreen');
    
    // エラーが発生する全画面切り替えを実行
    await user.click(fullscreenButton);
    
    // エラートーストが表示されることを確認
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
        title: 'エラー',
        description: '全画面表示の切り替えに失敗しました',
        status: 'error',
      }));
    });
  });

  test('WebSocket接続エラーハンドリング', async () => {
    let errorCallback: () => void = () => {};
    
    // onErrorのモックを設定してコールバックを取得
    (websocketManager.onError as jest.Mock).mockImplementation((callback) => {
      errorCallback = callback;
      return jest.fn(); // アンサブスクライブ関数
    });

    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    // エラーをシミュレート
    await act(async () => {
      errorCallback();
    });

    // エラートーストが表示されることを確認
    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
      title: '接続エラー',
      description: 'サーバーとの接続に失敗しました',
      status: 'error',
    }));
  });

  test('fullscreenchangeイベントの処理', () => {
    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    // fullscreenchangeイベントをシミュレート（全画面モード）
    Object.defineProperty(document, 'fullscreenElement', {
      writable: true,
      value: document.createElement('div'),
    });

    act(() => {
      fireEvent(document, new Event('fullscreenchange'));
    });

    // 全画面解除のアイコンが表示されることを確認
    const fullscreenButton = screen.getByLabelText('Toggle fullscreen');
    expect(fullscreenButton).toBeInTheDocument();

    // 通常モードに戻る
    Object.defineProperty(document, 'fullscreenElement', {
      writable: true,
      value: null,
    });

    act(() => {
      fireEvent(document, new Event('fullscreenchange'));
    });

    // 全画面モードのアイコンが表示されることを確認
    expect(fullscreenButton).toBeInTheDocument();
  });

  test('コンポーネントのクリーンアップが正しく動作する', () => {
    const mockUnsubscribeError = jest.fn();
    const mockUnsubscribeStatus = jest.fn();

    (websocketManager.onError as jest.Mock).mockImplementation(() => mockUnsubscribeError);
    (websocketManager.onStatusUpdate as jest.Mock).mockImplementation(() => mockUnsubscribeStatus);

    const { unmount } = render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    // コンポーネントをアンマウント
    unmount();

    // クリーンアップ関数が呼ばれることを確認
    expect(mockUnsubscribeError).toHaveBeenCalled();
    expect(mockUnsubscribeStatus).toHaveBeenCalled();
  });

  test('アクセシビリティが適切に設定されている', () => {
    render(
      <ChakraProvider>
        <MonitorView />
      </ChakraProvider>
    );

    // 全画面ボタンにaria-labelが設定されていることを確認
    const fullscreenButton = screen.getByLabelText('Toggle fullscreen');
    expect(fullscreenButton).toBeInTheDocument();

    // 画像にaltが設定されていることを確認
    const image = screen.getByAltText('Monitor');
    expect(image).toBeInTheDocument();
  });
}); 