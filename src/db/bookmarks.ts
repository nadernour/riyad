import { useSyncExternalStore } from 'react';

import { addBookmark, clearBookmarks, listBookmarks, removeBookmark, type Bookmark } from './user';
import { userDb } from './userDb';

// The bookmarks, as every screen that shows them sees them: the reader's button, the bookmarks screen and the side
// menu change together. They are read from user.db once, and again after each change.
const listeners = new Set<() => void>();
const NONE: Bookmark[] = [];
let snapshot: Bookmark[] | null = null;
// When user.db last failed to be read: it is tried again only after RETRY_MS, rather than at every render.
let failedAt = -Infinity;
const RETRY_MS = 5000;

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

// If user.db can't be read, there are no bookmarks to show, and the rest of the app works on without them. It is
// tried again a little later.
function getSnapshot(): Bookmark[] {
  if (!snapshot) {
    if (Date.now() - failedAt < RETRY_MS) return NONE;
    try {
      snapshot = listBookmarks(userDb());
    } catch {
      failedAt = Date.now();
      return NONE;
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
