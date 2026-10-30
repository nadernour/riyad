import { useColorScheme } from 'react-native';

// Font family names, as loaded by useFonts in src/app/_layout.tsx. Amiri for the book's text, Cairo for the interface (as in v1).
export const fonts = {
  text: 'Amiri',
  textBold: 'Amiri-Bold',
  ui: 'Cairo',
  uiSemiBold: 'Cairo-SemiBold',
  uiBold: 'Cairo-Bold',
} as const;

export const fontFiles = {
  [fonts.text]: require('../../assets/fonts/Amiri-Regular.ttf'),
  [fonts.textBold]: require('../../assets/fonts/Amiri-Bold.ttf'),
  [fonts.ui]: require('../../assets/fonts/Cairo-Regular.ttf'),
  [fonts.uiSemiBold]: require('../../assets/fonts/Cairo-SemiBold.ttf'),
  [fonts.uiBold]: require('../../assets/fonts/Cairo-Bold.ttf'),
};

// The text is fully vocalized: iOS clips the marks above and below a line when the line height is tight.
export const TEXT_LINE_HEIGHT = 2;

// v1's default; the setting for it comes in P4. v1 lets it range from 14 to 30.
export const DEFAULT_FONT_SIZE = 24;

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

// Follows the phone's setting for now; the System / Light / Dark setting comes in P4.
export function useColors(): Colors {
  return useColorScheme() === 'dark' ? dark : light;
}
