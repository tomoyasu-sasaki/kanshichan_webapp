import { Badge, Card, CardBody, CardHeader, Divider, HStack, Heading, Icon, Text, VStack } from '@chakra-ui/react'
import { FiMonitor } from 'react-icons/fi'

interface SystemInfoProps {
  fitMode: 'contain' | 'cover'
  isFullscreen: boolean
  isVideoLoading: boolean
}

export const SystemInfo: React.FC<SystemInfoProps> = ({ fitMode, isFullscreen, isVideoLoading }) => {
  return (
    <Card>
      <CardHeader pb={2}>
        <HStack spacing={3}>
          <Icon as={FiMonitor} color="gray.500" boxSize={5} />
          <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>システム情報</Heading>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        <VStack spacing={3} align="stretch">
          <HStack justify="space-between">
            <Text fontSize="sm" color="gray.600">表示モード</Text>
            <Badge variant="outline">{fitMode === 'contain' ? 'フィット' : 'フル'}</Badge>
          </HStack>
          <HStack justify="space-between">
            <Text fontSize="sm" color="gray.600">画面状態</Text>
            <Badge variant="outline">{isFullscreen ? '全画面' : '通常'}</Badge>
          </HStack>
          <HStack justify="space-between">
            <Text fontSize="sm" color="gray.600">ストリーム</Text>
            <Badge colorScheme={isVideoLoading ? 'yellow' : 'green'} variant="outline">{isVideoLoading ? '読み込み中' : 'アクティブ'}</Badge>
          </HStack>
          <Divider />
          <Text fontSize="xs" color="gray.500" textAlign="center">AI監視システム v2.0</Text>
        </VStack>
      </CardBody>
    </Card>
  )
}


