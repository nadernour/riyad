import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect, type ReactNode } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import { ContentProvider } from '@/db/ContentProvider';
import { fontFiles } from '@/theme';

SplashScreen.preventAutoHideAsync();

// Rendered inside ContentProvider, which renders nothing until riyad.db is copied and opened: on a first launch, or
// the first after a new riyad.db, that takes a moment, and the splash screen covers it.
function HideSplash() {
  useEffect(() => {
    SplashScreen.hideAsync();
  }, []);
  return null;
}

// The screens render once the fonts are loaded and riyad.db is open.
function Ready({ children }: { children: ReactNode }) {
  const [loaded, error] = useFonts(fontFiles);
  if (!loaded && !error) return null;
  return (
    <ContentProvider>
      <HideSplash />
      {children}
    </ContentProvider>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      {/* The navigator itself is mounted from the start, and only what it renders waits for Ready: a link that comes
          while the app is starting (/?id=12) has a navigator to go to, rather than being dropped. */}
      <Stack screenOptions={{ headerShown: false }} layout={({ children }) => <Ready>{children}</Ready>} />
      <StatusBar style="auto" />
    </GestureHandlerRootView>
  );
}
