import { router, useLocalSearchParams } from 'expo-router';
import { NavigationBar } from 'expo-navigation-bar';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { getHadithCount } from '@/db/content';
import { useHadith, useQuery } from '@/db/hooks';
import { getSetting, setSetting } from '@/db/user';
import { userDb } from '@/db/userDb';
import { HadithPage } from '@/reader/HadithPage';
import { Pager } from '@/reader/Pager';
import { HEADER_HEIGHT, ReaderHeader } from '@/reader/ReaderHeader';
import { DEFAULT_FONT_SIZE, fonts, useColors } from '@/theme';

const LAST_HADITH = 'lastHadith';

// Remembering the last hadith read is a convenience: if user.db can't be read or written, the reader opens at the
// first hadith and reads on without it, rather than failing.
function lastHadithRead(): number {
  try {
    const last = Number(getSetting(userDb(), LAST_HADITH));
    return Number.isInteger(last) && last > 0 ? last : 1;
  } catch {
    return 1;
  }
}

function rememberHadith(id: number) {
  try {
    setSetting(userDb(), LAST_HADITH, String(id));
  } catch {
    // As above: the reader works without it.
  }
}

// A hadith asked for by another screen (/?id=12).
function askedHadith(param: string | undefined): number | null {
  const id = Number(param);
  return Number.isInteger(id) && id > 0 ? id : null;
}

export default function ReaderScreen() {
  const colors = useColors();
  const params = useLocalSearchParams<{ id?: string }>();
  const count = useQuery('hadithCount', getHadithCount);

  const [requested, setRequested] = useState(() => askedHadith(params.id) ?? lastHadithRead());
  const [fullScreen, setFullScreen] = useState(false);

  // Opening a hadith from another screen while the reader is already open: a new id moves to it, during render, as
  // React has state follow a prop. The id is then cleared from the route, so asking for the same hadith again, after
  // paging away from it, is a new id too.
  const [askedFor, setAskedFor] = useState(params.id);
  if (params.id !== askedFor) {
    setAskedFor(params.id);
    const asked = askedHadith(params.id);
    if (asked) setRequested(asked);
  }
  useEffect(() => {
    if (params.id) router.setParams({ id: undefined });
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
  const title = current.status === 'done' && current.value ? current.value.book : 'رياض الصالحين';

  const toggleFullScreen = useCallback(() => setFullScreen((full) => !full), []);
  const renderPage = useCallback(
    (id: number) => (
      <HadithPage
        id={id}
        fontSize={DEFAULT_FONT_SIZE}
        insetTop={margins.top + HEADER_HEIGHT}
        insetBottom={margins.bottom}
      />
    ),
    [margins.top, margins.bottom],
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
      <Pager count={last} index={index} onIndexChange={setRequested} renderPage={renderPage} onTap={toggleFullScreen} />
      <ReaderHeader title={title} insetTop={margins.top} hidden={fullScreen} />
      <StatusBar hidden={fullScreen} animated />
      <NavigationBar hidden={fullScreen} />
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  error: { flex: 1, padding: 20, fontFamily: fonts.ui, fontSize: 16, textAlign: 'left' },
});
