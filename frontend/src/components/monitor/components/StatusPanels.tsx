import { Avatar, Badge, Box, HStack, Icon, Text, VStack, useColorModeValue } from '@chakra-ui/react'
import { FaWifi } from 'react-icons/fa'
import { FiSmartphone, FiUser } from 'react-icons/fi'
import { ConnectionStatus, DetectionStatus } from '../types'
import { formatSeconds } from '../utils/format'

interface StatusPanelsProps {
  status: DetectionStatus
  connectionStatus: ConnectionStatus
  lastUpdateAt: number | null
}

export const StatusPanels: React.FC<StatusPanelsProps> = ({ status, connectionStatus, lastUpdateAt }) => {
  const personBgDetected = useColorModeValue('green.50', 'green.900')
  const personBgNotDetected = useColorModeValue('red.50', 'red.900')
  const personBorderDetected = useColorModeValue('green.200', 'green.700')
  const personBorderNotDetected = useColorModeValue('red.200', 'red.700')
  const phoneBgDetected = useColorModeValue('orange.50', 'orange.900')
  const phoneBgNotDetected = useColorModeValue('green.50', 'green.900')
  const phoneBorderDetected = useColorModeValue('orange.200', 'orange.700')
  const phoneBorderNotDetected = useColorModeValue('green.200', 'green.700')

  return (
    <VStack spacing={6} align="stretch">
      {/* 人物検知 */}
      <Box p={4} borderRadius="lg" bg={status.personDetected ? personBgDetected : personBgNotDetected} border="1px solid" borderColor={status.personDetected ? personBorderDetected : personBorderNotDetected}>
        <HStack justify="space-between" align="center">
          <HStack spacing={3}>
            <Avatar icon={<Icon as={FiUser} />} bg={status.personDetected ? 'green.500' : 'red.500'} size="sm" />
            <VStack align="start" spacing={0}>
              <Text fontWeight="semibold" fontSize="sm">人物検知</Text>
              <Text fontSize="xs" color="gray.500">不在時間: {formatSeconds(status.absenceTime)}</Text>
            </VStack>
          </HStack>
          <Badge colorScheme={status.personDetected ? 'green' : 'red'} variant="solid" px={3} py={1} borderRadius="full">{status.personDetected ? '在席' : '不在'}</Badge>
        </HStack>
      </Box>

      {/* スマートフォン検知 */}
      <Box p={4} borderRadius="lg" bg={status.smartphoneDetected ? phoneBgDetected : phoneBgNotDetected} border="1px solid" borderColor={status.smartphoneDetected ? phoneBorderDetected : phoneBorderNotDetected}>
        <HStack justify="space-between" align="center">
          <HStack spacing={3}>
            <Avatar icon={<Icon as={FiSmartphone} />} bg={status.smartphoneDetected ? 'orange.500' : 'green.500'} size="sm" />
            <VStack align="start" spacing={0}>
              <Text fontWeight="semibold" fontSize="sm">スマートフォン</Text>
              <Text fontSize="xs" color="gray.500">使用時間: {formatSeconds(status.smartphoneUseTime)}</Text>
            </VStack>
          </HStack>
          <Badge colorScheme={status.smartphoneDetected ? 'orange' : 'green'} variant="solid" px={3} py={1} borderRadius="full">{status.smartphoneDetected ? '使用中' : '未使用'}</Badge>
        </HStack>
      </Box>

      {/* 接続状態 */}
      <Box p={4} borderRadius="lg" bg={useColorModeValue(`${connectionStatus.color}.50`, `${connectionStatus.color}.900`)} border="1px solid" borderColor={useColorModeValue(`${connectionStatus.color}.200`, `${connectionStatus.color}.700`)}>
        <HStack justify="space-between" align="center">
          <HStack spacing={3}>
            <Avatar icon={<Icon as={FaWifi} />} bg={`${connectionStatus.color}.500`} size="sm" />
            <VStack align="start" spacing={0}>
              <Text fontWeight="semibold" fontSize="sm">接続状態</Text>
              <Text fontSize="xs" color="gray.500">最終更新: {lastUpdateAt ? new Date(lastUpdateAt).toLocaleTimeString() : '未取得'}</Text>
            </VStack>
          </HStack>
          <Badge colorScheme={connectionStatus.color} variant="solid" px={3} py={1} borderRadius="full">{connectionStatus.label}</Badge>
        </HStack>
      </Box>
    </VStack>
  )
}


