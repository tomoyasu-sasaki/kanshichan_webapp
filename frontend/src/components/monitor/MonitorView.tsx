import { Box, VStack, SimpleGrid, useToast, Container } from '@chakra-ui/react';
import { useEffect, useRef, useState, useCallback } from 'react';
import { websocketManager, DetectionStatus } from '../../utils/websocket';
import { logger } from '../../utils/logger';
import { HeaderStats } from './components/HeaderStats';
import { VideoFeed } from './components/VideoFeed';
import { DetectionOverlay } from './components/DetectionOverlay';
import { StatusPanels } from './components/StatusPanels';
import { QuickActions } from './components/QuickActions';
import { SystemInfo } from './components/SystemInfo';
import { getConnectionStatus, getLiveColor } from './utils/connection';

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

  // 時刻フォーマットは子コンポーネント側で実施

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
  const liveColor = getLiveColor(liveDelta);
  const connectionStatus = getConnectionStatus(liveDelta);

  return (
    <Container maxW="1400px" px={{ base: 4, md: 6 }}>
      <VStack spacing={8} align="stretch">
        <HeaderStats status={status} connectionStatus={connectionStatus} lastUpdateAt={lastUpdateAt} />

        {/* メインコンテンツ */}
        <SimpleGrid columns={{ base: 1, xl: 3 }} spacing={8} alignItems="stretch">
          <Box gridColumn={{ base: 1, xl: "1 / 3" }}>
            <VideoFeed
              containerRef={containerRef}
              videoRef={videoRef}
              fitMode={fitMode}
              isFullscreen={isFullscreen}
              isVideoLoading={isVideoLoading}
              lastUpdateAt={lastUpdateAt}
              liveDelta={liveDelta}
              liveColor={liveColor}
              onCapture={captureSnapshot}
              onReconnect={reconnectStream}
              onToggleFit={toggleFitMode}
              onToggleFullscreen={toggleFullscreen}
              overlay={<DetectionOverlay status={status} />}
            />
          </Box>

          {/* 右サイドパネル */}
          <VStack spacing={6} align="stretch">
            <StatusPanels status={status} connectionStatus={connectionStatus} lastUpdateAt={lastUpdateAt} />
            <QuickActions
              fitMode={fitMode}
              isFullscreen={isFullscreen}
              onCapture={captureSnapshot}
              onReconnect={reconnectStream}
              onToggleFit={toggleFitMode}
              onToggleFullscreen={toggleFullscreen}
            />
            <SystemInfo fitMode={fitMode} isFullscreen={isFullscreen} isVideoLoading={isVideoLoading} />
          </VStack>
        </SimpleGrid>
      </VStack>
    </Container>
  );
}; 