// Splits a hadith's commentary as v1 stores it (riyad_salheen.db, hadiths.sharh) into word meanings and benefits, the
// form of v2's `meanings` and `benefits` tables. Used only to build the preview database for test builds
// (scripts/build-preview-db.js): v2 is never released with v1's commentary (CLAUDE.md).
//
// v1's tags come from the colours of the HTML it was copied from: <p0> a heading («لغة الحديث», «أفاد الحديث»),
// <p1> the word being explained, <bullet> a benefit. A heading is sometimes split over two tags, so a heading line is
// recognised by its text.

const TAG = /<\/?[a-z0-9]+>/g;

function plain(line) {
  return line.replace(TAG, ' ').replace(/\s+/g, ' ').trim();
}

function append(text, more) {
  return `${text} ${more}`.trim();
}

function parseCommentary(sharh) {
  const meanings = [];
  const benefits = [];
  let section = null;
  // Most of v1 marks the explained word with <p1>; a few commentaries mark none, and there a line «word : meaning» is
  // one. Where words are marked, an unmarked «… : …» (such as «قال تعالى : …») goes on with the meaning before it.
  const marked = (sharh ?? '').includes('<p1>');

  for (const line of (sharh ?? '').split('\n')) {
    // A heading starts its line; <p0> later in a line marks something else, such as a verse quoted in a meaning.
    if (line.trimStart().startsWith('<p0>')) {
      const heading = plain(line);
      if (/^لغة/.test(heading)) {
        section = 'meanings';
      } else if (/^(و?أفاد|فوائد)/.test(heading)) {
        section = 'benefits';
      } else if (/^تنبيه/.test(heading)) {
        // A note printed with the benefits (README.md, "What the app shows"): the note is the benefit.
        section = 'benefits';
        benefits.push(heading);
      } else {
        section = null;
      }
      continue;
    }

    const text = plain(line);
    if (!text) continue;

    if (section === 'meanings') {
      // «<p1>word</p1> : meaning», from v1's hadith 113 on «<bullet> <p1>word:</p1> meaning»; a line that doesn't start
      // with a marked word goes on with the meaning before it, as does text before a line's first bullet.
      const parts = line.split('<bullet>');
      for (const part of parts) {
        const partText = plain(part);
        const match = partText.match(/^(.+?)\s*:\s*(.+)$/);
        const isWord = marked ? part.trimStart().startsWith('<p1>') : match && match[1].split(' ').length <= 5;
        if (isWord && match) {
          meanings.push({ term: match[1], meaning: match[2] });
        } else if (partText && meanings.length > 0) {
          meanings[meanings.length - 1].meaning = append(meanings[meanings.length - 1].meaning, partText);
        }
      }
    } else if (section === 'benefits') {
      if (line.includes('<bullet>')) {
        // Text before the first bullet goes on with the benefit before it.
        const [before, ...items] = line.split('<bullet>').map(plain);
        if (before && benefits.length > 0) benefits[benefits.length - 1] = append(benefits[benefits.length - 1], before);
        else if (before) benefits.push(before);
        for (const item of items) if (item) benefits.push(item);
      } else if (benefits.length > 0) {
        benefits[benefits.length - 1] = append(benefits[benefits.length - 1], text);
      } else {
        // Some benefits are a paragraph with no bullet.
        benefits.push(text);
      }
    }
  }

  return { meanings, benefits };
}

module.exports = { parseCommentary };
