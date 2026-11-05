/**
 * @jest-environment node
 */
import path from 'path';

import { getHadith } from '@/db/content';
import { openContentDb } from '@/db/testing';

import { shareText } from './shareText';

const db = openContentDb(path.join(__dirname, '../../database/riyad.db'));

test('a shared hadith has its title, its text and its number', async () => {
  const hadith = (await getHadith(db, 1))!;
  const text = shareText(hadith);
  expect(text.startsWith(`${hadith.title}\n\n`)).toBe(true);
  for (const piece of hadith.pieces) expect(text).toContain(piece.text.trim());
  expect(text.endsWith('رياض الصالحين، الحديث رقم 1')).toBe(true);
});
