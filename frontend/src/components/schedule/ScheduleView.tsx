import {
  Box,
  Heading,
  Divider,
  Text,
  useColorModeValue,
  FormControl,
  FormLabel,
  Input,
  Button,
  HStack,
  VStack,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  TableContainer,
  SimpleGrid,
  Flex,
  Spacer,
  Badge,
  Skeleton,
  SkeletonText,
  useDisclosure,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  InputGroup,
  InputLeftElement,
  Center,
  Container,
  Card,
  CardHeader,
  CardBody,
  Icon,
  Grid,
  GridItem,
  useBreakpointValue,
  Avatar,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress,
  Tooltip
} from '@chakra-ui/react'
import { useTranslation } from 'react-i18next'
import { DeleteIcon, AddIcon, SearchIcon, CalendarIcon, WarningIcon, TimeIcon, EditIcon } from '@chakra-ui/icons'
import { FaClock, FaCalendarAlt, FaBell, FaPlus, FaList, FaChartLine } from 'react-icons/fa'
import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { websocketManager, ScheduleAlert } from '../../utils/websocket.ts'

interface Schedule {
  id: string
  time: string
  content: string
}

export const ScheduleView: React.FC = () => {
  const { t } = useTranslation()
  const [currentDate, setCurrentDate] = useState<string>('')
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState<string>('')
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)
  const { isOpen: isConfirmOpen, onOpen: onConfirmOpen, onClose: onConfirmClose } = useDisclosure()
  const cancelRef = useRef<HTMLButtonElement>(null)

  // フォーム入力値
  const [time, setTime] = useState<string>('')
  const [content, setContent] = useState<string>('')

  const toast = useToast()
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  // 本日の日付を「YYYY/MM/DD」形式で取得
  useEffect(() => {
    const date = new Date()
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    setCurrentDate(`${year}/${month}/${day}`)
  }, [])

  // WebSocketの初期化とスケジュールアラートの受信設定
  useEffect(() => {
    // WebSocketマネージャーを初期化
    websocketManager.initialize()

    // スケジュールアラートの受信
    const unsubscribe = websocketManager.onScheduleAlert((data?: ScheduleAlert) => {
      if (data && data.content) {
        toast({
          title: t('schedule.notification_title'),
          description: `${data.time}: ${data.content}`,
          status: 'info',
          duration: 10000,
          isClosable: true,
          position: 'top',
        })
      }
    })

    return () => {
      unsubscribe()
    }
  }, [toast])

  // 時刻の比較/整列ユーティリティ
  const timeToMinutes = (timeStr: string): number => {
    const [hh, mm] = timeStr.split(':').map(Number)
    if (Number.isNaN(hh) || Number.isNaN(mm)) return Number.MAX_SAFE_INTEGER
    return hh * 60 + mm
  }

  const sortedSchedules = useMemo(() => {
    return [...schedules].sort((a, b) => timeToMinutes(a.time) - timeToMinutes(b.time))
  }, [schedules])

  const filteredSchedules = useMemo(() => {
    if (!query) return sortedSchedules
    const q = query.toLowerCase()
    return sortedSchedules.filter((s) => s.content.toLowerCase().includes(q) || s.time.includes(q))
  }, [query, sortedSchedules])

  const nextSchedule = useMemo(() => {
    const now = new Date()
    const minutes = now.getHours() * 60 + now.getMinutes()
    return sortedSchedules.find((s) => timeToMinutes(s.time) >= minutes) || null
  }, [sortedSchedules])

  // スケジュール一覧を取得する関数
  const fetchSchedules = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/v1/schedules')
      if (!response.ok) {
        throw new Error(`APIエラー: ${response.status}`)
      }
      const data = await response.json()
      const schedules = (data && (data.data?.schedules ?? data.schedules)) || []
      setSchedules(schedules)
    } catch (err) {
      console.error('スケジュール取得エラー:', err)
      setError('スケジュールの取得に失敗しました')
      toast({
        title: t('common.error'),
        description: t('schedule.loading'),
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast])

  // コンポーネントのマウント時にスケジュール一覧を取得
  useEffect(() => {
    fetchSchedules()
  }, [fetchSchedules])

  // 新しいスケジュールを追加する関数
  const addSchedule = async () => {
    // 入力値のバリデーション
    if (!time) {
      toast({
        title: t('common.error'),
        description: t('schedule.time'),
        status: 'warning',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    if (!content) {
      toast({
        title: t('common.error'),
        description: t('schedule.message'),
        status: 'warning',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/schedules', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ time, content }),
      })

      if (!response.ok) {
        throw new Error(`APIエラー: ${response.status}`)
      }

      // 成功したら入力フォームをクリアしてスケジュール一覧を再取得
      setTime('')
      setContent('')
      fetchSchedules()

      toast({
        title: t('common.success'),
        description: t('schedule.add'),
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    } catch (err) {
      console.error('スケジュール追加エラー:', err)
      toast({
        title: t('common.error'),
        description: t('schedule.add'),
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
    }
  }

  // スケジュールを削除する関数
  const deleteSchedule = async (id: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/v1/schedules/${id}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error(`APIエラー: ${response.status}`)
      }

      // 成功したらスケジュール一覧を再取得
      fetchSchedules()

      toast({
        title: t('common.success'),
        description: t('schedule.delete'),
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    } catch (err) {
      console.error('スケジュール削除エラー:', err)
      toast({
        title: t('common.error'),
        description: t('schedule.delete'),
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
    }
  }

  const requestDelete = (id: string) => {
    setPendingDeleteId(id)
    onConfirmOpen()
  }

  // レスポンシブレイアウト設定
  const isMobile = useBreakpointValue({ base: true, lg: false });
  const gridTemplateColumns = useBreakpointValue({
    base: '1fr',
    lg: '1fr 2fr'
  });

  const gradientBg = useColorModeValue(
    'linear(to-r, blue.50, purple.50)',
    'linear(to-r, blue.900, purple.900)'
  );

  const cardBg = useColorModeValue('white', 'gray.800');
  const accentColor = useColorModeValue('blue.500', 'blue.300');

  // 統計情報の計算
  const stats = useMemo(() => {
    const now = new Date();
    const currentMinutes = now.getHours() * 60 + now.getMinutes();

    const completed = schedules.filter(s => timeToMinutes(s.time) < currentMinutes).length;
    const remaining = schedules.filter(s => timeToMinutes(s.time) >= currentMinutes).length;
    const progress = schedules.length > 0 ? (completed / schedules.length) * 100 : 0;

    return { total: schedules.length, completed, remaining, progress };
  }, [schedules]);

  return (
    <Container maxW="1400px" px={{ base: 4, md: 6 }}>
      <VStack spacing={8} align="stretch">
        {/* ヘッダーセクション */}
        <Box
          bgGradient={gradientBg}
          borderRadius="xl"
          border="1px solid"
          borderColor={borderColor}
          p={6}
          shadow="lg"
        >
          <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
            <VStack align="start" spacing={2}>
              <HStack spacing={3}>
                <Avatar
                  icon={<Icon as={FaCalendarAlt} />}
                  bg="blue.500"
                  size="md"
                />
                <VStack align="start" spacing={0}>
                  <Heading size="xl" color="gray.700" _dark={{ color: 'gray.100' }}>
                    {currentDate ? `${currentDate}` : '今日'}のスケジュール
                  </Heading>
                  <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.300' }}>
                    効率的な一日を過ごしましょう
                  </Text>
                </VStack>
              </HStack>
            </VStack>

            <HStack spacing={4} wrap="wrap">
              <InputGroup maxW="300px">
                <InputLeftElement pointerEvents="none">
                  <SearchIcon color="gray.400" />
                </InputLeftElement>
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="検索 (時間/内容)"
                  bg={cardBg}
                  borderRadius="lg"
                  isDisabled={isLoading}
                />
              </InputGroup>
              <Button
                variant="outline"
                onClick={fetchSchedules}
                isLoading={isLoading}
                bg={cardBg}
                borderRadius="lg"
              >
                再読み込み
              </Button>
            </HStack>
          </Flex>

          {/* 統計情報 */}
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4} mt={6}>
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
          </SimpleGrid>
        </Box>

        {/* 上部カード - 新規追加フォーム + 次の予定を横並び */}
        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} mb={8}>
          {/* 新規スケジュール追加 */}
          <Card bg={cardBg} shadow="lg">
            <CardHeader pb={2}>
              <HStack spacing={3}>
                <Icon as={FaPlus} color="green.500" boxSize={5} />
                <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                  新しい予定を追加
                </Heading>
              </HStack>
            </CardHeader>
            <CardBody pt={2}>
              {isLoading ? (
                <>
                  <Skeleton h="40px" mb={4} />
                  <Skeleton h="40px" mb={4} />
                  <Skeleton h="40px" />
                </>
              ) : (
                <VStack spacing={4} align="stretch">
                  <VStack spacing={4} align="stretch">
                    <FormControl id="time" isRequired>
                      <FormLabel fontWeight="semibold" color="gray.600">
                        <HStack spacing={2}>
                          <Icon as={FaClock} boxSize={4} />
                          <Text>時間</Text>
                        </HStack>
                      </FormLabel>
                      <Input
                        type="time"
                        value={time}
                        onChange={(e) => setTime(e.target.value)}
                        isDisabled={isLoading}
                        size="lg"
                        borderRadius="lg"
                        _focus={{
                          borderColor: 'blue.400',
                          boxShadow: '0 0 0 1px var(--chakra-colors-blue-400)'
                        }}
                      />
                    </FormControl>
                    <FormControl id="content" isRequired>
                      <FormLabel fontWeight="semibold" color="gray.600">
                        <HStack spacing={2}>
                          <Icon as={EditIcon} boxSize={4} />
                          <Text>内容</Text>
                        </HStack>
                      </FormLabel>
                      <Input
                        type="text"
                        placeholder="予定の内容を入力してください"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        isDisabled={isLoading}
                        size="lg"
                        borderRadius="lg"
                        _focus={{
                          borderColor: 'blue.400',
                          boxShadow: '0 0 0 1px var(--chakra-colors-blue-400)'
                        }}
                      />
                    </FormControl>
                  </VStack>

                  <HStack spacing={3} justify="flex-end">
                    <Button
                      variant="ghost"
                      onClick={() => { setTime(''); setContent('') }}
                      isDisabled={isLoading}
                      borderRadius="lg"
                    >
                      クリア
                    </Button>
                    <Button
                      leftIcon={<AddIcon />}
                      colorScheme="blue"
                      onClick={addSchedule}
                      isLoading={isLoading}
                      size="lg"
                      borderRadius="lg"
                      px={8}
                    >
                      予定を追加
                    </Button>
                  </HStack>
                </VStack>
              )}
            </CardBody>
          </Card>

          {/* 次の予定ハイライト */}
          <Card
            bg={cardBg}
            shadow="lg"
            border="2px solid"
            borderColor={nextSchedule ? "purple.200" : "gray.200"}
            _dark={{
              borderColor: nextSchedule ? "purple.600" : "gray.600"
            }}
          >
            <CardHeader pb={2}>
              <HStack spacing={3}>
                <Icon as={FaBell} color="purple.500" boxSize={5} />
                <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                  次の予定
                </Heading>
              </HStack>
            </CardHeader>
            <CardBody pt={2}>
              {isLoading ? (
                <SkeletonText noOfLines={3} />
              ) : nextSchedule ? (
                <VStack align="stretch" spacing={4}>
                  <HStack justify="space-between" align="center">
                    <Badge
                      colorScheme="purple"
                      fontSize="sm"
                      px={3}
                      py={1}
                      borderRadius="full"
                    >
                      NEXT UP
                    </Badge>
                    <Text fontSize="xs" color="gray.500">
                      {(() => {
                        const now = new Date();
                        const [hours, minutes] = nextSchedule.time.split(':').map(Number);
                        const scheduleTime = new Date();
                        scheduleTime.setHours(hours, minutes, 0, 0);
                        const diff = Math.max(0, Math.floor((scheduleTime.getTime() - now.getTime()) / (1000 * 60)));
                        return diff > 0 ? `${diff}分後` : '進行中';
                      })()}
                    </Text>
                  </HStack>

                  <Box
                    p={4}
                    bg={useColorModeValue('purple.50', 'purple.900')}
                    borderRadius="lg"
                    border="1px solid"
                    borderColor={useColorModeValue('purple.200', 'purple.700')}
                  >
                    <VStack align="stretch" spacing={3}>
                      <HStack justify="center">
                        <Text fontSize="3xl" fontWeight="bold" color="purple.600" _dark={{ color: 'purple.300' }}>
                          {nextSchedule.time}
                        </Text>
                      </HStack>
                      <Text
                        fontSize="lg"
                        fontWeight="medium"
                        color="gray.700"
                        _dark={{ color: 'gray.200' }}
                        textAlign="center"
                      >
                        {nextSchedule.content}
                      </Text>
                    </VStack>
                  </Box>
                </VStack>
              ) : (
                <VStack spacing={3} py={4}>
                  <Icon as={WarningIcon} boxSize={8} color="gray.400" />
                  <Text color="gray.500" textAlign="center">
                    本日の残り予定はありません
                  </Text>
                  <Text fontSize="sm" color="gray.400" textAlign="center">
                    お疲れ様でした！
                  </Text>
                </VStack>
              )}
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* 下部 - スケジュール一覧（全幅） */}
        <Card bg={cardBg} shadow="lg">
          <CardHeader pb={2}>
            <Flex align="center" justify="space-between">
              <HStack spacing={3}>
                <Icon as={FaList} color="blue.500" boxSize={5} />
                <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>
                  今日の予定一覧
                </Heading>
              </HStack>
              <HStack spacing={2}>
                <Badge
                  colorScheme="blue"
                  variant="subtle"
                  px={3}
                  py={1}
                  borderRadius="full"
                  fontSize="sm"
                >
                  {filteredSchedules.length} 件
                </Badge>
                {query && (
                  <Badge
                    colorScheme="green"
                    variant="outline"
                    px={2}
                    py={1}
                    borderRadius="full"
                    fontSize="xs"
                  >
                    検索中
                  </Badge>
                )}
              </HStack>
            </Flex>
          </CardHeader>

          <CardBody pt={2}>
            {error && (
              <Box
                p={4}
                bg="red.50"
                borderRadius="lg"
                border="1px solid"
                borderColor="red.200"
                mb={4}
                _dark={{
                  bg: 'red.900',
                  borderColor: 'red.700'
                }}
              >
                <Text color="red.600" _dark={{ color: 'red.300' }}>
                  {error}
                </Text>
              </Box>
            )}

            {isLoading ? (
              <VStack spacing={3}>
                {[...Array(3)].map((_, i) => (
                  <Box key={i} p={4} borderRadius="lg" bg={useColorModeValue('gray.50', 'gray.700')} w="full">
                    <HStack justify="space-between">
                      <Skeleton h="20px" w="80px" />
                      <Skeleton h="20px" w="200px" />
                      <Skeleton h="20px" w="30px" />
                    </HStack>
                  </Box>
                ))}
              </VStack>
            ) : filteredSchedules.length === 0 ? (
              <Center py={12}>
                <VStack spacing={4}>
                  <Icon as={FaCalendarAlt} boxSize={12} color="gray.300" />
                  <VStack spacing={2}>
                    <Text color="gray.500" fontSize="lg" fontWeight="medium">
                      {query ? '検索結果が見つかりません' : '予定がありません'}
                    </Text>
                    <Text color="gray.400" fontSize="sm" textAlign="center">
                      {query ? '別のキーワードで検索してみてください' : '新しい予定を追加して一日を計画しましょう'}
                    </Text>
                  </VStack>
                </VStack>
              </Center>
            ) : (
              <VStack spacing={2} align="stretch">
                {filteredSchedules.map((schedule, index) => {
                  const isNext = nextSchedule?.id === schedule.id;
                  const now = new Date();
                  const currentMinutes = now.getHours() * 60 + now.getMinutes();
                  const scheduleMinutes = timeToMinutes(schedule.time);
                  const isCompleted = scheduleMinutes < currentMinutes;
                  const isUpcoming = scheduleMinutes >= currentMinutes;

                  return (
                    <Box
                      key={schedule.id}
                      p={4}
                      borderRadius="lg"
                      border="2px solid"
                      borderColor={
                        isNext
                          ? useColorModeValue('purple.300', 'purple.600')
                          : isCompleted
                            ? useColorModeValue('green.200', 'green.700')
                            : useColorModeValue('gray.200', 'gray.600')
                      }
                      bg={
                        isNext
                          ? useColorModeValue('purple.50', 'purple.900')
                          : isCompleted
                            ? useColorModeValue('green.50', 'green.900')
                            : useColorModeValue('white', 'gray.700')
                      }
                      position="relative"
                      transition="all 0.2s"
                      _hover={{
                        transform: 'translateY(-2px)',
                        shadow: 'md'
                      }}
                    >
                      <HStack justify="space-between" align="center">
                        <HStack spacing={4} flex={1}>
                          <VStack align="center" spacing={1}>
                            <Text
                              fontSize="xl"
                              fontWeight="bold"
                              color={
                                isNext
                                  ? 'purple.600'
                                  : isCompleted
                                    ? 'green.600'
                                    : 'blue.600'
                              }
                              _dark={{
                                color: isNext
                                  ? 'purple.300'
                                  : isCompleted
                                    ? 'green.300'
                                    : 'blue.300'
                              }}
                            >
                              {schedule.time}
                            </Text>
                            <Badge
                              size="xs"
                              colorScheme={
                                isNext
                                  ? 'purple'
                                  : isCompleted
                                    ? 'green'
                                    : 'blue'
                              }
                              variant="subtle"
                            >
                              {isNext ? 'NEXT' : isCompleted ? 'DONE' : 'PENDING'}
                            </Badge>
                          </VStack>

                          <VStack align="start" spacing={1} flex={1}>
                            <Text
                              fontSize="md"
                              fontWeight="medium"
                              color="gray.700"
                              _dark={{ color: 'gray.200' }}
                              textDecoration={isCompleted ? 'line-through' : 'none'}
                              opacity={isCompleted ? 0.7 : 1}
                            >
                              {schedule.content}
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              {isCompleted
                                ? '完了済み'
                                : isNext
                                  ? '次の予定'
                                  : `${index + 1}番目の予定`}
                            </Text>
                          </VStack>
                        </HStack>

                        <Tooltip label="予定を削除" placement="top">
                          <IconButton
                            aria-label="予定を削除"
                            icon={<DeleteIcon />}
                            size="sm"
                            colorScheme="red"
                            variant="ghost"
                            onClick={() => requestDelete(schedule.id)}
                            isDisabled={isLoading}
                            borderRadius="lg"
                            _hover={{
                              bg: 'red.100',
                              _dark: { bg: 'red.800' }
                            }}
                          />
                        </Tooltip>
                      </HStack>

                      {/* 進行状況インジケーター */}
                      {isNext && (
                        <Box
                          position="absolute"
                          top={0}
                          left={0}
                          right={0}
                          h="3px"
                          bg="purple.400"
                          borderTopRadius="lg"
                        />
                      )}
                    </Box>
                  );
                })}
              </VStack>
            )}
          </CardBody>
        </Card>
      </VStack>

      {/* 削除確認ダイアログ */}
      <AlertDialog
        isOpen={isConfirmOpen}
        leastDestructiveRef={cancelRef}
        onClose={onConfirmClose}
        isCentered
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              {t('schedule.delete')}
            </AlertDialogHeader>
            <AlertDialogBody>
              このスケジュールを削除しますか？この操作は元に戻せません。
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onConfirmClose}>
                キャンセル
              </Button>
              <Button
                colorScheme="red"
                ml={3}
                onClick={async () => {
                  if (pendingDeleteId) {
                    await deleteSchedule(pendingDeleteId)
                    setPendingDeleteId(null)
                  }
                  onConfirmClose()
                }}
                isLoading={isLoading}
              >
                削除
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Container>
  )
} 
