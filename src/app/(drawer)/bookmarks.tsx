import { Drawer } from 'expo-router/drawer';
import { ActivityIndicator, Alert, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';

import { HadithRow } from '@/components/HadithRow';
import { Icon } from '@/components/Icon';
import { removeAllBookmarks, setBookmarked, useBookmarks } from '@/db/bookmarks';
import { listHadith } from '@/db/content';
import { useQuery } from '@/db/hooks';
import { openHadith } from '@/reader/openHadith';
import { fonts, useColors } from '@/theme';

// v1 asks before removing a bookmark, and before clearing them all.
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

  const clearAll = ids.length > 0 && (
    <Pressable
      onPress={() => confirm('مسح جميع المفضلة؟', 'مسح الكل', removeAllBookmarks)}
      hitSlop={8}
      style={styles.headerButton}
      accessibilityRole="button">
      <Text style={[styles.headerButtonText, { color: colors.prophet }]}>مسح الكل</Text>
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
        <ActivityIndicator style={styles.fill} color={colors.prophet} />
      ) : list.status === 'error' ? (
        <Text style={[styles.emptyText, { color: colors.text }]}>{list.error.message}</Text>
      ) : (
        <FlatList
          data={list.value}
          keyExtractor={(hadith) => String(hadith.id)}
          renderItem={({ item }) => (
            <HadithRow
              hadith={item}
              onPress={() => openHadith(item.id)}
              action={
                <Pressable
                  onPress={() => confirm('إزالة هذا الحديث من المفضلة؟', 'إزالة', () => setBookmarked(item.id, false))}
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
});
