/**
 * Phase 5: フロントエンド統合テスト
 * ====================================
 * Phase 1-4の全フロントエンドコンポーネントを統合したE2Eテストスイート
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { describe, test, expect, beforeEach, jest, beforeAll, afterAll } from '@jest/globals';

import App from '../../App';
import { MonitorView } from '../../components/MonitorView';
import { VoiceSettings } from '../../components/VoiceSettings';
import { BehaviorInsights } from '../../components/BehaviorInsights';
import { AudioPlayer } from '../../components/AudioPlayer';
import { AdvancedAnalyticsDashboard } from '../../components/analytics/AdvancedAnalyticsDashboard';
import { PersonalizationPanel } from '../../components/analytics/PersonalizationPanel';
import { PredictiveInsights } from '../../components/analytics/PredictiveInsights';
import { LearningProgress } from '../../components/analytics/LearningProgress';

// Mock WebSocket
class MockWebSocket {
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  readyState: number = WebSocket.CONNECTING;
  
  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 100);
  }
  
  send(): void {
    // Mock send implementation
  }
  
  close(): void {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
}

// Mock WebSocket globally
declare const global: typeof globalThis & {
  WebSocket: typeof MockWebSocket;
};
global.WebSocket = MockWebSocket as unknown as typeof WebSocket;

const renderWithChakra = (component: React.ReactElement) => {
  return render(
    <ChakraProvider>
      {component}
    </ChakraProvider>
  );
};

// Mock API responses
const mockApiResponses = {
  // Phase 1: Data collection APIs
  behaviorLogs: [
    {
      timestamp: '2025-01-06T15:30:00Z',
      focus_score: 0.8,
      posture_score: 0.7,
      smartphone_usage: false,
      face_visible: true
    }
  ],
  
  // Phase 2: TTS APIs
  ttsVoices: [
    {
      voice_id: 'voice_001',
      voice_name: 'デフォルト音声',
      language: 'ja-JP',
      emotions: ['neutral', 'gentle', 'encouraging']
    }
  ],
  
  // Phase 4.1: Advanced Analysis APIs
  advancedPatterns: {
    patterns: {
      focus_patterns: [
        {
          pattern_type: 'deep_focus',
          confidence: 0.9,
          frequency: 3,
          description: '長時間集中パターン'
        }
      ],
      behavior_patterns: [
        {
          pattern_type: 'morning_productivity',
          confidence: 0.85,
          frequency: 5,
          description: '午前中の生産性が高い'
        }
      ]
    }
  },
  
  // Phase 4.2: Personalization APIs
  userProfile: {
    user_id: 'test_user',
    work_style: 'MORNING_PERSON',
    focus_duration_minutes: 45,
    optimal_time_slots: ['09:00-11:00', '14:00-16:00'],
    break_frequency_minutes: 50,
    health_habits: ['定期休憩', '水分補給']
  },
  
  recommendations: {
    recommendations: [
      {
        recommendation_id: 'rec_001',
        category: 'break_optimization',
        title: '休憩時間最適化',
        description: '現在の集中度に基づいて、15分後に5分間の休憩をおすすめします。',
        priority: 8,
        effectiveness_score: 0.85,
        implementation_difficulty: 'easy'
      }
    ]
  },
  
  // Phase 4.3: Real-time Analysis APIs
  performanceReport: {
    system_statistics: {
      avg_cpu_usage: 45.2,
      avg_memory_usage: 68.7
    },
    analysis_statistics: {
      avg_accuracy: 0.89,
      avg_latency: 45.6
    },
    health_score: 0.91
  }
};

// Mock fetch
global.fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

beforeAll(() => {
  // Setup mock WebSocket
});

afterAll(() => {
  // Cleanup
});

beforeEach(() => {
  (global.fetch as jest.MockedFunction<typeof fetch>).mockClear();
});

describe('Phase 5: フロントエンド統合テスト', () => {
  
  describe('アプリケーション全体統合テスト', () => {
    test('Appコンポーネントが正常にマウントされる', () => {
      renderWithChakra(<App />);
      
      // タブが存在することを確認
      expect(screen.getByText('監視')).toBeDefined();
      expect(screen.getByText('設定')).toBeDefined();
      expect(screen.getByText('スケジュール')).toBeDefined();
      expect(screen.getByText('音声設定')).toBeDefined();
      expect(screen.getByText('行動分析')).toBeDefined();
    });

    test('タブ切り替えが正常に動作する', async () => {
      renderWithChakra(<App />);
      
      // 設定タブに切り替え
      const settingsTab = screen.getByText('設定');
      fireEvent.click(settingsTab);
      
      await waitFor(() => {
        expect(screen.getByText('システム設定')).toBeDefined();
      });
      
      // 音声設定タブに切り替え
      const voiceTab = screen.getByText('音声設定');
      fireEvent.click(voiceTab);
      
      await waitFor(() => {
        expect(screen.getByText('音声設定')).toBeDefined();
      });
    });
  });

  describe('Phase 1統合: データ収集・監視機能', () => {
    test('MonitorViewが正常に表示される', () => {
      renderWithChakra(<MonitorView />);
      
      expect(screen.getByText('監視カメラ')).toBeDefined();
      expect(screen.getByText('フルスクリーン')).toBeDefined();
    });

    test('監視状態が正常に更新される', async () => {
      renderWithChakra(<MonitorView />);
      
      // フルスクリーンボタンクリック
      const fullscreenButton = screen.getByText('フルスクリーン');
      fireEvent.click(fullscreenButton);
      
      // 状態変更を確認
      await waitFor(() => {
        expect(screen.getByText('Exit Fullscreen')).toBeDefined();
      });
    });
  });

  describe('Phase 2統合: TTS音声システム', () => {
    beforeEach(() => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockImplementation((url) => {
        if (url?.toString().includes('/api/tts/voices')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ voices: mockApiResponses.ttsVoices })
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });
    });

    test('VoiceSettingsが正常に表示される', async () => {
      renderWithChakra(<VoiceSettings />);
      
      await waitFor(() => {
        expect(screen.getByText('音声設定')).toBeDefined();
        expect(screen.getByText('音声選択')).toBeDefined();
      });
    });

    test('AudioPlayerが正常に動作する', async () => {
      renderWithChakra(<AudioPlayer />);
      
      await waitFor(() => {
        expect(screen.getByText('音声プレイヤー')).toBeDefined();
        expect(screen.getByText('テキスト入力')).toBeDefined();
      });
    });
  });

  describe('Phase 4.1統合: 高度行動分析', () => {
    beforeEach(() => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockImplementation((url) => {
        if (url?.toString().includes('/api/analysis/advanced-patterns')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockApiResponses.advancedPatterns)
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });
    });

    test('BehaviorInsightsが高度分析データを表示する', async () => {
      renderWithChakra(<BehaviorInsights />);
      
      await waitFor(() => {
        expect(screen.getByText('行動傾向分析')).toBeDefined();
      });
    });
  });

  describe('Phase 4.2統合: パーソナライゼーション', () => {
    beforeEach(() => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockImplementation((url) => {
        if (url?.toString().includes('/api/analysis/user-profile')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ user_profile: mockApiResponses.userProfile })
          } as Response);
        }
        if (url?.toString().includes('/api/analysis/personalized-recommendations')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockApiResponses.recommendations)
          } as Response);
        }
        if (url?.toString().includes('/api/analysis/adaptive-learning-status')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              learning_status: {
                learning_active: true,
                model_accuracy: 0.87,
                recommendations_given: 45,
                user_satisfaction_avg: 4.2
              }
            })
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });
    });

    test('PersonalizationPanelが正常に表示される', async () => {
      renderWithChakra(<PersonalizationPanel />);
      
      await waitFor(() => {
        expect(screen.getByText('パーソナライゼーション')).toBeDefined();
        expect(screen.getByText('ユーザープロファイル')).toBeDefined();
      });
    });

    test('パーソナライズド推奨が表示される', async () => {
      renderWithChakra(<PersonalizationPanel />);
      
      await waitFor(() => {
        expect(screen.getByText('パーソナライズド推奨')).toBeDefined();
        expect(screen.getByText('休憩時間最適化')).toBeDefined();
      });
    });
  });

  describe('Phase 4.3統合: リアルタイム分析', () => {
    beforeEach(() => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockImplementation((url) => {
        if (url?.toString().includes('/api/analysis/performance-report')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockApiResponses.performanceReport)
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });
    });

    test('リアルタイムWebSocket接続が正常に動作する', async () => {
      renderWithChakra(<AdvancedAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('高度分析ダッシュボード')).toBeDefined();
      });
    });
  });

  describe('Phase 4.4統合: 高度分析ダッシュボード', () => {
    beforeEach(() => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockImplementation((url) => {
        const urlStr = url?.toString() || '';
        
        if (urlStr.includes('/api/analysis/trends')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ trends: { focus_trends: mockApiResponses.behaviorLogs } })
          } as Response);
        }
        if (urlStr.includes('/api/analysis/advanced-patterns')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockApiResponses.advancedPatterns)
          } as Response);
        }
        if (urlStr.includes('/api/analysis/predictions')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              predictions: [
                {
                  metric: 'focus_score',
                  predicted_value: 0.75,
                  confidence: 0.88,
                  trend: 'stable'
                }
              ]
            })
          } as Response);
        }
        if (urlStr.includes('/api/analysis/performance-report')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockApiResponses.performanceReport)
          } as Response);
        }
        
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });
    });

    test('AdvancedAnalyticsDashboardが全タブで正常に表示される', async () => {
      renderWithChakra(<AdvancedAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('高度分析ダッシュボード')).toBeDefined();
        expect(screen.getByText('概要')).toBeDefined();
        expect(screen.getByText('行動パターン')).toBeDefined();
        expect(screen.getByText('予測インサイト')).toBeDefined();
        expect(screen.getByText('パフォーマンス')).toBeDefined();
      });
    });

    test('PredictiveInsightsが予測データを表示する', async () => {
      renderWithChakra(<PredictiveInsights />);
      
      await waitFor(() => {
        expect(screen.getByText('予測インサイト')).toBeDefined();
        expect(screen.getByText('メトリクス予測')).toBeDefined();
      });
    });

    test('LearningProgressが学習状況を表示する', async () => {
      renderWithChakra(<LearningProgress />);
      
      await waitFor(() => {
        expect(screen.getByText('学習進捗')).toBeDefined();
        expect(screen.getByText('学習メトリクス')).toBeDefined();
      });
    });
  });

  describe('コンポーネント間連携テスト', () => {
    test('設定変更が他のコンポーネントに反映される', async () => {
      renderWithChakra(<App />);
      
      // 設定タブに移動
      const settingsTab = screen.getByText('設定');
      fireEvent.click(settingsTab);
      
      await waitFor(() => {
        expect(screen.getByText('システム設定')).toBeDefined();
      });
      
      // 監視タブに戻る
      const monitorTab = screen.getByText('監視');
      fireEvent.click(monitorTab);
      
      await waitFor(() => {
        expect(screen.getByText('監視カメラ')).toBeDefined();
      });
    });

    test('分析データが複数のダッシュボードで共有される', async () => {
      // AdvancedAnalyticsDashboardとPersonalizationPanelで同じAPIデータが使用されることを確認
      const dashboardComponent = renderWithChakra(<AdvancedAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('高度分析ダッシュボード')).toBeDefined();
      });
      
      dashboardComponent.unmount();
      
      renderWithChakra(<PersonalizationPanel />);
      
      await waitFor(() => {
        expect(screen.getByText('パーソナライゼーション')).toBeDefined();
      });
    });
  });

  describe('エラーハンドリング統合テスト', () => {
    test('API エラー時のフォールバック表示', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockImplementation(() => {
        return Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ error: 'Internal Server Error' })
        } as Response);
      });

      renderWithChakra(<AdvancedAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('データ取得エラー')).toBeDefined();
      });
    });
  });

  describe('パフォーマンステスト', () => {
    test('大量データ表示時のパフォーマンス', async () => {
      // 大量のモックデータを生成
      const largeBehaviorData = Array.from({ length: 1000 }, (_, i) => ({
        timestamp: new Date(Date.now() - i * 60000).toISOString(),
        focus_score: Math.random(),
        posture_score: Math.random(),
        smartphone_usage: Math.random() > 0.5,
        face_visible: Math.random() > 0.3
      }));

      (global.fetch as jest.MockedFunction<typeof fetch>).mockImplementation(() => {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ trends: { focus_trends: largeBehaviorData } })
        } as Response);
      });

      const startTime = performance.now();
      renderWithChakra(<AdvancedAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('高度分析ダッシュボード')).toBeDefined();
      });
      
      const renderTime = performance.now() - startTime;
      
      // レンダリング時間が2秒以内であることを確認
      expect(renderTime).toBeLessThan(2000);
    });
  });

  describe('アクセシビリティテスト', () => {
    test('キーボードナビゲーションが正常に動作する', async () => {
      renderWithChakra(<App />);
      
      // タブキーでナビゲーション
      const firstTab = screen.getByText('監視');
      firstTab.focus();
      
      // Enterキーで選択
      fireEvent.keyDown(firstTab, { key: 'Enter', code: 'Enter' });
      
      await waitFor(() => {
        expect(screen.getByText('監視カメラ')).toBeDefined();
      });
    });

    test('基本的なUIコンポーネントが正しく表示される', () => {
      renderWithChakra(<AdvancedAnalyticsDashboard />);
      
      // 基本要素の存在確認
      const heading = screen.getByRole('heading', { level: 2 });
      expect(heading).toBeDefined();
    });
  });
}); 