// Learn more https://docs.expo.dev/guides/customizing-metro
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// database/riyad.db is bundled as an asset (database/README.md).
config.resolver.assetExts.push('db');

// Keep Metro out of the content pipeline (book_data/.cache holds hundreds of MB of page images) and the v1 app.
const escape = (dir) => path.join(__dirname, dir).replace(/[/\\]/g, '[/\\\\]').replace(/\./g, '\\.');
config.resolver.blockList = [new RegExp(`^${escape('book_data')}[/\\\\].*`), new RegExp(`^${escape('v1')}[/\\\\].*`)];

// A test build bundles .preview/riyad.db, with v1's commentary, in place of database/riyad.db when there is one
// (npm run preview-db). A release never does: v2 is not released with v1's commentary (CLAUDE.md). Nor does a build
// once database/riyad.db has changed since the preview was built from it: that would show the old text.
const DATABASE = path.join(__dirname, 'database', 'riyad.db');
const PREVIEW = path.join(__dirname, '.preview', 'riyad.db');
const STAMP = path.join(__dirname, '.preview', 'source.sha256');

function previewIsCurrent() {
  if (!fs.existsSync(PREVIEW) || !fs.existsSync(STAMP)) return false;
  const hash = crypto.createHash('sha256').update(fs.readFileSync(DATABASE)).digest('hex');
  if (fs.readFileSync(STAMP, 'utf8').trim() === hash) return true;
  console.warn(
    "database/riyad.db has changed since .preview/riyad.db was built: bundling it, without v1's commentary. Run `npm run preview-db` to rebuild the preview.",
  );
  return false;
}

if (process.env.APP_VARIANT !== 'production' && previewIsCurrent()) {
  const upstream = config.resolver.resolveRequest;
  config.resolver.resolveRequest = (context, moduleName, platform) => {
    const resolution = (upstream ?? context.resolveRequest)(context, moduleName, platform);
    if (resolution.type === 'assetFiles' && resolution.filePaths.includes(DATABASE)) {
      return { type: 'assetFiles', filePaths: [PREVIEW] };
    }
    return resolution;
  };
}

module.exports = config;
