// Learn more https://docs.expo.dev/guides/customizing-metro
const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// database/riyad.db is bundled as an asset (database/README.md).
config.resolver.assetExts.push('db');

// Keep Metro out of the content pipeline (book_data/.cache holds hundreds of MB of page images) and the v1 app.
const escape = (dir) => path.join(__dirname, dir).replace(/[/\\]/g, '[/\\\\]').replace(/\./g, '\\.');
config.resolver.blockList = [new RegExp(`^${escape('book_data')}[/\\\\].*`), new RegExp(`^${escape('v1')}[/\\\\].*`)];

module.exports = config;
