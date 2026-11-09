import { MIN_QUERY_LENGTH, simplify } from './simplify';

// Where a search matched in a text as it is shown, with its tashkeel. Search matches the simplified text, which has
// fewer characters (database/README.md, "Search"), so the text is simplified here one character at a time, keeping
// where each character came from: simplifyMapped(text).simplified is always simplify(text) (tested on every hadith).
export interface Range {
  start: number;
  end: number;
}

// Written with escapes: Arabic in a character class shows reordered, and is easily copied so.
const MARK = /[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/; // tashkeel and tatweel, as simplify() removes them
const LETTER = /[\u0621-\u064A]/;
const SALUTATION = ' صلي الله عليه وسلم '; // ﷺ written out, as simplify() writes it, with ى as ي

function normalize(char: string): string {
  if (/[أإآٱ]/.test(char)) return 'ا';
  if (char === 'ى') return 'ي';
  if (char === 'ة') return 'ه';
  return char;
}

export function simplifyMapped(text: string): { simplified: string; origin: number[] } {
  const out: string[] = [];
  const origin: number[] = [];
  const emit = (char: string, from: number) => {
    // Anything but letters is one space, and none at the start.
    if (char === ' ' && (out.length === 0 || out[out.length - 1] === ' ')) return;
    out.push(char);
    origin.push(from);
  };
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === 'ﷺ') {
      for (const written of SALUTATION) emit(written, i);
    } else if (!MARK.test(char)) {
      const normal = normalize(char);
      emit(LETTER.test(normal) ? normal : ' ', i);
    }
  }
  // None at the end either.
  if (out[out.length - 1] === ' ') {
    out.pop();
    origin.pop();
  }
  return { simplified: out.join(''), origin };
}

// Every place in the text a query matches, as search finds it: anywhere, even inside a word. A match takes in the
// marks on its last letter.
export function findMatches(text: string, query: string): Range[] {
  const wanted = simplify(query);
  if (wanted.length < MIN_QUERY_LENGTH) return [];
  const { simplified, origin } = simplifyMapped(text);
  const ranges: Range[] = [];
  for (let at = simplified.indexOf(wanted); at >= 0; at = simplified.indexOf(wanted, at + 1)) {
    const start = origin[at];
    let end = origin[at + wanted.length - 1] + 1;
    while (end < text.length && MARK.test(text[end])) end++;
    const last = ranges[ranges.length - 1];
    if (last && start <= last.end) last.end = Math.max(last.end, end);
    else ranges.push({ start, end });
  }
  return ranges;
}

// A text cut into spans, each in a match or not, for drawing the matches apart.
export function splitAt<T extends { text: string }>(
  pieces: T[],
  ranges: Range[],
): (T & { matched: boolean })[] {
  const spans: (T & { matched: boolean })[] = [];
  let offset = 0;
  for (const piece of pieces) {
    const pieceEnd = offset + piece.text.length;
    let at = offset;
    for (const range of ranges) {
      if (range.end <= at || range.start >= pieceEnd) continue;
      const start = Math.max(range.start, at);
      if (start > at) spans.push({ ...piece, text: piece.text.slice(at - offset, start - offset), matched: false });
      const end = Math.min(range.end, pieceEnd);
      spans.push({ ...piece, text: piece.text.slice(start - offset, end - offset), matched: true });
      at = end;
    }
    if (at < pieceEnd) spans.push({ ...piece, text: piece.text.slice(at - offset), matched: false });
    offset = pieceEnd;
  }
  return spans;
}

// How much of the text before the first match a search result shows, so the match has some context, and about how
// much in all: it shows two lines, and the rest needn't be laid out.
const BEFORE = 30;
const LENGTH = 200;

// The part of a text a search result shows: from a little before the first match, starting at a word, with the
// matches in it. Without a match, the text's start.
export function snippet(text: string, ranges: Range[]): { text: string; ranges: Range[] } {
  // One space for each line break, so the ranges still fit.
  const flat = text.replace(/\s/g, ' ');
  const first = ranges[0];
  let from = 0;
  if (first && first.start > BEFORE) {
    const space = flat.indexOf(' ', first.start - BEFORE);
    from = space >= 0 && space < first.start ? space + 1 : first.start;
  }
  // It ends at the end of a word, so a letter keeps its marks, and takes in the whole of a match it reaches.
  let to = flat.indexOf(' ', Math.min(flat.length, from + LENGTH));
  if (to < 0) to = flat.length;
  for (const range of ranges) if (range.start < to && range.end > to) to = range.end;
  const prefix = from > 0 ? '… ' : '';
  const shift = prefix.length - from;
  return {
    text: prefix + flat.slice(from, to),
    ranges: ranges
      .filter((range) => range.start >= from && range.start < to)
      .map((range) => ({ start: range.start + shift, end: range.end + shift })),
  };
}
