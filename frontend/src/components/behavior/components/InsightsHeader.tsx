import React from 'react';
import {
  Card,
  CardHeader,
  HStack,
  VStack,
  Heading,
  Text,
  Button,
  Select,
  Badge,
  Box,
  useColorModeValue
} from '@chakra-ui/react';
import { FaSync, FaClock, FaChartLine } from 'react-icons/fa';

interface InsightsHeaderProps {
  timeframe: string;
  onTimeframeChange: (timeframe: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
  lastUpdated: Date | null;
  loadingProgress: {
    summary: boolean;
    trends: boolean;
    insights: boolean;
  };
}

export const InsightsHeader: React.FC<InsightsHeaderProps> = ({
  timeframe,
  onTimeframeChange,
  onRefresh,
  isLoading,
  lastUpdated,
  loadingProgress
}) => {
  const bgGradient = useColorModeValue(
    'linear(to-r, blue.50, purple.50)',
    'linear(to-r, blue.900, purple.900)'
  );
  const cardBg = useColorModeValue('white', 'gray.800');

  const getLoadingMessage = () => {
    if (loadingProgress.summary) return '📊 基本データ取得中...';
    if (loadingProgress.trends) return '📈 トレンド分析中...';
    if (loadingProgress.insights) return '🧠 AI洞察生成中...';
    return '✅ データ更新完了';
  };

  const getProgressPercentage = () => {
    if (!loadingProgress.summary && !loadingProgress.trends && !loadingProgress.insights) return 100;
    if (!loadingProgress.summary && !loadingProgress.trends) return 80;
    if (!loadingProgress.summary) return 50;
    return 20;
  };

  return (
    <Card bg={cardBg} shadow="lg" borderRadius="xl" overflow="hidden">
      <Box bgGradient={bgGradient} p={1}>
        <CardHeader bg={cardBg} m={1} borderRadius="lg">
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between" align="center">
              <HStack spacing={3}>
                <Box
                  p={2}
                  bg="blue.500"
                  borderRadius="lg"
                  color="white"
                >
                  <FaChartLine size="20px" />
                </Box>
                <VStack align="start" spacing={0}>
                  <Heading size="lg" color="gray.800">
                    行動分析インサイト
                  </Heading>
                  <Text fontSize="sm" color="gray.600">
                    AIによる行動パターン分析と改善提案
                  </Text>
                </VStack>
              </HStack>

              <HStack spacing={3}>
                <Select
                  value={timeframe}
                  onChange={(e) => onTimeframeChange(e.target.value)}
                  size="sm"
                  width="120px"
                  bg="white"
                  borderColor="gray.300"
                  _hover={{ borderColor: 'blue.400' }}
                  _focus={{ borderColor: 'blue.500', boxShadow: '0 0 0 1px blue.500' }}
                >
                  <option value="today">今日</option>
                  <option value="week">今週</option>
                  <option value="month">今月</option>
                </Select>

                <Button
                  onClick={onRefresh}
                  size="sm"
                  colorScheme="blue"
                  variant="solid"
                  leftIcon={<FaSync />}
                  isLoading={isLoading}
                  loadingText="更新中"
                  _hover={{ transform: 'translateY(-1px)', shadow: 'md' }}
                  transition="all 0.2s"
                >
                  更新
                </Button>
              </HStack>
            </HStack>

            {/* Progress and Status */}
            <HStack justify="space-between" align="center">
              <HStack spacing={4}>
                {isLoading && (
                  <VStack spacing={2} align="start">
                    <Text fontSize="xs" color="blue.600" fontWeight="medium">
                      {getLoadingMessage()}
                    </Text>
                    <Box
                      bg="gray.200"
                      height="3px"
                      width="200px"
                      borderRadius="full"
                      overflow="hidden"
                    >
                      <Box
                        bg="blue.500"
                        height="100%"
                        width={`${getProgressPercentage()}%`}
                        borderRadius="full"
                        transition="width 0.5s ease"
                      />
                    </Box>
                  </VStack>
                )}
              </HStack>

              {lastUpdated && (
                <HStack spacing={2}>
                  <FaClock color="gray" size="12px" />
                  <Text fontSize="xs" color="gray.500">
                    最終更新: {lastUpdated.toLocaleTimeString()}
                  </Text>
                  <Badge colorScheme="green" size="sm">
                    リアルタイム
                  </Badge>
                </HStack>
              )}
            </HStack>
          </VStack>
        </CardHeader>
      </Box>
    </Card>
  );
};