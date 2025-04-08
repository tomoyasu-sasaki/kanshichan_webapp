import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChakraProvider, useToast } from '@chakra-ui/react';
import { ScheduleView } from '../ScheduleView';
import { websocketManager } from '../../utils/websocket';

// WebSocketマネージャーをモック化
jest.mock('../../utils/websocket', () => {
  const originalModule = jest.requireActual('../../utils/websocket');
  return {
    ...originalModule,
    websocketManager: {
      initialize: jest.fn(),
      onScheduleAlert: jest.fn(() => jest.fn()), // アンサブスクライブ関数を返す
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

// fetchをモック化
global.fetch = jest.fn();

describe('ScheduleView Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // モックのfetch実装
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/schedules' && !options?.method) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { id: '1', time: '09:00', content: '朝のミーティング' },
            { id: '2', time: '12:30', content: '昼食' }
          ])
        });
      } else if (url === '/api/schedules' && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: '3', time: '15:00', content: 'テスト' })
        });
      } else if (url.includes('/api/schedules/')) {
        return Promise.resolve({
          ok: true
        });
      }
      
      return Promise.reject(new Error('モックされていないURL'));
    });
  });

  test('コンポーネントが正しくレンダリングされる', async () => {
    render(
      <ChakraProvider>
        <ScheduleView />
      </ChakraProvider>
    );
    
    // ヘッダーが表示されることを確認
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
    
    // フォームが表示されることを確認
    expect(screen.getByLabelText(/時刻/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/内容/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /追加/i })).toBeInTheDocument();
    
    // スケジュールデータがロードされるのを待つ
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/schedules');
    });
    
    // スケジュールアイテムが表示されることを確認
    await waitFor(() => {
      expect(screen.getByText('朝のミーティング')).toBeInTheDocument();
      expect(screen.getByText('昼食')).toBeInTheDocument();
    });
  });

  test('WebSocketマネージャーが初期化され、スケジュールアラートのリスナーが登録される', () => {
    render(
      <ChakraProvider>
        <ScheduleView />
      </ChakraProvider>
    );
    
    expect(websocketManager.initialize).toHaveBeenCalled();
    expect(websocketManager.onScheduleAlert).toHaveBeenCalled();
  });

  test('スケジュールフォームの入力と送信', async () => {
    const user = userEvent.setup();
    
    render(
      <ChakraProvider>
        <ScheduleView />
      </ChakraProvider>
    );
    
    // フォームに入力
    const timeInput = screen.getByLabelText(/時刻/i);
    const contentInput = screen.getByLabelText(/内容/i);
    const addButton = screen.getByRole('button', { name: /追加/i });
    
    await user.type(timeInput, '15:00');
    await user.type(contentInput, 'テスト');
    
    // フォームを送信
    await user.click(addButton);
    
    // POSTリクエストが正しく送信されたか確認
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/schedules', expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        }),
        body: expect.any(String)
      }));
    });
    
    // フォームがリセットされたか確認
    await waitFor(() => {
      expect(timeInput).toHaveValue('');
      expect(contentInput).toHaveValue('');
    });
  });

  test('スケジュールの削除', async () => {
    const user = userEvent.setup();
    
    render(
      <ChakraProvider>
        <ScheduleView />
      </ChakraProvider>
    );
    
    // スケジュールデータがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByText('朝のミーティング')).toBeInTheDocument();
    });
    
    // 削除ボタンをクリック
    const deleteButtons = screen.getAllByRole('button', { name: /削除/i });
    await user.click(deleteButtons[0]);
    
    // DELETEリクエストが正しく送信されたか確認
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(expect.stringMatching(/\/api\/schedules\/\d+/), expect.objectContaining({
        method: 'DELETE'
      }));
    });
  });

  test('バリデーションエラー：空の入力値', async () => {
    const user = userEvent.setup();
    const mockToast = jest.fn();
    
    // useToastをモック化
    (useToast as jest.Mock).mockImplementation(() => mockToast);
    
    render(
      <ChakraProvider>
        <ScheduleView />
      </ChakraProvider>
    );
    
    // 内容だけを入力して送信（時刻が空）
    const contentInput = screen.getByLabelText(/内容/i);
    const addButton = screen.getByRole('button', { name: /追加/i });
    
    await user.type(contentInput, 'テスト内容');
    await user.click(addButton);
    
    // トーストが表示されることを確認
    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
      title: '入力エラー',
      status: 'warning',
    }));
    
    jest.clearAllMocks();
    
    // 時刻だけを入力して送信（内容が空）
    const timeInput = screen.getByLabelText(/時刻/i);
    await user.clear(contentInput);
    await user.type(timeInput, '15:00');
    await user.click(addButton);
    
    // トーストが表示されることを確認
    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
      title: '入力エラー',
      status: 'warning',
    }));
  });
}); 