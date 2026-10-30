import { DrawerToggleButton } from 'expo-router/drawer';
import { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';

import { fonts, useColors } from '@/theme';

export const HEADER_HEIGHT = 56;

type Props = {
  title: string;
  // The phone's status bar, above the header.
  insetTop: number;
  hidden: boolean;
};

// The reader's bar: the menu and the current book's title, as in v1. It lies over the pages rather than above them, so
// hiding it for full screen slides it away without moving the text under it.
export function ReaderHeader({ title, insetTop, hidden }: Props) {
  const colors = useColors();
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
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  header: { position: 'absolute', top: 0, left: 0, right: 0, borderBottomWidth: StyleSheet.hairlineWidth },
  row: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 8 },
  title: { flex: 1, fontFamily: fonts.uiBold, fontSize: 18, textAlign: 'left' },
});
