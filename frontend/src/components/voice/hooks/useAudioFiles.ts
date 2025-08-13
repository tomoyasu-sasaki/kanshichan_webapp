import { useState, useCallback } from 'react';
import type { AudioFile } from '../types';

export const useAudioFiles = () => {
  const [availableFiles, setAvailableFiles] = useState<AudioFile[]>([]);

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

  return {
    availableFiles,
    fetchAudioFiles
  };
};