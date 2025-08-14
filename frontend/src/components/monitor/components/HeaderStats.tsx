import { Avatar, Badge, Box, Flex, HStack, Heading, Icon, Stat, StatLabel, StatNumber, Text, useColorModeValue, VStack } from '@chakra-ui/react'
import { FaEye } from 'react-icons/fa'
import { FiCheckCircle, FiSmartphone, FiXCircle } from 'react-icons/fi'
import { ConnectionStatus, DetectionStatus } from '../types'
import { formatSeconds } from '../utils/format'

interface HeaderStatsProps {
  status: DetectionStatus
  connectionStatus: ConnectionStatus
  lastUpdateAt: number | null
}

export const HeaderStats: React.FC<HeaderStatsProps> = ({ status, connectionStatus, lastUpdateAt }) => {
  const gradientBg = useColorModeValue('linear(to-r, blue.50, green.50)', 'linear(to-r, blue.900, green.900)')
  const borderColor = useColorModeValue('gray.200', 'gray.600')

  return (
    <Box bgGradient={gradientBg} borderRadius="xl" border="1px solid" borderColor={borderColor} p={6} shadow="lg">
      <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
        <VStack align="start" spacing={3}>
          <HStack spacing={4}>
            <Avatar icon={<Icon as={FaEye} />} bg="blue.500" size="lg" />
            <VStack align="start" spacing={1}>
              <Heading size="xl" color="gray.700" _dark={{ color: 'gray.100' }}>リアルタイム監視システム</Heading>
              <Text fontSize="md" color="gray.600" _dark={{ color: 'gray.300' }}>AI による行動パターン検知と分析</Text>
            </VStack>
          </HStack>

          <HStack spacing={4} wrap="wrap">
            <Badge colorScheme={status.personDetected ? 'green' : 'red'} px={3} py={1} borderRadius="full" fontSize="sm">
              <HStack spacing={1}>
                <Icon as={status.personDetected ? FiCheckCircle : FiXCircle} boxSize={3} />
                <Text>{status.personDetected ? '在席中' : '不在'}</Text>
              </HStack>
            </Badge>
            <Badge colorScheme={status.smartphoneDetected ? 'orange' : 'green'} px={3} py={1} borderRadius="full" fontSize="sm">
              <HStack spacing={1}>
                <Icon as={FiSmartphone} boxSize={3} />
                <Text>{status.smartphoneDetected ? 'スマホ使用中' : 'スマホ未使用'}</Text>
              </HStack>
            </Badge>
            <Badge colorScheme={connectionStatus.color} px={3} py={1} borderRadius="full" fontSize="sm">
              <HStack spacing={1}>
                <Icon as={connectionStatus.icon} boxSize={3} />
                <Text>接続{connectionStatus.label}</Text>
              </HStack>
            </Badge>
          </HStack>
        </VStack>

        <VStack spacing={3} align="end">
          <HStack spacing={6}>
            <Stat textAlign="center">
              <StatLabel fontSize="xs">不在時間</StatLabel>
              <StatNumber fontSize="lg" color="red.500">{formatSeconds(status.absenceTime)}</StatNumber>
            </Stat>
            <Stat textAlign="center">
              <StatLabel fontSize="xs">スマホ使用</StatLabel>
              <StatNumber fontSize="lg" color="orange.500">{formatSeconds(status.smartphoneUseTime)}</StatNumber>
            </Stat>
          </HStack>
          <Text fontSize="xs" color="gray.500">最終更新: {lastUpdateAt ? new Date(lastUpdateAt).toLocaleTimeString() : '未取得'}</Text>
        </VStack>
      </Flex>
    </Box>
  )
}


