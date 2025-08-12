import React, { useCallback } from 'react';
import { Button, Menu, MenuButton, MenuItem, MenuList } from '@chakra-ui/react';
import { FaGlobe } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';

export const LanguageSwitcher: React.FC = () => {
  const { i18n, t } = useTranslation();

  const changeLanguage = useCallback(
    (lang: 'ja' | 'en') => {
      i18n.changeLanguage(lang);
    },
    [i18n]
  );

  const currentLabel = i18n.language === 'en' ? 'English' : '日本語';

  return (
    <Menu>
      <MenuButton as={Button} leftIcon={<FaGlobe />} aria-label={t('settings.language.title') || 'Language'}>
        {currentLabel}
      </MenuButton>
      <MenuList>
        <MenuItem onClick={() => changeLanguage('ja')}>{t('settings.language.japanese') || '日本語'}</MenuItem>
        <MenuItem onClick={() => changeLanguage('en')}>{t('settings.language.english') || 'English'}</MenuItem>
      </MenuList>
    </Menu>
  );
};

export default LanguageSwitcher;


