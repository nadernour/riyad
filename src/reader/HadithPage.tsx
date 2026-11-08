import { router, type Href } from 'expo-router';
import type { ReactNode } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  View,
  type AccessibilityActionEvent,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';

import { ErrorView } from '@/components/ErrorView';
import { Text } from '@/components/Text';
import { usePreviewCommentary } from '@/db/ContentProvider';
import { useHadith } from '@/db/hooks';
import { fonts, MAX_SCALE, TEXT_LINE_HEIGHT, useColors } from '@/theme';

import { HadithText } from './HadithText';
import { claimTap, releaseTap } from './tapGuard';

type Props = {
  id: number;
  // How many hadith there are, for «الحديث رقم 181 من 1898».
  total: number;
  fontSize: number;
  // Room left at the top for the header, which lies over the page, and at the bottom for the phone's own bars.
  insetTop: number;
  insetBottom: number;
  // Turns to the next (1) or previous (-1) hadith, for a screen reader, which takes the swipes for itself.
  onTurn?: (step: 1 | -1) => void;
  // A search query, opened from search: where it is in the text is highlighted.
  highlight?: string;
};

// One hadith, as v1 shows it: its chapter and number, its short title, its text, then the word meanings and benefits
// from Nuzhat al-Muttaqin, which show only once they are transcribed (content step 5).
export function HadithPage({ id, total, fontSize, insetTop, insetBottom, onTurn, highlight }: Props) {
  const colors = useColors();
  const state = useHadith(id);
  const previewDb = usePreviewCommentary();

  if (state.status === 'loading') {
    return <ActivityIndicator style={[styles.fill, { paddingTop: insetTop }]} color={colors.accent} />;
  }
  if (state.status === 'error') {
    return <ErrorView error={state.error} onRetry={state.retry} style={{ paddingTop: insetTop }} />;
  }
  if (!state.value) {
    return (
      <Text
        maxFontSizeMultiplier={MAX_SCALE.reader}
        style={[styles.meta, { color: colors.text, paddingTop: insetTop + 20, padding: 20 }]}>
        لم يوجد الحديث رقم {id}
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
      {/* The chapter opens Books & chapters, which shows it among the book's chapters, and the number opens search,
          where a number typed opens that hadith. A press here is not the pager's tap for full screen. */}
      <View style={styles.headingRow}>
        <PageLink href="/books" hint="يفتح الكتب والأبواب" style={styles.chapter}>
          <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.meta, { color: colors.accent }]}>
            {hadith.chapter}
          </Text>
        </PageLink>
        <PageLink href="/search" hint="يفتح البحث، للانتقال إلى حديث برقمه">
          <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.meta, { color: colors.muted }]}>
            الحديث رقم {hadith.id} من {total}
          </Text>
        </PageLink>
      </View>
      <Text
        maxFontSizeMultiplier={MAX_SCALE.reader}
        style={[styles.title, { color: colors.text }]}
        accessibilityRole="header"
        {...turn}>
        {hadith.title}
      </Text>

      <View style={[styles.rule, { backgroundColor: colors.border }]} />

      <HadithText pieces={hadith.pieces} fontSize={fontSize} highlight={highlight} {...turn} />

      {hadith.meanings.length > 0 && (
        <View style={styles.section}>
          <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.sectionTitle, { color: colors.accent }]}>
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
          <Text maxFontSizeMultiplier={MAX_SCALE.reader} style={[styles.sectionTitle, { color: colors.accent }]}>
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

// A link on the page, to another screen. Its press is not the pager's tap for full screen (src/reader/tapGuard.ts).
function PageLink({
  href,
  hint,
  style,
  children,
}: {
  href: Href;
  hint: string;
  style?: StyleProp<ViewStyle>;
  children: ReactNode;
}) {
  return (
    <Pressable
      onPressIn={() => claimTap()}
      onPressOut={() => releaseTap()}
      onPress={() => router.navigate(href)}
      style={style}
      accessibilityRole="link"
      accessibilityHint={hint}>
      {children}
    </Pressable>
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
