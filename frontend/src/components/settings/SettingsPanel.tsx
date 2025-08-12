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
  Divider,
  Text,
  Switch,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td
} from '@chakra-ui/react';
import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { logger } from '../../utils/logger';

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

  const fetchSettings = useCallback(async () => {
    try {
      await logger.info('SettingsPanel: 設定取得開始', 
        { component: 'SettingsPanel', action: 'fetch_settings_start' }, 
        'SettingsPanel'
      );

      const response = await axios.get('/api/v1/settings');
      
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
      
      await fetchSettings();
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

      await axios.post('/api/v1/settings', requestData);

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

  return (
    <Box p={6} maxW="1200px" mx="auto" shadow="md" borderWidth="1px" borderRadius="lg">
      <VStack spacing={4} align="stretch">
        <Heading size="md">{t('settings.title')}</Heading>
        
        <FormControl>
          <FormLabel>{t('settings.thresholds.absence')}</FormLabel>
          <NumberInput
            value={settings.absence_threshold}
            min={1}
            onChange={(_, value) => handleThresholdChange('absence_threshold', value)}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <FormControl>
          <FormLabel>{t('settings.thresholds.smartphone')}</FormLabel>
          <NumberInput
            value={settings.smartphone_threshold}
            min={1}
            onChange={(_, value) => handleThresholdChange('smartphone_threshold', value)}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <Divider my={4} />

        <Heading size="md">{t('settings.landmarks.title')}</Heading>
        <Table variant="simple">
          <Thead>
            <Tr>
                <Th>{t('settings.landmarks.pose')}</Th>
                <Th>{t('settings.landmarks.enabled')}</Th>
            </Tr>
          </Thead>
          <Tbody>
            {Object.entries(settings.landmark_settings).map(([key, value]) => (
              <Tr key={key}>
                <Td>{value.name}</Td>
                <Td>
                  <Switch
                    isChecked={value.enabled}
                    onChange={() => handleLandmarkToggle(key)}
                  />
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>

        <Divider my={4} />

        <Heading size="md">{t('settings.detection.title')}</Heading>
        <Text fontSize="sm" color="gray.600">{t('settings.detection.threshold')}</Text>

        <Table variant="simple">
          <Thead>
            <Tr>
                <Th>{t('settings.detection.smartphone')}</Th>
                <Th>{t('settings.detection.enabled')}</Th>
                <Th>{t('settings.detection.threshold')}</Th>
                <Th>{t('settings.thresholds.smartphone')}</Th>
            </Tr>
          </Thead>
          <Tbody>
            {Object.entries(settings.detection_objects).map(([key, value]) => (
              <Tr key={key}>
                <Td>{value.name}</Td>
                <Td>
                  <Switch
                    isChecked={value.enabled}
                    onChange={() => handleObjectSettingChange(key, 'enabled', !value.enabled)}
                  />
                </Td>
                <Td>
                  <NumberInput
                    value={value.confidence_threshold}
                    onChange={(_, val) => handleObjectSettingChange(key, 'confidence_threshold', val)}
                    min={0}
                    max={1}
                    step={0.1}
                    w="100px"
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </Td>
                <Td>
                  <NumberInput
                    value={value.alert_threshold}
                    onChange={(_, val) => handleObjectSettingChange(key, 'alert_threshold', val)}
                    min={0}
                    w="100px"
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>

        <Button colorScheme="blue" onClick={handleSave} mt={4}>
          {t('settings.save')}
        </Button>
      </VStack>
    </Box>
  );
}; 