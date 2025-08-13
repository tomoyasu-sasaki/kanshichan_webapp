import React, { useState, useEffect, useCallback, Suspense, useRef } from 'react';
import {
  Box,
  Grid,
  GridItem,
  VStack,
  HStack,
  Text,
  Heading,
  Badge,
  Card,
  CardHeader,
  CardBody,
  Button,
  Select,
  Switch,
  FormControl,
  FormLabel,
  Progress,
  Divider,
  useColorModeValue,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Icon,
  SimpleGrid,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure
} from '@chakra-ui/react';
import { 
  FiHome, FiVolumeX, FiActivity, FiTarget, FiRefreshCw,
  FiSettings, FiTrendingUp, FiCalendar
} from 'react-icons/fi';
import { useTranslation } from 'react-i18next';
import { LanguageSwitcher } from '../LanguageSwitcher';

import { MonitorView } from '../monitor/MonitorView';
const VoiceSettings = React.lazy(() => import('../voice/VoiceSettings').then(m => ({ default: m.VoiceSettings })));
import { SettingsPanel } from '../settings/SettingsPanel';
import { ScheduleView } from '../schedule/ScheduleView';
import { BehaviorInsights } from '../behavior/BehaviorInsights';
import { AdvancedAnalyticsDashboard } from '../analytics/AdvancedAnalyticsDashboard';
import { PersonalizationPanel } from '../analytics/PersonalizationPanel';
import { PredictiveInsights } from '../analytics/PredictiveInsights';
import { LearningProgress } from '../analytics/LearningProgress';

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
  const { t } = useTranslation();
  // 重複リクエスト抑制（StrictModeのダブルマウント対策）
  const statusFetchLockRef = useRef(false);
  const lastStatusFetchAtRef = useRef(0);
  
  // Settings modal state
  const [localAutoRefresh, setLocalAutoRefresh] = useState(autoRefresh);
  const [localRefreshInterval, setLocalRefreshInterval] = useState(refreshInterval);
  
  // UI theming
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  // Initialize local settings when modal opens
  useEffect(() => {
    if (isOpen) {
      setLocalAutoRefresh(autoRefresh);
      setLocalRefreshInterval(refreshInterval);
    }
  }, [isOpen, autoRefresh, refreshInterval]);

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

      // Calculate overall health
      const activePhases = Object.values(statusData).filter(status => status === 'active').length;
      statusData.overall_health = (activePhases - 1) / 3; // Exclude last_update from count

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

  // Render system status
  const renderSystemStatus = () => {
    if (!systemStatus) return null;

    const statusMapping = {
      'active': { color: 'green', label: 'アクティブ' },
      'inactive': { color: 'yellow', label: '非アクティブ' },
      'error': { color: 'red', label: 'エラー' }
    };

    return (
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
        <Card bg={cardBg}>
          <CardBody>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontSize="sm" color="gray.500">データ収集</Text>
                <Badge colorScheme={statusMapping[systemStatus.data_collection].color}>
                  {statusMapping[systemStatus.data_collection].label}
                </Badge>
              </VStack>
              <Icon as={FiHome} color="blue.500" />
            </HStack>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontSize="sm" color="gray.500">TTS音声</Text>
                <Badge colorScheme={statusMapping[systemStatus.tts_system].color}>
                  {statusMapping[systemStatus.tts_system].label}
                </Badge>
              </VStack>
              <Icon as={FiVolumeX} color="purple.500" />
            </HStack>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontSize="sm" color="gray.500">統合</Text>
                <Badge colorScheme={statusMapping[systemStatus.integration].color}>
                  {statusMapping[systemStatus.integration].label}
                </Badge>
              </VStack>
              <Icon as={FiActivity} color="green.500" />
            </HStack>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontSize="sm" color="gray.500">AI分析</Text>
                <Badge colorScheme={statusMapping[systemStatus.ai_analysis].color}>
                  {statusMapping[systemStatus.ai_analysis].label}
                </Badge>
              </VStack>
              <Icon as={FiTarget} color="orange.500" />
            </HStack>
          </CardBody>
        </Card>
      </SimpleGrid>
    );
  };

  // Render overall health
  const renderOverallHealth = () => {
    if (!systemStatus) return null;

    const healthColor = systemStatus.overall_health > 0.8 ? 'green' : 
                       systemStatus.overall_health > 0.6 ? 'yellow' : 'red';

    return (
      <Card bg={cardBg}>
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="md">{t('dashboard.overall_health')}</Heading>
            <Text fontSize="sm" color="gray.500">
              {t('dashboard.last_update')}: {lastRefresh.toLocaleTimeString()}
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4}>
            <Box width="100%">
              <HStack justify="space-between" mb={2}>
                <Text>健康度スコア</Text>
                <Text fontWeight="bold" color={`${healthColor}.500`}>
                  {(systemStatus.overall_health * 100).toFixed(0)}%
                </Text>
              </HStack>
              <Progress 
                value={systemStatus.overall_health * 100}
                colorScheme={healthColor}
                size="lg"
              />
            </Box>
            
            {/* 監視常時アクティブ状態表示 */}
              <HStack justify="center" width="100%" p={3} bg="green.50" borderRadius="md" role="status" aria-live="polite">
              <Icon as={FiActivity} color="green.500" />
              <Text fontSize="sm" color="green.700" fontWeight="medium">
                監視システム: 常時アクティブ
              </Text>
            </HStack>
            
            <HStack spacing={4} width="100%">
              <Button
                leftIcon={<Icon as={FiRefreshCw} />}
                onClick={fetchSystemStatus}
                isLoading={isLoading}
                size="sm"
                variant="outline"
              >
                {t('common.update')}
              </Button>
              
              <Button
                leftIcon={<Icon as={FiSettings} />}
                onClick={onOpen}
                size="sm"
                variant="outline"
              >
                {t('common.settings')}
              </Button>
            </HStack>
          </VStack>
        </CardBody>
      </Card>
    );
  };

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
          <VStack spacing={6} align="stretch">
            <Text fontSize="lg" fontWeight="bold">{t('dashboard.title')}</Text>
            <Text color="gray.600">{t('dashboard.description')}</Text>
            {renderSystemStatus()}
            {renderOverallHealth()}
          </VStack>
        );
    }
  };

  // Settings save handler
  const handleSaveSettings = useCallback(() => {
    // 設定値の保存とtoast表示
    toast({
      title: '設定を保存しました',
      description: `自動更新: ${localAutoRefresh ? 'ON' : 'OFF'}, 更新間隔: ${localRefreshInterval}秒`,
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
    
    // モーダルを閉じる
    onClose();
    
    // 設定が変更されている場合は再レンダリングを促す
    if (localAutoRefresh !== autoRefresh || localRefreshInterval !== refreshInterval) {
      // propsが変更された場合の処理は親コンポーネントでハンドリング
      console.log('Settings changed:', { localAutoRefresh, localRefreshInterval });
    }
  }, [localAutoRefresh, localRefreshInterval, autoRefresh, refreshInterval, toast, onClose]);

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
          <Box role="navigation" position="fixed" height="100vh" width="250px" bg={cardBg} p={4} overflowY="auto" display="flex" flexDirection="column">
            <VStack spacing={3} align="stretch" flex="1">
              <Heading size="md" mb={4}>{t('app.title')}</Heading>
              
              <Button
                variant={selectedView === 'overview' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiTrendingUp} />}
                onClick={() => handleViewChange('overview')}
                aria-current={selectedView === 'overview' ? 'page' : undefined}
                aria-label={t('tabs.overview')}
              >
                {t('tabs.overview')}
              </Button>
              
              <Divider />
              <Text fontSize="sm" fontWeight="bold" color="gray.500">{t('nav.sections.core')}</Text>
              
              <Button
                variant={selectedView === 'monitor' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiHome} />}
                onClick={() => handleViewChange('monitor')}
                aria-current={selectedView === 'monitor' ? 'page' : undefined}
                aria-label={t('tabs.monitor')}
              >
                {t('tabs.monitor')}
              </Button>
              
              <Button
                variant={selectedView === 'voice' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiVolumeX} />}
                onClick={() => handleViewChange('voice')}
                aria-current={selectedView === 'voice' ? 'page' : undefined}
                aria-label={t('tabs.voice')}
              >
                {t('tabs.voice')}
              </Button>

              <Button
                variant={selectedView === 'schedule' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiCalendar} />}
                onClick={() => handleViewChange('schedule')}
                aria-current={selectedView === 'schedule' ? 'page' : undefined}
                aria-label={t('tabs.schedule')}
              >
                {t('tabs.schedule')}
              </Button>

              <Button
                variant={selectedView === 'settings' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiSettings} />}
                onClick={() => handleViewChange('settings')}
                aria-current={selectedView === 'settings' ? 'page' : undefined}
                aria-label={t('tabs.settings')}
              >
                {t('tabs.settings')}
              </Button>
              
              <Button
                variant={selectedView === 'behavior' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiActivity} />}
                onClick={() => handleViewChange('behavior')}
                aria-current={selectedView === 'behavior' ? 'page' : undefined}
                aria-label={t('tabs.behavior')}
              >
                {t('tabs.behavior')}
              </Button>
              
              <Divider />
              <Text fontSize="sm" fontWeight="bold" color="gray.500">{t('nav.sections.advanced')}</Text>
              
              <Button
                variant={selectedView === 'analytics' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiTarget} />}
                onClick={() => handleViewChange('analytics')}
                aria-current={selectedView === 'analytics' ? 'page' : undefined}
                aria-label={t('tabs.analytics')}
              >
                {t('tabs.analytics')}
              </Button>
              
              <Button
                variant={selectedView === 'personalization' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiSettings} />}
                onClick={() => handleViewChange('personalization')}
                aria-current={selectedView === 'personalization' ? 'page' : undefined}
                aria-label={t('tabs.personalization')}
              >
                {t('tabs.personalization')}
              </Button>
              
              <Button
                variant={selectedView === 'predictions' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiTrendingUp} />}
                onClick={() => handleViewChange('predictions')}
                aria-current={selectedView === 'predictions' ? 'page' : undefined}
                aria-label={t('tabs.predictions')}
              >
                {t('tabs.predictions')}
              </Button>
              
              <Button
                variant={selectedView === 'learning' ? 'solid' : 'ghost'}
                justifyContent="flex-start"
                leftIcon={<Icon as={FiActivity} />}
                onClick={() => handleViewChange('learning')}
                aria-current={selectedView === 'learning' ? 'page' : undefined}
                aria-label={t('tabs.learning')}
              >
                {t('tabs.learning')}
              </Button>
            </VStack>
            <Box pt={2}>
              <LanguageSwitcher />
            </Box>
          </Box>
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

      {/* Settings Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>統合ダッシュボード設定</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="auto-refresh" mb="0">
                  自動更新
                </FormLabel>
                <Switch 
                  id="auto-refresh" 
                  isChecked={localAutoRefresh}
                  onChange={(e) => setLocalAutoRefresh(e.target.checked)}
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>更新間隔（秒）</FormLabel>
                <Select 
                  value={localRefreshInterval}
                  onChange={(e) => setLocalRefreshInterval(Number(e.target.value))}
                >
                  <option value={15}>15秒</option>
                  <option value={30}>30秒</option>
                  <option value={60}>1分</option>
                  <option value={300}>5分</option>
                </Select>
              </FormControl>
              
              <FormControl>
                <FormLabel>ユーザーID</FormLabel>
                <Text fontSize="sm" color="gray.600">{userId}</Text>
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              キャンセル
            </Button>
            <Button colorScheme="blue" onClick={handleSaveSettings}>
              保存
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}; 