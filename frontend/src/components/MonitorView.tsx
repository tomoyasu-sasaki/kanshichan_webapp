import { Box, VStack, Text, HStack, Badge, IconButton, useToast } from '@chakra-ui/react';
import { useEffect, useRef, useState } from 'react';
import { FaExpand, FaCompress } from 'react-icons/fa';
import { websocketManager, DetectionStatus } from '../utils/websocket.ts';

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
    // WebSocketマネージャーを初期化
    websocketManager.initialize();
    
    // 接続エラーのハンドリング
    const errorUnsubscribe = websocketManager.onError(() => {
      toast({
        title: '接続エラー',
        description: 'サーバーとの接続に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    });

    // ステータス更新のハンドリング
    const statusUnsubscribe = websocketManager.onStatusUpdate((newStatus) => {
      if (newStatus) {
        setStatus(newStatus);
      }
    });

    // クリーンアップ関数
    return () => {
      errorUnsubscribe();
      statusUnsubscribe();
    };
  }, [toast]);

  useEffect(() => {
    if (videoRef.current) {
      // MJPEGストリームのエンドポイントを直接srcに設定
      // キャッシュ無効化のタイムスタンプは不要
      videoRef.current.src = 'http://localhost:8000/api/video_feed';
    }
  }, []); // マウント時に一度だけ実行

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
      console.error('エラー:', error);
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