import { act, renderHook } from '@testing-library/react-native';

import { useQuery } from './hooks';

// The database is the same object at every render, as SQLiteProvider's is.
const mockDb = {};
jest.mock('expo-sqlite', () => ({ useSQLiteContext: () => mockDb }));

test('a query that failed runs again when retried', async () => {
  let failing = true;
  const query = jest.fn(() => (failing ? Promise.reject(new Error('disk I/O error')) : Promise.resolve(42)));
  const { result } = await renderHook(() => useQuery('answer', query));
  expect(result.current).toMatchObject({ status: 'error', error: { message: 'disk I/O error' } });

  failing = false;
  const calls = query.mock.calls.length;
  await act(async () => {
    if (result.current.status === 'error') result.current.retry();
  });
  expect(query.mock.calls.length).toBeGreaterThan(calls);
  expect(result.current).toEqual({ status: 'done', value: 42 });
});
