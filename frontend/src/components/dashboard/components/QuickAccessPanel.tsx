import React from 'react';
import { Card, CardHeader, CardBody, HStack, VStack, Heading, Text, Icon, Box, SimpleGrid, Button, Divider, useColorModeValue } from '@chakra-ui/react';
import { FiTarget, FiHome, FiVolumeX, FiCalendar, FiSettings, FiActivity, FiTrendingUp } from 'react-icons/fi';
import { FaChartLine } from 'react-icons/fa';

interface QuickAccessPanelProps {
  onNavigate: (view: string) => void;
}

export const QuickAccessPanel: React.FC<QuickAccessPanelProps> = ({ onNavigate }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const hover = (light: string, dark: string) => ({ bg: useColorModeValue(light, dark) });

  return (
    <Card bg={cardBg} shadow="lg">
      <CardHeader pb={2}>
        <HStack spacing={3}>
          <Icon as={FiTarget} color="green.500" boxSize={6} />
          <VStack align="start" spacing={0}>
            <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>クイックアクセス</Heading>
            <Text fontSize="sm" color="gray.500">よく使用する機能への直接アクセス</Text>
          </VStack>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        <VStack spacing={6} align="stretch">
          <Box>
            <Text fontSize="sm" fontWeight="semibold" color="gray.600" mb={3}>主要機能</Text>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
              <Button variant="outline" leftIcon={<Icon as={FiHome} />} onClick={() => onNavigate('monitor')} justifyContent="flex-start" h="50px" borderRadius="lg" _hover={hover('blue.50', 'blue.900')}>
                <VStack align="start" spacing={0} flex={1}><Text fontSize="sm" fontWeight="medium">監視</Text><Text fontSize="xs" color="gray.500">リアルタイム監視</Text></VStack>
              </Button>
              <Button variant="outline" leftIcon={<Icon as={FiVolumeX} />} onClick={() => onNavigate('voice')} justifyContent="flex-start" h="50px" borderRadius="lg" _hover={hover('purple.50', 'purple.900')}>
                <VStack align="start" spacing={0} flex={1}><Text fontSize="sm" fontWeight="medium">音声設定</Text><Text fontSize="xs" color="gray.500">TTS・音声合成</Text></VStack>
              </Button>
              <Button variant="outline" leftIcon={<Icon as={FiCalendar} />} onClick={() => onNavigate('schedule')} justifyContent="flex-start" h="50px" borderRadius="lg" _hover={hover('green.50', 'green.900')}>
                <VStack align="start" spacing={0} flex={1}><Text fontSize="sm" fontWeight="medium">スケジュール</Text><Text fontSize="xs" color="gray.500">予定管理</Text></VStack>
              </Button>
              <Button variant="outline" leftIcon={<Icon as={FiSettings} />} onClick={() => onNavigate('settings')} justifyContent="flex-start" h="50px" borderRadius="lg" _hover={hover('orange.50', 'orange.900')}>
                <VStack align="start" spacing={0} flex={1}><Text fontSize="sm" fontWeight="medium">設定</Text><Text fontSize="xs" color="gray.500">システム設定</Text></VStack>
              </Button>
            </SimpleGrid>
          </Box>
          <Divider />
          <Box>
            <Text fontSize="sm" fontWeight="semibold" color="gray.600" mb={3}>分析・解析</Text>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
              <Button variant="outline" leftIcon={<Icon as={FiActivity} />} onClick={() => onNavigate('behavior')} justifyContent="flex-start" h="50px" borderRadius="lg" _hover={hover('teal.50', 'teal.900')}>
                <VStack align="start" spacing={0} flex={1}><Text fontSize="sm" fontWeight="medium">行動分析</Text><Text fontSize="xs" color="gray.500">パターン解析</Text></VStack>
              </Button>
              <Button variant="outline" leftIcon={<Icon as={FiTarget} />} onClick={() => onNavigate('analytics')} justifyContent="flex-start" h="50px" borderRadius="lg" _hover={hover('cyan.50', 'cyan.900')}>
                <VStack align="start" spacing={0} flex={1}><Text fontSize="sm" fontWeight="medium">詳細分析</Text><Text fontSize="xs" color="gray.500">高度な解析</Text></VStack>
              </Button>
              <Button variant="outline" leftIcon={<Icon as={FiTrendingUp} />} onClick={() => onNavigate('predictions')} justifyContent="flex-start" h="50px" borderRadius="lg" _hover={hover('pink.50', 'pink.900')}>
                <VStack align="start" spacing={0} flex={1}><Text fontSize="sm" fontWeight="medium">予測分析</Text><Text fontSize="xs" color="gray.500">将来予測</Text></VStack>
              </Button>
              <Button variant="outline" leftIcon={<Icon as={FaChartLine} />} onClick={() => onNavigate('learning')} justifyContent="flex-start" h="50px" borderRadius="lg" _hover={hover('indigo.50', 'indigo.900')}>
                <VStack align="start" spacing={0} flex={1}><Text fontSize="sm" fontWeight="medium">学習進捗</Text><Text fontSize="xs" color="gray.500">AI学習状況</Text></VStack>
              </Button>
            </SimpleGrid>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
};


