import { Box, VStack, Heading, Button, useToast, Text, Container, Card, CardHeader, CardBody, SimpleGrid, HStack, Icon, Tabs, TabList, TabPanels, Tab, TabPanel, Tooltip, Alert, AlertIcon, AlertTitle, AlertDescription, useColorModeValue } from '@chakra-ui/react';
import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { logger } from '../../utils/logger';
import { FaSave, FaSlidersH, FaUser, FaEye } from 'react-icons/fa';
import { HeaderSection, BasicThresholdsCard, LandmarkSettingsGrid, DetectionObjectsList } from './index';
import type { Settings as SettingsType, SettingsStats } from './types';

export const SettingsPanel = () => {
  const { t } = useTranslation();
  const [settings, setSettings] = useState<SettingsType>({
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
    const oldValue = settings[field as keyof Pick<SettingsType, 'absence_threshold' | 'smartphone_threshold'>];

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

  // 統計情報（ヘッダー用）
  const stats: SettingsStats = {
    totalLandmarks: Object.keys(settings.landmark_settings).length,
    enabledLandmarks: Object.values(settings.landmark_settings).filter(l => l.enabled).length,
    totalObjects: Object.keys(settings.detection_objects).length,
    enabledObjects: Object.values(settings.detection_objects).filter(o => o.enabled).length
  };

  const cardBg = useColorModeValue('white', 'gray.800');

  return (
    <Container maxW="1400px" px={{ base: 4, md: 6 }}>
      <VStack spacing={8} align="stretch">
        {/* ヘッダーセクション */}
        <HeaderSection stats={stats} />

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
                <BasicThresholdsCard
                  absenceThreshold={settings.absence_threshold}
                  smartphoneThreshold={settings.smartphone_threshold}
                  onChangeAbsence={(v) => handleThresholdChange('absence_threshold', v)}
                  onChangeSmartphone={(v) => handleThresholdChange('smartphone_threshold', v)}
                />

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
              <LandmarkSettingsGrid
                items={Object.entries(settings.landmark_settings).map(([key, v]) => ({ key, name: v.name, enabled: v.enabled }))}
                enabledCount={stats.enabledLandmarks}
                totalCount={stats.totalLandmarks}
                onToggle={handleLandmarkToggle}
              />
            </TabPanel>

            {/* 検知オブジェクト設定タブ */}
            <TabPanel px={0} py={6}>
              <DetectionObjectsList
                items={Object.entries(settings.detection_objects).map(([key, v]) => ({ key, name: v.name, enabled: v.enabled, confidence_threshold: v.confidence_threshold, alert_threshold: v.alert_threshold }))}
                enabledCount={stats.enabledObjects}
                totalCount={stats.totalObjects}
                onToggle={(key, val) => handleObjectSettingChange(key, 'enabled', val)}
                onChangeConfidence={(key, val) => handleObjectSettingChange(key, 'confidence_threshold', val)}
                onChangeAlert={(key, val) => handleObjectSettingChange(key, 'alert_threshold', val)}
              />
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