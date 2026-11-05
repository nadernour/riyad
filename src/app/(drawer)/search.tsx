import { useIsFocused } from 'expo-router';
import { useDrawerProgress } from 'expo-router/drawer';
import { useCallback, useEffect, useRef, useState, type ComponentRef } from 'react';
import { FlatList, Pressable, StyleSheet, TextInput, View } from 'react-native';
import { useAnimatedReaction } from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';

import { HadithRow } from '@/components/HadithRow';
import { Icon } from '@/components/Icon';
import { Text } from '@/components/Text';
import { hadithNumber, MIN_QUERY_LENGTH, search, SEARCH_LIMIT } from '@/db/content';
import { useQuery } from '@/db/hooks';
import { openHadith } from '@/reader/openHadith';
import { simplify } from '@/search/simplify';
import { count, HADITH } from '@/text/count';
import { fonts, MAX_SCALE, useColors } from '@/theme';

// How long typing pauses before the search runs.
const DELAY = 250;

// Search the hadith text by word, ignoring tashkeel, or open a hadith by its number (database/README.md, "Search").
export default function SearchScreen() {
  const colors = useColors();
  const [typed, setTyped] = useState('');
  const [query, setQuery] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setQuery(typed), DELAY);
    return () => clearTimeout(timer);
  }, [typed]);

  // Each time the screen is opened, the field is ready to type in. The side menu hides the keyboard as it starts to
  // open or close, so when the screen is opened from it, the field takes the focus only once the menu is closed.
  const input = useRef<ComponentRef<typeof TextInput>>(null);
  const focused = useIsFocused();
  const isFocused = useRef(focused);
  const progress = useDrawerProgress();
  const focusField = useCallback(() => {
    if (isFocused.current) input.current?.focus();
  }, []);
  useEffect(() => {
    isFocused.current = focused;
    if (focused && progress.get() === 0) input.current?.focus();
  }, [focused, progress]);
  useAnimatedReaction(
    () => progress.get() === 0,
    (closed, wasClosed) => {
      if (closed && wasClosed === false) scheduleOnRN(focusField);
    },
    [progress, focusField],
  );

  const tooShort = hadithNumber(query) === null && simplify(query).length < MIN_QUERY_LENGTH;
  // While a new search runs, the last results stay on screen rather than flashing away at each pause in typing.
  const results = useQuery(`search:${query}`, (db) => search(db, query), { keepPrevious: true });
  const hadith = !tooShort && results.status === 'done' ? results.value.hadith : [];

  let note: string | null = null;
  if (!query.trim()) note = 'ابحث بكلمة من نص الحديث، بلا حاجة إلى التشكيل، أو برقم الحديث';
  else if (tooShort) note = `اكتب ${MIN_QUERY_LENGTH} أحرف على الأقل`;
  else if (results.status === 'error') note = results.error.message;
  else if (results.status === 'done' && !results.stale) {
    if (hadith.length === 0) note = 'لم يوجد حديث فيه هذا النص';
    else if (results.value.more) note = `أول ${count(SEARCH_LIMIT, HADITH)}`;
    else note = count(hadith.length, HADITH);
  }

  return (
    <View style={[styles.fill, { backgroundColor: colors.background }]}>
      <View style={[styles.field, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        <Icon name="search" color={colors.muted} size={22} />
        <TextInput
          maxFontSizeMultiplier={MAX_SCALE.ui}
          ref={input}
          style={[styles.input, { color: colors.text }]}
          value={typed}
          onChangeText={setTyped}
          placeholder="كلمة أو رقم حديث"
          placeholderTextColor={colors.muted}
          autoCorrect={false}
          returnKeyType="search"
          accessibilityLabel="البحث"
        />
        {typed.length > 0 && (
          <Pressable onPress={() => setTyped('')} hitSlop={12} accessibilityRole="button" accessibilityLabel="مسح">
            <Icon name="clear" color={colors.muted} size={20} />
          </Pressable>
        )}
      </View>
      {note && <Text style={[styles.note, { color: colors.muted }]}>{note}</Text>}
      <FlatList
        data={hadith}
        keyExtractor={(hadith) => String(hadith.id)}
        renderItem={({ item }) => <HadithRow hadith={item} onPress={() => openHadith(item.id)} />}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  field: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    margin: 16,
    marginBottom: 8,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  input: { flex: 1, paddingVertical: 10, fontFamily: fonts.ui, fontSize: 17, textAlign: 'left' },
  note: { marginHorizontal: 16, marginBottom: 8, fontFamily: fonts.ui, fontSize: 14, textAlign: 'left' },
});
