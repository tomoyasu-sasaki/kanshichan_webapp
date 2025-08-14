import { Box, HStack, Icon, Text, VStack } from '@chakra-ui/react'
import { FiSmartphone, FiXCircle, FiCheckCircle } from 'react-icons/fi'
import { DetectionStatus } from '../types'

interface DetectionOverlayProps {
  status: DetectionStatus
}

export const DetectionOverlay: React.FC<DetectionOverlayProps> = ({ status }) => {
  return (
    <Box position="absolute" top={4} left={4} bg="rgba(0,0,0,0.8)" borderRadius="lg" p={3} backdropFilter="blur(10px)">
      <VStack spacing={2} align="start">
        <HStack spacing={2}>
          <Icon as={status.personDetected ? FiCheckCircle : FiXCircle} color={status.personDetected ? 'green.400' : 'red.400'} boxSize={4} />
          <Text color="white" fontSize="sm" fontWeight="medium">{status.personDetected ? '人物検知' : '人物未検知'}</Text>
        </HStack>
        <HStack spacing={2}>
          <Icon as={FiSmartphone} color={status.smartphoneDetected ? 'orange.400' : 'green.400'} boxSize={4} />
          <Text color="white" fontSize="sm" fontWeight="medium">{status.smartphoneDetected ? 'スマホ検知' : 'スマホ未検知'}</Text>
        </HStack>
      </VStack>
    </Box>
  )
}


