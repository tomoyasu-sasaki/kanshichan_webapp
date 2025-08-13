import React from 'react';
import {
  FormControl,
  FormLabel,
  VStack,
  HStack,
  Switch,
  Box,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Text,
  SimpleGrid,
  Badge,
  Icon,
  useColorModeValue
} from '@chakra-ui/react';
import {
  FaSmile,
  FaSadTear,
  FaGrimace,
  FaFrown,
  FaSurprise,
  FaAngry,
  FaQuestion,
  FaMeh
} from 'react-icons/fa';
import type { VoiceSettings, TTSStatus } from '../types';
import { emotionTranslations } from '../constants';

interface EmotionSettingsProps {
  settings: VoiceSettings;
  ttsStatus: TTSStatus | null;
  onSettingsChange: (updates: Partial<VoiceSettings>) => void;
}

export const EmotionSettings: React.FC<EmotionSettingsProps> = ({
  settings,
  ttsStatus,
  onSettingsChange
}) => {
  // 感情プリセット選択ハンドラ
  const handleEmotionPresetChange = (emotion: string) => {
    // プリセット選択時に該当する感情を1.0、それ以外を0.0に設定
    const emotionValues = {
      emotionHappiness: emotion === 'happiness' ? 1.0 : 0.0,
      emotionSadness: emotion === 'sadness' ? 1.0 : 0.0,
      emotionDisgust: emotion === 'disgust' ? 1.0 : 0.0,
      emotionFear: emotion === 'fear' ? 1.0 : 0.0,
      emotionSurprise: emotion === 'surprise' ? 1.0 : 0.0,
      emotionAnger: emotion === 'anger' ? 1.0 : 0.0,
      emotionOther: emotion === 'other' ? 1.0 : 0.0,
      emotionNeutral: emotion === 'neutral' ? 1.0 : 0.0,
    };

    onSettingsChange({
      defaultEmotion: emotion,
      ...emotionValues
    });
  };

  const cardBg = useColorModeValue('gray.50', 'gray.700');

  // 感情アイコンマッピング
  const emotionIcons = {
    happiness: FaSmile,
    sadness: FaSadTear,
    disgust: FaGrimace,
    fear: FaFrown,
    surprise: FaSurprise,
    anger: FaAngry,
    other: FaQuestion,
    neutral: FaMeh
  };

  // 感情カラーマッピング
  const emotionColors = {
    happiness: 'yellow',
    sadness: 'blue',
    disgust: 'purple',
    fear: 'cyan',
    surprise: 'green',
    anger: 'red',
    other: 'orange',
    neutral: 'gray'
  };

  const availableEmotions = (ttsStatus?.available_emotions || ['neutral'])
    .filter((e) => ['neutral', 'happiness', 'sadness', 'disgust', 'fear', 'surprise', 'anger', 'other'].includes(e));

  return (
    <VStack spacing={6} align="stretch">
      <FormControl>
        <HStack justify="space-between" align="center" mb={4}>
          <FormLabel mb={0} fontWeight="semibold">感情設定モード</FormLabel>
          <HStack spacing={2}>
            <Text fontSize="sm" color="gray.600">詳細調整</Text>
            <Switch
              isChecked={settings.useEmotionPreset}
              onChange={(e) => onSettingsChange({ useEmotionPreset: e.target.checked })}
              colorScheme="blue"
            />
            <Text fontSize="sm" color="gray.600">プリセット</Text>
          </HStack>
        </HStack>

        {settings.useEmotionPreset ? (
          // プリセット選択モード
          <VStack spacing={4} align="stretch">
            <Text fontSize="sm" color="gray.600">
              感情プリセットから選択
            </Text>
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={3}>
              {availableEmotions.map((emotion) => {
                const IconComponent = emotionIcons[emotion as keyof typeof emotionIcons];
                const isSelected = settings.defaultEmotion === emotion;
                return (
                  <Box
                    key={emotion}
                    p={4}
                    borderRadius="lg"
                    border="2px solid"
                    borderColor={isSelected ? `${emotionColors[emotion as keyof typeof emotionColors]}.500` : 'gray.200'}
                    bg={isSelected ? `${emotionColors[emotion as keyof typeof emotionColors]}.50` : cardBg}
                    cursor="pointer"
                    onClick={() => handleEmotionPresetChange(emotion)}
                    transition="all 0.2s"
                    _hover={{
                      transform: 'translateY(-2px)',
                      shadow: 'md'
                    }}
                    _dark={{
                      borderColor: isSelected ? `${emotionColors[emotion as keyof typeof emotionColors]}.400` : 'gray.600',
                      bg: isSelected ? `${emotionColors[emotion as keyof typeof emotionColors]}.900` : 'gray.600'
                    }}
                  >
                    <VStack spacing={2}>
                      <Icon
                        as={IconComponent}
                        boxSize={6}
                        color={`${emotionColors[emotion as keyof typeof emotionColors]}.500`}
                      />
                      <Text fontWeight="medium" fontSize="sm">
                        {emotionTranslations[emotion] || emotion}
                      </Text>
                      {isSelected && (
                        <Badge colorScheme={emotionColors[emotion as keyof typeof emotionColors]} size="sm">
                          選択中
                        </Badge>
                      )}
                    </VStack>
                  </Box>
                );
              })}
            </SimpleGrid>
          </VStack>
        ) : (
          // 感情強度8軸スライダー
          <VStack spacing={4} align="stretch">
            <Text fontSize="sm" color="gray.600">
              感情強度を個別に調整（8軸）
            </Text>
            <SimpleGrid columns={1} spacing={4}>
              {/* 幸福 */}
              <FormControl>
                <HStack justify="space-between" mb={2}>
                  <HStack spacing={2}>
                    <Icon as={FaSmile} color="yellow.500" />
                    <FormLabel mb={0} fontSize="sm">幸福</FormLabel>
                  </HStack>
                  <Badge colorScheme="yellow" variant="outline">
                    {settings.emotionHappiness.toFixed(2)}
                  </Badge>
                </HStack>
                <Slider
                  value={settings.emotionHappiness}
                  onChange={(value) => onSettingsChange({ emotionHappiness: value })}
                  min={0}
                  max={1}
                  step={0.05}
                  colorScheme="yellow"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* 悲しみ */}
              <FormControl>
                <HStack justify="space-between" mb={2}>
                  <HStack spacing={2}>
                    <Icon as={FaSadTear} color="blue.500" />
                    <FormLabel mb={0} fontSize="sm">悲しみ</FormLabel>
                  </HStack>
                  <Badge colorScheme="blue" variant="outline">
                    {settings.emotionSadness.toFixed(2)}
                  </Badge>
                </HStack>
                <Slider
                  value={settings.emotionSadness}
                  onChange={(value) => onSettingsChange({ emotionSadness: value })}
                  min={0}
                  max={1}
                  step={0.05}
                  colorScheme="blue"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* 嫌悪 */}
              <FormControl>
                <HStack justify="space-between" mb={2}>
                  <HStack spacing={2}>
                    <Icon as={FaGrimace} color="purple.500" />
                    <FormLabel mb={0} fontSize="sm">嫌悪</FormLabel>
                  </HStack>
                  <Badge colorScheme="purple" variant="outline">
                    {settings.emotionDisgust.toFixed(2)}
                  </Badge>
                </HStack>
                <Slider
                  value={settings.emotionDisgust}
                  onChange={(value) => onSettingsChange({ emotionDisgust: value })}
                  min={0}
                  max={1}
                  step={0.05}
                  colorScheme="purple"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* 恐怖 */}
              <FormControl>
                <HStack justify="space-between" mb={2}>
                  <HStack spacing={2}>
                    <Icon as={FaFrown} color="cyan.500" />
                    <FormLabel mb={0} fontSize="sm">恐怖</FormLabel>
                  </HStack>
                  <Badge colorScheme="cyan" variant="outline">
                    {settings.emotionFear.toFixed(2)}
                  </Badge>
                </HStack>
                <Slider
                  value={settings.emotionFear}
                  onChange={(value) => onSettingsChange({ emotionFear: value })}
                  min={0}
                  max={1}
                  step={0.05}
                  colorScheme="cyan"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* 驚き */}
              <FormControl>
                <HStack justify="space-between" mb={2}>
                  <HStack spacing={2}>
                    <Icon as={FaSurprise} color="green.500" />
                    <FormLabel mb={0} fontSize="sm">驚き</FormLabel>
                  </HStack>
                  <Badge colorScheme="green" variant="outline">
                    {settings.emotionSurprise.toFixed(2)}
                  </Badge>
                </HStack>
                <Slider
                  value={settings.emotionSurprise}
                  onChange={(value) => onSettingsChange({ emotionSurprise: value })}
                  min={0}
                  max={1}
                  step={0.05}
                  colorScheme="green"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* 怒り */}
              <FormControl>
                <HStack justify="space-between" mb={2}>
                  <HStack spacing={2}>
                    <Icon as={FaAngry} color="red.500" />
                    <FormLabel mb={0} fontSize="sm">怒り</FormLabel>
                  </HStack>
                  <Badge colorScheme="red" variant="outline">
                    {settings.emotionAnger.toFixed(2)}
                  </Badge>
                </HStack>
                <Slider
                  value={settings.emotionAnger}
                  onChange={(value) => onSettingsChange({ emotionAnger: value })}
                  min={0}
                  max={1}
                  step={0.05}
                  colorScheme="red"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* その他 */}
              <FormControl>
                <HStack justify="space-between" mb={2}>
                  <HStack spacing={2}>
                    <Icon as={FaQuestion} color="orange.500" />
                    <FormLabel mb={0} fontSize="sm">その他</FormLabel>
                  </HStack>
                  <Badge colorScheme="orange" variant="outline">
                    {settings.emotionOther.toFixed(2)}
                  </Badge>
                </HStack>
                <Slider
                  value={settings.emotionOther}
                  onChange={(value) => onSettingsChange({ emotionOther: value })}
                  min={0}
                  max={1}
                  step={0.05}
                  colorScheme="orange"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              {/* 普通 */}
              <FormControl>
                <HStack justify="space-between" mb={2}>
                  <HStack spacing={2}>
                    <Icon as={FaMeh} color="gray.500" />
                    <FormLabel mb={0} fontSize="sm">普通</FormLabel>
                  </HStack>
                  <Badge colorScheme="gray" variant="outline">
                    {settings.emotionNeutral.toFixed(2)}
                  </Badge>
                </HStack>
                <Slider
                  value={settings.emotionNeutral}
                  onChange={(value) => onSettingsChange({ emotionNeutral: value })}
                  min={0}
                  max={1}
                  step={0.05}
                  colorScheme="gray"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>
            </SimpleGrid>
          </VStack>
        )}
      </FormControl>
    </VStack>
  );
};