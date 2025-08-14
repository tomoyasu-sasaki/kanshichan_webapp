import React from 'react';
import { Box, Flex, VStack, HStack, Avatar, Icon, Heading, Text, Badge, SimpleGrid, Stat, StatLabel, StatNumber, StatHelpText, useColorModeValue } from '@chakra-ui/react';
import { FaCog } from 'react-icons/fa';
import { FiActivity, FiCheckCircle } from 'react-icons/fi';
import { SettingsStats } from '../types';

interface HeaderSectionProps {
  stats: SettingsStats;
}

export const HeaderSection: React.FC<HeaderSectionProps> = ({ stats }) => {
  const gradientBg = useColorModeValue('linear(to-r, purple.50, blue.50)', 'linear(to-r, purple.900, blue.900)');
  const headerBorderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Box bgGradient={gradientBg} borderRadius="xl" border="1px solid" borderColor={headerBorderColor} p={6} shadow="lg">
      <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
        <VStack align="start" spacing={3}>
          <HStack spacing={4}>
            <Avatar icon={<Icon as={FaCog} />} bg="purple.500" size="lg" />
            <VStack align="start" spacing={1}>
              <Heading size="xl" color="gray.700" _dark={{ color: 'gray.100' }}>システム設定</Heading>
              <Text fontSize="md" color="gray.600" _dark={{ color: 'gray.300' }}>検知パラメータと動作設定の管理</Text>
            </VStack>
          </HStack>
          <HStack spacing={4} wrap="wrap">
            <Badge colorScheme="green" px={3} py={1} borderRadius="full"><HStack spacing={1}><Icon as={FiCheckCircle} boxSize={3} /><Text fontSize="sm">設定読み込み完了</Text></HStack></Badge>
            <Badge colorScheme="blue" px={3} py={1} borderRadius="full"><HStack spacing={1}><Icon as={FiActivity} boxSize={3} /><Text fontSize="sm">リアルタイム適用</Text></HStack></Badge>
          </HStack>
        </VStack>
        <VStack spacing={3} align="end">
          <SimpleGrid columns={2} spacing={4}>
            <Stat textAlign="center">
              <StatLabel fontSize="xs">ランドマーク</StatLabel>
              <StatNumber fontSize="lg" color="green.500">{stats.enabledLandmarks}/{stats.totalLandmarks}</StatNumber>
              <StatHelpText fontSize="xs">有効/総数</StatHelpText>
            </Stat>
            <Stat textAlign="center">
              <StatLabel fontSize="xs">検知オブジェクト</StatLabel>
              <StatNumber fontSize="lg" color="blue.500">{stats.enabledObjects}/{stats.totalObjects}</StatNumber>
              <StatHelpText fontSize="xs">有効/総数</StatHelpText>
            </Stat>
          </SimpleGrid>
        </VStack>
      </Flex>
    </Box>
  );
};


