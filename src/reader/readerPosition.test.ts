import { act, renderHook } from '@testing-library/react-native';

import { useReaderPosition } from './readerPosition';

jest.mock('./lastHadith', () => ({ lastHadithRead: () => 7 }));

type Params = { id?: string; q?: string };

function reader(params: Params) {
  return renderHook((props: Params) => useReaderPosition(props), { initialProps: params });
}

test('opens at the last hadith read, or the one asked for', async () => {
  expect((await reader({})).result.current).toMatchObject({ requested: 7, highlight: null });
  expect((await reader({ id: '12' })).result.current).toMatchObject({ requested: 12, highlight: null });
});

test('opened from search, the hadith shows the query, until the reader turns a page', async () => {
  const { result, rerender } = await reader({ id: '12', q: 'الصلاة' });
  expect(result.current).toMatchObject({ requested: 12, highlight: { id: 12, query: 'الصلاة' } });
  // The screen clears the id from the route; that changes nothing.
  await rerender({});
  expect(result.current.highlight).toEqual({ id: 12, query: 'الصلاة' });
  await act(() => result.current.turnTo(13));
  expect(result.current).toMatchObject({ requested: 13, highlight: null });
  // Back on it, it stays plain: the highlight was of that one visit from search.
  await act(() => result.current.turnTo(12));
  expect(result.current.highlight).toBeNull();
});

test('a hadith asked for while the reader is open moves it there, with its highlight if from search', async () => {
  const { result, rerender } = await reader({});
  await rerender({ id: '40', q: 'الزكاة' });
  expect(result.current).toMatchObject({ requested: 40, highlight: { id: 40, query: 'الزكاة' } });
  await rerender({});
  // From bookmarks or a link: no highlight.
  await rerender({ id: '30' });
  expect(result.current).toMatchObject({ requested: 30, highlight: null });
});

test('the same hadith asked for again, after paging away, is a new ask', async () => {
  const { result, rerender } = await reader({ id: '12', q: 'الصلاة' });
  await rerender({});
  await act(() => result.current.turnTo(13));
  await rerender({ id: '12', q: 'الصلاة' });
  expect(result.current).toMatchObject({ requested: 12, highlight: { id: 12, query: 'الصلاة' } });
});
