import { openDatabaseSync, type SQLiteDatabase } from 'expo-sqlite';

import { migrateUserDb } from './user';

let db: SQLiteDatabase | null = null;

// user.db, opened and brought up to date the first time it's needed. Its queries are small, so they run synchronously.
// It is kept only once its migrations succeed, so a failed one is tried again on the next call, not skipped.
export function userDb(): SQLiteDatabase {
  if (!db) {
    const opened = openDatabaseSync('user.db');
    try {
      migrateUserDb(opened);
    } catch (error) {
      opened.closeSync();
      throw error;
    }
    db = opened;
  }
  return db;
}
