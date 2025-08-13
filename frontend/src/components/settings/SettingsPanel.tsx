import {
  Box,
  VStack,
  Heading,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Button,
  useToast,
  Text,
  Switch,
  Container,
  Card,
  CardHeader,
  CardBody,
  SimpleGrid,
  HStack,
  Icon,
  Avatar,
  Badge,
  useColorModeValue,
  Flex,
  Tooltip,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText
} from '@chakra-ui/react';
import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { logger } from '../../utils/logger';
import {
  FaCog,
  FaEye,
  FaUser,
  FaSave,
  FaSlidersH,
  FaToggleOn,
  FaToggleOff
} from 'react-icons/fa';
import {
  FiActivity,
  FiSmartphone,
  FiUser,
  FiEye,
  FiTarget,
  FiCheckCircle
} from 'react-icons/fi';

interface Settings {
  absence_threshold: number;
  smartphone_threshold: number;
  landmark_settings: {
    [key: string]: {
      enabled: boolean;
      name: string;
    };
  };
  detection_objects: {
    [key: string]: {
      enabled: boolean;
      name: string;
      confidence_threshold: number;
      alert_threshold: number;
    };
  };
}

export const SettingsPanel = () => {
  const { t } = useTranslation();
  const [settings, setSettings] = useState<Settings>({
    absence_threshold: 5,
    smartphone_threshold: 3,
    landmark_settings: {},
    detection_objects: {}
  });
  const toast = useToast();

  const fetchedOnceRef = useRef(false);
  const API_BASE = '/api/v1/settings/'; // 末尾スラッシュ付きで直接正しいエンドポイントへ

  const fetchSettings = useCallback(async () => {
    try {
      await logger.info('SettingsPanel: 設定取得開始',
        { component: 'SettingsPanel', action: 'fetch_settings_start' },
        'SettingsPanel'
      );

      const response = await axios.get(API_BASE);

      const payload = response.data?.data || response.data;
      const fetchedSettings = {
        absence_threshold: payload.absence_threshold,
        smartphone_threshold: payload.smartphone_threshold,
        landmark_settings: payload.landmark_settings,
        detection_objects: payload.detection_objects
      };

      setSettings(fetchedSettings);

      await logger.info('SettingsPanel: 設定取得成功',
        {
          component: 'SettingsPanel',
          action: 'fetch_settings_success',
          settingsCount: Object.keys(fetchedSettings).length,
          absenceThreshold: fetchedSettings.absence_threshold,
          smartphoneThreshold: fetchedSettings.smartphone_threshold
        },
        'SettingsPanel'
      );

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);

      await logger.error('SettingsPanel: 設定取得エラー',
        {
          component: 'SettingsPanel',
          action: 'fetch_settings_error',
          error: errorMessage,
          endpoint: '/api/v1/settings'
        },
        'SettingsPanel'
      );

      console.error('Settings fetch error:', err);
      toast({
        title: t('common.error'),
        description: t('settings.error'),
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  }, [toast]);

  useEffect(() => {
    const initSettingsPanel = async () => {
      await logger.info('SettingsPanel: コンポーネント初期化',
        { component: 'SettingsPanel', action: 'initialize' },
        'SettingsPanel'
      );

      // StrictModeなどで二重実行されないようガード
      if (!fetchedOnceRef.current) {
        fetchedOnceRef.current = true;
        await fetchSettings();
      }
    };

    void initSettingsPanel();
  }, [fetchSettings]);

  const handleSave = async () => {
    try {
      await logger.info('SettingsPanel: 設定保存開始',
        {
          component: 'SettingsPanel',
          action: 'save_settings_start',
          settings: {
            absence_threshold: settings.absence_threshold,
            smartphone_threshold: settings.smartphone_threshold,
            landmark_settings_count: Object.keys(settings.landmark_settings).length,
            detection_objects_count: Object.keys(settings.detection_objects).length
          }
        },
        'SettingsPanel'
      );

      const requestData = {
        absence_threshold: settings.absence_threshold,
        smartphone_threshold: settings.smartphone_threshold,
        landmark_settings: settings.landmark_settings,
        detection_objects: settings.detection_objects
      };

      await axios.post(API_BASE, requestData);

      await logger.info('SettingsPanel: 設定保存成功',
        {
          component: 'SettingsPanel',
          action: 'save_settings_success',
          savedSettings: requestData
        },
        'SettingsPanel'
      );

      toast({
        title: t('common.success'),
        description: t('settings.saved'),
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);

      await logger.error('SettingsPanel: 設定保存エラー',
        {
          component: 'SettingsPanel',
          action: 'save_settings_error',
          error: errorMessage,
          endpoint: '/api/v1/settings'
        },
        'SettingsPanel'
      );

      console.error('Settings save error:', err);
      toast({
        title: t('common.error'),
        description: t('settings.error'),
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleThresholdChange = async (field: string, value: number) => {
    const oldValue = settings[field as keyof Pick<Settings, 'absence_threshold' | 'smartphone_threshold'>];

    setSettings(prev => ({
      ...prev,
      [field]: value
    }));

    await logger.debug('SettingsPanel: 閾値変更',
      {
        component: 'SettingsPanel',
        action: 'threshold_change',
        field,
        oldValue,
        newValue: value
      },
      'SettingsPanel'
    );
  };

  const handleLandmarkToggle = async (key: string) => {
    const oldEnabled = settings.landmark_settings[key]?.enabled;
    const newEnabled = !oldEnabled;

    const newSettings = {
      ...settings,
      landmark_settings: {
        ...settings.landmark_settings,
        [key]: {
          ...settings.landmark_settings[key],
          enabled: newEnabled
        }
      }
    };
    setSettings(newSettings);

    await logger.info('SettingsPanel: ランドマーク設定切り替え',
      {
        component: 'SettingsPanel',
        action: 'landmark_toggle',
        landmarkKey: key,
        oldEnabled,
        newEnabled,
        landmarkName: settings.landmark_settings[key]?.name
      },
      'SettingsPanel'
    );
  };

  const handleObjectSettingChange = async (
    key: string,
    field: 'enabled' | 'confidence_threshold' | 'alert_threshold',
    value: boolean | number
  ) => {
    const oldValue = settings.detection_objects[key]?.[field];

    const newSettings = {
      ...settings,
      detection_objects: {
        ...settings.detection_objects,
        [key]: {
          ...settings.detection_objects[key],
          [field]: value
        }
      }
    };
    setSettings(newSettings);

    await logger.debug('SettingsPanel: 検知オブジェクト設定変更',
      {
        component: 'SettingsPanel',
        action: 'detection_object_change',
        objectKey: key,
        field,
        oldValue,
        newValue: value,
        objectName: settings.detection_objects[key]?.name
      },
      'SettingsPanel'
    );
  };

  const cardBg = useColorModeValue('white', 'gray.800');
  const gradientBg = useColorModeValue(
    'linear(to-r, purple.50, blue.50)',
    'linear(to-r, purple.900, blue.900)'
  );

  // 統計情報の計算
  const stats = {
    totalLandmarks: Object.keys(settings.landmark_settings).length,
    enabledLandmarks: Object.values(settings.landmark_settings).filter(l => l.enabled).length,
    totalObjects: Object.keys(settings.detection_objects).length,
    enabledObjects: Object.values(settings.detection_objects).filter(o => o.enabled).length
  };

  return (
    <Container maxW="1400px" px={{ base: 4, md: 6 }}>
      <VStack spacing={8} align="stretch">
        {/* ヘッダーセクション */}
        <Box
          bgGradient={gradientBg}
          borderRadius="xl"
          border="1px solid"
          borderColor={useColorModeValue('gray.200', 'gray.600')}
          p={6}
          shadow="lg"
        >
          <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
            <VStack align="start" spacing={3}>
              <HStack spacing={4}>
                <Avatar
                  icon={<Icon as={FaCog} />}
                  bg="purple.500"
                  size="lg"
                />
                <VStack align="start" spacing={1}>
                  <Heading size="xl" color="gray.700" _dark={{ color: 'gray.100' }}>
                    システム設定
                  </Heading>
                  <Text fontSize="md" color="gray.600" _dark={{ color: 'gray.300' }}>
                    検知パラメータと動作設定の管理
                  </Text>
                </VStack>
              </HStack>

              {/* ステータスバッジ */}
              <HStack spacing={4} wrap="wrap">
                <Badge colorScheme="green" px={3} py={1} borderRadius="full">
                  <HStack spacing={1}>
                    <Icon as={FiCheckCircle} boxSize={3} />
                    <Text fontSize="sm">設定読み込み完了</Text>
                  </HStack>
                </Badge>
                <Badge colorScheme="blue" px={3} py={1} borderRadius="full">
                  <HStack spacing={1}>
                    <Icon as={FiActivity} boxSize={3} />
                    <Text fontSize="sm">リアルタイム適用</Text>
                  </HStack>
                </Badge>
              </HStack>
            </VStack>

            {/* 統計情報 */}
            <VStack spacing={3} align="end">
              <SimpleGrid columns={2} spacing={4}>
                <Stat textAlign="center">
                  <StatLabel fontSize="xs">ランドマーク</StatLabel>
                  <StatNumber fontSize="lg" color="green.500">
                    {stats.enabledLandmarks}/{stats.totalLandmarks}
                  </StatNumber>
                  <StatHelpText fontSize="xs">有効/総数</StatHelpText>
                </Stat>
                <Stat textAlign="center">
                  <StatLabel fontSize="xs">検知オブジェクト</StatLabel>
                  <StatNumber fontSize="lg" color="blue.500">
                    {stats.enabledObjects}/{stats.totalObjects}
                  </StatNumber>
                  <StatHelpText fontSize="xs">有効/総数</StatHelpText>
                </Stat>
              </SimpleGrid>
            </VStack>
          </Flex>
        </Box>

        {/* メインコンテンツ */}
        <Tabs variant="enclosed" colorScheme="purple">
          <TabList>
            <Tab>
              <HStack spacing={2}>
                <Icon as={FaSlidersH} />
                <Text>基本設定</Text>
              </HStack>
            </Tab>
            <Tab>
              <HStack spacing={2}>
                <Icon as={FaUser} />
                <Text>ランドマーク</Text>
              </HStack>
            </Tab>
            <Tab>
              <HStack spacing={2}>
                <Icon as={FaEye} />
                <Text>検知オブジェクト</Text>
              </HStack>
            </Tab>
          </TabList>

          <TabPanels>
            {/* 基本設定タブ */}
            <TabPanel px={0} py={6}>
              <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
                {/* 閾値設定 */}
                <Card bg={cardBg} shadow="lg">
                  <CardHeader pb={2}>
                    <HStack spacing={3}>
                      <Icon as={FiTarget} color="red.500" boxSize={5} />
                      <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                        検知閾値設定
                      </Heading>
                    </HStack>
                  </CardHeader>
                  <CardBody pt={2}>
                    <VStack spacing={6} align="stretch">
                      {/* 不在閾値 */}
                      <Box
                        p={4}
                        borderRadius="lg"
                        bg={useColorModeValue('red.50', 'red.900')}
                        border="1px solid"
                        borderColor={useColorModeValue('red.200', 'red.700')}
                      >
                        <VStack spacing={4} align="stretch">
                          <HStack justify="space-between" align="center">
                            <HStack spacing={3}>
                              <Avatar
                                icon={<Icon as={FiUser} />}
                                bg="red.500"
                                size="sm"
                              />
                              <VStack align="start" spacing={0}>
                                <Text fontWeight="semibold" fontSize="sm">
                                  不在検知閾値
                                </Text>
                                <Text fontSize="xs" color="gray.500">
                                  不在と判定するまでの時間（秒）
                                </Text>
                              </VStack>
                            </HStack>
                            <Badge colorScheme="red" variant="outline">
                              {settings.absence_threshold}秒
                            </Badge>
                          </HStack>
                          <NumberInput
                            value={settings.absence_threshold}
                            min={1}
                            max={60}
                            onChange={(_, value) => handleThresholdChange('absence_threshold', value)}
                            size="lg"
                          >
                            <NumberInputField borderRadius="lg" />
                            <NumberInputStepper>
                              <NumberIncrementStepper />
                              <NumberDecrementStepper />
                            </NumberInputStepper>
                          </NumberInput>
                        </VStack>
                      </Box>

                      {/* スマートフォン閾値 */}
                      <Box
                        p={4}
                        borderRadius="lg"
                        bg={useColorModeValue('orange.50', 'orange.900')}
                        border="1px solid"
                        borderColor={useColorModeValue('orange.200', 'orange.700')}
                      >
                        <VStack spacing={4} align="stretch">
                          <HStack justify="space-between" align="center">
                            <HStack spacing={3}>
                              <Avatar
                                icon={<Icon as={FiSmartphone} />}
                                bg="orange.500"
                                size="sm"
                              />
                              <VStack align="start" spacing={0}>
                                <Text fontWeight="semibold" fontSize="sm">
                                  スマートフォン検知閾値
                                </Text>
                                <Text fontSize="xs" color="gray.500">
                                  使用中と判定するまでの時間（秒）
                                </Text>
                              </VStack>
                            </HStack>
                            <Badge colorScheme="orange" variant="outline">
                              {settings.smartphone_threshold}秒
                            </Badge>
                          </HStack>
                          <NumberInput
                            value={settings.smartphone_threshold}
                            min={1}
                            max={30}
                            onChange={(_, value) => handleThresholdChange('smartphone_threshold', value)}
                            size="lg"
                          >
                            <NumberInputField borderRadius="lg" />
                            <NumberInputStepper>
                              <NumberIncrementStepper />
                              <NumberDecrementStepper />
                            </NumberInputStepper>
                          </NumberInput>
                        </VStack>
                      </Box>
                    </VStack>
                  </CardBody>
                </Card>

                {/* 保存アクション */}
                <Card bg={cardBg} shadow="lg">
                  <CardHeader pb={2}>
                    <HStack spacing={3}>
                      <Icon as={FaSave} color="green.500" boxSize={5} />
                      <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                        設定の保存
                      </Heading>
                    </HStack>
                  </CardHeader>
                  <CardBody pt={2}>
                    <VStack spacing={4} align="stretch">
                      <Alert status="info" borderRadius="lg">
                        <AlertIcon />
                        <Box>
                          <AlertTitle fontSize="sm">設定の適用について</AlertTitle>
                          <AlertDescription fontSize="xs">
                            変更した設定は保存ボタンを押すことで即座にシステムに適用されます。
                          </AlertDescription>
                        </Box>
                      </Alert>

                      <Button
                        colorScheme="green"
                        onClick={handleSave}
                        size="lg"
                        leftIcon={<FaSave />}
                        borderRadius="lg"
                        width="full"
                      >
                        設定を保存
                      </Button>

                      <Text fontSize="xs" color="gray.500" textAlign="center">
                        最後に保存した設定がシステム全体に適用されます
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>
              </SimpleGrid>
            </TabPanel>

            {/* ランドマーク設定タブ */}
            <TabPanel px={0} py={6}>
              <Card bg={cardBg} shadow="lg">
                <CardHeader pb={2}>
                  <HStack justify="space-between" align="center">
                    <HStack spacing={3}>
                      <Icon as={FaUser} color="blue.500" boxSize={5} />
                      <VStack align="start" spacing={0}>
                        <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                          ランドマーク検知設定
                        </Heading>
                        <Text fontSize="sm" color="gray.500">
                          人体の特徴点検知の有効/無効を設定
                        </Text>
                      </VStack>
                    </HStack>
                    <Badge colorScheme="blue" variant="subtle" px={3} py={1} borderRadius="full">
                      {stats.enabledLandmarks}/{stats.totalLandmarks} 有効
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody pt={2}>
                  {Object.keys(settings.landmark_settings).length === 0 ? (
                    <Alert status="warning" borderRadius="lg">
                      <AlertIcon />
                      <Box>
                        <AlertTitle>ランドマーク設定が見つかりません</AlertTitle>
                        <AlertDescription>
                          システムからランドマーク設定を読み込めませんでした。
                        </AlertDescription>
                      </Box>
                    </Alert>
                  ) : (
                    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
                      {Object.entries(settings.landmark_settings).map(([key, value]) => (
                        <Box
                          key={key}
                          p={4}
                          borderRadius="lg"
                          border="2px solid"
                          borderColor={value.enabled
                            ? useColorModeValue('green.200', 'green.600')
                            : useColorModeValue('gray.200', 'gray.600')
                          }
                          bg={value.enabled
                            ? useColorModeValue('green.50', 'green.900')
                            : useColorModeValue('gray.50', 'gray.700')
                          }
                          transition="all 0.2s"
                          _hover={{
                            transform: 'translateY(-2px)',
                            shadow: 'md'
                          }}
                        >
                          <VStack spacing={3} align="stretch">
                            <HStack justify="space-between" align="center">
                              <Avatar
                                icon={<Icon as={value.enabled ? FaToggleOn : FaToggleOff} />}
                                bg={value.enabled ? 'green.500' : 'gray.500'}
                                size="sm"
                              />
                              <Switch
                                isChecked={value.enabled}
                                onChange={() => handleLandmarkToggle(key)}
                                colorScheme="green"
                                size="lg"
                              />
                            </HStack>
                            <VStack align="start" spacing={1}>
                              <Text fontWeight="semibold" fontSize="sm">
                                {value.name}
                              </Text>
                              <Badge
                                colorScheme={value.enabled ? 'green' : 'gray'}
                                variant="subtle"
                                fontSize="xs"
                              >
                                {value.enabled ? '有効' : '無効'}
                              </Badge>
                            </VStack>
                          </VStack>
                        </Box>
                      ))}
                    </SimpleGrid>
                  )}
                </CardBody>
              </Card>
            </TabPanel>

            {/* 検知オブジェクト設定タブ */}
            <TabPanel px={0} py={6}>
              <Card bg={cardBg} shadow="lg">
                <CardHeader pb={2}>
                  <HStack justify="space-between" align="center">
                    <HStack spacing={3}>
                      <Icon as={FaEye} color="purple.500" boxSize={5} />
                      <VStack align="start" spacing={0}>
                        <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                          検知オブジェクト設定
                        </Heading>
                        <Text fontSize="sm" color="gray.500">
                          オブジェクト検知の詳細パラメータ設定
                        </Text>
                      </VStack>
                    </HStack>
                    <Badge colorScheme="purple" variant="subtle" px={3} py={1} borderRadius="full">
                      {stats.enabledObjects}/{stats.totalObjects} 有効
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody pt={2}>
                  {Object.keys(settings.detection_objects).length === 0 ? (
                    <Alert status="warning" borderRadius="lg">
                      <AlertIcon />
                      <Box>
                        <AlertTitle>検知オブジェクト設定が見つかりません</AlertTitle>
                        <AlertDescription>
                          システムから検知オブジェクト設定を読み込めませんでした。
                        </AlertDescription>
                      </Box>
                    </Alert>
                  ) : (
                    <VStack spacing={4} align="stretch">
                      {Object.entries(settings.detection_objects).map(([key, value]) => (
                        <Box
                          key={key}
                          p={6}
                          borderRadius="lg"
                          border="1px solid"
                          borderColor={useColorModeValue('gray.200', 'gray.600')}
                          bg={value.enabled
                            ? useColorModeValue('purple.50', 'purple.900')
                            : useColorModeValue('gray.50', 'gray.700')
                          }
                        >
                          <VStack spacing={4} align="stretch">
                            {/* ヘッダー */}
                            <HStack justify="space-between" align="center">
                              <HStack spacing={3}>
                                <Avatar
                                  icon={<Icon as={FiEye} />}
                                  bg={value.enabled ? 'purple.500' : 'gray.500'}
                                  size="md"
                                />
                                <VStack align="start" spacing={0}>
                                  <Text fontWeight="bold" fontSize="lg">
                                    {value.name}
                                  </Text>
                                  <Badge
                                    colorScheme={value.enabled ? 'purple' : 'gray'}
                                    variant="subtle"
                                  >
                                    {value.enabled ? '検知有効' : '検知無効'}
                                  </Badge>
                                </VStack>
                              </HStack>
                              <Switch
                                isChecked={value.enabled}
                                onChange={() => handleObjectSettingChange(key, 'enabled', !value.enabled)}
                                colorScheme="purple"
                                size="lg"
                              />
                            </HStack>

                            {/* パラメータ設定 */}
                            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                              {/* 信頼度閾値 */}
                              <FormControl>
                                <FormLabel fontSize="sm" fontWeight="semibold">
                                  信頼度閾値
                                </FormLabel>
                                <Text fontSize="xs" color="gray.500" mb={2}>
                                  検知の最小信頼度 (0.0 - 1.0)
                                </Text>
                                <HStack spacing={3}>
                                  <NumberInput
                                    value={value.confidence_threshold}
                                    onChange={(_, val) => handleObjectSettingChange(key, 'confidence_threshold', val)}
                                    min={0}
                                    max={1}
                                    step={0.1}
                                    size="lg"
                                    flex={1}
                                  >
                                    <NumberInputField borderRadius="lg" />
                                    <NumberInputStepper>
                                      <NumberIncrementStepper />
                                      <NumberDecrementStepper />
                                    </NumberInputStepper>
                                  </NumberInput>
                                  <Badge colorScheme="blue" variant="outline" px={3} py={2}>
                                    {(value.confidence_threshold * 100).toFixed(0)}%
                                  </Badge>
                                </HStack>
                              </FormControl>

                              {/* アラート閾値 */}
                              <FormControl>
                                <FormLabel fontSize="sm" fontWeight="semibold">
                                  アラート閾値
                                </FormLabel>
                                <Text fontSize="xs" color="gray.500" mb={2}>
                                  アラート発生までの時間（秒）
                                </Text>
                                <HStack spacing={3}>
                                  <NumberInput
                                    value={value.alert_threshold}
                                    onChange={(_, val) => handleObjectSettingChange(key, 'alert_threshold', val)}
                                    min={0}
                                    max={300}
                                    size="lg"
                                    flex={1}
                                  >
                                    <NumberInputField borderRadius="lg" />
                                    <NumberInputStepper>
                                      <NumberIncrementStepper />
                                      <NumberDecrementStepper />
                                    </NumberInputStepper>
                                  </NumberInput>
                                  <Badge colorScheme="orange" variant="outline" px={3} py={2}>
                                    {value.alert_threshold}秒
                                  </Badge>
                                </HStack>
                              </FormControl>
                            </SimpleGrid>
                          </VStack>
                        </Box>
                      ))}
                    </VStack>
                  )}
                </CardBody>
              </Card>
            </TabPanel>
          </TabPanels>
        </Tabs>

        {/* フローティング保存ボタン */}
        <Box
          position="fixed"
          bottom={8}
          right={8}
          zIndex={1000}
        >
          <Tooltip label="設定を保存" placement="left">
            <Button
              colorScheme="green"
              size="lg"
              borderRadius="full"
              shadow="lg"
              leftIcon={<FaSave />}
              onClick={handleSave}
              _hover={{
                transform: 'scale(1.05)',
                shadow: 'xl'
              }}
              transition="all 0.2s"
            >
              保存
            </Button>
          </Tooltip>
        </Box>
      </VStack>
    </Container>
  );
}; 