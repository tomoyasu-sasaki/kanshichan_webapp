import { useState, useCallback, useRef, useEffect } from 'react';
import type { TTSStatus } from '../types';

export const useTTSStatus = () => {
  const [ttsStatus, setTtsStatus] = useState<TTSStatus | null>(null);
  const [loadingTTSStatus, setLoadingTTSStatus] = useState(true);

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

  // 初期化（React StrictMode のダブルマウント対策）
  const didInitRef = useRef(false);
  useEffect(() => {
    if (didInitRef.current) return;
    didInitRef.current = true;
    fetchTTSStatus();
  }, [fetchTTSStatus]);

  return {
    ttsStatus,
    loadingTTSStatus,
    fetchTTSStatus
  };
};