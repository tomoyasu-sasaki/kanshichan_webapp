import React from 'react';
import {
  Box,
  VStack,
  Heading,
  Button,
  Divider,
  Text,
  Icon,
  useColorModeValue
} from '@chakra-ui/react';
import {
  FiTrendingUp,
  FiHome,
  FiVolumeX,
  FiCalendar,
  FiSettings,
  FiActivity,
  FiTarget
} from 'react-icons/fi';
import { useTranslation } from 'react-i18next';
import { LanguageSwitcher } from '../../LanguageSwitcher';

interface SidebarNavProps {
  selectedView: string;
  onChange: (view: string) => void;
}

export const SidebarNav: React.FC<SidebarNavProps> = ({ selectedView, onChange }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const { t } = useTranslation();

  return (
    <Box role="navigation" position="fixed" height="100vh" width="250px" bg={cardBg} p={4} overflowY="auto" display="flex" flexDirection="column">
      <VStack spacing={3} align="stretch" flex="1">
        <Heading size="md" mb={4}>{t('app.title')}</Heading>

        <Button
          variant={selectedView === 'overview' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiTrendingUp} />}
          onClick={() => onChange('overview')}
          aria-current={selectedView === 'overview' ? 'page' : undefined}
          aria-label={t('tabs.overview')}
        >
          {t('tabs.overview')}
        </Button>

        <Divider />
        <Text fontSize="sm" fontWeight="bold" color="gray.500">{t('nav.sections.core')}</Text>

        <Button
          variant={selectedView === 'monitor' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiHome} />}
          onClick={() => onChange('monitor')}
          aria-current={selectedView === 'monitor' ? 'page' : undefined}
          aria-label={t('tabs.monitor')}
        >
          {t('tabs.monitor')}
        </Button>

        <Button
          variant={selectedView === 'voice' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiVolumeX} />}
          onClick={() => onChange('voice')}
          aria-current={selectedView === 'voice' ? 'page' : undefined}
          aria-label={t('tabs.voice')}
        >
          {t('tabs.voice')}
        </Button>

        <Button
          variant={selectedView === 'schedule' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiCalendar} />}
          onClick={() => onChange('schedule')}
          aria-current={selectedView === 'schedule' ? 'page' : undefined}
          aria-label={t('tabs.schedule')}
        >
          {t('tabs.schedule')}
        </Button>

        <Button
          variant={selectedView === 'settings' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiSettings} />}
          onClick={() => onChange('settings')}
          aria-current={selectedView === 'settings' ? 'page' : undefined}
          aria-label={t('tabs.settings')}
        >
          {t('tabs.settings')}
        </Button>

        <Button
          variant={selectedView === 'behavior' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiActivity} />}
          onClick={() => onChange('behavior')}
          aria-current={selectedView === 'behavior' ? 'page' : undefined}
          aria-label={t('tabs.behavior')}
        >
          {t('tabs.behavior')}
        </Button>

        <Divider />
        <Text fontSize="sm" fontWeight="bold" color="gray.500">{t('nav.sections.advanced')}</Text>

        <Button
          variant={selectedView === 'analytics' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiTarget} />}
          onClick={() => onChange('analytics')}
          aria-current={selectedView === 'analytics' ? 'page' : undefined}
          aria-label={t('tabs.analytics')}
        >
          {t('tabs.analytics')}
        </Button>

        <Button
          variant={selectedView === 'personalization' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiSettings} />}
          onClick={() => onChange('personalization')}
          aria-current={selectedView === 'personalization' ? 'page' : undefined}
          aria-label={t('tabs.personalization')}
        >
          {t('tabs.personalization')}
        </Button>

        <Button
          variant={selectedView === 'predictions' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiTrendingUp} />}
          onClick={() => onChange('predictions')}
          aria-current={selectedView === 'predictions' ? 'page' : undefined}
          aria-label={t('tabs.predictions')}
        >
          {t('tabs.predictions')}
        </Button>

        <Button
          variant={selectedView === 'learning' ? 'solid' : 'ghost'}
          justifyContent="flex-start"
          leftIcon={<Icon as={FiActivity} />}
          onClick={() => onChange('learning')}
          aria-current={selectedView === 'learning' ? 'page' : undefined}
          aria-label={t('tabs.learning')}
        >
          {t('tabs.learning')}
        </Button>
      </VStack>
      <Box pt={2}>
        <LanguageSwitcher />
      </Box>
    </Box>
  );
};


