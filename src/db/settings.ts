import { useSyncExternalStore } from 'react';

import type { Palette } from '@/theme';

import type { SearchOrder } from './content';
import { getSetting, setSetting } from './user';
import { userDb } from './userDb';

// The reader's settings, kept in user.db's settings table, as every screen sees them: the reader, the settings
// screen and the theme and palette change together. The order of search results is kept with them, as the search screen last had it.
export type Theme = 'system' | 'light' | 'dark';

export interface Settings {
  fontSize: number;
  theme: Theme;
  palette: Palette;
  searchOrder: SearchOrder;
}

// v1's default and range, in v1's steps of 2.
export const FONT_SIZE = { min: 14, max: 30, step: 2, default: 24 } as const;

// Search shows the closest matches first unless asked for the book's order (v1 had only the book's).
const DEFAULTS: Settings = { fontSize: FONT_SIZE.default, theme: 'system', palette: 'green', searchOrder: 'relevance' };

// A saved value the app no longer knows, or none, reads as the default.
export function parseFontSize(value: string | null): number {
  const size = Number(value);
  if (!value || !Number.isFinite(size)) return FONT_SIZE.default;
  const stepped = FONT_SIZE.min + Math.round((size - FONT_SIZE.min) / FONT_SIZE.step) * FONT_SIZE.step;
  return Math.min(FONT_SIZE.max, Math.max(FONT_SIZE.min, stepped));
}

export function parseTheme(value: string | null): Theme {
  return value === 'light' || value === 'dark' || value === 'system' ? value : DEFAULTS.theme;
}

// Every palette, as the type has them, so a new one can't be missed here.
const PALETTE_NAMES: Record<Palette, true> = { green: true, gold: true, manuscript: true };

export function parsePalette(value: string | null): Palette {
  return value && Object.prototype.hasOwnProperty.call(PALETTE_NAMES, value) ? (value as Palette) : DEFAULTS.palette;
}

export function parseSearchOrder(value: string | null): SearchOrder {
  return value === 'book' || value === 'relevance' ? value : DEFAULTS.searchOrder;
}

const listeners = new Set<() => void>();
let snapshot: Settings | null = null;
// When user.db last failed to be read: it is tried again only after RETRY_MS, since every view reads the theme.
let failedAt = -Infinity;
const RETRY_MS = 5000;

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

// If user.db can't be read, the app reads with the defaults, and tries user.db again a little later.
function getSnapshot(): Settings {
  if (!snapshot) {
    if (Date.now() - failedAt < RETRY_MS) return DEFAULTS;
    try {
      const db = userDb();
      snapshot = {
        fontSize: parseFontSize(getSetting(db, 'fontSize')),
        theme: parseTheme(getSetting(db, 'theme')),
        palette: parsePalette(getSetting(db, 'palette')),
        searchOrder: parseSearchOrder(getSetting(db, 'searchOrder')),
      };
    } catch {
      failedAt = Date.now();
      return DEFAULTS;
    }
  }
  return snapshot;
}

// A change shows at once, even if user.db can't be written: then it lasts until the app is closed.
function change(key: keyof Settings, value: string, next: Settings) {
  snapshot = next;
  try {
    setSetting(userDb(), key, value);
  } catch {
    // As above.
  }
  listeners.forEach((listener) => listener());
}

export function useSettings(): Settings {
  return useSyncExternalStore(subscribe, getSnapshot);
}

// One setting alone, so that a view re-renders only when that one changes: every view reads the theme.
export function useTheme(): Theme {
  return useSyncExternalStore(subscribe, () => getSnapshot().theme);
}

export function usePalette(): Palette {
  return useSyncExternalStore(subscribe, () => getSnapshot().palette);
}

export function useFontSize(): number {
  return useSyncExternalStore(subscribe, () => getSnapshot().fontSize);
}

export function useSearchOrder(): SearchOrder {
  return useSyncExternalStore(subscribe, () => getSnapshot().searchOrder);
}

export function setFontSize(size: number) {
  const fontSize = parseFontSize(String(size));
  change('fontSize', String(fontSize), { ...getSnapshot(), fontSize });
}

export function setTheme(theme: Theme) {
  change('theme', theme, { ...getSnapshot(), theme });
}

export function setPalette(palette: Palette) {
  change('palette', palette, { ...getSnapshot(), palette });
}

export function setSearchOrder(searchOrder: SearchOrder) {
  change('searchOrder', searchOrder, { ...getSnapshot(), searchOrder });
}
