// The same steps as simplify() in book_data/tools/arabic.py, which builds hadith.search_text: a query must be simplified
// exactly as the text was. database/simplify.json has the test cases both must pass (database/README.md, "Search").
export function simplify(text: string): string {
  return text
    .replace(/ﷺ/g, ' صلى الله عليه وسلم ') // the salutation ﷺ, written out
    .replace(/[ؐ-ًؚ-ٰٟۖ-ۭـ]/g, '') // tashkeel and tatweel
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .replace(/[^ء-ي]+/g, ' ') // anything else but letters: one space
    .trim();
}
