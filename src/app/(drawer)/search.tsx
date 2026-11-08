import { useIsFocused } from 'expo-router';
import { useDrawerProgress } from 'expo-router/drawer';
import { useCallback, useEffect, useRef, useState, type ComponentRef } from 'react';
import { FlatList, Pressable, StyleSheet, TextInput, View } from 'react-native';
import { useAnimatedReaction } from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';

import { ErrorView } from '@/components/ErrorView';
import { HadithRow } from '@/components/HadithRow';
import { Icon } from '@/components/Icon';
import { Text } from '@/components/Text';
import { hadithNumber, MIN_QUERY_LENGTH, search, SEARCH_LIMIT, type SearchOrder } from '@/db/content';
import { useQuery } from '@/db/hooks';
import { setSearchOrder, useSearchOrder } from '@/db/settings';
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
  const order = useSearchOrder();
  // «عرض المزيد» shows the next SEARCH_LIMIT results; a new query or order starts again from the first.
  const [more, setMore] = useState({ for: '', limit: SEARCH_LIMIT });
  const searched = `${order}:${query}`;
  if (more.for !== searched && more.limit !== SEARCH_LIMIT) setMore({ for: '', limit: SEARCH_LIMIT });
  const limit = more.for === searched ? more.limit : SEARCH_LIMIT;
  const results = useQuery(`search:${order}:${limit}:${query}`, (db) => search(db, query, order, limit), {
    keepPrevious: true,
  });
  const showMore = () => setMore({ for: searched, limit: limit + SEARCH_LIMIT });
  // The order matters only for a word: a number finds one hadith.
  const byWord = !tooShort && hadithNumber(query) === null;
  const hadith = !tooShort && results.status === 'done' ? results.value.hadith : [];
  // The rows are highlighted, and open the reader, with the query they were found for, which can be behind the one
  // being typed while the next search runs.
  const foundFor = results.status === 'done' ? results.value.query : '';
  const highlightFor = hadithNumber(foundFor) === null ? foundFor : undefined;

  let note: string | null = null;
  if (!query.trim()) note = 'ابحث بكلمة من نص الحديث، بلا حاجة إلى التشكيل، أو برقم الحديث';
  else if (tooShort) note = `اكتب ${MIN_QUERY_LENGTH} أحرف على الأقل`;
  else if (results.status === 'done' && !results.stale) {
    if (hadith.length === 0) note = 'لم يوجد حديث فيه هذا النص';
    else if (results.value.more) note = `أول ${count(hadith.length, HADITH)}`;
    else note = count(hadith.length, HADITH);
  }
  const hasMore = !tooShort && results.status === 'done' && results.value.more;

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
      {(note || byWord) && (
        <View style={styles.bar}>
          {note && <Text style={[styles.note, { color: colors.muted }]}>{note}</Text>}
          {byWord && <OrderChoice order={order} />}
        </View>
      )}
      {results.status === 'error' && !tooShort ? (
        <ErrorView error={results.error} onRetry={results.retry} />
      ) : (
        <FlatList
          data={hadith}
          keyExtractor={(hadith) => String(hadith.id)}
          renderItem={({ item }) => (
            <HadithRow hadith={item} found={item} onPress={() => openHadith(item.id, highlightFor)} />
          )}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
          ListFooterComponent={
            hasMore ? (
              <Pressable
                onPress={showMore}
                disabled={results.stale}
                style={({ pressed }) => [styles.more, pressed && { backgroundColor: colors.surface }]}
                accessibilityRole="button">
                <Text style={[styles.moreText, { color: colors.accent }]}>عرض المزيد</Text>
              </Pressable>
            ) : undefined
          }
        />
      )}
    </View>
  );
}

const ORDERS: { order: SearchOrder; label: string }[] = [
  { order: 'relevance', label: 'الأقرب' },
  { order: 'book', label: 'ترتيب الكتاب' },
];

// The order of the results: the closest matches first, or the book's order. Kept for the next search.
function OrderChoice({ order }: { order: SearchOrder }) {
  const colors = useColors();
  return (
    <View
      style={[styles.choice, { borderColor: colors.border }]}
      accessibilityRole="radiogroup"
      accessibilityLabel="ترتيب النتائج">
      {ORDERS.map((option) => {
        const chosen = option.order === order;
        return (
          <Pressable
            key={option.order}
            onPress={() => setSearchOrder(option.order)}
            style={[styles.option, chosen && { backgroundColor: colors.surface }]}
            hitSlop={4}
            accessibilityRole="radio"
            accessibilityLabel={`ترتيب النتائج: ${option.label}`}
            accessibilityState={{ checked: chosen, selected: chosen }}>
            <Text style={[styles.optionText, { color: chosen ? colors.accent : colors.muted }]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  bar: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    marginHorizontal: 16,
    marginBottom: 8,
  },
  choice: { flexDirection: 'row', borderWidth: StyleSheet.hairlineWidth, borderRadius: 8, overflow: 'hidden' },
  option: { paddingVertical: 4, paddingHorizontal: 10 },
  optionText: { fontFamily: fonts.uiSemiBold, fontSize: 13 },
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
  note: { flexShrink: 1, fontFamily: fonts.ui, fontSize: 14, textAlign: 'left' },
  more: { alignItems: 'center', padding: 16 },
  moreText: { fontFamily: fonts.uiSemiBold, fontSize: 15 },
});
