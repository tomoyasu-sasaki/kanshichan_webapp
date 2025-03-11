import { Box, VStack, Text, HStack, Badge, IconButton, useToast } from '@chakra-ui/react';
import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { FaExpand, FaCompress } from 'react-icons/fa';

interface DetectionStatus {
  personDetected: boolean;
  smartphoneDetected: boolean;
  absenceTime: number;
  smartphoneUseTime: number;
}

export const MonitorView = () => {
  const videoRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const toast = useToast();
  const [status, setStatus] = useState<DetectionStatus>({
    personDetected: false,
    smartphoneDetected: false,
    absenceTime: 0,
    smartphoneUseTime: 0
  });

  useEffect(() => {
    // WebSocketの設定
    const socket = io('http://localhost:5001', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });
    
    socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      toast({
        title: '接続エラー',
        description: 'サーバーとの接続に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    });

    socket.on('status_update', (newStatus: DetectionStatus) => {
      setStatus(newStatus);
    });

    return () => {
      socket.disconnect();
    };
  }, [toast]);

  useEffect(() => {
    let frameRequestId: number;
    const updateImage = () => {
      if (videoRef.current) {
        videoRef.current.src = `http://localhost:5001/api/video_feed?t=${Date.now()}`;
      }
      frameRequestId = requestAnimationFrame(updateImage);
    };

    frameRequestId = requestAnimationFrame(updateImage);
    return () => {
      if (frameRequestId) {
        cancelAnimationFrame(frameRequestId);
      }
    };
  }, []);

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await containerRef.current?.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
      }
    } catch (error) {
      toast({
        title: 'エラー',
        description: '全画面表示の切り替えに失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  return (
    <Box
      ref={containerRef}
      position="relative"
      width="100%"
      height={isFullscreen ? "100vh" : "calc(100vh - 100px)"}
      bg="black"
    >
      <img
        ref={videoRef}
        alt="Monitor"
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
        }}
      />
      
      {/* ステータスオーバーレイ */}
      <Box
        position="absolute"
        top={4}
        right={4}
        p={4}
        bg="rgba(0, 0, 0, 0.7)"
        color="white"
        borderRadius="md"
        zIndex={1}
      >
        <VStack align="start" spacing={2}>
          <HStack>
            <Text>在席状態:</Text>
            <Badge colorScheme={status.personDetected ? 'green' : 'red'}>
              {status.personDetected ? '在席中' : '不在'}
            </Badge>
          </HStack>
          {!status.personDetected && (
            <Text>不在時間: {Math.floor(status.absenceTime)}秒</Text>
          )}
          <HStack>
            <Text>スマートフォン:</Text>
            <Badge colorScheme={status.smartphoneDetected ? 'red' : 'green'}>
              {status.smartphoneDetected ? '使用中' : '未使用'}
            </Badge>
          </HStack>
          {status.smartphoneDetected && (
            <Text>使用時間: {Math.floor(status.smartphoneUseTime)}秒</Text>
          )}
        </VStack>
      </Box>

      {/* 全画面表示ボタン */}
      <IconButton
        aria-label="Toggle fullscreen"
        icon={isFullscreen ? <FaCompress /> : <FaExpand />}
        position="absolute"
        bottom={4}
        right={4}
        colorScheme="blackAlpha"
        onClick={toggleFullscreen}
        zIndex={1}
      />
    </Box>
  );
}; 