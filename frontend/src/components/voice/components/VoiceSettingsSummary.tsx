import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  VStack,
  HStack,
  Text,
  Badge,
  Divider,
  Heading,
  Box,
  Icon,
  SimpleGrid,
  Progress,
  useColorModeValue
} from '@chakra-ui/react';
import { 
  FaMicrophone, 
  FaRobot, 
  FaHeart, 
  FaLanguage, 
  FaTachometerAlt,
  FaVolumeUp,
  FaRocket,
  FaWaveSquare,
  FaMusic
} from 'react-icons/fa';
import type { VoiceSettings } from '../types';
import { emotionTranslations } from '../constants';

interface VoiceSettingsSummaryProps {
  settings: VoiceSettings;
}

export const VoiceSettingsSummary: React.FC<VoiceSettingsSummaryProps> = ({
  settings
}) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const sectionBg = useColorModeValue('gray.50', 'gray.700');

  return (
    <Card bg={cardBg} borderColor={borderColor} shadow="lg">
      <CardHeader pb={2}>
        <HStack spacing={3}>
          <Icon as={FaMusic} color="teal.500" boxSize={5} />
          <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
            設定サマリー
          </Heading>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        <VStack spacing={4} align="stretch">
          {/* 基本設定セクション */}
          <Box bg={sectionBg} borderRadius="lg" p={4}>
            <Text fontWeight="semibold" fontSize="sm" color="gray.600" mb={3}>
              基本設定
            </Text>
            <SimpleGrid columns={1} spacing={3}>
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <Icon as={settings.voiceMode === 'voiceClone' ? FaRobot : FaMicrophone} 
                        color={settings.voiceMode === 'voiceClone' ? 'purple.500' : 'blue.500'} 
                        boxSize={4} />
                  <Text fontSize="sm">音声モード</Text>
                </HStack>
                <Badge colorScheme={settings.voiceMode === 'voiceClone' ? 'purple' : 'blue'} variant="subtle">
                  {settings.voiceMode === 'voiceClone' ? 'ボイスクローン' : 'TTS音声合成'}
                </Badge>
              </HStack>
              
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <Icon as={FaHeart} color="pink.500" boxSize={4} />
                  <Text fontSize="sm">感情</Text>
                </HStack>
                <Badge colorScheme="pink" variant="subtle">
                  {emotionTranslations[settings.defaultEmotion] || settings.defaultEmotion}
                </Badge>
              </HStack>
              
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <Icon as={FaLanguage} color="green.500" boxSize={4} />
                  <Text fontSize="sm">言語</Text>
                </HStack>
                <Badge colorScheme="green" variant="subtle">
                  {settings.defaultLanguage}
                </Badge>
              </HStack>
              
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <Icon as={FaRocket} color="orange.500" boxSize={4} />
                  <Text fontSize="sm">高速モード</Text>
                </HStack>
                <Badge colorScheme={settings.fastMode ? 'orange' : 'gray'} variant="subtle">
                  {settings.fastMode ? 'ON' : 'OFF'}
                </Badge>
              </HStack>
            </SimpleGrid>
          </Box>

          {/* 音声パラメータセクション */}
          <Box bg={sectionBg} borderRadius="lg" p={4}>
            <Text fontWeight="semibold" fontSize="sm" color="gray.600" mb={3}>
              音声パラメータ
            </Text>
            <VStack spacing={3} align="stretch">
              <HStack justify="space-between">
                <Text fontSize="sm">話速</Text>
                <HStack spacing={2}>
                  <Progress 
                    value={(settings.voiceSpeed - 0.5) / 1.5 * 100} 
                    size="sm" 
                    width="60px" 
                    colorScheme="blue"
                    borderRadius="full"
                  />
                  <Badge colorScheme="blue" variant="outline" minW="50px">
                    {settings.voiceSpeed.toFixed(1)}x
                  </Badge>
                </HStack>
              </HStack>
              
              <HStack justify="space-between">
                <Text fontSize="sm">音程</Text>
                <HStack spacing={2}>
                  <Progress 
                    value={(settings.voicePitch - 0.5) / 1.5 * 100} 
                    size="sm" 
                    width="60px" 
                    colorScheme="green"
                    borderRadius="full"
                  />
                  <Badge colorScheme="green" variant="outline" minW="50px">
                    {settings.voicePitch.toFixed(1)}x
                  </Badge>
                </HStack>
              </HStack>
              
              <HStack justify="space-between">
                <Text fontSize="sm">音量</Text>
                <HStack spacing={2}>
                  <Progress 
                    value={settings.voiceVolume * 100} 
                    size="sm" 
                    width="60px" 
                    colorScheme="purple"
                    borderRadius="full"
                  />
                  <Badge colorScheme="purple" variant="outline" minW="50px">
                    {Math.round(settings.voiceVolume * 100)}%
                  </Badge>
                </HStack>
              </HStack>
            </VStack>
          </Box>

          {/* 音質設定セクション */}
          <Box bg={sectionBg} borderRadius="lg" p={4}>
            <Text fontWeight="semibold" fontSize="sm" color="gray.600" mb={3}>
              音質設定
            </Text>
            <SimpleGrid columns={1} spacing={3}>
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <Icon as={FaWaveSquare} color="cyan.500" boxSize={4} />
                  <Text fontSize="sm">最大周波数</Text>
                </HStack>
                <Badge colorScheme="cyan" variant="outline">
                  {settings.maxFrequency}Hz
                </Badge>
              </HStack>
              
              <HStack justify="space-between">
                <Text fontSize="sm">音質スコア</Text>
                <HStack spacing={2}>
                  <Progress 
                    value={settings.audioQuality / 5 * 100} 
                    size="sm" 
                    width="60px" 
                    colorScheme="teal"
                    borderRadius="full"
                  />
                  <Badge colorScheme="teal" variant="outline" minW="50px">
                    {settings.audioQuality.toFixed(1)}
                  </Badge>
                </HStack>
              </HStack>
              
              <HStack justify="space-between">
                <Text fontSize="sm">VQスコア</Text>
                <HStack spacing={2}>
                  <Progress 
                    value={settings.vqScore * 100} 
                    size="sm" 
                    width="60px" 
                    colorScheme="yellow"
                    borderRadius="full"
                  />
                  <Badge colorScheme="yellow" variant="outline" minW="50px">
                    {settings.vqScore.toFixed(2)}
                  </Badge>
                </HStack>
              </HStack>
            </SimpleGrid>
          </Box>

          {/* ボイスクローン設定 */}
          {settings.voiceMode === 'voiceClone' && (
            <Box bg={sectionBg} borderRadius="lg" p={4}>
              <Text fontWeight="semibold" fontSize="sm" color="gray.600" mb={3}>
                ボイスクローン
              </Text>
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <Icon as={FaRobot} color="purple.500" boxSize={4} />
                  <Text fontSize="sm">音声サンプル</Text>
                </HStack>
                <Badge colorScheme={settings.voiceSampleId ? 'green' : 'gray'} variant="subtle">
                  {settings.voiceSampleId ? '設定済み' : '未設定'}
                </Badge>
              </HStack>
            </Box>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};