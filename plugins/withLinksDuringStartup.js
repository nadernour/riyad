// On Android, a link that comes while the app is still starting (its JavaScript not yet running) is dropped by React
// Native: ReactHostImpl.onNewIntent passes a link on only once there is a React context. Keeping it as the activity's
// intent makes it the link the app was opened with, which Expo Router reads once it starts, so opening a hadith from a
// link (/?id=12) works however soon after launch the link comes. Tested by .maestro/links.yaml.
const { withMainActivity } = require('expo/config-plugins');

const MARKER = '// withLinksDuringStartup';

module.exports = function withLinksDuringStartup(config) {
  return withMainActivity(config, (activity) => {
    let source = activity.modResults.contents;
    if (source.includes(MARKER)) return activity;
    if (activity.modResults.language !== 'kt') throw new Error('withLinksDuringStartup expects a Kotlin MainActivity');

    if (!source.includes('import android.content.Intent')) {
      source = source.replace('import android.os.Bundle', 'import android.content.Intent\nimport android.os.Bundle');
    }
    source = source.replace(
      /class MainActivity : ReactActivity\(\) \{/,
      `$&
  ${MARKER}: keep a link that comes before React Native is running, for Expo Router to read once it is.
  override fun onNewIntent(intent: Intent) {
    super.onNewIntent(intent)
    setIntent(intent)
  }
`,
    );
    // A newer Expo template that no longer matches would otherwise lose the fix without a word.
    if (!source.includes(MARKER) || !source.includes('import android.content.Intent')) {
      throw new Error('withLinksDuringStartup could not find where to add onNewIntent in MainActivity.kt');
    }
    activity.modResults.contents = source;
    return activity;
  });
};
