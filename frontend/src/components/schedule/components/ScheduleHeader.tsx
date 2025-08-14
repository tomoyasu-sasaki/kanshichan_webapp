import { Avatar, Box, Button, Flex, HStack, Heading, Icon, Input, InputGroup, InputLeftElement, Stat, StatLabel, StatNumber, Text, useColorModeValue, Progress, Badge } from '@chakra-ui/react'
import { SearchIcon } from '@chakra-ui/icons'
import { FaCalendarAlt } from 'react-icons/fa'
import { ScheduleStats } from '../types'

interface ScheduleHeaderProps {
  currentDate: string
  query: string
  onQueryChange: (value: string) => void
  onReload: () => void
  isLoading: boolean
  stats: ScheduleStats
}

export const ScheduleHeader: React.FC<ScheduleHeaderProps> = ({ currentDate, query, onQueryChange, onReload, isLoading, stats }) => {
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const cardBg = useColorModeValue('white', 'gray.800')
  const gradientBg = useColorModeValue('linear(to-r, blue.50, purple.50)', 'linear(to-r, blue.900, purple.900)')
  const accentColor = useColorModeValue('blue.500', 'blue.300')

  return (
    <Box
      bgGradient={gradientBg}
      borderRadius="xl"
      border="1px solid"
      borderColor={borderColor}
      p={6}
      shadow="lg"
    >
      <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
        <HStack spacing={3}>
          <Avatar icon={<Icon as={FaCalendarAlt} />} bg="blue.500" size="md" />
          <Box>
            <Heading size="xl" color="gray.700" _dark={{ color: 'gray.100' }}>
              {currentDate ? `${currentDate}` : '今日'}のスケジュール
            </Heading>
            <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.300' }}>
              効率的な一日を過ごしましょう
            </Text>
          </Box>
        </HStack>

        <HStack spacing={4}>
          <InputGroup maxW="300px">
            <InputLeftElement pointerEvents="none">
              <SearchIcon color="gray.400" />
            </InputLeftElement>
            <Input
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              placeholder="検索 (時間/内容)"
              bg={cardBg}
              borderRadius="lg"
              isDisabled={isLoading}
            />
          </InputGroup>
          <Button variant="outline" onClick={onReload} isLoading={isLoading} bg={cardBg} borderRadius="lg">
            再読み込み
          </Button>
        </HStack>
      </Flex>

      <HStack spacing={6} mt={6} wrap="wrap">
        <Stat>
          <StatLabel fontSize="xs" color="gray.600">総予定数</StatLabel>
          <StatNumber fontSize="2xl" color={accentColor}>{stats.total}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel fontSize="xs" color="gray.600">完了</StatLabel>
          <StatNumber fontSize="2xl" color="green.500">{stats.completed}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel fontSize="xs" color="gray.600">残り</StatLabel>
          <StatNumber fontSize="2xl" color="orange.500">{stats.remaining}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel fontSize="xs" color="gray.600">進捗</StatLabel>
          <StatNumber fontSize="2xl" color="purple.500">{Math.round(stats.progress)}%</StatNumber>
          <Progress value={stats.progress} colorScheme="purple" size="sm" mt={1} borderRadius="full" />
        </Stat>
        <Badge colorScheme="blue" variant="subtle" px={3} py={1} borderRadius="full" fontSize="sm">
          {stats.total - stats.completed === stats.remaining ? `${stats.remaining} 件` : `${stats.total} 件`}
        </Badge>
      </HStack>
    </Box>
  )
}


