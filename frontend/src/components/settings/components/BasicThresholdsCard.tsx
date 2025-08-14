import React from 'react';
import { Card, CardHeader, CardBody, HStack, Heading, Icon, VStack, Box, Avatar, Text, Badge, NumberInput, NumberInputField, NumberInputStepper, NumberIncrementStepper, NumberDecrementStepper, useColorModeValue } from '@chakra-ui/react';
import { FiTarget, FiUser, FiSmartphone } from 'react-icons/fi';

interface BasicThresholdsCardProps {
  absenceThreshold: number;
  smartphoneThreshold: number;
  onChangeAbsence: (val: number) => void;
  onChangeSmartphone: (val: number) => void;
}

export const BasicThresholdsCard: React.FC<BasicThresholdsCardProps> = ({ absenceThreshold, smartphoneThreshold, onChangeAbsence, onChangeSmartphone }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const absenceBg = useColorModeValue('red.50', 'red.900');
  const absenceBorder = useColorModeValue('red.200', 'red.700');
  const smartphoneBg = useColorModeValue('orange.50', 'orange.900');
  const smartphoneBorder = useColorModeValue('orange.200', 'orange.700');

  return (
    <Card bg={cardBg} shadow="lg">
      <CardHeader pb={2}>
        <HStack spacing={3}>
          <Icon as={FiTarget} color="red.500" boxSize={5} />
          <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>検知閾値設定</Heading>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        <VStack spacing={6} align="stretch">
          <Box p={4} borderRadius="lg" bg={absenceBg} border="1px solid" borderColor={absenceBorder}>
            <VStack spacing={4} align="stretch">
              <HStack justify="space-between" align="center">
                <HStack spacing={3}>
                  <Avatar icon={<Icon as={FiUser} />} bg="red.500" size="sm" />
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="semibold" fontSize="sm">不在検知閾値</Text>
                    <Text fontSize="xs" color="gray.500">不在と判定するまでの時間（秒）</Text>
                  </VStack>
                </HStack>
                <Badge colorScheme="red" variant="outline">{absenceThreshold}秒</Badge>
              </HStack>
              <NumberInput value={absenceThreshold} min={1} max={60} onChange={(_, v) => onChangeAbsence(v)} size="lg">
                <NumberInputField borderRadius="lg" />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </VStack>
          </Box>
          <Box p={4} borderRadius="lg" bg={smartphoneBg} border="1px solid" borderColor={smartphoneBorder}>
            <VStack spacing={4} align="stretch">
              <HStack justify="space-between" align="center">
                <HStack spacing={3}>
                  <Avatar icon={<Icon as={FiSmartphone} />} bg="orange.500" size="sm" />
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="semibold" fontSize="sm">スマートフォン検知閾値</Text>
                    <Text fontSize="xs" color="gray.500">使用中と判定するまでの時間（秒）</Text>
                  </VStack>
                </HStack>
                <Badge colorScheme="orange" variant="outline">{smartphoneThreshold}秒</Badge>
              </HStack>
              <NumberInput value={smartphoneThreshold} min={1} max={30} onChange={(_, v) => onChangeSmartphone(v)} size="lg">
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
  );
};


