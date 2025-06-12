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

    // ローディングが完了するのを待つ
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/analysis/basic/recommendations'));
    });

    // 推奨メッセージが表示されていることを確認
    await waitFor(() => {
      expect(screen.getByText('集中力向上のための推奨事項です')).toBeInTheDocument();
      expect(screen.getByText('音声機能付きアドバイスメッセージ')).toBeInTheDocument();
    });

    // 優先度バッジが表示されていることを確認
    expect(screen.getByText('重要')).toBeInTheDocument();
    expect(screen.getByText('普通')).toBeInTheDocument();
  });

  test('優先度タブで絞り込みができる', async () => {
    render(
      <ChakraProvider>
        <BehaviorInsights />
      </ChakraProvider>
    );

    // ローディングが完了するのを待つ
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/analysis/basic/recommendations'));
    });

    // 「重要」タブをクリック
    fireEvent.click(screen.getByText('重要'));

    // APIが適切なパラメータで呼び出されることを確認
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('priority=high'));
    });
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
    render(
      <ChakraProvider>
        <BehaviorInsights />
      </ChakraProvider>
    );

    // ローディングが完了するのを待つ
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/analysis/basic/recommendations'));
    });

    // 音声ボタンを探して実行
    const audioButtons = await screen.findAllByLabelText('音声再生');
    expect(audioButtons.length).toBeGreaterThan(0);
    
    fireEvent.click(audioButtons[0]);

    // Audio.play()が呼ばれていることを確認
    await waitFor(() => {
      expect(Audio.prototype.play).toHaveBeenCalled();
    });
  });
}); 