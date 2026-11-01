import { router } from 'expo-router';

// Opens the reader at a hadith, from any screen (src/app/(drawer)/index.tsx reads the id).
export function openHadith(id: number) {
  router.navigate({ pathname: '/', params: { id: String(id) } });
}
