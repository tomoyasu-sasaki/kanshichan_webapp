import React from 'react';
import { Card, CardHeader, CardBody, HStack, Heading, Icon, VStack, Box, Avatar, Text, Badge, Switch, SimpleGrid, NumberInput, NumberInputField, NumberInputStepper, NumberIncrementStepper, NumberDecrementStepper, useColorModeValue } from '@chakra-ui/react';
import { FaEye } from 'react-icons/fa';

interface DetectionItem {
  key: string;
  name: string;
  enabled: boolean;
  confidence_threshold: number;
  alert_threshold: number;
}

interface DetectionObjectsListProps {
  items: DetectionItem[];
  enabledCount: number;
  totalCount: number;
  onToggle: (key: string, value: boolean) => void;
  onChangeConfidence: (key: string, value: number) => void;
  onChangeAlert: (key: string, value: number) => void;
}

export const DetectionObjectsList: React.FC<DetectionObjectsListProps> = ({ items, enabledCount, totalCount, onToggle, onChangeConfidence, onChangeAlert }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const objectItemBorder = useColorModeValue('gray.200', 'gray.600');
  const objectBgEnabled = useColorModeValue('purple.50', 'purple.900');
  const objectBgDisabled = useColorModeValue('gray.50', 'gray.700');

  return (
    <Card bg={cardBg} shadow="lg">
      <CardHeader pb={2}>
        <HStack justify="space-between" align="center">
          <HStack spacing={3}>
            <Icon as={FaEye} color="purple.500" boxSize={5} />
            <VStack align="start" spacing={0}>
              <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>検知オブジェクト設定</Heading>
              <Text fontSize="sm" color="gray.500">オブジェクト検知の詳細パラメータ設定</Text>
            </VStack>
          </HStack>
          <Badge colorScheme="purple" variant="subtle" px={3} py={1} borderRadius="full">{enabledCount}/{totalCount} 有効</Badge>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        <VStack spacing={4} align="stretch">
          {items.map(item => (
            <Box key={item.key} p={6} borderRadius="lg" border="1px solid" borderColor={objectItemBorder} bg={item.enabled ? objectBgEnabled : objectBgDisabled}>
              <VStack spacing={4} align="stretch">
                <HStack justify="space-between" align="center">
                  <HStack spacing={3}>
                    <Avatar icon={<Icon as={FaEye} />} bg={item.enabled ? 'purple.500' : 'gray.500'} size="md" />
                    <VStack align="start" spacing={0}>
                      <Text fontWeight="bold" fontSize="lg">{item.name}</Text>
                      <Badge colorScheme={item.enabled ? 'purple' : 'gray'} variant="subtle">{item.enabled ? '検知有効' : '検知無効'}</Badge>
                    </VStack>
                  </HStack>
                  <Switch isChecked={item.enabled} onChange={(e) => onToggle(item.key, e.target.checked)} colorScheme="purple" size="lg" />
                </HStack>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                  <Box>
                    <Text fontSize="sm" fontWeight="semibold">信頼度閾値</Text>
                    <Text fontSize="xs" color="gray.500" mb={2}>検知の最小信頼度 (0.0 - 1.0)</Text>
                    <HStack spacing={3}>
                      <NumberInput value={item.confidence_threshold} onChange={(_, v) => onChangeConfidence(item.key, v)} min={0} max={1} step={0.1} size="lg" flex={1}>
                        <NumberInputField borderRadius="lg" />
                        <NumberInputStepper>
                          <NumberIncrementStepper />
                          <NumberDecrementStepper />
                        </NumberInputStepper>
                      </NumberInput>
                      <Badge colorScheme="blue" variant="outline" px={3} py={2}>{(item.confidence_threshold * 100).toFixed(0)}%</Badge>
                    </HStack>
                  </Box>
                  <Box>
                    <Text fontSize="sm" fontWeight="semibold">アラート閾値</Text>
                    <Text fontSize="xs" color="gray.500" mb={2}>アラート発生までの時間（秒）</Text>
                    <HStack spacing={3}>
                      <NumberInput value={item.alert_threshold} onChange={(_, v) => onChangeAlert(item.key, v)} min={0} max={300} size="lg" flex={1}>
                        <NumberInputField borderRadius="lg" />
                        <NumberInputStepper>
                          <NumberIncrementStepper />
                          <NumberDecrementStepper />
                        </NumberInputStepper>
                      </NumberInput>
                      <Badge colorScheme="orange" variant="outline" px={3} py={2}>{item.alert_threshold}秒</Badge>
                    </HStack>
                  </Box>
                </SimpleGrid>
              </VStack>
            </Box>
          ))}
        </VStack>
      </CardBody>
    </Card>
  );
};


