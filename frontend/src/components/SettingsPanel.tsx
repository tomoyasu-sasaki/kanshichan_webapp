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
  Td,
  HStack
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import axios from 'axios';

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

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get('/api/settings');
      setSettings({
        absence_threshold: response.data.absence_threshold,
        smartphone_threshold: response.data.smartphone_threshold,
        message_extensions: response.data.message_extensions,
        landmark_settings: response.data.landmark_settings,
        detection_objects: response.data.detection_objects
      });
    } catch (error) {
      toast({
        title: 'エラー',
        description: '設定の取得に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleSave = async () => {
    try {
      await axios.post('/api/settings', {
        absence_threshold: settings.absence_threshold,
        smartphone_threshold: settings.smartphone_threshold,
        message_extensions: settings.message_extensions,
        landmark_settings: settings.landmark_settings,
        detection_objects: settings.detection_objects
      });
      toast({
        title: '成功',
        description: '設定を保存しました',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'エラー',
        description: '設定の保存に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleThresholdChange = (field: string, value: number) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleMessageExtensionChange = (message: string, value: number) => {
    setSettings(prev => ({
      ...prev,
      message_extensions: {
        ...prev.message_extensions,
        [message]: value
      }
    }));
  };

  const handleLandmarkToggle = (key: string) => {
    const newSettings = {
      ...settings,
      landmark_settings: {
        ...settings.landmark_settings,
        [key]: {
          ...settings.landmark_settings[key],
          enabled: !settings.landmark_settings[key].enabled
        }
      }
    };
    setSettings(newSettings);
  };

  const handleObjectSettingChange = (
    key: string,
    field: 'enabled' | 'confidence_threshold' | 'alert_threshold',
    value: boolean | number
  ) => {
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