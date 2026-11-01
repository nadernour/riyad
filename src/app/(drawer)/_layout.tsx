import { Drawer, DrawerToggleButton } from 'expo-router/drawer';
import type { ColorValue } from 'react-native';

import { Icon, type IconName } from '@/components/Icon';
import { SideMenu } from '@/components/SideMenu';
import { fonts, useColors } from '@/theme';

function drawerIcon(name: IconName) {
  return function DrawerIcon({ color }: { color: ColorValue }) {
    return <Icon name={name} color={color} />;
  };
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
        headerTitleStyle: { fontFamily: fonts.uiBold },
        headerStyle: { backgroundColor: colors.background },
        headerTintColor: colors.text,
        drawerLabelStyle: { fontFamily: fonts.uiSemiBold },
        drawerStyle: { backgroundColor: colors.background },
        drawerActiveTintColor: colors.prophet,
        drawerInactiveTintColor: colors.text,
      }}>
      {/* The reader draws its own header, which hides for full screen. */}
      <Drawer.Screen
        name="index"
        options={{
          title: 'رياض الصالحين',
          drawerLabel: 'القراءة',
          headerShown: false,
          drawerIcon: drawerIcon('reader'),
        }}
      />
      <Drawer.Screen name="books" options={{ title: 'الكتب والأبواب', drawerIcon: drawerIcon('books') }} />
      <Drawer.Screen name="search" options={{ title: 'البحث', drawerIcon: drawerIcon('search') }} />
      <Drawer.Screen name="bookmarks" options={{ title: 'المفضلة', drawerIcon: drawerIcon('bookmarks') }} />
    </Drawer>
  );
}
