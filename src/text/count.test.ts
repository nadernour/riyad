import { CHAPTER, count, HADITH } from './count';

test('counts as Arabic counts', () => {
  expect(count(1, HADITH)).toBe('حديث واحد');
  expect(count(2, HADITH)).toBe('حديثان');
  expect(count(3, HADITH)).toBe('3 أحاديث');
  expect(count(10, HADITH)).toBe('10 أحاديث');
  expect(count(11, HADITH)).toBe('11 حديثًا');
  expect(count(99, HADITH)).toBe('99 حديثًا');
  expect(count(100, HADITH)).toBe('100 حديث');
  expect(count(102, HADITH)).toBe('102 حديث');
  expect(count(103, HADITH)).toBe('103 أحاديث');
  expect(count(1898, HADITH)).toBe('1898 حديثًا');
  expect(count(115, CHAPTER)).toBe('115 بابًا');
});
