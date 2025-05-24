import { websocketManager } from '../websocket';
import { io } from 'socket.io-client';

// Socket.IOクライアントをモック化
jest.mock('socket.io-client', () => ({
  io: jest.fn(),
}));

const mockSocket = {
  on: jest.fn(),
  emit: jest.fn(),
  disconnect: jest.fn(),
  connect: jest.fn(),
  connected: false,
};

const mockedIo = io as jest.MockedFunction<typeof io>;

describe('websocketManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedIo.mockReturnValue(mockSocket as unknown as ReturnType<typeof io>);
  });

  afterEach(() => {
    // テスト後のクリーンアップ
    websocketManager.disconnect();
  });

  test('websocketManagerがオブジェクトとして存在する', () => {
    expect(websocketManager).toBeDefined();
    expect(typeof websocketManager.initialize).toBe('function');
  });

  test('initialize()でSocket.IO接続が開始される', () => {
    websocketManager.initialize();
    
    expect(mockedIo).toHaveBeenCalledWith('http://localhost:5001', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });
    expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('connect_error', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('status_update', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('schedule_alert', expect.any(Function));
  });

  test('ステータス更新コールバックが正しく動作する', () => {
    const statusUpdateCallback = jest.fn();
    
    websocketManager.initialize();
    websocketManager.onStatusUpdate(statusUpdateCallback);
    
    // Socket.IOのonメソッドから 'status_update' イベントのハンドラーを取得
    const statusHandler = (mockSocket.on as jest.Mock).mock.calls
      .find(call => call[0] === 'status_update')?.[1];
    
    expect(statusHandler).toBeDefined();
    
    // ステータス更新をシミュレート
    const testStatus = {
      personDetected: true,
      smartphoneDetected: false,
      absenceTime: 0,
      smartphoneUseTime: 0
    };
    
    statusHandler(testStatus);
    
    expect(statusUpdateCallback).toHaveBeenCalledWith(testStatus);
  });

  test('スケジュールアラートコールバックが正しく動作する', () => {
    const scheduleAlertCallback = jest.fn();
    
    websocketManager.initialize();
    websocketManager.onScheduleAlert(scheduleAlertCallback);
    
    // Socket.IOのonメソッドから 'schedule_alert' イベントのハンドラーを取得
    const alertHandler = (mockSocket.on as jest.Mock).mock.calls
      .find(call => call[0] === 'schedule_alert')?.[1];
    
    expect(alertHandler).toBeDefined();
    
    // スケジュールアラートをシミュレート
    const testAlert = {
      type: 'schedule_alert' as const,
      time: '09:00',
      content: 'ミーティング'
    };
    
    alertHandler(testAlert);
    
    expect(scheduleAlertCallback).toHaveBeenCalledWith(testAlert);
  });

  test('エラーコールバックが正しく動作する', () => {
    const errorCallback = jest.fn();
    
    websocketManager.initialize();
    websocketManager.onError(errorCallback);
    
    // Socket.IOのonメソッドから 'connect_error' イベントのハンドラーを取得
    const errorHandler = (mockSocket.on as jest.Mock).mock.calls
      .find(call => call[0] === 'connect_error')?.[1];
    
    expect(errorHandler).toBeDefined();
    
    // エラーをシミュレート
    const testError = new Error('Connection failed');
    errorHandler(testError);
    
    expect(errorCallback).toHaveBeenCalledWith(testError);
  });

  test('イベントリスナーの登録解除が正しく動作する', () => {
    const statusCallback = jest.fn();
    
    // リスナーを登録
    const unsubscribe = websocketManager.onStatusUpdate(statusCallback);
    
    // 登録解除関数が返されることを確認
    expect(typeof unsubscribe).toBe('function');
    
    // 登録解除を実行
    unsubscribe();
    
    // 登録解除後はコールバックが呼ばれないことを確認するため、
    // 新しいコールバックを登録してテスト
    const newCallback = jest.fn();
    websocketManager.onStatusUpdate(newCallback);
    
    websocketManager.initialize();
    
    const statusHandler = (mockSocket.on as jest.Mock).mock.calls
      .find(call => call[0] === 'status_update')?.[1];
    
    const testStatus = {
      personDetected: true,
      smartphoneDetected: false,
      absenceTime: 0,
      smartphoneUseTime: 0
    };
    
    statusHandler(testStatus);
    
    // 元のコールバックは呼ばれず、新しいコールバックは呼ばれることを確認
    expect(statusCallback).not.toHaveBeenCalled();
    expect(newCallback).toHaveBeenCalledWith(testStatus);
  });

  test('disconnect()でSocket.IO接続が切断される', () => {
    websocketManager.initialize();
    websocketManager.disconnect();
    
    expect(mockSocket.disconnect).toHaveBeenCalled();
  });
});

describe('websocketManager singleton', () => {
  test('websocketManagerがシングルトンインスタンスである', () => {
    expect(websocketManager).toBeDefined();
    
    // 複数回インポートしても同じインスタンスが返されることを確認
    const { websocketManager: manager2 } = jest.requireActual('../websocket');
    expect(websocketManager).toBe(manager2);
  });
}); 