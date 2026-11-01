import { useIsFocused } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '@/components/Icon';
import { listBooks, listChapters, type Book, type Chapter } from '@/db/content';
import { useHadith, useQuery } from '@/db/hooks';
import { lastHadithRead } from '@/reader/lastHadith';
import { openHadith } from '@/reader/openHadith';
import { CHAPTER, count } from '@/text/count';
import { fonts, useColors } from '@/theme';

// One list of the books, with the open book's chapters under it, so it can scroll to a chapter.
type Row = { kind: 'book'; book: Book } | { kind: 'chapter'; chapter: Chapter };

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
  const rows: Row[] =
    books.status === 'done'
      ? books.value.flatMap((book): Row[] => [
          { kind: 'book', book },
          ...(book.id === open && chapters.status === 'done'
            ? chapters.value.map((chapter): Row => ({ kind: 'chapter', chapter }))
            : []),
        ])
      : [];

  // Scrolled to the chapter being read once its row is there, once each time the reader has moved.
  const list = useRef<FlatList<Row>>(null);
  const scrolledFor = useRef<number | null>(null);
  const rowCount = useRef(0);
  useEffect(() => {
    rowCount.current = rows.length;
  });
  const target = rows.findIndex((row) => row.kind === 'chapter' && row.chapter.id === here?.chapterId);
  useEffect(() => {
    if (target < 0 || scrolledFor.current === openedFor) return;
    scrolledFor.current = openedFor;
    list.current?.scrollToIndex({ index: target, viewPosition: 0.3, animated: false });
  }, [target, openedFor]);

  if (books.status !== 'done') {
    return (
      <View style={[styles.fill, { backgroundColor: colors.background }]}>
        {books.status === 'loading' ? (
          <ActivityIndicator style={styles.fill} color={colors.prophet} />
        ) : (
          <Text style={[styles.chapter, { color: colors.text }]}>{books.error.message}</Text>
        )}
      </View>
    );
  }

  return (
    <FlatList
      ref={list}
      style={{ backgroundColor: colors.background }}
      data={rows}
      keyExtractor={(row) => (row.kind === 'book' ? `book:${row.book.id}` : `chapter:${row.chapter.id}`)}
      renderItem={({ item }) =>
        item.kind === 'book' ? (
          <BookRow
            book={item.book}
            open={open === item.book.id}
            onPress={() => setOpen(open === item.book.id ? null : item.book.id)}
          />
        ) : (
          <ChapterRow chapter={item.chapter} current={item.chapter.id === here?.chapterId} />
        )
      }
      ListFooterComponent={
        open !== null && chapters.status === 'loading' ? (
          <ActivityIndicator style={styles.loading} color={colors.prophet} />
        ) : undefined
      }
      // The rows above it may not be laid out yet: scroll near it, then try once more once they are, if the row is
      // still there (the book may have been closed meanwhile).
      onScrollToIndexFailed={({ index, averageItemLength }) => {
        list.current?.scrollToOffset({ offset: index * averageItemLength, animated: false });
        setTimeout(() => {
          if (index < rowCount.current) list.current?.scrollToIndex({ index, viewPosition: 0.3, animated: false });
        }, 50);
      }}
    />
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
      <Icon name="books" color={colors.prophet} />
      <View style={styles.fill}>
        <Text style={[styles.bookTitle, { color: colors.text }]}>{book.title}</Text>
        <Text style={[styles.count, { color: colors.muted }]}>{count(book.chapterCount, CHAPTER)}</Text>
      </View>
      <Icon name={open ? 'collapse' : 'expand'} color={colors.muted} />
    </Pressable>
  );
}

function ChapterRow({ chapter, current }: { chapter: Chapter; current: boolean }) {
  const colors = useColors();
  return (
    <Pressable
      style={({ pressed }) => [styles.chapterRow, pressed && { backgroundColor: colors.surface }]}
      onPress={() => openHadith(chapter.firstHadith)}
      accessibilityRole="button"
      accessibilityState={{ selected: current }}>
      <Text style={[styles.chapter, { color: current ? colors.prophet : colors.text }]}>{chapter.title}</Text>
      {current && <Icon name="current" color={colors.prophet} size={20} />}
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
