import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  VStack,
  FormControl,
  FormLabel,
  Select,
  Text,
  HStack,
  Switch,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Box,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Button,
  Heading,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Icon,
  Badge,
  Divider,
  SimpleGrid,
  useColorModeValue
} from '@chakra-ui/react';
import { 
  FaVolumeUp, 
  FaCog, 
  FaHeart, 
  FaMusic, 
  FaWaveSquare, 
  FaRocket,
  FaMicrophone,
  FaRobot
} from 'react-icons/fa';
import type { VoiceSettings, TTSStatus } from '../types';
import { EmotionSettings } from './EmotionSettings';
import { AudioQualitySettings } from './AudioQualitySettings';
import { GenerationParameterSettings } from './GenerationParameterSettings';
import { AudioStyleSettings } from './AudioStyleSettings';
import { ProcessingOptions } from './ProcessingOptions';

interface BasicSettingsProps {
  settings: VoiceSettings;
  ttsStatus: TTSStatus | null;
  onSettingsChange: (settings: VoiceSettings) => void;
  onSaveAsDefault: () => void;
}

export const BasicSettings: React.FC<BasicSettingsProps> = ({
  settings,
  ttsStatus,
  onSettingsChange,
  onSaveAsDefault
}) => {
  const updateSettings = (updates: Partial<VoiceSettings>) => {
    onSettingsChange({ ...settings, ...updates });
  };

  const handleLanguageChange = (language: string) => {
    updateSettings({ defaultLanguage: language });
  };

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Card bg={cardBg} borderColor={borderColor} shadow="lg">
      <CardBody p={0}>
        <Tabs variant="enclosed" colorScheme="blue">
          <TabList px={6} pt={6}>
            <Tab>
              <HStack spacing={2}>
                <Icon as={FaCog} />
                <Text>基本設定</Text>
              </HStack>
            </Tab>
            <Tab>
              <HStack spacing={2}>
                <Icon as={FaHeart} />
                <Text>感情</Text>
              </HStack>
            </Tab>
            <Tab>
              <HStack spacing={2}>
                <Icon as={FaMusic} />
                <Text>音質</Text>
              </HStack>
            </Tab>
            <Tab>
              <HStack spacing={2}>
                <Icon as={FaWaveSquare} />
                <Text>詳細</Text>
              </HStack>
            </Tab>
          </TabList>

          <TabPanels>
            {/* 基本設定タブ */}
            <TabPanel px={6} pb={6}>
              <VStack spacing={6} align="stretch">
                {/* 音声モード選択 */}
                <Box>
                  <FormControl>
                    <FormLabel fontWeight="semibold" mb={3}>音声モード</FormLabel>
                    <SimpleGrid columns={2} spacing={3}>
                      <Box
                        p={4}
                        borderRadius="lg"
                        border="2px solid"
                        borderColor={settings.voiceMode === 'tts' ? 'blue.500' : 'gray.200'}
                        bg={settings.voiceMode === 'tts' ? 'blue.50' : 'gray.50'}
                        cursor="pointer"
                        onClick={() => updateSettings({ voiceMode: 'tts' })}
                        _dark={{
                          borderColor: settings.voiceMode === 'tts' ? 'blue.400' : 'gray.600',
                          bg: settings.voiceMode === 'tts' ? 'blue.900' : 'gray.700'
                        }}
                      >
                        <VStack spacing={2}>
                          <Icon as={FaMicrophone} boxSize={6} color="blue.500" />
                          <Text fontWeight="medium">TTS音声合成</Text>
                          <Text fontSize="xs" color="gray.600" textAlign="center">
                            標準の音声合成
                          </Text>
                        </VStack>
                      </Box>
                      <Box
                        p={4}
                        borderRadius="lg"
                        border="2px solid"
                        borderColor={settings.voiceMode === 'voiceClone' ? 'purple.500' : 'gray.200'}
                        bg={settings.voiceMode === 'voiceClone' ? 'purple.50' : 'gray.50'}
                        cursor="pointer"
                        onClick={() => updateSettings({ voiceMode: 'voiceClone' })}
                        _dark={{
                          borderColor: settings.voiceMode === 'voiceClone' ? 'purple.400' : 'gray.600',
                          bg: settings.voiceMode === 'voiceClone' ? 'purple.900' : 'gray.700'
                        }}
                      >
                        <VStack spacing={2}>
                          <Icon as={FaRobot} boxSize={6} color="purple.500" />
                          <Text fontWeight="medium">ボイスクローン</Text>
                          <Text fontSize="xs" color="gray.600" textAlign="center">
                            音声サンプル使用
                          </Text>
                        </VStack>
                      </Box>
                    </SimpleGrid>
                  </FormControl>
                </Box>

                <Divider />

                {/* 高速モード設定 */}
                <FormControl>
                  <HStack justify="space-between" align="center">
                    <VStack align="start" spacing={1}>
                      <HStack>
                        <Icon as={FaRocket} color="orange.500" />
                        <FormLabel mb={0} fontWeight="semibold">高速モード</FormLabel>
                        {settings.fastMode && <Badge colorScheme="orange" size="sm">ON</Badge>}
                      </HStack>
                      <Text fontSize="sm" color="gray.600">
                        {settings.fastMode
                          ? '約30秒で音声生成（シンプル処理）'
                          : '高品質音声生成（詳細処理）'}
                      </Text>
                    </VStack>
                    <Switch
                      isChecked={settings.fastMode}
                      onChange={(e) => updateSettings({ fastMode: e.target.checked })}
                      colorScheme="orange"
                      size="lg"
                    />
                  </HStack>
                  {settings.fastMode && (
                    <Alert status="info" mt={3} borderRadius="lg">
                      <AlertIcon />
                      <Box>
                        <AlertTitle fontSize="sm">高速モード有効</AlertTitle>
                        <AlertDescription fontSize="xs">
                          品質評価とキャッシュ機能を省略して高速化します
                        </AlertDescription>
                      </Box>
                    </Alert>
                  )}
                </FormControl>

                <Divider />

                {/* 言語設定 */}
                <FormControl>
                  <FormLabel fontWeight="semibold">デフォルト言語</FormLabel>
                  <Select
                    value={settings.defaultLanguage}
                    onChange={(e) => handleLanguageChange(e.target.value)}
                    size="lg"
                  >
                    {ttsStatus?.supported_languages?.map((language) => (
                      <option key={language} value={language}>
                        {language}
                      </option>
                    )) || (
                        <option value="ja">ja</option>
                      )}
                  </Select>
                </FormControl>

                {/* 音声パラメータ */}
                <VStack spacing={4} align="stretch">
                  <Text fontWeight="semibold" color="gray.700" _dark={{ color: 'gray.200' }}>
                    音声パラメータ
                  </Text>
                  
                  {/* 話速調整 */}
                  <FormControl>
                    <HStack justify="space-between" mb={2}>
                      <FormLabel mb={0}>話速</FormLabel>
                      <Badge colorScheme="blue" variant="outline">
                        {settings.voiceSpeed.toFixed(1)}x
                      </Badge>
                    </HStack>
                    <Slider
                      value={settings.voiceSpeed}
                      onChange={(value) => updateSettings({ voiceSpeed: value })}
                      min={0.5}
                      max={2.0}
                      step={0.1}
                      colorScheme="blue"
                    >
                      <SliderTrack>
                        <SliderFilledTrack />
                      </SliderTrack>
                      <SliderThumb />
                    </Slider>
                  </FormControl>

                  {/* 音程調整 */}
                  <FormControl>
                    <HStack justify="space-between" mb={2}>
                      <FormLabel mb={0}>音程</FormLabel>
                      <Badge colorScheme="green" variant="outline">
                        {settings.voicePitch.toFixed(1)}x
                      </Badge>
                    </HStack>
                    <Slider
                      value={settings.voicePitch}
                      onChange={(value) => updateSettings({ voicePitch: value })}
                      min={0.5}
                      max={2.0}
                      step={0.1}
                      colorScheme="green"
                    >
                      <SliderTrack>
                        <SliderFilledTrack />
                      </SliderTrack>
                      <SliderThumb />
                    </Slider>
                  </FormControl>

                  {/* 音量調整 */}
                  <FormControl>
                    <HStack justify="space-between" mb={2}>
                      <FormLabel mb={0}>音量</FormLabel>
                      <Badge colorScheme="purple" variant="outline">
                        {Math.round(settings.voiceVolume * 100)}%
                      </Badge>
                    </HStack>
                    <Slider
                      value={settings.voiceVolume}
                      onChange={(value) => updateSettings({ voiceVolume: value })}
                      min={0}
                      max={1}
                      step={0.1}
                      colorScheme="purple"
                    >
                      <SliderTrack>
                        <SliderFilledTrack />
                      </SliderTrack>
                      <SliderThumb />
                    </Slider>
                  </FormControl>
                </VStack>

                {/* デフォルト設定ボタン */}
                <Button
                  colorScheme="teal"
                  leftIcon={<FaVolumeUp />}
                  onClick={onSaveAsDefault}
                  size="lg"
                  mt={4}
                >
                  デフォルト音声に設定する
                </Button>
              </VStack>
            </TabPanel>

            {/* 感情設定タブ */}
            <TabPanel px={6} pb={6}>
              <EmotionSettings
                settings={settings}
                ttsStatus={ttsStatus}
                onSettingsChange={updateSettings}
              />
            </TabPanel>

            {/* 音質設定タブ */}
            <TabPanel px={6} pb={6}>
              <VStack spacing={6} align="stretch">
                <AudioQualitySettings
                  settings={settings}
                  onSettingsChange={updateSettings}
                />
                <AudioStyleSettings
                  settings={settings}
                  onSettingsChange={updateSettings}
                />
              </VStack>
            </TabPanel>

            {/* 詳細設定タブ */}
            <TabPanel px={6} pb={6}>
              <VStack spacing={6} align="stretch">
                <GenerationParameterSettings
                  settings={settings}
                  onSettingsChange={updateSettings}
                />
                <ProcessingOptions
                  settings={settings}
                  onSettingsChange={updateSettings}
                />
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </CardBody>
    </Card>
  );
};