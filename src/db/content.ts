import { simplify } from '@/search/simplify';

// Reads database/riyad.db; database/README.md describes its tables. The functions take this interface rather than
// expo-sqlite's SQLiteDatabase, which has it, so that the tests can run the same SQL with Node's own SQLite.
export interface ContentDb {
  getAllAsync<T>(source: string, params: (string | number)[]): Promise<T[]>;
  getFirstAsync<T>(source: string, params: (string | number)[]): Promise<T | null>;
}

// PRAGMA user_version of the database this code is written for. It rises whenever the tables change.
export const SCHEMA_VERSION = 2;

export type Role = 'narration' | 'prophet' | 'speech' | 'gloss';

export interface Piece {
  role: Role;
  text: string;
}

export interface Meaning {
  term: string;
  meaning: string;
}

export interface Hadith {
  id: number;
  title: string;
  page: number;
  bookId: number;
  book: string;
  chapterId: number;
  chapter: string;
  pieces: Piece[];
  // Empty until content step 5 transcribes them: a screen shows nothing for them then.
  meanings: Meaning[];
  benefits: string[];
}

export interface Book {
  id: number;
  title: string;
  firstHadith: number;
}

export interface Chapter {
  id: number;
  title: string;
  firstHadith: number;
}

export interface SearchResult {
  id: number;
  title: string;
  book: string;
  chapter: string;
}

// The shortest simplified query search runs: the index is of trigrams, so a shorter one matches nothing.
export const MIN_QUERY_LENGTH = 3;
export const SEARCH_LIMIT = 100;

export async function checkSchema(db: ContentDb): Promise<void> {
  const row = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version', []);
  if (row?.user_version !== SCHEMA_VERSION) {
    throw new Error(`riyad.db has schema ${row?.user_version}, but the app is written for ${SCHEMA_VERSION}`);
  }
}

export async function getInfo(db: ContentDb): Promise<Record<string, string>> {
  const rows = await db.getAllAsync<{ key: string; value: string }>('SELECT key, value FROM info', []);
  return Object.fromEntries(rows.map((row) => [row.key, row.value]));
}

export async function getHadithCount(db: ContentDb): Promise<number> {
  const row = await db.getFirstAsync<{ count: number }>('SELECT count(*) AS count FROM hadith', []);
  return row?.count ?? 0;
}

export async function getHadith(db: ContentDb, id: number): Promise<Hadith | null> {
  const row = await db.getFirstAsync<Omit<Hadith, 'pieces' | 'meanings' | 'benefits'>>(
    `SELECT h.id, h.title, h.page, h.book_id AS bookId, b.title AS book, h.chapter_id AS chapterId, c.title AS chapter
     FROM hadith h JOIN books b ON b.id = h.book_id JOIN chapters c ON c.id = h.chapter_id
     WHERE h.id = ?`,
    [id],
  );
  if (!row) return null;

  const [pieces, meanings, benefits] = await Promise.all([
    db.getAllAsync<Piece>('SELECT role, text FROM matn_pieces WHERE hadith_id = ? ORDER BY seq', [id]),
    db.getAllAsync<Meaning>('SELECT term, meaning FROM meanings WHERE hadith_id = ? ORDER BY seq', [id]),
    db.getAllAsync<{ text: string }>('SELECT text FROM benefits WHERE hadith_id = ? ORDER BY seq', [id]),
  ]);
  return { ...row, pieces, meanings, benefits: benefits.map((benefit) => benefit.text) };
}

export function listBooks(db: ContentDb): Promise<Book[]> {
  return db.getAllAsync<Book>(
    `SELECT b.id, b.title, min(h.id) AS firstHadith FROM books b JOIN hadith h ON h.book_id = b.id
     GROUP BY b.id ORDER BY b.id`,
    [],
  );
}

export function listChapters(db: ContentDb, bookId: number): Promise<Chapter[]> {
  return db.getAllAsync<Chapter>(
    `SELECT c.id, c.title, min(h.id) AS firstHadith FROM chapters c JOIN hadith h ON h.chapter_id = c.id
     WHERE c.book_id = ? GROUP BY c.id ORDER BY c.id`,
    [bookId],
  );
}

// A query of digits only opens the hadith with that number; otherwise it is simplified as the text was, and found
// anywhere in a hadith's text, even inside a word (database/README.md, "Search").
export async function search(db: ContentDb, query: string): Promise<SearchResult[]> {
  const select = `SELECT h.id, h.title, b.title AS book, c.title AS chapter
    FROM hadith h JOIN books b ON b.id = h.book_id JOIN chapters c ON c.id = h.chapter_id`;

  const trimmed = query.trim();
  // Western digits, Arabic-Indic (٠–٩) or Extended Arabic-Indic (۰–۹), which Persian and Urdu keyboards type.
  if (/^[0-9٠-٩۰-۹]+$/.test(trimmed)) {
    const id = Number(trimmed.replace(/[٠-٩۰-۹]/g, (digit) => String(digit.charCodeAt(0) % 16)));
    return db.getAllAsync<SearchResult>(`${select} WHERE h.id = ?`, [id]);
  }

  const simplified = simplify(trimmed);
  if (simplified.length < MIN_QUERY_LENGTH) return [];
  // simplify() leaves only letters and spaces, so the query can't break out of the double quotes. The limit is inside
  // the full-text query, as database/README.md has it, so a common word stops at the first matches.
  return db.getAllAsync<SearchResult>(
    `${select} WHERE h.id IN (SELECT rowid FROM hadith_search WHERE hadith_search MATCH ? ORDER BY rowid LIMIT ?)
     ORDER BY h.id`,
    [`"${simplified}"`, SEARCH_LIMIT],
  );
}
