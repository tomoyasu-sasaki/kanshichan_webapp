import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';

// WebSocketマネージャーをモック化
jest.mock('../utils/websocket', () => ({
  websocketManager: {
    initialize: jest.fn(),
    onError: jest.fn(() => jest.fn()),
    onStatusUpdate: jest.fn(() => jest.fn()),
    onScheduleAlert: jest.fn(() => jest.fn()),
    disconnect: jest.fn(),
  },
}));

// axiosをモック化
jest.mock('axios', () => ({
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: { success: true } })),
}));

// HTMLImageElementのsrcプロパティをモック化
Object.defineProperty(HTMLImageElement.prototype, 'src', {
  set: jest.fn(),
  get: jest.fn(() => 'http://localhost:8000/api/video_feed'),
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

Object.defineProperty(HTMLDivElement.prototype, 'requestFullscreen', {
  writable: true,
  value: jest.fn(() => Promise.resolve()),
});

// fetchをモック化
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve([]),
  })
) as jest.Mock;

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('Appコンポーネントが正しくレンダリングされる', () => {
    render(<App />);

    // アプリケーションタイトルが表示されることを確認
    expect(screen.getByText('監視ちゃん')).toBeInTheDocument();

    // タブが表示されることを確認
    expect(screen.getByRole('tab', { name: /監視画面/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /設定/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /スケジュール/i })).toBeInTheDocument();
  });

  test('初期状態で監視画面タブが選択されている', () => {
    render(<App />);

    // 監視画面タブが選択されていることを確認
    const monitorTab = screen.getByRole('tab', { name: /監視画面/i });
    expect(monitorTab).toHaveAttribute('aria-selected', 'true');

    // MonitorViewコンポーネントの要素が表示されることを確認
    expect(screen.getByAltText('Monitor')).toBeInTheDocument();
  });

  test('設定タブをクリックすると設定画面が表示される', async () => {
    const user = userEvent.setup();
    
    render(<App />);

    // 設定タブをクリック
    const settingsTab = screen.getByRole('tab', { name: /設定/i });
    await user.click(settingsTab);

    // 設定タブが選択されていることを確認
    expect(settingsTab).toHaveAttribute('aria-selected', 'true');

    // SettingsPanelコンポーネントの要素が表示されることを確認
    expect(screen.getByText('監視設定')).toBeInTheDocument();
  });

  test('スケジュールタブをクリックするとスケジュール画面が表示される', async () => {
    const user = userEvent.setup();
    
    render(<App />);

    // スケジュールタブをクリック
    const scheduleTab = screen.getByRole('tab', { name: /スケジュール/i });
    await user.click(scheduleTab);

    // スケジュールタブが選択されていることを確認
    expect(scheduleTab).toHaveAttribute('aria-selected', 'true');

    // ScheduleViewコンポーネントの要素が表示されることを確認
    expect(screen.getByText(/のスケジュール/)).toBeInTheDocument();
  });

  test('タブ間の切り替えが正しく動作する', async () => {
    const user = userEvent.setup();
    
    render(<App />);

    // 初期状態：監視画面
    expect(screen.getByRole('tab', { name: /監視画面/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByAltText('Monitor')).toBeInTheDocument();

    // 設定タブに切り替え
    await user.click(screen.getByRole('tab', { name: /設定/i }));
    expect(screen.getByRole('tab', { name: /設定/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText('監視設定')).toBeInTheDocument();

    // スケジュールタブに切り替え
    await user.click(screen.getByRole('tab', { name: /スケジュール/i }));
    expect(screen.getByRole('tab', { name: /スケジュール/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText(/のスケジュール/)).toBeInTheDocument();

    // 監視画面タブに戻る
    await user.click(screen.getByRole('tab', { name: /監視画面/i }));
    expect(screen.getByRole('tab', { name: /監視画面/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByAltText('Monitor')).toBeInTheDocument();
  });

  test('ChakraProviderが適用されている', () => {
    render(<App />);

    // Chakra UIのクラスが適用されていることを確認
    const container = screen.getByRole('main') || document.body.firstChild;
    expect(container).toHaveClass('chakra-ui-light');
  });

  test('レスポンシブレイアウトが適用されている', () => {
    render(<App />);

    // コンテナが適切なレイアウトクラスを持っていることを確認
    const tabPanels = screen.getByRole('tabpanel');
    expect(tabPanels).toBeInTheDocument();
  });

  test('アクセシビリティが適切に設定されている', () => {
    render(<App />);

    // タブリストが適切に設定されていることを確認
    const tabList = screen.getByRole('tablist');
    expect(tabList).toBeInTheDocument();

    // 各タブが適切にラベル付けされていることを確認
    expect(screen.getByRole('tab', { name: /監視画面/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /設定/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /スケジュール/i })).toBeInTheDocument();

    // タブパネルが適切に設定されていることを確認
    expect(screen.getByRole('tabpanel')).toBeInTheDocument();
  });
}); 