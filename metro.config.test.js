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

describe('the preview database, with v1 commentary', () => {
  const DATABASE = path.join(__dirname, 'database', 'riyad.db');
  const PREVIEW = path.join(__dirname, '.preview', 'riyad.db');
  const STAMP = path.join(__dirname, '.preview', 'source.sha256');
  // sha256 of the stand-in database/riyad.db below.
  const SOURCE_HASH = require('crypto').createHash('sha256').update('the database').digest('hex');

  // The config as Metro would load it with this APP_VARIANT, whether the preview file is there, and the hash of the
  // database it was built from.
  function load(variant, previewExists, builtFrom = SOURCE_HASH) {
    const fs = require('fs');
    const existsSync = jest
      .spyOn(fs, 'existsSync')
      .mockImplementation((file) => previewExists && (file === PREVIEW || file === STAMP));
    const read = fs.readFileSync;
    const readFileSync = jest.spyOn(fs, 'readFileSync').mockImplementation((file, ...rest) => {
      if (file === DATABASE) return Buffer.from('the database');
      if (file === STAMP) return `${builtFrom}\n`;
      return read(file, ...rest);
    });
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    process.env.APP_VARIANT = variant ?? '';
    let loaded;
    jest.isolateModules(() => {
      loaded = require('./metro.config');
    });
    existsSync.mockRestore();
    readFileSync.mockRestore();
    warn.mockRestore();
    delete process.env.APP_VARIANT;
    return loaded;
  }

  // Resolves the database as the app requires it, with Metro's own resolver giving the real file.
  function resolveDatabase(loaded) {
    const context = {
      resolveRequest: () => ({ type: 'assetFiles', filePaths: [DATABASE] }),
    };
    const resolve = loaded.resolver.resolveRequest ?? context.resolveRequest;
    return resolve(context, '../../database/riyad.db', 'android').filePaths;
  }

  test('a test build bundles it when it has been built', () => {
    expect(resolveDatabase(load(undefined, true))).toEqual([PREVIEW]);
  });

  test('a test build without it bundles the real database', () => {
    expect(resolveDatabase(load(undefined, false))).toEqual([DATABASE]);
  });

  test('a test build bundles the real database once that has changed since the preview was built', () => {
    expect(resolveDatabase(load(undefined, true, 'an older hash'))).toEqual([DATABASE]);
  });

  test('a release never bundles it', () => {
    expect(resolveDatabase(load('production', true))).toEqual([DATABASE]);
  });
});
