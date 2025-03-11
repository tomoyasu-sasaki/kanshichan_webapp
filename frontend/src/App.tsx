import { Container, VStack } from '@chakra-ui/react'
import { MonitorView } from './components/MonitorView'
import { SettingsPanel } from './components/SettingsPanel'

function App() {
  return (
    <Container maxW="container.xl" py={4}>
      <VStack spacing={8} align="stretch">
        <MonitorView />
        <SettingsPanel />
      </VStack>
    </Container>
  )
}

export default App
