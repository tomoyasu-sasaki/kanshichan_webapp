import { Box, Heading, Divider, Text, useColorModeValue, FormControl, FormLabel, Input, Button, HStack, VStack, useToast, Table, Thead, Tbody, Tr, Th, Td, IconButton } from '@chakra-ui/react'
import { DeleteIcon } from '@chakra-ui/icons'
import { useState, useEffect, useCallback } from 'react'
import { websocketManager, ScheduleAlert } from '../utils/websocket.ts'

interface Schedule {
  id: string
  time: string
  content: string
}

export const ScheduleView: React.FC = () => {
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
        // トースト通知を表示
        toast({
          title: 'スケジュール通知',
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
      const response = await fetch('/api/schedules')
      if (!response.ok) {
        throw new Error(`APIエラー: ${response.status}`)
      }
      const data = await response.json()
      setSchedules(data)
    } catch (err) {
      console.error('スケジュール取得エラー:', err)
      setError('スケジュールの取得に失敗しました')
      toast({
        title: 'エラー',
        description: 'スケジュールの取得に失敗しました',
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
        title: '入力エラー',
        description: '時刻を入力してください',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      })
      return
    }
    
    if (!content) {
      toast({
        title: '入力エラー',
        description: '内容を入力してください',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch('/api/schedules', {
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
        title: '追加完了',
        description: 'スケジュールが追加されました',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    } catch (err) {
      console.error('スケジュール追加エラー:', err)
      toast({
        title: 'エラー',
        description: 'スケジュールの追加に失敗しました',
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
      const response = await fetch(`/api/schedules/${id}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error(`APIエラー: ${response.status}`)
      }

      // 成功したらスケジュール一覧を再取得
      fetchSchedules()
      
      toast({
        title: '削除完了',
        description: 'スケジュールが削除されました',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    } catch (err) {
      console.error('スケジュール削除エラー:', err)
      toast({
        title: 'エラー',
        description: 'スケジュールの削除に失敗しました',
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
        {currentDate ? `${currentDate}のスケジュール` : 'スケジュール'}
      </Heading>
      
      <Divider my={4} />
      
      {/* スケジュール設定フォームエリア */}
      <Box mb={6}>
        <Heading as="h3" size="md" mb={3}>
          新しいスケジュールを追加
        </Heading>
        
        <VStack spacing={4} align="stretch">
          <HStack spacing={4}>
            <FormControl id="time" isRequired>
              <FormLabel>時刻</FormLabel>
              <Input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                isDisabled={isLoading}
              />
            </FormControl>
            
            <FormControl id="content" isRequired>
              <FormLabel>内容</FormLabel>
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
            追加
          </Button>
        </VStack>
      </Box>
      
      <Divider my={4} />
      
      {/* スケジュール一覧表示エリア */}
      <Box>
        <Heading as="h3" size="md" mb={3}>
          登録済みスケジュール
        </Heading>
        
        {error && (
          <Text color="red.500" mb={4}>
            {error}
          </Text>
        )}
        
        {schedules.length === 0 ? (
          <Text color="gray.500">
            登録されているスケジュールはありません
          </Text>
        ) : (
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>時刻</Th>
                <Th>内容</Th>
                <Th width="50px">操作</Th>
              </Tr>
            </Thead>
            <Tbody>
              {schedules.map((schedule) => (
                <Tr key={schedule.id}>
                  <Td>{schedule.time}</Td>
                  <Td>{schedule.content}</Td>
                  <Td>
                    <IconButton
                      aria-label="削除"
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