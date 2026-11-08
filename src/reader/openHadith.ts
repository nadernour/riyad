import { router } from 'expo-router';

// Opens the reader at a hadith, from any screen (src/app/(drawer)/index.tsx reads the id). From search, the query
// goes too, and the reader highlights where it is in the hadith.
export function openHadith(id: number, query?: string) {
  router.navigate({ pathname: '/', params: query ? { id: String(id), q: query } : { id: String(id) } });
}
