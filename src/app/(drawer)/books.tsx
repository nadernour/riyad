import { useIsFocused } from 'expo-router';
import { Fragment, useEffect, useRef, useState, type ComponentRef } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
  type LayoutChangeEvent,
} from 'react-native';

import { ErrorView } from '@/components/ErrorView';
import { Icon } from '@/components/Icon';
import { Text } from '@/components/Text';
import { listBooks, listChapters, type Book, type Chapter } from '@/db/content';
import { useHadith, useQuery } from '@/db/hooks';
import { lastHadithRead } from '@/reader/lastHadith';
import { openHadith } from '@/reader/openHadith';
import { CHAPTER, count } from '@/text/count';
import { fonts, useColors } from '@/theme';

// How many frames the list tries for to reach the chapter being read (see settle).
const MAX_TRIES = 30;

// Browse by book and chapter, as v1 does: a book opens to its chapters, and a chapter opens the reader at its first
// hadith. The book and chapter being read are open, marked and scrolled to.
export default function BooksScreen() {
  const colors = useColors();
  const books = useQuery('books', listBooks);

  // The drawer keeps this screen once opened, so each time it comes back it reads where the reader is now.
  const focused = useIsFocused();
  const [wasFocused, setWasFocused] = useState(focused);
  const [reading, setReading] = useState(lastHadithRead);
  const current = useHadith(reading);
  const here = current.status === 'done' && current.value ? current.value : null;
  const [open, setOpen] = useState<number | null>(null);
  const [openedFor, setOpenedFor] = useState<number | null>(null);
  if (focused !== wasFocused) {
    setWasFocused(focused);
    if (focused) setReading(lastHadithRead());
  }
  if (here && openedFor !== here.id) {
    setOpenedFor(here.id);
    setOpen(here.bookId);
  }

  const chapters = useQuery(`chapters:${open}`, (db) => (open ? listChapters(db, open) : Promise.resolve([])));

  // Scrolled to the chapter being read, once each time the reader has moved, as soon as the list and that chapter's
  // row are laid out. The list is short (20 books, and at most 115 chapters open), so it is all laid out and each
  // row's place is known: a FlatList lays out only the rows near the top, and could only guess at how far down a
  // chapter is. A chapter's place doesn't change, since only one book is open at a time.
  const list = useRef<ComponentRef<typeof ScrollView>>(null);
  const height = useRef(0);
  const contentHeight = useRef(0);
  const offset = useRef(0);
  const chapterY = useRef(new Map<number, number>());
  const target = useRef<{ chapterId: number; openedFor: number } | null>(null);
  const scrolledFor = useRef<number | null>(null);
  // Android cuts a scroll short to the content as it is on screen, which can still be the content before the book
  // opened (the rows report their layout before they are drawn). So the list checks, frame by frame, that it got
  // there, and scrolls again if not; a bounded number of times, and not once the reader scrolls it.
  const pending = useRef<{ y: number; tries: number } | null>(null);
  const settle = () => {
    const goal = pending.current;
    if (!goal || Math.abs(offset.current - goal.y) < 1 || goal.tries >= MAX_TRIES) {
      pending.current = null;
      return;
    }
    goal.tries += 1;
    list.current?.scrollTo({ y: goal.y, animated: false });
    requestAnimationFrame(settle);
  };
  const scrollToCurrent = () => {
    const goal = target.current;
    const y = goal ? chapterY.current.get(goal.chapterId) : undefined;
    if (!goal || y === undefined || !height.current || scrolledFor.current === goal.openedFor) return;
    scrolledFor.current = goal.openedFor;
    // A chapter near the end can't come up to 30% of the screen: the list scrolls only as far as its end.
    const end = Math.max(0, contentHeight.current - height.current);
    pending.current = { y: Math.min(Math.max(0, y - height.current * 0.3), end || Infinity), tries: 0 };
    settle();
  };
  const chapterId = here?.chapterId;
  useEffect(() => {
    target.current = chapterId !== undefined && openedFor !== null ? { chapterId, openedFor } : null;
    scrollToCurrent();
  });

  if (books.status !== 'done') {
    return (
      <View style={[styles.fill, { backgroundColor: colors.background }]}>
        {books.status === 'loading' ? (
          <ActivityIndicator style={styles.fill} color={colors.accent} />
        ) : (
          <ErrorView error={books.error} onRetry={books.retry} />
        )}
      </View>
    );
  }

  return (
    <ScrollView
      ref={list}
      style={{ backgroundColor: colors.background }}
      onLayout={(event) => {
        height.current = event.nativeEvent.layout.height;
        scrollToCurrent();
      }}
      onScroll={(event) => {
        offset.current = event.nativeEvent.contentOffset.y;
      }}
      scrollEventThrottle={16}
      onContentSizeChange={(_, size) => {
        contentHeight.current = size;
      }}
      onScrollBeginDrag={() => {
        pending.current = null;
      }}>
      {books.value.map((book) => (
        <Fragment key={book.id}>
          <BookRow book={book} open={open === book.id} onPress={() => setOpen(open === book.id ? null : book.id)} />
          {book.id === open &&
            (chapters.status === 'done' ? (
              chapters.value.map((chapter) => (
                <ChapterRow
                  key={chapter.id}
                  chapter={chapter}
                  current={chapter.id === here?.chapterId}
                  onLayout={(event) => {
                    chapterY.current.set(chapter.id, event.nativeEvent.layout.y);
                    scrollToCurrent();
                  }}
                />
              ))
            ) : chapters.status === 'loading' ? (
              <ActivityIndicator style={styles.loading} color={colors.accent} />
            ) : (
              <ErrorView error={chapters.error} onRetry={chapters.retry} style={styles.loading} />
            ))}
        </Fragment>
      ))}
    </ScrollView>
  );
}

function BookRow({ book, open, onPress }: { book: Book; open: boolean; onPress: () => void }) {
  const colors = useColors();
  return (
    <Pressable
      style={({ pressed }) => [
        styles.bookRow,
        { borderColor: colors.border },
        pressed && { backgroundColor: colors.surface },
      ]}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${book.title}، ${count(book.chapterCount, CHAPTER)}`}
      accessibilityState={{ expanded: open }}>
      <Icon name="books" color={colors.accent} />
      <View style={styles.fill}>
        <Text style={[styles.bookTitle, { color: colors.text }]}>{book.title}</Text>
        <Text style={[styles.count, { color: colors.muted }]}>{count(book.chapterCount, CHAPTER)}</Text>
      </View>
      <Icon name={open ? 'collapse' : 'expand'} color={colors.muted} />
    </Pressable>
  );
}

function ChapterRow({
  chapter,
  current,
  onLayout,
}: {
  chapter: Chapter;
  current: boolean;
  onLayout?: (event: LayoutChangeEvent) => void;
}) {
  const colors = useColors();
  return (
    <Pressable
      onLayout={onLayout}
      style={({ pressed }) => [styles.chapterRow, pressed && { backgroundColor: colors.surface }]}
      onPress={() => openHadith(chapter.firstHadith)}
      accessibilityRole="button"
      accessibilityState={{ selected: current }}>
      <Text style={[styles.chapter, { color: current ? colors.accent : colors.text }]}>{chapter.title}</Text>
      {current && <Icon name="current" color={colors.accent} size={20} />}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  bookRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  bookTitle: { fontFamily: fonts.uiBold, fontSize: 17, textAlign: 'left' },
  count: { fontFamily: fonts.ui, fontSize: 13, textAlign: 'left' },
  chapterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 10,
    paddingStart: 52,
    paddingEnd: 16,
  },
  chapter: { flex: 1, fontFamily: fonts.ui, fontSize: 15, lineHeight: 26, textAlign: 'left' },
  loading: { padding: 16 },
});
