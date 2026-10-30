import { I18nManager, ScrollView, StyleSheet, Text, View } from 'react-native';

import { fonts, TEXT_LINE_HEIGHT, useColors } from '@/theme';

// A P0 check screen: hadith 1 as database/riyad.db holds it, to see Amiri, ﷺ, the tashkeel and the right-to-left layout on a
// phone. P1 reads it from the database and P2 replaces this screen with the reader.
const SAMPLE = {
  id: 1,
  book: 'الكتاب الأول',
  chapter: 'الإخلاص و إحضار النية',
  title: 'إنَّما الأَعمالُ بالنِّيَّات',
  pieces: [
    {
      role: 'narration',
      text: 'وعَنْ أَميرِ الْمُؤْمِنِينَ أَبِي حفْصٍ عُمرَ بنِ الْخَطَّابِ رَضِيَ اللهُ عَنْهُ ، قَالَ : سمعْتُ رسُولَ اللهِ ﷺ يقُولُ ',
    },
    {
      role: 'prophet',
      text: '« إنَّما الأَعمالُ بالنِّيَّات ، وإِنَّمَا لِكُلِّ امرئٍ مَا نَوَى ، فمنْ كانَتْ هجْرَتُهُ إِلَى اللهِ ورَسُولِهِ فهجرتُه إِلَى اللهِ ورسُولِهِ ، ومنْ كَانَتْ هجْرَتُه لدُنْيَا يُصيبُها ، أَو امرَأَةٍ يَنْكحُها فَهِجْرَتُهُ إِلَى مَا هَاجَر إليْهِ »',
    },
    { role: 'narration', text: '\nمتَّفَقٌ عَلَى صحَّتِه.' },
  ],
};

const FONT_SIZE = 24;

export default function CheckScreen() {
  const colors = useColors();

  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.content}>
      <View style={[styles.header, { borderColor: colors.border }]}>
        <Text style={[styles.meta, { color: colors.muted }]}>
          {SAMPLE.book} · {SAMPLE.chapter}
        </Text>
        <Text style={[styles.title, { color: colors.text }]}>
          {SAMPLE.id}. {SAMPLE.title}
        </Text>
      </View>

      <Text style={[styles.matn, { color: colors.text }]}>
        {SAMPLE.pieces.map((piece, i) => (
          <Text key={i} style={piece.role === 'prophet' && { color: colors.prophet, fontFamily: fonts.textBold }}>
            {piece.text}
          </Text>
        ))}
      </Text>

      <Text style={[styles.meta, { color: colors.muted }]}>
        {I18nManager.isRTL ? 'الاتجاه: من اليمين إلى اليسار' : 'Layout is left to right: forcesRTL did not apply'}
      </Text>
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
