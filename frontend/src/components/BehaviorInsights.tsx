import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Badge,
  Progress,
  Alert,
  AlertIcon,
  Button,
  Select,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Divider,
  List,
  ListItem,
  ListIcon,
  useToast,
  Grid,
  Skeleton,
  SkeletonText
} from '@chakra-ui/react';
import { useEffect, useState, useCallback } from 'react';
import { 
  FaChartLine, 
  FaLightbulb, 
  FaEye,
  FaExclamationTriangle,
  FaCheckCircle
} from 'react-icons/fa';

interface BehaviorInsightsProps {
  refreshInterval?: number; // リフレッシュ間隔（秒）
  onNavigate?: (view: string) => void; // ナビゲーション関数
}

interface BehaviorTrend {
  timeframe: string;
  period_start?: string;
  period_end?: string;
  total_logs: number;
  focus_analysis?: {
    average_focus?: number;
    trend_direction?: 'up' | 'down' | 'stable';
    trend_percentage?: number;
    good_posture_percentage?: number;
    presence_rate?: number;
    smartphone_usage_rate?: number;
    total_sessions?: number;
  };
  anomalies?: unknown[];
  trend_summary?: unknown;
  message?: string;
  period_hours?: number;
  logs_count?: number;
}

interface DailyInsight {
  target_date: string;
  logs_analyzed?: number;
  insights?: {
    focus_score?: number;
    productivity_score?: number;
    key_findings?: string[];
    improvement_areas?: string[];
  };
  summary?: {
    summary?: string;
  };
  message?: string;
  recommendations?: unknown[];
}

interface Recommendation {
  type: string;
  priority: 'high' | 'medium' | 'low';
  message: string;
  emotion: string;
  source: string;
  timestamp: string;
}

interface BehaviorSummary {
  today?: {
    total_time?: number;
    focus_time?: number;
    break_time?: number;
    absence_time?: number;
    smartphone_usage_time?: number;
    posture_alerts?: number;
  };
  yesterday?: {
    total_time?: number;
    focus_time?: number;
    break_time?: number;
    absence_time?: number;
    smartphone_usage_time?: number;
    posture_alerts?: number;
  };
}

export const BehaviorInsights: React.FC<BehaviorInsightsProps> = ({
  refreshInterval = 30,
  onNavigate
}) => {
  // 分析データ状態
  const [behaviorTrends, setBehaviorTrends] = useState<BehaviorTrend | null>(null);
  const [dailyInsights, setDailyInsights] = useState<DailyInsight | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [behaviorSummary, setBehaviorSummary] = useState<BehaviorSummary | null>(null);

  // UI状態
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('today'); // today, week, month
  const [priorityFilter, setPriorityFilter] = useState('all'); // all, high, medium, low
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const toast = useToast();

  // 行動トレンドデータを取得
  const fetchBehaviorTrends = useCallback(async (selectedTimeframe: string) => {
    try {
      // フロントエンドの表示値をAPIパラメータにマッピング
      const timeframeMapping: { [key: string]: string } = {
        'today': 'daily',
        'week': 'weekly', 
        'month': 'weekly' // 月次は現在のAPIでは週次で代用
      };
      
      const apiTimeframe = timeframeMapping[selectedTimeframe] || 'daily';
      
      const response = await fetch(`/api/analysis/trends?timeframe=${apiTimeframe}`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setBehaviorTrends(data.data || null);
        }
      }
    } catch (error) {
      console.error('Failed to fetch behavior trends:', error);
    }
  }, []);

  // 今日の洞察を取得
  const fetchDailyInsights = useCallback(async () => {
    try {
      const response = await fetch('/api/analysis/insights');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setDailyInsights(data.data || null);
        }
      }
    } catch (error) {
      console.error('Failed to fetch daily insights:', error);
    }
  }, []);

  // 推奨事項を取得
  const fetchRecommendations = useCallback(async (priority: string) => {
    try {
      const url = priority === 'all' 
        ? '/api/analysis/recommendations'
        : `/api/analysis/recommendations?priority=${priority}`;
        
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setRecommendations(data.data?.recommendations || []);
        }
      }
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    }
  }, []);

  // 行動サマリーを取得
  const fetchBehaviorSummary = useCallback(async () => {
    try {
      const response = await fetch('/api/behavior/summary?detailed=true');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setBehaviorSummary(data.data || null);
        }
      }
    } catch (error) {
      console.error('Failed to fetch behavior summary:', error);
    }
  }, []);

  // 全データ更新
  const refreshAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchBehaviorTrends(timeframe),
        fetchDailyInsights(),
        fetchRecommendations(priorityFilter),
        fetchBehaviorSummary()
      ]);
      setLastUpdated(new Date());
    } catch {
      toast({
        title: 'データ更新エラー',
        description: 'データの更新に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  }, [timeframe, priorityFilter, fetchBehaviorTrends, fetchDailyInsights, fetchRecommendations, fetchBehaviorSummary, toast]);

  // 初期化とリフレッシュ
  useEffect(() => {
    refreshAllData();
    
    const interval = setInterval(refreshAllData, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshAllData, refreshInterval]);

  // 時間枠変更ハンドラ
  const handleTimeframeChange = useCallback((newTimeframe: string) => {
    setTimeframe(newTimeframe);
    fetchBehaviorTrends(newTimeframe);
  }, [fetchBehaviorTrends]);

  // 優先度フィルタ変更ハンドラ
  const handlePriorityFilterChange = useCallback((newPriority: string) => {
    setPriorityFilter(newPriority);
    fetchRecommendations(newPriority);
  }, [fetchRecommendations]);

  // 時間をフォーマット
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}時間${minutes}分`;
  };

  // パーセンテージをフォーマット
  const formatPercentage = (value: number): string => {
    return `${Math.round(value * 100)}%`;
  };

  // トレンド方向のアイコンとカラーを取得
  const getTrendDisplay = (direction: 'up' | 'down' | 'stable', percentage: number) => {
    switch (direction) {
      case 'up':
        return {
          icon: <StatArrow type="increase" />,
          color: 'green',
          text: `+${percentage.toFixed(1)}%`
        };
      case 'down':
        return {
          icon: <StatArrow type="decrease" />,
          color: 'red',
          text: `-${percentage.toFixed(1)}%`
        };
      default:
        return {
          icon: null,
          color: 'gray',
          text: '変化なし'
        };
    }
  };

  return (
    <Box width="100%" maxWidth="1200px" mx="auto">
      <VStack spacing={6} align="stretch">
        {/* ヘッダー */}
        <Card>
          <CardHeader>
            <HStack justify="space-between" align="center">
              <Heading size="md">行動分析インサイト</Heading>
              <HStack spacing={4}>
                <Select
                  value={timeframe}
                  onChange={(e) => handleTimeframeChange(e.target.value)}
                  size="sm"
                  width="120px"
                >
                  <option value="today">今日</option>
                  <option value="week">今週</option>
                  <option value="month">今月</option>
                </Select>
                <Button onClick={refreshAllData} size="sm" isLoading={loading}>
                  更新
                </Button>
                {lastUpdated && (
                  <Text fontSize="xs" color="gray.500">
                    最終更新: {lastUpdated.toLocaleTimeString()}
                  </Text>
                )}
              </HStack>
            </HStack>
          </CardHeader>
        </Card>

        {/* サマリー統計 */}
        <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
          {loading ? (
            Array.from({ length: 4 }).map((_, index) => (
              <Card key={index}>
                <CardBody>
                  <Skeleton height="60px" />
                </CardBody>
              </Card>
            ))
          ) : behaviorSummary ? (
            <>
              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>今日の集中時間</StatLabel>
                    <StatNumber>{formatTime(behaviorSummary.today?.focus_time ?? 0)}</StatNumber>
                    <StatHelpText>
                      {(behaviorSummary.today?.focus_time ?? 0) > (behaviorSummary.yesterday?.focus_time ?? 0) ? (
                        <StatArrow type="increase" />
                      ) : (
                        <StatArrow type="decrease" />
                      )}
                      前日比: {formatTime(Math.abs((behaviorSummary.today?.focus_time ?? 0) - (behaviorSummary.yesterday?.focus_time ?? 0)))}
                    </StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              
              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>在席率</StatLabel>
                    <StatNumber>
                      {formatPercentage(
                        (behaviorSummary.today?.total_time ?? 0) > 0
                          ? ((behaviorSummary.today?.total_time ?? 0) - (behaviorSummary.today?.absence_time ?? 0)) / (behaviorSummary.today?.total_time ?? 0)
                          : 0
                      )}
                    </StatNumber>
                    <StatHelpText>
                      不在時間: {formatTime(behaviorSummary.today?.absence_time ?? 0)}
                    </StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              
              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>スマホ使用時間</StatLabel>
                    <StatNumber>{formatTime(behaviorSummary.today?.smartphone_usage_time ?? 0)}</StatNumber>
                    <StatHelpText>
                      {(behaviorSummary.today?.smartphone_usage_time ?? 0) < (behaviorSummary.yesterday?.smartphone_usage_time ?? 0) ? (
                        <StatArrow type="decrease" />
                      ) : (
                        <StatArrow type="increase" />
                      )}
                      前日比: {formatTime(Math.abs((behaviorSummary.today?.smartphone_usage_time ?? 0) - (behaviorSummary.yesterday?.smartphone_usage_time ?? 0)))}
                    </StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              
              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel>姿勢アラート</StatLabel>
                    <StatNumber>{behaviorSummary.today?.posture_alerts ?? 0}回</StatNumber>
                    <StatHelpText>
                      {(behaviorSummary.today?.posture_alerts ?? 0) < (behaviorSummary.yesterday?.posture_alerts ?? 0) ? (
                        <StatArrow type="decrease" />
                      ) : (
                        <StatArrow type="increase" />
                      )}
                      前日: {behaviorSummary.yesterday?.posture_alerts ?? 0}回
                    </StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </>
          ) : (
            <Card gridColumn="1 / -1">
              <CardBody>
                <Alert status="info">
                  <AlertIcon />
                  データが不足しています。しばらく使用してからご確認ください。
                </Alert>
              </CardBody>
            </Card>
          )}
        </Grid>

        {/* 行動トレンド */}
        <Card>
          <CardHeader>
            <HStack>
              <FaChartLine />
              <Heading size="sm">行動トレンド</Heading>
            </HStack>
          </CardHeader>
          <CardBody>
            {loading ? (
              <SkeletonText noOfLines={4} spacing="4" />
            ) : behaviorTrends ? (
              <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={6}>
                <Box>
                  <Text fontWeight="bold" mb={2}>集中度トレンド</Text>
                  <HStack justify="space-between">
                    <Text>平均集中度:</Text>
                    <HStack>
                      <Badge colorScheme="blue">
                        {formatPercentage(behaviorTrends.focus_analysis?.average_focus || 0)}
                      </Badge>
                      {(() => {
                        const trend = getTrendDisplay(
                          behaviorTrends.focus_analysis?.trend_direction || 'stable',
                          behaviorTrends.focus_analysis?.trend_percentage || 0
                        );
                        return (
                          <HStack color={trend.color}>
                            {trend.icon}
                            <Text fontSize="sm">{trend.text}</Text>
                          </HStack>
                        );
                      })()}
                    </HStack>
                  </HStack>
                </Box>

                <Box>
                  <Text fontWeight="bold" mb={2}>姿勢トレンド</Text>
                  <HStack justify="space-between">
                    <Text>良い姿勢:</Text>
                    <HStack>
                      <Badge colorScheme="green">
                        {formatPercentage(behaviorTrends.focus_analysis?.good_posture_percentage || 0)}
                      </Badge>
                      {(() => {
                        const trend = getTrendDisplay(
                          behaviorTrends.focus_analysis?.trend_direction || 'stable',
                          0 // 姿勢の変化率は別途計算が必要
                        );
                        return (
                          <HStack color={trend.color}>
                            {trend.icon}
                          </HStack>
                        );
                      })()}
                    </HStack>
                  </HStack>
                </Box>

                <Box>
                  <Text fontWeight="bold" mb={2}>活動状況</Text>
                  <VStack spacing={1} align="stretch" fontSize="sm">
                    <HStack justify="space-between">
                      <Text>在席率:</Text>
                      <Badge>{formatPercentage(behaviorTrends.focus_analysis?.presence_rate || 0)}</Badge>
                    </HStack>
                    <HStack justify="space-between">
                      <Text>スマホ使用率:</Text>
                      <Badge colorScheme="orange">
                        {formatPercentage(behaviorTrends.focus_analysis?.smartphone_usage_rate || 0)}
                      </Badge>
                    </HStack>
                    <HStack justify="space-between">
                      <Text>セッション数:</Text>
                      <Badge colorScheme="purple">
                        {behaviorTrends.focus_analysis?.total_sessions || 0}回
                      </Badge>
                    </HStack>
                  </VStack>
                </Box>
              </Grid>
            ) : (
              <Alert status="info">
                <AlertIcon />
                トレンドデータが不足しています
              </Alert>
            )}
          </CardBody>
        </Card>

        {/* 今日の洞察 */}
        <Card>
          <CardHeader>
            <HStack>
              <FaLightbulb />
              <Heading size="sm">今日の洞察</Heading>
            </HStack>
          </CardHeader>
          <CardBody>
            {loading ? (
              <SkeletonText noOfLines={6} spacing="4" />
            ) : dailyInsights ? (
              <VStack spacing={4} align="stretch">
                <Text>{dailyInsights.summary?.summary || ''}</Text>
                
                <Divider />
                
                <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
                  <Box>
                    <Text fontWeight="bold" mb={2}>集中スコア</Text>
                    <Progress 
                      value={(dailyInsights.insights?.focus_score ?? 0) * 100} 
                      colorScheme="blue" 
                      size="lg"
                    />
                    <Text fontSize="sm" color="gray.600">
                      {Math.round((dailyInsights.insights?.focus_score ?? 0) * 100)}/100
                    </Text>
                  </Box>
                  
                  <Box>
                    <Text fontWeight="bold" mb={2}>生産性スコア</Text>
                    <Progress 
                      value={(dailyInsights.insights?.productivity_score ?? 0) * 100} 
                      colorScheme="green" 
                      size="lg"
                    />
                    <Text fontSize="sm" color="gray.600">
                      {Math.round((dailyInsights.insights?.productivity_score ?? 0) * 100)}/100
                    </Text>
                  </Box>
                </Grid>
                
                {(dailyInsights.insights?.key_findings?.length ?? 0) > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Text fontWeight="bold" mb={2}>主な発見</Text>
                      <List spacing={1}>
                        {(dailyInsights.insights?.key_findings ?? []).map((finding: string, index: number) => (
                          <ListItem key={index}>
                            <ListIcon as={FaEye} color="blue.500" />
                            <Text as="span">{finding}</Text>
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  </>
                )}
                
                {(dailyInsights.insights?.improvement_areas?.length ?? 0) > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Text fontWeight="bold" mb={2}>改善領域</Text>
                      <List spacing={1}>
                        {(dailyInsights.insights?.improvement_areas ?? []).map((area: string, index: number) => (
                          <ListItem key={index}>
                            <ListIcon as={FaExclamationTriangle} color="orange.500" />
                            <Text as="span">{area}</Text>
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  </>
                )}
              </VStack>
            ) : (
              <Alert status="info">
                <AlertIcon />
                十分なデータが蓄積されていません。継続的な使用で洞察が生成されます。
              </Alert>
            )}
          </CardBody>
        </Card>

        {/* 改善提案 */}
        <Card>
          <CardHeader>
            <HStack justify="space-between" align="center">
              <HStack>
                <FaCheckCircle />
                <Heading size="sm">改善提案</Heading>
              </HStack>
              <Select
                value={priorityFilter}
                onChange={(e) => handlePriorityFilterChange(e.target.value)}
                size="sm"
                width="120px"
              >
                <option value="all">すべて</option>
                <option value="high">重要</option>
                <option value="medium">普通</option>
                <option value="low">軽微</option>
              </Select>
            </HStack>
          </CardHeader>
          <CardBody>
            {loading ? (
              <SkeletonText noOfLines={4} spacing="4" />
            ) : recommendations.length > 0 ? (
              <VStack spacing={3} align="stretch">
                {recommendations.map((rec, index) => (
                  <Alert 
                    key={index}
                    status={rec.priority === 'high' ? 'warning' : rec.priority === 'medium' ? 'info' : 'success'}
                    variant="left-accent"
                  >
                    <AlertIcon />
                    <Box flex="1">
                      <Text fontSize="sm">{rec.message}</Text>
                      <Text fontSize="xs" color="gray.500" mt={1}>
                        {rec.source} • {new Date(rec.timestamp).toLocaleString()}
                      </Text>
                    </Box>
                    <Badge colorScheme={rec.priority === 'high' ? 'red' : rec.priority === 'medium' ? 'orange' : 'green'}>
                      {rec.priority === 'high' ? '重要' : rec.priority === 'medium' ? '普通' : '軽微'}
                            </Badge>
                  </Alert>
                ))}
              </VStack>
            ) : (
              <Alert status="info">
                <AlertIcon />
                現在利用可能な改善提案はありません
              </Alert>
            )}
          </CardBody>
        </Card>

        {/* 高度分析リンク */}
        <Card>
          <CardHeader>
            <Heading size="sm">🚀 高度分析機能</Heading>
          </CardHeader>
          <CardBody>
            <Text mb={4} color="gray.600">
              より詳細な分析機能を利用できます：
            </Text>
            <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
              <Button 
                leftIcon={<FaChartLine />}
                colorScheme="blue" 
                variant="outline"
                onClick={() => {
                  if (onNavigate) {
                    onNavigate('analytics');
                  } else {
                    // Tab構造での使用時の代替処理
                    alert('統合ダッシュボード機能はIntegratedDashboard使用時のみ利用可能です。');
                  }
                }}
                size="sm"
              >
                高度分析ダッシュボード
              </Button>
              <Button 
                leftIcon={<FaLightbulb />}
                colorScheme="purple" 
                variant="outline"
                onClick={() => {
                  if (onNavigate) {
                    onNavigate('personalization');
                  } else {
                    alert('統合ダッシュボード機能はIntegratedDashboard使用時のみ利用可能です。');
                  }
                }}
                size="sm"
              >
                パーソナライゼーション
              </Button>
              <Button 
                leftIcon={<FaEye />}
                colorScheme="green" 
                variant="outline"
                onClick={() => {
                  if (onNavigate) {
                    onNavigate('predictions');
                  } else {
                    alert('統合ダッシュボード機能はIntegratedDashboard使用時のみ利用可能です。');
                  }
                }}
                size="sm"
              >
                予測インサイト
              </Button>
              <Button 
                leftIcon={<FaCheckCircle />}
                colorScheme="orange" 
                variant="outline"
                onClick={() => {
                  if (onNavigate) {
                    onNavigate('learning');
                  } else {
                    alert('統合ダッシュボード機能はIntegratedDashboard使用時のみ利用可能です。');
                  }
                }}
                size="sm"
              >
                学習進捗
              </Button>
            </Grid>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
}; 