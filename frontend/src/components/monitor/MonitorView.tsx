import { Box, VStack, Text, HStack, Badge, IconButton, useToast } from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';
import { useEffect, useRef, useState, useCallback } from 'react';
import { FaExpand, FaCompress } from 'react-icons/fa';
import { websocketManager, DetectionStatus } from '../../utils/websocket';
import { logger } from '../../utils/logger';

export const MonitorView = () => {
  const { t } = useTranslation();
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
          videoRef.current.src = videoUrl;
          
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
            <Text>{t('monitor.labels.presence')}:</Text>
            <Badge colorScheme={status.personDetected ? 'green' : 'red'}>
              {status.personDetected ? t('monitor.status.present') : t('monitor.status.absent')}
            </Badge>
          </HStack>
          {!status.personDetected && (
            <Text>{t('monitor.labels.absence_time')}: {Math.floor(status.absenceTime)}秒</Text>
          )}
          <HStack>
            <Text>{t('monitor.labels.smartphone')}:</Text>
            <Badge colorScheme={status.smartphoneDetected ? 'red' : 'green'}>
              {status.smartphoneDetected ? t('common.yes') : t('common.no')}
            </Badge>
          </HStack>
          {status.smartphoneDetected && (
            <Text>{t('monitor.labels.use_time')}: {Math.floor(status.smartphoneUseTime)}秒</Text>
          )}
        </VStack>
      </Box>

      {/* 全画面表示ボタン */}
      <IconButton
        aria-label={isFullscreen ? t('monitor.fullscreen.exit') : t('monitor.fullscreen.enter')}
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