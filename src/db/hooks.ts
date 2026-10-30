import { useSQLiteContext } from 'expo-sqlite';
import { useEffect, useRef, useState } from 'react';

import { getHadith, type ContentDb, type Hadith } from './content';

export function useContentDb(): ContentDb {
  return useSQLiteContext();
}

export type Loaded<T> = { status: 'loading' } | { status: 'done'; value: T } | { status: 'error'; error: Error };

// Runs a query on riyad.db, again whenever `key` changes: the key names what the query reads, such as `hadith:12`.
// The result is kept with the key it's for, so a new key shows as loading until its own result comes, and a result
// that comes after the key changed, or after the screen closed, is dropped. A `cached` value is shown as it is, with
// no query and no second render.
export function useQuery<T>(key: string, query: (db: ContentDb) => Promise<T>, cached?: T): Loaded<T> {
  const db = useContentDb();
  const latest = useRef(query);
  const [result, setResult] = useState<{ key: string; state: Loaded<T> } | null>(null);
  const isCached = cached !== undefined;

  useEffect(() => {
    latest.current = query;
  });

  useEffect(() => {
    if (isCached) return;
    let current = true;
    latest.current(db).then(
      (value) => current && setResult({ key, state: { status: 'done', value } }),
      (error: Error) => current && setResult({ key, state: { status: 'error', error } }),
    );
    return () => {
      current = false;
    };
  }, [db, key, isCached]);

  if (isCached) return { status: 'done', value: cached };
  return result?.key === key ? result.state : { status: 'loading' };
}

// The hadith read most recently, so that paging back, or a second screen showing the same hadith, needs no query.
// A Map keeps insertion order, so moving a hadith to the end when it's read makes the first one the least recent.
const CACHE_SIZE = 30;
const loaded = new Map<number, Hadith>();
// Loads under way, so that two screens asking for the same hadith at once share one load.
const pending = new Map<number, Promise<Hadith | null>>();

function cachedHadith(id: number): Hadith | undefined {
  const hadith = loaded.get(id);
  if (hadith) {
    loaded.delete(id);
    loaded.set(id, hadith);
  }
  return hadith;
}

function loadHadith(db: ContentDb, id: number): Promise<Hadith | null> {
  const hadith = cachedHadith(id);
  if (hadith) return Promise.resolve(hadith);
  let load = pending.get(id);
  if (!load) {
    load = getHadith(db, id).finally(() => pending.delete(id));
    load.then((value) => {
      if (!value) return;
      loaded.set(id, value);
      if (loaded.size > CACHE_SIZE) loaded.delete(loaded.keys().next().value!);
    }, () => {});
    pending.set(id, load);
  }
  return load;
}

export function useHadith(id: number): Loaded<Hadith | null> {
  return useQuery(`hadith:${id}`, (db) => loadHadith(db, id), cachedHadith(id));
}
