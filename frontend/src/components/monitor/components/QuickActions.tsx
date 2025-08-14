import { Button, Card, CardBody, CardHeader, HStack, Heading, Icon, VStack } from '@chakra-ui/react'
import { FaCompress, FaExpand } from 'react-icons/fa'
import { FiCamera, FiMaximize, FiMinimize, FiRefreshCw, FiZap } from 'react-icons/fi'

interface QuickActionsProps {
  fitMode: 'contain' | 'cover'
  isFullscreen: boolean
  onCapture: () => void
  onReconnect: () => void
  onToggleFit: () => void
  onToggleFullscreen: () => void
}

export const QuickActions: React.FC<QuickActionsProps> = ({ fitMode, isFullscreen, onCapture, onReconnect, onToggleFit, onToggleFullscreen }) => {
  return (
    <Card>
      <CardHeader pb={2}>
        <HStack spacing={3}>
          <Icon as={FiZap} color="blue.500" boxSize={5} />
          <Heading size="md" color="gray.700" _dark={{ color: 'gray.100' }}>クイックアクション</Heading>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        <VStack spacing={3} align="stretch">
          <Button leftIcon={<FiCamera />} onClick={onCapture} colorScheme="blue" variant="outline" justifyContent="flex-start" borderRadius="lg">スクリーンショット撮影</Button>
          <Button leftIcon={<FiRefreshCw />} onClick={onReconnect} colorScheme="green" variant="outline" justifyContent="flex-start" borderRadius="lg">ストリーム再接続</Button>
          <Button leftIcon={fitMode === 'contain' ? <FiMaximize /> : <FiMinimize />} onClick={onToggleFit} colorScheme="purple" variant="outline" justifyContent="flex-start" borderRadius="lg">{fitMode === 'contain' ? 'フル表示' : 'フィット表示'}</Button>
          <Button leftIcon={isFullscreen ? <FaCompress /> : <FaExpand />} onClick={onToggleFullscreen} colorScheme="orange" variant="outline" justifyContent="flex-start" borderRadius="lg">{isFullscreen ? '全画面終了' : '全画面表示'}</Button>
        </VStack>
      </CardBody>
    </Card>
  )
}


