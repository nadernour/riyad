import { Asset } from 'expo-asset';
import * as SplashScreen from 'expo-splash-screen';
import { deleteDatabaseAsync, SQLiteProvider, useSQLiteContext, type SQLiteDatabase } from 'expo-sqlite';
import { createContext, use, useMemo, type ReactNode } from 'react';

import { checkSchema } from './content';
import { getSetting, setSetting } from './user';
import { userDb } from './userDb';

const DATABASE = require('../../database/riyad.db');

// SQLiteProvider copies the bundled database to the phone only if no file of that name is there yet. Naming the copy
// after the bundled file's hash makes a new riyad.db, in a new version of the app, a new file that is copied afresh.
const hash = Asset.fromModule(DATABASE).hash;
const NAME = hash ? `riyad-${hash.slice(0, 12)}.db` : 'riyad.db';

const PREVIOUS_KEY = 'contentDatabase';

// The open database's `info` table (database/README.md), read once it is open.
const Info = createContext<Record<string, string>>({});

function InfoProvider({ children }: { children: ReactNode }) {
  const db = useSQLiteContext();
  const info = useMemo(() => {
    const rows = db.getAllSync<{ key: string; value: string }>('SELECT key, value FROM info');
    return Object.fromEntries(rows.map((row) => [row.key, row.value]));
  }, [db]);
  return <Info value={info}>{children}</Info>;
}

// Whether the database is a test build's, with v1's commentary in place of the book's (scripts/build-preview-db.js):
// the app says so wherever it shows that commentary.
export function usePreviewCommentary(): boolean {
  return use(Info).preview === 'v1-commentary';
}

async function init(db: SQLiteDatabase) {
  await checkSchema(db);
  const previous = getSetting(userDb(), PREVIOUS_KEY);
  if (previous && previous !== NAME) await deleteDatabaseAsync(previous).catch(() => {});
  setSetting(userDb(), PREVIOUS_KEY, NAME);
}

export function ContentProvider({ children }: { children: ReactNode }) {
  return (
    <SQLiteProvider
      databaseName={NAME}
      // Without a hash there's no telling whether the copy on the phone is current, so it is replaced each launch.
      assetSource={{ assetId: DATABASE, forceOverwrite: !hash }}
      onInit={init}
      onError={(error) => {
        // The children, which hide the splash screen, never render: hide it here, so the error can show.
        SplashScreen.hideAsync();
        throw error;
      }}>
      <InfoProvider>{children}</InfoProvider>
    </SQLiteProvider>
  );
}
