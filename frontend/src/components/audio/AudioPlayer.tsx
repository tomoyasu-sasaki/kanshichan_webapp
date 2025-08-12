import {
  Box,
  VStack,
  HStack,
  Text,
  IconButton,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Badge,
  List,
  ListItem,
  Tooltip,
  Alert,
  AlertIcon,
  useToast
} from '@chakra-ui/react';
import { useEffect, useState, useCallback, useRef } from 'react';
import { 
  FaPlay, 
  FaPause, 
  FaStop, 
  FaVolumeUp, 
  FaVolumeMute,
  FaStepForward,
  FaStepBackward,
  FaRetweet,
  FaRandom
} from 'react-icons/fa';
import { 
  websocketManager, 
  AudioStreamData,
  AudioNotification,
  AudioStatusUpdate
} from '../../utils/websocket.ts';

interface AudioPlayerProps {
  autoPlay?: boolean;
  showQueue?: boolean;
  showControls?: boolean;
}

interface QueuedAudio {
  id: string;
  title: string;
  duration?: number;
  status: 'waiting' | 'playing' | 'completed' | 'error';
  metadata?: {
    text_content?: string;
    emotion?: string;
    language?: string;
    voice_cloned?: boolean;
  };
}

interface PlaybackState {
  isPlaying: boolean;
  isPaused: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  currentTrack: QueuedAudio | null;
  repeatMode: 'none' | 'one' | 'all';
  shuffleMode: boolean;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  autoPlay = true,
  showQueue = true,
  showControls = true
}) => {
  // 再生状態
  const [playbackState, setPlaybackState] = useState<PlaybackState>({
    isPlaying: false,
    isPaused: false,
    currentTime: 0,
    duration: 0,
    volume: 0.7,
    isMuted: false,
    currentTrack: null,
    repeatMode: 'none',
    shuffleMode: false
  });

  // キュー管理
  const [audioQueue, setAudioQueue] = useState<QueuedAudio[]>([]);
  const [currentIndex, setCurrentIndex] = useState(-1);

  // WebSocket状態
  const [isConnected, setIsConnected] = useState(false);
  const [streamingStatus, setStreamingStatus] = useState({
    connected_clients: 0,
    audio_queue_size: 0
  });

  // 音声要素の参照
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const progressUpdateRef = useRef<number | null>(null);
  const toast = useToast();

  // 音声要素の初期化
  useEffect(() => {
    const audio = new Audio();
    audio.volume = playbackState.volume;
    
    // 音声イベントリスナー
    audio.addEventListener('loadedmetadata', () => {
      setPlaybackState(prev => ({
        ...prev,
        duration: audio.duration
      }));
    });

    audio.addEventListener('timeupdate', () => {
      setPlaybackState(prev => ({
        ...prev,
        currentTime: audio.currentTime
      }));
    });

    audio.addEventListener('ended', handleTrackEnded);
    audio.addEventListener('error', handleAudioError);

    audioRef.current = audio;

    return () => {
      if (progressUpdateRef.current) {
        cancelAnimationFrame(progressUpdateRef.current);
      }
      audio.removeEventListener('loadedmetadata', () => {});
      audio.removeEventListener('timeupdate', () => {});
      audio.removeEventListener('ended', handleTrackEnded);
      audio.removeEventListener('error', handleAudioError);
    };
  }, []);

  // WebSocket接続管理
  useEffect(() => {
    websocketManager.initialize();

    const connectUnsub = websocketManager.onConnect(() => {
      setIsConnected(true);
      updateStreamingStatus();
    });

    const disconnectUnsub = websocketManager.onDisconnect(() => {
      setIsConnected(false);
    });

    const audioStreamUnsub = websocketManager.onAudioStream(handleAudioStream);
    const audioNotificationUnsub = websocketManager.onAudioNotification(handleAudioNotification);
    const audioStatusUnsub = websocketManager.onAudioStatusUpdate(handleAudioStatusUpdate);

    // 定期的なステータス更新
    const statusInterval = setInterval(updateStreamingStatus, 10000);

    return () => {
      connectUnsub();
      disconnectUnsub();
      audioStreamUnsub();
      audioNotificationUnsub();
      audioStatusUnsub();
      clearInterval(statusInterval);
    };
  }, []);

  // 音量変更の同期
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = playbackState.isMuted ? 0 : playbackState.volume;
    }
  }, [playbackState.volume, playbackState.isMuted]);

  // ストリーミング状態更新
  const updateStreamingStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/tts/streaming-status');
      if (response.ok) {
        const data = await response.json();
        const payload = data?.data || data;
        const connected = payload?.streaming_system?.connected_clients ?? 0;
        const queueSize = payload?.streaming_system?.active_streams ?? 0;
        setStreamingStatus({ connected_clients: connected, audio_queue_size: queueSize });
      }
    } catch (error) {
      console.error('Failed to update streaming status:', error);
    }
  }, []);

  // 音声ストリーム受信処理
  const handleAudioStream = useCallback((data?: AudioStreamData) => {
    if (!data) return;

    const newTrack: QueuedAudio = {
      id: data.metadata.audio_id,
      title: data.metadata.text_content?.substring(0, 50) + '...' || '音声メッセージ',
      status: 'waiting',
      metadata: {
        text_content: data.metadata.text_content,
        emotion: data.metadata.emotion,
        language: data.metadata.language,
        voice_cloned: data.metadata.streaming_mode // streaming_mode を voice_cloned として使用
      }
    };

    setAudioQueue(prev => [...prev, newTrack]);

    // 自動再生が有効で現在再生中でない場合、即座に再生開始
    if (autoPlay && !playbackState.isPlaying && audioQueue.length === 0) {
      playAudioFromBlob(data.audio_data, newTrack); // audio_data_base64 → audio_data
    }

    toast({
      title: '新しい音声',
      description: `音声メッセージが届きました: ${data.metadata.emotion}`,
      status: 'info',
      duration: 3000,
      isClosable: true,
    });
  }, [autoPlay, playbackState.isPlaying, audioQueue.length, toast]);

  // 音声通知処理
  const handleAudioNotification = useCallback((notification?: AudioNotification) => {
    if (!notification) return;

    // キューの状態更新
    if (notification.audio_id) {
      setAudioQueue(prev => prev.map(track => 
        track.id === notification.audio_id
          ? { 
              ...track, 
              status: notification.type === 'tts_completed' ? 'waiting' :
                      notification.type === 'tts_error' ? 'error' : track.status
            }
          : track
      ));
    }
  }, []);

  // 音声状態更新処理
  const handleAudioStatusUpdate = useCallback((statusUpdate?: AudioStatusUpdate) => {
    if (!statusUpdate) return;

    setAudioQueue(prev => prev.map(track => 
      track.id === statusUpdate.audio_id
        ? { 
            ...track, 
            status: statusUpdate.status === 'playing' ? 'playing' :
                   statusUpdate.status === 'finished' ? 'completed' :
                   statusUpdate.status === 'error' ? 'error' : track.status
          }
        : track
    ));
  }, []);

  // Base64音声データから再生
  const playAudioFromBlob = useCallback(async (base64Data: string, track: QueuedAudio) => {
    if (!audioRef.current) return;

    try {
      // Base64データをBlobに変換
      const binaryString = atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(blob);

      // 音声要素に設定
      audioRef.current.src = audioUrl;
      
      // 再生状態更新
      setPlaybackState(prev => ({
        ...prev,
        isPlaying: true,
        isPaused: false,
        currentTrack: track
      }));

      // キューのインデックス更新
      const trackIndex = audioQueue.findIndex(q => q.id === track.id);
      if (trackIndex !== -1) {
        setCurrentIndex(trackIndex);
      }

      // 再生開始
      await audioRef.current.play();

      // WebSocketにステータス送信
      websocketManager.notifyAudioPlaybackStatus(track.id, 'playing');

    } catch (error) {
      console.error('Failed to play audio:', error);
      setPlaybackState(prev => ({
        ...prev,
        isPlaying: false,
        currentTrack: null
      }));
      
      toast({
        title: '再生エラー',
        description: '音声の再生に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  }, [audioQueue, toast]);

  // トラック終了処理
  const handleTrackEnded = useCallback(() => {
    if (playbackState.currentTrack) {
      websocketManager.notifyAudioPlaybackStatus(playbackState.currentTrack.id, 'finished');
    }

    setPlaybackState(prev => ({
      ...prev,
      isPlaying: false,
      currentTrack: null,
      currentTime: 0
    }));

    // 次のトラックへ進む
    if (playbackState.repeatMode === 'one') {
      // 同じトラックを繰り返し
      if (playbackState.currentTrack && audioRef.current) {
        audioRef.current.currentTime = 0;
        audioRef.current.play();
      }
    } else if (currentIndex < audioQueue.length - 1) {
      // 次のトラックへ
      playNextTrack();
    } else if (playbackState.repeatMode === 'all') {
      // キューの最初から再生
      setCurrentIndex(0);
      if (audioQueue.length > 0) {
        playTrackAtIndex(0);
      }
    }
  }, [playbackState.currentTrack, playbackState.repeatMode, currentIndex, audioQueue]);

  // 音声エラー処理
  const handleAudioError = useCallback(() => {
    if (playbackState.currentTrack) {
      websocketManager.notifyAudioPlaybackStatus(playbackState.currentTrack.id, 'error');
    }

    setPlaybackState(prev => ({
      ...prev,
      isPlaying: false,
      currentTrack: null
    }));

    toast({
      title: '再生エラー',
      description: '音声の再生中にエラーが発生しました',
      status: 'error',
      duration: 3000,
      isClosable: true,
    });
  }, [playbackState.currentTrack, toast]);

  // 再生/一時停止切り替え
  const togglePlayPause = useCallback(() => {
    if (!audioRef.current) return;

    if (playbackState.isPlaying) {
      audioRef.current.pause();
      setPlaybackState(prev => ({
        ...prev,
        isPlaying: false,
        isPaused: true
      }));
    } else {
      audioRef.current.play();
      setPlaybackState(prev => ({
        ...prev,
        isPlaying: true,
        isPaused: false
      }));
    }
  }, [playbackState.isPlaying]);

  // 停止
  const stopPlayback = useCallback(() => {
    if (!audioRef.current) return;

    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    
    setPlaybackState(prev => ({
      ...prev,
      isPlaying: false,
      isPaused: false,
      currentTime: 0,
      currentTrack: null
    }));
  }, []);

  // 次のトラック
  const playNextTrack = useCallback(() => {
    const nextIndex = playbackState.shuffleMode 
      ? Math.floor(Math.random() * audioQueue.length)
      : currentIndex + 1;

    if (nextIndex < audioQueue.length) {
      playTrackAtIndex(nextIndex);
    }
  }, [playbackState.shuffleMode, currentIndex, audioQueue.length]);

  // 前のトラック
  const playPreviousTrack = useCallback(() => {
    const prevIndex = Math.max(0, currentIndex - 1);
    playTrackAtIndex(prevIndex);
  }, [currentIndex]);

  // 指定インデックスのトラックを再生
  const playTrackAtIndex = useCallback(async (index: number) => {
    if (index < 0 || index >= audioQueue.length) return;

    const track = audioQueue[index];
    setCurrentIndex(index);

    // 実際の音声データが必要な場合はAPIから取得
    // ここでは仮実装として、キューにある情報のみ使用
    try {
      // APIから音声ファイルを取得（file_idが必要）
      const response = await fetch(`/api/v1/tts/audio/${track.id}`);
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          await audioRef.current.play();
          
          setPlaybackState(prev => ({
            ...prev,
            isPlaying: true,
            isPaused: false,
            currentTrack: track
          }));
        }
      }
    } catch (error) {
      console.error('Failed to load track:', error);
    }
  }, [audioQueue]);

  // 音量変更
  const handleVolumeChange = useCallback((value: number) => {
    setPlaybackState(prev => ({
      ...prev,
      volume: value,
      isMuted: value === 0
    }));
  }, []);

  // ミュート切り替え
  const toggleMute = useCallback(() => {
    setPlaybackState(prev => ({
      ...prev,
      isMuted: !prev.isMuted
    }));
  }, []);

  // リピートモード切り替え
  const toggleRepeatMode = useCallback(() => {
    setPlaybackState(prev => ({
      ...prev,
      repeatMode: prev.repeatMode === 'none' ? 'all' : 
                  prev.repeatMode === 'all' ? 'one' : 'none'
    }));
  }, []);

  // シャッフルモード切り替え
  const toggleShuffleMode = useCallback(() => {
    setPlaybackState(prev => ({
      ...prev,
      shuffleMode: !prev.shuffleMode
    }));
  }, []);

  // プログレス変更
  const handleProgressChange = useCallback((value: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = value;
      setPlaybackState(prev => ({
        ...prev,
        currentTime: value
      }));
    }
  }, []);

  // 時間フォーマット
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Box width="100%" maxWidth="600px" mx="auto">
      <VStack spacing={4} align="stretch">
        {/* 接続状態 */}
        <Card>
          <CardHeader>
            <HStack justify="space-between" align="center">
              <Heading size="sm">音声プレイヤー</Heading>
              <HStack spacing={2}>
                <Badge colorScheme={isConnected ? 'green' : 'red'}>
                  {isConnected ? '接続中' : '切断'}
                </Badge>
                <Badge colorScheme="blue">
                  {streamingStatus.connected_clients} クライアント
                </Badge>
                <Badge colorScheme="purple">
                  キュー: {streamingStatus.audio_queue_size}
                </Badge>
              </HStack>
            </HStack>
          </CardHeader>
        </Card>

        {/* 現在の再生 */}
        {playbackState.currentTrack && (
          <Card>
            <CardBody>
              <VStack spacing={3} align="stretch">
                <Text fontWeight="bold" fontSize="md">
                  {playbackState.currentTrack.title}
                </Text>
                
                {playbackState.currentTrack.metadata && (
                  <HStack spacing={2} flexWrap="wrap">
                    {playbackState.currentTrack.metadata.emotion && (
                      <Badge colorScheme="blue">
                        {playbackState.currentTrack.metadata.emotion}
                      </Badge>
                    )}
                    {playbackState.currentTrack.metadata.language && (
                      <Badge colorScheme="green">
                        {playbackState.currentTrack.metadata.language}
                      </Badge>
                    )}
                    {playbackState.currentTrack.metadata.voice_cloned && (
                      <Badge colorScheme="purple">
                        音声クローン
                      </Badge>
                    )}
                  </HStack>
                )}

                {/* プログレスバー */}
                <VStack spacing={1} align="stretch">
                  <Slider
                    value={playbackState.currentTime}
                    max={playbackState.duration || 100}
                    onChange={handleProgressChange}
                    isDisabled={!playbackState.currentTrack}
                  >
                    <SliderTrack>
                      <SliderFilledTrack />
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                  <HStack justify="space-between" fontSize="sm" color="gray.500">
                    <Text>{formatTime(playbackState.currentTime)}</Text>
                    <Text>{formatTime(playbackState.duration)}</Text>
                  </HStack>
                </VStack>
              </VStack>
            </CardBody>
          </Card>
        )}

        {/* 再生コントロール */}
        {showControls && (
          <Card>
            <CardBody>
              <VStack spacing={4}>
                {/* メインコントロール */}
                <HStack spacing={4} justify="center">
                  <Tooltip label="前のトラック">
                    <IconButton
                      aria-label="Previous track"
                      icon={<FaStepBackward />}
                      onClick={playPreviousTrack}
                      isDisabled={currentIndex <= 0}
                      size="sm"
                    />
                  </Tooltip>
                  
                  <Tooltip label={playbackState.isPlaying ? "一時停止" : "再生"}>
                    <IconButton
                      aria-label="Play/Pause"
                      icon={playbackState.isPlaying ? <FaPause /> : <FaPlay />}
                      onClick={togglePlayPause}
                      isDisabled={!playbackState.currentTrack}
                      colorScheme="blue"
                      size="lg"
                    />
                  </Tooltip>
                  
                  <Tooltip label="停止">
                    <IconButton
                      aria-label="Stop"
                      icon={<FaStop />}
                      onClick={stopPlayback}
                      isDisabled={!playbackState.currentTrack}
                      size="sm"
                    />
                  </Tooltip>
                  
                  <Tooltip label="次のトラック">
                    <IconButton
                      aria-label="Next track"
                      icon={<FaStepForward />}
                      onClick={playNextTrack}
                      isDisabled={currentIndex >= audioQueue.length - 1}
                      size="sm"
                    />
                  </Tooltip>
                </HStack>

                {/* 音量コントロール */}
                <HStack spacing={3} width="100%">
                  <Tooltip label={playbackState.isMuted ? "ミュート解除" : "ミュート"}>
                    <IconButton
                      aria-label="Mute/Unmute"
                      icon={playbackState.isMuted ? <FaVolumeMute /> : <FaVolumeUp />}
                      onClick={toggleMute}
                      size="sm"
                      variant="ghost"
                    />
                  </Tooltip>
                  
                  <Slider
                    value={playbackState.isMuted ? 0 : playbackState.volume}
                    onChange={handleVolumeChange}
                    min={0}
                    max={1}
                    step={0.1}
                    flex={1}
                  >
                    <SliderTrack>
                      <SliderFilledTrack />
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                  
                  <Text fontSize="sm" minWidth="30px">
                    {Math.round(playbackState.volume * 100)}%
                  </Text>
                </HStack>

                {/* 追加コントロール */}
                <HStack spacing={2} justify="center">
                  <Tooltip label={`リピート: ${playbackState.repeatMode}`}>
                    <IconButton
                      aria-label="Repeat mode"
                      icon={<FaRetweet />}
                      onClick={toggleRepeatMode}
                      colorScheme={playbackState.repeatMode !== 'none' ? 'blue' : 'gray'}
                      variant={playbackState.repeatMode !== 'none' ? 'solid' : 'ghost'}
                      size="sm"
                    />
                  </Tooltip>
                  
                  <Tooltip label="シャッフル">
                    <IconButton
                      aria-label="Shuffle mode"
                      icon={<FaRandom />}
                      onClick={toggleShuffleMode}
                      colorScheme={playbackState.shuffleMode ? 'blue' : 'gray'}
                      variant={playbackState.shuffleMode ? 'solid' : 'ghost'}
                      size="sm"
                    />
                  </Tooltip>
                </HStack>
              </VStack>
            </CardBody>
          </Card>
        )}

        {/* 音声キュー */}
        {showQueue && (
          <Card>
            <CardHeader>
              <Heading size="sm">音声キュー ({audioQueue.length})</Heading>
            </CardHeader>
            <CardBody>
              {audioQueue.length > 0 ? (
                <List spacing={2}>
                  {audioQueue.map((track, index) => (
                    <ListItem 
                      key={track.id}
                      onClick={() => playTrackAtIndex(index)}
                      cursor="pointer"
                      _hover={{ bg: 'gray.50' }}
                      p={2}
                      borderRadius="md"
                      bg={index === currentIndex ? 'blue.50' : 'transparent'}
                    >
                      <HStack justify="space-between">
                        <VStack align="start" spacing={1} flex={1}>
                          <Text fontSize="sm" fontWeight="medium">
                            {track.title}
                          </Text>
                          {track.metadata && (
                            <HStack spacing={1}>
                              {track.metadata.emotion && (
                                <Badge size="xs" colorScheme="blue">
                                  {track.metadata.emotion}
                                </Badge>
                              )}
                              {track.metadata.language && (
                                <Badge size="xs" colorScheme="green">
                                  {track.metadata.language}
                                </Badge>
                              )}
                            </HStack>
                          )}
                        </VStack>
                        <Badge
                          colorScheme={
                            track.status === 'playing' ? 'blue' :
                            track.status === 'completed' ? 'green' :
                            track.status === 'error' ? 'red' : 'gray'
                          }
                          size="sm"
                        >
                          {track.status === 'playing' ? '再生中' :
                           track.status === 'completed' ? '完了' :
                           track.status === 'error' ? 'エラー' : '待機中'}
                        </Badge>
                      </HStack>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Alert status="info">
                  <AlertIcon />
                  音声キューは空です
                </Alert>
              )}
            </CardBody>
          </Card>
        )}
      </VStack>
    </Box>
  );
}; 