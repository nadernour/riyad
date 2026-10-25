# The app's database

`riyad.db` is the SQLite database the app reads. Everything the app shows from the books is in it, and nothing else is. It is built from the checked content in `book_data/` by `book_data/tools/build_db.py` (see "Building it" below), so it is never edited by hand.

## What it holds now

| | |
|---|---|
| Books and chapters | The 20 books (كتاب) and their 367 chapters (باب), with v1's titles. A pass after content step 4 corrects their typos. |
| Hadith | All 1,898, with the book's numbers, v1's short titles and the page where each starts. |
| Hadith text | 172 hadith have been checked against the printed book. The rest have v1's text, which content step 4 is checking now. |
| Speaker roles | v1's, not checked yet, so some pieces have the wrong role until a pass after step 4. |
| Word meanings, benefits, narrators | Empty tables, filled when content steps 5 and 6 transcribe them. |

Each new build replaces the file, and the `info` table says which build it is. Build every screen to work with what's there: a hadith with no word meanings or benefits yet shows nothing for them.

## Tables

`PRAGMA user_version` is the schema version, now 1. It rises whenever the tables change.

**`info`**: `key` and `value` (text):

| key | value |
|---|---|
| `schema` | The schema version, as in `user_version` |
| `content` | A short hash of the content it was built from: it changes whenever the content does |
| `hadith` | The number of hadith, 1898 |
| `matn_checked` | How many hadith texts have been checked against the printed book |

**`books`**

| Column | |
|---|---|
| `id` | 1–20, in the book's order |
| `title` | The book's title, e.g. «كتاب الأدب» |

**`chapters`**

| Column | |
|---|---|
| `id` | The book's chapter number, 1–372, numbered through the whole book. The few chapters that have no numbered hadith, only verses, aren't included, so some numbers are missing. |
| `book_id` | Its book |
| `title` | The chapter's title, e.g. «التوبة». v1's titles leave out the word «باب». |

**`hadith`**

| Column | |
|---|---|
| `id` | The hadith number printed in the book, 1–1898, with no gaps. It never changes, so bookmarks can store it. |
| `book_id`, `chapter_id` | Its book and chapter |
| `title` | The short title shown above it. It comes from v1; the book doesn't have one. |
| `page` | The page of the printed book where it starts |
| `old_id` | v1's id for it, or `NULL` for the 4 hadith v1 lacks |
| `search_text` | The text, simplified for search (see "Search") |

**`matn_pieces`**: the hadith text, as pieces in reading order, each with its speaker.

| Column | |
|---|---|
| `hadith_id`, `seq` | The hadith, and the piece's place in it: 1, 2, 3, … |
| `role` | `narration`: the narrator's account. `prophet`: the Prophet's words, which the app sets apart. `speech`: other people's words. `gloss`: a word Nawawi explains after the hadith. |
| `text` | The piece's text. Joined in order, the pieces make the whole text, with its spaces and punctuation; a `\n` starts a new line. |

**`meanings`**: the word meanings (لغة الحديث), in printed order: `hadith_id`, `seq`, `term` and `meaning`. Empty for now.

**`benefits`**: the benefits (أفاد الحديث), in printed order: `hadith_id`, `seq` and `text`. Empty for now.

**`narrators`**: the narrator biographies: `id`, `name`, `biography` and `page`. Empty for now.

How a term is linked to its words in the text (tap a word) and a narrator to their name (tap a narrator) comes with content steps 5 and 6. They will most likely be ranges of the text, so a renderer that can style any range of a hadith's text, not just whole pieces, will take them without a rewrite.

**`v1_ids`**: every v1 hadith id, 1–1893, with the hadith to open for it (`v1_id`, `hadith_id`), to carry v1 users' bookmarks and last hadith read over (see "Upgrading v1 users" in the root README). Where one v1 entry holds two printed hadith, it opens the first, and v1's one entry the book doesn't number opens the hadith before it.

**`hadith_search`**: a full-text index (SQLite FTS5) of `hadith.search_text`. Its `rowid` is the hadith's `id`.

## Common queries

```sql
-- a hadith, with the titles shown above it
SELECT h.id, h.title, b.title AS book, c.title AS chapter
FROM hadith h JOIN books b ON b.id = h.book_id JOIN chapters c ON c.id = h.chapter_id
WHERE h.id = ?;

-- its text
SELECT role, text FROM matn_pieces WHERE hadith_id = ? ORDER BY seq;

-- browsing: a book's chapters, each with its first hadith
SELECT c.id, c.title, min(h.id) AS first FROM chapters c JOIN hadith h ON h.chapter_id = c.id
WHERE c.book_id = ? GROUP BY c.id ORDER BY c.id;
```

The next and previous hadith are `id + 1` and `id - 1`.

## Search

v1 searches the hadith text for any part of a word, ignoring the tashkeel, or finds a hadith by its number. v2 does the same, and also ignores the forms of alif, ta marbuta and alif maqsura:

1. A query of digits only opens the hadith with that number.
2. Otherwise, simplify the query (below). If it has 3 letters or more, search with it in double quotes, which finds it anywhere in a text, even inside a word, as v1 does:

   ```sql
   SELECT rowid FROM hadith_search WHERE hadith_search MATCH '"' || ? || '"' ORDER BY rowid LIMIT 100;
   ```

   `SELECT id FROM hadith WHERE search_text LIKE '%' || ? || '%' ORDER BY id LIMIT 100` gives the same results, more slowly. expo-sqlite has FTS5 on Android and iPhone, but not on web.

The query must be simplified exactly as the build script simplifies the text (`simplify` in `book_data/tools/arabic.py`). [`simplify.json`](simplify.json) has the test cases, each an input and the output expected: run them in the app's tests. In TypeScript:

```ts
// The same steps as simplify() in book_data/tools/arabic.py; database/simplify.json has the test cases.
export function simplify(text: string): string {
  return text
    .replace(/ﷺ/g, ' صلى الله عليه وسلم ') // the salutation ﷺ, written out
    .replace(/[ؐ-ًؚ-ٰٟۖ-ۭـ]/g, '') // tashkeel and tatweel
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .replace(/[^ء-ي]+/g, ' ') // anything else but letters: one space
    .trim();
}
```

`search_text` has fewer characters than the text, so a match's position in it isn't its position in the text. To show where a match is, simplify the text word by word.

## Using it in the Expo app

- **Bundle it as an asset.** Metro bundles a `.db` file only if `db` is in its asset extensions, in `metro.config.js`: `config.resolver.assetExts.push('db')`.
- **Open it with expo-sqlite's `SQLiteProvider`**, which copies it into the app's storage on first launch: `<SQLiteProvider databaseName="riyad.db" assetSource={{ assetId: require('<path to>/database/riyad.db') }}>`.
- **Keep the user's data out of it.** Bookmarks, the last hadith read and the settings go in their own storage. Then a new version of the app can simply replace the database, e.g. with `assetSource`'s `forceOverwrite: true` when the app's version changes.
- **Fonts.** The text writes the salutation as the ligature ﷺ (U+FDFA), so check that the hadith font draws it. The text is fully vocalized: leave room for the marks above and below each line (iOS clips them when the line height is tight).
- **If the Expo project is at the root of this repository,** keep Metro out of `book_data/` (its `.cache/` holds hundreds of megabytes of page images) and `v1/`, with `resolver.blockList`.

## Building it

The owner builds it, from `book_data/` on the owner's machine:

```sh
.venv/bin/python tools/build_db.py
```

It is made anew each time, and the same content makes the same file. It is committed so that the app can be built without the content tools. Each commit of it adds its whole size to the repository, so it is built again when the app should get the latest content, not after every change.
