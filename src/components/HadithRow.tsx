import type { ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { Marked } from '@/components/Marked';
import { Text } from '@/components/Text';
import type { HadithSummary, SearchHit } from '@/db/content';
import { fonts, useColors } from '@/theme';

type Props = {
  hadith: HadithSummary;
  onPress: () => void;
  // A button at the row's end, such as removing a bookmark.
  action?: ReactNode;
  // One line, the title only, as the side menu lists the newest bookmarks.
  compact?: boolean;
  // A search result: where the query is in the title, and an excerpt of the text with it.
  found?: Pick<SearchHit, 'titleMatches' | 'excerpt'>;
};

// A hadith in a list, as search results and bookmarks show it: its number, its short title, and where it is.
export function HadithRow({ hadith, onPress, action, compact = false, found }: Props) {
  const colors = useColors();
  const excerpt = found?.excerpt;
  return (
    <View style={[styles.row, !compact && { borderBottomWidth: StyleSheet.hairlineWidth, borderColor: colors.border }]}>
      <Pressable
        style={({ pressed }) => [styles.main, pressed && { backgroundColor: colors.surface }]}
        onPress={onPress}
        accessibilityRole="button"
        // A search result says where it matched too, as the excerpt shows it.
        accessibilityLabel={`الحديث رقم ${hadith.id}: ${hadith.title}${excerpt ? `، ${excerpt.text}` : ''}`}>
        <Text style={[styles.number, { color: colors.prophet }]}>{hadith.id}</Text>
        <View style={styles.texts}>
          <Marked
            text={hadith.title}
            ranges={found?.titleMatches ?? []}
            style={[styles.title, { color: colors.text }]}
            numberOfLines={compact ? 1 : 2}
          />
          {excerpt && (
            <Marked
              text={excerpt.text}
              ranges={excerpt.ranges}
              style={[styles.excerpt, { color: colors.text }]}
              numberOfLines={2}
            />
          )}
          {!compact && (
            <Text style={[styles.where, { color: colors.muted }]} numberOfLines={1}>
              {hadith.book}، {hadith.chapter}
            </Text>
          )}
        </View>
      </Pressable>
      {action}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center' },
  main: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 10, paddingHorizontal: 16 },
  number: { minWidth: 40, fontFamily: fonts.uiBold, fontSize: 16, textAlign: 'center' },
  texts: { flex: 1, gap: 2 },
  title: { fontFamily: fonts.text, fontSize: 19, lineHeight: 19 * 1.8, textAlign: 'left', writingDirection: 'rtl' },
  excerpt: { fontFamily: fonts.text, fontSize: 16, lineHeight: 16 * 1.8, textAlign: 'left', writingDirection: 'rtl' },
  where: { fontFamily: fonts.ui, fontSize: 13, textAlign: 'left' },
});
