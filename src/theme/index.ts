import { useColorScheme } from 'react-native';

import { usePalette, useTheme } from '@/db/settings';

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

// How far the phone's text size may enlarge the app's text (src/components/Text.tsx). iPhone's largest accessibility
// size is about 3 times, which leaves a word or two on a line, or a letter or two of a title. The bars have a fixed
// height. The reader has its own size setting, up to 30, on top of the phone's.
export const MAX_SCALE = { ui: 1.5, bar: 1.3, reader: 2 } as const;

// The text is fully vocalized: iOS clips the marks above and below a line when the line height is tight.
export const TEXT_LINE_HEIGHT = 2;

// The colours, in three palettes (the settings screen's «الألوان»), each light and dark. `accent` is the app's own:
// buttons, icons, headings, the item chosen; `prophet` is only for the Prophet's words ﷺ, which are bold as well, so they
// stand out in greyscale and for colour-blind readers too. Every text colour has at least 4.5:1 contrast on its
// background, and on `highlight`, except the Manuscript's dark red on the dark highlight (4.3:1, on bold text).
export type Palette = 'green' | 'gold' | 'manuscript';

export interface Colors {
  background: string;
  surface: string;
  text: string;
  muted: string;
  border: string;
  accent: string;
  prophet: string;
  // Other people's words, such as a Companion's question: set apart from the narration, more quietly than the Prophet's.
  speech: string;
  // Behind the words a search found.
  highlight: string;
}

// The first palette, and the default: green and grey-green. Its dark highlight is slate rather than the first amber
// (#5E4C14), behind which the Prophet's green and the speech blue had only 4.2:1.
const green: Record<'light' | 'dark', Colors> = {
  light: {
    background: '#FBFCFC',
    surface: '#F1F5F4',
    text: '#14211F',
    muted: '#55625F',
    border: '#D6DFDC',
    accent: '#0B6E5F',
    prophet: '#0B6E5F',
    speech: '#3D4F6B',
    highlight: '#F9E3A0',
  },
  dark: {
    background: '#0F1615',
    surface: '#172120',
    text: '#E4ECEA',
    muted: '#9AABA7',
    border: '#2A3735',
    accent: '#5CC9B4',
    prophet: '#5CC9B4',
    speech: '#A9B9D6',
    highlight: '#3A3F55',
  },
};

// The icon's colours: gold on its near-black in dark mode, and a deeper bronze-gold on paper in light mode, where the
// icon's own gold (#FFD700) would be unreadable (1.4:1).
const gold: Record<'light' | 'dark', Colors> = {
  light: {
    background: '#FAF7F0',
    surface: '#F2EDE1',
    text: '#1C1A16',
    muted: '#6A6255',
    border: '#E2DACA',
    accent: '#8A6500',
    prophet: '#7A5600',
    speech: '#3F4C66',
    highlight: '#FBE7B0',
  },
  dark: {
    background: '#111318',
    surface: '#1A1D24',
    text: '#ECE7DA',
    muted: '#A39C8E',
    border: '#2A2F3A',
    accent: '#E9C54A',
    prophet: '#F2CF5B',
    speech: '#AEBBD3',
    highlight: '#3A3F55',
  },
};

// The gold palette, with the Prophet's words in a rubric red, as many printed hadith books and manuscripts mark them.
const manuscript: Record<'light' | 'dark', Colors> = {
  light: { ...gold.light, prophet: '#9A2B2B' },
  dark: { ...gold.dark, prophet: '#F08C80' },
};

export const PALETTES: Record<Palette, Record<'light' | 'dark', Colors>> = { green, gold, manuscript };

// The theme setting: the phone's, or light or dark whatever the phone's is. The screens read the setting itself, and
// the phone's own views (alerts, the keyboard) follow it through Appearance (src/app/_layout.tsx).
export function useScheme(): 'light' | 'dark' {
  const theme = useTheme();
  const system = useColorScheme();
  return (theme === 'system' ? system : theme) === 'dark' ? 'dark' : 'light';
}

export function useColors(): Colors {
  return PALETTES[usePalette()][useScheme()];
}
