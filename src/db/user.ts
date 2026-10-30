// The user's own data: bookmarks and settings (the last hadith read, font size, theme). It lives in its own database,
// user.db, so a new riyad.db never touches it. Bookmarks store the book's hadith numbers, which never change.
export interface UserDb {
  execSync(source: string): void;
  runSync(source: string, params: (string | number | null)[]): void;
  getAllSync<T>(source: string, params: (string | number | null)[]): T[];
  getFirstSync<T>(source: string, params: (string | number | null)[]): T | null;
}

export interface Bookmark {
  hadithId: number;
  createdAt: number;
}

// Each migration takes user.db from the version before it to its own place in the list (PRAGMA user_version). Only
// ever add to the end: a released migration must never change, since phones have already run it.
const MIGRATIONS = [
  `CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
   CREATE TABLE bookmarks (hadith_id INTEGER PRIMARY KEY, created_at INTEGER NOT NULL);`,
];

// Each migration runs in its own transaction, so one that fails leaves user.db as the one before left it.
export function migrateUserDb(db: UserDb, migrations = MIGRATIONS): void {
  const version = db.getFirstSync<{ user_version: number }>('PRAGMA user_version', [])?.user_version ?? 0;
  for (let next = version + 1; next <= migrations.length; next++) {
    try {
      db.execSync(`BEGIN; ${migrations[next - 1]} PRAGMA user_version = ${next}; COMMIT;`);
    } catch (error) {
      try {
        db.execSync('ROLLBACK');
      } catch {
        // There was no transaction left to roll back.
      }
      throw error;
    }
  }
}

export function getSetting(db: UserDb, key: string): string | null {
  return db.getFirstSync<{ value: string }>('SELECT value FROM settings WHERE key = ?', [key])?.value ?? null;
}

export function setSetting(db: UserDb, key: string, value: string): void {
  db.runSync('INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET value = excluded.value', [
    key,
    value,
  ]);
}

// Newest first, as v1 lists them.
export function listBookmarks(db: UserDb): Bookmark[] {
  return db.getAllSync<Bookmark>(
    'SELECT hadith_id AS hadithId, created_at AS createdAt FROM bookmarks ORDER BY created_at DESC, hadith_id DESC',
    [],
  );
}

export function isBookmarked(db: UserDb, hadithId: number): boolean {
  return db.getFirstSync('SELECT 1 FROM bookmarks WHERE hadith_id = ?', [hadithId]) !== null;
}

export function addBookmark(db: UserDb, hadithId: number, now = Date.now()): void {
  db.runSync('INSERT OR IGNORE INTO bookmarks (hadith_id, created_at) VALUES (?, ?)', [hadithId, now]);
}

export function removeBookmark(db: UserDb, hadithId: number): void {
  db.runSync('DELETE FROM bookmarks WHERE hadith_id = ?', [hadithId]);
}

export function clearBookmarks(db: UserDb): void {
  db.runSync('DELETE FROM bookmarks', []);
}
