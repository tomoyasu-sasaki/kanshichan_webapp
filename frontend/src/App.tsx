import { Container, Tabs, TabList, TabPanels, Tab, TabPanel, Flex, Heading, Spacer } from '@chakra-ui/react'
import { useTranslation } from 'react-i18next'
import { MonitorView } from './components/MonitorView'
import { SettingsPanel } from './components/SettingsPanel'
import { ScheduleView } from './components/ScheduleView'
import LanguageSwitcher from './components/LanguageSwitcher'

function App() {
  const { t } = useTranslation();

  return (
    <Container maxW="container.xl" py={4}>
      <Flex mb={4} align="center">
        <Heading size="lg">{t('app.title')}</Heading>
        <Spacer />
        <LanguageSwitcher />
      </Flex>
      <Tabs>
        <TabList>
          <Tab>{t('tabs.monitor')}</Tab>
          <Tab>{t('tabs.schedule')}</Tab>
          <Tab>{t('tabs.settings')}</Tab>
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
