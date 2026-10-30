import { Asset } from 'expo-asset';
import * as SplashScreen from 'expo-splash-screen';
import { deleteDatabaseAsync, SQLiteProvider, type SQLiteDatabase } from 'expo-sqlite';
import type { ReactNode } from 'react';

import { checkSchema } from './content';
import { getSetting, setSetting } from './user';
import { userDb } from './userDb';

const DATABASE = require('../../database/riyad.db');

// SQLiteProvider copies the bundled database to the phone only if no file of that name is there yet. Naming the copy
// after the bundled file's hash makes a new riyad.db, in a new version of the app, a new file that is copied afresh.
const hash = Asset.fromModule(DATABASE).hash;
const NAME = hash ? `riyad-${hash.slice(0, 12)}.db` : 'riyad.db';

const PREVIOUS_KEY = 'contentDatabase';

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
      {children}
    </SQLiteProvider>
  );
}
