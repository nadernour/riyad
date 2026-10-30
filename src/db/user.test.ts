/**
 * @jest-environment node
 */
import { openUserDb } from './testing';
import {
  addBookmark,
  clearBookmarks,
  getSetting,
  isBookmarked,
  listBookmarks,
  migrateUserDb,
  removeBookmark,
  setSetting,
} from './user';

function freshDb() {
  const db = openUserDb();
  migrateUserDb(db);
  return db;
}

test('migrating twice changes nothing', () => {
  const db = freshDb();
  setSetting(db, 'lastHadith', '42');
  migrateUserDb(db);
  expect(getSetting(db, 'lastHadith')).toBe('42');
  expect(db.getFirstSync<{ user_version: number }>('PRAGMA user_version', [])?.user_version).toBe(1);
});

test('a migration that fails is rolled back, and can be run again once fixed', () => {
  const db = openUserDb();
  const good = 'CREATE TABLE a (x);';
  expect(() => migrateUserDb(db, [good, 'CREATE TABLE b (x); NOT SQL;'])).toThrow();
  expect(db.getFirstSync<{ user_version: number }>('PRAGMA user_version', [])?.user_version).toBe(1);
  expect(db.getFirstSync("SELECT 1 FROM sqlite_master WHERE name = 'b'", [])).toBeNull();

  migrateUserDb(db, [good, 'CREATE TABLE b (x);']);
  expect(db.getFirstSync<{ user_version: number }>('PRAGMA user_version', [])?.user_version).toBe(2);
});

test('settings', () => {
  const db = freshDb();
  expect(getSetting(db, 'fontSize')).toBeNull();
  setSetting(db, 'fontSize', '24');
  setSetting(db, 'fontSize', '26');
  expect(getSetting(db, 'fontSize')).toBe('26');
});

test('bookmarks, newest first', () => {
  const db = freshDb();
  addBookmark(db, 10, 1000);
  addBookmark(db, 5, 2000);
  addBookmark(db, 300, 3000);
  expect(listBookmarks(db).map((bookmark) => bookmark.hadithId)).toEqual([300, 5, 10]);
});

test('bookmarking a hadith twice keeps the first time', () => {
  const db = freshDb();
  addBookmark(db, 10, 1000);
  addBookmark(db, 10, 5000);
  expect(listBookmarks(db)).toEqual([{ hadithId: 10, createdAt: 1000 }]);
});

test('removing one and clearing all', () => {
  const db = freshDb();
  addBookmark(db, 1, 1);
  addBookmark(db, 2, 2);
  removeBookmark(db, 1);
  expect(isBookmarked(db, 1)).toBe(false);
  expect(isBookmarked(db, 2)).toBe(true);
  clearBookmarks(db);
  expect(listBookmarks(db)).toEqual([]);
});
