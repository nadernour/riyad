import { router } from 'expo-router';
import { DrawerToggleButton } from 'expo-router/drawer';
import { useEffect, type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';

import { Icon } from '@/components/Icon';
import { setBookmarked, useIsBookmarked } from '@/db/bookmarks';
import { fonts, useColors } from '@/theme';

export const HEADER_HEIGHT = 56;

type Props = {
  title: string;
  // The hadith on screen, which the bookmark button marks.
  hadithId: number;
  // The phone's status bar, above the header.
  insetTop: number;
  hidden: boolean;
};

// The reader's bar: the menu, the current book's title, and the search and bookmark buttons, as in v1. It lies over the
// pages rather than above them, so hiding it for full screen slides it away without moving the text under it.
export function ReaderHeader({ title, hadithId, insetTop, hidden }: Props) {
  const colors = useColors();
  const bookmarked = useIsBookmarked(hadithId);
  const height = insetTop + HEADER_HEIGHT;
  const offset = useSharedValue(0);

  useEffect(() => {
    offset.set(withTiming(hidden ? -height : 0, { duration: 200 }));
  }, [hidden, height, offset]);

  const style = useAnimatedStyle(() => ({ transform: [{ translateY: offset.get() }] }));

  return (
    <Animated.View
      style={[
        styles.header,
        { height, paddingTop: insetTop, backgroundColor: colors.background, borderColor: colors.border },
        style,
      ]}>
      <View style={styles.row}>
        <DrawerToggleButton tintColor={colors.text} accessibilityLabel="القائمة" />
        <Text style={[styles.title, { color: colors.text }]} numberOfLines={1}>
          {title}
        </Text>
        <HeaderButton label="البحث" onPress={() => router.navigate('/search')}>
          <Icon name="search" color={colors.text} />
        </HeaderButton>
        <HeaderButton
          label={bookmarked ? 'إزالة من المفضلة' : 'إضافة إلى المفضلة'}
          onPress={() => setBookmarked(hadithId, !bookmarked)}>
          <Icon name={bookmarked ? 'bookmarked' : 'bookmark'} color={bookmarked ? colors.prophet : colors.text} />
        </HeaderButton>
      </View>
    </Animated.View>
  );
}

function HeaderButton({ label, onPress, children }: { label: string; onPress: () => void; children: ReactNode }) {
  return (
    <Pressable onPress={onPress} hitSlop={4} style={styles.button} accessibilityRole="button" accessibilityLabel={label}>
      {children}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: { padding: 8 },
  header: { position: 'absolute', top: 0, left: 0, right: 0, borderBottomWidth: StyleSheet.hairlineWidth },
  row: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 8 },
  title: { flex: 1, fontFamily: fonts.uiBold, fontSize: 18, textAlign: 'left' },
});
