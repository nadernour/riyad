// A noun's forms for counting it, as Arabic counts: one, two, 3 to 10 (plural), 11 to 99 (singular, accusative), and
// 100, 200… (singular). From 3 on, the form follows the number's last two digits.
export interface Counted {
  one: string;
  two: string;
  few: string;
  many: string;
  hundreds: string;
}

export const HADITH: Counted = { one: 'حديث واحد', two: 'حديثان', few: 'أحاديث', many: 'حديثًا', hundreds: 'حديث' };
export const CHAPTER: Counted = { one: 'باب واحد', two: 'بابان', few: 'أبواب', many: 'بابًا', hundreds: 'باب' };

export function count(n: number, noun: Counted): string {
  if (n === 1) return noun.one;
  if (n === 2) return noun.two;
  const lastTwo = n % 100;
  if (lastTwo >= 3 && lastTwo <= 10) return `${n} ${noun.few}`;
  if (lastTwo >= 11) return `${n} ${noun.many}`;
  return `${n} ${noun.hundreds}`;
}
