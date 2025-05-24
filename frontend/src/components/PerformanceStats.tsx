import React, { useState, useEffect } from 'react';
import {
  Box,
  Text,
  VStack,
  HStack,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  useColorModeValue
} from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';

interface PerformanceData {
  fps: number;
  avg_inference_ms: number;
  memory_mb: number;
  skip_rate: number;
  optimization_active: boolean;
}

const PerformanceStats: React.FC = () => {
  const { t } = useTranslation();
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  useEffect(() => {
    const fetchPerformanceData = async () => {
      try {
        const response = await fetch('/api/performance');
        if (response.ok) {
          const data = await response.json();
          setPerformanceData(data);
        }
      } catch (error) {
        console.error('Failed to fetch performance data:', error);
      }
    };

    // 初回取得
    fetchPerformanceData();

    // 5秒間隔で更新
    const interval = setInterval(fetchPerformanceData, 5000);

    return () => clearInterval(interval);
  }, []);

  if (!performanceData) {
    return (
      <Box p={4} bg={bgColor} borderRadius="md" border="1px" borderColor={borderColor}>
        <Text>{t('common.loading')}</Text>
      </Box>
    );
  }

  const getFPSColor = (fps: number) => {
    if (fps >= 15) return 'green';
    if (fps >= 10) return 'yellow';
    return 'red';
  };

  const getMemoryColor = (memory: number) => {
    if (memory < 200) return 'green';
    if (memory < 400) return 'yellow';
    return 'red';
  };

  return (
    <Box p={4} bg={bgColor} borderRadius="md" border="1px" borderColor={borderColor}>
      <VStack spacing={4} align="stretch">
        <HStack justify="space-between">
          <Text fontSize="lg" fontWeight="bold">
            {t('monitor.performance.title', 'Performance')}
          </Text>
          <Badge colorScheme={performanceData.optimization_active ? 'green' : 'gray'}>
            {performanceData.optimization_active ? 'Optimized' : 'Standard'}
          </Badge>
        </HStack>

        <SimpleGrid columns={2} spacing={4}>
          <Stat>
            <StatLabel>{t('monitor.performance.fps')}</StatLabel>
            <StatNumber color={`${getFPSColor(performanceData.fps)}.500`}>
              {performanceData.fps.toFixed(1)}
            </StatNumber>
            <StatHelpText>frames/sec</StatHelpText>
          </Stat>

          <Stat>
            <StatLabel>{t('monitor.performance.inference')}</StatLabel>
            <StatNumber>
              {performanceData.avg_inference_ms.toFixed(1)}ms
            </StatNumber>
            <StatHelpText>avg inference</StatHelpText>
          </Stat>

          <Stat>
            <StatLabel>{t('monitor.performance.memory')}</StatLabel>
            <StatNumber color={`${getMemoryColor(performanceData.memory_mb)}.500`}>
              {performanceData.memory_mb.toFixed(1)}MB
            </StatNumber>
            <StatHelpText>memory usage</StatHelpText>
          </Stat>

          <Stat>
            <StatLabel>{t('monitor.performance.skip_rate')}</StatLabel>
            <StatNumber>
              {performanceData.skip_rate}x
            </StatNumber>
            <StatHelpText>frame skip</StatHelpText>
          </Stat>
        </SimpleGrid>
      </VStack>
    </Box>
  );
};

export default PerformanceStats; 