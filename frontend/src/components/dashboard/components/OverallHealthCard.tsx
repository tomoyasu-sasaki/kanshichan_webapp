import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  HStack,
  VStack,
  Heading,
  Text,
  Avatar,
  Icon,
  CircularProgress,
  CircularProgressLabel,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Box,
  useColorModeValue
} from '@chakra-ui/react';
import { FiMonitor, FiActivity } from 'react-icons/fi';

interface OverallHealthCardProps {
  overall: number; // 0..1
  lastRefresh: Date;
}

export const OverallHealthCard: React.FC<OverallHealthCardProps> = ({ overall, lastRefresh }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const infoBg = useColorModeValue('green.50', 'green.900');
  const infoBorder = useColorModeValue('green.200', 'green.700');

  const healthColor = overall > 0.8 ? 'green' : overall > 0.6 ? 'yellow' : 'red';
  const healthPercentage = Math.round(overall * 100);

  return (
    <Card bg={cardBg} shadow="lg">
      <CardHeader pb={2}>
        <HStack justify="space-between" align="center">
          <HStack spacing={3}>
            <Avatar icon={<Icon as={FiMonitor} />} bg="blue.500" size="md" />
            <VStack align="start" spacing={0}>
              <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                システム健康度
              </Heading>
              <Text fontSize="sm" color="gray.500">最終更新: {lastRefresh.toLocaleTimeString()}</Text>
            </VStack>
          </HStack>
          <CircularProgress value={healthPercentage} color={`${healthColor}.500`} size="60px" thickness="8px">
            <CircularProgressLabel fontSize="sm" fontWeight="bold">{healthPercentage}%</CircularProgressLabel>
          </CircularProgress>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        <VStack spacing={5}>
          <SimpleGrid columns={2} spacing={4} width="100%">
            <Stat>
              <StatLabel fontSize="xs">アクティブ</StatLabel>
              <StatNumber fontSize="lg" color="green.500">1</StatNumber>
              <StatHelpText fontSize="xs"><StatArrow type="increase" />システム</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel fontSize="xs">稼働時間</StatLabel>
              <StatNumber fontSize="lg" color="blue.500">24h</StatNumber>
              <StatHelpText fontSize="xs"><StatArrow type="increase" />連続稼働</StatHelpText>
            </Stat>
          </SimpleGrid>
          <Box width="100%" p={4} bg={infoBg} borderRadius="lg" border="1px solid" borderColor={infoBorder}>
            <HStack justify="center" spacing={3}>
              <Icon as={FiActivity} color="green.500" boxSize={5} />
              <VStack spacing={0} align="center">
                <Text fontSize="sm" color="green.700" _dark={{ color: 'green.300' }} fontWeight="medium">監視システム稼働中</Text>
                <Text fontSize="xs" color="green.600" _dark={{ color: 'green.400' }}>リアルタイム監視アクティブ</Text>
              </VStack>
            </HStack>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
};


