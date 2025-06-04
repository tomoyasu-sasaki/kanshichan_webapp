"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var websocket_1 = require("../websocket");
var socket_io_client_1 = require("socket.io-client");
// Socket.IOクライアントをモック化
jest.mock('socket.io-client', function () { return ({
    io: jest.fn(),
}); });
var mockSocket = {
    on: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn(),
    connect: jest.fn(),
    connected: false,
};
var mockedIo = socket_io_client_1.io;
describe('websocketManager', function () {
    beforeEach(function () {
        jest.clearAllMocks();
        mockedIo.mockReturnValue(mockSocket);
    });
    afterEach(function () {
        // テスト後のクリーンアップ
        websocket_1.websocketManager.disconnect();
    });
    test('websocketManagerがオブジェクトとして存在する', function () {
        expect(websocket_1.websocketManager).toBeDefined();
        expect(typeof websocket_1.websocketManager.initialize).toBe('function');
    });
    test('initialize()でSocket.IO接続が開始される', function () {
        websocket_1.websocketManager.initialize();
        expect(mockedIo).toHaveBeenCalledWith('http://localhost:8000', {
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
    test('ステータス更新コールバックが正しく動作する', function () {
        var _a;
        var statusUpdateCallback = jest.fn();
        websocket_1.websocketManager.initialize();
        websocket_1.websocketManager.onStatusUpdate(statusUpdateCallback);
        // Socket.IOのonメソッドから 'status_update' イベントのハンドラーを取得
        var statusHandler = (_a = mockSocket.on.mock.calls
            .find(function (call) { return call[0] === 'status_update'; })) === null || _a === void 0 ? void 0 : _a[1];
        expect(statusHandler).toBeDefined();
        // ステータス更新をシミュレート
        var testStatus = {
            personDetected: true,
            smartphoneDetected: false,
            absenceTime: 0,
            smartphoneUseTime: 0
        };
        statusHandler(testStatus);
        expect(statusUpdateCallback).toHaveBeenCalledWith(testStatus);
    });
    test('スケジュールアラートコールバックが正しく動作する', function () {
        var _a;
        var scheduleAlertCallback = jest.fn();
        websocket_1.websocketManager.initialize();
        websocket_1.websocketManager.onScheduleAlert(scheduleAlertCallback);
        // Socket.IOのonメソッドから 'schedule_alert' イベントのハンドラーを取得
        var alertHandler = (_a = mockSocket.on.mock.calls
            .find(function (call) { return call[0] === 'schedule_alert'; })) === null || _a === void 0 ? void 0 : _a[1];
        expect(alertHandler).toBeDefined();
        // スケジュールアラートをシミュレート
        var testAlert = {
            type: 'schedule_alert',
            time: '09:00',
            content: 'ミーティング'
        };
        alertHandler(testAlert);
        expect(scheduleAlertCallback).toHaveBeenCalledWith(testAlert);
    });
    test('エラーコールバックが正しく動作する', function () {
        var _a;
        var errorCallback = jest.fn();
        websocket_1.websocketManager.initialize();
        websocket_1.websocketManager.onError(errorCallback);
        // Socket.IOのonメソッドから 'connect_error' イベントのハンドラーを取得
        var errorHandler = (_a = mockSocket.on.mock.calls
            .find(function (call) { return call[0] === 'connect_error'; })) === null || _a === void 0 ? void 0 : _a[1];
        expect(errorHandler).toBeDefined();
        // エラーをシミュレート
        var testError = new Error('Connection failed');
        errorHandler(testError);
        expect(errorCallback).toHaveBeenCalledWith(testError);
    });
    test('イベントリスナーの登録解除が正しく動作する', function () {
        var _a;
        var statusCallback = jest.fn();
        // リスナーを登録
        var unsubscribe = websocket_1.websocketManager.onStatusUpdate(statusCallback);
        // 登録解除関数が返されることを確認
        expect(typeof unsubscribe).toBe('function');
        // 登録解除を実行
        unsubscribe();
        // 登録解除後はコールバックが呼ばれないことを確認するため、
        // 新しいコールバックを登録してテスト
        var newCallback = jest.fn();
        websocket_1.websocketManager.onStatusUpdate(newCallback);
        websocket_1.websocketManager.initialize();
        var statusHandler = (_a = mockSocket.on.mock.calls
            .find(function (call) { return call[0] === 'status_update'; })) === null || _a === void 0 ? void 0 : _a[1];
        var testStatus = {
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
    test('disconnect()でSocket.IO接続が切断される', function () {
        websocket_1.websocketManager.initialize();
        websocket_1.websocketManager.disconnect();
        expect(mockSocket.disconnect).toHaveBeenCalled();
    });
});
describe('websocketManager singleton', function () {
    test('websocketManagerがシングルトンインスタンスである', function () {
        expect(websocket_1.websocketManager).toBeDefined();
        // 複数回インポートしても同じインスタンスが返されることを確認
        var manager2 = jest.requireActual('../websocket').websocketManager;
        expect(websocket_1.websocketManager).toBe(manager2);
    });
});
