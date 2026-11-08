/**
 * @jest-environment node
 */
import path from 'path';

import { openContentDb } from '@/db/testing';

import cases from '../../database/simplify.json';

import { findMatches, simplifyMapped, snippet, splitAt } from './highlight';
import { simplify } from './simplify';

const db = openContentDb(path.join(__dirname, '../../database/riyad.db'));

async function hadithTexts(): Promise<{ id: number; text: string; title: string }[]> {
  const pieces = await db.getAllAsync<{ id: number; text: string }>(
    'SELECT hadith_id AS id, text FROM matn_pieces ORDER BY hadith_id, seq',
    [],
  );
  const texts = new Map<number, string>();
  for (const piece of pieces) texts.set(piece.id, (texts.get(piece.id) ?? '') + piece.text);
  const titles = await db.getAllAsync<{ id: number; title: string }>('SELECT id, title FROM hadith', []);
  return titles.map(({ id, title }) => ({ id, title, text: texts.get(id) ?? '' }));
}

test('simplifies one character at a time exactly as simplify() does, on every hadith and test case', async () => {
  for (const [input] of cases.cases) expect(simplifyMapped(input).simplified).toBe(simplify(input));
  for (const { text, title } of await hadithTexts()) {
    expect(simplifyMapped(text).simplified).toBe(simplify(text));
    expect(simplifyMapped(title).simplified).toBe(simplify(title));
  }
});

test('finds each place a query matches, with its marks, where search finds it', async () => {
  const text = 'قَالَ رَسُولُ اللَّهِ ﷺ: «إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ»';
  const ranges = findMatches(text, 'انما');
  expect(ranges.map((range) => text.slice(range.start, range.end))).toEqual(['إِنَّمَا', 'إِنَّمَا']);
  // Inside a word, and across words.
  expect(findMatches(text, 'اعمال').map((r) => text.slice(r.start, r.end))).toEqual(['أَعْمَالُ']);
  expect(findMatches(text, 'انما الاعمال').map((r) => text.slice(r.start, r.end))).toEqual(['إِنَّمَا الأَعْمَالُ']);
  // The salutation, written out.
  expect(findMatches(text, 'عليه وسلم').map((r) => text.slice(r.start, r.end))).toEqual(['ﷺ']);
  expect(findMatches(text, 'في')).toEqual([]);
});

test('every match, in every hadith search finds, is the query once simplified', async () => {
  const query = 'الصلاه';
  let found = 0;
  for (const { text } of await hadithTexts()) {
    const ranges = findMatches(text, query);
    if (simplify(text).includes(query)) expect(ranges.length).toBeGreaterThan(0);
    for (const range of ranges) expect(simplify(text.slice(range.start, range.end))).toContain(query);
    found += ranges.length;
  }
  expect(found).toBeGreaterThan(100);
});

test("cuts pieces at the matches, keeping each piece's other fields", () => {
  const pieces = [
    { role: 'narration', text: 'قال: ' },
    { role: 'prophet', text: 'إنما الأعمال' },
  ];
  const spans = splitAt(pieces, [{ start: 3, end: 9 }]);
  expect(spans).toEqual([
    { role: 'narration', text: 'قال', matched: false },
    { role: 'narration', text: ': ', matched: true },
    { role: 'prophet', text: 'إنما', matched: true },
    { role: 'prophet', text: ' الأعمال', matched: false },
  ]);
  expect(spans.map((span) => span.text).join('')).toBe(pieces.map((piece) => piece.text).join(''));
});

test('a snippet starts at a word a little before the first match, and keeps the matches in place', () => {
  const text = 'كلمة '.repeat(20) + 'الصلاة خير\nمن النوم';
  const ranges = findMatches(text, 'الصلاه');
  const cut = snippet(text, ranges);
  expect(cut.text.startsWith('… كلمة')).toBe(true);
  expect(cut.text.slice(cut.ranges[0].start, cut.ranges[0].end)).toBe('الصلاة');
  expect(cut.text).not.toContain('\n');
  // A match near the start: the text's start.
  expect(snippet('الصلاة خير', findMatches('الصلاة خير', 'الصلاه')).text).toBe('الصلاة خير');
  // Only so much of a long text, as two lines show, ending at the end of a word, with its marks.
  const long = snippet('كَلِمَةٌ '.repeat(100), []);
  expect(long.text.length).toBeLessThanOrEqual(210);
  expect(long.text.endsWith('كَلِمَةٌ')).toBe(true);
  // A match it reaches is taken in whole.
  const phrase = 'كلمة '.repeat(39) + 'صلاة الجماعة';
  const reached = snippet(phrase, [{ start: 195, end: phrase.length }]);
  expect(reached.text.endsWith("صلاة الجماعة")).toBe(true);
  expect(reached.ranges[0].end).toBe(reached.text.length);
});
