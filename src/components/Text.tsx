import { Text as NativeText, type TextProps } from 'react-native';

import { MAX_SCALE } from '@/theme';

// React Native's Text, which the phone's text size enlarges only as far as MAX_SCALE.ui, unless it is given its own
// limit: the app's screens use this one.
export function Text(props: TextProps) {
  return <NativeText maxFontSizeMultiplier={MAX_SCALE.ui} {...props} />;
}
