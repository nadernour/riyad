import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';

import { useHadith } from '@/db/hooks';
import { fonts, TEXT_LINE_HEIGHT, useColors } from '@/theme';

import { HadithText } from './HadithText';

type Props = {
  id: number;
  fontSize: number;
  // Room left at the top for the header, which lies over the page, and at the bottom for the phone's own bars.
  insetTop: number;
  insetBottom: number;
};

// One hadith, as v1 shows it: its chapter and number, its short title, its text, then the word meanings and benefits
// from Nuzhat al-Muttaqin, which show only once they are transcribed (content step 5).
export function HadithPage({ id, fontSize, insetTop, insetBottom }: Props) {
  const colors = useColors();
  const state = useHadith(id);

  if (state.status === 'loading') {
    return <ActivityIndicator style={[styles.fill, { paddingTop: insetTop }]} color={colors.prophet} />;
  }
  if (state.status === 'error' || !state.value) {
    return (
      <Text style={[styles.meta, { color: colors.text, paddingTop: insetTop + 20, padding: 20 }]}>
        {state.status === 'error' ? state.error.message : `لم يوجد الحديث رقم ${id}`}
      </Text>
    );
  }

  const hadith = state.value;
  const bodySize = fontSize * 0.8;
  const body = { fontFamily: fonts.text, fontSize: bodySize, lineHeight: bodySize * TEXT_LINE_HEIGHT };

  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={[styles.content, { paddingTop: insetTop + 12, paddingBottom: insetBottom + 32 }]}>
      <View style={styles.headingRow}>
        <Text style={[styles.meta, styles.chapter, { color: colors.muted }]}>{hadith.chapter}</Text>
        <Text style={[styles.meta, { color: colors.muted }]}>الحديث رقم {hadith.id}</Text>
      </View>
      <Text style={[styles.title, { color: colors.text }]}>{hadith.title}</Text>

      <View style={[styles.rule, { backgroundColor: colors.border }]} />

      <HadithText pieces={hadith.pieces} fontSize={fontSize} />

      {hadith.meanings.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.prophet }]}>لغة الحديث</Text>
          {hadith.meanings.map((meaning, i) => (
            <Text key={i} style={[body, { color: colors.text }]}>
              <Text style={{ fontFamily: fonts.textBold }}>{meaning.term}</Text>: {meaning.meaning}
            </Text>
          ))}
        </View>
      )}

      {hadith.benefits.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.prophet }]}>أفاد الحديث</Text>
          {hadith.benefits.map((benefit, i) => (
            <Text key={i} style={[body, { color: colors.text }]}>
              • {benefit}
            </Text>
          ))}
        </View>
      )}

      <Text style={[styles.meta, styles.page, { color: colors.muted }]}>نزهة المتقين، صفحة {hadith.page}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  content: { paddingHorizontal: 20, gap: 12 },
  headingRow: { flexDirection: 'row', gap: 12, alignItems: 'flex-start' },
  chapter: { flex: 1 },
  meta: { fontFamily: fonts.ui, fontSize: 14, textAlign: 'left' },
  title: { fontFamily: fonts.uiBold, fontSize: 20, textAlign: 'left' },
  rule: { height: StyleSheet.hairlineWidth, marginVertical: 4 },
  section: { gap: 6, marginTop: 12 },
  sectionTitle: { fontFamily: fonts.uiBold, fontSize: 16, textAlign: 'left' },
  page: { marginTop: 20, textAlign: 'center' },
});
