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
import axios from 'axios';
import { logger } from '../utils/logger';

interface Settings {
  absence_threshold: number;
  smartphone_threshold: number;
  message_extensions: { [key: string]: number };
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
  const [settings, setSettings] = useState<Settings>({
    absence_threshold: 5,
    smartphone_threshold: 3,
    message_extensions: {},
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

      const response = await axios.get('/api/settings');
      
      const fetchedSettings = {
        absence_threshold: response.data.absence_threshold,
        smartphone_threshold: response.data.smartphone_threshold,
        message_extensions: response.data.message_extensions,
        landmark_settings: response.data.landmark_settings,
        detection_objects: response.data.detection_objects
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
          endpoint: '/api/settings'
        }, 
        'SettingsPanel'
      );

      console.error('Settings fetch error:', err);
      toast({
        title: 'エラー',
        description: '設定の取得に失敗しました',
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
            message_extensions_count: Object.keys(settings.message_extensions).length,
            landmark_settings_count: Object.keys(settings.landmark_settings).length,
            detection_objects_count: Object.keys(settings.detection_objects).length
          }
        }, 
        'SettingsPanel'
      );

      const requestData = {
        absence_threshold: settings.absence_threshold,
        smartphone_threshold: settings.smartphone_threshold,
        message_extensions: settings.message_extensions,
        landmark_settings: settings.landmark_settings,
        detection_objects: settings.detection_objects
      };

      await axios.post('/api/settings', requestData);

      await logger.info('SettingsPanel: 設定保存成功', 
        { 
          component: 'SettingsPanel', 
          action: 'save_settings_success',
          savedSettings: requestData
        }, 
        'SettingsPanel'
      );

      toast({
        title: '成功',
        description: '設定を保存しました',
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
          endpoint: '/api/settings'
        }, 
        'SettingsPanel'
      );

      console.error('Settings save error:', err);
      toast({
        title: 'エラー',
        description: '設定の保存に失敗しました',
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

  const handleMessageExtensionChange = async (message: string, value: number) => {
    const oldValue = settings.message_extensions[message];
    
    setSettings(prev => ({
      ...prev,
      message_extensions: {
        ...prev.message_extensions,
        [message]: value
      }
    }));

    await logger.debug('SettingsPanel: メッセージ延長設定変更', 
      { 
        component: 'SettingsPanel', 
        action: 'message_extension_change',
        message,
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
    <Box p={6} shadow="md" borderWidth="1px" borderRadius="lg">
      <VStack spacing={4} align="stretch">
        <Heading size="md">監視設定</Heading>
        
        <FormControl>
          <FormLabel>不在検知閾値（秒）</FormLabel>
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
          <FormLabel>スマートフォン使用検知閾値（秒）</FormLabel>
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

        <Heading size="md">LINEメッセージ設定</Heading>
        <Text fontSize="sm" color="gray.600">
          各メッセージ受信時の不在検知閾値の延長時間（秒）
        </Text>

        {Object.entries(settings.message_extensions).map(([message, extension]) => (
          <FormControl key={message}>
            <FormLabel>{message}</FormLabel>
            <NumberInput
              value={extension}
              min={0}
              onChange={(_, value) => handleMessageExtensionChange(message, value)}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>
        ))}

        <Divider my={4} />

        <Heading size="md">ランドマーク表示設定</Heading>
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>種類</Th>
              <Th>表示</Th>
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

        <Heading size="md">検出対象物体設定</Heading>
        <Text fontSize="sm" color="gray.600">
          各物体の検出設定
        </Text>

        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>物体</Th>
              <Th>有効</Th>
              <Th>信頼度閾値</Th>
              <Th>警告時間(秒)</Th>
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
          設定を保存
        </Button>
      </VStack>
    </Box>
  );
}; 