import { Container, Tabs, TabList, TabPanels, Tab, TabPanel } from '@chakra-ui/react'
import { MonitorView } from './components/MonitorView'
import { SettingsPanel } from './components/SettingsPanel'
import { ScheduleView } from './components/ScheduleView'

function App() {
  return (
    <Container maxW="container.xl" py={4}>
      <Tabs>
        <TabList>
          <Tab>モニター</Tab>
          <Tab>スケジュール</Tab>
          <Tab>設定</Tab>
        </TabList>
        <TabPanels>
          <TabPanel px={0}>
            <MonitorView />
          </TabPanel>
          <TabPanel px={0}>
            <ScheduleView />
          </TabPanel>
          <TabPanel px={0}>
            <SettingsPanel />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Container>
  )
}

export default App
