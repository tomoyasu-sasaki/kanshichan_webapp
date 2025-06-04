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
var SettingsPanel_1 = require("../SettingsPanel");
var axios_1 = __importDefault(require("axios"));
// axiosをモック化
jest.mock('axios');
var mockedAxios = axios_1.default;
// Chakra UIのuseToastをモック化
jest.mock('@chakra-ui/react', function () {
    var originalModule = jest.requireActual('@chakra-ui/react');
    return __assign(__assign({}, originalModule), { useToast: jest.fn(function () { return jest.fn(); }) });
});
describe('SettingsPanel Component', function () {
    var mockToast = jest.fn();
    var mockSettingsData = {
        absence_threshold: 5,
        smartphone_threshold: 3,
        message_extensions: {
            '休憩中': 600,
            '外出中': 1800
        },
        landmark_settings: {
            nose: { enabled: true, name: '鼻' },
            left_eye: { enabled: false, name: '左目' },
            right_eye: { enabled: true, name: '右目' }
        },
        detection_objects: {
            person: {
                enabled: true,
                name: '人物',
                confidence_threshold: 0.5,
                alert_threshold: 5
            },
            cell_phone: {
                enabled: true,
                name: 'スマートフォン',
                confidence_threshold: 0.7,
                alert_threshold: 3
            }
        }
    };
    beforeEach(function () {
        jest.clearAllMocks();
        react_2.useToast.mockImplementation(function () { return mockToast; });
        // デフォルトの成功レスポンス
        mockedAxios.get.mockResolvedValue({ data: mockSettingsData });
        mockedAxios.post.mockResolvedValue({ data: { success: true } });
    });
    test('コンポーネントが正しくレンダリングされる', function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
            // ヘッダーが表示されることを確認
            expect(react_1.screen.getByText('監視設定')).toBeInTheDocument();
            // 基本的な設定項目が表示されることを確認
            expect(react_1.screen.getByText('不在検知閾値（秒）')).toBeInTheDocument();
            expect(react_1.screen.getByText('スマートフォン使用検知閾値（秒）')).toBeInTheDocument();
            // 保存ボタンが表示されることを確認
            expect(react_1.screen.getByRole('button', { name: /保存/i })).toBeInTheDocument();
            return [2 /*return*/];
        });
    }); });
    test('初期設定データが正しく読み込まれる', function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // APIが呼ばれることを確認
                    expect(mockedAxios.get).toHaveBeenCalledWith('/api/settings');
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            // 閾値が正しく表示されることを確認
                            var absenceInput = react_1.screen.getByLabelText('不在検知閾値（秒）');
                            var smartphoneInput = react_1.screen.getByLabelText('スマートフォン使用検知閾値（秒）');
                            expect(absenceInput).toHaveValue(5);
                            expect(smartphoneInput).toHaveValue(3);
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('設定データの取得エラーハンドリング', function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    mockedAxios.get.mockRejectedValue(new Error('Network Error'));
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // エラートーストが表示されることを確認
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
                                title: 'エラー',
                                description: '設定の取得に失敗しました',
                                status: 'error',
                            }));
                        })];
                case 1:
                    // エラートーストが表示されることを確認
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('閾値の変更が動作する', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, absenceInput, smartphoneInput;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByDisplayValue('5')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    absenceInput = react_1.screen.getByLabelText('不在検知閾値（秒）');
                    return [4 /*yield*/, user.clear(absenceInput)];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, user.type(absenceInput, '10')];
                case 3:
                    _a.sent();
                    smartphoneInput = react_1.screen.getByLabelText('スマートフォン使用検知閾値（秒）');
                    return [4 /*yield*/, user.clear(smartphoneInput)];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, user.type(smartphoneInput, '5')];
                case 5:
                    _a.sent();
                    // 値が更新されることを確認
                    expect(absenceInput).toHaveValue(10);
                    expect(smartphoneInput).toHaveValue(5);
                    return [2 /*return*/];
            }
        });
    }); });
    test('ランドマーク設定の切り替えが動作する', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, leftEyeSwitch;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByText('鼻')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    leftEyeSwitch = react_1.screen.getByRole('checkbox', { name: /左目/i });
                    return [4 /*yield*/, user.click(leftEyeSwitch)];
                case 2:
                    _a.sent();
                    // スイッチの状態が変わることを確認
                    expect(leftEyeSwitch).toBeChecked();
                    return [2 /*return*/];
            }
        });
    }); });
    test('検出オブジェクト設定の変更が動作する', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, personSwitch;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByText('人物')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    personSwitch = react_1.screen.getByRole('checkbox', { name: /人物/i });
                    return [4 /*yield*/, user.click(personSwitch)];
                case 2:
                    _a.sent();
                    // スイッチの状態が変わることを確認
                    expect(personSwitch).not.toBeChecked();
                    return [2 /*return*/];
            }
        });
    }); });
    test('設定の保存が正常に動作する', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, absenceInput, saveButton;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByDisplayValue('5')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    absenceInput = react_1.screen.getByLabelText('不在検知閾値（秒）');
                    return [4 /*yield*/, user.clear(absenceInput)];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, user.type(absenceInput, '8')];
                case 3:
                    _a.sent();
                    saveButton = react_1.screen.getByRole('button', { name: /保存/i });
                    return [4 /*yield*/, user.click(saveButton)];
                case 4:
                    _a.sent();
                    // POSTリクエストが正しく送信されることを確認
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(mockedAxios.post).toHaveBeenCalledWith('/api/settings', expect.objectContaining({
                                absence_threshold: 8,
                                smartphone_threshold: 3,
                            }));
                        })];
                case 5:
                    // POSTリクエストが正しく送信されることを確認
                    _a.sent();
                    // 成功トーストが表示されることを確認
                    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
                        title: '成功',
                        description: '設定を保存しました',
                        status: 'success',
                    }));
                    return [2 /*return*/];
            }
        });
    }); });
    test('設定保存時のエラーハンドリング', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, saveButton;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    mockedAxios.post.mockRejectedValue(new Error('Save Error'));
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByDisplayValue('5')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    saveButton = react_1.screen.getByRole('button', { name: /保存/i });
                    return [4 /*yield*/, user.click(saveButton)];
                case 2:
                    _a.sent();
                    // エラートーストが表示されることを確認
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
                                title: 'エラー',
                                description: '設定の保存に失敗しました',
                                status: 'error',
                            }));
                        })];
                case 3:
                    // エラートーストが表示されることを確認
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('メッセージ延長設定が表示される', function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByText('LINEメッセージ設定')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    // メッセージ延長設定の項目が表示されることを確認
                    expect(react_1.screen.getByText('休憩中')).toBeInTheDocument();
                    expect(react_1.screen.getByText('外出中')).toBeInTheDocument();
                    return [2 /*return*/];
            }
        });
    }); });
    test('メッセージ延長時間の変更が動作する', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, breakExtensionInput;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByDisplayValue('600')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    breakExtensionInput = react_1.screen.getByDisplayValue('600');
                    return [4 /*yield*/, user.clear(breakExtensionInput)];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, user.type(breakExtensionInput, '900')];
                case 3:
                    _a.sent();
                    // 値が更新されることを確認
                    expect(breakExtensionInput).toHaveValue(900);
                    return [2 /*return*/];
            }
        });
    }); });
    test('検出オブジェクトの信頼度閾値変更が動作する', function () { return __awaiter(void 0, void 0, void 0, function () {
        var user, confidenceInputs;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    user = user_event_1.default.setup();
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByText('人物')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    confidenceInputs = react_1.screen.getAllByDisplayValue('0.5');
                    if (!(confidenceInputs.length > 0)) return [3 /*break*/, 4];
                    return [4 /*yield*/, user.clear(confidenceInputs[0])];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, user.type(confidenceInputs[0], '0.8')];
                case 3:
                    _a.sent();
                    expect(confidenceInputs[0]).toHaveValue(0.8);
                    _a.label = 4;
                case 4: return [2 /*return*/];
            }
        });
    }); });
    test('すべての設定項目が適切にラベル付けされている', function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // アクセシビリティラベルが適切に設定されていることを確認
                    expect(react_1.screen.getByLabelText('不在検知閾値（秒）')).toBeInTheDocument();
                    expect(react_1.screen.getByLabelText('スマートフォン使用検知閾値（秒）')).toBeInTheDocument();
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByText('鼻')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    // 各ランドマーク設定にアクセシビリティが設定されていることを確認
                    expect(react_1.screen.getByRole('checkbox', { name: /鼻/i })).toBeInTheDocument();
                    expect(react_1.screen.getByRole('checkbox', { name: /左目/i })).toBeInTheDocument();
                    expect(react_1.screen.getByRole('checkbox', { name: /右目/i })).toBeInTheDocument();
                    return [2 /*return*/];
            }
        });
    }); });
    test('設定項目が適切にグループ化されている', function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    (0, react_1.render)((0, jsx_runtime_1.jsx)(react_2.ChakraProvider, { children: (0, jsx_runtime_1.jsx)(SettingsPanel_1.SettingsPanel, {}) }));
                    // セクション見出しが表示されることを確認
                    expect(react_1.screen.getByText('監視設定')).toBeInTheDocument();
                    // データがロードされるのを待つ
                    return [4 /*yield*/, (0, react_1.waitFor)(function () {
                            expect(react_1.screen.getByText('LINEメッセージ設定')).toBeInTheDocument();
                        })];
                case 1:
                    // データがロードされるのを待つ
                    _a.sent();
                    // 各セクションの見出しが正しく表示されることを確認
                    expect(react_1.screen.getByText('LINEメッセージ設定')).toBeInTheDocument();
                    return [2 /*return*/];
            }
        });
    }); });
});
