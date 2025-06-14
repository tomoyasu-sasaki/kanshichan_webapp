import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
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
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  SimpleGrid,
  Tag,
  TagLabel,
  Circle
} from '@chakra-ui/react';
import { 
  FiTrendingUp, 
  FiTrendingDown, 
  FiActivity, 
  FiClock, 
  FiEye, 
  FiUser,
  FiTarget,
  FiZap
} from 'react-icons/fi';

interface PredictionData {
  metric: string;
  current_value: number;
  predicted_value: number;
  confidence: number;
  trend: 'increasing' | 'decreasing' | 'stable';
  prediction_horizon_hours: number;
  factors_influencing: string[];
  recommendations: string[];
}

interface TrendAnalysis {
  period: string;
  trend_strength: number;
  trend_direction: 'up' | 'down' | 'stable';
  seasonal_patterns: string[];
  anomalies_detected: number;
}

interface FutureScenario {
  scenario_name: string;
  probability: number;
  expected_outcomes: {
    focus_score: number;
    productivity_score: number;
    health_score: number;
  };
  key_factors: string[];
  preventive_actions: string[];
}

interface PredictiveInsightsProps {
  userId?: string;
  predictionHorizon?: number; // hours
}

// API ベース URL（バックエンド Flask サーバ）
const API_BASE_URL = 'http://localhost:8000/api';

export const PredictiveInsights: React.FC<PredictiveInsightsProps> = ({
  userId = 'default',
  predictionHorizon = 24
}) => {
  // State management
  const [predictions, setPredictions] = useState<PredictionData[]>([]);
  const [trendAnalysis, setTrendAnalysis] = useState<TrendAnalysis[]>([]);
  const [futureScenarios, setFutureScenarios] = useState<FutureScenario[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedHorizon, setSelectedHorizon] = useState(predictionHorizon);

  // UI theming
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const toast = useToast();

  // Data fetching
  const fetchPredictions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch predictions
      const predictionsResponse = await fetch(
        `${API_BASE_URL}/analysis/predictions?user_id=${userId}&metrics=focus_score,productivity_score,fatigue_level,posture_score&horizon=${selectedHorizon}`
      );
      if (!predictionsResponse.ok) throw new Error('Failed to fetch predictions');
      const predictionsData = await predictionsResponse.json();

      // Fetch advanced patterns for trend analysis
      const patternsResponse = await fetch(
        `${API_BASE_URL}/analysis/advanced-patterns?user_id=${userId}&timeframe=weekly`
      );
      if (!patternsResponse.ok) throw new Error('Failed to fetch patterns');
      const patternsData = await patternsResponse.json();

      // Process data
      setPredictions(predictionsData.predictions || []);
      setTrendAnalysis(processTrendAnalysis(patternsData));
      setFutureScenarios(generateFutureScenarios(predictionsData.predictions || []));

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      toast({
        title: '予測データ取得エラー',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  }, [userId, selectedHorizon, toast]);

  // Process trend analysis data
  const processTrendAnalysis = (patternsData: {
    patterns?: {
      timeseries_analysis?: {
        trend_strength?: number;
        trend_direction?: 'up' | 'down' | 'stable';
        seasonal_patterns?: string[];
        anomalies_count?: number;
      };
    };
  }): TrendAnalysis[] => {
    const timeseries = patternsData.patterns?.timeseries_analysis || {};
    
    return [
      {
        period: '1週間',
        trend_strength: timeseries.trend_strength || 0.5,
        trend_direction: timeseries.trend_direction || 'stable',
        seasonal_patterns: timeseries.seasonal_patterns || [],
        anomalies_detected: timeseries.anomalies_count || 0
      }
    ];
  };

  // Generate future scenarios
  const generateFutureScenarios = (predictions: PredictionData[]): FutureScenario[] => {
    if (!predictions.length) return [];

    const avgConfidence = predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length;
    
    return [
      {
        scenario_name: '現在のペース継続',
        probability: avgConfidence,
        expected_outcomes: {
          focus_score: predictions.find(p => p.metric === 'focus_score')?.predicted_value || 0.7,
          productivity_score: predictions.find(p => p.metric === 'productivity_score')?.predicted_value || 0.75,
          health_score: predictions.find(p => p.metric === 'posture_score')?.predicted_value || 0.8
        },
        key_factors: ['現在の作業パターン継続', '環境変化なし'],
        preventive_actions: ['定期的な休憩の維持', '姿勢チェックの継続']
      },
      {
        scenario_name: '改善施策実行',
        probability: 0.8,
        expected_outcomes: {
          focus_score: Math.min((predictions.find(p => p.metric === 'focus_score')?.predicted_value || 0.7) + 0.15, 1.0),
          productivity_score: Math.min((predictions.find(p => p.metric === 'productivity_score')?.predicted_value || 0.75) + 0.1, 1.0),
          health_score: Math.min((predictions.find(p => p.metric === 'posture_score')?.predicted_value || 0.8) + 0.1, 1.0)
        },
        key_factors: ['推奨事項の実行', '生活習慣の改善'],
        preventive_actions: ['新しい休憩パターンの実践', '作業環境の最適化']
      }
    ];
  };

  // Initial data fetch
  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  // Render metric icon
  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'focus_score': return FiEye;
      case 'productivity_score': return FiTarget;
      case 'fatigue_level': return FiActivity;
      case 'posture_score': return FiUser;
      default: return FiTarget;
    }
  };

  // Render metric name
  const getMetricName = (metric: string) => {
    switch (metric) {
      case 'focus_score': return '集中度';
      case 'productivity_score': return '生産性';
      case 'fatigue_level': return '疲労度';
      case 'posture_score': return '姿勢スコア';
      default: return metric;
    }
  };

  // Render trend direction
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing': return FiTrendingUp;
      case 'decreasing': return FiTrendingDown;
      default: return FiActivity;
    }
  };

  // Render trend color
  const getTrendColor = (trend: string, isPositiveMetric: boolean = true) => {
    if (trend === 'stable') return 'gray';
    
    if (isPositiveMetric) {
      return trend === 'increasing' ? 'green' : 'red';
    } else {
      return trend === 'increasing' ? 'red' : 'green';
    }
  };

  // Render predictions
  const renderPredictions = () => (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
      {predictions.map((prediction, index) => {
        const isPositiveMetric = prediction.metric !== 'fatigue_level';
        const trendColor = getTrendColor(prediction.trend, isPositiveMetric);
        
        return (
          <Card key={index} bg={cardBg}>
            <CardBody>
              <VStack spacing={3} align="stretch">
                <HStack justify="space-between">
                  <HStack>
                    <Icon as={getMetricIcon(prediction.metric)} color="blue.500" />
                    <Text fontWeight="bold" fontSize="sm">
                      {getMetricName(prediction.metric)}
                    </Text>
                  </HStack>
                  <Icon as={getTrendIcon(prediction.trend)} color={`${trendColor}.500`} />
                </HStack>

                <Box>
                  <HStack justify="space-between" mb={2}>
                    <Text fontSize="xs" color="gray.500">現在</Text>
                    <Text fontSize="xs" color="gray.500">予測</Text>
                  </HStack>
                  <HStack justify="space-between" mb={2}>
                    <Text fontWeight="bold">
                      {(prediction.current_value * 100).toFixed(0)}%
                    </Text>
                    <Text fontWeight="bold" color={`${trendColor}.500`}>
                      {(prediction.predicted_value * 100).toFixed(0)}%
                    </Text>
                  </HStack>
                  <Progress 
                    value={prediction.predicted_value * 100}
                    colorScheme={trendColor}
                    size="sm"
                  />
                </Box>

                <Box>
                  <Text fontSize="xs" color="gray.500" mb={1}>
                    信頼度: {(prediction.confidence * 100).toFixed(0)}%
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    予測期間: {prediction.prediction_horizon_hours}時間後
                  </Text>
                </Box>

                {prediction.factors_influencing.length > 0 && (
                  <Box>
                    <Text fontSize="xs" fontWeight="bold" mb={1}>影響要因:</Text>
                    <HStack wrap="wrap">
                      {prediction.factors_influencing.slice(0, 2).map((factor, idx) => (
                        <Tag key={idx} size="xs" colorScheme="blue" variant="outline">
                          <TagLabel>{factor}</TagLabel>
                        </Tag>
                      ))}
                    </HStack>
                  </Box>
                )}
              </VStack>
            </CardBody>
          </Card>
        );
      })}
    </SimpleGrid>
  );

  // Render trend analysis
  const renderTrendAnalysis = () => (
    <Card bg={cardBg}>
      <CardHeader>
        <HStack>
          <Icon as={FiActivity} />
          <Heading size="md">トレンド分析</Heading>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {trendAnalysis.map((trend, index) => (
            <Box key={index}>
              <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                <Stat>
                  <StatLabel>期間</StatLabel>
                  <StatNumber fontSize="lg">{trend.period}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>トレンド強度</StatLabel>
                  <StatNumber fontSize="lg">
                    {(trend.trend_strength * 100).toFixed(0)}%
                  </StatNumber>
                  <StatHelpText>
                    <StatArrow type={trend.trend_direction === 'up' ? 'increase' : 'decrease'} />
                    {trend.trend_direction === 'up' ? '上昇' : trend.trend_direction === 'down' ? '下降' : '安定'}
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>異常検出</StatLabel>
                  <StatNumber fontSize="lg">{trend.anomalies_detected}件</StatNumber>
                  <StatHelpText>
                    {trend.anomalies_detected === 0 ? '正常' : '要注意'}
                  </StatHelpText>
                </Stat>
              </SimpleGrid>

              {trend.seasonal_patterns.length > 0 && (
                <Box mt={4}>
                  <Text fontWeight="bold" mb={2}>季節パターン:</Text>
                  <HStack wrap="wrap">
                    {trend.seasonal_patterns.map((pattern, idx) => (
                      <Tag key={idx} colorScheme="purple" variant="outline">
                        <TagLabel>{pattern}</TagLabel>
                      </Tag>
                    ))}
                  </HStack>
                </Box>
              )}
            </Box>
          ))}
        </VStack>
      </CardBody>
    </Card>
  );

  // Render future scenarios
  const renderFutureScenarios = () => (
    <Card bg={cardBg}>
      <CardHeader>
        <HStack>
          <Icon as={FiZap} />
          <Heading size="md">将来シナリオ</Heading>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={6} align="stretch">
          {futureScenarios.map((scenario, index) => (
            <Box key={index} p={4} borderWidth={1} borderRadius="md">
              <VStack spacing={4} align="stretch">
                <HStack justify="space-between">
                  <Text fontWeight="bold" fontSize="lg">{scenario.scenario_name}</Text>
                  <Badge 
                    colorScheme={scenario.probability > 0.8 ? 'green' : scenario.probability > 0.6 ? 'yellow' : 'orange'}
                    size="lg"
                  >
                    {(scenario.probability * 100).toFixed(0)}%
                  </Badge>
                </HStack>

                <SimpleGrid columns={3} spacing={4}>
                  <Box textAlign="center">
                    <Circle size="60px" bg="blue.100" color="blue.500" mx="auto" mb={2}>
                      <Text fontWeight="bold">
                        {(scenario.expected_outcomes.focus_score * 100).toFixed(0)}
                      </Text>
                    </Circle>
                    <Text fontSize="sm">集中度</Text>
                  </Box>
                  <Box textAlign="center">
                    <Circle size="60px" bg="green.100" color="green.500" mx="auto" mb={2}>
                      <Text fontWeight="bold">
                        {(scenario.expected_outcomes.productivity_score * 100).toFixed(0)}
                      </Text>
                    </Circle>
                    <Text fontSize="sm">生産性</Text>
                  </Box>
                  <Box textAlign="center">
                    <Circle size="60px" bg="purple.100" color="purple.500" mx="auto" mb={2}>
                      <Text fontWeight="bold">
                        {(scenario.expected_outcomes.health_score * 100).toFixed(0)}
                      </Text>
                    </Circle>
                    <Text fontSize="sm">健康スコア</Text>
                  </Box>
                </SimpleGrid>

                <Divider />

                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <Box>
                    <Text fontWeight="bold" fontSize="sm" mb={2}>主要要因:</Text>
                    <VStack align="start" spacing={1}>
                      {scenario.key_factors.map((factor, idx) => (
                        <Text key={idx} fontSize="sm" color="gray.600">
                          • {factor}
                        </Text>
                      ))}
                    </VStack>
                  </Box>
                  <Box>
                    <Text fontWeight="bold" fontSize="sm" mb={2}>推奨アクション:</Text>
                    <VStack align="start" spacing={1}>
                      {scenario.preventive_actions.map((action, idx) => (
                        <Text key={idx} fontSize="sm" color="green.600">
                          • {action}
                        </Text>
                      ))}
                    </VStack>
                  </Box>
                </SimpleGrid>
              </VStack>
            </Box>
          ))}
        </VStack>
      </CardBody>
    </Card>
  );

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        <AlertTitle>予測データ取得エラー</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <Box bg={bgColor} minH="100vh" p={6}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between" align="center">
          <Heading size="lg">予測インサイト</Heading>
          <HStack spacing={4}>
            <Select 
              value={selectedHorizon}
              onChange={(e) => setSelectedHorizon(Number(e.target.value))}
              size="sm"
              w="auto"
            >
              <option value={1}>1時間後</option>
              <option value={4}>4時間後</option>
              <option value={8}>8時間後</option>
              <option value={24}>24時間後</option>
              <option value={72}>3日後</option>
            </Select>
            <Button
              leftIcon={<Icon as={FiClock} />}
              onClick={fetchPredictions}
              isLoading={isLoading}
              size="sm"
            >
              更新
            </Button>
          </HStack>
        </HStack>

        {isLoading && (
          <HStack justify="center" py={8}>
            <Spinner size="lg" />
            <Text>予測データを分析中...</Text>
          </HStack>
        )}

        {!isLoading && (
          <VStack spacing={6} align="stretch">
            {/* Predictions */}
            <Box>
              <Heading size="md" mb={4}>メトリクス予測</Heading>
              {renderPredictions()}
            </Box>

            {/* Trend Analysis */}
            {renderTrendAnalysis()}

            {/* Future Scenarios */}
            {renderFutureScenarios()}
          </VStack>
        )}
      </VStack>
    </Box>
  );
}; 