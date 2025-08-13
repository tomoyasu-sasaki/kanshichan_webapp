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
  Container,
  Flex,
  Avatar,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Tooltip,
  CircularProgress,
  CircularProgressLabel
} from '@chakra-ui/react';
import {
  FiHome, FiVolumeX, FiActivity, FiTarget, FiRefreshCw,
  FiSettings, FiTrendingUp, FiCalendar, FiMonitor, FiCpu,
  FiWifi, FiDatabase, FiZap, FiShield, FiUsers, FiBarChart
} from 'react-icons/fi';
import { FaRobot, FaMicrophone, FaChartLine, FaBell } from 'react-icons/fa';
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

  // Render system status with enhanced design
  const renderSystemStatus = () => {
    if (!systemStatus) return null;

    const statusMapping = {
      'active': { color: 'green', label: 'アクティブ', icon: FiZap },
      'inactive': { color: 'yellow', label: '非アクティブ', icon: FiWifi },
      'error': { color: 'red', label: 'エラー', icon: FiShield }
    };

    const systemComponents = [
      {
        key: 'data_collection',
        title: 'データ収集',
        description: 'リアルタイム監視',
        icon: FiDatabase,
        color: 'blue.500',
        status: systemStatus.data_collection
      },
      {
        key: 'tts_system',
        title: 'TTS音声',
        description: '音声合成エンジン',
        icon: FaMicrophone,
        color: 'purple.500',
        status: systemStatus.tts_system
      },
      {
        key: 'integration',
        title: '統合システム',
        description: 'コンポーネント連携',
        icon: FiCpu,
        color: 'green.500',
        status: systemStatus.integration
      },
      {
        key: 'ai_analysis',
        title: 'AI分析',
        description: '行動パターン解析',
        icon: FaRobot,
        color: 'orange.500',
        status: systemStatus.ai_analysis
      }
    ];

    return (
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
        {systemComponents.map((component) => {
          const statusInfo = statusMapping[component.status];
          return (
            <Card
              key={component.key}
              bg={cardBg}
              shadow="lg"
              border="1px solid"
              borderColor={useColorModeValue('gray.200', 'gray.600')}
              _hover={{
                transform: 'translateY(-2px)',
                shadow: 'xl'
              }}
              transition="all 0.2s"
            >
              <CardBody p={6}>
                <VStack spacing={4} align="stretch">
                  <HStack justify="space-between" align="center">
                    <Avatar
                      icon={<Icon as={component.icon} />}
                      bg={component.color}
                      size="md"
                    />
                    <Tooltip label={`状態: ${statusInfo.label}`}>
                      <Icon
                        as={statusInfo.icon}
                        color={`${statusInfo.color}.500`}
                        boxSize={5}
                      />
                    </Tooltip>
                  </HStack>

                  <VStack align="start" spacing={2}>
                    <Heading size="sm" color="gray.700" _dark={{ color: 'gray.100' }}>
                      {component.title}
                    </Heading>
                    <Text fontSize="xs" color="gray.500">
                      {component.description}
                    </Text>
                    <Badge
                      colorScheme={statusInfo.color}
                      variant="subtle"
                      px={3}
                      py={1}
                      borderRadius="full"
                      fontSize="xs"
                    >
                      {statusInfo.label}
                    </Badge>
                  </VStack>
                </VStack>
              </CardBody>
            </Card>
          );
        })}
      </SimpleGrid>
    );
  };

  // Render overall health with enhanced design
  const renderOverallHealth = () => {
    if (!systemStatus) return null;

    const healthColor = systemStatus.overall_health > 0.8 ? 'green' :
      systemStatus.overall_health > 0.6 ? 'yellow' : 'red';
    const healthPercentage = Math.round(systemStatus.overall_health * 100);

    return (
      <Card bg={cardBg} shadow="lg">
        <CardHeader pb={2}>
          <HStack justify="space-between" align="center">
            <HStack spacing={3}>
              <Avatar
                icon={<Icon as={FiMonitor} />}
                bg="blue.500"
                size="md"
              />
              <VStack align="start" spacing={0}>
                <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                  システム健康度
                </Heading>
                <Text fontSize="sm" color="gray.500">
                  最終更新: {lastRefresh.toLocaleTimeString()}
                </Text>
              </VStack>
            </HStack>
            <CircularProgress
              value={healthPercentage}
              color={`${healthColor}.500`}
              size="60px"
              thickness="8px"
            >
              <CircularProgressLabel fontSize="sm" fontWeight="bold">
                {healthPercentage}%
              </CircularProgressLabel>
            </CircularProgress>
          </HStack>
        </CardHeader>
        <CardBody pt={2}>
          <VStack spacing={5}>
            {/* 詳細メトリクス */}
            <SimpleGrid columns={2} spacing={4} width="100%">
              <Stat>
                <StatLabel fontSize="xs">アクティブ</StatLabel>
                <StatNumber fontSize="lg" color="green.500">
                  {Object.values(systemStatus).filter(status => status === 'active').length}
                </StatNumber>
                <StatHelpText fontSize="xs">
                  <StatArrow type="increase" />
                  システム
                </StatHelpText>
              </Stat>
              <Stat>
                <StatLabel fontSize="xs">稼働時間</StatLabel>
                <StatNumber fontSize="lg" color="blue.500">
                  24h
                </StatNumber>
                <StatHelpText fontSize="xs">
                  <StatArrow type="increase" />
                  連続稼働
                </StatHelpText>
              </Stat>
            </SimpleGrid>

            {/* ステータスインジケーター */}
            <Box
              width="100%"
              p={4}
              bg={useColorModeValue('green.50', 'green.900')}
              borderRadius="lg"
              border="1px solid"
              borderColor={useColorModeValue('green.200', 'green.700')}
            >
              <HStack justify="center" spacing={3}>
                <Icon as={FiActivity} color="green.500" boxSize={5} />
                <VStack spacing={0} align="center">
                  <Text fontSize="sm" color="green.700" _dark={{ color: 'green.300' }} fontWeight="medium">
                    監視システム稼働中
                  </Text>
                  <Text fontSize="xs" color="green.600" _dark={{ color: 'green.400' }}>
                    リアルタイム監視アクティブ
                  </Text>
                </VStack>
              </HStack>
            </Box>

            {/* アクションボタン */}
            <HStack spacing={3} width="100%">
              <Button
                leftIcon={<Icon as={FiRefreshCw} />}
                onClick={fetchSystemStatus}
                isLoading={isLoading}
                colorScheme="blue"
                variant="outline"
                flex={1}
                borderRadius="lg"
              >
                更新
              </Button>
              <Tooltip label="詳細な監視画面を開く">
                <Button
                  leftIcon={<Icon as={FiMonitor} />}
                  onClick={() => handleViewChange('monitor')}
                  colorScheme="green"
                  variant="outline"
                  flex={1}
                  borderRadius="lg"
                >
                  詳細
                </Button>
              </Tooltip>
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
          <Container maxW="1400px" px={0}>
            <VStack spacing={8} align="stretch">
              {/* ヘッダーセクション */}
              <Box
                bgGradient={useColorModeValue(
                  'linear(to-r, blue.50, purple.50)',
                  'linear(to-r, blue.900, purple.900)'
                )}
                borderRadius="xl"
                border="1px solid"
                borderColor={useColorModeValue('gray.200', 'gray.600')}
                p={8}
                shadow="lg"
              >
                <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
                  <VStack align="start" spacing={3}>
                    <HStack spacing={4}>
                      <Avatar
                        icon={<Icon as={FiBarChart} />}
                        bg="blue.500"
                        size="lg"
                      />
                      <VStack align="start" spacing={1}>
                        <Heading size="xl" color="gray.700" _dark={{ color: 'gray.100' }}>
                          システム概要ダッシュボード
                        </Heading>
                        <Text fontSize="md" color="gray.600" _dark={{ color: 'gray.300' }}>
                          リアルタイム監視とシステム状態の統合管理
                        </Text>
                      </VStack>
                    </HStack>

                    {/* クイックステータス */}
                    <HStack spacing={4} wrap="wrap">
                      <Badge colorScheme="green" px={3} py={1} borderRadius="full">
                        <HStack spacing={1}>
                          <Icon as={FiZap} boxSize={3} />
                          <Text fontSize="sm">システム稼働中</Text>
                        </HStack>
                      </Badge>
                      <Badge colorScheme="blue" px={3} py={1} borderRadius="full">
                        <HStack spacing={1}>
                          <Icon as={FiUsers} boxSize={3} />
                          <Text fontSize="sm">監視アクティブ</Text>
                        </HStack>
                      </Badge>
                      <Badge colorScheme="purple" px={3} py={1} borderRadius="full">
                        <HStack spacing={1}>
                          <Icon as={FaBell} boxSize={3} />
                          <Text fontSize="sm">通知有効</Text>
                        </HStack>
                      </Badge>
                    </HStack>
                  </VStack>

                  {/* クイックアクション */}
                  <VStack spacing={3}>
                    <HStack spacing={3}>
                      <Tooltip label="監視画面を開く">
                        <Button
                          leftIcon={<Icon as={FiHome} />}
                          onClick={() => handleViewChange('monitor')}
                          colorScheme="blue"
                          variant="solid"
                          borderRadius="lg"
                        >
                          監視
                        </Button>
                      </Tooltip>
                      <Tooltip label="音声設定を開く">
                        <Button
                          leftIcon={<Icon as={FiVolumeX} />}
                          onClick={() => handleViewChange('voice')}
                          colorScheme="purple"
                          variant="solid"
                          borderRadius="lg"
                        >
                          音声
                        </Button>
                      </Tooltip>
                      <Tooltip label="分析画面を開く">
                        <Button
                          leftIcon={<Icon as={FiTarget} />}
                          onClick={() => handleViewChange('analytics')}
                          colorScheme="green"
                          variant="solid"
                          borderRadius="lg"
                        >
                          分析
                        </Button>
                      </Tooltip>
                    </HStack>
                    <Text fontSize="xs" color="gray.500" textAlign="center">
                      最終更新: {lastRefresh.toLocaleTimeString()}
                    </Text>
                  </VStack>
                </Flex>
              </Box>

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
                  {renderSystemStatus()}
                </CardBody>
              </Card>

              {/* 下段: 健康度とクイックアクセス */}
              <SimpleGrid columns={{ base: 1, xl: 2 }} spacing={8} alignItems="stretch">
                {renderOverallHealth()}

                {/* クイックアクセスパネル */}
                <Card bg={cardBg} shadow="lg">
                  <CardHeader pb={2}>
                    <HStack spacing={3}>
                      <Icon as={FiTarget} color="green.500" boxSize={6} />
                      <VStack align="start" spacing={0}>
                        <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                          クイックアクセス
                        </Heading>
                        <Text fontSize="sm" color="gray.500">
                          よく使用する機能への直接アクセス
                        </Text>
                      </VStack>
                    </HStack>
                  </CardHeader>
                  <CardBody pt={2}>
                    <VStack spacing={6} align="stretch">
                      {/* 主要機能 */}
                      <Box>
                        <Text fontSize="sm" fontWeight="semibold" color="gray.600" mb={3}>
                          主要機能
                        </Text>
                        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                          <Button
                            variant="outline"
                            leftIcon={<Icon as={FiHome} />}
                            onClick={() => handleViewChange('monitor')}
                            justifyContent="flex-start"
                            h="50px"
                            borderRadius="lg"
                            _hover={{ bg: useColorModeValue('blue.50', 'blue.900') }}
                          >
                            <VStack align="start" spacing={0} flex={1}>
                              <Text fontSize="sm" fontWeight="medium">監視</Text>
                              <Text fontSize="xs" color="gray.500">リアルタイム監視</Text>
                            </VStack>
                          </Button>
                          <Button
                            variant="outline"
                            leftIcon={<Icon as={FiVolumeX} />}
                            onClick={() => handleViewChange('voice')}
                            justifyContent="flex-start"
                            h="50px"
                            borderRadius="lg"
                            _hover={{ bg: useColorModeValue('purple.50', 'purple.900') }}
                          >
                            <VStack align="start" spacing={0} flex={1}>
                              <Text fontSize="sm" fontWeight="medium">音声設定</Text>
                              <Text fontSize="xs" color="gray.500">TTS・音声合成</Text>
                            </VStack>
                          </Button>
                          <Button
                            variant="outline"
                            leftIcon={<Icon as={FiCalendar} />}
                            onClick={() => handleViewChange('schedule')}
                            justifyContent="flex-start"
                            h="50px"
                            borderRadius="lg"
                            _hover={{ bg: useColorModeValue('green.50', 'green.900') }}
                          >
                            <VStack align="start" spacing={0} flex={1}>
                              <Text fontSize="sm" fontWeight="medium">スケジュール</Text>
                              <Text fontSize="xs" color="gray.500">予定管理</Text>
                            </VStack>
                          </Button>
                          <Button
                            variant="outline"
                            leftIcon={<Icon as={FiSettings} />}
                            onClick={() => handleViewChange('settings')}
                            justifyContent="flex-start"
                            h="50px"
                            borderRadius="lg"
                            _hover={{ bg: useColorModeValue('orange.50', 'orange.900') }}
                          >
                            <VStack align="start" spacing={0} flex={1}>
                              <Text fontSize="sm" fontWeight="medium">設定</Text>
                              <Text fontSize="xs" color="gray.500">システム設定</Text>
                            </VStack>
                          </Button>
                        </SimpleGrid>
                      </Box>

                      <Divider />

                      {/* 分析・解析機能 */}
                      <Box>
                        <Text fontSize="sm" fontWeight="semibold" color="gray.600" mb={3}>
                          分析・解析
                        </Text>
                        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                          <Button
                            variant="outline"
                            leftIcon={<Icon as={FiActivity} />}
                            onClick={() => handleViewChange('behavior')}
                            justifyContent="flex-start"
                            h="50px"
                            borderRadius="lg"
                            _hover={{ bg: useColorModeValue('teal.50', 'teal.900') }}
                          >
                            <VStack align="start" spacing={0} flex={1}>
                              <Text fontSize="sm" fontWeight="medium">行動分析</Text>
                              <Text fontSize="xs" color="gray.500">パターン解析</Text>
                            </VStack>
                          </Button>
                          <Button
                            variant="outline"
                            leftIcon={<Icon as={FiTarget} />}
                            onClick={() => handleViewChange('analytics')}
                            justifyContent="flex-start"
                            h="50px"
                            borderRadius="lg"
                            _hover={{ bg: useColorModeValue('cyan.50', 'cyan.900') }}
                          >
                            <VStack align="start" spacing={0} flex={1}>
                              <Text fontSize="sm" fontWeight="medium">詳細分析</Text>
                              <Text fontSize="xs" color="gray.500">高度な解析</Text>
                            </VStack>
                          </Button>
                          <Button
                            variant="outline"
                            leftIcon={<Icon as={FiTrendingUp} />}
                            onClick={() => handleViewChange('predictions')}
                            justifyContent="flex-start"
                            h="50px"
                            borderRadius="lg"
                            _hover={{ bg: useColorModeValue('pink.50', 'pink.900') }}
                          >
                            <VStack align="start" spacing={0} flex={1}>
                              <Text fontSize="sm" fontWeight="medium">予測分析</Text>
                              <Text fontSize="xs" color="gray.500">将来予測</Text>
                            </VStack>
                          </Button>
                          <Button
                            variant="outline"
                            leftIcon={<Icon as={FaChartLine} />}
                            onClick={() => handleViewChange('learning')}
                            justifyContent="flex-start"
                            h="50px"
                            borderRadius="lg"
                            _hover={{ bg: useColorModeValue('indigo.50', 'indigo.900') }}
                          >
                            <VStack align="start" spacing={0} flex={1}>
                              <Text fontSize="sm" fontWeight="medium">学習進捗</Text>
                              <Text fontSize="xs" color="gray.500">AI学習状況</Text>
                            </VStack>
                          </Button>
                        </SimpleGrid>
                      </Box>
                    </VStack>
                  </CardBody>
                </Card>
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

      {/* 設定ダイアログは廃止 */}
    </Box>
  );
}; 