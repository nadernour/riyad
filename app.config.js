// app.json holds the app's settings; this only changes them for builds that aren't the release. Those get their own id,
// name and link scheme, so a test build installs next to the v1 or v2 from the store instead of conflicting with it.
// The release settings are used only when APP_VARIANT is production: the production build profile in eas.json sets
// it, and `npm run submit` sets it for EAS Submit, whose profiles can't.
// The release reads everything from the bundle and needs no permissions, as v1 asks for none: those the native modules
// add (the internet, storage, drawing over other apps, vibration) are blocked, so v1's users see no new ones in the
// update. Test builds keep them: the development build loads its JavaScript over the network.
const BLOCKED_PERMISSIONS = [
  'android.permission.INTERNET',
  'android.permission.READ_EXTERNAL_STORAGE',
  'android.permission.WRITE_EXTERNAL_STORAGE',
  'android.permission.SYSTEM_ALERT_WINDOW',
  'android.permission.VIBRATE',
];

module.exports = ({ config }) => {
  if (process.env.APP_VARIANT === 'production') {
    return { ...config, android: { ...config.android, blockedPermissions: BLOCKED_PERMISSIONS } };
  }

  return {
    ...config,
    name: `${config.name} (تجربة)`,
    scheme: `${config.scheme}-dev`,
    ios: { ...config.ios, bundleIdentifier: `${config.ios.bundleIdentifier}.dev` },
    android: { ...config.android, package: `${config.android.package}.dev` },
  };
};
