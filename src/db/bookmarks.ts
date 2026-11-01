import { useSyncExternalStore } from 'react';

import { addBookmark, clearBookmarks, listBookmarks, removeBookmark, type Bookmark } from './user';
import { userDb } from './userDb';

// The bookmarks, as every screen that shows them sees them: the reader's button, the bookmarks screen and the side
// menu change together. They are read from user.db once, and again after each change.
const listeners = new Set<() => void>();
const NONE: Bookmark[] = [];
let snapshot: Bookmark[] | null = null;

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

// If user.db can't be read, there are no bookmarks to show, and the rest of the app works on without them.
function getSnapshot(): Bookmark[] {
  if (!snapshot) {
    try {
      snapshot = listBookmarks(userDb());
    } catch {
      snapshot = NONE;
    }
  }
  return snapshot;
}

// A write that fails changes nothing on screen: the screens show user.db as it is.
function change(write: () => void) {
  try {
    write();
  } catch {
    // As above.
  } finally {
    snapshot = null;
    listeners.forEach((listener) => listener());
  }
}

// Newest first.
export function useBookmarks(): Bookmark[] {
  return useSyncExternalStore(subscribe, getSnapshot);
}

export function useIsBookmarked(hadithId: number): boolean {
  return useBookmarks().some((bookmark) => bookmark.hadithId === hadithId);
}

export function setBookmarked(hadithId: number, bookmarked: boolean) {
  change(() => (bookmarked ? addBookmark(userDb(), hadithId) : removeBookmark(userDb(), hadithId)));
}

export function removeAllBookmarks() {
  change(() => clearBookmarks(userDb()));
}
