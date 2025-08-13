import { useState, useCallback } from 'react';
import { useToast } from '@chakra-ui/react';
import type { VoiceSettings, TTSRequestBody } from '../types';

export const useVoicePreview = () => {
  const [previewing, setPreviewing] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const toast = useToast();

  // ブラウザTTSフォールバック処理
  const handleBrowserTTSFallback = useCallback(async (testText: string, settings: VoiceSettings) => {
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
  }, [toast]);

  // 音声プレビュー
  const handlePreview = useCallback(async (testText: string, settings: VoiceSettings) => {
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
          await handleBrowserTTSFallback(testText, settings);
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
        
        await handleBrowserTTSFallback(testText, settings);
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
  }, [previewing, currentAudio, toast, handleBrowserTTSFallback]);

  return {
    previewing,
    handlePreview
  };
};