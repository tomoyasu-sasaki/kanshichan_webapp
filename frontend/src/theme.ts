import { extendTheme } from '@chakra-ui/theme-utils'
import { type ThemeConfig } from '@chakra-ui/theme'

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: false,
}

export const theme = extendTheme({ config }) 