import { Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { Icon, type IconName } from '@/components/Icon';
import { Text } from '@/components/Text';
import { useHadith } from '@/db/hooks';
import { FONT_SIZE, setFontSize, setTheme, useSettings, type Theme } from '@/db/settings';
import { HadithText } from '@/reader/HadithText';
import { fonts, useColors } from '@/theme';

const THEMES: { theme: Theme; label: string; note?: string }[] = [
  { theme: 'system', label: 'تلقائي', note: 'كإعداد الجهاز' },
  { theme: 'light', label: 'فاتح' },
  { theme: 'dark', label: 'داكن' },
];


// The reader's settings: the font size, as v1 has it (14 to 30), and the theme: the phone's, light or dark. v1 has a
// dark-mode toggle that means "the opposite of the phone's", which turns the app light when the phone turns dark.
export default function SettingsScreen() {
  const colors = useColors();
  const { fontSize, theme } = useSettings();
  // A sample to show the font size by: the first hadith's short title, a phrase of its text, in the Prophet's style.
  const first = useHadith(1);
  const sample = first.status === 'done' && first.value ? first.value.title : null;
  const smaller = () => setFontSize(fontSize - FONT_SIZE.step);
  const larger = () => setFontSize(fontSize + FONT_SIZE.step);

  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.content}>
      <Text style={[styles.heading, { color: colors.prophet }]}>حجم الخط</Text>
      <View style={[styles.card, { borderColor: colors.border }]}>
        <View style={styles.stepper}>
          <StepButton icon="smaller" label="تصغير الخط" disabled={fontSize <= FONT_SIZE.min} onPress={smaller} />
          <Text style={[styles.size, { color: colors.text }]} accessibilityLabel={`حجم الخط ${fontSize}`}>
            {fontSize}
          </Text>
          <StepButton icon="larger" label="تكبير الخط" disabled={fontSize >= FONT_SIZE.max} onPress={larger} />
        </View>
        {sample && (
          <View style={[styles.sample, { borderColor: colors.border }]}>
            <HadithText pieces={[{ role: 'prophet', text: sample }]} fontSize={fontSize} />
          </View>
        )}
      </View>

      <Text style={[styles.heading, { color: colors.prophet }]}>المظهر</Text>
      <View style={[styles.card, { borderColor: colors.border }]} accessibilityRole="radiogroup">
        {THEMES.map((option, i) => {
          const chosen = option.theme === theme;
          return (
            <Pressable
              key={option.theme}
              onPress={() => setTheme(option.theme)}
              style={({ pressed }) => [
                styles.option,
                i > 0 && { borderTopWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
                pressed && { backgroundColor: colors.surface },
              ]}
              accessibilityRole="radio"
              accessibilityLabel={option.note ? `${option.label}، ${option.note}` : option.label}
              accessibilityState={{ checked: chosen, selected: chosen }}>
              <View style={styles.fill}>
                <Text style={[styles.label, { color: colors.text }]}>{option.label}</Text>
                {option.note && <Text style={[styles.note, { color: colors.muted }]}>{option.note}</Text>}
              </View>
              {chosen && <Icon name="chosen" color={colors.prophet} />}
            </Pressable>
          );
        })}
      </View>
    </ScrollView>
  );
}

function StepButton({
  icon,
  label,
  disabled,
  onPress,
}: {
  icon: IconName;
  label: string;
  disabled: boolean;
  onPress: () => void;
}) {
  const colors = useColors();
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      hitSlop={8}
      style={({ pressed }) => [
        styles.step,
        { borderColor: colors.border },
        pressed && { backgroundColor: colors.surface },
        disabled && styles.disabled,
      ]}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}>
      <Icon name={icon} color={colors.text} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  content: { padding: 16, gap: 8 },
  heading: { fontFamily: fonts.uiBold, fontSize: 15, textAlign: 'left', marginTop: 8 },
  card: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 12, overflow: 'hidden' },
  stepper: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 12 },
  step: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 22, padding: 10 },
  disabled: { opacity: 0.35 },
  size: { fontFamily: fonts.uiBold, fontSize: 20 },
  sample: { paddingHorizontal: 16, paddingVertical: 8, borderTopWidth: StyleSheet.hairlineWidth },
  option: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12, paddingHorizontal: 16 },
  label: { fontFamily: fonts.uiSemiBold, fontSize: 16, textAlign: 'left' },
  note: { fontFamily: fonts.ui, fontSize: 13, textAlign: 'left' },
});
