import { Box, Center, Container, HStack, SimpleGrid, VStack, useColorModeValue, useDisclosure, useToast, Text, Heading, Badge, Skeleton } from '@chakra-ui/react'
import { useTranslation } from 'react-i18next'
import { FaList } from 'react-icons/fa'
import { useState, useEffect, useCallback, useMemo } from 'react'
import { websocketManager, ScheduleAlert } from '../../utils/websocket.ts'
import { Schedule } from './types'
import { timeToMinutes } from './utils/time'
import { ScheduleHeader } from './components/ScheduleHeader'
import { NewScheduleForm } from './components/NewScheduleForm'
import { NextScheduleCard } from './components/NextScheduleCard'
import { ScheduleList } from './components/ScheduleList'
import { DeleteConfirmDialog } from './components/DeleteConfirmDialog'

export const ScheduleView: React.FC = () => {
  const { t } = useTranslation()
  const [currentDate, setCurrentDate] = useState<string>('')
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState<string>('')
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)
  const { isOpen: isConfirmOpen, onOpen: onConfirmOpen, onClose: onConfirmClose } = useDisclosure()

  // フォーム入力値
  const [time, setTime] = useState<string>('')
  const [content, setContent] = useState<string>('')

  const toast = useToast()
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

  // 時刻ユーティリティは共通化

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

  const cardBg = useColorModeValue('white', 'gray.800')

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
        <ScheduleHeader
          currentDate={currentDate}
          query={query}
          onQueryChange={setQuery}
          onReload={fetchSchedules}
          isLoading={isLoading}
          stats={stats}
        />

        {/* 上部カード - 新規追加フォーム + 次の予定を横並び */}
        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} mb={8}>
          <NewScheduleForm
            time={time}
            content={content}
            isLoading={isLoading}
            onChangeTime={setTime}
            onChangeContent={setContent}
            onSubmit={addSchedule}
            onClear={() => { setTime(''); setContent('') }}
          />
          <NextScheduleCard nextSchedule={nextSchedule} isLoading={isLoading} />
        </SimpleGrid>

        {/* 下部 - スケジュール一覧（全幅） */}
        <Box bg={cardBg} borderRadius="lg" border="1px solid" borderColor={borderColor} p={4} shadow="lg">
          <HStack align="center" justify="space-between" mb={2}>
            <HStack spacing={3}>
              <Box as={FaList} color="blue.500" />
              <Heading size="md">今日の予定一覧</Heading>
            </HStack>
            <HStack spacing={2}>
              <Badge colorScheme="blue" variant="subtle" px={3} py={1} borderRadius="full" fontSize="sm">{filteredSchedules.length} 件</Badge>
              {query && <Badge colorScheme="green" variant="outline" px={2} py={1} borderRadius="full" fontSize="xs">検索中</Badge>}
            </HStack>
          </HStack>

          {error ? (
            <Box p={4} bg="red.50" borderRadius="lg" border="1px solid" borderColor="red.200" mb={4} _dark={{ bg: 'red.900', borderColor: 'red.700' }}>
              <Text color="red.600" _dark={{ color: 'red.300' }}>{error}</Text>
            </Box>
          ) : null}

          {isLoading ? (
            <VStack spacing={3}>
              {[...Array(3)].map((_, i) => (
                <Box key={i} p={4} borderRadius="lg" w="full" border="1px solid" borderColor={borderColor}>
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
                <Box as={FaList} boxSize={12} color="gray.300" />
                <VStack spacing={2}>
                  <Text color="gray.500" fontSize="lg" fontWeight="medium">{query ? '検索結果が見つかりません' : '予定がありません'}</Text>
                  <Text color="gray.400" fontSize="sm" textAlign="center">{query ? '別のキーワードで検索してみてください' : '新しい予定を追加して一日を計画しましょう'}</Text>
                </VStack>
              </VStack>
            </Center>
          ) : (
            <ScheduleList schedules={filteredSchedules} nextSchedule={nextSchedule} isLoading={isLoading} onRequestDelete={requestDelete} />
          )}
        </Box>
      </VStack>

      <DeleteConfirmDialog
        isOpen={isConfirmOpen}
        onClose={onConfirmClose}
        onConfirm={async () => {
          if (pendingDeleteId) {
            await deleteSchedule(pendingDeleteId)
            setPendingDeleteId(null)
          }
          onConfirmClose()
        }}
        isLoading={isLoading}
        title={t('schedule.delete')}
      />
    </Container>
  )
} 
