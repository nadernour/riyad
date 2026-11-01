import { getSetting, setSetting } from '@/db/user';
import { userDb } from '@/db/userDb';

const LAST_HADITH = 'lastHadith';

// Remembering the last hadith read is a convenience: if user.db can't be read or written, the reader opens at the
// first hadith and reads on without it, rather than failing.
export function lastHadithRead(): number {
  try {
    const last = Number(getSetting(userDb(), LAST_HADITH));
    return Number.isInteger(last) && last > 0 ? last : 1;
  } catch {
    return 1;
  }
}

export function rememberHadith(id: number) {
  try {
    setSetting(userDb(), LAST_HADITH, String(id));
  } catch {
    // As above: the reader works without it.
  }
}
