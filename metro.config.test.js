const path = require('path');

const config = require('./metro.config');

const blocked = (file) => config.resolver.blockList.some((re) => re.test(path.join(__dirname, file)));

test('bundles the database as an asset', () => {
  expect(config.resolver.assetExts).toContain('db');
});

test('keeps Metro out of book_data/ and v1/', () => {
  expect(blocked('book_data/.cache/pages/0001.png')).toBe(true);
  expect(blocked('v1/app/src/main/assets/databases/riyad_salheen.db')).toBe(true);
  expect(blocked('database/riyad.db')).toBe(false);
  expect(blocked('src/app/_layout.tsx')).toBe(false);
});
