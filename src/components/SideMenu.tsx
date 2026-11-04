import { DrawerContentScrollView, DrawerItemList, type DrawerContentComponentProps } from 'expo-router/drawer';
import { StyleSheet, View } from 'react-native';

import { HadithRow } from '@/components/HadithRow';
import { Text } from '@/components/Text';
import { useBookmarks } from '@/db/bookmarks';
import { getHadithCount, listHadith } from '@/db/content';
import { useQuery } from '@/db/hooks';
import { openHadith } from '@/reader/openHadith';
import { count as countOf, HADITH } from '@/text/count';
import { fonts, useColors } from '@/theme';

// How many of the newest bookmarks the side menu lists, as in v1.
const LATEST = 3;

// The side menu: the app's name and hadith count, its screens, and the newest bookmarks.
export function SideMenu(props: DrawerContentComponentProps) {
  const colors = useColors();
  const count = useQuery('hadithCount', getHadithCount);
  // All of them are looked up, so a bookmark of a hadith this database doesn't have doesn't take one of the places.
  const ids = useBookmarks().map((bookmark) => bookmark.hadithId);
  const bookmarks = useQuery(`bookmarks:${ids.join(',')}`, (db) => listHadith(db, ids), { keepPrevious: true });
  const latest = bookmarks.status === 'done' ? bookmarks.value.slice(0, LATEST) : [];

  return (
    <DrawerContentScrollView {...props}>
      <View style={[styles.header, { borderColor: colors.border }]}>
        <Text style={[styles.name, { color: colors.text }]}>رياض الصالحين</Text>
        {count.status === 'done' && (
          <Text style={[styles.count, { color: colors.muted }]}>{countOf(count.value, HADITH)}</Text>
        )}
      </View>
      <DrawerItemList {...props} />
      {latest.length > 0 && (
        <View style={[styles.section, { borderColor: colors.border }]}>
          <Text style={[styles.sectionTitle, { color: colors.muted }]}>آخر المفضلة</Text>
          {latest.map((hadith) => (
            <HadithRow
              key={hadith.id}
              hadith={hadith}
              compact
              onPress={() => {
                props.navigation.closeDrawer();
                openHadith(hadith.id);
              }}
            />
          ))}
        </View>
      )}
    </DrawerContentScrollView>
  );
}

const styles = StyleSheet.create({
  header: { paddingHorizontal: 16, paddingBottom: 16, marginBottom: 8, borderBottomWidth: StyleSheet.hairlineWidth },
  name: { fontFamily: fonts.uiBold, fontSize: 22, textAlign: 'left' },
  count: { fontFamily: fonts.uiSemiBold, fontSize: 14, textAlign: 'left' },
  section: { marginTop: 8, paddingTop: 12, borderTopWidth: StyleSheet.hairlineWidth },
  sectionTitle: {
    paddingHorizontal: 16,
    paddingBottom: 4,
    fontFamily: fonts.uiSemiBold,
    fontSize: 13,
    textAlign: 'left',
  },
});
