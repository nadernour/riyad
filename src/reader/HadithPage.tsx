import { ActivityIndicator, StyleSheet, View, type AccessibilityActionEvent } from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';

import { Text } from '@/components/Text';
import { usePreviewCommentary } from '@/db/ContentProvider';
import { useHadith } from '@/db/hooks';
import { fonts, MAX_SCALE, TEXT_LINE_HEIGHT, useColors } from '@/theme';

import { HadithText } from './HadithText';

type Props = {
  id: number;
  fontSize: number;
  // Room left at the top for the header, which lies over the page, and at the bottom for the phone's own bars.
  insetTop: number;
  insetBottom: number;
  // Turns to the next (1) or previous (-1) hadith, for a screen reader, which takes the swipes for itself.
  onTurn?: (step: 1 | -1) => void;
};

// One hadith, as v1 shows it: its chapter and number, its short title, its text, then the word meanings and benefits
// from Nuzhat al-Muttaqin, which show only once they are transcribed (content step 5).
export function HadithPage({ id, fontSize, insetTop, insetBottom, onTurn }: Props) {
  const colors = useColors();
  const state = useHadith(id);
  const previewDb = usePreviewCommentary();

  if (state.status === 'loading') {
    return <ActivityIndicator style={[styles.fill, { paddingTop: insetTop }]} color={colors.prophet} />;
  }
  if (state.status === 'error' || !state.value) {
    return (
      <Text
        maxFontSizeMultiplier={MAX_SCALE.reader}
        style={[styles.meta, { color: colors.text, paddingTop: insetTop + 20, padding: 20 }]}>
        {state.status === 'error' ? state.error.message : `لم يوجد الحديث رقم ${id}`}
      </Text>
    );
  }

  const hadith = state.value;
  // VoiceOver offers these in its rotor, TalkBack in its actions menu, on the title and the text.
  const turn = onTurn && {
    accessibilityActions: [
      { name: 'next', label: 'الحديث التالي' },
      { name: 'previous', label: 'الحديث السابق' },
    ],
    onAccessibilityAction: (event: AccessibilityActionEvent) => {
      if (event.nativeEvent.actionName === 'next') onTurn(1);
      else if (event.nativeEvent.actionName === 'previous') onTurn(-1);
    },
  };
  const preview = previewDb && (
    <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.meta, { color: colors.muted }]}>
      من شرح النسخة الأولى، غير مراجَع
    </Text>
  );
  const bodySize = fontSize * 0.8;
  const body = { fontFamily: fonts.text, fontSize: bodySize, lineHeight: bodySize * TEXT_LINE_HEIGHT };

  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={[styles.content, { paddingTop: insetTop + 12, paddingBottom: insetBottom + 32 }]}>
      <View style={styles.headingRow}>
        <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.meta, styles.chapter, { color: colors.muted }]}>
          {hadith.chapter}
        </Text>
        <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.meta, { color: colors.muted }]}>
          الحديث رقم {hadith.id}
        </Text>
      </View>
      <Text
        maxFontSizeMultiplier={MAX_SCALE.reader}
        style={[styles.title, { color: colors.text }]}
        accessibilityRole="header"
        {...turn}>
        {hadith.title}
      </Text>

      <View style={[styles.rule, { backgroundColor: colors.border }]} />

      <HadithText pieces={hadith.pieces} fontSize={fontSize} {...turn} />

      {hadith.meanings.length > 0 && (
        <View style={styles.section}>
          <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.sectionTitle, { color: colors.prophet }]}>
            لغة الحديث
          </Text>
          {preview}
          {hadith.meanings.map((meaning, i) => (
            <Text maxFontSizeMultiplier={MAX_SCALE.reader} key={i} style={[body, { color: colors.text }]}>
              <Text style={{ fontFamily: fonts.textBold }} maxFontSizeMultiplier={MAX_SCALE.reader}>
                {meaning.term}
              </Text>
              : {meaning.meaning}
            </Text>
          ))}
        </View>
      )}

      {hadith.benefits.length > 0 && (
        <View style={styles.section}>
          <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.sectionTitle, { color: colors.prophet }]}>
            أفاد الحديث
          </Text>
          {preview}
          {hadith.benefits.map((benefit, i) => (
            <Text maxFontSizeMultiplier={MAX_SCALE.reader} key={i} style={[body, { color: colors.text }]}>
              • {benefit}
            </Text>
          ))}
        </View>
      )}

      {/* The page of the printed book, so a reader can check the text against it; not shown under v1's commentary,
          which isn't that page's. It is v2's own addition: v1 doesn't show it. */}
      {!(previewDb && (hadith.meanings.length > 0 || hadith.benefits.length > 0)) && (
        <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.meta, styles.page, { color: colors.muted }]}>
          نزهة المتقين، صفحة {hadith.page}
        </Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  content: { paddingHorizontal: 20, gap: 12 },
  // With large text the number goes under the chapter, rather than squeezing it to a word a line.
  headingRow: { flexDirection: 'row', flexWrap: 'wrap', columnGap: 12, alignItems: 'flex-start' },
  chapter: { flexGrow: 1, flexShrink: 1, flexBasis: '60%' },
  meta: { fontFamily: fonts.ui, fontSize: 14, textAlign: 'left' },
  title: { fontFamily: fonts.uiBold, fontSize: 20, textAlign: 'left' },
  rule: { height: StyleSheet.hairlineWidth, marginVertical: 4 },
  section: { gap: 6, marginTop: 12 },
  sectionTitle: { fontFamily: fonts.uiBold, fontSize: 16, textAlign: 'left' },
  page: { marginTop: 20, textAlign: 'center' },
});
