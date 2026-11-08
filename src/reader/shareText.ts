import { hadithText, type Hadith } from '@/db/content';

// A hadith as it is shared: its short title, its text, and where it is in the book, which v1 left out.
export function shareText(hadith: Hadith): string {
  const text = hadithText(hadith.pieces);
  return `${hadith.title}\n\n${text.trim()}\n\nرياض الصالحين، الحديث رقم ${hadith.id}`;
}
