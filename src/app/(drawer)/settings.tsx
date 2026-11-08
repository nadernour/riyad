import { Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { Icon, type IconName } from '@/components/Icon';
import { Text } from '@/components/Text';
import { useHadith } from '@/db/hooks';
import { FONT_SIZE, setFontSize, setPalette, setTheme, useSettings, type Theme } from '@/db/settings';
import { HadithText } from '@/reader/HadithText';
import { fonts, PALETTES, useColors, useScheme, type Palette } from '@/theme';

const THEMES: { theme: Theme; label: string; note?: string }[] = [
  { theme: 'system', label: 'تلقائي', note: 'كإعداد الجهاز' },
  { theme: 'light', label: 'فاتح' },
  { theme: 'dark', label: 'داكن' },
];

// Every palette, as the type has them, so a new one can't be left out of the list.
const PALETTE_CHOICES: Record<Palette, { label: string; note: string }> = {
  green: { label: 'أخضر', note: 'ألوان التطبيق الأولى' },
  gold: { label: 'ذهبي', note: 'بألوان شعار التطبيق' },
  manuscript: { label: 'مخطوطة', note: 'كلام النبي ﷺ بالأحمر، كما في كتب الحديث' },
};

// The reader's settings: the font size, as v1 has it (14 to 30), the theme: the phone's, light or dark, and the
// palette (src/theme). v1 has a dark-mode toggle that means "the opposite of the phone's", which turns the app light
// when the phone turns dark.
export default function SettingsScreen() {
  const colors = useColors();
  const { fontSize, theme, palette } = useSettings();
  const scheme = useScheme();
  // A sample to show the font size by: the first hadith's short title, a phrase of its text, in the Prophet's style.
  const first = useHadith(1);
  const sample = first.status === 'done' && first.value ? first.value.title : null;
  const smaller = () => setFontSize(fontSize - FONT_SIZE.step);
  const larger = () => setFontSize(fontSize + FONT_SIZE.step);

  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.content}>
      <Text style={[styles.heading, { color: colors.accent }]}>حجم الخط</Text>
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

      <Text style={[styles.heading, { color: colors.accent }]}>المظهر</Text>
      <Choices
        options={THEMES.map((option) => ({ key: option.theme, label: option.label, note: option.note }))}
        chosen={theme}
        onChoose={setTheme}
      />

      <Text style={[styles.heading, { color: colors.accent }]}>الألوان</Text>
      <Choices
        options={(Object.keys(PALETTE_CHOICES) as Palette[]).map((key) => {
          const option = PALETTE_CHOICES[key];
          const shown = PALETTES[key][scheme];
          return {
            key,
            label: option.label,
            note: option.note,
            swatches: [shown.background, shown.accent, shown.prophet],
          };
        })}
        chosen={palette}
        onChoose={setPalette}
      />
    </ScrollView>
  );
}

// A list to choose one of, each with its label, a note under it, and colours to show it by.
function Choices<K extends string>({
  options,
  chosen,
  onChoose,
}: {
  options: { key: K; label: string; note?: string; swatches?: string[] }[];
  chosen: K;
  onChoose: (key: K) => void;
}) {
  const colors = useColors();
  return (
    <View style={[styles.card, { borderColor: colors.border }]} accessibilityRole="radiogroup">
      {options.map((option, i) => {
        const isChosen = option.key === chosen;
        return (
          <Pressable
            key={option.key}
            onPress={() => onChoose(option.key)}
            style={({ pressed }) => [
              styles.option,
              i > 0 && { borderTopWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
              pressed && { backgroundColor: colors.surface },
            ]}
            accessibilityRole="radio"
            accessibilityLabel={option.note ? `${option.label}، ${option.note}` : option.label}
            accessibilityState={{ checked: isChosen, selected: isChosen }}>
            {option.swatches && (
              <View style={[styles.swatches, { borderColor: colors.border }]}>
                {option.swatches.map((color, at) => (
                  <View key={at} style={[styles.swatch, { backgroundColor: color }]} />
                ))}
              </View>
            )}
            <View style={styles.fill}>
              <Text style={[styles.label, { color: colors.text }]}>{option.label}</Text>
              {option.note && <Text style={[styles.note, { color: colors.muted }]}>{option.note}</Text>}
            </View>
            {isChosen && <Icon name="chosen" color={colors.accent} />}
          </Pressable>
        );
      })}
    </View>
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
  swatches: { flexDirection: 'row', borderWidth: StyleSheet.hairlineWidth, borderRadius: 8, overflow: 'hidden' },
  swatch: { width: 14, height: 28 },
});
