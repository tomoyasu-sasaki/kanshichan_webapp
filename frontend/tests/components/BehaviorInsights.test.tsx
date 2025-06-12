import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BehaviorInsights } from '../../src/components/BehaviorInsights';
import '@testing-library/jest-dom';
import { ChakraProvider } from '@chakra-ui/react';

// モックサービス
jest.mock('../../src/utils/logger', () => ({
  logger: {
    info: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  },
}));

// fetch モック
global.fetch = jest.fn();

describe('BehaviorInsights Component', () => {
  const mockRecommendationsResponse = {
    status: 'success',
    data: {
      recommendations: [
        {
          type: 'focus_improvement',
          priority: 'high',
          message: '集中力向上のための推奨事項です',
          action: 'focus_training',
          source: 'behavior_analysis',
          timestamp: new Date().toISOString(),
        },
        {
          type: 'contextual_advice',
          priority: 'medium',
          message: '音声機能付きアドバイスメッセージ',
          emotion: 'encouraging',
          source: 'llm_advice',
          timestamp: new Date().toISOString(),
          audio_url: '/api/tts/test.mp3',
          tts_requested: true,
        },
      ],
      pagination: {
        page: 1,
        limit: 5,
        total_items: 7,
        total_pages: 2,
      },
    },
    timestamp: new Date().toISOString(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/analysis/basic/recommendations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockRecommendationsResponse),
        });
      }
      
      // その他のAPIコールは空のデータを返す
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'success', data: {} }),
      });
    });

    // AudioオブジェクトのモックとPlay関数のモック
    global.Audio = jest.fn().mockImplementation(() => ({
      play: jest.fn().mockResolvedValue(undefined),
    }));

    // クリップボードAPI モック
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn(),
      },
    });
  });

  test('改善提案を表示する', async () => {
    render(
      <ChakraProvider>
        <BehaviorInsights />
      </ChakraProvider>
    );
    
    // 初期表示を確認
    expect(screen.getByText('行動分析インサイト')).toBeInTheDocument();
    
    // モックデータの内容が表示されることを確認
    await waitFor(() => {
      expect(screen.getByText('集中力が低下しています')).toBeInTheDocument();
    });
    
    // 優先度バッジが表示されていることを確認
    expect(screen.getAllByText('重要')[0]).toBeInTheDocument();
    expect(screen.getByText('普通')).toBeInTheDocument();
  });

  test('優先度タブで絞り込みができる', async () => {
    // モックデータを準備
    // high priorityのデータだけを含むレスポンスを作成
    const highPriorityResponse = {
      status: 'success',
      data: {
        recommendations: [
          {
            type: 'focus_improvement',
            priority: 'high',
            message: '集中力向上のための推奨事項です',
            action: 'focus_training',
            source: 'behavior_analysis',
            timestamp: new Date().toISOString(),
          }
        ],
        pagination: {
          page: 1,
          limit: 5,
          total_items: 1,
          total_pages: 1,
        },
      },
      timestamp: new Date().toISOString(),
    };

    // テスト用のモックを上書き
    (global.fetch as jest.Mock).mockImplementation((url) => {
      console.log('Mock fetch called with URL:', url);
      
      if (url.includes('priority=high')) {
        console.log('Returning high priority response');
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(highPriorityResponse),
        });
      } else if (url.includes('/api/analysis/basic/recommendations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockRecommendationsResponse),
        });
      }
      
      // その他のAPIコールは空のデータを返す
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'success', data: {} }),
      });
    });

    render(
      <ChakraProvider>
        <BehaviorInsights />
      </ChakraProvider>
    );
    
    // 初期表示のローディングを待つ
    await waitFor(() => {
      expect(screen.getByText('行動分析インサイト')).toBeInTheDocument();
    });

    // タブのマウントを待つ
    await waitFor(() => {
      const allTabs = screen.getAllByRole('tab');
      expect(allTabs.length).toBeGreaterThan(0);
    });
    
    // タブの中から「重要」を見つけてクリック
    const importantTab = screen.getByRole('tab', { name: '重要' });
    fireEvent.click(importantTab);
    
    // モックfetchがpriority=highで呼ばれることを確認
    await waitFor(() => {
      const calls = (global.fetch as jest.Mock).mock.calls;
      const highPriorityCall = calls.find((call: Array<string | Record<string, unknown>>) => 
        typeof call[0] === 'string' && call[0].includes('priority=high')
      );
      expect(highPriorityCall).toBeTruthy();
    }, { timeout: 3000 });
    
    // 結果が絞り込まれたことを確認（これは上記が成功していれば不要かもしれない）
    await waitFor(() => {
      // 重要タグの付いた提案が表示されていることを確認
      expect(screen.getAllByText('重要').length).toBeGreaterThan(0);
      
      // レスポンスの内容が表示されていることを確認
      expect(screen.getByText('集中力向上のための推奨事項です')).toBeInTheDocument();
      
      // 「普通」優先度の項目はレスポンスに含まれていないはずなので
      // 表示されるはずがない
      expect(screen.queryByText('音声機能付きアドバイスメッセージ')).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test('ページネーションが機能する', async () => {
    render(
      <ChakraProvider>
        <BehaviorInsights />
      </ChakraProvider>
    );

    // ローディングが完了するのを待つ
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/analysis/basic/recommendations'));
    });

    // 「もっと見る」ボタンが表示されていることを確認
    const loadMoreButton = await screen.findByText('もっと見る');
    expect(loadMoreButton).toBeInTheDocument();

    // 「もっと見る」ボタンをクリック
    fireEvent.click(loadMoreButton);

    // 2ページ目がリクエストされることを確認
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('page=2'));
    });
  });

  test('音声ボタンが機能する', async () => {
    // Audio APIのモック
    const mockPlay = jest.fn();
    const originalAudio = global.Audio;
    global.Audio = jest.fn().mockImplementation(() => ({
      play: mockPlay,
    }));

    render(
      <ChakraProvider>
        <BehaviorInsights />
      </ChakraProvider>
    );
    
    // 音声ボタンをクリック
    await waitFor(() => {
      screen.getByLabelText('音声で読み上げ');
    });

    fireEvent.click(screen.getByLabelText('音声で読み上げ'));
    
    // Audio.play()が呼ばれていることを確認
    await waitFor(() => {
      expect(mockPlay).toHaveBeenCalled();
    });

    // モックをリストア
    global.Audio = originalAudio;
  });
}); 