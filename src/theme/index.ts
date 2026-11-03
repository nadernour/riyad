import { useColorScheme } from 'react-native';

import { useTheme } from '@/db/settings';

// Font family names, as loaded by useFonts in src/app/_layout.tsx. Scheherazade New for the book's text, Cairo for the
// interface (as in v1). v1's Amiri was dropped: it crowds the marks of short letters, such as لَيْلَةَ and وَآخِرَ.
export const fonts = {
  text: 'ScheherazadeNew',
  textBold: 'ScheherazadeNew-Bold',
  ui: 'Cairo',
  uiSemiBold: 'Cairo-SemiBold',
  uiBold: 'Cairo-Bold',
} as const;

export const fontFiles = {
  [fonts.text]: require('../../assets/fonts/ScheherazadeNew-Regular.ttf'),
  [fonts.textBold]: require('../../assets/fonts/ScheherazadeNew-Bold.ttf'),
  [fonts.ui]: require('../../assets/fonts/Cairo-Regular.ttf'),
  [fonts.uiSemiBold]: require('../../assets/fonts/Cairo-SemiBold.ttf'),
  [fonts.uiBold]: require('../../assets/fonts/Cairo-Bold.ttf'),
};

// The text is fully vocalized: iOS clips the marks above and below a line when the line height is tight.
export const TEXT_LINE_HEIGHT = 2;

const light = {
  background: '#FBFCFC',
  surface: '#F1F5F4',
  text: '#14211F',
  muted: '#55625F',
  border: '#D6DFDC',
  prophet: '#0B6E5F',
  // Other people's words, such as a Companion's question: set apart from the narration, more quietly than the Prophet's.
  speech: '#3D4F6B',
};

export type Colors = typeof light;

const dark: Colors = {
  background: '#0F1615',
  surface: '#172120',
  text: '#E4ECEA',
  muted: '#9AABA7',
  border: '#2A3735',
  prophet: '#5CC9B4',
  speech: '#A9B9D6',
};

// The theme setting: the phone's, or light or dark whatever the phone's is. The screens read the setting itself, and
// the phone's own views (alerts, the keyboard) follow it through Appearance (src/app/_layout.tsx).
export function useColors(): Colors {
  const theme = useTheme();
  const system = useColorScheme();
  return (theme === 'system' ? system : theme) === 'dark' ? dark : light;
}

export function useIsDark(): boolean {
  return useColors() === dark;
}
