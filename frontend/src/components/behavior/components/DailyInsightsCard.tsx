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
  List,
  ListItem,
  Alert,
  AlertIcon,
  Skeleton,
  useColorModeValue,
  Icon,
  Divider,
  Grid,
  CircularProgress,
  CircularProgressLabel
} from '@chakra-ui/react';
import {
  FaLightbulb,
  FaEye,
  FaExclamationTriangle,
  FaBrain,
  FaBullseye
} from 'react-icons/fa';
import type { DailyInsight, InsightItem } from '../types';

interface DailyInsightsCardProps {
  dailyInsights: DailyInsight | null;
  isLoading: boolean;
}

interface ScoreCardProps {
  title: string;
  score: number;
  color: string;
  icon: React.ElementType;
  description: string;
}

const ScoreCard: React.FC<ScoreCardProps> = ({
  title,
  score,
  color,
  icon,
  description
}) => {
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const percentage = Math.round(score * 100);

  return (
    <Box
      p={6}
      bg={cardBg}
      border="1px"
      borderColor={borderColor}
      borderRadius="xl"
      _hover={{ borderColor: `${color}.300`, shadow: 'md' }}
      transition="all 0.2s"
    >
      <VStack spacing={4}>
        <HStack spacing={3} w="full" justify="center">
          <Box
            p={2}
            bg={`${color}.100`}
            borderRadius="lg"
            color={`${color}.600`}
          >
            <Icon as={icon} boxSize={5} />
          </Box>
          <VStack spacing={0} align="center">
            <Text fontSize="sm" fontWeight="medium" color="gray.600">
              {title}
            </Text>
            <Text fontSize="xs" color="gray.500" textAlign="center">
              {description}
            </Text>
          </VStack>
        </HStack>

        <Box position="relative">
          <CircularProgress
            value={percentage}
            color={`${color}.500`}
            size="120px"
            thickness="8px"
            trackColor={useColorModeValue('gray.100', 'gray.600')}
          >
            <CircularProgressLabel>
              <VStack spacing={0}>
                <Text fontSize="2xl" fontWeight="bold" color="gray.800">
                  {percentage}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  / 100
                </Text>
              </VStack>
            </CircularProgressLabel>
          </CircularProgress>
        </Box>

        <Badge
          colorScheme={
            percentage >= 80 ? 'green' :
            percentage >= 60 ? 'blue' :
            percentage >= 40 ? 'orange' : 'red'
          }
          px={3}
          py={1}
          borderRadius="full"
          fontSize="sm"
        >
          {percentage >= 80 ? '優秀' :
           percentage >= 60 ? '良好' :
           percentage >= 40 ? '普通' : '要改善'}
        </Badge>
      </VStack>
    </Box>
  );
};

export const DailyInsightsCard: React.FC<DailyInsightsCardProps> = ({
  dailyInsights,
  isLoading
}) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  // 条件分岐内で使用するカラーモード値は事前に評価しておく（Hooks順序を守る）
  const summaryBg = useColorModeValue('purple.50', 'purple.900');
  const summaryBorderColor = useColorModeValue('purple.200', 'purple.700');
  const footerBg = useColorModeValue('gray.50', 'gray.700');

  if (isLoading) {
    return (
      <Card bg={cardBg} border="1px" borderColor={borderColor} borderRadius="xl" shadow="sm">
        <CardHeader>
          <HStack spacing={3}>
            <Box
              p={2}
              bg="purple.100"
              borderRadius="lg"
              color="purple.600"
            >
              <Icon as={FaLightbulb} boxSize={5} />
            </Box>
            <VStack align="start" spacing={0}>
              <Text fontSize="lg" fontWeight="bold" color="gray.800">
                今日の洞察
              </Text>
              <Text fontSize="sm" color="gray.600">
                AIによる行動分析結果
              </Text>
            </VStack>
          </HStack>
        </CardHeader>
        <CardBody pt={0}>
          <VStack spacing={4} align="stretch">
            <Skeleton height="60px" />
            <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
              <Skeleton height="200px" />
              <Skeleton height="200px" />
            </Grid>
            <Skeleton height="100px" />
          </VStack>
        </CardBody>
      </Card>
    );
  }

  if (!dailyInsights) {
    return (
      <Card bg={cardBg} border="1px" borderColor={borderColor} borderRadius="xl" shadow="sm">
        <CardHeader>
          <HStack spacing={3}>
            <Box
              p={2}
              bg="purple.100"
              borderRadius="lg"
              color="purple.600"
            >
              <Icon as={FaLightbulb} boxSize={5} />
            </Box>
            <Text fontSize="lg" fontWeight="bold" color="gray.800">
              今日の洞察
            </Text>
          </HStack>
        </CardHeader>
        <CardBody pt={0}>
          <Alert status="info" borderRadius="lg">
            <AlertIcon />
            十分なデータが蓄積されていません。継続的な使用で洞察が生成されます。
          </Alert>
        </CardBody>
      </Card>
    );
  }

  const insights = dailyInsights.insights || {};
  const keyFindings = insights.key_findings || [];
  const improvementAreas = insights.improvement_areas || [];

  const formatInsightText = (item: string | InsightItem): string => {
    if (typeof item === 'string') return item;
    if (typeof item === 'object' && item !== null) {
      return (item as InsightItem).message || 
             (item as InsightItem).action || 
             JSON.stringify(item);
    }
    return String(item);
  };

  return (
    <Card bg={cardBg} border="1px" borderColor={borderColor} borderRadius="xl" shadow="sm">
      <CardHeader>
        <HStack justify="space-between" align="center">
          <HStack spacing={3}>
            <Box
              p={2}
              bg="purple.100"
              borderRadius="lg"
              color="purple.600"
            >
              <Icon as={FaLightbulb} boxSize={5} />
            </Box>
            <VStack align="start" spacing={0}>
              <Text fontSize="lg" fontWeight="bold" color="gray.800">
                今日の洞察
              </Text>
              <Text fontSize="sm" color="gray.600">
                AIによる行動分析結果
              </Text>
            </VStack>
          </HStack>

          <Badge colorScheme="purple" px={3} py={1} borderRadius="full">
            {dailyInsights.logs_analyzed || 0}件のデータを分析
          </Badge>
        </HStack>
      </CardHeader>

      <CardBody pt={0}>
        <VStack spacing={6} align="stretch">
          {/* サマリー */}
          {dailyInsights.summary?.summary && (
            <Box
              p={4}
              bg={summaryBg}
              borderRadius="lg"
              border="1px"
              borderColor={summaryBorderColor}
            >
              <Text fontSize="sm" color="gray.700" lineHeight="1.6">
                {dailyInsights.summary.summary}
              </Text>
            </Box>
          )}

          {/* スコア表示 */}
          <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={6}>
            <ScoreCard
              title="集中スコア"
              score={insights.focus_score || 0}
              color="blue"
              icon={FaBrain}
              description="集中力の維持度合い"
            />

            <ScoreCard
              title="生産性スコア"
              score={insights.productivity_score || 0}
              color="green"
              icon={FaBullseye}
              description="効率的な作業の実行度"
            />
          </Grid>

          {/* 主な発見 */}
          {keyFindings.length > 0 && (
            <>
              <Divider />
              <Box>
                <HStack spacing={2} mb={4}>
                  <Icon as={FaEye} color="blue.500" boxSize={4} />
                  <Text fontSize="md" fontWeight="bold" color="gray.800">
                    主な発見
                  </Text>
                  <Badge colorScheme="blue" size="sm">
                    {keyFindings.length}件
                  </Badge>
                </HStack>
                <List spacing={3}>
                  {keyFindings.map((finding, index) => (
                    <ListItem key={index}>
                      <HStack align="start" spacing={3}>
                        <Box
                          mt={1}
                          p={1}
                          bg="blue.100"
                          borderRadius="full"
                          color="blue.600"
                        >
                          <Icon as={FaEye} boxSize={3} />
                        </Box>
                        <Text fontSize="sm" color="gray.700" lineHeight="1.5">
                          {formatInsightText(finding)}
                        </Text>
                      </HStack>
                    </ListItem>
                  ))}
                </List>
              </Box>
            </>
          )}

          {/* 改善領域 */}
          {improvementAreas.length > 0 && (
            <>
              <Divider />
              <Box>
                <HStack spacing={2} mb={4}>
                  <Icon as={FaExclamationTriangle} color="orange.500" boxSize={4} />
                  <Text fontSize="md" fontWeight="bold" color="gray.800">
                    改善領域
                  </Text>
                  <Badge colorScheme="orange" size="sm">
                    {improvementAreas.length}件
                  </Badge>
                </HStack>
                <List spacing={3}>
                  {improvementAreas.map((area, index) => (
                    <ListItem key={index}>
                      <HStack align="start" spacing={3}>
                        <Box
                          mt={1}
                          p={1}
                          bg="orange.100"
                          borderRadius="full"
                          color="orange.600"
                        >
                          <Icon as={FaExclamationTriangle} boxSize={3} />
                        </Box>
                        <Text fontSize="sm" color="gray.700" lineHeight="1.5">
                          {formatInsightText(area)}
                        </Text>
                      </HStack>
                    </ListItem>
                  ))}
                </List>
              </Box>
            </>
          )}

          {/* 分析日時 */}
          <Box
            p={3}
            bg={footerBg}
            borderRadius="lg"
            textAlign="center"
          >
            <Text fontSize="xs" color="gray.500">
              分析対象日: {dailyInsights.target_date} • 
              データ件数: {dailyInsights.logs_analyzed || 0}件
            </Text>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
};