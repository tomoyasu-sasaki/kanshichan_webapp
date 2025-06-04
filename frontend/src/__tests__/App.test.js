"use strict";
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
var App_1 = __importDefault(require("../App"));
// WebSocketマネージャーをモック化
jest.mock('../utils/websocket', function () { return ({
    websocketManager: {
        initialize: jest.fn(),
        onError: jest.fn(function () { return jest.fn(); }),
        onStatusUpdate: jest.fn(function () { return jest.fn(); }),
        onScheduleAlert: jest.fn(function () { return jest.fn(); }),
        disconnect: jest.fn(),
    },
}); });
// axiosをモック化
jest.mock('axios', function () { return ({
    get: jest.fn(function () { return Promise.resolve({ data: {} }); }),
    post: jest.fn(function () { return Promise.resolve({ data: { success: true } }); }),
}); });
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
Object.defineProperty(HTMLDivElement.prototype, 'requestFullscreen', {
    writable: true,
    value: jest.fn(function () { return Promise.resolve(); }),
});
// fetchをモック化
global.fetch = jest.fn(function () {
    return Promise.resolve({
        ok: true,
        json: function () { return Promise.resolve([]); },
    });
});
describe('App Component', function () {
    beforeEach(function () {
        jest.clearAllMocks();
    });
    test('Appコンポーネントが正しくレンダリングされる', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(App_1.default, {}));
        // アプリケーションタイトルが表示されることを確認
        expect(react_1.screen.getByText('監視ちゃん')).toBeInTheDocument();
        // タブが表示されることを確認
        expect(react_1.screen.getByRole('tab', { name: /監視画面/i })).toBeInTheDocument();
        expect(react_1.screen.getByRole('tab', { name: /設定/i })).toBeInTheDocument();
        expect(react_1.screen.getByRole('tab', { name: /スケジュール/i })).toBeInTheDocument();
    });
    test('初期状態で監視画面タブが選択されている', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(App_1.default, {}));
        // 監視画面タブが選択されていることを確認
        var monitorTab = react_1.screen.getByRole('tab', { name: /監視画面/i });
        expect(monitorTab).toHaveAttribute('aria-selected', 'true');
        // MonitorViewコンポーネントの要素が表示されることを確認
        expect(react_1.screen.getByAltText('Monitor')).toBeInTheDocument();
    });
    test('設定タブをクリックすると設定画面が表示される', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, settingsTab;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(App_1.default, {}));
                    settingsTab = react_1.screen.getByRole('tab', { name: /設定/i });
                    return [4 /*yield*/, user.click(settingsTab)];
                case 1:
                    _a.sent();
                    // 設定タブが選択されていることを確認
                    expect(settingsTab).toHaveAttribute('aria-selected', 'true');
                    // SettingsPanelコンポーネントの要素が表示されることを確認
                    expect(react_1.screen.getByText('監視設定')).toBeInTheDocument();
                    return [2 /*return*/];
            }
        });
    }); });
    test('スケジュールタブをクリックするとスケジュール画面が表示される', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, scheduleTab;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(App_1.default, {}));
                    scheduleTab = react_1.screen.getByRole('tab', { name: /スケジュール/i });
                    return [4 /*yield*/, user.click(scheduleTab)];
                case 1:
                    _a.sent();
                    // スケジュールタブが選択されていることを確認
                    expect(scheduleTab).toHaveAttribute('aria-selected', 'true');
                    // ScheduleViewコンポーネントの要素が表示されることを確認
                    expect(react_1.screen.getByText(/のスケジュール/)).toBeInTheDocument();
                    return [2 /*return*/];
            }
        });
    }); });
    test('タブ間の切り替えが正しく動作する', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(App_1.default, {}));
                    // 初期状態：監視画面
                    expect(react_1.screen.getByRole('tab', { name: /監視画面/i })).toHaveAttribute('aria-selected', 'true');
                    expect(react_1.screen.getByAltText('Monitor')).toBeInTheDocument();
                    // 設定タブに切り替え
                    return [4 /*yield*/, user.click(react_1.screen.getByRole('tab', { name: /設定/i }))];
                case 1:
                    // 設定タブに切り替え
                    _a.sent();
                    expect(react_1.screen.getByRole('tab', { name: /設定/i })).toHaveAttribute('aria-selected', 'true');
                    expect(react_1.screen.getByText('監視設定')).toBeInTheDocument();
                    // スケジュールタブに切り替え
                    return [4 /*yield*/, user.click(react_1.screen.getByRole('tab', { name: /スケジュール/i }))];
                case 2:
                    // スケジュールタブに切り替え
                    _a.sent();
                    expect(react_1.screen.getByRole('tab', { name: /スケジュール/i })).toHaveAttribute('aria-selected', 'true');
                    expect(react_1.screen.getByText(/のスケジュール/)).toBeInTheDocument();
                    // 監視画面タブに戻る
                    return [4 /*yield*/, user.click(react_1.screen.getByRole('tab', { name: /監視画面/i }))];
                case 3:
                    // 監視画面タブに戻る
                    _a.sent();
                    expect(react_1.screen.getByRole('tab', { name: /監視画面/i })).toHaveAttribute('aria-selected', 'true');
                    expect(react_1.screen.getByAltText('Monitor')).toBeInTheDocument();
                    return [2 /*return*/];
            }
        });
    }); });
    test('ChakraProviderが適用されている', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(App_1.default, {}));
        // Chakra UIのクラスが適用されていることを確認
        var container = react_1.screen.getByRole('main') || document.body.firstChild;
        expect(container).toHaveClass('chakra-ui-light');
    });
    test('レスポンシブレイアウトが適用されている', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(App_1.default, {}));
        // コンテナが適切なレイアウトクラスを持っていることを確認
        var tabPanels = react_1.screen.getByRole('tabpanel');
        expect(tabPanels).toBeInTheDocument();
    });
    test('アクセシビリティが適切に設定されている', function () {
        (0, react_1.render)((0, jsx_runtime_1.jsx)(App_1.default, {}));
        // タブリストが適切に設定されていることを確認
        var tabList = react_1.screen.getByRole('tablist');
        expect(tabList).toBeInTheDocument();
        // 各タブが適切にラベル付けされていることを確認
        expect(react_1.screen.getByRole('tab', { name: /監視画面/i })).toBeInTheDocument();
        expect(react_1.screen.getByRole('tab', { name: /設定/i })).toBeInTheDocument();
        expect(react_1.screen.getByRole('tab', { name: /スケジュール/i })).toBeInTheDocument();
        // タブパネルが適切に設定されていることを確認
        expect(react_1.screen.getByRole('tabpanel')).toBeInTheDocument();
    });
});
