import { useIsFocused } from 'expo-router';
import { Drawer } from 'expo-router/drawer';
import { useEffect, useState } from 'react';
import { AccessibilityInfo, ActivityIndicator, Alert, FlatList, Pressable, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ErrorView } from '@/components/ErrorView';
import { HadithRow } from '@/components/HadithRow';
import { Icon } from '@/components/Icon';
import { Text } from '@/components/Text';
import { removeAllBookmarks, restoreBookmark, setBookmarked, useBookmarks } from '@/db/bookmarks';
import { listHadith } from '@/db/content';
import { useQuery } from '@/db/hooks';
import type { Bookmark } from '@/db/user';
import { openHadith } from '@/reader/openHadith';
import { fonts, useColors } from '@/theme';

// How long «تراجع» is offered after a bookmark is removed.
const UNDO_MS = 6000;

// Clearing them all asks first, as v1 does. One bookmark is removed at once, with «تراجع» to put it back, where v1
// asks first.
function confirm(message: string, action: string, onConfirm: () => void) {
  Alert.alert(message, undefined, [
    { text: 'إلغاء', style: 'cancel' },
    { text: action, style: 'destructive', onPress: onConfirm },
  ]);
}

// The bookmarked hadith, newest first.
export default function BookmarksScreen() {
  const colors = useColors();
  const bookmarks = useBookmarks();
  const ids = bookmarks.map((bookmark) => bookmark.hadithId);
  // Kept on screen while a removal reloads it, so the list doesn't jump back to the top.
  const list = useQuery(`bookmarks:${ids.join(',')}`, (db) => listHadith(db, ids), { keepPrevious: true });
  // A bookmark of a hadith this database doesn't have isn't listed; «مسح الكل» still clears it.
  const empty = ids.length === 0 || (list.status === 'done' && !list.stale && list.value.length === 0);

  // The bookmark last removed, while it can be put back: until the time is up, the next removal, or the screen closes.
  // With a screen reader on, the time doesn't run out: it may take longer to reach the button.
  const [removed, setRemoved] = useState<Bookmark | null>(null);
  const focused = useIsFocused();
  if (!focused && removed) setRemoved(null);
  useEffect(() => {
    if (!removed) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let current = true;
    AccessibilityInfo.isScreenReaderEnabled().then((on) => {
      if (current && !on) timer = setTimeout(() => setRemoved(null), UNDO_MS);
    });
    return () => {
      current = false;
      clearTimeout(timer);
    };
  }, [removed]);
  const remove = (hadithId: number) => {
    const bookmark = bookmarks.find((b) => b.hadithId === hadithId);
    if (!bookmark) return;
    setBookmarked(hadithId, false);
    setRemoved(bookmark);
    AccessibilityInfo.announceForAccessibility(`أزيل الحديث رقم ${hadithId} من المفضلة`);
  };
  const undo = () => {
    if (removed) restoreBookmark(removed);
    setRemoved(null);
  };

  const clearAll = ids.length > 0 && (
    <Pressable
      onPress={() =>
        confirm('مسح جميع المفضلة؟', 'مسح الكل', () => {
          removeAllBookmarks();
          setRemoved(null);
        })
      }
      hitSlop={8}
      style={styles.headerButton}
      accessibilityRole="button">
      <Text style={[styles.headerButtonText, { color: colors.accent }]}>مسح الكل</Text>
    </Pressable>
  );

  return (
    <View style={[styles.fill, { backgroundColor: colors.background }]}>
      <Drawer.Screen options={{ headerRight: () => clearAll }} />
      {empty ? (
        <View style={styles.empty}>
          <Icon name="bookmarks" color={colors.muted} size={48} />
          <Text style={[styles.emptyTitle, { color: colors.text }]}>لا توجد أحاديث في المفضلة</Text>
          <Text style={[styles.emptyText, { color: colors.muted }]}>
            اضغط على علامة المفضلة أعلى صفحة الحديث لإضافته هنا
          </Text>
        </View>
      ) : list.status === 'loading' ? (
        <ActivityIndicator style={styles.fill} color={colors.accent} />
      ) : list.status === 'error' ? (
        <ErrorView error={list.error} onRetry={list.retry} />
      ) : (
        <FlatList
          data={list.value}
          // Room under the last row for the undo bar, so it doesn't cover that row's button.
          contentContainerStyle={removed && styles.roomForUndo}
          keyExtractor={(hadith) => String(hadith.id)}
          renderItem={({ item }) => (
            <HadithRow
              hadith={item}
              onPress={() => openHadith(item.id)}
              action={
                <Pressable
                  onPress={() => remove(item.id)}
                  hitSlop={8}
                  style={styles.remove}
                  accessibilityRole="button"
                  accessibilityLabel={`إزالة الحديث رقم ${item.id} من المفضلة`}>
                  <Icon name="remove" color={colors.muted} size={22} />
                </Pressable>
              }
            />
          )}
        />
      )}
      {removed && <UndoBar hadithId={removed.hadithId} onUndo={undo} />}
    </View>
  );
}

function UndoBar({ hadithId, onUndo }: { hadithId: number; onUndo: () => void }) {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.undoBar, { backgroundColor: colors.text, marginBottom: insets.bottom + 12 }]}>
      <Text style={[styles.undoText, { color: colors.background }]}>أزيل الحديث رقم {hadithId} من المفضلة</Text>
      <Pressable onPress={onUndo} hitSlop={8} accessibilityRole="button" accessibilityLabel="تراجع عن الإزالة">
        <Text style={[styles.undoButton, { color: colors.background }]}>تراجع</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, padding: 32 },
  emptyTitle: { fontFamily: fonts.uiBold, fontSize: 18, textAlign: 'center' },
  emptyText: { fontFamily: fonts.ui, fontSize: 15, textAlign: 'center', padding: 16 },
  headerButton: { paddingHorizontal: 16 },
  headerButtonText: { fontFamily: fonts.uiSemiBold, fontSize: 15 },
  remove: { padding: 16 },
  roomForUndo: { paddingBottom: 96 },
  undoBar: {
    position: 'absolute',
    bottom: 0,
    left: 16,
    right: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
  },
  undoText: { flex: 1, fontFamily: fonts.ui, fontSize: 15, textAlign: 'left' },
  undoButton: { fontFamily: fonts.uiBold, fontSize: 15 },
});
