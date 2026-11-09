import { useMemo } from 'react';
import type { TextProps, TextStyle } from 'react-native';

import { Text } from '@/components/Text';
import { hadithText, type Piece, type Role } from '@/db/content';
import { findMatches, splitAt } from '@/search/highlight';
import { fonts, MAX_SCALE, TEXT_LINE_HEIGHT, useColors, type Colors } from '@/theme';

// How each speaker's words look. The Prophet's words, ﷺ, stand out in colour and in weight, so they show without
// colour too. Nawawi's explanation of a word (gloss) has the colour of the other speech, with no style of its own for
// now: an underline cuts through the letters' tails and marks, and v1's roles, not yet checked (database/README.md),
// sometimes mark a whole paragraph as gloss.
function roleStyle(role: Role, colors: Colors): TextStyle | null {
  switch (role) {
    case 'prophet':
      return { color: colors.prophet, fontFamily: fonts.textBold };
    case 'speech':
    case 'gloss':
      return { color: colors.speech };
    default:
      return null;
  }
}

// A hadith's text: its pieces joined, in reading order, each styled by its speaker. One Text with nested spans, so it
// wraps, justifies and selects as one paragraph. Its writing direction is set, not left to iOS: iOS lays out a
// justified paragraph's last line by the device's language, not the text's, so on an English iPhone it went left.
export function HadithText({
  pieces,
  fontSize,
  highlight,
  ...props
}: {
  pieces: Piece[];
  fontSize: number;
  // A search query: where it is in the text is drawn on a highlight.
  highlight?: string;
} & Pick<TextProps, 'accessibilityActions' | 'onAccessibilityAction'>) {
  const colors = useColors();
  // Worked out once for the text and query, not again at each render, such as a change of font size.
  const spans = useMemo(
    () =>
      highlight
        ? splitAt(pieces, findMatches(hadithText(pieces), highlight))
        : pieces.map((piece) => ({ ...piece, matched: false })),
    [pieces, highlight],
  );
  return (
    <Text
      {...props}
      maxFontSizeMultiplier={MAX_SCALE.reader}
      style={{
        color: colors.text,
        fontFamily: fonts.text,
        fontSize,
        lineHeight: fontSize * TEXT_LINE_HEIGHT,
        textAlign: 'justify',
        writingDirection: 'rtl',
      }}>
      {spans.map((span, i) => (
        // Each span has the limit too: a span's own limit, the app's Text's 1.5 by default, overrides its paragraph's.
        <Text
          key={i}
          style={[roleStyle(span.role, colors), span.matched && { backgroundColor: colors.highlight }]}
          maxFontSizeMultiplier={MAX_SCALE.reader}>
          {span.text}
        </Text>
      ))}
    </Text>
  );
}
