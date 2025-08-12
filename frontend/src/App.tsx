import { IntegratedDashboard } from './components/dashboard/IntegratedDashboard'
import { Box } from '@chakra-ui/react'

function App() {
  return (
    <Box minH="100vh">
      <IntegratedDashboard
        userId="default"
        autoRefresh={true}
        refreshInterval={30}
      />
    </Box>
  )
}

export default App
