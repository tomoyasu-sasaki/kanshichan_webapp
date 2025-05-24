import React from 'react';
import { Button, Menu, MenuButton, MenuList, MenuItem, Icon } from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';
import { useTranslation } from 'react-i18next';
import { FaGlobe } from 'react-icons/fa';

const LanguageSwitcher: React.FC = () => {
  const { i18n, t } = useTranslation();

  const changeLanguage = (language: string) => {
    i18n.changeLanguage(language);
  };

  const getCurrentLanguageLabel = () => {
    return i18n.language === 'en' ? 'English' : '日本語';
  };

  return (
    <Menu>
      <MenuButton
        as={Button}
        rightIcon={<ChevronDownIcon />}
        leftIcon={<Icon as={FaGlobe} />}
        variant="outline"
        size="sm"
      >
        {getCurrentLanguageLabel()}
      </MenuButton>
      <MenuList>
        <MenuItem onClick={() => changeLanguage('ja')}>
          {t('settings.language.japanese')}
        </MenuItem>
        <MenuItem onClick={() => changeLanguage('en')}>
          {t('settings.language.english')}
        </MenuItem>
      </MenuList>
    </Menu>
  );
};

export default LanguageSwitcher; 