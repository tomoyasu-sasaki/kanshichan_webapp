// Voice Settings Types
export interface VoiceSettings {
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

export interface AudioFile {
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

export interface TTSRequestBody {
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

export interface TTSStatus {
  initialized: boolean;
  model_name: string;
  device: string;
  voice_cloning_enabled: boolean;
  default_language: string;
  supported_languages: string[];
  available_emotions: string[];
}

export interface VoiceSettingsProps {
  onSettingsChange?: (settings: VoiceSettings) => void;
}