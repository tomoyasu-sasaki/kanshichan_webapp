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
// React import is handled by JSX runtime
var react_1 = require("@testing-library/react");
var user_event_1 = __importDefault(require("@testing-library/user-event"));
var react_2 = require("@chakra-ui/react");
var ScheduleView_1 = require("../ScheduleView");
var websocket_1 = require("../../utils/websocket");
// WebSocketマネージャーをモック化
jest.mock('../../utils/websocket', function () {
    var originalModule = jest.requireActual('../../utils/websocket');
    return __assign(__assign({}, originalModule), { websocketManager: {
            initialize: jest.fn(),
            onScheduleAlert: jest.fn(function () { return jest.fn(); }), // アンサブスクライブ関数を返す
        } });
});
// Chakra UIのuseToastをモック化
jest.mock('@chakra-ui/react', function () {
    var originalModule = jest.requireActual('@chakra-ui/react');
    return __assign(__assign({}, originalModule), { useToast: jest.fn(function () { return jest.fn(); }) });
});
// fetchをモック化
global.fetch = jest.fn();
describe('ScheduleView Component', function () {
    beforeEach(function () {
        jest.clearAllMocks();
        // モックのfetch実装
        global.fetch.mockImplementation(function (url, options) {
            if (url === '/api/schedules' && !(options === null || options === void 0 ? void 0 : options.method)) {
                return Promise.resolve({
                    ok: true,
                    json: function () { return Promise.resolve([
                        { id: '1', time: '09:00', content: '朝のミーティング' },
                        { id: '2', time: '12:30', content: '昼食' }
                    ]); }
                });
            }
            else if (url === '/api/schedules' && (options === null || options === void 0 ? void 0 : options.method) === 'POST') {
                return Promise.resolve({
                    ok: true,
                    json: function () { return Promise.resolve({ id: '3', time: '15:00', content: 'テスト' }); }
                });
            }
            else if (url.includes('/api/schedules/')) {
                return Promise.resolve({
                    ok: true
                });
            }
            return Promise.reject(new Error('モックされていないURL'));
        });
    });
    test('コンポーネントが正しくレンダリングされる', function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(ScheduleView_1.ScheduleView, {}) }));
                    // ヘッダーが表示されることを確認
                    expect(react_1.screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
                    // フォームが表示されることを確認
                    expect(react_1.screen.getByLabelText(/時刻/i)).toBeInTheDocument();
                    expect(react_1.screen.getByLabelText(/内容/i)).toBeInTheDocument();
                    expect(react_1.screen.getByRole('button', { name: /追加/i })).toBeInTheDocument();
                    // スケジュールデータがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(global.fetch).toHaveBeenCalledWith('/api/schedules');
                        })];
                case 1:
                    // スケジュールデータがロードされるのを待つ
                    _a.sent();
                    // スケジュールアイテムが表示されることを確認
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByText('朝のミーティング')).toBeInTheDocument();
                            expect(react_1.screen.getByText('昼食')).toBeInTheDocument();
                        })];
                case 2:
                    // スケジュールアイテムが表示されることを確認
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('WebSocketマネージャーが初期化され、スケジュールアラートのリスナーが登録される', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(ScheduleView_1.ScheduleView, {}) }));
        expect(websocket_1.websocketManager.initialize).toHaveBeenCalled();
        expect(websocket_1.websocketManager.onScheduleAlert).toHaveBeenCalled();
    });
    test('スケジュールフォームの入力と送信', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, timeInput, contentInput, addButton;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(ScheduleView_1.ScheduleView, {}) }));
                    timeInput = react_1.screen.getByLabelText(/時刻/i);
                    contentInput = react_1.screen.getByLabelText(/内容/i);
                    addButton = react_1.screen.getByRole('button', { name: /追加/i });
                    return [4 /*yield*/, user.type(timeInput, '15:00')];
                case 1:
                    _a.sent();
                    return [4 /*yield*/, user.type(contentInput, 'テスト')];
                case 2:
                    _a.sent();
                    // フォームを送信
                    return [4 /*yield*/, user.click(addButton)];
                case 3:
                    // フォームを送信
                    _a.sent();
                    // POSTリクエストが正しく送信されたか確認
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(global.fetch).toHaveBeenCalledWith('/api/schedules', expect.objectContaining({
                                method: 'POST',
                                headers: expect.objectContaining({
                                    'Content-Type': 'application/json'
                                }),
                                body: expect.any(String)
                            }));
                        })];
                case 4:
                    // POSTリクエストが正しく送信されたか確認
                    _a.sent();
                    // フォームがリセットされたか確認
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(timeInput).toHaveValue('');
                            expect(contentInput).toHaveValue('');
                        })];
                case 5:
                    // フォームがリセットされたか確認
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('スケジュールの削除', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, deleteButtons;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(ScheduleView_1.ScheduleView, {}) }));
                    // スケジュールデータがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByText('朝のミーティング')).toBeInTheDocument();
                        })];
                case 1:
                    // スケジュールデータがロードされるのを待つ
                    _a.sent();
                    deleteButtons = react_1.screen.getAllByRole('button', { name: /削除/i });
                    return [4 /*yield*/, user.click(deleteButtons[0])];
                case 2:
                    _a.sent();
                    // DELETEリクエストが正しく送信されたか確認
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(global.fetch).toHaveBeenCalledWith(expect.stringMatching(/\/api\/schedules\/\d+/), expect.objectContaining({
                                method: 'DELETE'
                            }));
                        })];
                case 3:
                    // DELETEリクエストが正しく送信されたか確認
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('バリデーションエラー：空の入力値', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, mockToast, contentInput, addButton, timeInput;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    mockToast = jest.fn();
                    // useToastをモック化
                    react_2.useToast.mockImplementation(function () { return mockToast; });
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(ScheduleView_1.ScheduleView, {}) }));
                    contentInput = react_1.screen.getByLabelText(/内容/i);
                    addButton = react_1.screen.getByRole('button', { name: /追加/i });
                    return [4 /*yield*/, user.type(contentInput, 'テスト内容')];
                case 1:
                    _a.sent();
                    return [4 /*yield*/, user.click(addButton)];
                case 2:
                    _a.sent();
                    // トーストが表示されることを確認
                    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
                        title: '入力エラー',
                        status: 'warning',
                    }));
                    jest.clearAllMocks();
                    timeInput = react_1.screen.getByLabelText(/時刻/i);
                    return [4 /*yield*/, user.clear(contentInput)];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, user.type(timeInput, '15:00')];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, user.click(addButton)];
                case 5:
                    _a.sent();
                    // トーストが表示されることを確認
                    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
                        title: '入力エラー',
                        status: 'warning',
                    }));
                    return [2 /*return*/];
            }
        });
    }); });
});
