/**
 * @jest-environment node
 */
import { FONT_SIZE, parseFontSize, parseSearchOrder, parseTheme, setFontSize, setSearchOrder, setTheme } from './settings';
import { openUserDb } from './testing';
import { getSetting, migrateUserDb } from './user';

const mockDb = openUserDb();
migrateUserDb(mockDb);
jest.mock('./userDb', () => ({ userDb: () => mockDb }));

test('a font size reads as one of v1 steps, within its range', () => {
  expect(parseFontSize(null)).toBe(FONT_SIZE.default);
  expect(parseFontSize('nonsense')).toBe(FONT_SIZE.default);
  expect(parseFontSize('18')).toBe(18);
  expect(parseFontSize('19')).toBe(20);
  expect(parseFontSize('8')).toBe(FONT_SIZE.min);
  expect(parseFontSize('40')).toBe(FONT_SIZE.max);
});

test('a theme the app does not know reads as the system one', () => {
  expect(parseTheme('dark')).toBe('dark');
  expect(parseTheme(null)).toBe('system');
  expect(parseTheme('sepia')).toBe('system');
});

test('search shows the closest matches first unless the book order was chosen', () => {
  expect(parseSearchOrder(null)).toBe('relevance');
  expect(parseSearchOrder('book')).toBe('book');
  expect(parseSearchOrder('random')).toBe('relevance');
});

test('settings are saved in user.db', () => {
  setFontSize(29);
  setTheme('dark');
  setSearchOrder('book');
  expect(getSetting(mockDb, 'searchOrder')).toBe('book');
  expect(getSetting(mockDb, 'fontSize')).toBe('30');
  expect(getSetting(mockDb, 'theme')).toBe('dark');
});
