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
  AlertDescription,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Divider,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Spacer
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
  maxFrequency: number;
  audioQuality: number;
  vqScore: number;
  // 感情強度8軸
  emotionHappiness: number;
  emotionSadness: number;
  emotionDisgust: number;
  emotionFear: number;
  emotionSurprise: number;
  emotionAnger: number;
  emotionOther: number;
  emotionNeutral: number;
  useEmotionPreset: boolean; // プリセット使用フラグ
  
  // 生成パラメータ
  cfgScale: number; // 条件付き確率スケール
  minP: number; // 最小確率サンプリング
  seed: number; // 乱数シード
  useSeed: boolean; // シード使用有無

  // オーディオスタイル
  audioPrefix: string | null; // 音声プレフィックス
  useBreathStyle: boolean; // 息継ぎスタイル
  useWhisperStyle: boolean; // ささやきスタイル
  styleIntensity: number; // スタイル強度
  
  // 処理オプション
  useNoiseReduction: boolean; // ノイズ除去
  useStreamingPlayback: boolean; // ストリーミング再生
  speakerNoised: boolean; // 話者ノイズ追加
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

interface TTSRequestBody {
  text: string;
  language: string;
  return_url: boolean;
  emotion: string;
  speed: number;
  pitch: number;
  max_frequency: number;
  audio_quality: number;
  vq_score: number;
  emotion_vector?: number[];
  speaker_sample_id?: string;
  voice_clone_mode?: boolean;
  tts_mode?: boolean;
  
  // 生成パラメータ
  cfg_scale?: number;
  min_p?: number;
  seed?: number;
  
  // オーディオスタイル
  audio_prefix?: string;
  breath_style?: boolean;
  whisper_style?: boolean;
  style_intensity?: number;
  
  // 処理オプション
  noise_reduction?: boolean;
  stream_playback?: boolean;
  speaker_noised?: boolean;
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
    'happiness': '幸福',
    'sadness': '悲しみ',
    'disgust': '嫌悪',
    'fear': '恐怖',
    'surprise': '驚き',
    'anger': '怒り',
    'other': 'その他',
    'neutral': '普通',
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
    fastMode: false,
    maxFrequency: 24000,   // デフォルトは最大値 24000Hz
    audioQuality: 4.0,     // デフォルトは良好な音質 4.0/5.0
    vqScore: 0.78,         // デフォルトは高品質 0.78
    // 感情強度8軸
    emotionHappiness: 0.0,
    emotionSadness: 0.0,
    emotionDisgust: 0.0,
    emotionFear: 0.0,
    emotionSurprise: 0.0,
    emotionAnger: 0.0,
    emotionOther: 0.0,
    emotionNeutral: 1.0,   // デフォルトは「普通」を最大に
    useEmotionPreset: true, // 初期値はプリセット使用
    
    // 生成パラメータ
    cfgScale: 0.8, // 条件付き確率スケール
    minP: 0.0, // 最小確率サンプリング
    seed: 0, // 乱数シード
    useSeed: false, // シード使用有無

    // オーディオスタイル
    audioPrefix: null, // 音声プレフィックス
    useBreathStyle: false, // 息継ぎスタイル
    useWhisperStyle: false, // ささやきスタイル
    styleIntensity: 0.5, // スタイル強度
    
    // 処理オプション
    useNoiseReduction: true, // ノイズ除去
    useStreamingPlayback: false, // ストリーミング再生
    speakerNoised: false, // 話者ノイズ追加
  });

  // UI状態
  const [uploading, setUploading] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [loadingTTSStatus, setLoadingTTSStatus] = useState(true);
  const [testText, setTestText] = useState('これは音声設定のテストです。設定した感情とトーンで再生されます。');
  const [sampleName, setSampleName] = useState(''); // 新しい音声サンプル名
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedStyleFile, setSelectedStyleFile] = useState<File | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  
  // TTS情報
  const [ttsStatus, setTtsStatus] = useState<TTSStatus | null>(null);
  const [availableFiles, setAvailableFiles] = useState<AudioFile[]>([]);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const styleFileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  // TTSサービス状態を取得
  const fetchTTSStatus = useCallback(async () => {
    try {
      setLoadingTTSStatus(true);
      const response = await fetch('/api/v1/tts/status');
      if (response.ok) {
        const data = await response.json();
        console.log('TTS Status Response:', data); // デバッグ用
        // success_response 形式に対応（payload.data 配下に本体が入る）
        const payload = (data && typeof data === 'object' && 'data' in data) ? (data as { data: TTSStatus }).data : data;
        
        if (data.success) {
          // 複数のレスポンス構造をサポート（下位互換性を保持）
          let ttsStatusData = null;
          
          // 優先順位：tts_details > status.tts_service > フォールバック
          if (payload?.tts_details) {
            ttsStatusData = payload.tts_details;
          } else if (payload?.status?.tts_service) {
            ttsStatusData = payload.status.tts_service;
          } else if (payload?.services?.tts_service === 'available') {
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
      const response = await fetch('/api/v1/tts/voices?type=sample');
      if (response.ok) {
        const data = await response.json();
        const payload = (data && typeof data === 'object' && 'data' in data) ? (data as { data: AudioFile[] }).data : data;
        if (data.success) {
          setAvailableFiles(payload?.files || []);
        }
      }
    } catch (error) {
      console.error('Failed to fetch audio files:', error);
    }
  }, []);

  // 初期化（React StrictMode のダブルマウント対策）
  const didInitRef = useRef(false);
  useEffect(() => {
    if (didInitRef.current) return;
    didInitRef.current = true;

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

      const response = await fetch('/api/v1/tts/upload_voice_sample', {
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
      const response = await fetch(`/api/v1/tts/voices/${fileId}`, {
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
      const apiEndpoint = settings.fastMode ? '/api/v1/tts/synthesize-fast' : '/api/v1/tts/synthesize';
      
      // 基本リクエストボディ
      const baseRequestBody: TTSRequestBody = {
        text: testText,
        language: settings.defaultLanguage,
        speed: settings.voiceSpeed,
        pitch: settings.voicePitch,
        return_url: false,
        max_frequency: settings.maxFrequency,
        audio_quality: settings.audioQuality,
        vq_score: settings.vqScore,
        emotion: settings.defaultEmotion // 初期値として設定（後で上書きされる可能性あり）
      };
      
      // 感情ベクトル準備
      if (settings.useEmotionPreset) {
        // プリセット感情
        baseRequestBody.emotion = settings.defaultEmotion;
      } else {
        // カスタム感情ベクトル
        baseRequestBody.emotion_vector = [
          settings.emotionHappiness,
          settings.emotionSadness,
          settings.emotionDisgust,
          settings.emotionFear,
          settings.emotionSurprise,
          settings.emotionAnger,
          settings.emotionOther,
          settings.emotionNeutral
        ];
        // カスタム感情使用時は emotion を 'custom' に設定
        baseRequestBody.emotion = 'custom';
      }
      
      // 生成パラメータ
      baseRequestBody.cfg_scale = settings.cfgScale;
      baseRequestBody.min_p = settings.minP;
      
      // シード値
      if (settings.useSeed) {
        baseRequestBody.seed = settings.seed;
      }
      
      // オーディオスタイル
      if (settings.audioPrefix) {
        baseRequestBody.audio_prefix = settings.audioPrefix;
      }
      
      if (settings.useBreathStyle) {
        baseRequestBody.breath_style = true;
        baseRequestBody.style_intensity = settings.styleIntensity;
      }
      
      if (settings.useWhisperStyle) {
        baseRequestBody.whisper_style = true;
        baseRequestBody.style_intensity = settings.styleIntensity;
      }
      
      // 処理オプション
      baseRequestBody.noise_reduction = settings.useNoiseReduction;
      baseRequestBody.stream_playback = settings.useStreamingPlayback;

      const requestBody = settings.voiceMode === 'voiceClone'
        ? {
            ...baseRequestBody,
            speaker_sample_id: settings.voiceSampleId || 'default_sample',
            voice_clone_mode: true, // バックエンドへの明示的な指示
            speaker_noised: settings.speakerNoised // 話者ノイズ設定
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

  // 感情プリセット選択ハンドラ
  const handleEmotionPresetChange = useCallback((emotion: string) => {
    // プリセット選択時に該当する感情を1.0、それ以外を0.0に設定
    const emotionValues = {
      emotionHappiness: emotion === 'happiness' ? 1.0 : 0.0,
      emotionSadness: emotion === 'sadness' ? 1.0 : 0.0,
      emotionDisgust: emotion === 'disgust' ? 1.0 : 0.0,
      emotionFear: emotion === 'fear' ? 1.0 : 0.0,
      emotionSurprise: emotion === 'surprise' ? 1.0 : 0.0,
      emotionAnger: emotion === 'anger' ? 1.0 : 0.0,
      emotionOther: emotion === 'other' ? 1.0 : 0.0,
      emotionNeutral: emotion === 'neutral' ? 1.0 : 0.0,
    };

    setSettings(prev => ({ 
      ...prev, 
      defaultEmotion: emotion,
      ...emotionValues
    }));
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

  const handleStyleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedStyleFile(file);
      toast({
        title: 'スタイルファイル選択',
        description: `${file.name} が選択されました`,
        status: 'info',
        duration: 2000,
        isClosable: true,
      });
    }
  };

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
                <FormLabel>感情設定</FormLabel>
                <VStack spacing={2} align="stretch">
                  <HStack>
                    <FormLabel htmlFor="useEmotionPreset" mb={0} fontSize="sm">
                      初期値プリセットを使用
                    </FormLabel>
                    <Switch 
                      id="useEmotionPreset"
                      isChecked={settings.useEmotionPreset}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        useEmotionPreset: e.target.checked 
                      }))}
                    />
                  </HStack>
                  
                  {settings.useEmotionPreset ? (
                    // プリセット選択モード
                    <Select
                      value={settings.defaultEmotion}
                      onChange={(e) => handleEmotionPresetChange(e.target.value)}
                    >
                      {(
                        (ttsStatus?.available_emotions || ['neutral'])
                          // 日本語UIで使用するプリセットだけ許可
                          .filter((e) => ['neutral','happiness','sadness','disgust','fear','surprise','anger','other'].includes(e))
                      ).map((emotion) => (
                        <option key={emotion} value={emotion}>
                          {emotionTranslations[emotion] || emotion}
                        </option>
                      ))}
                    </Select>
                  ) : (
                    // 感情強度8軸スライダー
                    <Accordion allowToggle defaultIndex={[0]}>
                      <AccordionItem>
                        <AccordionButton>
                          <Box as="span" flex='1' textAlign='left'>
                            感情強度調整（8軸）
                          </Box>
                          <AccordionIcon />
                        </AccordionButton>
                        <AccordionPanel pb={4}>
                          <VStack spacing={3} align="stretch">
                            {/* 幸福 */}
                            <FormControl>
                              <FormLabel fontSize="sm">幸福: {settings.emotionHappiness.toFixed(2)}</FormLabel>
                              <Slider
                                value={settings.emotionHappiness}
                                onChange={(value) => setSettings(prev => ({ ...prev, emotionHappiness: value }))}
                                min={0}
                                max={1}
                                step={0.05}
                                colorScheme="yellow"
                              >
                                <SliderTrack>
                                  <SliderFilledTrack />
                                </SliderTrack>
                                <SliderThumb />
                              </Slider>
                            </FormControl>

                            {/* 悲しみ */}
                            <FormControl>
                              <FormLabel fontSize="sm">悲しみ: {settings.emotionSadness.toFixed(2)}</FormLabel>
                              <Slider
                                value={settings.emotionSadness}
                                onChange={(value) => setSettings(prev => ({ ...prev, emotionSadness: value }))}
                                min={0}
                                max={1}
                                step={0.05}
                                colorScheme="blue"
                              >
                                <SliderTrack>
                                  <SliderFilledTrack />
                                </SliderTrack>
                                <SliderThumb />
                              </Slider>
                            </FormControl>

                            {/* 嫌悪 */}
                            <FormControl>
                              <FormLabel fontSize="sm">嫌悪: {settings.emotionDisgust.toFixed(2)}</FormLabel>
                              <Slider
                                value={settings.emotionDisgust}
                                onChange={(value) => setSettings(prev => ({ ...prev, emotionDisgust: value }))}
                                min={0}
                                max={1}
                                step={0.05}
                                colorScheme="purple"
                              >
                                <SliderTrack>
                                  <SliderFilledTrack />
                                </SliderTrack>
                                <SliderThumb />
                              </Slider>
                            </FormControl>

                            {/* 恐怖 */}
                            <FormControl>
                              <FormLabel fontSize="sm">恐怖: {settings.emotionFear.toFixed(2)}</FormLabel>
                              <Slider
                                value={settings.emotionFear}
                                onChange={(value) => setSettings(prev => ({ ...prev, emotionFear: value }))}
                                min={0}
                                max={1}
                                step={0.05}
                                colorScheme="cyan"
                              >
                                <SliderTrack>
                                  <SliderFilledTrack />
                                </SliderTrack>
                                <SliderThumb />
                              </Slider>
                            </FormControl>

                            {/* 驚き */}
                            <FormControl>
                              <FormLabel fontSize="sm">驚き: {settings.emotionSurprise.toFixed(2)}</FormLabel>
                              <Slider
                                value={settings.emotionSurprise}
                                onChange={(value) => setSettings(prev => ({ ...prev, emotionSurprise: value }))}
                                min={0}
                                max={1}
                                step={0.05}
                                colorScheme="green"
                              >
                                <SliderTrack>
                                  <SliderFilledTrack />
                                </SliderTrack>
                                <SliderThumb />
                              </Slider>
                            </FormControl>

                            {/* 怒り */}
                            <FormControl>
                              <FormLabel fontSize="sm">怒り: {settings.emotionAnger.toFixed(2)}</FormLabel>
                              <Slider
                                value={settings.emotionAnger}
                                onChange={(value) => setSettings(prev => ({ ...prev, emotionAnger: value }))}
                                min={0}
                                max={1}
                                step={0.05}
                                colorScheme="red"
                              >
                                <SliderTrack>
                                  <SliderFilledTrack />
                                </SliderTrack>
                                <SliderThumb />
                              </Slider>
                            </FormControl>

                            {/* その他 */}
                            <FormControl>
                              <FormLabel fontSize="sm">その他: {settings.emotionOther.toFixed(2)}</FormLabel>
                              <Slider
                                value={settings.emotionOther}
                                onChange={(value) => setSettings(prev => ({ ...prev, emotionOther: value }))}
                                min={0}
                                max={1}
                                step={0.05}
                                colorScheme="orange"
                              >
                                <SliderTrack>
                                  <SliderFilledTrack />
                                </SliderTrack>
                                <SliderThumb />
                              </Slider>
                            </FormControl>

                            {/* 普通 */}
                            <FormControl>
                              <FormLabel fontSize="sm">普通: {settings.emotionNeutral.toFixed(2)}</FormLabel>
                              <Slider
                                value={settings.emotionNeutral}
                                onChange={(value) => setSettings(prev => ({ ...prev, emotionNeutral: value }))}
                                min={0}
                                max={1}
                                step={0.05}
                                colorScheme="gray"
                              >
                                <SliderTrack>
                                  <SliderFilledTrack />
                                </SliderTrack>
                                <SliderThumb />
                              </Slider>
                            </FormControl>
                          </VStack>
                        </AccordionPanel>
                      </AccordionItem>
                    </Accordion>
                  )}
                </VStack>
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

              {/* 音質詳細設定（アコーディオン） */}
              <Accordion allowToggle mt={2}>
                <AccordionItem>
                  <AccordionButton>
                    <Box as="span" flex='1' textAlign='left'>
                      音質詳細設定
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel pb={4}>
                    <VStack spacing={4} align="stretch">
                      {/* 最大周波数調整 */}
                      <FormControl>
                        <FormLabel>最大周波数: {settings.maxFrequency}Hz</FormLabel>
                        <Slider
                          value={settings.maxFrequency}
                          onChange={(value) => setSettings(prev => ({ ...prev, maxFrequency: value }))}
                          min={8000}
                          max={24000}
                          step={1000}
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                        <Text fontSize="xs" color="gray.500">
                          低い値=柔らかい音質、高い値=クリアな音質（デフォルト:24000）
                        </Text>
                      </FormControl>

                      {/* 音質スコア調整 */}
                      <FormControl>
                        <FormLabel>音質スコア: {settings.audioQuality.toFixed(1)}</FormLabel>
                        <Slider
                          value={settings.audioQuality}
                          onChange={(value) => setSettings(prev => ({ ...prev, audioQuality: value }))}
                          min={1.0}
                          max={5.0}
                          step={0.1}
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                        <Text fontSize="xs" color="gray.500">
                          音声の明瞭さと自然さのバランス（デフォルト:4.0）
                        </Text>
                      </FormControl>

                      {/* VQスコア調整 */}
                      <FormControl>
                        <FormLabel>VQスコア: {settings.vqScore.toFixed(2)}</FormLabel>
                        <Slider
                          value={settings.vqScore}
                          onChange={(value) => setSettings(prev => ({ ...prev, vqScore: value }))}
                          min={0.5}
                          max={0.8}
                          step={0.01}
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                        <Text fontSize="xs" color="gray.500">
                          音声の音響品質（デフォルト:0.78）
                        </Text>
                      </FormControl>
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              </Accordion>

              {/* 生成パラメータ設定（アコーディオン） */}
              <Accordion allowToggle mt={2}>
                <AccordionItem>
                  <AccordionButton>
                    <Box as="span" flex='1' textAlign='left'>
                      生成パラメータ設定
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel pb={4}>
                    <VStack spacing={4} align="stretch">
                      {/* CFGスケール調整 */}
                      <FormControl>
                        <FormLabel>CFGスケール: {settings.cfgScale.toFixed(2)}</FormLabel>
                        <Slider
                          value={settings.cfgScale}
                          onChange={(value) => setSettings(prev => ({ ...prev, cfgScale: value }))}
                          min={0.0}
                          max={1.5}
                          step={0.05}
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                        <Text fontSize="xs" color="gray.500">
                          低い値=自由度高、高い値=一貫性重視（デフォルト:0.8）
                        </Text>
                      </FormControl>

                      {/* Min-P調整 */}
                      <FormControl>
                        <FormLabel>Min-P: {settings.minP.toFixed(2)}</FormLabel>
                        <Slider
                          value={settings.minP}
                          onChange={(value) => setSettings(prev => ({ ...prev, minP: value }))}
                          min={0.0}
                          max={1.0}
                          step={0.05}
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                        <Text fontSize="xs" color="gray.500">
                          最小確率サンプリング値（高いほど自然だが変化少）
                        </Text>
                      </FormControl>

                      {/* シード設定 */}
                      <FormControl>
                        <HStack justify="space-between" align="center">
                          <FormLabel mb={0}>乱数シード使用</FormLabel>
                          <Switch
                            isChecked={settings.useSeed}
                            onChange={(e) => setSettings(prev => ({ ...prev, useSeed: e.target.checked }))}
                          />
                        </HStack>
                        
                        {settings.useSeed && (
                          <HStack mt={2}>
                            <NumberInput 
                              value={settings.seed} 
                              min={0} 
                              max={2147483647}
                              onChange={(_, value) => setSettings(prev => ({ ...prev, seed: value }))}
                              size="sm"
                              flex={1}
                            >
                              <NumberInputField />
                              <NumberInputStepper>
                                <NumberIncrementStepper />
                                <NumberDecrementStepper />
                              </NumberInputStepper>
                            </NumberInput>
                            <Button 
                              size="sm"
                              onClick={() => setSettings(prev => ({ 
                                ...prev, 
                                seed: Math.floor(Math.random() * 2147483647) 
                              }))}
                            >
                              ランダム
                            </Button>
                          </HStack>
                        )}
                        <Text fontSize="xs" color="gray.500" mt={1}>
                          同じシードで同じ内容を生成すると同じ結果になります
                        </Text>
                      </FormControl>
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              </Accordion>

              {/* オーディオスタイル設定（アコーディオン） */}
              <Accordion allowToggle mt={2}>
                <AccordionItem>
                  <AccordionButton>
                    <Box as="span" flex='1' textAlign='left'>
                      オーディオスタイル設定
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel pb={4}>
                    <VStack spacing={4} align="stretch">
                      {/* オーディオプレフィックス */}
                      <FormControl>
                        <FormLabel>音声プレフィックス</FormLabel>
                        <Input 
                          placeholder="例: うーん、あのー、えっと" 
                          size="sm"
                          value={settings.audioPrefix || ''}
                          onChange={(e) => setSettings(prev => ({ 
                            ...prev, 
                            audioPrefix: e.target.value || null 
                          }))}
                        />
                        <Text fontSize="xs" color="gray.500" mt={1}>
                          生成音声の先頭に付与するフレーズ
                        </Text>
                      </FormControl>

                      {/* スタイルチェックボックス */}
                      <VStack spacing={2} align="stretch">
                        <FormControl display="flex" alignItems="center">
                          <FormLabel htmlFor="useBreathStyle" mb="0" fontSize="sm">
                            息継ぎスタイル
                          </FormLabel>
                          <Spacer />
                          <Switch 
                            id="useBreathStyle"
                            colorScheme="blue"
                            isChecked={settings.useBreathStyle}
                            onChange={(e) => setSettings(prev => ({ 
                              ...prev, 
                              useBreathStyle: e.target.checked 
                            }))}
                          />
                        </FormControl>

                        <FormControl display="flex" alignItems="center">
                          <FormLabel htmlFor="useWhisperStyle" mb="0" fontSize="sm">
                            ささやきスタイル (Whisper風)
                          </FormLabel>
                          <Spacer />
                          <Switch 
                            id="useWhisperStyle"
                            colorScheme="blue"
                            isChecked={settings.useWhisperStyle}
                            onChange={(e) => setSettings(prev => ({ 
                              ...prev, 
                              useWhisperStyle: e.target.checked 
                            }))}
                          />
                        </FormControl>
                      </VStack>

                      {/* スタイル強度 */}
                      {(settings.useBreathStyle || settings.useWhisperStyle) && (
                        <FormControl>
                          <FormLabel>スタイル強度: {settings.styleIntensity.toFixed(2)}</FormLabel>
                          <Slider
                            value={settings.styleIntensity}
                            onChange={(value) => setSettings(prev => ({ ...prev, styleIntensity: value }))}
                            min={0.1}
                            max={1.0}
                            step={0.05}
                          >
                            <SliderTrack>
                              <SliderFilledTrack />
                            </SliderTrack>
                            <SliderThumb />
                          </Slider>
                          <Text fontSize="xs" color="gray.500">
                            スタイルの適用強度（高いほど特徴的）
                          </Text>
                        </FormControl>
                      )}

                      {/* スタイルファイルアップロード */}
                      <FormControl>
                        <FormLabel>スタイル参照ファイル</FormLabel>
                        <HStack>
                          <Input
                            type="file"
                            accept="audio/*"
                            onChange={handleStyleFileUpload}
                            size="sm"
                            display="none"
                            ref={styleFileInputRef}
                          />
                          <Button
                            onClick={() => styleFileInputRef.current?.click()}
                            size="sm"
                            leftIcon={<FaUpload />}
                          >
                            ファイル選択
                          </Button>
                          <Text 
                            fontSize="sm" 
                            color={selectedStyleFile ? "green.500" : "gray.500"}
                          >
                            {selectedStyleFile ? selectedStyleFile.name : '未選択'}
                          </Text>
                        </HStack>
                        <Text fontSize="xs" color="gray.500" mt={1}>
                          特定のスタイルを参照するオーディオファイル
                        </Text>
                      </FormControl>
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              </Accordion>

              {/* 処理オプション設定 */}
              <FormControl mt={4}>
                <FormLabel>処理オプション</FormLabel>
                <VStack spacing={2} align="stretch">
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="useNoiseReduction" mb="0" fontSize="sm">
                      ノイズ除去
                    </FormLabel>
                    <Spacer />
                    <Switch 
                      id="useNoiseReduction"
                      colorScheme="blue"
                      isChecked={settings.useNoiseReduction}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        useNoiseReduction: e.target.checked 
                      }))}
                    />
                  </FormControl>

                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="useStreamingPlayback" mb="0" fontSize="sm">
                      ストリーミング再生
                    </FormLabel>
                    <Spacer />
                    <Switch 
                      id="useStreamingPlayback"
                      colorScheme="blue"
                      isChecked={settings.useStreamingPlayback}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        useStreamingPlayback: e.target.checked 
                      }))}
                    />
                  </FormControl>
                </VStack>
                <Text fontSize="xs" color="gray.500" mt={1}>
                  ストリーミング再生: リアルタイムで音声を再生します
                </Text>
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
              <HStack justify="space-between">
                <Text>高速モード:</Text>
                <Badge colorScheme={settings.fastMode ? 'green' : 'gray'}>
                  {settings.fastMode ? 'ON' : 'OFF'}
                </Badge>
              </HStack>
              <Divider my={1} />
              <HStack justify="space-between">
                <Text>最大周波数:</Text>
                <Badge>{settings.maxFrequency}Hz</Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>音質スコア:</Text>
                <Badge>{settings.audioQuality.toFixed(1)}</Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>VQスコア:</Text>
                <Badge>{settings.vqScore.toFixed(2)}</Badge>
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