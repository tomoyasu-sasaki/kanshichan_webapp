import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChakraProvider, useToast } from '@chakra-ui/react';
import { SettingsPanel } from '../SettingsPanel';
import axios from 'axios';

// axiosをモック化
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Chakra UIのuseToastをモック化
jest.mock('@chakra-ui/react', () => {
  const originalModule = jest.requireActual('@chakra-ui/react');
  return {
    ...originalModule,
    useToast: jest.fn(() => jest.fn()),
  };
});

describe('SettingsPanel Component', () => {
  const mockToast = jest.fn();
  
  const mockSettingsData = {
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

  beforeEach(() => {
    jest.clearAllMocks();
    (useToast as jest.Mock).mockImplementation(() => mockToast);
    
    // デフォルトの成功レスポンス
    mockedAxios.get.mockResolvedValue({ data: mockSettingsData });
    mockedAxios.post.mockResolvedValue({ data: { success: true } });
  });

  test('コンポーネントが正しくレンダリングされる', async () => {
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // ヘッダーが表示されることを確認
    expect(screen.getByText('監視設定')).toBeInTheDocument();
    
    // 基本的な設定項目が表示されることを確認
    expect(screen.getByText('不在検知閾値（秒）')).toBeInTheDocument();
    expect(screen.getByText('スマートフォン使用検知閾値（秒）')).toBeInTheDocument();
    
    // 保存ボタンが表示されることを確認
    expect(screen.getByRole('button', { name: /保存/i })).toBeInTheDocument();
  });

  test('初期設定データが正しく読み込まれる', async () => {
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // APIが呼ばれることを確認
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/settings');

    // データがロードされるのを待つ
    await waitFor(() => {
      // 閾値が正しく表示されることを確認
      const absenceInput = screen.getByLabelText('不在検知閾値（秒）');
      const smartphoneInput = screen.getByLabelText('スマートフォン使用検知閾値（秒）');
      
      expect(absenceInput).toHaveValue(5);
      expect(smartphoneInput).toHaveValue(3);
    });
  });

  test('設定データの取得エラーハンドリング', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Network Error'));

    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // エラートーストが表示されることを確認
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
        title: 'エラー',
        description: '設定の取得に失敗しました',
        status: 'error',
      }));
    });
  });

  test('閾値の変更が動作する', async () => {
    const user = userEvent.setup();
    
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByDisplayValue('5')).toBeInTheDocument();
    });

    // 不在検知閾値を変更
    const absenceInput = screen.getByLabelText('不在検知閾値（秒）');
    await user.clear(absenceInput);
    await user.type(absenceInput, '10');

    // スマートフォン使用検知閾値を変更
    const smartphoneInput = screen.getByLabelText('スマートフォン使用検知閾値（秒）');
    await user.clear(smartphoneInput);
    await user.type(smartphoneInput, '5');

    // 値が更新されることを確認
    expect(absenceInput).toHaveValue(10);
    expect(smartphoneInput).toHaveValue(5);
  });

  test('ランドマーク設定の切り替えが動作する', async () => {
    const user = userEvent.setup();
    
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByText('鼻')).toBeInTheDocument();
    });

    // 左目のスイッチを見つけて切り替え
    const leftEyeSwitch = screen.getByRole('checkbox', { name: /左目/i });
    await user.click(leftEyeSwitch);

    // スイッチの状態が変わることを確認
    expect(leftEyeSwitch).toBeChecked();
  });

  test('検出オブジェクト設定の変更が動作する', async () => {
    const user = userEvent.setup();
    
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByText('人物')).toBeInTheDocument();
    });

    // 人物検出のスイッチを切り替え
    const personSwitch = screen.getByRole('checkbox', { name: /人物/i });
    await user.click(personSwitch);

    // スイッチの状態が変わることを確認
    expect(personSwitch).not.toBeChecked();
  });

  test('設定の保存が正常に動作する', async () => {
    const user = userEvent.setup();
    
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByDisplayValue('5')).toBeInTheDocument();
    });

    // 設定を変更
    const absenceInput = screen.getByLabelText('不在検知閾値（秒）');
    await user.clear(absenceInput);
    await user.type(absenceInput, '8');

    // 保存ボタンをクリック
    const saveButton = screen.getByRole('button', { name: /保存/i });
    await user.click(saveButton);

    // POSTリクエストが正しく送信されることを確認
    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/settings', expect.objectContaining({
        absence_threshold: 8,
        smartphone_threshold: 3,
      }));
    });

    // 成功トーストが表示されることを確認
    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
      title: '成功',
      description: '設定を保存しました',
      status: 'success',
    }));
  });

  test('設定保存時のエラーハンドリング', async () => {
    const user = userEvent.setup();
    mockedAxios.post.mockRejectedValue(new Error('Save Error'));
    
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByDisplayValue('5')).toBeInTheDocument();
    });

    // 保存ボタンをクリック
    const saveButton = screen.getByRole('button', { name: /保存/i });
    await user.click(saveButton);

    // エラートーストが表示されることを確認
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
        title: 'エラー',
        description: '設定の保存に失敗しました',
        status: 'error',
      }));
    });
  });

  test('メッセージ延長設定が表示される', async () => {
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByText('LINEメッセージ設定')).toBeInTheDocument();
    });

    // メッセージ延長設定の項目が表示されることを確認
    expect(screen.getByText('休憩中')).toBeInTheDocument();
    expect(screen.getByText('外出中')).toBeInTheDocument();
  });

  test('メッセージ延長時間の変更が動作する', async () => {
    const user = userEvent.setup();
    
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByDisplayValue('600')).toBeInTheDocument();
    });

    // 休憩中の延長時間を変更
    const breakExtensionInput = screen.getByDisplayValue('600');
    await user.clear(breakExtensionInput);
    await user.type(breakExtensionInput, '900');

    // 値が更新されることを確認
    expect(breakExtensionInput).toHaveValue(900);
  });

  test('検出オブジェクトの信頼度閾値変更が動作する', async () => {
    const user = userEvent.setup();
    
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByText('人物')).toBeInTheDocument();
    });

    // 人物検出の信頼度閾値を変更
    const confidenceInputs = screen.getAllByDisplayValue('0.5');
    if (confidenceInputs.length > 0) {
      await user.clear(confidenceInputs[0]);
      await user.type(confidenceInputs[0], '0.8');
      expect(confidenceInputs[0]).toHaveValue(0.8);
    }
  });

  test('すべての設定項目が適切にラベル付けされている', async () => {
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // アクセシビリティラベルが適切に設定されていることを確認
    expect(screen.getByLabelText('不在検知閾値（秒）')).toBeInTheDocument();
    expect(screen.getByLabelText('スマートフォン使用検知閾値（秒）')).toBeInTheDocument();
    
    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByText('鼻')).toBeInTheDocument();
    });

    // 各ランドマーク設定にアクセシビリティが設定されていることを確認
    expect(screen.getByRole('checkbox', { name: /鼻/i })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /左目/i })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /右目/i })).toBeInTheDocument();
  });

  test('設定項目が適切にグループ化されている', async () => {
    render(
      <ChakraProvider>
        <SettingsPanel />
      </ChakraProvider>
    );

    // セクション見出しが表示されることを確認
    expect(screen.getByText('監視設定')).toBeInTheDocument();
    
    // データがロードされるのを待つ
    await waitFor(() => {
      expect(screen.getByText('LINEメッセージ設定')).toBeInTheDocument();
    });

    // 各セクションの見出しが正しく表示されることを確認
    expect(screen.getByText('LINEメッセージ設定')).toBeInTheDocument();
  });
}); 