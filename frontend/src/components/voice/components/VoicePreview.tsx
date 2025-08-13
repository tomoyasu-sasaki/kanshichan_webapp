import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  VStack,
  FormControl,
  FormLabel,
  Textarea,
  HStack,
  Button,
  IconButton,
  Tooltip,
  Progress,
  Heading,
  Text,
  Box,
  Icon,
  useColorModeValue,
  Flex
} from '@chakra-ui/react';
import { FaPlay, FaStop, FaVolumeUp, FaMicrophone } from 'react-icons/fa';
import type { VoiceSettings, TTSStatus } from '../types';

interface VoicePreviewProps {
  settings: VoiceSettings;
  ttsStatus: TTSStatus | null;
  loadingTTSStatus: boolean;
  onPreview: (testText: string, settings: VoiceSettings) => Promise<void>;
  previewing: boolean;
}

export const VoicePreview: React.FC<VoicePreviewProps> = ({
  settings,
  ttsStatus,
  loadingTTSStatus,
  onPreview,
  previewing
}) => {
  const [testText, setTestText] = useState('これは音声設定のテストです。設定した感情とトーンで再生されます。');

  const handlePreview = () => {
    onPreview(testText, settings);
  };

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const gradientBg = useColorModeValue(
    'linear(to-br, blue.50, purple.50)',
    'linear(to-br, blue.900, purple.900)'
  );

  const isDisabled = !testText.trim() || loadingTTSStatus || (!!settings.voiceSampleId && !ttsStatus?.initialized);

  return (
    <Card bg={cardBg} borderColor={borderColor} shadow="lg">
      <CardHeader pb={2}>
        <Flex align="center" justify="space-between">
          <HStack spacing={3}>
            <Icon as={FaMicrophone} color="blue.500" boxSize={5} />
            <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
              音声プレビュー
            </Heading>
          </HStack>
          <Tooltip label="現在の設定で音声を生成・再生します">
            <IconButton
              aria-label="ヘルプ"
              icon={<FaVolumeUp />}
              size="sm"
              variant="ghost"
              color="gray.500"
            />
          </Tooltip>
        </Flex>
      </CardHeader>
      
      <CardBody pt={2}>
        <VStack spacing={5} align="stretch">
          <FormControl>
            <FormLabel fontWeight="semibold" mb={3}>テスト用テキスト</FormLabel>
            <Textarea
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              placeholder="プレビューで読み上げるテキストを入力してください"
              size="md"
              minH="100px"
              borderRadius="lg"
              _focus={{
                borderColor: 'blue.400',
                boxShadow: '0 0 0 1px var(--chakra-colors-blue-400)'
              }}
            />
            <Text fontSize="xs" color="gray.500" mt={2}>
              文字数: {testText.length}
            </Text>
          </FormControl>

          {/* プレビューコントロール */}
          <Box
            bgGradient={gradientBg}
            borderRadius="xl"
            p={4}
            border="1px solid"
            borderColor={borderColor}
          >
            <VStack spacing={3}>
              <Button
                leftIcon={previewing ? <FaStop /> : <FaPlay />}
                onClick={handlePreview}
                colorScheme={previewing ? 'red' : 'blue'}
                isLoading={loadingTTSStatus}
                loadingText="初期化中..."
                isDisabled={isDisabled}
                size="lg"
                width="full"
                borderRadius="lg"
              >
                {previewing ? '停止' : 'プレビュー再生'}
              </Button>

              {previewing && (
                <Box width="full">
                  <Text fontSize="sm" color="gray.600" mb={2} textAlign="center">
                    音声を生成中...
                  </Text>
                  <Progress 
                    size="md" 
                    isIndeterminate 
                    colorScheme="blue" 
                    borderRadius="full"
                  />
                </Box>
              )}

              {isDisabled && !loadingTTSStatus && (
                <Text fontSize="xs" color="gray.500" textAlign="center">
                  {!testText.trim() 
                    ? 'テキストを入力してください' 
                    : 'TTSサービスの初期化を待っています...'}
                </Text>
              )}
            </VStack>
          </Box>

          {/* 設定サマリー */}
          <Box
            bg={useColorModeValue('gray.50', 'gray.700')}
            borderRadius="lg"
            p={3}
          >
            <Text fontSize="xs" fontWeight="semibold" color="gray.600" mb={2}>
              現在の設定
            </Text>
            <HStack spacing={4} wrap="wrap">
              <Text fontSize="xs" color="gray.500">
                モード: {settings.voiceMode === 'tts' ? 'TTS' : 'ボイスクローン'}
              </Text>
              <Text fontSize="xs" color="gray.500">
                感情: {settings.defaultEmotion}
              </Text>
              <Text fontSize="xs" color="gray.500">
                話速: {settings.voiceSpeed.toFixed(1)}x
              </Text>
              <Text fontSize="xs" color="gray.500">
                音程: {settings.voicePitch.toFixed(1)}x
              </Text>
            </HStack>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
};