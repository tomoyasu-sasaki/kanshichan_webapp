import { Badge, Box, Card, CardBody, CardHeader, HStack, Heading, Icon, SkeletonText, Text, useColorModeValue, VStack } from '@chakra-ui/react'
import { WarningIcon } from '@chakra-ui/icons'
import { FaBell } from 'react-icons/fa'
import { minutesUntil } from '../utils/time'
import { Schedule } from '../types'

interface NextScheduleCardProps {
  nextSchedule: Schedule | null
  isLoading: boolean
}

export const NextScheduleCard: React.FC<NextScheduleCardProps> = ({ nextSchedule, isLoading }) => {
  const cardBg = useColorModeValue('white', 'gray.800')
  const nextPanelBg = useColorModeValue('purple.50', 'purple.900')
  const nextPanelBorder = useColorModeValue('purple.200', 'purple.700')

  return (
    <Card bg={cardBg} shadow="lg" border="2px solid" borderColor={nextSchedule ? 'purple.200' : 'gray.200'} _dark={{ borderColor: nextSchedule ? 'purple.600' : 'gray.600' }}>
      <CardHeader pb={2}>
        <HStack spacing={3}>
          <Icon as={FaBell} color="purple.500" boxSize={5} />
          <Heading size="md">次の予定</Heading>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        {isLoading ? (
          <SkeletonText noOfLines={3} />
        ) : nextSchedule ? (
          <VStack align="stretch" spacing={4}>
            <HStack justify="space-between" align="center">
              <Badge colorScheme="purple" fontSize="sm" px={3} py={1} borderRadius="full">NEXT UP</Badge>
              <Text fontSize="xs" color="gray.500">{(() => {
                const diff = minutesUntil(nextSchedule.time)
                return diff > 0 ? `${diff}分後` : '進行中'
              })()}</Text>
            </HStack>
            <Box p={4} bg={nextPanelBg} borderRadius="lg" border="1px solid" borderColor={nextPanelBorder}>
              <VStack align="stretch" spacing={3}>
                <HStack justify="center">
                  <Text fontSize="3xl" fontWeight="bold" color="purple.600" _dark={{ color: 'purple.300' }}>{nextSchedule.time}</Text>
                </HStack>
                <Text fontSize="lg" fontWeight="medium" textAlign="center">{nextSchedule.content}</Text>
              </VStack>
            </Box>
          </VStack>
        ) : (
          <VStack spacing={3} py={4}>
            <Icon as={WarningIcon} boxSize={8} color="gray.400" />
            <Text color="gray.500" textAlign="center">本日の残り予定はありません</Text>
            <Text fontSize="sm" color="gray.400" textAlign="center">お疲れ様でした！</Text>
          </VStack>
        )}
      </CardBody>
    </Card>
  )
}


