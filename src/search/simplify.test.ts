import { simplify } from './simplify';

const { cases } = require('../../database/simplify.json') as { cases: [string, string][] };

test('has the test cases', () => {
  expect(cases.length).toBeGreaterThan(0);
});

test.each(cases)('simplify(%j)', (input, expected) => {
  expect(simplify(input)).toBe(expected);
});
