import { Box, Heading, Divider, Text, useColorModeValue, FormControl, FormLabel, Input, Button, HStack, VStack, useToast, Table, Thead, Tbody, Tr, Th, Td, IconButton } from '@chakra-ui/react'
import { useTranslation } from 'react-i18next'
import { DeleteIcon } from '@chakra-ui/icons'
import { useState, useEffect, useCallback } from 'react'
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

  return (
    <Box 
      p={5} 
      shadow="md" 
      borderWidth="1px" 
      borderRadius="lg" 
      bg={bgColor}
      borderColor={borderColor}
    >
      <Heading as="h2" size="lg" mb={4}>
        {currentDate ? `${currentDate} ${t('schedule.title')}` : t('schedule.title')}
      </Heading>
      
      <Divider my={4} />
      
      {/* スケジュール設定フォームエリア */}
      <Box mb={6}>
        <Heading as="h3" size="md" mb={3}>
          {t('schedule.add_new')}
        </Heading>
        
        <VStack spacing={4} align="stretch">
          <HStack spacing={4}>
            <FormControl id="time" isRequired>
              <FormLabel>{t('schedule.time')}</FormLabel>
              <Input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                isDisabled={isLoading}
              />
            </FormControl>
            
            <FormControl id="content" isRequired>
              <FormLabel>{t('schedule.message')}</FormLabel>
              <Input
                type="text"
                placeholder="作業内容を入力"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                isDisabled={isLoading}
              />
            </FormControl>
          </HStack>
          
          <Button
            colorScheme="blue"
            onClick={addSchedule}
            isLoading={isLoading}
            alignSelf="flex-end"
          >
            {t('schedule.add')}
          </Button>
        </VStack>
      </Box>
      
      <Divider my={4} />
      
      {/* スケジュール一覧表示エリア */}
      <Box>
        <Heading as="h3" size="md" mb={3}>
          {t('schedule.registered')}
        </Heading>
        
        {error && (
          <Text color="red.500" mb={4}>
            {error}
          </Text>
        )}
        
        {schedules.length === 0 ? (
          <Text color="gray.500">
            {t('schedule.no_schedules')}
          </Text>
        ) : (
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>{t('schedule.time')}</Th>
                <Th>{t('schedule.message')}</Th>
                <Th width="50px">{t('common.settings')}</Th>
              </Tr>
            </Thead>
            <Tbody>
              {schedules.map((schedule) => (
                <Tr key={schedule.id}>
                  <Td>{schedule.time}</Td>
                  <Td>{schedule.content}</Td>
                  <Td>
                    <IconButton
                      aria-label={t('schedule.delete')}
                      icon={<DeleteIcon />}
                      size="sm"
                      colorScheme="red"
                      variant="ghost"
                      onClick={() => deleteSchedule(schedule.id)}
                      isDisabled={isLoading}
                    />
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </Box>
    </Box>
  )
} 