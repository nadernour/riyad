// For tests only: Node's own SQLite behind the interfaces the app's database code takes, so tests run the app's SQL.
import type { ContentDb } from './content';
import type { UserDb } from './user';

// eslint-disable-next-line @typescript-eslint/no-require-imports
const { DatabaseSync } = require('node:sqlite') as typeof import('node:sqlite');

type Params = (string | number | null)[];

export function openContentDb(path: string): ContentDb {
  const db = new DatabaseSync(path, { readOnly: true });
  return {
    getAllAsync: async <T>(source: string, params: Params) => db.prepare(source).all(...params) as T[],
    getFirstAsync: async <T>(source: string, params: Params) => (db.prepare(source).get(...params) as T) ?? null,
  };
}

export function openUserDb(): UserDb {
  const db = new DatabaseSync(':memory:');
  return {
    execSync: (source) => db.exec(source),
    runSync: (source, params) => {
      db.prepare(source).run(...params);
    },
    getAllSync: <T>(source: string, params: Params) => db.prepare(source).all(...params) as T[],
    getFirstSync: <T>(source: string, params: Params) => (db.prepare(source).get(...params) as T) ?? null,
  };
}
