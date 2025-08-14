import { Badge, Card, CardBody, CardHeader, Flex, HStack, Heading, Icon, IconButton, Spinner, Text, Tooltip, VStack, useColorModeValue } from '@chakra-ui/react'
import { FaCompress, FaExpand, FaVideo } from 'react-icons/fa'
import { FiCamera, FiMaximize, FiMinimize, FiRefreshCw } from 'react-icons/fi'
import { MutableRefObject } from 'react'

interface VideoFeedProps {
  containerRef: MutableRefObject<HTMLDivElement | null>
  videoRef: MutableRefObject<HTMLImageElement | null>
  fitMode: 'contain' | 'cover'
  isFullscreen: boolean
  isVideoLoading: boolean
  lastUpdateAt: number | null
  liveDelta: number
  liveColor: 'gray' | 'green' | 'yellow' | 'red'
  onCapture: () => void
  onReconnect: () => void
  onToggleFit: () => void
  onToggleFullscreen: () => void
  overlay?: React.ReactNode
}

export const VideoFeed: React.FC<VideoFeedProps> = ({ containerRef, videoRef, fitMode, isFullscreen, isVideoLoading, lastUpdateAt, liveDelta, liveColor, onCapture, onReconnect, onToggleFit, onToggleFullscreen, overlay }) => {
  const borderColor = useColorModeValue('gray.300', 'gray.600')

  return (
    <Card ref={containerRef as React.RefObject<HTMLDivElement>} bg="black" overflow="hidden" height={isFullscreen ? '100vh' : { base: '400px', md: '500px', lg: '600px' }} shadow="xl" border="2px solid" borderColor={borderColor}>
      <CardHeader bg="rgba(0,0,0,0.8)" backdropFilter="blur(10px)">
        <HStack justify="space-between" color="white">
          <HStack spacing={3}>
            <Icon as={FaVideo} color="blue.400" boxSize={5} />
            <Heading size="md">ライブフィード</Heading>
            <Badge colorScheme={liveColor} variant="solid" px={3} py={1} borderRadius="full">
              {liveDelta === Infinity ? 'OFFLINE' : 'LIVE'}
            </Badge>
          </HStack>
          <HStack spacing={3}>
            <Text fontSize="sm" color="gray.300">{fitMode === 'contain' ? 'フィット表示' : 'フル表示'}</Text>
            <Text fontSize="xs" color="gray.400">{lastUpdateAt ? new Date(lastUpdateAt).toLocaleTimeString() : '未接続'}</Text>
          </HStack>
        </HStack>
      </CardHeader>

      <CardBody position="relative" p={0}>
        <img ref={videoRef} alt="Monitor Feed" style={{ width: '100%', height: '100%', objectFit: fitMode, backgroundColor: '#000' }} />

        {isVideoLoading && (
          <Flex position="absolute" top={0} left={0} right={0} bottom={0} justify="center" align="center" bg="rgba(0,0,0,0.7)" backdropFilter="blur(5px)">
            <VStack spacing={4}>
              <Spinner size="xl" color="blue.400" thickness="4px" />
              <Text color="white" fontSize="lg" fontWeight="medium">ビデオストリーム読み込み中...</Text>
            </VStack>
          </Flex>
        )}

        {overlay}

        <HStack position="absolute" bottom={4} left={4} spacing={2} bg="rgba(0,0,0,0.8)" borderRadius="lg" p={2} backdropFilter="blur(10px)">
          <Tooltip label="スクリーンショット撮影">
            <IconButton aria-label="screenshot" icon={<FiCamera />} onClick={onCapture} colorScheme="blue" variant="solid" size="sm" />
          </Tooltip>
          <Tooltip label="ストリーム再接続">
            <IconButton aria-label="reconnect" icon={<FiRefreshCw />} onClick={onReconnect} colorScheme="green" variant="solid" size="sm" />
          </Tooltip>
          <Tooltip label={fitMode === 'contain' ? 'フル表示に切り替え' : 'フィット表示に切り替え'}>
            <IconButton aria-label="fitmode" icon={fitMode === 'contain' ? <FiMaximize /> : <FiMinimize />} onClick={onToggleFit} colorScheme="purple" variant="solid" size="sm" />
          </Tooltip>
        </HStack>

        <Tooltip label={isFullscreen ? '全画面終了' : '全画面表示'}>
          <IconButton aria-label="fullscreen" icon={isFullscreen ? <FaCompress /> : <FaExpand />} position="absolute" bottom={4} right={4} colorScheme="orange" variant="solid" onClick={onToggleFullscreen} bg="rgba(0,0,0,0.8)" backdropFilter="blur(10px)" _hover={{ bg: 'orange.500' }} />
        </Tooltip>
      </CardBody>
    </Card>
  )
}


