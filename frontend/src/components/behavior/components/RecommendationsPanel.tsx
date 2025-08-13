import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  VStack,
  HStack,
  Text,
  Box,
  Badge,
  Button,
  IconButton,
  Alert,
  AlertIcon,
  Skeleton,
  useColorModeValue,
  Icon,
  Collapse,
  useToast,
  Tabs,
  TabList,
  Tab,
  Divider
} from '@chakra-ui/react';
import {
  FaCheckCircle,
  FaVolumeUp,
  FaCopy,
  FaArrowDown,
  FaExclamationTriangle,
  FaInfoCircle,
  FaThumbsUp
} from 'react-icons/fa';
import { Recommendation, PaginationInfo } from '../../../types/recommendation';

interface RecommendationsPanelProps {
  recommendations: Recommendation[];
  paginationInfo: PaginationInfo;
  priorityFilter: string;
  isLoading: boolean;
  onPriorityChange: (priority: string) => void;
  onLoadMore: () => void;
}

interface RecommendationItemProps {
  recommendation: Recommendation;
  index: number;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onPlayAudio: (url: string) => void;
  onCopy: (text: string) => void;
}

const RecommendationItem: React.FC<RecommendationItemProps> = ({
  recommendation,
  index,
  isExpanded,
  onToggleExpand,
  onPlayAudio,
  onCopy
}) => {
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const getPriorityConfig = (priority: string) => {
    switch (priority) {
      case 'high':
        return {
          colorScheme: 'red',
          icon: FaExclamationTriangle,
          label: '重要',
          bgColor: useColorModeValue('red.50', 'red.900'),
          borderColor: useColorModeValue('red.200', 'red.700')
        };
      case 'medium':
        return {
          colorScheme: 'orange',
          icon: FaInfoCircle,
          label: '普通',
          bgColor: useColorModeValue('orange.50', 'orange.900'),
          borderColor: useColorModeValue('orange.200', 'orange.700')
        };
      default:
        return {
          colorScheme: 'green',
          icon: FaThumbsUp,
          label: '軽微',
          bgColor: useColorModeValue('green.50', 'green.900'),
          borderColor: useColorModeValue('green.200', 'green.700')
        };
    }
  };

  const priorityConfig = getPriorityConfig(recommendation.priority);
  const shouldShowExpand = recommendation.message.length > 120;

  return (
    <Box
      p={4}
      bg={cardBg}
      border="1px"
      borderColor={borderColor}
      borderRadius="lg"
      _hover={{ borderColor: priorityConfig.borderColor, shadow: 'sm' }}
      transition="all 0.2s"
    >
      <VStack spacing={3} align="stretch">
        <HStack justify="space-between" align="start">
          <HStack spacing={3} flex={1}>
            <Box
              p={2}
              bg={priorityConfig.bgColor}
              borderRadius="lg"
              color={`${priorityConfig.colorScheme}.600`}
            >
              <Icon as={priorityConfig.icon} boxSize={4} />
            </Box>
            <VStack align="start" spacing={1} flex={1}>
              <HStack spacing={2}>
                <Badge
                  colorScheme={priorityConfig.colorScheme}
                  px={2}
                  py={1}
                  borderRadius="full"
                  fontSize="xs"
                >
                  {priorityConfig.label}
                </Badge>
                <Text fontSize="xs" color="gray.500">
                  {new Date(recommendation.timestamp).toLocaleString()}
                </Text>
              </HStack>
              <Box>
                <Collapse
                  startingHeight={shouldShowExpand ? 60 : undefined}
                  in={isExpanded || !shouldShowExpand}
                  animateOpacity
                >
                  <Text fontSize="sm" color="gray.700" lineHeight="1.6">
                    {recommendation.message}
                  </Text>
                </Collapse>
                {shouldShowExpand && (
                  <Button
                    size="xs"
                    variant="link"
                    colorScheme="blue"
                    onClick={onToggleExpand}
                    mt={2}
                  >
                    {isExpanded ? '折りたたむ' : 'もっと見る'}
                  </Button>
                )}
              </Box>
            </VStack>
          </HStack>

          <HStack spacing={2}>
            {recommendation.audio_url && (
              <IconButton
                aria-label="音声再生"
                icon={<FaVolumeUp />}
                size="sm"
                variant="ghost"
                colorScheme="blue"
                onClick={() => onPlayAudio(recommendation.audio_url!)}
                _hover={{ bg: 'blue.100' }}
              />
            )}
            <IconButton
              aria-label="コピー"
              icon={<FaCopy />}
              size="sm"
              variant="ghost"
              colorScheme="gray"
              onClick={() => onCopy(recommendation.message)}
              _hover={{ bg: 'gray.100' }}
            />
          </HStack>
        </HStack>

        {recommendation.source && (
          <HStack justify="space-between" align="center">
            <Text fontSize="xs" color="gray.500">
              ソース: {recommendation.source}
            </Text>
          </HStack>
        )}
      </VStack>
    </Box>
  );
};

export const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({
  recommendations,
  paginationInfo,
  priorityFilter,
  isLoading,
  onPriorityChange,
  onLoadMore
}) => {
  const [expandedItems, setExpandedItems] = useState<Record<number, boolean>>({});
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const priorities = ['all', 'high', 'medium', 'low'];
  const priorityLabels = {
    all: 'すべて',
    high: '重要',
    medium: '普通',
    low: '軽微'
  };

  const toggleItemExpansion = (index: number) => {
    setExpandedItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const playAudio = (url: string) => {
    const audio = new Audio(url);
    audio.play().catch((error) => {
      console.error('音声再生エラー:', error);
      toast({
        title: '音声再生エラー',
        description: '音声の再生に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'コピーしました',
      description: 'クリップボードにコピーされました',
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  };

  return (
    <Card bg={cardBg} border="1px" borderColor={borderColor} borderRadius="xl" shadow="sm">
      <CardHeader>
        <HStack justify="space-between" align="center">
          <HStack spacing={3}>
            <Box
              p={2}
              bg="green.100"
              borderRadius="lg"
              color="green.600"
            >
              <Icon as={FaCheckCircle} boxSize={5} />
            </Box>
            <VStack align="start" spacing={0}>
              <Text fontSize="lg" fontWeight="bold" color="gray.800">
                改善提案
              </Text>
              <Text fontSize="sm" color="gray.600">
                AIによるパーソナライズされた提案
              </Text>
            </VStack>
          </HStack>

          <Badge colorScheme="green" px={3} py={1} borderRadius="full">
            {recommendations.length}件の提案
          </Badge>
        </HStack>

        <Box mt={4}>
          <Tabs
            variant="soft-rounded"
            colorScheme="blue"
            size="sm"
            onChange={(index) => onPriorityChange(priorities[index])}
            defaultIndex={priorities.indexOf(priorityFilter)}
          >
            <TabList>
              {priorities.map((priority) => (
                <Tab key={priority} px={4} py={2}>
                  {priorityLabels[priority as keyof typeof priorityLabels]}
                </Tab>
              ))}
            </TabList>
          </Tabs>
        </Box>
      </CardHeader>

      <CardBody pt={0}>
        {isLoading ? (
          <VStack spacing={4} align="stretch">
            {Array.from({ length: 3 }).map((_, index) => (
              <Box key={index} p={4} border="1px" borderColor={borderColor} borderRadius="lg">
                <VStack spacing={3} align="stretch">
                  <HStack justify="space-between">
                    <Skeleton height="20px" width="100px" />
                    <Skeleton height="20px" width="60px" />
                  </HStack>
                  <Skeleton height="60px" />
                  <Skeleton height="16px" width="150px" />
                </VStack>
              </Box>
            ))}
          </VStack>
        ) : recommendations.length > 0 ? (
          <VStack spacing={4} align="stretch">
            {recommendations.map((rec, index) => (
              <RecommendationItem
                key={`${rec.timestamp}-${index}`}
                recommendation={rec}
                index={index}
                isExpanded={expandedItems[index] || false}
                onToggleExpand={() => toggleItemExpansion(index)}
                onPlayAudio={playAudio}
                onCopy={copyToClipboard}
              />
            ))}

            {/* ページネーション */}
            {paginationInfo.total_pages > 1 && paginationInfo.page < paginationInfo.total_pages && (
              <>
                <Divider />
                <Box textAlign="center">
                  <Button
                    onClick={onLoadMore}
                    size="sm"
                    variant="outline"
                    colorScheme="blue"
                    leftIcon={<FaArrowDown />}
                    _hover={{ bg: 'blue.50' }}
                  >
                    さらに読み込む ({paginationInfo.page} / {paginationInfo.total_pages})
                  </Button>
                </Box>
              </>
            )}
          </VStack>
        ) : (
          <Alert status="info" borderRadius="lg">
            <AlertIcon />
            <VStack align="start" spacing={1}>
              <Text fontWeight="medium">
                現在利用可能な改善提案はありません
              </Text>
              <Text fontSize="sm" color="gray.600">
                継続的な使用により、パーソナライズされた提案が生成されます
              </Text>
            </VStack>
          </Alert>
        )}
      </CardBody>
    </Card>
  );
};