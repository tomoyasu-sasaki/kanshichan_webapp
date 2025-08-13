import React from 'react';
import {
  Grid,
  Card,
  CardBody,
  VStack,
  HStack,
  Text,
  Box,
  Progress,
  Badge,
  Skeleton,
  Alert,
  AlertIcon,
  useColorModeValue,
  Icon
} from '@chakra-ui/react';
import { TriangleDownIcon, TriangleUpIcon } from '@chakra-ui/icons';
import {
  FaClock,
  FaBrain,
  FaUserCheck,
  FaMobile,
  FaExclamationTriangle,
  FaChartLine
} from 'react-icons/fa';
import type { BehaviorSummary } from '../types';

interface SummaryCardsProps {
  behaviorSummary: BehaviorSummary | null;
  isLoading: boolean;
  error: string | null;
}

interface StatCardProps {
  title: string;
  value: string;
  change: string;
  trend: 'increase' | 'decrease' | 'neutral';
  icon: React.ElementType;
  color: string;
  isLoading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  trend,
  icon,
  color,
  isLoading = false
}) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  if (isLoading) {
    return (
      <Card bg={cardBg} border="1px" borderColor={borderColor} borderRadius="xl" shadow="sm">
        <CardBody p={6}>
          <VStack spacing={4} align="stretch">
            <Skeleton height="20px" />
            <Skeleton height="32px" />
            <Skeleton height="16px" />
          </VStack>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card 
      bg={cardBg} 
      border="1px" 
      borderColor={borderColor} 
      borderRadius="xl" 
      shadow="sm"
      _hover={{ 
        shadow: 'md', 
        transform: 'translateY(-2px)',
        borderColor: `${color}.300`
      }}
      transition="all 0.2s"
    >
      <CardBody p={6}>
        <VStack spacing={4} align="stretch">
          <HStack justify="space-between" align="center">
            <Text fontSize="sm" color="gray.600" fontWeight="medium">
              {title}
            </Text>
            <Box
              p={2}
              bg={`${color}.100`}
              borderRadius="lg"
              color={`${color}.600`}
            >
              <Icon as={icon} boxSize={4} />
            </Box>
          </HStack>

          <Box>
            <Text fontSize="2xl" fontWeight="bold" color="gray.800">
              {value}
            </Text>
            <HStack spacing={2} mt={1}>
              {trend !== 'neutral' && (
                <Icon
                  as={trend === 'increase' ? TriangleUpIcon : TriangleDownIcon}
                  color={trend === 'increase' ? 'green.500' : 'red.500'}
                  boxSize={3}
                />
              )}
              <Text fontSize="sm" color="gray.500">
                {change}
              </Text>
            </HStack>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
};

export const SummaryCards: React.FC<SummaryCardsProps> = ({
  behaviorSummary,
  isLoading,
  error
}) => {
  // Helper functions
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatPercentage = (value: number): string => {
    return `${Math.round(value * 100)}%`;
  };

  const getTrend = (today: number, yesterday: number): 'increase' | 'decrease' | 'neutral' => {
    if (today > yesterday) return 'increase';
    if (today < yesterday) return 'decrease';
    return 'neutral';
  };

  const getChangeText = (today: number, yesterday: number, formatter: (n: number) => string): string => {
    const diff = Math.abs(today - yesterday);
    if (diff === 0) return '変化なし';
    return `前日比 ${formatter(diff)}`;
  };

  if (error) {
    return (
      <Card borderRadius="xl">
        <CardBody>
          <Alert status="error" borderRadius="lg">
            <AlertIcon />
            {error}
          </Alert>
        </CardBody>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Grid templateColumns="repeat(auto-fit, minmax(280px, 1fr))" gap={6}>
        {Array.from({ length: 6 }).map((_, index) => (
          <StatCard
            key={index}
            title=""
            value=""
            change=""
            trend="neutral"
            icon={FaClock}
            color="blue"
            isLoading={true}
          />
        ))}
      </Grid>
    );
  }

  if (!behaviorSummary) {
    return (
      <Card borderRadius="xl">
        <CardBody>
          <Alert status="info" borderRadius="lg">
            <AlertIcon />
            データが不足しています。しばらく使用してからご確認ください。
          </Alert>
        </CardBody>
      </Card>
    );
  }

  const today = behaviorSummary.today || {};
  const yesterday = behaviorSummary.yesterday || {};

  return (
    <Grid templateColumns="repeat(auto-fit, minmax(280px, 1fr))" gap={6}>
      {/* 監視時間 */}
      <StatCard
        title="今日の監視時間"
        value={formatTime(today.total_time || 0)}
        change={getChangeText(today.total_time || 0, yesterday.total_time || 0, formatTime)}
        trend={getTrend(today.total_time || 0, yesterday.total_time || 0)}
        icon={FaClock}
        color="blue"
      />

      {/* 集中時間 */}
      <StatCard
        title="集中時間"
        value={formatTime(today.focus_time || 0)}
        change={getChangeText(today.focus_time || 0, yesterday.focus_time || 0, formatTime)}
        trend={getTrend(today.focus_time || 0, yesterday.focus_time || 0)}
        icon={FaBrain}
        color="green"
      />

      {/* 在席率 */}
      <StatCard
        title="在席率"
        value={formatPercentage(
          (today.total_time || 0) > 0
            ? ((today.total_time || 0) - (today.absence_time || 0)) / (today.total_time || 0)
            : 0
        )}
        change={`不在時間: ${formatTime(today.absence_time || 0)}`}
        trend="neutral"
        icon={FaUserCheck}
        color="purple"
      />

      {/* スマホ使用時間 */}
      <StatCard
        title="スマホ使用時間"
        value={formatTime(today.smartphone_usage_time || 0)}
        change={getChangeText(
          today.smartphone_usage_time || 0,
          yesterday.smartphone_usage_time || 0,
          formatTime
        )}
        trend={getTrend(
          yesterday.smartphone_usage_time || 0, // 逆転: 少ない方が良い
          today.smartphone_usage_time || 0
        )}
        icon={FaMobile}
        color="orange"
      />

      {/* 姿勢アラート */}
      <StatCard
        title="姿勢アラート"
        value={`${today.posture_alerts || 0}回`}
        change={`前日: ${yesterday.posture_alerts || 0}回`}
        trend={getTrend(
          yesterday.posture_alerts || 0, // 逆転: 少ない方が良い
          today.posture_alerts || 0
        )}
        icon={FaExclamationTriangle}
        color="red"
      />

      {/* 生産性スコア */}
      <Card 
        bg={useColorModeValue('white', 'gray.800')} 
        border="1px" 
        borderColor={useColorModeValue('gray.200', 'gray.600')} 
        borderRadius="xl" 
        shadow="sm"
        _hover={{ 
          shadow: 'md', 
          transform: 'translateY(-2px)',
          borderColor: 'teal.300'
        }}
        transition="all 0.2s"
      >
        <CardBody p={6}>
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between" align="center">
              <Text fontSize="sm" color="gray.600" fontWeight="medium">
                生産性スコア
              </Text>
              <Box
                p={2}
                bg="teal.100"
                borderRadius="lg"
                color="teal.600"
              >
                <Icon as={FaChartLine} boxSize={4} />
              </Box>
            </HStack>

            <Box>
              <Text fontSize="2xl" fontWeight="bold" color="gray.800" mb={2}>
                {Math.round(
                  ((today.focus_time || 0) / Math.max(today.total_time || 1, 1)) * 100
                )}%
              </Text>
              <Progress
                value={((today.focus_time || 0) / Math.max(today.total_time || 1, 1)) * 100}
                colorScheme="teal"
                size="lg"
                borderRadius="full"
              />
              <Text fontSize="sm" color="gray.500" mt={1}>
                集中時間 / 総時間
              </Text>
            </Box>
          </VStack>
        </CardBody>
      </Card>
    </Grid>
  );
};