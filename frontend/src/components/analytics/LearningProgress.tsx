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
  Progress,
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
  SimpleGrid,
  Tag,
  TagLabel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer
} from '@chakra-ui/react';
import { 
  FiTarget, 
  FiActivity, 
  FiAward,
  FiBarChart,
  FiRefreshCw,
  FiTrendingUp,
  FiTrendingDown
} from 'react-icons/fi';

interface LearningMetric {
  metric_name: string;
  current_value: number;
  baseline_value: number;
  improvement_percentage: number;
  trend: 'improving' | 'stable' | 'declining';
  last_updated: string;
}

interface LearningMilestone {
  milestone_id: string;
  title: string;
  description: string;
  target_date: string;
  completion_percentage: number;
  status: 'completed' | 'in_progress' | 'pending';
  achievements: string[];
}

interface ABTestResult {
  test_id: string;
  test_name: string;
  start_date: string;
  end_date: string;
  variant_a: {
    name: string;
    performance_score: number;
    user_satisfaction: number;
  };
  variant_b: {
    name: string;
    performance_score: number;
    user_satisfaction: number;
  };
  winner: 'a' | 'b' | 'no_difference';
  confidence_level: number;
}

interface ModelPerformance {
  model_name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  training_date: string;
  data_points_used: number;
}

interface LearningProgressProps {
  userId?: string;
}

export const LearningProgress: React.FC<LearningProgressProps> = ({
  userId = 'default'
}) => {
  // State management
  const [learningMetrics, setLearningMetrics] = useState<LearningMetric[]>([]);
  const [milestones, setMilestones] = useState<LearningMilestone[]>([]);
  const [abTestResults, setAbTestResults] = useState<ABTestResult[]>([]);
  const [modelPerformance, setModelPerformance] = useState<ModelPerformance[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // UI theming
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const toast = useToast();

  // Data fetching
  const fetchLearningData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch adaptive learning status
      const learningResponse = await fetch(`/api/v1/analysis/adaptive-learning-status?user_id=${userId}`);
      if (!learningResponse.ok) throw new Error('Failed to fetch learning status');
      const learningData = await learningResponse.json();

      // Process learning data
      setLearningMetrics(generateLearningMetrics(learningData?.data || learningData));
      setMilestones(generateMilestones());
      setAbTestResults(generateABTestResults());
      setModelPerformance(generateModelPerformance());

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      toast({
        title: '学習データ取得エラー',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  }, [userId, toast]);

  // Generate learning metrics
  const generateLearningMetrics = (data: { 
    learning_status?: {
      model_accuracy?: number;
      user_satisfaction_avg?: number;
      adaptation_count?: number;
    } 
  }): LearningMetric[] => {
    const learningStatus = data.learning_status || {};
    
    return [
      {
        metric_name: '推奨精度',
        current_value: learningStatus.model_accuracy || 0.85,
        baseline_value: 0.7,
        improvement_percentage: ((learningStatus.model_accuracy || 0.85) - 0.7) / 0.7 * 100,
        trend: 'improving',
        last_updated: new Date().toISOString()
      },
      {
        metric_name: 'ユーザー満足度',
        current_value: learningStatus.user_satisfaction_avg || 4.2,
        baseline_value: 3.5,
        improvement_percentage: ((learningStatus.user_satisfaction_avg || 4.2) - 3.5) / 3.5 * 100,
        trend: 'improving',
        last_updated: new Date().toISOString()
      },
      {
        metric_name: '適応速度',
        current_value: learningStatus.adaptation_count || 15,
        baseline_value: 10,
        improvement_percentage: ((learningStatus.adaptation_count || 15) - 10) / 10 * 100,
        trend: 'stable',
        last_updated: new Date().toISOString()
      }
    ];
  };

  // Generate milestones
  const generateMilestones = (): LearningMilestone[] => {
    return [
      {
        milestone_id: 'milestone_1',
        title: '基本パターン学習完了',
        description: 'ユーザーの基本的な行動パターンの学習を完了',
        target_date: '2025-01-15',
        completion_percentage: 100,
        status: 'completed',
        achievements: ['行動パターン認識', 'スケジュール最適化', '基本推奨システム']
      },
      {
        milestone_id: 'milestone_2',
        title: '高度パーソナライゼーション',
        description: '個人別カスタマイズされた推奨システムの実装',
        target_date: '2025-01-30',
        completion_percentage: 75,
        status: 'in_progress',
        achievements: ['コンテキスト認識', '動的推奨調整']
      },
      {
        milestone_id: 'milestone_3',
        title: '予測モデル最適化',
        description: '長期予測精度の向上と信頼度向上',
        target_date: '2025-02-15',
        completion_percentage: 30,
        status: 'in_progress',
        achievements: []
      }
    ];
  };

  // Generate A/B test results
  const generateABTestResults = (): ABTestResult[] => {
    return [
      {
        test_id: 'ab_test_1',
        test_name: '休憩推奨タイミング',
        start_date: '2025-01-01',
        end_date: '2025-01-07',
        variant_a: {
          name: '固定間隔（50分毎）',
          performance_score: 0.72,
          user_satisfaction: 3.8
        },
        variant_b: {
          name: '適応的間隔',
          performance_score: 0.84,
          user_satisfaction: 4.3
        },
        winner: 'b',
        confidence_level: 0.95
      },
      {
        test_id: 'ab_test_2',
        test_name: 'アラート表示方法',
        start_date: '2024-12-20',
        end_date: '2024-12-27',
        variant_a: {
          name: 'ポップアップ',
          performance_score: 0.68,
          user_satisfaction: 3.5
        },
        variant_b: {
          name: 'TTS音声',
          performance_score: 0.79,
          user_satisfaction: 4.1
        },
        winner: 'b',
        confidence_level: 0.89
      }
    ];
  };

  // Generate model performance data
  const generateModelPerformance = (): ModelPerformance[] => {
    return [
      {
        model_name: '集中度予測モデル',
        accuracy: 0.87,
        precision: 0.85,
        recall: 0.89,
        f1_score: 0.87,
        training_date: '2025-01-06',
        data_points_used: 15432
      },
      {
        model_name: 'パーソナライゼーションモデル',
        accuracy: 0.82,
        precision: 0.84,
        recall: 0.80,
        f1_score: 0.82,
        training_date: '2025-01-05',
        data_points_used: 8765
      }
    ];
  };

  // Initial data fetch
  useEffect(() => {
    fetchLearningData();
  }, [fetchLearningData]);

  // Render learning metrics
  const renderLearningMetrics = () => (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
      {learningMetrics.map((metric, index) => (
        <Card key={index} bg={cardBg}>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <HStack justify="space-between">
                <Text fontWeight="bold" fontSize="lg">{metric.metric_name}</Text>
                <Badge colorScheme={
                  metric.trend === 'improving' ? 'green' :
                  metric.trend === 'declining' ? 'red' : 'gray'
                }>
                  {metric.trend === 'improving' ? '改善中' :
                   metric.trend === 'declining' ? '低下中' : '安定'}
                </Badge>
              </HStack>

              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontSize="xs" color="gray.500">現在値</Text>
                  <Text fontSize="2xl" fontWeight="bold">
                    {metric.metric_name === '予測精度' || metric.metric_name === 'モデル適応率' ? 
                      metric.current_value.toFixed(1) : 
                      (metric.current_value * 100).toFixed(0) + '%'
                    }
                  </Text>
                </VStack>
                <VStack align="end" spacing={1}>
                  <Text fontSize="xs" color="gray.500">改善率</Text>
                  <HStack>
                    <Icon 
                      as={metric.improvement_percentage > 0 ? FiTrendingUp : FiTrendingDown} 
                      color={metric.improvement_percentage > 0 ? 'green.500' : 'red.500'}
                    />
                    <Text fontWeight="bold" color={metric.improvement_percentage > 0 ? 'green.500' : 'red.500'}>
                      {Math.abs(metric.improvement_percentage).toFixed(1)}%
                    </Text>
                  </HStack>
                </VStack>
              </HStack>

              <Progress 
                value={(metric.current_value / (metric.metric_name === 'ユーザー満足度' ? 5 : 1)) * 100}
                colorScheme={metric.trend === 'improving' ? 'green' : 'blue'}
                size="sm"
              />

              <Text fontSize="xs" color="gray.500">
                最終更新: {new Date(metric.last_updated).toLocaleDateString('ja-JP')}
              </Text>
            </VStack>
          </CardBody>
        </Card>
      ))}
    </SimpleGrid>
  );

  // Render milestones
  const renderMilestones = () => (
    <Card bg={cardBg}>
      <CardHeader>
        <HStack>
          <Icon as={FiTarget} />
          <Heading size="md">学習マイルストーン</Heading>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {milestones.map((milestone, index) => (
            <Box key={index} p={4} borderWidth={1} borderRadius="md">
              <VStack spacing={3} align="stretch">
                <HStack justify="space-between">
                  <Text fontWeight="bold">{milestone.title}</Text>
                  <Badge colorScheme={
                    milestone.status === 'completed' ? 'green' :
                    milestone.status === 'in_progress' ? 'blue' : 'gray'
                  }>
                    {milestone.status === 'completed' ? '完了' :
                     milestone.status === 'in_progress' ? '進行中' : '待機中'}
                  </Badge>
                </HStack>

                <Text fontSize="sm" color="gray.600">
                  {milestone.description}
                </Text>

                <HStack justify="space-between">
                  <Text fontSize="sm" color="gray.500">
                    目標日: {new Date(milestone.target_date).toLocaleDateString('ja-JP')}
                  </Text>
                  <Text fontSize="sm" fontWeight="bold">
                    {milestone.completion_percentage}%
                  </Text>
                </HStack>

                <Progress 
                  value={milestone.completion_percentage}
                  colorScheme={milestone.status === 'completed' ? 'green' : 'blue'}
                  size="sm"
                />

                {milestone.achievements.length > 0 && (
                  <Box>
                    <Text fontSize="sm" fontWeight="bold" mb={2}>達成項目:</Text>
                    <HStack wrap="wrap">
                      {milestone.achievements.map((achievement, idx) => (
                        <Tag key={idx} size="sm" colorScheme="green">
                          <TagLabel>{achievement}</TagLabel>
                        </Tag>
                      ))}
                    </HStack>
                  </Box>
                )}
              </VStack>
            </Box>
          ))}
        </VStack>
      </CardBody>
    </Card>
  );

  // Render A/B test results
  const renderABTestResults = () => (
    <Card bg={cardBg}>
      <CardHeader>
        <HStack>
          <Icon as={FiBarChart} />
          <Heading size="md">A/Bテスト結果</Heading>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {abTestResults.map((test, index) => (
            <Box key={index} p={4} borderWidth={1} borderRadius="md">
              <VStack spacing={4} align="stretch">
                <HStack justify="space-between">
                  <Text fontWeight="bold">{test.test_name}</Text>
                  <Badge colorScheme="purple">
                    信頼度 {(test.confidence_level * 100).toFixed(0)}%
                  </Badge>
                </HStack>

                <SimpleGrid columns={2} spacing={4}>
                  <Box p={3} borderWidth={1} borderRadius="md" bg={test.winner === 'a' ? 'green.50' : 'gray.50'}>
                    <VStack spacing={2}>
                      <HStack justify="space-between" w="100%">
                        <Text fontWeight="bold" fontSize="sm">バリアント A</Text>
                        {test.winner === 'a' && <Icon as={FiAward} color="green.500" />}
                      </HStack>
                      <Text fontSize="sm">{test.variant_a.name}</Text>
                      <SimpleGrid columns={2} spacing={2} w="100%">
                        <Stat size="sm">
                          <StatLabel fontSize="xs">パフォーマンス</StatLabel>
                          <StatNumber fontSize="sm">{(test.variant_a.performance_score * 100).toFixed(0)}%</StatNumber>
                        </Stat>
                        <Stat size="sm">
                          <StatLabel fontSize="xs">満足度</StatLabel>
                          <StatNumber fontSize="sm">{test.variant_a.user_satisfaction.toFixed(1)}</StatNumber>
                        </Stat>
                      </SimpleGrid>
                    </VStack>
                  </Box>

                  <Box p={3} borderWidth={1} borderRadius="md" bg={test.winner === 'b' ? 'green.50' : 'gray.50'}>
                    <VStack spacing={2}>
                      <HStack justify="space-between" w="100%">
                        <Text fontWeight="bold" fontSize="sm">バリアント B</Text>
                        {test.winner === 'b' && <Icon as={FiAward} color="green.500" />}
                      </HStack>
                      <Text fontSize="sm">{test.variant_b.name}</Text>
                      <SimpleGrid columns={2} spacing={2} w="100%">
                        <Stat size="sm">
                          <StatLabel fontSize="xs">パフォーマンス</StatLabel>
                          <StatNumber fontSize="sm">{(test.variant_b.performance_score * 100).toFixed(0)}%</StatNumber>
                        </Stat>
                        <Stat size="sm">
                          <StatLabel fontSize="xs">満足度</StatLabel>
                          <StatNumber fontSize="sm">{test.variant_b.user_satisfaction.toFixed(1)}</StatNumber>
                        </Stat>
                      </SimpleGrid>
                    </VStack>
                  </Box>
                </SimpleGrid>

                <Text fontSize="xs" color="gray.500">
                  テスト期間: {new Date(test.start_date).toLocaleDateString('ja-JP')} - {new Date(test.end_date).toLocaleDateString('ja-JP')}
                </Text>
              </VStack>
            </Box>
          ))}
        </VStack>
      </CardBody>
    </Card>
  );

  // Render model performance
  const renderModelPerformance = () => (
    <Card bg={cardBg}>
      <CardHeader>
        <HStack>
          <Icon as={FiActivity} />
          <Heading size="md">モデルパフォーマンス</Heading>
        </HStack>
      </CardHeader>
      <CardBody>
        <TableContainer>
          <Table size="sm">
            <Thead>
              <Tr>
                <Th>モデル名</Th>
                <Th>精度</Th>
                <Th>適合率</Th>
                <Th>再現率</Th>
                <Th>F1スコア</Th>
                <Th>学習データ数</Th>
                <Th>更新日</Th>
              </Tr>
            </Thead>
            <Tbody>
              {modelPerformance.map((model, index) => (
                <Tr key={index}>
                  <Td fontWeight="bold">{model.model_name}</Td>
                  <Td>
                    <Badge colorScheme={model.accuracy > 0.85 ? 'green' : 'yellow'}>
                      {(model.accuracy * 100).toFixed(1)}%
                    </Badge>
                  </Td>
                  <Td>{(model.precision * 100).toFixed(1)}%</Td>
                  <Td>{(model.recall * 100).toFixed(1)}%</Td>
                  <Td>{(model.f1_score * 100).toFixed(1)}%</Td>
                  <Td>{model.data_points_used.toLocaleString()}</Td>
                  <Td fontSize="xs">{new Date(model.training_date).toLocaleDateString('ja-JP')}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </TableContainer>
      </CardBody>
    </Card>
  );

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        <AlertTitle>学習データ取得エラー</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <Box bg={bgColor} minH="100vh" p={6}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between" align="center">
          <Heading size="lg">学習進捗</Heading>
          <Button
            leftIcon={<Icon as={FiRefreshCw} />}
            onClick={fetchLearningData}
            isLoading={isLoading}
            size="sm"
          >
            更新
          </Button>
        </HStack>

        {isLoading && (
          <HStack justify="center" py={8}>
            <Spinner size="lg" />
            <Text>学習データを取得中...</Text>
          </HStack>
        )}

        {!isLoading && (
          <VStack spacing={6} align="stretch">
            {/* Learning Metrics */}
            <Box>
              <Heading size="md" mb={4}>学習メトリクス</Heading>
              {renderLearningMetrics()}
            </Box>

            {/* Milestones */}
            {renderMilestones()}

            {/* A/B Test Results */}
            {renderABTestResults()}

            {/* Model Performance */}
            {renderModelPerformance()}
          </VStack>
        )}
      </VStack>
    </Box>
  );
}; 