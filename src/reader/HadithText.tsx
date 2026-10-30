import { Text, type TextStyle } from 'react-native';

import type { Piece, Role } from '@/db/content';
import { fonts, TEXT_LINE_HEIGHT, useColors, type Colors } from '@/theme';

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
export function HadithText({ pieces, fontSize }: { pieces: Piece[]; fontSize: number }) {
  const colors = useColors();
  return (
    <Text
      style={{
        color: colors.text,
        fontFamily: fonts.text,
        fontSize,
        lineHeight: fontSize * TEXT_LINE_HEIGHT,
        textAlign: 'justify',
        writingDirection: 'rtl',
      }}>
      {pieces.map((piece, i) => (
        <Text key={i} style={roleStyle(piece.role, colors)}>
          {piece.text}
        </Text>
      ))}
    </Text>
  );
}
