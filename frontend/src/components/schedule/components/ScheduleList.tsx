import { Badge, Box, HStack, IconButton, Text, Tooltip, VStack, useColorModeValue } from '@chakra-ui/react'
import { DeleteIcon } from '@chakra-ui/icons'
import { Schedule } from '../types'
import { timeToMinutes } from '../utils/time'

interface ScheduleListProps {
  schedules: Schedule[]
  nextSchedule: Schedule | null
  isLoading: boolean
  onRequestDelete: (id: string) => void
}

export const ScheduleList: React.FC<ScheduleListProps> = ({ schedules, nextSchedule, isLoading, onRequestDelete }) => {
  const listBorderNext = useColorModeValue('purple.300', 'purple.600')
  const listBorderCompleted = useColorModeValue('green.200', 'green.700')
  const listBorderDefault = useColorModeValue('gray.200', 'gray.600')
  const listBgNext = useColorModeValue('purple.50', 'purple.900')
  const listBgCompleted = useColorModeValue('green.50', 'green.900')
  const listBgDefault = useColorModeValue('white', 'gray.700')

  const now = new Date()
  const currentMinutes = now.getHours() * 60 + now.getMinutes()

  return (
    <VStack spacing={2} align="stretch">
      {schedules.map((schedule, index) => {
        const isNext = nextSchedule?.id === schedule.id
        const scheduleMinutes = timeToMinutes(schedule.time)
        const isCompleted = scheduleMinutes < currentMinutes

        return (
          <Box
            key={schedule.id}
            p={4}
            borderRadius="lg"
            border="2px solid"
            borderColor={isNext ? listBorderNext : isCompleted ? listBorderCompleted : listBorderDefault}
            bg={isNext ? listBgNext : isCompleted ? listBgCompleted : listBgDefault}
            position="relative"
            transition="all 0.2s"
            _hover={{ transform: 'translateY(-2px)', shadow: 'md' }}
          >
            <HStack justify="space-between" align="center">
              <HStack spacing={4} flex={1}>
                <VStack align="center" spacing={1}>
                  <Text
                    fontSize="xl"
                    fontWeight="bold"
                    color={isNext ? 'purple.600' : isCompleted ? 'green.600' : 'blue.600'}
                    _dark={{ color: isNext ? 'purple.300' : isCompleted ? 'green.300' : 'blue.300' }}
                  >
                    {schedule.time}
                  </Text>
                  <Badge size="xs" colorScheme={isNext ? 'purple' : isCompleted ? 'green' : 'blue'} variant="subtle">
                    {isNext ? 'NEXT' : isCompleted ? 'DONE' : 'PENDING'}
                  </Badge>
                </VStack>

                <VStack align="start" spacing={1} flex={1}>
                  <Text fontSize="md" fontWeight="medium" color="gray.700" _dark={{ color: 'gray.200' }} textDecoration={isCompleted ? 'line-through' : 'none'} opacity={isCompleted ? 0.7 : 1}>
                    {schedule.content}
                  </Text>
                  <Text fontSize="xs" color="gray.500">{isCompleted ? '完了済み' : isNext ? '次の予定' : `${index + 1}番目の予定`}</Text>
                </VStack>
              </HStack>

              <Tooltip label="予定を削除" placement="top">
                <IconButton aria-label="予定を削除" icon={<DeleteIcon />} size="sm" colorScheme="red" variant="ghost" onClick={() => onRequestDelete(schedule.id)} isDisabled={isLoading} borderRadius="lg" _hover={{ bg: 'red.100', _dark: { bg: 'red.800' } }} />
              </Tooltip>
            </HStack>

            {isNext && <Box position="absolute" top={0} left={0} right={0} h="3px" bg="purple.400" borderTopRadius="lg" />}
          </Box>
        )
      })}
    </VStack>
  )
}


