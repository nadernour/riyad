import { findMatches, snippet, type Range } from '@/search/highlight';
import { MIN_QUERY_LENGTH, simplify } from '@/search/simplify';

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
  chapterCount: number;
}

export interface Chapter {
  id: number;
  title: string;
  firstHadith: number;
}

// A hadith's text: its pieces joined in reading order (database/README.md). Search's highlights are positions in it, so
// everything that shows or matches the text joins it here.
export function hadithText(pieces: { text: string }[]): string {
  return pieces.map((piece) => piece.text).join('');
}

// A hadith as a list shows it: search results and bookmarks.
export interface HadithSummary {
  id: number;
  title: string;
  book: string;
  chapter: string;
}

export { MIN_QUERY_LENGTH } from '@/search/simplify';
// How many results search shows at first, and how many more each «عرض المزيد» adds.
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
    `SELECT b.id, b.title, min(h.id) AS firstHadith, count(DISTINCT h.chapter_id) AS chapterCount
     FROM books b JOIN hadith h ON h.book_id = b.id GROUP BY b.id ORDER BY b.id`,
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

const SUMMARY = `SELECT h.id, h.title, b.title AS book, c.title AS chapter
  FROM hadith h JOIN books b ON b.id = h.book_id JOIN chapters c ON c.id = h.chapter_id`;

// The hadith with these numbers, in the order given; a number with no hadith is left out.
export async function listHadith(db: ContentDb, ids: number[]): Promise<HadithSummary[]> {
  if (ids.length === 0) return [];
  const rows = await db.getAllAsync<HadithSummary>(`${SUMMARY} WHERE h.id IN (${ids.map(() => '?').join(', ')})`, ids);
  const byId = new Map(rows.map((row) => [row.id, row]));
  return ids.flatMap((id) => byId.get(id) ?? []);
}

// The number a query of digits only asks for: Western digits, Arabic-Indic (٠–٩) or Extended Arabic-Indic (۰–۹), which
// Persian and Urdu keyboards type.
export function hadithNumber(query: string): number | null {
  const trimmed = query.trim();
  if (!/^[0-9٠-٩۰-۹]+$/.test(trimmed)) return null;
  return Number(trimmed.replace(/[٠-٩۰-۹]/g, (digit) => String(digit.charCodeAt(0) % 16)));
}

// A search result: the hadith, and where the query is in its title and in an excerpt of its text, worked out once
// per search rather than at each render of the list.
export interface SearchHit extends HadithSummary {
  titleMatches: Range[];
  excerpt: { text: string; ranges: Range[] };
}

// The order of the results: the closest matches first (FTS5's bm25 rank: more of the query, in a shorter text, comes
// first), or the book's order.
export type SearchOrder = 'relevance' | 'book';

// Each order, as SQL, for the full-text match and for the results from it: `hit` is the matched hadith's number.
const ORDER: Record<SearchOrder, string> = { relevance: 'rank, hit', book: 'hit' };

export interface SearchResults {
  // The query these are the results of, which can be behind the one being typed.
  query: string;
  hadith: SearchHit[];
  // More hadith match than the limit asked for: these are the first.
  more: boolean;
}

// A query of digits only opens the hadith with that number; otherwise it is simplified as the text was, and found
// anywhere in a hadith's text, even inside a word (database/README.md, "Search"). It returns the first `limit` matches.
export async function search(
  db: ContentDb,
  query: string,
  order: SearchOrder,
  limit = SEARCH_LIMIT,
): Promise<SearchResults> {
  const id = hadithNumber(query);
  if (id !== null) {
    const hadith = await db.getAllAsync<HadithSummary>(`${SUMMARY} WHERE h.id = ?`, [id]);
    return { query, hadith: await withMatches(db, hadith, null), more: false };
  }

  const simplified = simplify(query);
  if (simplified.length < MIN_QUERY_LENGTH) return { query, hadith: [], more: false };
  // simplify() leaves only letters and spaces, so the query can't break out of the double quotes. The limit is inside
  // the full-text query, as database/README.md has it: in the book's order a common word stops at the first matches,
  // while the closest first has to rank every match before it keeps the first (all 1,898 hadith at most, which
  // SQLite ranks in milliseconds). One more than shown tells whether there are more.
  const hadith = await db.getAllAsync<HadithSummary>(
    `WITH found AS (
       SELECT rowid AS hit, rank FROM hadith_search WHERE hadith_search MATCH ? ORDER BY ${ORDER[order]} LIMIT ?
     )
     ${SUMMARY} JOIN found ON found.hit = h.id
     ORDER BY ${ORDER[order]}`,
    [`"${simplified}"`, limit + 1],
  );
  return {
    query,
    hadith: await withMatches(db, hadith.slice(0, limit), query),
    more: hadith.length > limit,
  };
}

// Where the query is in each hadith's title and text, as the reader shows them; a number has no matches, and shows
// the text's start.
async function withMatches(db: ContentDb, hadith: HadithSummary[], query: string | null): Promise<SearchHit[]> {
  if (hadith.length === 0) return [];
  const pieces = await db.getAllAsync<{ id: number; text: string }>(
    `SELECT hadith_id AS id, text FROM matn_pieces WHERE hadith_id IN (${hadith.map(() => '?').join(', ')})
     ORDER BY hadith_id, seq`,
    hadith.map((h) => h.id),
  );
  const byHadith = new Map<number, { text: string }[]>();
  for (const piece of pieces) byHadith.set(piece.id, [...(byHadith.get(piece.id) ?? []), piece]);
  return hadith.map((h) => {
    const text = hadithText(byHadith.get(h.id) ?? []);
    return {
      ...h,
      titleMatches: query ? findMatches(h.title, query) : [],
      excerpt: snippet(text, query ? findMatches(text, query) : []),
    };
  });
}
