import { Text, type TextStyle } from 'react-native';

import type { Piece, Role } from '@/db/content';
import { fonts, TEXT_LINE_HEIGHT, useColors, type Colors } from '@/theme';

// How each speaker's words look. The Prophet's words, ﷺ, stand out in colour and in weight, so they show without
// colour too; Amiri has no semi-bold, so the weight is bold.
function roleStyle(role: Role, colors: Colors): TextStyle | null {
  switch (role) {
    case 'prophet':
      return { color: colors.prophet, fontFamily: fonts.textBold };
    case 'speech':
      return { color: colors.speech };
    case 'gloss':
      return { textDecorationLine: 'underline', textDecorationStyle: 'dotted' };
    default:
      return null;
  }
}

// A hadith's text: its pieces joined, in reading order, each styled by its speaker. One Text with nested spans, so it
// wraps, justifies and selects as one paragraph.
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
      }}>
      {pieces.map((piece, i) => (
        <Text key={i} style={roleStyle(piece.role, colors)}>
          {piece.text}
        </Text>
      ))}
    </Text>
  );
}
