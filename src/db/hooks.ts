import { useSQLiteContext } from 'expo-sqlite';
import { useEffect, useRef, useState } from 'react';

import { getHadith, type ContentDb, type Hadith } from './content';

export function useContentDb(): ContentDb {
  return useSQLiteContext();
}

export type Loaded<T> = { status: 'loading' } | { status: 'done'; value: T } | { status: 'error'; error: Error };

// Runs a query on riyad.db, again whenever `key` changes: the key names what the query reads, such as `hadith:12`.
// The result is kept with the key it's for, so a new key shows as loading until its own result comes, and a result
// that comes after the key changed, or after the screen closed, is dropped.
export function useQuery<T>(key: string, query: (db: ContentDb) => Promise<T>): Loaded<T> {
  const db = useContentDb();
  const latest = useRef(query);
  const [result, setResult] = useState<{ key: string; state: Loaded<T> } | null>(null);

  useEffect(() => {
    latest.current = query;
  });

  useEffect(() => {
    let current = true;
    latest.current(db).then(
      (value) => current && setResult({ key, state: { status: 'done', value } }),
      (error: Error) => current && setResult({ key, state: { status: 'error', error } }),
    );
    return () => {
      current = false;
    };
  }, [db, key]);

  return result?.key === key ? result.state : { status: 'loading' };
}

export function useHadith(id: number): Loaded<Hadith | null> {
  return useQuery(`hadith:${id}`, (db) => getHadith(db, id));
}
