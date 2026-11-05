import type { Hadith } from '@/db/content';

// A hadith as it is shared: its short title, its text, and where it is in the book, which v1 left out.
export function shareText(hadith: Hadith): string {
  const text = hadith.pieces.map((piece) => piece.text).join('');
  return `${hadith.title}\n\n${text.trim()}\n\nرياض الصالحين، الحديث رقم ${hadith.id}`;
}
