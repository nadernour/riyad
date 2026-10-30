import { useEffect, useRef, type ReactNode } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import {
  GestureDetector,
  useCompetingGestures,
  usePanGesture,
  useTapGesture,
} from 'react-native-gesture-handler';
import Animated, {
  cancelAnimation,
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';

// How many pages are rendered on each side of the current one: enough that the next swipe never waits for a render.
const WINDOW = 2;
// A drag past this part of the screen, or a flick faster than SWIPE_VELOCITY, turns the page.
const SWIPE_FRACTION = 0.25;
const SWIPE_VELOCITY = 500;
// Past the first or last page the drag moves this much of the finger's distance.
const EDGE_RESISTANCE = 0.3;

type Props = {
  // Pages are numbered 1 to count, as the hadith are.
  count: number;
  index: number;
  onIndexChange: (index: number) => void;
  renderPage: (index: number) => ReactNode;
  onTap?: () => void;
};

// A right-to-left pager, as a printed Arabic book turns: the next page is to the left, so a drag to the right brings
// it in. All pages sit on one strip, page n at n screen widths, and `position` is how far the strip has moved, so
// turning a page only animates `position`: no page moves or re-renders, and pages render only near the current one.
export function Pager({ count, index, onIndexChange, renderPage, onTap }: Props) {
  const { width } = useWindowDimensions();
  const position = useSharedValue(index * width);
  const start = useSharedValue(0);
  const startIndex = useSharedValue(index);
  const pageWidth = useSharedValue(width);
  const lastPage = useSharedValue(count);

  // The index this pager last reported, so a new `index` from outside (opening a hadith from search) can be told
  // from the one it reported itself, which it is already animating to. `reportedPage` is the same, for the gestures.
  const reported = useRef(index);
  const reportedPage = useSharedValue(index);
  // Whether the current touch became a page drag; one that didn't (a tap, or a vertical scroll) still stopped any
  // page turn under way, and has to finish it.
  const dragging = useSharedValue(false);

  useEffect(() => {
    pageWidth.set(width);
    lastPage.set(count);
  }, [width, count, pageWidth, lastPage]);

  useEffect(() => {
    if (index !== reported.current) {
      reported.current = index;
      reportedPage.set(index);
      cancelAnimation(position);
      position.set(index * width);
    }
  }, [index, width, position, reportedPage]);

  // Keeps the strip in place when the screen's width changes.
  useEffect(() => {
    position.set(reported.current * width);
  }, [width, position]);

  function report(next: number) {
    reported.current = next;
    onIndexChange(next);
  }

  // Animates to a page and, if it isn't the one last reported, reports it: the page shown and the page reported can't
  // differ once the strip comes to rest.
  function settle(target: number) {
    'worklet';
    position.set(withTiming(target * pageWidth.get(), { duration: 220, easing: Easing.out(Easing.cubic) }));
    if (target !== reportedPage.get()) {
      reportedPage.set(target);
      scheduleOnRN(report, target);
    }
  }

  const pan = usePanGesture({
    // Horizontal drags turn pages; a vertical one fails this gesture first, so the page's own scroll takes it.
    activeOffsetX: [-12, 12],
    failOffsetY: [-12, 12],
    onBegin: () => {
      'worklet';
      cancelAnimation(position);
      dragging.set(false);
      start.set(position.get());
      startIndex.set(Math.min(Math.max(Math.round(position.get() / pageWidth.get()), 1), lastPage.get()));
    },
    onActivate: () => {
      'worklet';
      dragging.set(true);
    },
    onUpdate: (event) => {
      'worklet';
      const min = pageWidth.get();
      const max = lastPage.get() * pageWidth.get();
      const next = start.get() + event.translationX;
      position.set(
        next < min ? min - (min - next) * EDGE_RESISTANCE : next > max ? max + (next - max) * EDGE_RESISTANCE : next,
      );
    },
    onDeactivate: (event) => {
      'worklet';
      const moved = (position.get() - startIndex.get() * pageWidth.get()) / pageWidth.get();
      const step =
        moved > SWIPE_FRACTION || event.velocityX > SWIPE_VELOCITY
          ? 1
          : moved < -SWIPE_FRACTION || event.velocityX < -SWIPE_VELOCITY
            ? -1
            : 0;
      settle(Math.min(Math.max(startIndex.get() + step, 1), lastPage.get()));
    },
    onFinalize: () => {
      'worklet';
      // A touch that never became a drag, made while a page was turning, left the strip between two pages.
      if (!dragging.get()) settle(startIndex.get());
    },
  });

  const tap = useTapGesture({
    // A finger that moves, or stays down, is reading or scrolling, not tapping: without these a short page, which has
    // nothing to scroll, would take a vertical drag as a tap.
    maxDistance: 10,
    maxDuration: 300,
    onActivate: () => {
      'worklet';
      if (onTap) scheduleOnRN(onTap);
    },
  });

  const gesture = useCompetingGestures(pan, tap);

  const pages: number[] = [];
  for (let page = Math.max(1, index - WINDOW); page <= Math.min(count, index + WINDOW); page++) pages.push(page);

  return (
    <GestureDetector gesture={gesture}>
      <View style={styles.pager}>
        {pages.map((page) => (
          <Page key={page} page={page} position={position} pageWidth={pageWidth}>
            {renderPage(page)}
          </Page>
        ))}
      </View>
    </GestureDetector>
  );
}

function Page({
  page,
  position,
  pageWidth,
  children,
}: {
  page: number;
  position: SharedValue<number>;
  pageWidth: SharedValue<number>;
  children: ReactNode;
}) {
  // translateX is physical, never mirrored by the right-to-left layout: page n + 1 is one screen to the left of n.
  const style = useAnimatedStyle(() => ({ transform: [{ translateX: position.get() - page * pageWidth.get() }] }));
  return <Animated.View style={[StyleSheet.absoluteFill, style]}>{children}</Animated.View>;
}

const styles = StyleSheet.create({
  pager: { flex: 1, overflow: 'hidden' },
});
