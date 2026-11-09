import type { StyleProp, TextStyle } from 'react-native';

import { Text } from '@/components/Text';
import { splitAt, type Range } from '@/search/highlight';
import { useColors } from '@/theme';

// A line of text with the parts a search found drawn on a highlight, as search results show a hadith's title and text.
export function Marked({
  text,
  ranges,
  style,
  numberOfLines,
}: {
  text: string;
  ranges: Range[];
  style?: StyleProp<TextStyle>;
  numberOfLines?: number;
}) {
  const colors = useColors();
  return (
    <Text style={style} numberOfLines={numberOfLines}>
      {splitAt([{ text }], ranges).map((span, i) => (
        <Text key={i} style={span.matched && { backgroundColor: colors.highlight }}>
          {span.text}
        </Text>
      ))}
    </Text>
  );
}
