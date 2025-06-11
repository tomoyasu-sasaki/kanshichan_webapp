import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  Select,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  FormControl,
  FormLabel,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Badge,
  useToast,
  Textarea,
  Progress,
  Alert,
  AlertIcon,
  IconButton,
  Tooltip,
  Switch,
  AlertTitle,
  AlertDescription
} from '@chakra-ui/react';
import { useEffect, useState, useCallback, useRef } from 'react';
import { FaPlay, FaStop, FaUpload, FaVolumeUp } from 'react-icons/fa';

interface VoiceSettingsProps {
  onSettingsChange?: (settings: VoiceSettings) => void;
}

interface VoiceSettings {
  voiceMode: 'tts' | 'voiceClone';
  defaultEmotion: string;
  defaultLanguage: string;
  voiceSpeed: number;
  voicePitch: number;
  voiceSampleId: string | null;
  voiceVolume: number;
  fastMode: boolean;
}

interface AudioFile {
  file_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  metadata: {
    voice_sample_for?: string;
    language?: string;
    upload_timestamp?: string;
  };
}

interface TTSStatus {
  initialized: boolean;
  model_name: string;
  device: string;
  voice_cloning_enabled: boolean;
  default_language: string;
  supported_languages: string[];
  available_emotions: string[];
}

export const VoiceSettings: React.FC<VoiceSettingsProps> = ({
  onSettingsChange
}) => {
  // 感情名の英語から日本語へのマッピング
  const emotionTranslations: Record<string, string> = {
    'anger': '怒り',
    'angry': '怒った',
    'annoyed': 'イライラした',
    'assertive': '断定的',
    'calm': '穏やか',
    'cheerful': '陽気',
    'confident': '自信のある',
    'disgust': '嫌悪',
    'excited': '興奮した',
    'fear': '恐怖',
    'fearful': '恐れた',
    'happiness': '幸福',
    'happy': '嬉しい',
    'joy': '喜び',
    'melancholy': '憂鬱',
    'neutral': '普通',
    'peaceful': '平和な',
    'sad': '悲しい',
    'sadness': '悲しみ',
    'surprise': '驚き',
    'surprised': '驚いた',
    'worried': '心配した'
  };

  // 音声設定状態
  const [settings, setSettings] = useState<VoiceSettings>({
    voiceMode: 'tts',
    defaultEmotion: 'neutral',
    defaultLanguage: 'ja',
    voiceSpeed: 1.0,
    voicePitch: 1.0,
    voiceSampleId: null,
    voiceVolume: 0.7,
    fastMode: false
  });

  // UI状態
  const [uploading, setUploading] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [loadingTTSStatus, setLoadingTTSStatus] = useState(true);
  const [testText, setTestText] = useState('これは音声設定のテストです。設定した感情とトーンで再生されます。');
  const [sampleName, setSampleName] = useState(''); // 新しい音声サンプル名
  const [selectedFile, setSelectedFile] = useState<File | null>(null); // 選択されたファイル
  const [deleting, setDeleting] = useState<string | null>(null); // 削除中のファイルID
  
  // TTS情報
  const [ttsStatus, setTtsStatus] = useState<TTSStatus | null>(null);
  const [availableFiles, setAvailableFiles] = useState<AudioFile[]>([]);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  // TTSサービス状態を取得
  const fetchTTSStatus = useCallback(async () => {
    try {
      setLoadingTTSStatus(true);
      const response = await fetch('/api/tts/status');
      if (response.ok) {
        const data = await response.json();
        console.log('TTS Status Response:', data); // デバッグ用
        
        if (data.success) {
          // 複数のレスポンス構造をサポート（下位互換性を保持）
          let ttsStatusData = null;
          
          // 優先順位：tts_details > status.tts_service > フォールバック
          if (data.tts_details) {
            ttsStatusData = data.tts_details;
          } else if (data.status?.tts_service) {
            ttsStatusData = data.status.tts_service;
          } else if (data.services?.tts_service === 'available') {
            // サービスが利用可能でも詳細がない場合のフォールバック
            ttsStatusData = {
              initialized: true,
              model_name: 'Unknown',
              device: 'Unknown',
              voice_cloning_enabled: false,
              default_language: 'ja',
              supported_languages: ['ja'],
              available_emotions: ['neutral']
            };
          }
          
          if (ttsStatusData) {
            setTtsStatus(ttsStatusData);
          } else {
            console.warn('No TTS status data available:', data);
          }
        } else {
          console.error('TTS status API returned success: false');
        }
      } else {
        console.error('Failed to fetch TTS status:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch TTS status:', error);
    } finally {
      setLoadingTTSStatus(false);
    }
  }, []);

  // 音声ファイル一覧を取得
  const fetchAudioFiles = useCallback(async () => {
    try {
      const response = await fetch('/api/tts/voices?type=sample');
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAvailableFiles(data.files || []);
        }
      }
    } catch (error) {
      console.error('Failed to fetch audio files:', error);
    }
  }, []);

  // 初期化
  useEffect(() => {
    fetchTTSStatus();
    fetchAudioFiles();
    loadDefaultVoiceSettings(); // デフォルト設定を読み込む
  }, [fetchTTSStatus, fetchAudioFiles]);

  // 設定変更の通知
  useEffect(() => {
    onSettingsChange?.(settings);
  }, [settings, onSettingsChange]);

  // 音声ファイルアップロード
  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // ファイル検証
    if (!file.type.startsWith('audio/')) {
      toast({
        title: 'アップロードエラー',
        description: '音声ファイルを選択してください',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB制限
      toast({
        title: 'ファイルサイズエラー',
        description: 'ファイルサイズは10MB以下にしてください',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    // ファイルを選択状態にセット
    setSelectedFile(file);
  }, [toast]);
  
  // 音声サンプル登録
  const handleRegisterSample = useCallback(async () => {
    if (!selectedFile) {
      toast({
        title: '登録エラー',
        description: 'ファイルを選択してください',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('audio_file', selectedFile);
      formData.append('text', 'これは音声サンプルです。');
      formData.append('emotion', settings.defaultEmotion);
      formData.append('language', settings.defaultLanguage);
      formData.append('return_url', 'true');
      
      // カスタム名前が設定されている場合は追加
      if (sampleName.trim()) {
        formData.append('custom_filename', sampleName.trim());
      }

      const response = await fetch('/api/tts/upload_voice_sample', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          toast({
            title: '登録完了',
            description: `音声サンプル「${sampleName || selectedFile.name}」を登録しました`,
            status: 'success',
            duration: 3000,
            isClosable: true,
          });
          
          // 状態をリセット
          setSelectedFile(null);
          setSampleName('');
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
          
          // リストを更新
        await fetchAudioFiles();
        } else {
          throw new Error(data.error || 'アップロードに失敗しました');
        }
      } else {
        throw new Error('アップロードに失敗しました');
      }
    } catch (error) {
      toast({
        title: 'アップロードエラー',
        description: `ファイルアップロードに失敗しました: ${error}`,
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setUploading(false);
    }
  }, [selectedFile, sampleName, settings, toast, fetchAudioFiles]);
  
  // 音声サンプル削除
  const handleDeleteSample = useCallback(async (fileId: string, filename: string) => {
    if (!confirm(`音声サンプル「${filename}」を削除しますか？`)) {
      return;
    }
    
    setDeleting(fileId);

    try {
      const response = await fetch(`/api/tts/voices/${fileId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        toast({
          title: '削除完了',
          description: `音声サンプル「${filename}」を削除しました`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        
        // 削除したサンプルが現在選択されている場合はリセット
        if (settings.voiceSampleId === fileId) {
          setSettings(prev => ({ ...prev, voiceSampleId: null }));
        }
        
        // リストを更新
        await fetchAudioFiles();
      } else {
        throw new Error('削除に失敗しました');
      }
    } catch (error) {
      toast({
        title: '削除エラー',
        description: `削除に失敗しました: ${error}`,
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setDeleting(null);
    }
  }, [settings.voiceSampleId, toast, fetchAudioFiles]);

  // 音声プレビュー
  const handlePreview = useCallback(async () => {
    if (previewing) {
      // 停止
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        setCurrentAudio(null);
      }
      setPreviewing(false);
      return;
    }

    setPreviewing(true);
    
    // 処理時間測定開始
    const startTime = performance.now();

    try {
      // API呼び出し（高速モード対応）
      const apiEndpoint = settings.fastMode ? '/api/tts/synthesize-fast' : '/api/tts/synthesize';
      
      const baseRequestBody = {
        text: testText,
        language: settings.defaultLanguage,
        return_url: false,
      };

      const requestBody = settings.voiceMode === 'voiceClone'
        ? {
            ...baseRequestBody,
        speaker_sample_id: settings.voiceSampleId || 'default_sample',
            voice_clone_mode: true // バックエンドへの明示的な指示
          }
        : {
            ...baseRequestBody,
            tts_mode: true // TTS標準モードの明示的な指示
          };

      console.log('🎵 音声プレビュー開始:', {
        voiceMode: settings.voiceMode,
        fastMode: settings.fastMode,
        apiEndpoint,
        startTime: new Date().toISOString(),
        requestBody,
        expectedProcessing: settings.fastMode 
          ? '高速処理（30秒以内）' 
          : settings.voiceMode === 'voiceClone' ? '重い処理（ボイスクローン）' : '軽い処理（TTS標準）'
      });

      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const endTime = performance.now();
      const processingTime = (endTime - startTime) / 1000; // 秒

      console.log('🎵 音声プレビュー完了:', {
        voiceMode: settings.voiceMode,
        fastMode: settings.fastMode,
        processingTime: `${processingTime.toFixed(2)}秒`,
        responseOk: response.ok,
        expectedSpeed: settings.fastMode ? '高速' : settings.voiceMode === 'voiceClone' ? '遅い' : '高速',
        actualSpeed: processingTime > 5 ? '遅い' : processingTime > 2 ? '普通' : '高速'
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        audio.volume = settings.voiceVolume;
        audio.onended = () => {
          setPreviewing(false);
          setCurrentAudio(null);
          URL.revokeObjectURL(audioUrl);
        };
        audio.onerror = () => {
          setPreviewing(false);
          setCurrentAudio(null);
          URL.revokeObjectURL(audioUrl);
          toast({
            title: '再生エラー',
            description: '音声の再生に失敗しました',
            status: 'error',
            duration: 3000,
            isClosable: true,
          });
        };

        setCurrentAudio(audio);
        await audio.play();
        
        // 成功時のトースト通知（処理時間付き）
        toast({
          title: '音声プレビュー完了',
          description: `${settings.fastMode ? '高速' : settings.voiceMode === 'voiceClone' ? 'ボイスクローン' : 'TTS標準'}モード (${processingTime.toFixed(1)}秒)`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      } else {
        // TTSサービスが利用できない場合のフォールバック処理を強化
        const errorData = await response.json().catch(() => ({ error: 'unknown', message: '不明なエラー' }));
        console.error('TTSサービスエラー:', errorData);
        
        if (response.status === 503 || errorData.message?.includes('TTS service is not available')) {
          // TTSサービスが利用できない場合のメッセージを改善
          toast({
            title: 'TTSサービス未準備',
            description: 'TTSサービスが準備中または利用できません。ブラウザの音声合成を使用します。',
            status: 'warning',
            duration: 4000,
            isClosable: true,
          });
          
          // すべてのモードでブラウザTTSを試行
          await handleBrowserTTSFallback();
        } else {
          throw new Error(`音声合成に失敗しました: ${errorData.message || '不明なエラー'}`);
        }
      }
    } catch (error) {
      const endTime = performance.now();
      const processingTime = (endTime - startTime) / 1000;
      
      console.error('❌ 音声プレビューエラー:', {
        voiceMode: settings.voiceMode,
        fastMode: settings.fastMode,
        processingTime: `${processingTime.toFixed(2)}秒`,
        error: error
      });
      
      // エラー処理の改善 - すべてのエラーでブラウザTTSを試行
      try {
        toast({
          title: 'フォールバック処理',
          description: 'サーバーでエラーが発生したため、ブラウザの音声合成を使用します',
          status: 'warning',
          duration: 3000,
          isClosable: true,
        });
        
        await handleBrowserTTSFallback();
        return; // 成功した場合は早期リターン
      } catch (fallbackError) {
        console.warn('Browser TTS fallback also failed:', fallbackError);
        
        // 両方失敗した場合のエラー表示
        setPreviewing(false);
        toast({
          title: '音声合成エラー',
          description: `すべての音声合成方法が失敗しました。設定を確認してください。`,
          status: 'error',
          duration: 4000,
          isClosable: true,
        });
      }
    }
  }, [previewing, currentAudio, testText, settings, toast]);

  // ブラウザTTSフォールバック処理
  const handleBrowserTTSFallback = useCallback(async () => {
    return new Promise<void>((resolve, reject) => {
      if (!('speechSynthesis' in window)) {
        reject(new Error('ブラウザがTTSをサポートしていません'));
        return;
      }

      try {
        const utterance = new SpeechSynthesisUtterance(testText);
        utterance.lang = settings.defaultLanguage === 'ja' ? 'ja-JP' : 'en-US';
        utterance.rate = settings.voiceSpeed;
        utterance.pitch = settings.voicePitch;
        utterance.volume = settings.voiceVolume;

        utterance.onend = () => {
          setPreviewing(false);
          resolve();
        };

        utterance.onerror = (event) => {
          setPreviewing(false);
          reject(new Error(`ブラウザTTSエラー: ${event.error}`));
        };

        window.speechSynthesis.speak(utterance);
        
        toast({
          title: 'フォールバック動作',
          description: 'ブラウザ標準のTTSを使用しています',
          status: 'info',
          duration: 2000,
          isClosable: true,
        });
      } catch (error) {
        reject(error);
      }
    });
  }, [testText, settings, toast]);

  // 感情選択ハンドラ
  const handleEmotionChange = useCallback((emotion: string) => {
    setSettings(prev => ({ ...prev, defaultEmotion: emotion }));
  }, []);

  // 言語選択ハンドラ
  const handleLanguageChange = useCallback((language: string) => {
    setSettings(prev => ({ ...prev, defaultLanguage: language }));
  }, []);

  // 音声サンプル選択ハンドラ
  const handleVoiceSampleChange = useCallback((sampleId: string) => {
    setSettings(prev => ({ 
      ...prev, 
      voiceSampleId: sampleId === 'none' ? null : sampleId 
    }));
  }, []);

  // デフォルト音声設定を読み込む
  const loadDefaultVoiceSettings = useCallback(async () => {
    try {
      const response = await fetch('/api/tts/voice-settings');
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.voice_settings) {
          // デフォルト設定を反映
          setSettings(prevSettings => ({
            ...prevSettings,
            ...data.voice_settings
          }));
          console.log('Default voice settings loaded', data.voice_settings);
        }
      }
    } catch (error) {
      console.error('Failed to load default voice settings:', error);
    }
  }, []);

  // デフォルト音声に設定
  const saveAsDefaultVoice = useCallback(async () => {
    try {
      const response = await fetch('/api/tts/voice-settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...settings,
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

  return (
    <Box width="100%" maxWidth="800px" mx="auto">
      <VStack spacing={6} align="stretch">
        {/* ヘッダー */}
        <Card>
          <CardHeader>
            <HStack justify="space-between" align="center">
              <Heading size="md">音声設定</Heading>
              {loadingTTSStatus ? (
                <Badge colorScheme="yellow">初期化中</Badge>
              ) : ttsStatus ? (
                <Badge colorScheme={ttsStatus.initialized ? 'green' : 'red'}>
                  {ttsStatus.initialized ? '利用可能' : '初期化失敗'}
                </Badge>
              ) : (
                <Badge colorScheme="red">接続エラー</Badge>
              )}
            </HStack>
          </CardHeader>
        </Card>

        {/* TTS無効時の警告 */}
        {ttsStatus && !ttsStatus.voice_cloning_enabled && (
          <Alert status="warning">
            <AlertIcon />
            音声クローン機能が無効になっています
          </Alert>
        )}

        {/* 基本設定 */}
        <Card>
          <CardHeader>
            <Heading size="sm">基本設定</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {/* 音声モード選択 */}
              <FormControl>
                <FormLabel>音声モード</FormLabel>
                <Select
                  value={settings.voiceMode}
                  onChange={(e) => setSettings(prev => ({ ...prev, voiceMode: e.target.value as 'tts' | 'voiceClone' }))}
                >
                  <option value="tts">TTS音声合成</option>
                  <option value="voiceClone">ボイスクローン</option>
                </Select>
                <Text fontSize="xs" color="gray.500" mt={1}>
                  {settings.voiceMode === 'tts' 
                    ? '標準のTTS音声合成を使用します' 
                    : 'アップロードした音声サンプルでボイスクローンを使用します'}
                </Text>
              </FormControl>

              {/* 高速モード設定 */}
              <FormControl>
                <HStack justify="space-between" align="center">
                  <VStack align="start" spacing={0}>
                    <FormLabel mb={0}>高速モード</FormLabel>
                    <Text fontSize="xs" color="gray.500">
                      {settings.fastMode 
                        ? '約30秒で音声生成（シンプル処理）' 
                        : '高品質音声生成（詳細処理）'}
                    </Text>
                  </VStack>
                  <Switch
                    isChecked={settings.fastMode}
                    onChange={(e) => setSettings(prev => ({ ...prev, fastMode: e.target.checked }))}
                    colorScheme="blue"
                    size="lg"
                  />
                </HStack>
                {settings.fastMode && (
                  <Alert status="info" mt={2}>
                    <AlertIcon />
                    <Box>
                      <AlertTitle>高速モード有効</AlertTitle>
                      <AlertDescription fontSize="sm">
                        品質評価とキャッシュ機能を省略して高速化します
                      </AlertDescription>
                    </Box>
                  </Alert>
                )}
              </FormControl>

              {/* 感情設定 */}
              <FormControl>
                <FormLabel>デフォルト感情</FormLabel>
                <Select
                  value={settings.defaultEmotion}
                  onChange={(e) => handleEmotionChange(e.target.value)}
                >
                  {ttsStatus?.available_emotions?.map((emotion) => (
                    <option key={emotion} value={emotion}>
                      {emotionTranslations[emotion] || emotion}
                    </option>
                  )) || (
                    <option value="neutral">neutral</option>
                  )}
                </Select>
              </FormControl>

              {/* 言語設定 */}
              <FormControl>
                <FormLabel>デフォルト言語</FormLabel>
                <Select
                  value={settings.defaultLanguage}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                >
                  {ttsStatus?.supported_languages?.map((language) => (
                    <option key={language} value={language}>
                      {language}
                    </option>
                  )) || (
                    <option value="ja">ja</option>
                  )}
                </Select>
              </FormControl>

              {/* 話速調整 */}
              <FormControl>
                <FormLabel>話速: {settings.voiceSpeed.toFixed(1)}x</FormLabel>
                <Slider
                  value={settings.voiceSpeed}
                  onChange={(value) => setSettings(prev => ({ ...prev, voiceSpeed: value }))}
                  min={0.5}
                  max={2.0}
                  step={0.1}
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* 音程調整 */}
              <FormControl>
                <FormLabel>音程: {settings.voicePitch.toFixed(1)}x</FormLabel>
                <Slider
                  value={settings.voicePitch}
                  onChange={(value) => setSettings(prev => ({ ...prev, voicePitch: value }))}
                  min={0.5}
                  max={2.0}
                  step={0.1}
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* 音量調整 */}
              <FormControl>
                <FormLabel>音量: {Math.round(settings.voiceVolume * 100)}%</FormLabel>
                <Slider
                  value={settings.voiceVolume}
                  onChange={(value) => setSettings(prev => ({ ...prev, voiceVolume: value }))}
                  min={0}
                  max={1}
                  step={0.1}
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* デフォルト設定ボタン */}
              <Button
                colorScheme="teal"
                leftIcon={<FaVolumeUp />}
                onClick={saveAsDefaultVoice}
                mt={4}
              >
                デフォルト音声に設定する
              </Button>
            </VStack>
          </CardBody>
        </Card>

        {/* 音声サンプル設定 */}
        {settings.voiceMode === 'voiceClone' && (
        <Card>
          <CardHeader>
            <Heading size="sm">音声サンプル</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
                {/* 使用する音声サンプル選択 */}
              <FormControl>
                <FormLabel>使用する音声サンプル</FormLabel>
                <Select
                  value={settings.voiceSampleId || 'none'}
                  onChange={(e) => handleVoiceSampleChange(e.target.value)}
                >
                  <option value="none">デフォルト音声（sample.wav）</option>
                  {availableFiles.map((file) => (
                    <option key={file.file_id} value={file.file_id}>
                      {file.filename} ({(file.file_size / 1024 / 1024).toFixed(1)}MB)
                    </option>
                  ))}
                </Select>
              </FormControl>

                {/* 音声サンプル削除 */}
                {availableFiles.length > 0 && (
              <FormControl>
                    <FormLabel>音声サンプル削除</FormLabel>
                    <VStack spacing={2} align="stretch">
                      {availableFiles.map((file) => (
                        <HStack key={file.file_id} justify="space-between" p={2} bg="gray.50" borderRadius="md">
                          <VStack align="start" spacing={0}>
                            <Text fontSize="sm" fontWeight="medium">{file.filename}</Text>
                            <Text fontSize="xs" color="gray.500">
                              {(file.file_size / 1024 / 1024).toFixed(1)}MB
                            </Text>
                          </VStack>
                          <Button
                            size="xs"
                            colorScheme="red"
                            variant="outline"
                            onClick={() => handleDeleteSample(file.file_id, file.filename)}
                            isLoading={deleting === file.file_id}
                            loadingText="削除中..."
                          >
                            削除
                          </Button>
                        </HStack>
                      ))}
                    </VStack>
                  </FormControl>
                )}
                
                {/* 新しい音声サンプルのアップロード */}
                <FormControl>
                  <FormLabel>新しい音声サンプルのアップロード</FormLabel>
                <VStack spacing={3} align="stretch">
                  <FormControl>
                      <FormLabel fontSize="sm">サンプル名（オプション）</FormLabel>
                    <Input
                      placeholder="例: 自分の声サンプル、録音した音声など"
                        value={sampleName}
                        onChange={(e) => setSampleName(e.target.value)}
                      size="sm"
                      maxLength={50}
                    />
                    <Text fontSize="xs" color="gray.500">
                      名前を設定しない場合は、元のファイル名が使用されます
                    </Text>
                  </FormControl>
                  
                    <HStack spacing={3}>
                    <Button
                      leftIcon={<FaUpload />}
                      onClick={() => fileInputRef.current?.click()}
                      size="sm"
                        variant="outline"
                    >
                      ファイル選択
                    </Button>
                      
                      <Button
                        colorScheme="blue"
                        onClick={handleRegisterSample}
                        isLoading={uploading}
                        loadingText="登録中..."
                        size="sm"
                        isDisabled={!selectedFile}
                      >
                        登録
                      </Button>
                    </HStack>
                    
                    {selectedFile && (
                      <Text fontSize="sm" color="green.600">
                        選択されたファイル: {selectedFile.name}
                      </Text>
                    )}
                    
                    <Text fontSize="sm" color="gray.500">
                      WAV, MP3形式 (5-30秒推奨, 10MB以下)
                    </Text>
                  
                  <Input
                    ref={fileInputRef}
                    type="file"
                    accept="audio/*"
                    onChange={handleFileUpload}
                    display="none"
                  />
                </VStack>
              </FormControl>

              {uploading && (
                <Progress size="sm" isIndeterminate colorScheme="blue" />
              )}
            </VStack>
          </CardBody>
        </Card>
        )}

        {/* 音声プレビュー */}
        <Card>
          <CardHeader>
            <Heading size="sm">音声プレビュー</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>テスト用テキスト</FormLabel>
                <Textarea
                  value={testText}
                  onChange={(e) => setTestText(e.target.value)}
                  placeholder="プレビューで読み上げるテキストを入力してください"
                  size="sm"
                />
              </FormControl>

              <HStack>
                <Button
                  leftIcon={previewing ? <FaStop /> : <FaPlay />}
                  onClick={handlePreview}
                  colorScheme={previewing ? 'red' : 'blue'}
                  isLoading={loadingTTSStatus}
                  loadingText="初期化中..."
                  isDisabled={!testText.trim() || (loadingTTSStatus || (!!settings.voiceSampleId && !ttsStatus?.initialized))}
                >
                  {previewing ? '停止' : 'プレビュー再生'}
                </Button>
                
                <Tooltip label="現在の設定で音声を生成・再生します">
                  <IconButton
                    aria-label="ヘルプ"
                    icon={<FaVolumeUp />}
                    size="sm"
                    variant="ghost"
                  />
                </Tooltip>
              </HStack>

              {previewing && (
                <Progress size="sm" isIndeterminate colorScheme="blue" />
              )}
            </VStack>
          </CardBody>
        </Card>

        {/* 設定情報表示 */}
        <Card>
          <CardHeader>
            <Heading size="sm">現在の設定</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={2} align="stretch" fontSize="sm">
              <HStack justify="space-between">
                <Text>音声モード:</Text>
                <Badge colorScheme={settings.voiceMode === 'voiceClone' ? 'purple' : 'blue'}>
                  {settings.voiceMode === 'voiceClone' ? 'ボイスクローン' : 'TTS音声合成'}
                </Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>感情:</Text>
                <Badge>{emotionTranslations[settings.defaultEmotion] || settings.defaultEmotion}</Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>言語:</Text>
                <Badge>{settings.defaultLanguage}</Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>話速:</Text>
                <Badge>{settings.voiceSpeed.toFixed(1)}x</Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>音程:</Text>
                <Badge>{settings.voicePitch.toFixed(1)}x</Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>音量:</Text>
                <Badge>{Math.round(settings.voiceVolume * 100)}%</Badge>
              </HStack>
              {settings.voiceMode === 'voiceClone' && (
              <HStack justify="space-between">
                <Text>音声クローン:</Text>
                <Badge colorScheme={settings.voiceSampleId ? 'green' : 'gray'}>
                  {settings.voiceSampleId ? '有効' : '無効'}
                </Badge>
              </HStack>
              )}
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
}; 