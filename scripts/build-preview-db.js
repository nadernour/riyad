// Builds .preview/riyad.db: database/riyad.db with v1's commentary in its `meanings` and `benefits` tables, so test
// builds can show word meanings and benefits before content step 5 transcribes the book's own. It is never committed
// and never in a release (metro.config.js); the app labels its commentary as v1's, not reviewed. Run:
//   npm run preview-db
// v1's commentary is an edited version of Nuzhat al-Muttaqin's, with some meanings changed (book_data/docs/audit.md),
// which is why v2 is not released with it (CLAUDE.md).
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { DatabaseSync } = require('node:sqlite');

const { parseCommentary } = require('./v1-commentary');

const ROOT = path.join(__dirname, '..');
const SOURCE = path.join(ROOT, 'database/riyad.db');
const V1 = path.join(ROOT, 'v1/app/src/main/assets/databases/riyad_salheen.db');
const CONTENT = path.join(ROOT, 'book_data/content/hadith');
const OUT_DIR = path.join(ROOT, '.preview');
const OUT = path.join(OUT_DIR, 'riyad.db');
// The hash of the database/riyad.db it was built from: metro.config.js bundles the preview only while they match.
const STAMP = path.join(OUT_DIR, 'source.sha256');

const sha256 = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
// Letters only, to compare a v1 word with a hadith's text.
const bare = (text) => text.replace(/[\u064B-\u0652\u0670\u0640]/g, '').replace(/[أإآ]/g, 'ا');

// v2's hadith numbers, with the v1 id each was converted from (content step 2).
function v1Ids() {
  const ids = new Map();
  for (const file of fs.readdirSync(CONTENT).filter((name) => name.endsWith('.json')).sort()) {
    const book = JSON.parse(fs.readFileSync(path.join(CONTENT, file), 'utf8'));
    for (const chapter of book.chapters) for (const hadith of chapter.hadith) if (hadith.old_id) ids.set(hadith.id, hadith.old_id);
  }
  return ids;
}

// Where v2 splits one v1 hadith in two (v1's 295 and 710), v1's commentary is for one of them: the one whose text has
// the most of the words it explains.
function owners(db, ids) {
  const text = db.prepare("SELECT group_concat(text, '') AS text FROM matn_pieces WHERE hadith_id = ?");
  const byOld = new Map();
  for (const [id, oldId] of ids) byOld.set(oldId, [...(byOld.get(oldId) ?? []), id]);
  const owner = new Map();
  for (const [oldId, shared] of byOld) {
    if (shared.length === 1) continue;
    owner.set(oldId, shared.map((id) => ({ id, text: bare(text.get(id)?.text ?? '') })));
  }
  return owner;
}

function build(db, v1) {
  const ids = v1Ids();
  const shared = owners(db, ids);
  const sharh = v1.prepare('SELECT sharh FROM hadiths WHERE id = ?');
  const counts = { hadith: 0, withMeanings: 0, withBenefits: 0, meanings: 0, benefits: 0, noV1: 0, split: 0 };
  db.exec('DELETE FROM meanings; DELETE FROM benefits;');
  const addMeaning = db.prepare('INSERT INTO meanings (hadith_id, seq, term, meaning) VALUES (?, ?, ?, ?)');
  const addBenefit = db.prepare('INSERT INTO benefits (hadith_id, seq, text) VALUES (?, ?, ?)');

  for (const { id } of db.prepare('SELECT id FROM hadith ORDER BY id').all()) {
    counts.hadith++;
    const oldId = ids.get(id);
    const row = oldId ? sharh.get(oldId) : undefined;
    if (!row) {
      counts.noV1++;
      continue;
    }
    const { meanings, benefits } = parseCommentary(row.sharh);
    if (shared.has(oldId)) {
      const score = (hadith) => meanings.filter((meaning) => hadith.text.includes(bare(meaning.term))).length;
      const best = shared.get(oldId).reduce((a, b) => (score(b) > score(a) ? b : a));
      if (best.id !== id) {
        counts.split++;
        continue;
      }
    }
    meanings.forEach((meaning, i) => addMeaning.run(id, i + 1, meaning.term, meaning.meaning));
    benefits.forEach((benefit, i) => addBenefit.run(id, i + 1, benefit));
    if (meanings.length) counts.withMeanings++;
    if (benefits.length) counts.withBenefits++;
    counts.meanings += meanings.length;
    counts.benefits += benefits.length;
  }

  // The app shows the commentary of a database marked this way as v1's, not reviewed.
  db.prepare("INSERT OR REPLACE INTO info (key, value) VALUES ('preview', 'v1-commentary')").run();
  return counts;
}

// Built in a temporary file and moved into place only once it is whole, so a failed run leaves no half-made preview
// for Metro to bundle.
function main() {
  const v1 = new DatabaseSync(V1, { readOnly: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const temp = `${OUT}.tmp`;
  fs.copyFileSync(SOURCE, temp);
  let counts;
  try {
    const db = new DatabaseSync(temp);
    db.exec('BEGIN');
    counts = build(db, v1);
    db.exec('COMMIT; VACUUM;');
    db.close();
  } catch (error) {
    fs.rmSync(temp, { force: true });
    throw error;
  }
  fs.renameSync(temp, OUT);
  fs.writeFileSync(STAMP, `${sha256(SOURCE)}\n`);

  console.log(`Wrote ${path.relative(ROOT, OUT)} with v1's commentary:`);
  console.log(`  ${counts.withMeanings} of ${counts.hadith} hadith have word meanings (${counts.meanings} in all)`);
  console.log(`  ${counts.withBenefits} of ${counts.hadith} hadith have benefits (${counts.benefits} in all)`);
  console.log(`  ${counts.noV1} hadith have no v1 commentary to take`);
  console.log(`  ${counts.split} hadith share a v1 hadith with another, which has its commentary`);
}

main();
