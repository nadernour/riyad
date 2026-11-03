import Constants from 'expo-constants';
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Icon, type IconName } from '@/components/Icon';
import { usePreviewCommentary } from '@/db/ContentProvider';
import { fonts, useColors } from '@/theme';

// v1's contact details and email subject.
const EMAIL = '1992please@gmail.com';
const EMAIL_SUBJECT = 'ملاحظات حول تطبيق رياض الصالحين';
const GITHUB = 'https://github.com/1992please/riyad-alsalheen';

const SECTIONS = [
  {
    title: 'عن الكتاب',
    text:
      'كتاب «رياض الصالحين من كلام سيد المرسلين» للإمام النووي، جمع فيه الأحاديث الصحيحة في أعمال القلوب والجوارح ' +
      'والأخلاق والآداب، وهو من أشهر كتب الحديث وأكثرها قراءةً في العالم الإسلامي. ومعاني الكلمات وفوائد الأحاديث في ' +
      'التطبيق من كتاب «نزهة المتقين شرح رياض الصالحين».',
  },
  {
    title: 'عن المؤلف',
    text:
      'الإمام محيي الدين يحيى بن شرف النووي (631–676 هـ) من كبار علماء الحديث والفقه الشافعي، له مؤلفات عديدة منها ' +
      'شرح صحيح مسلم والمجموع شرح المهذب والأذكار. اشتهر بورعه وزهده وتفانيه في طلب العلم.',
  },
  {
    title: 'عن التطبيق',
    text: [
      '• تصفح الأحاديث حسب الكتب والأبواب',
      '• البحث في الأحاديث بكلمة من نصها أو برقم الحديث',
      '• حفظ الأحاديث في المفضلة',
      '• مشاركة الحديث',
      '• تكبير الخط وتصغيره، والمظهر الفاتح والداكن',
      '• يعمل دون اتصال بالإنترنت، بلا حساب ولا إعلانات ولا تتبع',
      '',
      'نص الأحاديث من الإصدار الأول من التطبيق، المبني على قاعدة بيانات تطبيق من تطوير «مجموعة زاد»، ويُراجَع على ' +
        'كتاب «نزهة المتقين» المطبوع.',
    ].join('\n'),
  },
];

// About the book, its author and the app, and how to reach the developer, as in v1.
export default function AboutScreen() {
  const colors = useColors();
  const version = Constants.expoConfig?.version;
  const previewDb = usePreviewCommentary();

  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.content}>
      <View style={styles.top}>
        <Text style={[styles.name, { color: colors.prophet }]}>رياض الصالحين</Text>
        {version && <Text style={[styles.note, { color: colors.muted }]}>الإصدار {version}</Text>}
      </View>

      {SECTIONS.map((section) => (
        <View key={section.title} style={[styles.card, styles.padded, { borderColor: colors.border }]}>
          <Text style={[styles.heading, { color: colors.prophet }]}>{section.title}</Text>
          <Text style={[styles.text, { color: colors.text }]}>{section.text}</Text>
        </View>
      ))}

      {/* A test build may show v1's commentary meanwhile (CLAUDE.md): About says so, as the reader does. */}
      {previewDb && (
        <Text style={[styles.note, { color: colors.muted }]}>
          نسخة اختبار: المعاني والفوائد فيها من شرح الإصدار الأول، غير مراجَعة، لا من «نزهة المتقين».
        </Text>
      )}

      <Text style={[styles.heading, { color: colors.prophet }]}>التواصل مع المطور</Text>
      <View style={[styles.card, { borderColor: colors.border }]}>
        <Link
          icon="email"
          label="مراسلة عبر البريد الإلكتروني"
          url={`mailto:${EMAIL}?subject=${encodeURIComponent(EMAIL_SUBJECT)}`}
        />
        <View style={[styles.rule, { backgroundColor: colors.border }]} />
        <Link icon="code" label="مشروع التطبيق على GitHub" url={GITHUB} />
      </View>

      <View style={styles.footer}>
        <Text style={[styles.dua, { color: colors.muted }]}>نسأل الله أن ينفع بهذا العمل</Text>
        <Text style={[styles.note, { color: colors.muted }]}>اللهم علمنا ما ينفعنا وانفعنا بما علمتنا</Text>
      </View>
    </ScrollView>
  );
}

// A phone with no mail app can't open mailto: then nothing happens, as nothing can.
function Link({ icon, label, url }: { icon: IconName; label: string; url: string }) {
  const colors = useColors();
  return (
    <Pressable
      onPress={() => Linking.openURL(url).catch(() => {})}
      style={({ pressed }) => [styles.link, pressed && { backgroundColor: colors.surface }]}
      accessibilityRole="link"
      accessibilityLabel={label}>
      <Icon name={icon} color={colors.prophet} />
      <Text style={[styles.label, { color: colors.text }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, gap: 12 },
  top: { alignItems: 'center', paddingVertical: 8 },
  name: { fontFamily: fonts.uiBold, fontSize: 26 },
  card: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 12, overflow: 'hidden' },
  padded: { padding: 16, gap: 6 },
  heading: { fontFamily: fonts.uiBold, fontSize: 16, textAlign: 'left' },
  text: { fontFamily: fonts.ui, fontSize: 15, lineHeight: 26, textAlign: 'left' },
  link: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 16 },
  label: { flex: 1, fontFamily: fonts.uiSemiBold, fontSize: 15, textAlign: 'left' },
  rule: { height: StyleSheet.hairlineWidth },
  footer: { alignItems: 'center', gap: 4, paddingVertical: 16 },
  dua: { fontFamily: fonts.uiSemiBold, fontSize: 15, textAlign: 'center' },
  note: { fontFamily: fonts.ui, fontSize: 13, textAlign: 'center' },
});
