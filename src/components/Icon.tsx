import { SymbolView } from 'expo-symbols';
import type { ComponentProps } from 'react';
import type { ColorValue } from 'react-native';

type SymbolName = ComponentProps<typeof SymbolView>['name'];

// The app's icons, by what they mean: SF Symbols on iPhone, Material Symbols on Android (expo-symbols). Android's are
// outlines only, so a bookmarked hadith shows a bookmark with a tick there, and a filled one on iPhone.
const ICONS = {
  reader: { ios: 'book', android: 'auto_stories' },
  books: { ios: 'books.vertical', android: 'menu_book' },
  search: { ios: 'magnifyingglass', android: 'search' },
  bookmarks: { ios: 'bookmark', android: 'bookmarks' },
  bookmark: { ios: 'bookmark', android: 'bookmark' },
  bookmarked: { ios: 'bookmark.fill', android: 'bookmark_added' },
  remove: { ios: 'trash', android: 'delete' },
  clear: { ios: 'xmark.circle.fill', android: 'close' },
  expand: { ios: 'chevron.down', android: 'expand_more' },
  collapse: { ios: 'chevron.up', android: 'expand_less' },
  current: { ios: 'checkmark.circle.fill', android: 'check_circle' },
  share: { ios: 'square.and.arrow.up', android: 'share' },
  settings: { ios: 'gearshape', android: 'settings' },
  about: { ios: 'info.circle', android: 'info' },
  email: { ios: 'envelope', android: 'mail' },
  code: { ios: 'chevron.left.forwardslash.chevron.right', android: 'code' },
  smaller: { ios: 'minus', android: 'remove' },
  larger: { ios: 'plus', android: 'add' },
  chosen: { ios: 'checkmark', android: 'check' },
} satisfies Record<string, SymbolName>;

export type IconName = keyof typeof ICONS;

// An icon says nothing to a screen reader: the button around it has the label (iOS would otherwise read the symbol's
// name, such as «books.vertical»).
export function Icon({ name, color, size = 24 }: { name: IconName; color: ColorValue; size?: number }) {
  return (
    <SymbolView
      name={ICONS[name]}
      tintColor={color}
      size={size}
      accessible={false}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    />
  );
}
