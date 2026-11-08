import { Component, type ReactNode } from 'react';
import { Pressable, StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';

import { Text } from '@/components/Text';
import { fonts, useColors } from '@/theme';

// What a screen shows when its content can't be read: a message in Arabic and a button to try again. The error's own
// message, in English, is kept in small type under it, for a reader reporting the problem to quote.
export function ErrorView({
  error,
  title = 'تعذّر تحميل المحتوى',
  onRetry,
  style,
}: {
  error: Error;
  title?: string;
  onRetry?: () => void;
  style?: StyleProp<ViewStyle>;
}) {
  const colors = useColors();
  return (
    <View style={[styles.box, style]}>
      <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
      {onRetry && (
        <Pressable
          onPress={onRetry}
          hitSlop={8}
          style={({ pressed }) => [
            styles.button,
            { borderColor: colors.accent },
            pressed && { backgroundColor: colors.surface },
          ]}
          accessibilityRole="button">
          <Text style={[styles.buttonText, { color: colors.accent }]}>إعادة المحاولة</Text>
        </Pressable>
      )}
      <Text style={[styles.detail, { color: colors.muted }]} selectable>
        {error.message}
      </Text>
    </View>
  );
}

// An error thrown while rendering what's inside: riyad.db failing to open (src/db/ContentProvider.tsx), or any screen
// failing to render. It is shown with ErrorView, whose button renders the inside afresh, opening the database again
// and starting from the reader.
export class ErrorBoundary extends Component<
  { children: ReactNode; style?: StyleProp<ViewStyle>; onError?: (error: Error) => void },
  { error: Error | null; attempt: number }
> {
  state = { error: null as Error | null, attempt: 0 };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error) {
    this.props.onError?.(error);
  }

  retry = () => this.setState(({ attempt }) => ({ error: null, attempt: attempt + 1 }));

  render() {
    if (this.state.error) {
      return <ErrorView error={this.state.error} title="حدث خطأ" onRetry={this.retry} style={this.props.style} />;
    }
    return (
      <View key={this.state.attempt} style={styles.fill}>
        {this.props.children}
      </View>
    );
  }
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  box: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    padding: 32,
  },
  title: { fontFamily: fonts.uiBold, fontSize: 18, textAlign: 'center' },
  button: {
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  buttonText: { fontFamily: fonts.uiSemiBold, fontSize: 15 },
  detail: {
    fontFamily: fonts.ui,
    fontSize: 12,
    textAlign: 'center',
    writingDirection: 'ltr',
  },
});
