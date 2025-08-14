import React from 'react';
import { Box, Flex, VStack, HStack, Avatar, Icon, Heading, Text, Badge, Button, useColorModeValue } from '@chakra-ui/react';
import { FiBarChart, FiZap, FiUsers, FiMonitor, FiTarget, FiVolumeX } from 'react-icons/fi';

interface OverviewHeaderProps {
  lastRefresh: Date;
  onNavigate: (view: string) => void;
}

export const OverviewHeader: React.FC<OverviewHeaderProps> = ({ lastRefresh, onNavigate }) => {
  const bgGradient = useColorModeValue('linear(to-r, blue.50, purple.50)', 'linear(to-r, blue.900, purple.900)');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Box bgGradient={bgGradient} borderRadius="xl" border="1px solid" borderColor={borderColor} p={8} shadow="lg">
      <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
        <VStack align="start" spacing={3}>
          <HStack spacing={4}>
            <Avatar icon={<Icon as={FiBarChart} />} bg="blue.500" size="lg" />
            <VStack align="start" spacing={1}>
              <Heading size="xl" color="gray.700" _dark={{ color: 'gray.100' }}>システム概要ダッシュボード</Heading>
              <Text fontSize="md" color="gray.600" _dark={{ color: 'gray.300' }}>リアルタイム監視とシステム状態の統合管理</Text>
            </VStack>
          </HStack>
          <HStack spacing={4} wrap="wrap">
            <Badge colorScheme="green" px={3} py={1} borderRadius="full"><HStack spacing={1}><Icon as={FiZap} boxSize={3} /><Text fontSize="sm">システム稼働中</Text></HStack></Badge>
            <Badge colorScheme="blue" px={3} py={1} borderRadius="full"><HStack spacing={1}><Icon as={FiUsers} boxSize={3} /><Text fontSize="sm">監視アクティブ</Text></HStack></Badge>
            <Badge colorScheme="purple" px={3} py={1} borderRadius="full"><HStack spacing={1}><Icon as={FiMonitor} boxSize={3} /><Text fontSize="sm">通知有効</Text></HStack></Badge>
          </HStack>
        </VStack>
        <VStack spacing={3}>
          <HStack spacing={3}>
            <Button leftIcon={<Icon as={FiMonitor} />} onClick={() => onNavigate('monitor')} colorScheme="blue" variant="solid" borderRadius="lg">監視</Button>
            <Button leftIcon={<Icon as={FiVolumeX} />} onClick={() => onNavigate('voice')} colorScheme="purple" variant="solid" borderRadius="lg">音声</Button>
            <Button leftIcon={<Icon as={FiTarget} />} onClick={() => onNavigate('analytics')} colorScheme="green" variant="solid" borderRadius="lg">分析</Button>
          </HStack>
          <Text fontSize="xs" color="gray.500" textAlign="center">最終更新: {lastRefresh.toLocaleTimeString()}</Text>
        </VStack>
      </Flex>
    </Box>
  );
};


