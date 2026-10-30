/**
 * @jest-environment node
 */
import path from 'path';

import { checkSchema, getHadith, getHadithCount, getInfo, listBooks, listChapters, search, SEARCH_LIMIT } from './content';
import { openContentDb } from './testing';

const db = openContentDb(path.join(__dirname, '../../database/riyad.db'));

test('the database has the schema the app is written for', async () => {
  await expect(checkSchema(db)).resolves.toBeUndefined();
});

test('info and count agree', async () => {
  const info = await getInfo(db);
  expect(Number(info.hadith)).toBe(await getHadithCount(db));
});

test('hadith 1, with its titles and text', async () => {
  const hadith = await getHadith(db, 1);
  expect(hadith).toMatchObject({ id: 1, bookId: 1, book: 'الكتاب الأول', chapterId: 1 });
  expect(hadith!.page).toBeGreaterThan(0);
  expect(hadith!.pieces.map((piece) => piece.role)).toContain('prophet');
  // Its short title is a phrase of its text, with the text's marks.
  expect(hadith!.pieces.map((piece) => piece.text).join('')).toContain(hadith!.title);
});

test('every hadith number from 1 to the count exists', async () => {
  const count = await getHadithCount(db);
  const ids = await db.getAllAsync<{ id: number }>('SELECT id FROM hadith ORDER BY id', []);
  expect(ids.map((row) => row.id)).toEqual(Array.from({ length: count }, (_, i) => i + 1));
});

test('a hadith that does not exist', async () => {
  expect(await getHadith(db, 0)).toBeNull();
  expect(await getHadith(db, (await getHadithCount(db)) + 1)).toBeNull();
});

test('books and chapters, each with its first hadith', async () => {
  const books = await listBooks(db);
  expect(books).toHaveLength(20);
  expect(books[0]).toEqual({ id: 1, title: 'الكتاب الأول', firstHadith: 1 });

  const chapters = await listChapters(db, 1);
  expect(chapters[0]).toMatchObject({ id: 1, firstHadith: 1 });
  for (let i = 1; i < chapters.length; i++) expect(chapters[i].firstHadith).toBeGreaterThan(chapters[i - 1].firstHadith);
});

describe('search', () => {
  const ids = async (query: string) => (await search(db, query)).map((result) => result.id);

  test('finds words, ignoring tashkeel', async () => {
    expect(await ids('إنما الأعمال بالنيات')).toContain(1);
    expect(await ids('إِنَّمَا الأَعْمَالُ')).toContain(1);
  });

  test('ignores the forms of alif, ta marbuta and alif maqsura', async () => {
    expect(await ids('انما الاعمال')).toEqual(await ids('إنما الأعمال'));
    expect(await ids('الصلاة')).toEqual(await ids('الصلاه'));
  });

  test('finds part of a word', async () => {
    expect(await ids('اعمال')).toContain(1);
  });

  test('opens a hadith by its number, in any kind of digits', async () => {
    expect(await ids('1500')).toEqual([1500]);
    expect(await ids('١٥٠٠')).toEqual([1500]);
    expect(await ids('۱۵۰۰')).toEqual([1500]);
    expect(await ids('٧')).toEqual([7]);
    expect(await ids('99999')).toEqual([]);
  });

  test('returns nothing for a query too short to search', async () => {
    expect(await ids('في')).toEqual([]);
    expect(await ids('  ')).toEqual([]);
  });

  test('returns the first matches up to the limit, in the book order', async () => {
    const found = await ids('الله');
    expect(found).toHaveLength(SEARCH_LIMIT);
    expect(found).toEqual([...found].sort((a, b) => a - b));
    const all = await db.getAllAsync<{ rowid: number }>(
      'SELECT rowid FROM hadith_search WHERE hadith_search MATCH ? ORDER BY rowid',
      ['"الله"'],
    );
    expect(found).toEqual(all.slice(0, SEARCH_LIMIT).map((row) => row.rowid));
  });

  test('quotes in a query cannot break the search', async () => {
    await expect(search(db, 'الله" OR "')).resolves.toBeDefined();
  });
});
