import { render, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';

import { HadithRow } from '@/components/HadithRow';
import { findMatches } from '@/search/highlight';
import { useColors } from '@/theme';

import { HadithText } from './HadithText';

const pieces = [
  { role: 'narration' as const, text: 'قَالَ رَسُولُ اللَّهِ ﷺ: ' },
  { role: 'prophet' as const, text: '«صَلَاةُ الرَّجُلِ فِي جَمَاعَةٍ، وَإِذَا دَخَلَ الْمَسْجِدَ كَانَ فِي الصَّلَاةِ»' },
];
const text = pieces.map((piece) => piece.text).join('');

async function highlightColor() {
  let color: unknown;
  function Probe() {
    color = useColors().highlight;
    return null;
  }
  await render(<Probe />);
  return color;
}

// The background of a span, nested in the text.
const background = (element: { props: { style?: unknown } }) =>
  (StyleSheet.flatten(element.props.style as never) as { backgroundColor?: string } | undefined)?.backgroundColor;

test('the reader draws each match on the highlight, in its speaker style, and nothing else', async () => {
  const color = await highlightColor();
  await render(<HadithText pieces={pieces} fontSize={24} highlight="الصلاة" />);
  const match = screen.getByText('الصَّلَاةِ');
  expect(background(match)).toBe(color);
  // Still the Prophet's words.
  expect(StyleSheet.flatten(match.props.style).fontFamily).toBe('ScheherazadeNew-Bold');
  // «صَلَاةُ» has no «ال»: not what was searched for.
  expect(background(screen.getByText(/صَلَاةُ الرَّجُلِ/))).toBeUndefined();
});

test('without a search, the text has no highlight', async () => {
  await render(<HadithText pieces={pieces} fontSize={24} />);
  expect(background(screen.getByText(/الصَّلَاةِ/))).toBeUndefined();
});

test('a search result highlights the query in its title and its excerpt', async () => {
  const color = await highlightColor();
  const title = 'صلاة الرجل في جماعة';
  await render(
    <HadithRow
      hadith={{ id: 10, title, book: 'الكتاب الأول', chapter: 'باب' }}
      found={{
        titleMatches: findMatches(title, 'صلاة'),
        excerpt: { text, ranges: findMatches(text, 'الصلاة') },
      }}
      onPress={() => {}}
    />,
  );
  expect(background(screen.getByText('صلاة'))).toBe(color);
  expect(background(screen.getByText('الصَّلَاةِ'))).toBe(color);
});
