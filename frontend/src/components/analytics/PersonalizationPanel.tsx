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
  ButtonGroup,
  FormControl,
  FormLabel,
  Textarea,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
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
  SimpleGrid,
  Tag,
  TagLabel,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure
} from '@chakra-ui/react';
import { FiUser, FiSettings, FiTarget, FiTrendingUp } from 'react-icons/fi';

interface UserProfile {
  user_id: string;
  work_style: string;
  focus_duration_minutes: number;
  optimal_time_slots: string[];
  break_frequency_minutes: number;
  productivity_rhythm: string;
  health_habits: string[];
  learning_speed: number;
}

interface PersonalizedRecommendation {
  recommendation_id: string;
  category: string;
  title: string;
  description: string;
  priority: number;
  effectiveness_score: number;
  implementation_difficulty: string;
  estimated_impact: string;
  context: {
    time_of_day?: string;
    work_type?: string;
    current_state?: string;
  };
}

interface AdaptiveLearningStatus {
  learning_active: boolean;
  model_accuracy: number;
  recommendations_given: number;
  user_satisfaction_avg: number;
  adaptation_count: number;
  last_model_update: string;
}

interface PersonalizationPanelProps {
  userId?: string;
}

export const PersonalizationPanel: React.FC<PersonalizationPanelProps> = ({
  userId = 'default'
}) => {
  // State management
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [recommendations, setRecommendations] = useState<PersonalizedRecommendation[]>([]);
  const [learningStatus, setLearningStatus] = useState<AdaptiveLearningStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<number>(3);
  const [feedbackText, setFeedbackText] = useState('');
  const [selectedRecommendation, setSelectedRecommendation] = useState<PersonalizedRecommendation | null>(null);

  // UI theming
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

  // Data fetching functions
  const fetchUserData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch user profile
      const profileResponse = await fetch(`/api/analysis/basic/user-profile?user_id=${userId}`);
      if (!profileResponse.ok) throw new Error('Failed to fetch user profile');
      const profileData = await profileResponse.json();

      // Fetch personalized recommendations
      const recommendationsResponse = await fetch(`/api/analysis/advanced/personalized-recommendations?user_id=${userId}&limit=10`);
      if (!recommendationsResponse.ok) throw new Error('Failed to fetch recommendations');
      const recommendationsData = await recommendationsResponse.json();

      // Fetch adaptive learning status
      const learningResponse = await fetch(`/api/analysis/advanced/adaptive-learning-status?user_id=${userId}`);
      if (!learningResponse.ok) throw new Error('Failed to fetch learning status');
      const learningData = await learningResponse.json();

      // Set data
      setUserProfile(profileData.user_profile || null);
      setRecommendations(recommendationsData.recommendations || []);
      setLearningStatus(learningData.learning_status || null);

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
  }, [userId, toast]);

  // Submit feedback
  const submitFeedback = async (recommendationId: string, isHelpful: boolean) => {
    try {
      const response = await fetch('/api/analysis/basic/recommendation-feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recommendation_id: recommendationId,
          is_helpful: isHelpful,
          user_id: userId,
        }),
      });

      if (!response.ok) throw new Error('Failed to submit feedback');

      toast({
        title: 'フィードバック送信完了',
        description: '改善のための貴重なご意見をありがとうございました。',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      // Reset form
      setFeedbackRating(3);
      setFeedbackText('');
      onClose();

      // Refresh data
      fetchUserData();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      toast({
        title: 'フィードバック送信エラー',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  // Execute recommendation
  const executeRecommendation = async (recommendation: PersonalizedRecommendation) => {
    try {
      // Implementation would depend on the specific recommendation type
      toast({
        title: '推奨事項を実行中',
        description: `「${recommendation.title}」を適用しています...`,
        status: 'info',
        duration: 2000,
        isClosable: true,
      });

      // Track execution
      await submitFeedback(recommendation.recommendation_id, true);

    } catch (err) {
      console.error('Failed to execute recommendation:', err);
      toast({
        title: '実行エラー',
        description: '推奨事項の実行に失敗しました。',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  // Render user profile card
  const renderUserProfile = () => {
    if (!userProfile) return null;

    return (
      <Card bg={cardBg}>
        <CardHeader>
          <HStack>
            <Icon as={FiUser} />
            <Heading size="md">ユーザープロファイル</Heading>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <SimpleGrid columns={2} spacing={4}>
              <Stat>
                <StatLabel>作業スタイル</StatLabel>
                <StatNumber fontSize="lg">{userProfile.work_style}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>集中持続時間</StatLabel>
                <StatNumber fontSize="lg">{userProfile.focus_duration_minutes}分</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>休憩頻度</StatLabel>
                <StatNumber fontSize="lg">{userProfile.break_frequency_minutes}分毎</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>学習速度</StatLabel>
                <StatNumber fontSize="lg">{(userProfile.learning_speed * 100).toFixed(0)}%</StatNumber>
              </Stat>
            </SimpleGrid>

            <Divider />

            <Box>
              <Text fontWeight="bold" mb={2}>最適時間帯</Text>
              <HStack wrap="wrap">
                {userProfile.optimal_time_slots.map((slot, index) => (
                  <Tag key={index} colorScheme="blue" size="sm">
                    <TagLabel>{slot}</TagLabel>
                  </Tag>
                ))}
              </HStack>
            </Box>

            <Box>
              <Text fontWeight="bold" mb={2}>健康習慣</Text>
              <HStack wrap="wrap">
                {userProfile.health_habits.map((habit, index) => (
                  <Tag key={index} colorScheme="green" size="sm">
                    <TagLabel>{habit}</TagLabel>
                  </Tag>
                ))}
              </HStack>
            </Box>
          </VStack>
        </CardBody>
      </Card>
    );
  };

  // Render recommendations
  const renderRecommendations = () => (
    <Card bg={cardBg}>
      <CardHeader>
        <HStack justify="space-between">
          <HStack>
            <Icon as={FiTarget} />
            <Heading size="md">パーソナライズド推奨</Heading>
          </HStack>
          <Badge colorScheme="blue">{recommendations.length}件</Badge>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {recommendations.length === 0 ? (
            <Text color="gray.500">現在利用可能な推奨事項はありません</Text>
          ) : (
            recommendations.map((recommendation, index) => (
              <Card key={index} size="sm" variant="outline">
                <CardBody>
                  <VStack align="stretch" spacing={3}>
                    <HStack justify="space-between">
                      <Text fontWeight="bold">{recommendation.title}</Text>
                      <HStack>
                        <Badge colorScheme="purple" variant="outline">
                          {recommendation.category}
                        </Badge>
                        <Badge 
                          colorScheme={
                            recommendation.priority >= 8 ? 'red' :
                            recommendation.priority >= 6 ? 'orange' :
                            recommendation.priority >= 4 ? 'yellow' : 'green'
                          }
                        >
                          優先度 {recommendation.priority}
                        </Badge>
                      </HStack>
                    </HStack>

                    <Text fontSize="sm" color="gray.600">
                      {recommendation.description}
                    </Text>

                    <HStack justify="space-between">
                      <VStack align="start" spacing={1}>
                        <Text fontSize="xs" color="gray.500">
                          効果予測: {(recommendation.effectiveness_score * 100).toFixed(0)}%
                        </Text>
                        <Text fontSize="xs" color="gray.500">
                          実装難易度: {recommendation.implementation_difficulty}
                        </Text>
                      </VStack>

                      <ButtonGroup size="sm">
                        <Button
                          colorScheme="blue"
                          variant="outline"
                          onClick={() => executeRecommendation(recommendation)}
                        >
                          実行
                        </Button>
                        <Button
                          colorScheme="gray"
                          variant="outline"
                          onClick={() => {
                            setSelectedRecommendation(recommendation);
                            onOpen();
                          }}
                        >
                          フィードバック
                        </Button>
                      </ButtonGroup>
                    </HStack>

                    {recommendation.context && (
                      <Box fontSize="xs" color="gray.500">
                        <Text>
                          コンテキスト: {recommendation.context.time_of_day || ''} 
                          {recommendation.context.work_type || ''} 
                          {recommendation.context.current_state || ''}
                        </Text>
                      </Box>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            ))
          )}
        </VStack>
      </CardBody>
    </Card>
  );

  // Render learning status
  const renderLearningStatus = () => {
    if (!learningStatus) return null;

    return (
      <Card bg={cardBg}>
        <CardHeader>
          <HStack>
            <Icon as={FiTrendingUp} />
            <Heading size="md">適応学習ステータス</Heading>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between">
              <Text>学習機能</Text>
              <Badge colorScheme={learningStatus.learning_active ? 'green' : 'gray'}>
                {learningStatus.learning_active ? 'アクティブ' : '停止中'}
              </Badge>
            </HStack>

            <Box>
              <HStack justify="space-between" mb={2}>
                <Text fontSize="sm">モデル精度</Text>
                <Text fontSize="sm">{(learningStatus.model_accuracy * 100).toFixed(1)}%</Text>
              </HStack>
              <Progress 
                value={learningStatus.model_accuracy * 100} 
                colorScheme={learningStatus.model_accuracy > 0.8 ? 'green' : 'yellow'}
                size="sm"
              />
            </Box>

            <SimpleGrid columns={2} spacing={4}>
              <Stat size="sm">
                <StatLabel>推奨提供数</StatLabel>
                <StatNumber>{learningStatus.recommendations_given}</StatNumber>
              </Stat>
              <Stat size="sm">
                <StatLabel>満足度平均</StatLabel>
                <StatNumber>{learningStatus.user_satisfaction_avg.toFixed(1)}/5</StatNumber>
              </Stat>
              <Stat size="sm">
                <StatLabel>適応回数</StatLabel>
                <StatNumber>{learningStatus.adaptation_count}</StatNumber>
              </Stat>
              <Stat size="sm">
                <StatLabel>最終更新</StatLabel>
                <StatNumber fontSize="sm">
                  {new Date(learningStatus.last_model_update).toLocaleDateString('ja-JP')}
                </StatNumber>
              </Stat>
            </SimpleGrid>
          </VStack>
        </CardBody>
      </Card>
    );
  };

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
          <Heading size="lg">パーソナライゼーション</Heading>
          <Button
            leftIcon={<Icon as={FiSettings} />}
            onClick={fetchUserData}
            isLoading={isLoading}
            size="sm"
          >
            更新
          </Button>
        </HStack>

        {isLoading && (
          <HStack justify="center" py={8}>
            <Spinner size="lg" />
            <Text>パーソナライゼーションデータを読み込み中...</Text>
          </HStack>
        )}

        {!isLoading && (
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
            {/* User Profile */}
            {renderUserProfile()}

            {/* Learning Status */}
            {renderLearningStatus()}

            {/* Recommendations - Full Width */}
            <Box gridColumn={{ base: '1', lg: '1 / -1' }}>
              {renderRecommendations()}
            </Box>
          </SimpleGrid>
        )}

        {/* Feedback Modal */}
        <Modal isOpen={isOpen} onClose={onClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>推奨事項フィードバック</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {selectedRecommendation && (
                <VStack spacing={4} align="stretch">
                  <Text fontWeight="bold">{selectedRecommendation.title}</Text>
                  <Text fontSize="sm" color="gray.600">
                    {selectedRecommendation.description}
                  </Text>

                  <FormControl>
                    <FormLabel>満足度評価</FormLabel>
                    <Slider
                      value={feedbackRating}
                      onChange={setFeedbackRating}
                      min={1}
                      max={5}
                      step={1}
                    >
                      <SliderTrack>
                        <SliderFilledTrack />
                      </SliderTrack>
                      <SliderThumb />
                    </Slider>
                    <HStack justify="space-between" mt={2}>
                      <Text fontSize="xs">1 (不満)</Text>
                      <Text fontSize="sm" fontWeight="bold">{feedbackRating}</Text>
                      <Text fontSize="xs">5 (満足)</Text>
                    </HStack>
                  </FormControl>

                  <FormControl>
                    <FormLabel>コメント（任意）</FormLabel>
                    <Textarea
                      value={feedbackText}
                      onChange={(e) => setFeedbackText(e.target.value)}
                      placeholder="この推奨事項についてのご意見をお聞かせください..."
                      rows={3}
                    />
                  </FormControl>
                </VStack>
              )}
            </ModalBody>

            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onClose}>
                キャンセル
              </Button>
              <Button
                colorScheme="blue"
                onClick={() => {
                  if (selectedRecommendation) {
                    submitFeedback(selectedRecommendation.recommendation_id, feedbackRating > 3);
                  }
                }}
              >
                送信
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </VStack>
    </Box>
  );
}; 