import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
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

export default function RootLayout() {
  const [loaded, error] = useFonts(fontFiles);

  if (!loaded && !error) return null;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ContentProvider>
        <HideSplash />
        <Stack screenOptions={{ headerShown: false }} />
      </ContentProvider>
      <StatusBar style="auto" />
    </GestureHandlerRootView>
  );
}
