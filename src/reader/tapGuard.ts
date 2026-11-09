// The reader's pager toggles full screen on a tap anywhere on the page (src/reader/Pager.tsx), including on the links
// in it, such as the chapter line (PageLink). A link claims the tap while the finger is on it, and for a moment after
// it lifts, when the pager's tap comes: the reader then leaves full screen alone. A touch that ends some other way, a
// swipe that began on the link or a long press, lets the claim lapse just as soon, so the next tap is the pager's.
const AFTER_RELEASE_MS = 150;
// A press longer than this isn't a tap, and lets the claim lapse even if its release never comes, as when the link
// leaves the screen under the finger.
const LONGEST_PRESS_MS = 5000;
let claimedUntil = -Infinity;
let pressed = false;

// As the finger comes down on a link.
export function claimTap(now = Date.now()) {
  claimedUntil = now + LONGEST_PRESS_MS;
  pressed = true;
}

// As it lifts, or the touch is taken over by a swipe.
export function releaseTap(now = Date.now()) {
  if (pressed) claimedUntil = Math.min(claimedUntil, now + AFTER_RELEASE_MS);
  pressed = false;
}

// Whether the pager's tap that just came was on a link; each claim covers one tap.
export function tapClaimed(now = Date.now()): boolean {
  const claimed = now < claimedUntil;
  claimedUntil = -Infinity;
  pressed = false;
  return claimed;
}
