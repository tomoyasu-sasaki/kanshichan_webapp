import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  VStack,
  HStack,
  Text,
  Box,
  Badge,
  Grid,
  Progress,
  Alert,
  AlertIcon,
  Skeleton,
  useColorModeValue,
  Icon,
  Divider
} from '@chakra-ui/react';
import {
  FaChartLine,
  FaArrowUp,
  FaArrowDown,
  FaMinus,
  FaBrain,
  FaUserCheck,
  FaMobile,
  FaCalendarCheck
} from 'react-icons/fa';
import type { BehaviorTrend } from '../types';

interface TrendsChartProps {
  behaviorTrends: BehaviorTrend | null;
  isLoading: boolean;
}

interface TrendIndicatorProps {
  direction: 'up' | 'down' | 'stable';
  percentage: number;
  size?: 'sm' | 'md';
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({ 
  direction, 
  percentage, 
  size = 'md' 
}) => {
  const getTrendDisplay = () => {
    switch (direction) {
      case 'up':
        return {
          icon: FaArrowUp,
          color: 'green',
          text: `+${percentage.toFixed(1)}%`,
        };
      case 'down':
        return {
          icon: FaArrowDown,
          color: 'red',
          text: `-${percentage.toFixed(1)}%`,
        };
      default:
        return {
          icon: FaMinus,
          color: 'gray',
          text: '変化なし',
        };
    }
  };

  const trend = getTrendDisplay();
  const iconSize = size === 'sm' ? 3 : 4;
  const fontSize = size === 'sm' ? 'xs' : 'sm';

  return (
    <HStack spacing={1} color={`${trend.color}.500`}>
      <Icon as={trend.icon} boxSize={iconSize} />
      <Text fontSize={fontSize} fontWeight="medium">
        {trend.text}
      </Text>
    </HStack>
  );
};

interface MetricCardProps {
  title: string;
  value: string;
  trend?: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
  };
  icon: React.ElementType;
  color: string;
  description?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  trend,
  icon,
  color,
  description
}) => {
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Box
      p={4}
      bg={cardBg}
      border="1px"
      borderColor={borderColor}
      borderRadius="lg"
      _hover={{ borderColor: `${color}.300`, shadow: 'sm' }}
      transition="all 0.2s"
    >
      <VStack spacing={3} align="stretch">
        <HStack justify="space-between" align="center">
          <HStack spacing={2}>
            <Box
              p={1.5}
              bg={`${color}.100`}
              borderRadius="md"
              color={`${color}.600`}
            >
              <Icon as={icon} boxSize={3} />
            </Box>
            <Text fontSize="sm" fontWeight="medium" color="gray.700">
              {title}
            </Text>
          </HStack>
          {trend && (
            <TrendIndicator
              direction={trend.direction}
              percentage={trend.percentage}
              size="sm"
            />
          )}
        </HStack>

        <Box>
          <Text fontSize="xl" fontWeight="bold" color="gray.800">
            {value}
          </Text>
          {description && (
            <Text fontSize="xs" color="gray.500" mt={1}>
              {description}
            </Text>
          )}
        </Box>
      </VStack>
    </Box>
  );
};

export const TrendsChart: React.FC<TrendsChartProps> = ({
  behaviorTrends,
  isLoading
}) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  // 以下は条件分岐内で使用するため、フック順序を守るために事前に評価しておく
  const infoBg = useColorModeValue('blue.50', 'blue.900');
  const infoBorderColor = useColorModeValue('blue.200', 'blue.700');

  const formatPercentage = (value: number): string => {
    return `${Math.round(value * 100)}%`;
  };

  if (isLoading) {
    return (
      <Card bg={cardBg} border="1px" borderColor={borderColor} borderRadius="xl" shadow="sm">
        <CardHeader>
          <HStack spacing={3}>
            <Box
              p={2}
              bg="blue.100"
              borderRadius="lg"
              color="blue.600"
            >
              <Icon as={FaChartLine} boxSize={5} />
            </Box>
            <VStack align="start" spacing={0}>
              <Text fontSize="lg" fontWeight="bold" color="gray.800">
                行動トレンド
              </Text>
              <Text fontSize="sm" color="gray.600">
                パフォーマンス指標の推移
              </Text>
            </VStack>
          </HStack>
        </CardHeader>
        <CardBody pt={0}>
          <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
            {Array.from({ length: 4 }).map((_, index) => (
              <Box key={index} p={4} border="1px" borderColor={borderColor} borderRadius="lg">
                <VStack spacing={3} align="stretch">
                  <Skeleton height="20px" />
                  <Skeleton height="24px" />
                  <Skeleton height="16px" />
                </VStack>
              </Box>
            ))}
          </Grid>
        </CardBody>
      </Card>
    );
  }

  if (!behaviorTrends) {
    return (
      <Card bg={cardBg} border="1px" borderColor={borderColor} borderRadius="xl" shadow="sm">
        <CardHeader>
          <HStack spacing={3}>
            <Box
              p={2}
              bg="blue.100"
              borderRadius="lg"
              color="blue.600"
            >
              <Icon as={FaChartLine} boxSize={5} />
            </Box>
            <Text fontSize="lg" fontWeight="bold" color="gray.800">
              行動トレンド
            </Text>
          </HStack>
        </CardHeader>
        <CardBody pt={0}>
          <Alert status="info" borderRadius="lg">
            <AlertIcon />
            トレンドデータが不足しています。継続的な使用でデータが蓄積されます。
          </Alert>
        </CardBody>
      </Card>
    );
  }

  const focusAnalysis = behaviorTrends.focus_analysis || {};
  const basicStats = focusAnalysis.basic_statistics || {};
  const trendAnalysis = focusAnalysis.trend_analysis || {};

  // トレンド方向の決定
  const getTrendDirection = (): 'up' | 'down' | 'stable' => {
    if (focusAnalysis.trend_direction) {
      return focusAnalysis.trend_direction;
    }
    if (trendAnalysis.trend === 'improving') return 'up';
    if (trendAnalysis.trend === 'declining') return 'down';
    return 'stable';
  };

  const trendDirection = getTrendDirection();
  const trendPercentage = focusAnalysis.trend_percentage || trendAnalysis.trend_strength || 0;

  return (
    <Card bg={cardBg} border="1px" borderColor={borderColor} borderRadius="xl" shadow="sm">
      <CardHeader>
        <HStack justify="space-between" align="center">
          <HStack spacing={3}>
            <Box
              p={2}
              bg="blue.100"
              borderRadius="lg"
              color="blue.600"
            >
              <Icon as={FaChartLine} boxSize={5} />
            </Box>
            <VStack align="start" spacing={0}>
              <Text fontSize="lg" fontWeight="bold" color="gray.800">
                行動トレンド
              </Text>
              <Text fontSize="sm" color="gray.600">
                パフォーマンス指標の推移
              </Text>
            </VStack>
          </HStack>

          <Badge
            colorScheme={
              trendDirection === 'up' ? 'green' : 
              trendDirection === 'down' ? 'red' : 'gray'
            }
            px={3}
            py={1}
            borderRadius="full"
            fontSize="sm"
          >
            {trendDirection === 'up' ? '改善傾向' : 
             trendDirection === 'down' ? '注意が必要' : '安定'}
          </Badge>
        </HStack>
      </CardHeader>

      <CardBody pt={0}>
        <VStack spacing={6} align="stretch">
          {/* メイン指標 */}
          <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
            <MetricCard
              title="平均集中度"
              value={formatPercentage(
                focusAnalysis.average_focus || basicStats.mean || 0
              )}
              trend={{
                direction: trendDirection,
                percentage: trendPercentage
              }}
              icon={FaBrain}
              color="blue"
              description="全体的な集中レベル"
            />

            <MetricCard
              title="良い姿勢率"
              value={formatPercentage(
                focusAnalysis.good_posture_percentage || basicStats.high_focus_ratio || 0
              )}
              trend={{
                direction: trendDirection,
                percentage: 0
              }}
              icon={FaUserCheck}
              color="green"
              description="正しい姿勢の維持率"
            />

            <MetricCard
              title="在席率"
              value={formatPercentage(
                focusAnalysis.presence_rate || 
                (1 - (basicStats.low_focus_ratio || 0))
              )}
              icon={FaCalendarCheck}
              color="purple"
              description="デスクでの作業時間"
            />

            <MetricCard
              title="スマホ使用率"
              value={formatPercentage(
                focusAnalysis.smartphone_usage_rate || basicStats.low_focus_ratio || 0
              )}
              icon={FaMobile}
              color="orange"
              description="注意散漫な時間"
            />
          </Grid>

          <Divider />

          {/* 詳細統計 */}
          <Box>
            <Text fontSize="md" fontWeight="bold" color="gray.800" mb={3}>
              詳細統計
            </Text>
            <Grid templateColumns="repeat(auto-fit, minmax(150px, 1fr))" gap={4}>
              <VStack spacing={2} align="start">
                <Text fontSize="sm" color="gray.600">総セッション数</Text>
                <Text fontSize="lg" fontWeight="bold" color="gray.800">
                  {focusAnalysis.total_sessions || 
                   Object.keys(focusAnalysis.hourly_patterns?.hourly_statistics || {}).length || 0}回
                </Text>
              </VStack>

              <VStack spacing={2} align="start">
                <Text fontSize="sm" color="gray.600">高集中時間率</Text>
                <Text fontSize="lg" fontWeight="bold" color="green.600">
                  {formatPercentage(basicStats.high_focus_ratio || 0)}
                </Text>
              </VStack>

              <VStack spacing={2} align="start">
                <Text fontSize="sm" color="gray.600">低集中時間率</Text>
                <Text fontSize="lg" fontWeight="bold" color="red.600">
                  {formatPercentage(basicStats.low_focus_ratio || 0)}
                </Text>
              </VStack>

              <VStack spacing={2} align="start">
                <Text fontSize="sm" color="gray.600">分析期間</Text>
                <Text fontSize="lg" fontWeight="bold" color="gray.800">
                  {behaviorTrends.period_hours || 24}時間
                </Text>
              </VStack>
            </Grid>
          </Box>

          {/* トレンド分析サマリー */}
          {trendAnalysis.trend && (
            <Box
              p={4}
              bg={infoBg}
              borderRadius="lg"
              border="1px"
              borderColor={infoBorderColor}
            >
              <HStack spacing={3}>
                <TrendIndicator
                  direction={trendDirection}
                  percentage={trendPercentage}
                />
                <Text fontSize="sm" color="gray.700">
                  {trendAnalysis.trend === 'improving' && '集中力が向上しています。この調子で継続しましょう。'}
                  {trendAnalysis.trend === 'declining' && '集中力が低下傾向にあります。休息や環境の見直しを検討してください。'}
                  {trendAnalysis.trend === 'stable' && '安定した集中力を維持しています。'}
                </Text>
              </HStack>
            </Box>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};