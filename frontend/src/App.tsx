import { ChakraProvider } from '@chakra-ui/react'
import { IntegratedDashboard } from './components/IntegratedDashboard'

function App() {
  return (
    <ChakraProvider>
      <IntegratedDashboard 
        userId="default"
        autoRefresh={true}
        refreshInterval={30}
      />
    </ChakraProvider>
  )
}

export default App
