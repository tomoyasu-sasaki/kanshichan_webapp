import React from 'react';
import {
  Box,
  HStack,
  VStack,
  Heading,
  Badge,
  Alert,
  AlertIcon,
  Text,
  Icon,
  Flex,
  useColorModeValue
} from '@chakra-ui/react';
import { FaMicrophone, FaRobot } from 'react-icons/fa';
import type { TTSStatus } from '../types';

interface VoiceSettingsHeaderProps {
  loadingTTSStatus: boolean;
  ttsStatus: TTSStatus | null;
}

export const VoiceSettingsHeader: React.FC<VoiceSettingsHeaderProps> = ({
  loadingTTSStatus,
  ttsStatus
}) => {
  const bgGradient = useColorModeValue(
    'linear(to-r, blue.50, purple.50)',
    'linear(to-r, blue.900, purple.900)'
  );
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const getStatusInfo = () => {
    if (loadingTTSStatus) {
      return { color: 'yellow', text: '初期化中', icon: FaRobot };
    }
    if (ttsStatus?.initialized) {
      return { color: 'green', text: '利用可能', icon: FaMicrophone };
    }
    if (ttsStatus && !ttsStatus.initialized) {
      return { color: 'red', text: '初期化失敗', icon: FaRobot };
    }
    return { color: 'red', text: '接続エラー', icon: FaRobot };
  };

  const statusInfo = getStatusInfo();

  return (
    <VStack spacing={4} align="stretch">
      {/* メインヘッダー */}
      <Box
        bgGradient={bgGradient}
        borderRadius="xl"
        border="1px solid"
        borderColor={borderColor}
        p={6}
        shadow="sm"
      >
        <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
          <VStack align="start" spacing={1}>
            <HStack spacing={3}>
              <Icon as={FaMicrophone} boxSize={6} color="blue.500" />
              <Heading size="lg" color="gray.700" _dark={{ color: 'gray.100' }}>
                音声設定
              </Heading>
            </HStack>
            <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.300' }}>
              音声合成とボイスクローンの詳細設定
            </Text>
          </VStack>

          <VStack align="end" spacing={2}>
            <HStack spacing={2}>
              <Icon as={statusInfo.icon} color={`${statusInfo.color}.500`} />
              <Badge 
                colorScheme={statusInfo.color} 
                variant="subtle" 
                px={3} 
                py={1} 
                borderRadius="full"
                fontSize="sm"
              >
                {statusInfo.text}
              </Badge>
            </HStack>
            {ttsStatus && (
              <Text fontSize="xs" color="gray.500" textAlign="right">
                モデル: {ttsStatus.model_name} | デバイス: {ttsStatus.device}
              </Text>
            )}
          </VStack>
        </Flex>
      </Box>

      {/* 警告メッセージ */}
      {ttsStatus && !ttsStatus.voice_cloning_enabled && (
        <Alert status="warning" borderRadius="lg">
          <AlertIcon />
          <VStack align="start" spacing={1}>
            <Text fontWeight="medium">音声クローン機能が無効</Text>
            <Text fontSize="sm">
              ボイスクローン機能を使用するには、サーバー設定を確認してください
            </Text>
          </VStack>
        </Alert>
      )}
    </VStack>
  );
};