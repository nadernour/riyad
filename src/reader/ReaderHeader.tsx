import { router } from 'expo-router';
import { DrawerToggleButton } from 'expo-router/drawer';
import { useEffect, type ReactNode } from 'react';
import { Pressable, Share, StyleSheet, View } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';

import { Icon } from '@/components/Icon';
import { Text } from '@/components/Text';
import { setBookmarked, useIsBookmarked } from '@/db/bookmarks';
import type { Hadith } from '@/db/content';
import { fonts, MAX_SCALE, useColors } from '@/theme';

import { shareText } from './shareText';

export const HEADER_HEIGHT = 56;

type Props = {
  title: string;
  // The hadith on screen, which the bookmark button marks.
  hadithId: number;
  // The same hadith, once it is read, for the share button.
  hadith: Hadith | null;
  // The phone's status bar, above the header.
  insetTop: number;
  hidden: boolean;
};

// The reader's bar: the menu, the current book's title, and the search, share and bookmark buttons. v1 shares on a
// long press, which nothing shows; v2 has a button for it. It lies over the
// pages rather than above them, so hiding it for full screen slides it away without moving the text under it.
export function ReaderHeader({ title, hadithId, hadith, insetTop, hidden }: Props) {
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
        <Text style={[styles.title, { color: colors.text }]} numberOfLines={1} maxFontSizeMultiplier={MAX_SCALE.bar}>
          {title}
        </Text>
        <HeaderButton label="البحث" onPress={() => router.navigate('/search')}>
          <Icon name="search" color={colors.text} />
        </HeaderButton>
        {/* Always there, so the bar doesn't shift while a hadith loads: until then it does nothing. */}
        <HeaderButton label="مشاركة الحديث" disabled={!hadith} onPress={() => hadith && share(hadith)}>
          <Icon name="share" color={colors.text} />
        </HeaderButton>
        <HeaderButton
          label={bookmarked ? 'إزالة من المفضلة' : 'إضافة إلى المفضلة'}
          onPress={() => setBookmarked(hadithId, !bookmarked)}>
          <Icon name={bookmarked ? 'bookmarked' : 'bookmark'} color={bookmarked ? colors.accent : colors.text} />
        </HeaderButton>
      </View>
    </Animated.View>
  );
}

// The share sheet says itself whether the hadith was shared: nothing is left for the reader to report.
function share(hadith: Hadith) {
  Share.share({ title: hadith.title, message: shareText(hadith) }).catch(() => {});
}

function HeaderButton({
  label,
  disabled = false,
  onPress,
  children,
}: {
  label: string;
  disabled?: boolean;
  onPress: () => void;
  children: ReactNode;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      hitSlop={4}
      style={styles.button}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}>
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
