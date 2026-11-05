import type { ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { Text } from '@/components/Text';
import type { HadithSummary } from '@/db/content';
import { fonts, useColors } from '@/theme';

type Props = {
  hadith: HadithSummary;
  onPress: () => void;
  // A button at the row's end, such as removing a bookmark.
  action?: ReactNode;
  // One line, the title only, as the side menu lists the newest bookmarks.
  compact?: boolean;
};

// A hadith in a list, as search results and bookmarks show it: its number, its short title, and where it is.
export function HadithRow({ hadith, onPress, action, compact = false }: Props) {
  const colors = useColors();
  return (
    <View style={[styles.row, !compact && { borderBottomWidth: StyleSheet.hairlineWidth, borderColor: colors.border }]}>
      <Pressable
        style={({ pressed }) => [styles.main, pressed && { backgroundColor: colors.surface }]}
        onPress={onPress}
        accessibilityRole="button"
        accessibilityLabel={`الحديث رقم ${hadith.id}: ${hadith.title}`}>
        <Text style={[styles.number, { color: colors.prophet }]}>{hadith.id}</Text>
        <View style={styles.texts}>
          <Text style={[styles.title, { color: colors.text }]} numberOfLines={compact ? 1 : 2}>
            {hadith.title}
          </Text>
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
  where: { fontFamily: fonts.ui, fontSize: 13, textAlign: 'left' },
});
