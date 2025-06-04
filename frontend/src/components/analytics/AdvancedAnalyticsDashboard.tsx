import React, { useState, useEffect, useCallback } from 'react';
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
  Select,
  Switch,
  FormControl,
  FormLabel,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Progress,
  Divider,
  useColorModeValue,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Tab,
  Tabs,
  TabList,
  TabPanel,
  TabPanels
} from '@chakra-ui/react';
import { io, Socket } from 'socket.io-client';

interface AnalyticsData {
  timestamp: string;
  focus_score: number;
  posture_score: number;
  productivity_score: number;
  fatigue_level: number;
  distraction_count: number;
}

interface BehaviorPattern {
  pattern_type: string;
  confidence: number;
  frequency: number;
  description: string;
  recommendations: string[];
}

interface PredictiveInsight {
  metric: string;
  predicted_value: number;
  confidence: number;
  timestamp: string;
  trend: 'increasing' | 'decreasing' | 'stable';
}

interface PerformanceMetric {
  name: string;
  current_value: number;
  target_value: number;
  status: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
}

interface PerformanceData {
  system_statistics?: {
    avg_cpu_usage?: number;
  };
  analysis_statistics?: {
    avg_accuracy?: number;
    avg_latency?: number;
  };
}

interface AdvancedAnalyticsDashboardProps {
  userId?: string;
  timeframe?: 'hour' | 'day' | 'week' | 'month';
  isRealtime?: boolean;
}

export const AdvancedAnalyticsDashboard: React.FC<AdvancedAnalyticsDashboardProps> = ({
  userId = 'default',
  timeframe = 'day',
  isRealtime = true
}) => {
  // State management
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData[]>([]);
  const [behaviorPatterns, setBehaviorPatterns] = useState<BehaviorPattern[]>([]);
  const [predictiveInsights, setPredictiveInsights] = useState<PredictiveInsight[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetric[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);
  const [realtimeEnabled, setRealtimeEnabled] = useState(isRealtime);
  const [error, setError] = useState<string | null>(null);

  // UI theming
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const toast = useToast();

  // API基底URL設定（Phase 0.2で追加）
  const API_BASE_URL = 'http://localhost:8000/api';

  // Data fetching functions
  const fetchAnalyticsData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch time series data
      const timeseriesResponse = await fetch(`${API_BASE_URL}/analysis/trends?timeframe=${selectedTimeframe}&user_id=${userId}`);
      if (!timeseriesResponse.ok) throw new Error('Failed to fetch analytics data');
      const timeseriesData = await timeseriesResponse.json();

      // Fetch advanced patterns
      const patternsResponse = await fetch(`${API_BASE_URL}/analysis/advanced-patterns?user_id=${userId}&timeframe=${selectedTimeframe}`);
      if (!patternsResponse.ok) throw new Error('Failed to fetch behavior patterns');
      const patternsData = await patternsResponse.json();

      // Fetch predictions
      const predictionsResponse = await fetch(`${API_BASE_URL}/analysis/predictions?user_id=${userId}&metrics=focus_score,productivity_score,fatigue_level`);
      if (!predictionsResponse.ok) throw new Error('Failed to fetch predictions');
      const predictionsData = await predictionsResponse.json();

      // Fetch performance metrics
      const performanceResponse = await fetch(`${API_BASE_URL}/analysis/performance-report?hours=24`);
      if (!performanceResponse.ok) throw new Error('Failed to fetch performance metrics');
      const performanceData = await performanceResponse.json();

      // Process and set data
      setAnalyticsData(timeseriesData.trends?.focus_trends || []);
      setBehaviorPatterns(patternsData.patterns?.behavior_patterns || []);
      setPredictiveInsights(predictionsData.predictions || []);
      setPerformanceMetrics(transformPerformanceData(performanceData));

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      toast({
        title: 'データ取得エラー',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  }, [selectedTimeframe, userId, toast]);

  // Transform performance data for display
  const transformPerformanceData = (data: PerformanceData): PerformanceMetric[] => {
    const systemMetrics = data.system_statistics || {};
    const analysisMetrics = data.analysis_statistics || {};
    
    return [
      {
        name: 'CPU使用率',
        current_value: systemMetrics.avg_cpu_usage || 0,
        target_value: 80,
        status: systemMetrics.avg_cpu_usage && systemMetrics.avg_cpu_usage > 90 ? 'critical' : 
                systemMetrics.avg_cpu_usage && systemMetrics.avg_cpu_usage > 80 ? 'poor' : 'good'
      },
      {
        name: '分析精度',
        current_value: analysisMetrics.avg_accuracy || 0,
        target_value: 85,
        status: analysisMetrics.avg_accuracy && analysisMetrics.avg_accuracy > 90 ? 'excellent' : 
                analysisMetrics.avg_accuracy && analysisMetrics.avg_accuracy > 85 ? 'good' : 'fair'
      },
      {
        name: 'レスポンス時間',
        current_value: analysisMetrics.avg_latency || 0,
        target_value: 100,
        status: analysisMetrics.avg_latency && analysisMetrics.avg_latency < 50 ? 'excellent' : 
                analysisMetrics.avg_latency && analysisMetrics.avg_latency < 100 ? 'good' : 'poor'
      }
    ];
  };

  // Realtime data streaming
  useEffect(() => {
    let socket: Socket | null = null;

    if (realtimeEnabled) {
      // Phase 4対応: Socket.IOクライアント接続
      socket = io('http://localhost:8000');
      
      socket.on('connect', () => {
        console.log('WebSocket connected to backend');
      });

      // Phase 4で実装した新しいイベントを受信
      socket.on('behavior_data', (data: any) => {
        try {
          console.log('Received behavior_data:', data);
          // 行動データの更新
          if (data.focus_trends && Array.isArray(data.focus_trends)) {
            const latestTrend = data.focus_trends[data.focus_trends.length - 1];
            if (latestTrend) {
              const newDataPoint: AnalyticsData = {
                timestamp: latestTrend.timestamp,
                focus_score: latestTrend.focus_level || 0,
                posture_score: data.current_status?.posture_score || 0,
                productivity_score: (latestTrend.focus_level || 0) * 0.8,
                fatigue_level: data.current_status?.smartphone_detected ? 0.7 : 0.3,
                distraction_count: data.current_status?.smartphone_detected ? 1 : 0
              };
              setAnalyticsData(prev => [...prev.slice(-99), newDataPoint]);
            }
          }
        } catch (err) {
          console.error('Behavior data processing error:', err);
        }
      });

      socket.on('analysis_results', (data: any) => {
        try {
          console.log('Received analysis_results:', data);
          // 分析結果の更新
          if (Array.isArray(data)) {
            // インサイトデータとして設定
            const newPatterns = data.map((insight: string, index: number) => ({
              pattern_type: `分析結果 ${index + 1}`,
              confidence: 0.85,
              frequency: 1,
              description: insight,
              recommendations: ['継続的な監視を推奨']
            }));
            setBehaviorPatterns(newPatterns);
          }
        } catch (err) {
          console.error('Analysis results processing error:', err);
        }
      });

      socket.on('status', (data: any) => {
        try {
          console.log('Received status:', data);
          // 統合ステータスの更新
          if (data.behavior_data && data.analysis_results) {
            // behavior_dataとanalysis_resultsの両方が含まれる場合の処理
            socket?.emit('behavior_data', data.behavior_data);
            socket?.emit('analysis_results', data.analysis_results);
          }
        } catch (err) {
          console.error('Status processing error:', err);
        }
      });

      socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
      });

      socket.on('error', (error: any) => {
        console.error('Socket.IO error:', error);
        toast({
          title: 'リアルタイム接続エラー',
          description: 'リアルタイムデータ取得に失敗しました',
          status: 'warning',
          duration: 3000,
          isClosable: true,
        });
      });
    }

    // クリーンアップ関数
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, [realtimeEnabled, toast]);

  // Initial data fetch
  useEffect(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  // Auto-refresh for non-realtime mode
  useEffect(() => {
    if (!realtimeEnabled) {
      const interval = setInterval(fetchAnalyticsData, 30000); // 30秒間隔
      return () => clearInterval(interval);
    }
  }, [realtimeEnabled, fetchAnalyticsData]);

  // Render performance status badge
  const renderStatusBadge = (status: string) => {
    const colorScheme = {
      excellent: 'green',
      good: 'blue',
      fair: 'yellow',
      poor: 'orange',
      critical: 'red'
    }[status] || 'gray';

    return <Badge colorScheme={colorScheme}>{status.toUpperCase()}</Badge>;
  };

  // Render time series chart
  const renderTimeSeriesChart = () => (
    <Box height={300} display="flex" alignItems="center" justifyContent="center">
      <Text color="gray.500">
        チャートライブラリが利用できません。時系列データを表形式で表示します。
      </Text>
    </Box>
  );

  // Render behavior patterns
  const renderBehaviorPatterns = () => (
    <VStack spacing={4} align="stretch">
      {behaviorPatterns.map((pattern, index) => (
        <Card key={index} size="sm">
          <CardBody>
            <HStack justify="space-between" mb={2}>
              <Text fontWeight="bold">{pattern.pattern_type}</Text>
              <Badge colorScheme="blue">{(pattern.confidence * 100).toFixed(0)}%</Badge>
            </HStack>
            <Text fontSize="sm" color="gray.600" mb={2}>
              {pattern.description}
            </Text>
            <Text fontSize="xs" color="gray.500">
              頻度: {pattern.frequency}回/日
            </Text>
          </CardBody>
        </Card>
      ))}
    </VStack>
  );

  // Render predictive insights
  const renderPredictiveInsights = () => (
    <VStack spacing={4} align="stretch">
      {predictiveInsights.map((insight, index) => (
        <Card key={index} size="sm">
          <CardBody>
            <HStack justify="space-between" mb={2}>
              <Text fontWeight="bold">
                {insight.metric === 'focus_score' ? '集中度' :
                 insight.metric === 'productivity_score' ? '生産性' :
                 insight.metric === 'fatigue_level' ? '疲労度' : insight.metric}
              </Text>
              <HStack>
                {insight.trend === 'increasing' && <StatArrow type="increase" />}
                {insight.trend === 'decreasing' && <StatArrow type="decrease" />}
                <Badge colorScheme={insight.trend === 'increasing' ? 'green' : insight.trend === 'decreasing' ? 'red' : 'gray'}>
                  {insight.trend}
                </Badge>
              </HStack>
            </HStack>
            <Progress 
              value={insight.predicted_value * 100} 
              colorScheme={insight.predicted_value > 0.7 ? 'green' : insight.predicted_value > 0.4 ? 'yellow' : 'red'}
              size="sm"
              mb={2}
            />
            <Text fontSize="xs" color="gray.500">
              信頼度: {(insight.confidence * 100).toFixed(0)}%
            </Text>
          </CardBody>
        </Card>
      ))}
    </VStack>
  );

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        <AlertTitle>データ取得エラー</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <Box bg={bgColor} minH="100vh" p={6}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between" align="center">
          <Heading size="lg">高度分析ダッシュボード</Heading>
          <HStack spacing={4}>
            <FormControl display="flex" alignItems="center">
              <FormLabel htmlFor="realtime-switch" mb="0" fontSize="sm">
                リアルタイム
              </FormLabel>
              <Switch 
                id="realtime-switch"
                isChecked={realtimeEnabled}
                onChange={(e) => setRealtimeEnabled(e.target.checked)}
              />
            </FormControl>
            <Select 
              value={selectedTimeframe} 
              onChange={(e) => setSelectedTimeframe(e.target.value as 'hour' | 'day' | 'week' | 'month')}
              size="sm"
              w="auto"
            >
              <option value="hour">1時間</option>
              <option value="day">1日</option>
              <option value="week">1週間</option>
              <option value="month">1ヶ月</option>
            </Select>
          </HStack>
        </HStack>

        {isLoading && (
          <HStack justify="center" py={8}>
            <Spinner size="lg" />
            <Text>データを読み込み中...</Text>
          </HStack>
        )}

        {!isLoading && (
          <Tabs>
            <TabList>
              <Tab>概要</Tab>
              <Tab>行動パターン</Tab>
              <Tab>予測インサイト</Tab>
              <Tab>パフォーマンス</Tab>
            </TabList>

            <TabPanels>
              {/* Overview Tab */}
              <TabPanel>
                <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={6}>
                  {/* Time Series Chart */}
                  <GridItem colSpan={2}>
                    <Card bg={cardBg}>
                      <CardHeader>
                        <Heading size="md">時系列分析</Heading>
                      </CardHeader>
                      <CardBody>
                        {renderTimeSeriesChart()}
                      </CardBody>
                    </Card>
                  </GridItem>

                  {/* Current Stats */}
                  <GridItem>
                    <Card bg={cardBg}>
                      <CardHeader>
                        <Heading size="md">現在の状況</Heading>
                      </CardHeader>
                      <CardBody>
                        <VStack spacing={4}>
                          <Stat>
                            <StatLabel>集中度</StatLabel>
                            <StatNumber>
                              {analyticsData.length > 0 ? 
                                `${(analyticsData[analyticsData.length - 1].focus_score * 100).toFixed(0)}%` : 
                                'N/A'
                              }
                            </StatNumber>
                            <StatHelpText>
                              {analyticsData.length > 1 && (
                                <StatArrow 
                                  type={analyticsData[analyticsData.length - 1].focus_score > analyticsData[analyticsData.length - 2].focus_score ? 'increase' : 'decrease'} 
                                />
                              )}
                              直近の変化
                            </StatHelpText>
                          </Stat>
                          <Divider />
                          <Stat>
                            <StatLabel>姿勢スコア</StatLabel>
                            <StatNumber>
                              {analyticsData.length > 0 ? 
                                `${(analyticsData[analyticsData.length - 1].posture_score * 100).toFixed(0)}%` : 
                                'N/A'
                              }
                            </StatNumber>
                          </Stat>
                          <Divider />
                          <Stat>
                            <StatLabel>生産性</StatLabel>
                            <StatNumber>
                              {analyticsData.length > 0 ? 
                                `${(analyticsData[analyticsData.length - 1].productivity_score * 100).toFixed(0)}%` : 
                                'N/A'
                              }
                            </StatNumber>
                          </Stat>
                        </VStack>
                      </CardBody>
                    </Card>
                  </GridItem>
                </Grid>
              </TabPanel>

              {/* Behavior Patterns Tab */}
              <TabPanel>
                <Card bg={cardBg}>
                  <CardHeader>
                    <Heading size="md">行動パターン分析</Heading>
                  </CardHeader>
                  <CardBody>
                    {behaviorPatterns.length > 0 ? renderBehaviorPatterns() : (
                      <Text color="gray.500">行動パターンデータがありません</Text>
                    )}
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Predictive Insights Tab */}
              <TabPanel>
                <Card bg={cardBg}>
                  <CardHeader>
                    <Heading size="md">予測インサイト</Heading>
                  </CardHeader>
                  <CardBody>
                    {predictiveInsights.length > 0 ? renderPredictiveInsights() : (
                      <Text color="gray.500">予測データがありません</Text>
                    )}
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Performance Tab */}
              <TabPanel>
                <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={4}>
                  {performanceMetrics.map((metric, index) => (
                    <Card key={index} bg={cardBg}>
                      <CardBody>
                        <VStack align="stretch" spacing={3}>
                          <HStack justify="space-between">
                            <Text fontWeight="bold">{metric.name}</Text>
                            {renderStatusBadge(metric.status)}
                          </HStack>
                          <Progress 
                            value={(metric.current_value / metric.target_value) * 100}
                            colorScheme={
                              metric.status === 'excellent' ? 'green' :
                              metric.status === 'good' ? 'blue' :
                              metric.status === 'fair' ? 'yellow' :
                              metric.status === 'poor' ? 'orange' : 'red'
                            }
                          />
                          <HStack justify="space-between" fontSize="sm">
                            <Text>現在: {metric.current_value.toFixed(1)}</Text>
                            <Text color="gray.500">目標: {metric.target_value}</Text>
                          </HStack>
                        </VStack>
                      </CardBody>
                    </Card>
                  ))}
                </Grid>
              </TabPanel>
            </TabPanels>
          </Tabs>
        )}
      </VStack>
    </Box>
  );
}; 