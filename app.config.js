// app.json holds the app's settings; this only changes them for builds that aren't the release. Those get their own id,
// name and link scheme, so a test build installs next to the v1 or v2 from the store instead of conflicting with it.
// The release settings are used only when APP_VARIANT is production: the production build profile in eas.json sets
// it, and `npm run submit` sets it for EAS Submit, whose profiles can't.
module.exports = ({ config }) => {
  if (process.env.APP_VARIANT === 'production') return config;

  return {
    ...config,
    name: `${config.name} (تجربة)`,
    scheme: `${config.scheme}-dev`,
    ios: { ...config.ios, bundleIdentifier: `${config.ios.bundleIdentifier}.dev` },
    android: { ...config.android, package: `${config.android.package}.dev` },
  };
};
