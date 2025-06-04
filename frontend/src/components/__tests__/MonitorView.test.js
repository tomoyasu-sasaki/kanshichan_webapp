"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
var jsx_runtime_1 = require("react/jsx-runtime");
var react_1 = require("@testing-library/react");
var user_event_1 = __importDefault(require("@testing-library/user-event"));
var react_2 = require("@chakra-ui/react");
var MonitorView_1 = require("../MonitorView");
var websocket_1 = require("../../utils/websocket");
// WebSocketマネージャーをモック化
jest.mock('../../utils/websocket', function () {
    var originalModule = jest.requireActual('../../utils/websocket');
    return __assign(__assign({}, originalModule), { websocketManager: {
            initialize: jest.fn(),
            onError: jest.fn(function () { return jest.fn(); }), // アンサブスクライブ関数を返す
            onStatusUpdate: jest.fn(function () { return jest.fn(); }), // アンサブスクライブ関数を返す
        } });
});
// Chakra UIのuseToastをモック化
jest.mock('@chakra-ui/react', function () {
    var originalModule = jest.requireActual('@chakra-ui/react');
    return __assign(__assign({}, originalModule), { useToast: jest.fn(function () { return jest.fn(); }) });
});
// HTMLImageElementのsrcプロパティをモック化
Object.defineProperty(HTMLImageElement.prototype, 'src', {
    set: jest.fn(),
    get: jest.fn(function () { return 'http://localhost:8000/api/video_feed'; }),
});
// 全画面API関連のモック
Object.defineProperty(document, 'fullscreenElement', {
    writable: true,
    value: null,
});
Object.defineProperty(document, 'exitFullscreen', {
    writable: true,
    value: jest.fn(function () { return Promise.resolve(); }),
});
// HTMLDivElementのrequestFullscreenをモック化
Object.defineProperty(HTMLDivElement.prototype, 'requestFullscreen', {
    writable: true,
    value: jest.fn(function () { return Promise.resolve(); }),
});
describe('MonitorView Component', function () {
    var mockToast = jest.fn();
    beforeEach(function () {
        jest.clearAllMocks();
        react_2.useToast.mockImplementation(function () { return mockToast; });
        // fullscreenElementを初期状態に戻す
        Object.defineProperty(document, 'fullscreenElement', {
            writable: true,
            value: null,
        });
    });
    test('コンポーネントが正しくレンダリングされる', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
        // 動画が表示されることを確認
        var image = react_1.screen.getByAltText('Monitor');
        expect(image).toBeInTheDocument();
        expect(image).toHaveAttribute('src', 'http://localhost:8000/api/video_feed');
        // 全画面ボタンが表示されることを確認
        var fullscreenButton = react_1.screen.getByLabelText('Toggle fullscreen');
        expect(fullscreenButton).toBeInTheDocument();
        // ステータス情報が表示されることを確認
        expect(react_1.screen.getByText('在席状態:')).toBeInTheDocument();
        expect(react_1.screen.getByText('スマートフォン:')).toBeInTheDocument();
    });
    test('WebSocketマネージャーが初期化される', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
        expect(websocket_1.websocketManager.initialize).toHaveBeenCalled();
        expect(websocket_1.websocketManager.onError).toHaveBeenCalled();
        expect(websocket_1.websocketManager.onStatusUpdate).toHaveBeenCalled();
    });
    test('初期状態で正しいステータスが表示される', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
        // 初期状態では不在とスマートフォン未使用が表示される
        expect(react_1.screen.getByText('不在')).toBeInTheDocument();
        expect(react_1.screen.getByText('未使用')).toBeInTheDocument();
        expect(react_1.screen.getByText('不在時間: 0秒')).toBeInTheDocument();
    });
    test('ステータス更新が正しく反映される', function () { return __awaiter(void 0, void 0, void 0, function () {
        var statusUpdateCallback;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    statusUpdateCallback = function () { };
                    // onStatusUpdateのモックを設定してコールバックを取得
                    websocket_1.websocketManager.onStatusUpdate.mockImplementation(function (callback) {
                        statusUpdateCallback = callback;
                        return jest.fn(); // アンサブスクライブ関数
                    });
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
                    // ステータス更新をシミュレート
                    return [4 /*yield*/, (0, react_1.act)(function () { return __awaiter(void 0, void 0, void 0, function () {
                            return __generator(this, function (_a) {
                                statusUpdateCallback({
                                    personDetected: true,
                                    smartphoneDetected: true,
                                    absenceTime: 0,
                                    smartphoneUseTime: 30
                                });
                                return [2 /*return*/];
                            });
                        }); })];
                case 1:
                    // ステータス更新をシミュレート
                    _a.sent();
                    // 更新されたステータスが表示されることを確認
                    expect(react_1.screen.getByText('在席中')).toBeInTheDocument();
                    expect(react_1.screen.getByText('使用中')).toBeInTheDocument();
                    expect(react_1.screen.getByText('使用時間: 30秒')).toBeInTheDocument();
                    return [2 /*return*/];
            }
        });
    }); });
    test('全画面表示の切り替えが動作する', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, mockRequestFullscreen, container, fullscreenButton;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    user = user_event_1.default.setup();
                    mockRequestFullscreen = jest.fn(function () { return Promise.resolve(); });
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
                    container = (_a = react_1.screen.getByLabelText('Toggle fullscreen').closest('[data-testid]')) === null || _a === void 0 ? void 0 : _a.parentElement;
                    if (container) {
                        container.requestFullscreen = mockRequestFullscreen;
                    }
                    fullscreenButton = react_1.screen.getByLabelText('Toggle fullscreen');
                    // 全画面モードに切り替え
                    return [4 /*yield*/, user.click(fullscreenButton)];
                case 1:
                    // 全画面モードに切り替え
                    _b.sent();
                    // requestFullscreenが呼ばれることを確認
                    expect(mockRequestFullscreen).toHaveBeenCalled();
                    return [2 /*return*/];
            }
        });
    }); });
    test('全画面解除が動作する', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, fullscreenButton;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    // 全画面状態をシミュレート
                    Object.defineProperty(document, 'fullscreenElement', {
                        writable: true,
                        value: document.createElement('div'),
                    });
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
                    fullscreenButton = react_1.screen.getByLabelText('Toggle fullscreen');
                    // 全画面解除
                    return [4 /*yield*/, user.click(fullscreenButton)];
                case 1:
                    // 全画面解除
                    _a.sent();
                    // exitFullscreenが呼ばれることを確認
                    expect(document.exitFullscreen).toHaveBeenCalled();
                    return [2 /*return*/];
            }
        });
    }); });
    test('全画面切り替え中のエラーハンドリング', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, mockRequestFullscreen, container, fullscreenButton;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    user = user_event_1.default.setup();
                    mockRequestFullscreen = jest.fn(function () { return Promise.reject(new Error('Fullscreen error')); });
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
                    container = (_a = react_1.screen.getByLabelText('Toggle fullscreen').closest('[data-testid]')) === null || _a === void 0 ? void 0 : _a.parentElement;
                    if (container) {
                        container.requestFullscreen = mockRequestFullscreen;
                    }
                    fullscreenButton = react_1.screen.getByLabelText('Toggle fullscreen');
                    // エラーが発生する全画面切り替えを実行
                    return [4 /*yield*/, user.click(fullscreenButton)];
                case 1:
                    // エラーが発生する全画面切り替えを実行
                    _b.sent();
                    // エラートーストが表示されることを確認
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
                                title: 'エラー',
                                description: '全画面表示の切り替えに失敗しました',
                                status: 'error',
                            }));
                        })];
                case 2:
                    // エラートーストが表示されることを確認
                    _b.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('WebSocket接続エラーハンドリング', function () { return __awaiter(void 0, void 0, void 0, function () {
        var errorCallback;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    errorCallback = function () { };
                    // onErrorのモックを設定してコールバックを取得
                    websocket_1.websocketManager.onError.mockImplementation(function (callback) {
                        errorCallback = callback;
                        return jest.fn(); // アンサブスクライブ関数
                    });
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
                    // エラーをシミュレート
                    return [4 /*yield*/, (0, react_1.act)(function () { return __awaiter(void 0, void 0, void 0, function () {
                            return __generator(this, function (_a) {
                                errorCallback();
                                return [2 /*return*/];
                            });
                        }); })];
                case 1:
                    // エラーをシミュレート
                    _a.sent();
                    // エラートーストが表示されることを確認
                    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
                        title: '接続エラー',
                        description: 'サーバーとの接続に失敗しました',
                        status: 'error',
                    }));
                    return [2 /*return*/];
            }
        });
    }); });
    test('fullscreenchangeイベントの処理', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
        // fullscreenchangeイベントをシミュレート（全画面モード）
        Object.defineProperty(document, 'fullscreenElement', {
            writable: true,
            value: document.createElement('div'),
        });
        (0, react_1.act)(function () {
            (0, react_1.fireEvent)(document, new Event('fullscreenchange'));
        });
        // 全画面解除のアイコンが表示されることを確認
        var fullscreenButton = react_1.screen.getByLabelText('Toggle fullscreen');
        expect(fullscreenButton).toBeInTheDocument();
        // 通常モードに戻る
        Object.defineProperty(document, 'fullscreenElement', {
            writable: true,
            value: null,
        });
        (0, react_1.act)(function () {
            (0, react_1.fireEvent)(document, new Event('fullscreenchange'));
        });
        // 全画面モードのアイコンが表示されることを確認
        expect(fullscreenButton).toBeInTheDocument();
    });
    test('コンポーネントのクリーンアップが正しく動作する', function () {
        var mockUnsubscribeError = jest.fn();
        var mockUnsubscribeStatus = jest.fn();
        websocket_1.websocketManager.onError.mockImplementation(function () { return mockUnsubscribeError; });
        websocket_1.websocketManager.onStatusUpdate.mockImplementation(function () { return mockUnsubscribeStatus; });
        var unmount = (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) })).unmount;
        // コンポーネントをアンマウント
        unmount();
        // クリーンアップ関数が呼ばれることを確認
        expect(mockUnsubscribeError).toHaveBeenCalled();
        expect(mockUnsubscribeStatus).toHaveBeenCalled();
    });
    test('アクセシビリティが適切に設定されている', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(MonitorView_1.MonitorView, {}) }));
        // 全画面ボタンにaria-labelが設定されていることを確認
        var fullscreenButton = react_1.screen.getByLabelText('Toggle fullscreen');
        expect(fullscreenButton).toBeInTheDocument();
        // 画像にaltが設定されていることを確認
        var image = react_1.screen.getByAltText('Monitor');
        expect(image).toBeInTheDocument();
    });
});
