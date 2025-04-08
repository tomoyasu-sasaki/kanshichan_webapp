// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
import '@testing-library/jest-dom';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock window.alert
window.alert = jest.fn();

// すべてのメソッドをモック化した簡易的なWebSocketモック
const mockWebSocketInstance = {
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  send: jest.fn(),
  close: jest.fn(),
};

// WebSocketコンストラクタをモック化
global.WebSocket = jest.fn(() => mockWebSocketInstance) as unknown as typeof WebSocket;

// 定数を追加
Object.defineProperties(global.WebSocket, {
  CONNECTING: { value: 0 },
  OPEN: { value: 1 },
  CLOSING: { value: 2 },
  CLOSED: { value: 3 }
}); 