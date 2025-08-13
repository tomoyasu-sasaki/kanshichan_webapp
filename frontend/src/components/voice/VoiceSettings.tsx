import { 
  Box, 
  VStack, 
  HStack, 
  useToast, 
  Container, 
  Grid, 
  GridItem,
  useBreakpointValue 
} from '@chakra-ui/react';
import { useEffect, useState, useCallback, useRef } from 'react';

// Types and constants
import type { VoiceSettings as VoiceSettingsType, VoiceSettingsProps, AudioFile } from './types';
import { defaultVoiceSettings } from './constants';

// Hooks
import { useTTSStatus } from './hooks/useTTSStatus';
import { useAudioFiles } from './hooks/useAudioFiles';
import { useVoicePreview } from './hooks/useVoicePreview';

// Components
import { VoiceSettingsHeader } from './components/VoiceSettingsHeader';
import { BasicSettings } from './components/BasicSettings';
import { VoiceSampleManager } from './components/VoiceSampleManager';
import { VoicePreview } from './components/VoicePreview';
import { VoiceSettingsSummary } from './components/VoiceSettingsSummary';

export const VoiceSettings: React.FC<VoiceSettingsProps> = ({
  onSettingsChange
}) => {
  // 音声設定状態
  const [settings, setSettings] = useState<VoiceSettingsType>(defaultVoiceSettings);
  
  const toast = useToast();
  
  // Custom hooks
  const { ttsStatus, loadingTTSStatus } = useTTSStatus();
  const { availableFiles, fetchAudioFiles } = useAudioFiles();
  const { previewing, handlePreview } = useVoicePreview();

  // 初期化（React StrictMode のダブルマウント対策）
  const didInitRef = useRef(false);
  useEffect(() => {
    if (didInitRef.current) return;
    didInitRef.current = true;

    fetchAudioFiles();
    loadDefaultVoiceSettings(); // デフォルト設定を読み込む
  }, [fetchAudioFiles]);

  // 設定変更の通知
  useEffect(() => {
    onSettingsChange?.(settings);
  }, [settings, onSettingsChange]);

  // デフォルト音声設定を読み込む
  const loadDefaultVoiceSettings = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/tts/voice-settings');
      if (response.ok) {
        const data = await response.json();
        const payload = (data && typeof data === 'object' && 'data' in data) ? (data as { data: AudioFile[] }).data : data;
        if (data.success && payload?.voice_settings) {
          // デフォルト設定を反映
          setSettings(prevSettings => ({
            ...prevSettings,
            ...payload.voice_settings
          }));
          console.log('Default voice settings loaded', payload.voice_settings);
        }
      }
    } catch (error) {
      console.error('Failed to load default voice settings:', error);
    }
  }, []);

  // デフォルト音声に設定
  const saveAsDefaultVoice = useCallback(async () => {
    try {
      // voiceSampleIdがある場合にパスも追加
      const settingsToSave = { ...settings };
      
      // バックエンドがパスを自動的に解決するため、
      // voiceSamplePathは送信しない（ID情報のみを送る）
      if (settings.voiceMode === 'voiceClone' && !settings.voiceSampleId) {
        // 音声サンプルがないけどボイスクローンモードの場合はデフォルトサンプルを使用
        settingsToSave.voiceSampleId = 'default_sample';
      }
      
      const response = await fetch('/api/v1/tts/voice-settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...settingsToSave,
          setAsDefault: true
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          toast({
            title: '設定完了',
            description: 'デフォルト音声設定として保存しました',
            status: 'success',
            duration: 3000,
            isClosable: true,
          });
        } else {
          throw new Error(data.message || 'デフォルト設定の保存に失敗しました');
        }
      } else {
        throw new Error('デフォルト設定の保存に失敗しました');
      }
    } catch (error) {
      console.error('Failed to save default voice settings:', error);
      toast({
        title: '保存エラー',
        description: error instanceof Error ? error.message : '設定の保存に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  }, [settings, toast]);

  // レスポンシブレイアウト設定
  const isMobile = useBreakpointValue({ base: true, lg: false });
  const gridTemplateColumns = useBreakpointValue({ 
    base: '1fr', 
    lg: '2fr 1fr' 
  });

  return (
    <Container maxW="1400px" px={{ base: 4, md: 6 }}>
      <VStack spacing={8} align="stretch">
        {/* ヘッダー */}
        <VoiceSettingsHeader
          loadingTTSStatus={loadingTTSStatus}
          ttsStatus={ttsStatus}
        />

        {/* メインコンテンツ - レスポンシブグリッド */}
        <Grid 
          templateColumns={gridTemplateColumns}
          gap={8}
          alignItems="start"
        >
          {/* 左カラム - メイン設定 */}
          <GridItem>
            <VStack spacing={6} align="stretch">
              {/* 基本設定 */}
              <BasicSettings
                settings={settings}
                ttsStatus={ttsStatus}
                onSettingsChange={setSettings}
                onSaveAsDefault={saveAsDefaultVoice}
              />

              {/* 音声サンプル設定 */}
              {settings.voiceMode === 'voiceClone' && (
                <VoiceSampleManager
                  settings={settings}
                  availableFiles={availableFiles}
                  onSettingsChange={setSettings}
                  onFilesUpdate={fetchAudioFiles}
                />
              )}
            </VStack>
          </GridItem>

          {/* 右カラム - プレビューと設定情報 */}
          <GridItem>
            <VStack spacing={6} align="stretch" position="sticky" top="20px">
              {/* 音声プレビュー */}
              <VoicePreview
                settings={settings}
                ttsStatus={ttsStatus}
                loadingTTSStatus={loadingTTSStatus}
                onPreview={handlePreview}
                previewing={previewing}
              />

              {/* 設定情報表示 */}
              <VoiceSettingsSummary settings={settings} />
            </VStack>
          </GridItem>
        </Grid>
      </VStack>
    </Container>
  );
}; 