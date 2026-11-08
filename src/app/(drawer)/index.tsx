import { router, useLocalSearchParams } from 'expo-router';
import { NavigationBar } from 'expo-navigation-bar';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, ActivityIndicator, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Text } from '@/components/Text';
import { getHadithCount } from '@/db/content';
import { useHadith, useQuery } from '@/db/hooks';
import { useFontSize } from '@/db/settings';
import { HadithPage } from '@/reader/HadithPage';
import { rememberHadith } from '@/reader/lastHadith';
import { Pager } from '@/reader/Pager';
import { useReaderPosition } from '@/reader/readerPosition';
import { HEADER_HEIGHT, ReaderHeader } from '@/reader/ReaderHeader';
import { fonts, useColors } from '@/theme';

export default function ReaderScreen() {
  const colors = useColors();
  const params = useLocalSearchParams<{ id?: string; q?: string }>();
  const count = useQuery('hadithCount', getHadithCount);
  const fontSize = useFontSize();

  const { requested, highlight, turnTo } = useReaderPosition(params);
  const [fullScreen, setFullScreen] = useState(false);

  useEffect(() => {
    if (params.id) router.setParams({ id: undefined, q: undefined });
  }, [params.id]);

  // The phone's bars change the safe-area insets when they hide for full screen. The pages and header keep the
  // largest insets seen, so full screen slides the header away without moving the text.
  const insets = useSafeAreaInsets();
  const [margins, setMargins] = useState({ top: insets.top, bottom: insets.bottom });
  if (insets.top > margins.top || insets.bottom > margins.bottom) {
    setMargins({ top: Math.max(insets.top, margins.top), bottom: Math.max(insets.bottom, margins.bottom) });
  }

  // A hadith number past the last one (an old link, or a position saved with a larger database) opens the last.
  const last = count.status === 'done' ? count.value : null;
  const index = last ? Math.min(requested, last) : requested;

  useEffect(() => {
    if (last) rememberHadith(index);
  }, [index, last]);

  const current = useHadith(index);
  const hadith = current.status === 'done' ? current.value : null;
  const title = hadith ? hadith.book : 'رياض الصالحين';

  const toggleFullScreen = useCallback(() => setFullScreen((full) => !full), []);
  // A screen reader's turn: it moves without the swipe's animation, and says where it is now. It reads the index
  // through a ref, so that it doesn't change, and re-render every page, at each turn.
  const shown = useRef(index);
  useEffect(() => {
    shown.current = index;
  }, [index]);
  const turn = useCallback(
    (step: 1 | -1) => {
      if (!last) return;
      const next = Math.min(Math.max(shown.current + step, 1), last);
      if (next === shown.current) return;
      // Set at once, so a second turn before the render goes on from this one.
      shown.current = next;
      turnTo(next);
      AccessibilityInfo.announceForAccessibility(`الحديث رقم ${next}`);
    },
    [last, turnTo],
  );
  const renderPage = useCallback(
    (id: number) => (
      <HadithPage
        id={id}
        fontSize={fontSize}
        insetTop={margins.top + HEADER_HEIGHT}
        insetBottom={margins.bottom}
        onTurn={turn}
        highlight={highlight?.id === id ? highlight.query : undefined}
      />
    ),
    [fontSize, margins.top, margins.bottom, turn, highlight],
  );

  if (count.status === 'error') {
    return (
      <Text style={[styles.error, { color: colors.text, backgroundColor: colors.background, paddingTop: margins.top }]}>
        {count.error.message}
      </Text>
    );
  }
  if (!last) {
    return <ActivityIndicator style={[styles.fill, { backgroundColor: colors.background }]} color={colors.prophet} />;
  }

  return (
    <View style={[styles.fill, { backgroundColor: colors.background }]}>
      <Pager count={last} index={index} onIndexChange={turnTo} renderPage={renderPage} onTap={toggleFullScreen} />
      <ReaderHeader title={title} hadithId={index} hadith={hadith} insetTop={margins.top} hidden={fullScreen} />
      <StatusBar hidden={fullScreen} animated />
      <NavigationBar hidden={fullScreen} />
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  error: { flex: 1, padding: 20, fontFamily: fonts.ui, fontSize: 16, textAlign: 'left' },
});
