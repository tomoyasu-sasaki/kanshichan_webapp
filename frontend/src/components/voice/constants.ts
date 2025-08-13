// Voice Settings Constants
export const emotionTranslations: Record<string, string> = {
  'happiness': '幸福',
  'sadness': '悲しみ',
  'disgust': '嫌悪',
  'fear': '恐怖',
  'surprise': '驚き',
  'anger': '怒り',
  'other': 'その他',
  'neutral': '普通',
};

export const defaultVoiceSettings = {
  voiceMode: 'tts' as const,
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
};