import { Drawer, DrawerToggleButton } from 'expo-router/drawer';
import { Platform, StyleSheet, type ColorValue, type LayoutChangeEvent } from 'react-native';

import { Icon, type IconName } from '@/components/Icon';
import { SideMenu } from '@/components/SideMenu';
import { Text } from '@/components/Text';
import { fonts, MAX_SCALE, useColors } from '@/theme';

// A side-menu item: its label is drawn with the app's Text, so the phone's text size enlarges it only as far as the
// app's other text (a plain string label would grow without limit).
function item(label: string, icon: IconName) {
  return {
    drawerLabel: function DrawerLabel({ color }: { color: ColorValue }) {
      return <Text style={[styles.label, { color }]}>{label}</Text>;
    },
    drawerAccessibilityLabel: label,
    drawerIcon: function DrawerIcon({ color }: { color: ColorValue }) {
      return <Icon name={icon} color={color} />;
    },
  };
}

// A screen's title, in its bar, which has a fixed height, at the size each platform's bar gives a title. The bar
// measures it through onLayout, to fit it beside its buttons.
function HeaderTitle({
  children,
  tintColor,
  onLayout,
}: {
  children: string;
  tintColor?: ColorValue;
  onLayout?: (event: LayoutChangeEvent) => void;
}) {
  return (
    <Text
      style={[styles.title, { color: tintColor }]}
      onLayout={onLayout}
      numberOfLines={1}
      maxFontSizeMultiplier={MAX_SCALE.bar}>
      {children}
    </Text>
  );
}

export default function DrawerLayout() {
  const colors = useColors();

  return (
    <Drawer
      drawerContent={(props) => <SideMenu {...props} />}
      screenOptions={{
        // In right-to-left layout the drawer opens from the right, and React Navigation then puts its button in headerRight,
        // which the mirrored header draws on the left. headerLeft is the header's start, so on the right, next to the drawer.
        headerLeft: () => <DrawerToggleButton tintColor={colors.text} accessibilityLabel="القائمة" />,
        headerRight: () => null,
        headerTitle: HeaderTitle,
        headerStyle: { backgroundColor: colors.background },
        headerTintColor: colors.text,
        drawerStyle: { backgroundColor: colors.background },
        drawerActiveTintColor: colors.prophet,
        drawerInactiveTintColor: colors.text,
      }}>
      {/* The reader draws its own header, which hides for full screen. */}
      <Drawer.Screen
        name="index"
        options={{
          title: 'رياض الصالحين',
          headerShown: false,
          ...item('القراءة', 'reader'),
        }}
      />
      <Drawer.Screen name="books" options={{ title: 'الكتب والأبواب', ...item('الكتب والأبواب', 'books') }} />
      <Drawer.Screen name="search" options={{ title: 'البحث', ...item('البحث', 'search') }} />
      <Drawer.Screen name="bookmarks" options={{ title: 'المفضلة', ...item('المفضلة', 'bookmarks') }} />
      <Drawer.Screen name="settings" options={{ title: 'الإعدادات', ...item('الإعدادات', 'settings') }} />
      <Drawer.Screen name="about" options={{ title: 'حول التطبيق', ...item('حول التطبيق', 'about') }} />
    </Drawer>
  );
}

const styles = StyleSheet.create({
  label: { fontFamily: fonts.uiSemiBold, fontSize: 15, textAlign: 'left' },
  title: { fontFamily: fonts.uiBold, fontSize: Platform.select({ ios: 17, default: 20 }) },
});
