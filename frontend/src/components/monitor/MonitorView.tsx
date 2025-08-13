import {
  Box,
  VStack,
  Text,
  HStack,
  Badge,
  IconButton,
  useToast,
  Card,
  CardHeader,
  CardBody,
  Heading,
  SimpleGrid,
  Button,
  Tooltip,
  Icon,
  Spinner,
  useColorModeValue,
  Container,
  Flex,
  Avatar,
  Stat,
  StatLabel,
  StatNumber,
  Divider
} from '@chakra-ui/react';
import { useEffect, useRef, useState, useCallback } from 'react';
import { FaExpand, FaCompress, FaEye, FaVideo, FaWifi } from 'react-icons/fa';
import {
  FiCamera,
  FiRefreshCw,
  FiMaximize,
  FiMinimize,
  FiActivity,
  FiSmartphone,
  FiUser,
  FiMonitor,
  FiZap,
  FiAlertTriangle,
  FiCheckCircle,
  FiXCircle
} from 'react-icons/fi';
import { websocketManager, DetectionStatus } from '../../utils/websocket';
import { logger } from '../../utils/logger';

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
  const [lastUpdateAt, setLastUpdateAt] = useState<number | null>(null);
  const [isVideoLoading, setIsVideoLoading] = useState(true);
  const [fitMode, setFitMode] = useState<'contain' | 'cover'>('contain');
  const cardBg = useColorModeValue('white', 'gray.800');

  // 現在のstatusを参照するためのRef（クロージャー問題解決）
  const statusRef = useRef(status);
  statusRef.current = status;

  // 初期化フラグ（初回の状態更新を除外するため）
  const isInitializedRef = useRef(false);

  // 状態変化のデバウンシング用のRef
  const lastStableStatusRef = useRef<DetectionStatus | null>(null);
  const statusStabilityCounterRef = useRef({ person: 0, smartphone: 0 });
  const lastLogTimeRef = useRef({ person: 0, smartphone: 0 });

  // デバウンシング設定
  const STABILITY_THRESHOLD = 2; // 応答性向上のため緩和
  const MIN_LOG_INTERVAL = 2500; // ログ負荷をわずかに抑制

  // 状態の安定性チェック関数
  const isStatusStable = useCallback((newStatus: DetectionStatus, previousStatus: DetectionStatus): { person: boolean; smartphone: boolean } => {
    const personChanged = newStatus.personDetected !== previousStatus.personDetected;
    const smartphoneChanged = newStatus.smartphoneDetected !== previousStatus.smartphoneDetected;

    // 変化がある場合はカウンターをリセット
    if (personChanged) {
      statusStabilityCounterRef.current.person = 1;
    } else {
      statusStabilityCounterRef.current.person += 1;
    }

    if (smartphoneChanged) {
      statusStabilityCounterRef.current.smartphone = 1;
    } else {
      statusStabilityCounterRef.current.smartphone += 1;
    }

    return {
      person: statusStabilityCounterRef.current.person >= STABILITY_THRESHOLD,
      smartphone: statusStabilityCounterRef.current.smartphone >= STABILITY_THRESHOLD
    };
  }, []);

  // ログ出力のレート制限チェック
  const shouldLogChange = useCallback((type: 'person' | 'smartphone'): boolean => {
    const now = Date.now();
    const lastLogTime = lastLogTimeRef.current[type];

    if (now - lastLogTime >= MIN_LOG_INTERVAL) {
      lastLogTimeRef.current[type] = now;
      return true;
    }

    return false;
  }, []);

  // ステータス更新ハンドラー（デバウンシング対応）
  const handleStatusUpdate = useCallback(async (newStatus?: DetectionStatus) => {
    if (!newStatus) return;

    const previousStatus = statusRef.current;

    // 初回の状態更新の場合は、変化ログを出力せずに状態のみ更新
    if (!isInitializedRef.current) {
      await logger.info('MonitorView: 初期状態設定',
        {
          component: 'MonitorView',
          action: 'initial_status_set',
          initialState: {
            personDetected: newStatus.personDetected,
            smartphoneDetected: newStatus.smartphoneDetected,
            absenceTime: newStatus.absenceTime,
            smartphoneUseTime: newStatus.smartphoneUseTime
          }
        },
        'MonitorView'
      );

      isInitializedRef.current = true;
      lastStableStatusRef.current = { ...newStatus };
      setStatus(newStatus);
      setLastUpdateAt(Date.now());
      return;
    }

    // 安定性チェック
    const stability = isStatusStable(newStatus, previousStatus);
    const lastStableStatus = lastStableStatusRef.current;

    // 在席状態の変化ログ（安定してからログ出力）
    if (lastStableStatus && newStatus.personDetected !== lastStableStatus.personDetected && stability.person && shouldLogChange('person')) {
      await logger.info(`MonitorView: 在席状態変化 ${lastStableStatus.personDetected ? '在席' : '不在'} → ${newStatus.personDetected ? '在席' : '不在'}`,
        {
          component: 'MonitorView',
          action: 'person_detection_change',
          previousState: lastStableStatus.personDetected,
          newState: newStatus.personDetected,
          absenceTime: newStatus.absenceTime,
          stabilityCounter: statusStabilityCounterRef.current.person
        },
        'MonitorView'
      );

      // 安定した状態を記録
      lastStableStatusRef.current = {
        ...lastStableStatusRef.current,
        personDetected: newStatus.personDetected,
        smartphoneDetected: lastStableStatusRef.current?.smartphoneDetected ?? newStatus.smartphoneDetected,
        absenceTime: newStatus.absenceTime,
        smartphoneUseTime: newStatus.smartphoneUseTime
      };
    }

    // スマートフォン検知状態の変化ログ（安定してからログ出力）
    if (lastStableStatus && newStatus.smartphoneDetected !== lastStableStatus.smartphoneDetected && stability.smartphone && shouldLogChange('smartphone')) {
      await logger.info(`MonitorView: スマートフォン検知状態変化 ${lastStableStatus.smartphoneDetected ? '使用中' : '未使用'} → ${newStatus.smartphoneDetected ? '使用中' : '未使用'}`,
        {
          component: 'MonitorView',
          action: 'smartphone_detection_change',
          previousState: lastStableStatus.smartphoneDetected,
          newState: newStatus.smartphoneDetected,
          useTime: newStatus.smartphoneUseTime,
          stabilityCounter: statusStabilityCounterRef.current.smartphone
        },
        'MonitorView'
      );

      // 安定した状態を記録
      lastStableStatusRef.current = {
        ...lastStableStatusRef.current,
        personDetected: lastStableStatusRef.current?.personDetected ?? newStatus.personDetected,
        smartphoneDetected: newStatus.smartphoneDetected,
        absenceTime: newStatus.absenceTime,
        smartphoneUseTime: newStatus.smartphoneUseTime
      };
    }

    // 不在時間の閾値チェック（30秒、60秒でアラート）- レート制限あり
    if (!newStatus.personDetected && (newStatus.absenceTime === 30 || newStatus.absenceTime === 60) && shouldLogChange('person')) {
      await logger.warn(`MonitorView: 長期不在検知 (${newStatus.absenceTime}秒)`,
        {
          component: 'MonitorView',
          action: 'long_absence_alert',
          absenceTime: newStatus.absenceTime
        },
        'MonitorView'
      );
    }

    // UIの状態を更新（リアルタイム）
    setStatus(newStatus);
    setLastUpdateAt(Date.now());
  }, [isStatusStable, shouldLogChange]);

  useEffect(() => {
    // 初期化
    logger.info('MonitorView: コンポーネント初期化開始',
      { component: 'MonitorView', action: 'initialize' },
      'MonitorView'
    );

    // WebSocket 初期化（多重初期化は内部で抑止される）
    websocketManager.initialize();
    logger.info('MonitorView: WebSocket初期化完了',
      { component: 'MonitorView', action: 'websocket_init' },
      'MonitorView'
    );

    // イベント購読
    const errorUnsubscribe = websocketManager.onError(async () => {
      await logger.error('MonitorView: WebSocket接続エラー',
        { component: 'MonitorView', action: 'websocket_error' },
        'MonitorView'
      );

      toast({
        title: '接続エラー',
        description: 'サーバーとの接続に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    });

    const statusUnsubscribe = websocketManager.onStatusUpdate(handleStatusUpdate);

    // クリーンアップ（StrictModeの二重マウントでも多重購読を確実に解除）
    return () => {
      errorUnsubscribe();
      statusUnsubscribe();
      isInitializedRef.current = false;
      logger.info('MonitorView: コンポーネントクリーンアップ',
        { component: 'MonitorView', action: 'cleanup' },
        'MonitorView'
      );
    };
  }, [handleStatusUpdate, toast]);

  useEffect(() => {
    const setupVideoStream = async () => {
      try {
        if (videoRef.current) {
          // MJPEGストリームのエンドポイントを直接srcに設定
          const videoUrl = '/api/v1/video_feed';
          setIsVideoLoading(true);
          videoRef.current.src = `${videoUrl}?t=${Date.now()}`; // キャッシュバスター

          await logger.info('MonitorView: ビデオストリーム設定完了',
            {
              component: 'MonitorView',
              action: 'video_stream_setup',
              videoUrl
            },
            'MonitorView'
          );

          // ビデオエラーイベントのハンドリング
          videoRef.current.onerror = async () => {
            await logger.error('MonitorView: ビデオストリームエラー',
              {
                component: 'MonitorView',
                action: 'video_stream_error',
                videoUrl
              },
              'MonitorView'
            );
            setIsVideoLoading(false);
          };

          // ビデオ読み込み完了イベント
          videoRef.current.onload = async () => {
            await logger.debug('MonitorView: ビデオストリーム読み込み完了',
              {
                component: 'MonitorView',
                action: 'video_stream_loaded',
                videoUrl
              },
              'MonitorView'
            );
            setIsVideoLoading(false);
          };
        }
      } catch (error) {
        await logger.error('MonitorView: ビデオストリーム設定エラー',
          {
            component: 'MonitorView',
            action: 'video_setup_error',
            error: error instanceof Error ? error.message : String(error)
          },
          'MonitorView'
        );
      }
    };

    void setupVideoStream();
  }, []); // マウント時に一度だけ実行

  const reconnectStream = async () => {
    try {
      if (!videoRef.current) return;
      const baseUrl = '/api/v1/video_feed';
      setIsVideoLoading(true);
      videoRef.current.src = `${baseUrl}?t=${Date.now()}`;
      await logger.info('MonitorView: ストリーム再接続', { component: 'MonitorView', action: 'stream_reconnect' }, 'MonitorView');
      toast({ title: 'ストリーム再接続', status: 'info', duration: 1500, isClosable: true });
    } catch (error) {
      await logger.error('MonitorView: ストリーム再接続エラー', { component: 'MonitorView', action: 'reconnect_error', error: error instanceof Error ? error.message : String(error) }, 'MonitorView');
      toast({ title: 'エラー', description: '再接続に失敗しました', status: 'error', duration: 2500, isClosable: true });
    }
  };

  const toggleFitMode = () => {
    setFitMode(prev => (prev === 'contain' ? 'cover' : 'contain'));
  };

  const captureSnapshot = async () => {
    try {
      if (!videoRef.current) return;
      const img = videoRef.current;
      const width = img.naturalWidth || img.width;
      const height = img.naturalHeight || img.height;
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.drawImage(img, 0, 0, width, height);
      const dataUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      const time = new Date();
      const pad = (n: number) => String(n).padStart(2, '0');
      const fileName = `snapshot_${time.getFullYear()}${pad(time.getMonth() + 1)}${pad(time.getDate())}_${pad(time.getHours())}${pad(time.getMinutes())}${pad(time.getSeconds())}.png`;
      link.href = dataUrl;
      link.download = fileName;
      link.click();
      toast({ title: 'スクリーンショットを保存しました', status: 'success', duration: 1500, isClosable: true });
      await logger.info('MonitorView: スクリーンショット保存', { component: 'MonitorView', action: 'snapshot_saved', fileName }, 'MonitorView');
    } catch (error) {
      await logger.error('MonitorView: スクリーンショット失敗', { component: 'MonitorView', action: 'snapshot_error', error: error instanceof Error ? error.message : String(error) }, 'MonitorView');
      toast({ title: 'エラー', description: 'スクリーンショットに失敗しました', status: 'error', duration: 2500, isClosable: true });
    }
  };

  const formatSeconds = (sec: number) => {
    const minutes = Math.floor(sec / 60);
    const seconds = Math.floor(sec % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await containerRef.current?.requestFullscreen();
        setIsFullscreen(true);

        await logger.info('MonitorView: 全画面モード開始',
          { component: 'MonitorView', action: 'fullscreen_enter' },
          'MonitorView'
        );
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);

        await logger.info('MonitorView: 全画面モード終了',
          { component: 'MonitorView', action: 'fullscreen_exit' },
          'MonitorView'
        );
      }
    } catch (error) {
      await logger.error('MonitorView: 全画面表示切り替えエラー',
        {
          component: 'MonitorView',
          action: 'fullscreen_toggle_error',
          error: error instanceof Error ? error.message : String(error)
        },
        'MonitorView'
      );

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

  const now = Date.now();
  const liveDelta = lastUpdateAt ? now - lastUpdateAt : Infinity;
  const liveColor = liveDelta === Infinity ? 'gray' : liveDelta < 5000 ? 'green' : liveDelta < 15000 ? 'yellow' : 'red';

  const gradientBg = useColorModeValue(
    'linear(to-r, blue.50, green.50)',
    'linear(to-r, blue.900, green.900)'
  );

  const getConnectionStatus = () => {
    if (liveDelta === Infinity) return { color: 'gray', label: '未接続', icon: FiXCircle };
    if (liveDelta < 5000) return { color: 'green', label: '安定', icon: FiCheckCircle };
    if (liveDelta < 15000) return { color: 'yellow', label: '遅延', icon: FiAlertTriangle };
    return { color: 'red', label: '切断', icon: FiXCircle };
  };

  const connectionStatus = getConnectionStatus();

  return (
    <Container maxW="1400px" px={{ base: 4, md: 6 }}>
      <VStack spacing={8} align="stretch">
        {/* ヘッダーセクション */}
        <Box
          bgGradient={gradientBg}
          borderRadius="xl"
          border="1px solid"
          borderColor={useColorModeValue('gray.200', 'gray.600')}
          p={6}
          shadow="lg"
        >
          <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
            <VStack align="start" spacing={3}>
              <HStack spacing={4}>
                <Avatar
                  icon={<Icon as={FaEye} />}
                  bg="blue.500"
                  size="lg"
                />
                <VStack align="start" spacing={1}>
                  <Heading size="xl" color="gray.700" _dark={{ color: 'gray.100' }}>
                    リアルタイム監視システム
                  </Heading>
                  <Text fontSize="md" color="gray.600" _dark={{ color: 'gray.300' }}>
                    AI による行動パターン検知と分析
                  </Text>
                </VStack>
              </HStack>

              {/* ステータスバッジ */}
              <HStack spacing={4} wrap="wrap">
                <Badge
                  colorScheme={status.personDetected ? 'green' : 'red'}
                  px={3}
                  py={1}
                  borderRadius="full"
                  fontSize="sm"
                >
                  <HStack spacing={1}>
                    <Icon as={status.personDetected ? FiCheckCircle : FiXCircle} boxSize={3} />
                    <Text>{status.personDetected ? '在席中' : '不在'}</Text>
                  </HStack>
                </Badge>
                <Badge
                  colorScheme={status.smartphoneDetected ? 'orange' : 'green'}
                  px={3}
                  py={1}
                  borderRadius="full"
                  fontSize="sm"
                >
                  <HStack spacing={1}>
                    <Icon as={FiSmartphone} boxSize={3} />
                    <Text>{status.smartphoneDetected ? 'スマホ使用中' : 'スマホ未使用'}</Text>
                  </HStack>
                </Badge>
                <Badge
                  colorScheme={connectionStatus.color}
                  px={3}
                  py={1}
                  borderRadius="full"
                  fontSize="sm"
                >
                  <HStack spacing={1}>
                    <Icon as={connectionStatus.icon} boxSize={3} />
                    <Text>接続{connectionStatus.label}</Text>
                  </HStack>
                </Badge>
              </HStack>
            </VStack>

            {/* 統計情報 */}
            <VStack spacing={3} align="end">
              <HStack spacing={6}>
                <Stat textAlign="center">
                  <StatLabel fontSize="xs">不在時間</StatLabel>
                  <StatNumber fontSize="lg" color="red.500">
                    {formatSeconds(status.absenceTime)}
                  </StatNumber>
                </Stat>
                <Stat textAlign="center">
                  <StatLabel fontSize="xs">スマホ使用</StatLabel>
                  <StatNumber fontSize="lg" color="orange.500">
                    {formatSeconds(status.smartphoneUseTime)}
                  </StatNumber>
                </Stat>
              </HStack>
              <Text fontSize="xs" color="gray.500">
                最終更新: {lastUpdateAt ? new Date(lastUpdateAt).toLocaleTimeString() : '未取得'}
              </Text>
            </VStack>
          </Flex>
        </Box>

        {/* メインコンテンツ */}
        <SimpleGrid columns={{ base: 1, xl: 3 }} spacing={8} alignItems="stretch">
          {/* ビデオフィード（2カラム分） */}
          <Box gridColumn={{ base: 1, xl: "1 / 3" }}>
            <Card
              ref={containerRef}
              bg="black"
              overflow="hidden"
              height={isFullscreen ? '100vh' : { base: '400px', md: '500px', lg: '600px' }}
              shadow="xl"
              border="2px solid"
              borderColor={useColorModeValue('gray.300', 'gray.600')}
            >
              <CardHeader bg="rgba(0,0,0,0.8)" backdropFilter="blur(10px)">
                <HStack justify="space-between" color="white">
                  <HStack spacing={3}>
                    <Icon as={FaVideo} color="blue.400" boxSize={5} />
                    <Heading size="md">ライブフィード</Heading>
                    <Badge
                      colorScheme={liveColor}
                      variant="solid"
                      px={3}
                      py={1}
                      borderRadius="full"
                    >
                      {liveDelta === Infinity ? 'OFFLINE' : 'LIVE'}
                    </Badge>
                  </HStack>

                  <HStack spacing={3}>
                    <Text fontSize="sm" color="gray.300">
                      {fitMode === 'contain' ? 'フィット表示' : 'フル表示'}
                    </Text>
                    <Text fontSize="xs" color="gray.400">
                      {lastUpdateAt ? new Date(lastUpdateAt).toLocaleTimeString() : '未接続'}
                    </Text>
                  </HStack>
                </HStack>
              </CardHeader>

              <CardBody position="relative" p={0}>
                {/* ビデオストリーム */}
                <img
                  ref={videoRef}
                  alt="Monitor Feed"
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: fitMode,
                    backgroundColor: '#000'
                  }}
                />

                {/* ローディングオーバーレイ */}
                {isVideoLoading && (
                  <Flex
                    position="absolute"
                    top={0}
                    left={0}
                    right={0}
                    bottom={0}
                    justify="center"
                    align="center"
                    bg="rgba(0,0,0,0.7)"
                    backdropFilter="blur(5px)"
                  >
                    <VStack spacing={4}>
                      <Spinner size="xl" color="blue.400" thickness="4px" />
                      <Text color="white" fontSize="lg" fontWeight="medium">
                        ビデオストリーム読み込み中...
                      </Text>
                    </VStack>
                  </Flex>
                )}

                {/* 検知状態オーバーレイ */}
                <Box
                  position="absolute"
                  top={4}
                  left={4}
                  bg="rgba(0,0,0,0.8)"
                  borderRadius="lg"
                  p={3}
                  backdropFilter="blur(10px)"
                >
                  <VStack spacing={2} align="start">
                    <HStack spacing={2}>
                      <Icon
                        as={status.personDetected ? FiCheckCircle : FiXCircle}
                        color={status.personDetected ? 'green.400' : 'red.400'}
                        boxSize={4}
                      />
                      <Text color="white" fontSize="sm" fontWeight="medium">
                        {status.personDetected ? '人物検知' : '人物未検知'}
                      </Text>
                    </HStack>
                    <HStack spacing={2}>
                      <Icon
                        as={FiSmartphone}
                        color={status.smartphoneDetected ? 'orange.400' : 'green.400'}
                        boxSize={4}
                      />
                      <Text color="white" fontSize="sm" fontWeight="medium">
                        {status.smartphoneDetected ? 'スマホ検知' : 'スマホ未検知'}
                      </Text>
                    </HStack>
                  </VStack>
                </Box>

                {/* コントロールパネル */}
                <HStack
                  position="absolute"
                  bottom={4}
                  left={4}
                  spacing={2}
                  bg="rgba(0,0,0,0.8)"
                  borderRadius="lg"
                  p={2}
                  backdropFilter="blur(10px)"
                >
                  <Tooltip label="スクリーンショット撮影">
                    <IconButton
                      aria-label="screenshot"
                      icon={<FiCamera />}
                      onClick={captureSnapshot}
                      colorScheme="blue"
                      variant="solid"
                      size="sm"
                    />
                  </Tooltip>
                  <Tooltip label="ストリーム再接続">
                    <IconButton
                      aria-label="reconnect"
                      icon={<FiRefreshCw />}
                      onClick={reconnectStream}
                      colorScheme="green"
                      variant="solid"
                      size="sm"
                    />
                  </Tooltip>
                  <Tooltip label={fitMode === 'contain' ? 'フル表示に切り替え' : 'フィット表示に切り替え'}>
                    <IconButton
                      aria-label="fitmode"
                      icon={fitMode === 'contain' ? <FiMaximize /> : <FiMinimize />}
                      onClick={toggleFitMode}
                      colorScheme="purple"
                      variant="solid"
                      size="sm"
                    />
                  </Tooltip>
                </HStack>

                {/* フルスクリーンボタン */}
                <Tooltip label={isFullscreen ? '全画面終了' : '全画面表示'}>
                  <IconButton
                    aria-label="fullscreen"
                    icon={isFullscreen ? <FaCompress /> : <FaExpand />}
                    position="absolute"
                    bottom={4}
                    right={4}
                    colorScheme="orange"
                    variant="solid"
                    onClick={toggleFullscreen}
                    bg="rgba(0,0,0,0.8)"
                    backdropFilter="blur(10px)"
                    _hover={{ bg: 'orange.500' }}
                  />
                </Tooltip>
              </CardBody>
            </Card>
          </Box>

          {/* 右サイドパネル */}
          <VStack spacing={6} align="stretch">
            {/* 現在の状態 */}
            <Card bg={cardBg} shadow="lg">
              <CardHeader pb={2}>
                <HStack spacing={3}>
                  <Icon as={FiActivity} color="green.500" boxSize={5} />
                  <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                    検知状態
                  </Heading>
                </HStack>
              </CardHeader>
              <CardBody pt={2}>
                <VStack spacing={4} align="stretch">
                  {/* 人物検知 */}
                  <Box
                    p={4}
                    borderRadius="lg"
                    bg={status.personDetected
                      ? useColorModeValue('green.50', 'green.900')
                      : useColorModeValue('red.50', 'red.900')
                    }
                    border="1px solid"
                    borderColor={status.personDetected
                      ? useColorModeValue('green.200', 'green.700')
                      : useColorModeValue('red.200', 'red.700')
                    }
                  >
                    <HStack justify="space-between" align="center">
                      <HStack spacing={3}>
                        <Avatar
                          icon={<Icon as={FiUser} />}
                          bg={status.personDetected ? 'green.500' : 'red.500'}
                          size="sm"
                        />
                        <VStack align="start" spacing={0}>
                          <Text fontWeight="semibold" fontSize="sm">
                            人物検知
                          </Text>
                          <Text fontSize="xs" color="gray.500">
                            不在時間: {formatSeconds(status.absenceTime)}
                          </Text>
                        </VStack>
                      </HStack>
                      <Badge
                        colorScheme={status.personDetected ? 'green' : 'red'}
                        variant="solid"
                        px={3}
                        py={1}
                        borderRadius="full"
                      >
                        {status.personDetected ? '在席' : '不在'}
                      </Badge>
                    </HStack>
                  </Box>

                  {/* スマートフォン検知 */}
                  <Box
                    p={4}
                    borderRadius="lg"
                    bg={status.smartphoneDetected
                      ? useColorModeValue('orange.50', 'orange.900')
                      : useColorModeValue('green.50', 'green.900')
                    }
                    border="1px solid"
                    borderColor={status.smartphoneDetected
                      ? useColorModeValue('orange.200', 'orange.700')
                      : useColorModeValue('green.200', 'green.700')
                    }
                  >
                    <HStack justify="space-between" align="center">
                      <HStack spacing={3}>
                        <Avatar
                          icon={<Icon as={FiSmartphone} />}
                          bg={status.smartphoneDetected ? 'orange.500' : 'green.500'}
                          size="sm"
                        />
                        <VStack align="start" spacing={0}>
                          <Text fontWeight="semibold" fontSize="sm">
                            スマートフォン
                          </Text>
                          <Text fontSize="xs" color="gray.500">
                            使用時間: {formatSeconds(status.smartphoneUseTime)}
                          </Text>
                        </VStack>
                      </HStack>
                      <Badge
                        colorScheme={status.smartphoneDetected ? 'orange' : 'green'}
                        variant="solid"
                        px={3}
                        py={1}
                        borderRadius="full"
                      >
                        {status.smartphoneDetected ? '使用中' : '未使用'}
                      </Badge>
                    </HStack>
                  </Box>

                  {/* 接続状態 */}
                  <Box
                    p={4}
                    borderRadius="lg"
                    bg={useColorModeValue(`${connectionStatus.color}.50`, `${connectionStatus.color}.900`)}
                    border="1px solid"
                    borderColor={useColorModeValue(`${connectionStatus.color}.200`, `${connectionStatus.color}.700`)}
                  >
                    <HStack justify="space-between" align="center">
                      <HStack spacing={3}>
                        <Avatar
                          icon={<Icon as={FaWifi} />}
                          bg={`${connectionStatus.color}.500`}
                          size="sm"
                        />
                        <VStack align="start" spacing={0}>
                          <Text fontWeight="semibold" fontSize="sm">
                            接続状態
                          </Text>
                          <Text fontSize="xs" color="gray.500">
                            最終更新: {lastUpdateAt ? new Date(lastUpdateAt).toLocaleTimeString() : '未取得'}
                          </Text>
                        </VStack>
                      </HStack>
                      <Badge
                        colorScheme={connectionStatus.color}
                        variant="solid"
                        px={3}
                        py={1}
                        borderRadius="full"
                      >
                        {connectionStatus.label}
                      </Badge>
                    </HStack>
                  </Box>
                </VStack>
              </CardBody>
            </Card>

            {/* クイックアクション */}
            <Card bg={cardBg} shadow="lg">
              <CardHeader pb={2}>
                <HStack spacing={3}>
                  <Icon as={FiZap} color="blue.500" boxSize={5} />
                  <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                    クイックアクション
                  </Heading>
                </HStack>
              </CardHeader>
              <CardBody pt={2}>
                <VStack spacing={3} align="stretch">
                  <Button
                    leftIcon={<FiCamera />}
                    onClick={captureSnapshot}
                    colorScheme="blue"
                    variant="outline"
                    justifyContent="flex-start"
                    borderRadius="lg"
                  >
                    スクリーンショット撮影
                  </Button>
                  <Button
                    leftIcon={<FiRefreshCw />}
                    onClick={reconnectStream}
                    colorScheme="green"
                    variant="outline"
                    justifyContent="flex-start"
                    borderRadius="lg"
                  >
                    ストリーム再接続
                  </Button>
                  <Button
                    leftIcon={fitMode === 'contain' ? <FiMaximize /> : <FiMinimize />}
                    onClick={toggleFitMode}
                    colorScheme="purple"
                    variant="outline"
                    justifyContent="flex-start"
                    borderRadius="lg"
                  >
                    {fitMode === 'contain' ? 'フル表示' : 'フィット表示'}
                  </Button>
                  <Button
                    leftIcon={isFullscreen ? <FaCompress /> : <FaExpand />}
                    onClick={toggleFullscreen}
                    colorScheme="orange"
                    variant="outline"
                    justifyContent="flex-start"
                    borderRadius="lg"
                  >
                    {isFullscreen ? '全画面終了' : '全画面表示'}
                  </Button>
                </VStack>
              </CardBody>
            </Card>

            {/* システム情報 */}
            <Card bg={cardBg} shadow="lg">
              <CardHeader pb={2}>
                <HStack spacing={3}>
                  <Icon as={FiMonitor} color="gray.500" boxSize={5} />
                  <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                    システム情報
                  </Heading>
                </HStack>
              </CardHeader>
              <CardBody pt={2}>
                <VStack spacing={3} align="stretch">
                  <HStack justify="space-between">
                    <Text fontSize="sm" color="gray.600">表示モード</Text>
                    <Badge variant="outline">
                      {fitMode === 'contain' ? 'フィット' : 'フル'}
                    </Badge>
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm" color="gray.600">画面状態</Text>
                    <Badge variant="outline">
                      {isFullscreen ? '全画面' : '通常'}
                    </Badge>
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm" color="gray.600">ストリーム</Text>
                    <Badge colorScheme={isVideoLoading ? 'yellow' : 'green'} variant="outline">
                      {isVideoLoading ? '読み込み中' : 'アクティブ'}
                    </Badge>
                  </HStack>
                  <Divider />
                  <Text fontSize="xs" color="gray.500" textAlign="center">
                    AI監視システム v2.0
                  </Text>
                </VStack>
              </CardBody>
            </Card>
          </VStack>
        </SimpleGrid>
      </VStack>
    </Container>
  );
}; 