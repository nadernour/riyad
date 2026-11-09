import { claimTap, releaseTap, tapClaimed } from './tapGuard';

test("a link's press claims the pager's tap that comes with it, and only that one", () => {
  expect(tapClaimed()).toBe(false);
  claimTap();
  expect(tapClaimed()).toBe(true);
  expect(tapClaimed()).toBe(false);
  // The pager's tap can come just after the link's release, too.
  claimTap();
  releaseTap();
  expect(tapClaimed()).toBe(true);
});

test('a press that ends without a tap, such as a swipe that began on a link, lets the claim lapse soon after', () => {
  const now = Date.now();
  claimTap();
  releaseTap(now);
  expect(tapClaimed(now + 300)).toBe(false);
});

test('a press whose release never comes, as when the link leaves the screen under the finger, lapses too', () => {
  const now = Date.now();
  claimTap(now);
  expect(tapClaimed(now + 6000)).toBe(false);
});
