import { ActivityIndicator, I18nManager, ScrollView, StyleSheet, Text, View } from 'react-native';

import { getInfo, search, type Role } from '@/db/content';
import { useHadith, useQuery } from '@/db/hooks';
import { fonts, TEXT_LINE_HEIGHT, useColors, type Colors } from '@/theme';

// A check screen until the reader (P2): hadith 1, read from database/riyad.db; a search, which needs the trigram
// tokenizer in the phone's own SQLite; and whether the forced right-to-left layout applied.
const FONT_SIZE = 24;

function useCheck(): string {
  const state = useQuery('check', (db) => Promise.all([getInfo(db), search(db, 'إنما الأعمال'), search(db, '1500')]));
  const direction = I18nManager.isRTL ? 'من اليمين إلى اليسار' : 'LEFT TO RIGHT: forcesRTL did not apply';
  if (state.status === 'loading') return direction;
  if (state.status === 'error') return `خطأ: ${state.error.message}`;
  const [info, words, number] = state.value;
  return `${direction} · قاعدة البيانات ${info.content} · ${info.hadith} حديثًا · البحث: ${words.length} نتيجة (أولها ${words[0]?.id}) · الرقم 1500: ${number[0]?.title}`;
}

function roleStyle(role: Role, colors: Colors) {
  switch (role) {
    case 'prophet':
      return { color: colors.prophet, fontFamily: fonts.textBold };
    case 'speech':
      return { color: colors.muted };
    case 'gloss':
      return { textDecorationLine: 'underline' as const, textDecorationStyle: 'dotted' as const };
    default:
      return null;
  }
}

export default function CheckScreen() {
  const colors = useColors();
  const state = useHadith(1);
  const check = useCheck();

  if (state.status === 'loading') {
    return <ActivityIndicator style={{ flex: 1, backgroundColor: colors.background }} color={colors.prophet} />;
  }
  if (state.status === 'error' || !state.value) {
    return (
      <Text style={[styles.meta, { color: colors.text, padding: 20 }]}>
        {state.status === 'error' ? state.error.message : 'لم يوجد الحديث'}
      </Text>
    );
  }

  const hadith = state.value;
  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.content}>
      <Text style={[styles.meta, { color: colors.muted }]}>{check}</Text>

      <View style={[styles.header, { borderColor: colors.border }]}>
        <Text style={[styles.meta, { color: colors.muted }]}>
          {hadith.book} · {hadith.chapter}
        </Text>
        <Text style={[styles.title, { color: colors.text }]}>
          {hadith.id}. {hadith.title}
        </Text>
      </View>

      <Text style={[styles.matn, { color: colors.text }]}>
        {hadith.pieces.map((piece, i) => (
          <Text key={i} style={roleStyle(piece.role, colors)}>
            {piece.text}
          </Text>
        ))}
      </Text>

      <Text style={[styles.meta, { color: colors.muted }]}>صفحة {hadith.page}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 20, gap: 20 },
  header: { gap: 4, paddingBottom: 12, borderBottomWidth: StyleSheet.hairlineWidth },
  meta: { fontFamily: fonts.ui, fontSize: 14, textAlign: 'left' },
  title: { fontFamily: fonts.uiBold, fontSize: 18, textAlign: 'left' },
  matn: { fontFamily: fonts.text, fontSize: FONT_SIZE, lineHeight: FONT_SIZE * TEXT_LINE_HEIGHT, textAlign: 'justify' },
});
