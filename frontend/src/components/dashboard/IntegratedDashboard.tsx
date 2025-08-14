import React, { useState, useEffect, useCallback, Suspense, useRef } from 'react';
import {
  Box,
  Grid,
  GridItem,
  VStack,
  HStack,
  Text,
  Heading,
  Card,
  CardHeader,
  CardBody,
  Button,
  useColorModeValue,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Icon,
  SimpleGrid,
  Container
} from '@chakra-ui/react';
import { FiRefreshCw, FiCpu, FiDatabase } from 'react-icons/fi';
import { FaRobot, FaMicrophone } from 'react-icons/fa';
import { SidebarNav, SystemStatusGrid, OverallHealthCard, OverviewHeader, QuickAccessPanel } from './index';

import { MonitorView } from '../monitor/MonitorView';
const VoiceSettings = React.lazy(() => import('../voice/VoiceSettings').then(m => ({ default: m.VoiceSettings })));
import { SettingsPanel } from '../settings/SettingsPanel';
import { ScheduleView } from '../schedule/ScheduleView';
import { BehaviorInsights } from '../behavior/BehaviorInsights';
import { AdvancedAnalyticsDashboard } from '../extension/AdvancedAnalyticsDashboard';
import { PersonalizationPanel } from '../extension/PersonalizationPanel';
import { PredictiveInsights } from '../extension/PredictiveInsights';
import { LearningProgress } from '../extension/LearningProgress';

interface SystemStatus {
  data_collection: 'active' | 'inactive' | 'error';
  tts_system: 'active' | 'inactive' | 'error';
  integration: 'active' | 'inactive' | 'error';
  ai_analysis: 'active' | 'inactive' | 'error';
  overall_health: number; // 0-1
  last_update: string;
}

interface IntegratedDashboardProps {
  userId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number; // seconds
}

export const IntegratedDashboard: React.FC<IntegratedDashboardProps> = ({
  userId = 'default',
  autoRefresh = true,
  refreshInterval = 30
}) => {
  // State management
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState('overview');
  const [lastRefresh, setLastRefresh] = useState(new Date());
  // 重複リクエスト抑制（StrictModeのダブルマウント対策）
  const statusFetchLockRef = useRef(false);
  const lastStatusFetchAtRef = useRef(0);

  // Settings modal state
  // ダッシュボード専用の設定ダイアログは廃止（UI設定は親や個別画面に委譲）

  // UI theming
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const toast = useToast();

  // 設定ダイアログ廃止に伴い、初期化ロジックは不要

  // Hash navigation sync
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash && ['overview', 'monitor', 'voice', 'behavior', 'analytics', 'personalization', 'predictions', 'learning'].includes(hash)) {
        setSelectedView(hash);
      }
    };

    // Initialize from URL
    handleHashChange();

    // Listen for hash changes
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Update URL when view changes
  const handleViewChange = useCallback((view: string) => {
    console.log('handleViewChange called with view:', view);
    setSelectedView(view);
    window.location.hash = view;
    console.log('URL hash set to:', view);
  }, []);

  // System status fetch
  const fetchSystemStatus = useCallback(async () => {
    // 短時間の二重実行を抑止（500ms以内/実行中はスキップ）
    const now = Date.now();
    if (statusFetchLockRef.current) return;
    if (now - lastStatusFetchAtRef.current < 500) return;
    statusFetchLockRef.current = true;
    try {
      setIsLoading(true);
      setError(null);

      // Parallel API calls for comprehensive status
      const [monitorStatus, ttsStatus, analysisStatus] = await Promise.allSettled([
        fetch('/api/v1/monitor/status'),
        fetch('/api/v1/tts/status'),
        fetch('/api/v1/analysis/status')
      ]);

      console.log('API Status Results:', {
        monitor: monitorStatus,
        tts: ttsStatus,
        analysis: analysisStatus
      });

      // Process responses with better error handling
      const statusData: SystemStatus = {
        data_collection: 'inactive',
        tts_system: 'inactive',
        integration: 'active', // Integration layer is current component
        ai_analysis: 'inactive',
        overall_health: 0.25, // Start with low baseline
        last_update: new Date().toISOString()
      };

      // Monitor status
      if (monitorStatus.status === 'fulfilled') {
        try {
          if (monitorStatus.value.ok) {
            const monitorData = await monitorStatus.value.json();
            console.log('Monitor API Response:', monitorData);
            statusData.data_collection = 'active';
          } else {
            console.warn('Monitor API returned error:', monitorStatus.value.status);
          }
        } catch (err) {
          console.error('Error parsing monitor response:', err);
        }
      } else {
        console.error('Monitor API call failed:', monitorStatus.reason);
      }

      // TTS status
      if (ttsStatus.status === 'fulfilled') {
        try {
          if (ttsStatus.value.ok) {
            const ttsData = await ttsStatus.value.json();
            console.log('TTS API Response:', ttsData);
            statusData.tts_system = 'active';
          } else {
            console.warn('TTS API returned error:', ttsStatus.value.status);
          }
        } catch (err) {
          console.error('Error parsing TTS response:', err);
        }
      } else {
        console.error('TTS API call failed:', ttsStatus.reason);
      }

      // Analysis status
      if (analysisStatus.status === 'fulfilled') {
        try {
          if (analysisStatus.value.ok) {
            const analysisData = await analysisStatus.value.json();
            console.log('Analysis API Response:', analysisData);
            statusData.ai_analysis = 'active';
          } else {
            console.warn('Analysis API returned error:', analysisStatus.value.status);
          }
        } catch (err) {
          console.error('Error parsing analysis response:', err);
        }
      } else {
        console.error('Analysis API call failed:', analysisStatus.reason);
      }

      // Calculate overall health（対象フェーズのみで算出）
      const activePhases =
        (statusData.data_collection === 'active' ? 1 : 0) +
        (statusData.tts_system === 'active' ? 1 : 0) +
        (statusData.integration === 'active' ? 1 : 0) +
        (statusData.ai_analysis === 'active' ? 1 : 0);
      statusData.overall_health = activePhases / 4;

      console.log('Final status data:', statusData);
      setSystemStatus(statusData);
      setLastRefresh(new Date());

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'システム状態取得エラー';
      console.error('fetchSystemStatus error:', errorMessage, err);
      setError(errorMessage);
      toast({
        title: 'システム状態エラー',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
      lastStatusFetchAtRef.current = Date.now();
      statusFetchLockRef.current = false;
    }
  }, [toast]);

  // Auto-refresh functionality（ステータス取得は「概要」ビューでのみ実行）
  useEffect(() => {
    if (selectedView !== 'overview') {
      return undefined;
    }

    fetchSystemStatus();

    if (autoRefresh) {
      const interval = setInterval(fetchSystemStatus, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
    return undefined;
  }, [fetchSystemStatus, autoRefresh, refreshInterval, selectedView]);

  // 分割したプレゼンテーションコンポーネントを使用

  // Render main content based on selected view
  const renderMainContent = () => {
    switch (selectedView) {
      case 'monitor':
        return <MonitorView />;
      case 'voice':
        return (
          <Suspense fallback={<Spinner size="lg" />}>
            <VoiceSettings />
          </Suspense>
        );
      case 'settings':
        return <SettingsPanel />;
      case 'schedule':
        return <ScheduleView />;
      case 'behavior':
        return <BehaviorInsights onNavigate={handleViewChange} />;
      case 'analytics':
        return <AdvancedAnalyticsDashboard userId={userId} />;
      case 'personalization':
        return <PersonalizationPanel userId={userId} />;
      case 'predictions':
        return <PredictiveInsights userId={userId} />;
      case 'learning':
        return <LearningProgress userId={userId} />;
      default:
        return (
          <Container maxW="1400px" px={0}>
            <VStack spacing={8} align="stretch">
              <OverviewHeader lastRefresh={lastRefresh} onNavigate={handleViewChange} />

              {/* システム状態カード */}
              <Card bg={cardBg} shadow="lg">
                <CardHeader pb={2}>
                  <HStack justify="space-between" align="center">
                    <HStack spacing={3}>
                      <Icon as={FiCpu} color="blue.500" boxSize={6} />
                      <VStack align="start" spacing={0}>
                        <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                          システムコンポーネント状態
                        </Heading>
                        <Text fontSize="sm" color="gray.500">
                          各サブシステムの稼働状況
                        </Text>
                      </VStack>
                    </HStack>
                    <Button
                      leftIcon={<Icon as={FiRefreshCw} />}
                      onClick={fetchSystemStatus}
                      isLoading={isLoading}
                      size="sm"
                      variant="outline"
                      borderRadius="lg"
                    >
                      更新
                    </Button>
                  </HStack>
                </CardHeader>
                <CardBody pt={2}>
                  {systemStatus && (
                    <SystemStatusGrid
                      items={[
                        { key: 'data_collection', title: 'データ収集', description: 'リアルタイム監視', icon: FiDatabase, color: 'blue.500', status: systemStatus.data_collection },
                        { key: 'tts_system', title: 'TTS音声', description: '音声合成エンジン', icon: FaMicrophone, color: 'purple.500', status: systemStatus.tts_system },
                        { key: 'integration', title: '統合システム', description: 'コンポーネント連携', icon: FiCpu, color: 'green.500', status: systemStatus.integration },
                        { key: 'ai_analysis', title: 'AI分析', description: '行動パターン解析', icon: FaRobot, color: 'orange.500', status: systemStatus.ai_analysis }
                      ]}
                    />
                  )}
                </CardBody>
              </Card>

              {/* 下段: 健康度とクイックアクセス */}
              <SimpleGrid columns={{ base: 1, xl: 2 }} spacing={8} alignItems="stretch">
                {systemStatus && (
                  <OverallHealthCard overall={systemStatus.overall_health} lastRefresh={lastRefresh} />
                )}

                <QuickAccessPanel onNavigate={handleViewChange} />
              </SimpleGrid>
            </VStack>
          </Container>
        );
    }
  };

  // 設定ダイアログは削除済みのため、保存ハンドラは不要

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        <AlertTitle>システムエラー</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <Box bg={bgColor} minH="100vh">
      <Grid templateColumns="250px 1fr" gap={6}>
        {/* Sidebar Navigation */}
        <GridItem>
          <SidebarNav selectedView={selectedView} onChange={handleViewChange} />
        </GridItem>

        {/* Main Content Area */}
        <GridItem>
          <Box p={6} maxW="1200px" mx="auto">
            {isLoading && (
              <HStack justify="center" py={8}>
                <Spinner size="lg" />
                <Text>システム状態を確認中...</Text>
              </HStack>
            )}

            {!isLoading && renderMainContent()}
          </Box>
        </GridItem>
      </Grid>

      {/* 設定ダイアログは廃止 */}
    </Box>
  );
}; 