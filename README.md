# Riyad al-Salihin

A free, offline app for reading Imam al-Nawawi's *Riyad al-Salihin* (رياض الصالحين), one hadith per page. Each hadith comes with its word meanings and benefits from *Nuzhat al-Muttaqin* (نزهة المتقين شرح رياض الصالحين).

## Status

- **v1** (branch `master`, tag `v1.0.0`) is the Android app on [Google Play](https://play.google.com/store/apps/details?id=com.nad.riyadalsalheen), written in Kotlin with Jetpack Compose. Its text came from the database of an abandoned app, [com.zad.riyadhsalheen](https://play.google.com/store/apps/details?id=com.zad.riyadhsalheen). The audit showed that its commentary is an edited version of the book's (see [docs/audit.md](docs/audit.md)).
- **v2** (this branch, `v2`) is under way: the text is being checked against the printed book (content step 4). It has two goals:
  1. Replace the text with one checked against the printed book.
  2. Rebuild the app in React Native with Expo, so that the same app runs on Android and iPhone.

The plan is below. Until the Expo app replaces it, this branch still holds the v1 code.

## What the app shows

One hadith per page, in the book's order. Each hadith has three parts:

| Part | Source |
|---|---|
| **The hadith** (المتن): the narrator, the hadith, Nawawi's source line (e.g. «متفق عليه»), and his explanation of rare words where he gives one | *Riyad al-Salihin*, Imam Yahya ibn Sharaf al-Nawawi (d. 676 AH) |
| **Word meanings** (لغة الحديث) | *Nuzhat al-Muttaqin* |
| **Benefits** (أفاد الحديث), including any «تنبيه» note printed with them | *Nuzhat al-Muttaqin* |

Tapping a narrator's name in the hadith opens their biography, from the narrator biographies at the end of *Nuzhat al-Muttaqin*.

The book and chapter titles are shown above each hadith, as in v1. Nothing else from the books goes into the app: no chapter introductions or verses, and no footnotes.

## Features

v2 keeps everything v1 does:

1. One hadith per page; swipe to the next or previous hadith
2. Tap the page for full-screen reading
3. Above each hadith: the book (كتاب) and chapter (باب) titles, the hadith number and a short title
4. Bookmarks, newest first, with the latest ones in the side menu; remove one or clear all, with a confirmation
5. Search the hadith text by word, ignoring tashkeel, or by hadith number
6. Browse by book and chapter
7. Font size (14–30), dark mode, and reopening at the last hadith read
8. Share a hadith as text
9. About screen with contact by email
10. Fully offline, with no account, ads or tracking

Fixes:

- **Theme setting: System, Light or Dark.** v1's toggle means "the opposite of the phone's setting", so with it on, the app turns light when the phone turns dark at night.
- **The Prophet's words stand out from the rest of the hadith.** v1 marks them, but its hadith font (Amiri) has no semi-bold, so they look the same as the Companion's words.
- **Sharing includes the hadith number.**

New:

- **Tap an explained word** in the hadith to see its meaning.
- **Tap a narrator's name** in the hadith to read their biography.

## Content

The printed book is the reference. Every word in the app is either confirmed by independent sources or checked on a zoomed scan of the page. Misprints in the book are never fixed silently: a correction is stored next to the printed text, with its reason.

The app shows only the book's text. v1's additions to the commentary (extra word meanings and benefits, grading notes) are not kept (the owner's decision, 2026-10-16).

### Sources

- **The v1 database** (`v1/app/src/main/assets/databases/riyad_salheen.db`) has 20 books, 366 chapters and 1,893 hadith. The hadith text is vocalized, though about one word in eight has no mark at all, and the commentary is one text field per hadith. Its tags come from the colors of the HTML the text was stored as:

  | Tag | In the hadith text | In the commentary |
  |---|---|---|
  | `<p0>` | the Prophet's words | the headings لغة الحديث and أفاد الحديث |
  | `<p1>` | other people's words, such as the Companion's account | the word being explained |
  | `<p2>` | a word Nawawi explains after the hadith, e.g. «ذروة الجبل» in hadith 30 | a few stray uses |
  | `<bullet>` | | a list item |

  The audit (step 1) showed two problems:
  - **The commentary is not the book's.** Its matn has few mistakes, but its commentary is an edited version of Nuzhat's: reworded, extended, cut, and in places changed in meaning.
  - **Its numbering drifts.** By the end of the book, v1 is 5 behind the book's numbers.

- **The scans of *Nuzhat al-Muttaqin*** (Mu'assasat al-Risala, Beirut, 14th edition, 1407 AH / 1987): one PDF of 1,433 scanned pages holding both volumes. About 1,270 of them are hadith and commentary, followed by the narrator biographies and indexes.
- **Machine-OCR text of the same PDF**, one page per `PAGE_SEPARATOR`, so text page *n* is PDF page *n*. It is a second, independent reading. For the commentary it is close to the print, but it misreads the ﷺ glyph and digits, and its tashkeel on the matn is unreliable. [aljam3.com](https://aljam3.com/6507/17722/1) shows each page with this text.
- **sunnah.com's Riyad al-Salihin**, through [hadith-json](https://github.com/AhmedBaset/hadith-json), is a check on the letters only. It has almost no tashkeel, and that dataset's numbering doesn't follow the book's.
- **Hadith collections with tashkeel** ([hadith-api](https://github.com/fawazahmed0/hadith-api): the six books and the Muwatta) check the hadith text's tashkeel wherever the wording matches.
- **Tesseract** reads the pages again, keeping each word's position. It reads the vocalized matn poorly, but it finds where each matn is printed, so it can be cropped from the scan.

### Steps

1. **Audit the v1 text** (done; see [docs/audit.md](docs/audit.md)). 30 random v1 hadith were checked against the scans.
   - **Matn:** 7 have a v1 mistake, nearly all a single wrong tashkeel mark.
   - **Commentary:** 26 differ from the book, and 6 of those change what it says.
   - **Numbers:** only 2 have the book's number.

   The book's text for those 30 hadith is in `content/audit/`, as the test set for the steps below.
2. **Convert the v1 database** into the new format (below), as the base for steps 3 and 4 (done; `tools/convert_v1.py` writes `content/hadith/`). It brings over:
   - the matn, as pieces with speaker roles taken from v1's tags;
   - the short titles, the books and chapters, and v1's ids.

   v1's commentary isn't brought over. The salutation becomes the glyph ﷺ, as the book prints it. The tool checks that every word of v1's matn survives the conversion.
3. **Number the hadith as printed** (done; see [docs/numbering.md](docs/numbering.md)). Every hadith now has the book's number (1–1,898) and page, and every chapter the book's number. The places where v1 and the book don't line up one to one are in `content/numbering.json`: cross-references the book numbers, two merged v1 entries, a repeated text, and chapter 261, which v1 lacks. The mapping agrees with every number the OCR kept above a hadith, every numbered chapter heading, and the 30 audited hadith. v1's ids are kept in `old_id`. v1's short titles had slipped one entry out of step in places, so they were paired with their hadith again, and 8 titles were written for hadith without one.
4. **Check the hadith text** (in progress; see [docs/matn.md](docs/matn.md)). It isn't transcribed, because v1 already has it with tashkeel. Instead, every hadith is read against its matn on the scan, and v1's text is corrected to the book's:
   - **Doubts first.** `tools/matn.py` compares each matn with the OCR text of its pages, sunnah.com and the collections, and lists the words in doubt: other letters in the OCR text, marks no collection agrees with, words vocalized as nowhere in the collections, and text the book prints after v1's last word, such as Nawawi's explanation of a word, which v1 sometimes lacks. Before the rounds there were 5,775, in 1,559 of the 1,868 hadith left.
   - **Then the whole matn.** In short Claude Code rounds (`tools/long_run.sh`), each hadith is read against a crop of its matn on the scan, starting with its doubts, and every word changed is read on a zoom. The pilot on the audit's 30 hadith showed this is needed: the doubts missed 4 of the audit's differences, all case endings or wordings that no source contradicts.
   - **The book's wording is kept** where v1 follows another edition (e.g. «إلى الإسلام» for the book's «للإسلام»), unless it's a misprint. The book's single kasra where the grammar needs tanween («بن قيسِ») is a printing habit, so v1's tanween stays. Spelling that doesn't change the reading (مائة / مئة) stays as v1 has it.
   - **Words v1 leaves without tashkeel get the book's** (the owner's decision, 2026-10-22): 12,637 words, in 1,371 hadith. A word v1 marks in part keeps its marks unless one conflicts with the book's.
   - **Every decision is kept** in `content/matn/`, one file per book, so the step can be applied again after rebuilding `content/hadith/`.
5. **Transcribe the word meanings and benefits** from the scans, page by page, in short Claude Code sessions, with a pipeline adapted from the owner's azkar project. That project isn't in this repo. It transcribed a 470-page scanned book in rounds of 5 pages at low effort, with chapter reviews at xhigh. A round cost about $0.9 at API prices (4–10% of the 5-hour limit, under 1% of the weekly one), and a chapter review about $1.7.
   - The OCR text of each page is the draft. It is proofread against the scan, with doubtful words zoomed, and split into word meanings and benefits, including commentary shared by several hadith (`shared_with`). v1's commentary isn't used, even as a cross-check, because the audit showed it is a different text.
   - A pilot on the audit's pages comes first, scored against the book's text in `content/audit/`. The rest of the book follows once the pilot's error rate is acceptable.
   - The rules will be in `docs/transcription.md`, written before the pilot.
   - **Explained words:** every word under لغة الحديث should be found in the hadith. One that isn't gets checked: either the printed text differs from ours there, or the word has to be matched by hand (e.g. «الهجرة» explains «هجرته»).
6. **Transcribe the narrator biographies** from the end of the book the same way. v1 doesn't have them, so aljam3's reading is the only cross-check. Each biography is then linked to the narrator's name in every hadith that names them. Names the tool can't match (a kunya, or a name written differently) are linked by hand.
7. **Owner review.** Questions the checks can't settle are listed per book (كتاب) for the owner to decide.

### Format

The source of truth is JSON in `content/hadith/`, one file per book (كتاب), so every change can be reviewed in git. Each file holds the book's `title` and its `chapters`. Each chapter has the book's chapter `number`, its `title`, v1's `old_id`, and its `hadith`. When the content is done, a build script turns it into the SQLite database that ships with the app, with full-text search.

Each hadith has these fields:

| Field | Content |
|---|---|
| `id` | The hadith number printed in the book. It never changes once released, so content fixes never break users' bookmarks |
| `old_id` | v1's number for this hadith, if different. Used to carry users' bookmarks over |
| `book`, `chapter` | The book (كتاب) and chapter (باب) it belongs to |
| `page` | The PDF page where it starts. The PDF holds both volumes, and its pages match the printed page numbers |
| `title` | The short title shown above it. Taken from v1 (paired again in step 3); it isn't in the book. Titles written in step 3 say so in `notes` |
| `matn` | The hadith text as a list of pieces, each with a role: `narration`, `prophet` (the Prophet's words), `speech` (other people's words) or `gloss` (a word Nawawi explains) |
| `meanings` | A list of `{term, meaning}` as printed. Each term is linked to its words in the hadith for the tap feature |
| `narrators` | The narrators named in the hadith who have a biography: each one's `id` in `content/narrators.json`, linked to their name in the hadith text |
| `benefits` | A list of items as printed |
| `shared_with` | When one commentary is printed for several hadith (e.g. «أفاد الحديثان»), the hadith it covers. It is shown with each of them |
| `corrections` | Misprints found in the book: the printed words, the correction and the reason. The text shows the correction, and the printed words are kept here |
| `notes` | English notes from the checking |

The narrator biographies are in `content/narrators.json`. Each has an `id`, the `name` as printed (with the kunya, if the book gives one), the `biography` as printed, its `page`, and any `corrections` and `notes`.

**Search** covers the hadith text only, as in v1: not the word meanings, benefits or titles (the owner's decision, 2026-10-17). The hadith text also has a simplified copy (tashkeel removed, أ/إ/آ → ا, ة → ه, ى → ي). The app must simplify the search query exactly as the build script does, and shared test cases keep the two in step.

**User data** (bookmarks, last hadith read, settings) is stored apart from the content, so content updates never touch it.

## The v2 app

- **React Native with Expo, in TypeScript:** one codebase for Android and iPhone. Expo's cloud build service (EAS) builds and submits the iPhone app without a Mac.
- **expo-sqlite** for the bundled database and its full-text search.
- **Arabic only, right to left,** with Amiri for the hadith text and Cairo for the interface, as in v1.
- **Room for tashkeel:** iOS clips the marks when the line height is too tight.

**Why not Kotlin Multiplatform?** It would keep about half of v1's code and need no data migration. But building and testing the iPhone app needs a Mac, and the owner works on Linux. Also, on iOS it draws its own text instead of using the phone's, which matters in an app that is all text.

### Upgrading v1 users

v2 replaces v1 on the same Google Play listing, so existing users get it as an update:

- **Same package and key:** package `com.nad.riyadalsalheen` and a `versionCode` above v1's. It is signed with v1's key, `v1/riyad_keystore.jks`, whose passwords are in `v1/local.properties` (not in git). EAS is given this keystore.
- **Saved data is carried over.** v1 keeps it in Jetpack DataStore (`files/datastore/settings.preferences_pb`):
  - `bookmarks`: hadith numbers, comma-separated, newest first
  - `reading_progress`: the last hadith read
  - `font_size`
  - `SYSTEM_THEME`

  React Native can't read that file. A small native module reads it once on first launch, converts the numbers with `old_id`, and saves everything in v2's storage.
- **Careful release:** internal testers first, then a staged rollout. v1 stays on `master` (tag `v1.0.0`) to roll back to.

On iPhone, this needs an Apple Developer account ($99 a year), and the app goes through TestFlight before the App Store.

## Plan

The order is: make the content clean, then build the app, then ship.

- [x] Create branch `v2` and write this plan
- [x] Tag the commit that is live on Google Play (it is tagged `v1.0.0`)
- [x] Move v1 into `v1/`, and get the book's PDF and OCR text
- [x] Content step 1: audit 30 hadith ([docs/audit.md](docs/audit.md))
- [x] Content step 2: convert the v1 database (`content/hadith/`)
- [x] Content step 3: number the hadith as printed ([docs/numbering.md](docs/numbering.md))
- [ ] Content step 4: check the hadith text ([docs/matn.md](docs/matn.md); the pilot's 30 hadith are done)
- [ ] Write `docs/transcription.md`, run the pilot on the audit's pages, then transcribe the commentary (content step 5)
- [ ] Transcribe the narrator biographies and link them to the hadith (content step 6)
- [ ] Owner review of the questions the checks couldn't settle (content step 7)

Once the content is clean:

- [ ] Write the build script that turns `content/` into the app's database
- [ ] Build the Expo app with v1's features, the fixes, tap-a-word and tap-a-narrator
- [ ] Write the native module that carries v1 users' data over
- [ ] Release v2 on Android and iPhone. It isn't released with v1's commentary, which is an edited version of the book's (the owner's decision, 2026-10-16).

## Repository layout

Now:

```
v1/                    the v1 Android app (Kotlin, Jetpack Compose), kept for reference until v2 ships
v1/app/src/main/assets/databases/riyad_salheen.db   v1's database, an input to the pipeline
v1/dp_update/          v1's Python script for the database
v1/docs/screenshots/   v1's screenshots
CLAUDE.md              what a Claude Code session working here needs to know
tools/                 the content pipeline's Python scripts (setup below)
content/hadith/        the content, one JSON file per book (source of truth)
content/numbering.json where v1's hadith and chapters differ from the book's (step 3)
content/matn/          step 4: the decisions from checking each hadith's text against the scan
content/audit/         the v1 audit: the book's text for 30 v1 hadith and how v1 differs (the test set)
docs/audit.md          the audit's findings
docs/numbering.md      step 3: numbering, pages, chapters and titles
docs/matn.md           step 4: how the hadith text is checked, and the rules for the review rounds
.cache/                downloads and files the tools make again (not in git); nothing that can't be remade
.cache/book/nuzhat.pdf    the book's scans (not in git)
.cache/aljam3/nuzhat.txt  the OCR text of the scans (not in git)
.cache/sunnah/, .cache/hadith-api/   sunnah.com's Riyad al-Salihin and the collections, downloaded by the tools (not in git)
.cache/ocr/               Tesseract and its reading of the pages (not in git)
```

Planned:

```
src/        the v2 app (Expo, TypeScript)
content/    the checked content, one JSON file per book (source of truth)
tools/      Python scripts for the content pipeline
docs/       transcription rules and notes
.cache/     scans, page images, OCR text and downloads (not in git)
```

Once v2 is released, `v1/` is deleted; it stays on `master` and the `v1.0.0` tag.

### Getting the book

Both files come from the [waqfeya-library dataset](https://huggingface.co/datasets/ieasybooks-org/waqfeya-library) on Hugging Face (MIT license), the same files aljam3 serves. The book is in the folder `2ـ 213.6 (230) المسانيد الأخرى والجوامع/01433ـ نزهة المتقين شرح رياض الصالحين --- مصطفى سعيد الخن، مصطفى البغا، محي الدين مستو، علي الشربجي، محمد أمين لطفي.PDF/`. Download `الكتاب.pdf` from that folder under `pdf/` to `.cache/book/nuzhat.pdf`, and `الكتاب.txt` from the same folder under `txt/` to `.cache/aljam3/nuzhat.txt`. You can also use the download buttons on the [aljam3 page](https://aljam3.com/6507/17722/1). The tools download both on first use, and the cross-check sources too. `tools/ocr.py` fetches Tesseract into `.cache/ocr/` with `tools/fetch_ocr.sh` (Debian packages, nothing installed system-wide).

### Setting up (Linux or macOS)

You need Python 3.10 or newer and Tesseract. The matn check's long run also needs Claude Code, logged in to your Claude subscription.

- **macOS:** `brew install python tesseract`. The system `python3` (3.9) is too old, so make the venv with Homebrew's: `$(brew --prefix)/bin/python3 -m venv .venv`, in place of the first command below.
- **Debian or Ubuntu:** the system Python will do. Tesseract can be installed with apt; if it isn't, `tools/ocr.py` unpacks it into `.cache/ocr/` on first use, without installing anything system-wide.

```sh
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/matn.py compare   # first run: downloads the book and the sources, and reads every page with Tesseract
```

The first `compare` takes a while, because Tesseract reads the 1,278 hadith pages (10 minutes on the owner's 18 cores, longer on a laptop). After that it takes about two minutes, and the tools make it again whenever `tools/matn.py` has changed, e.g. after a pull. Everything it downloads or makes goes to `.cache/`, and every tool makes again what it needs if `.cache/` is empty.

### Content tools

```sh
.venv/bin/python tools/locate.py 500                # the PDF pages where v1 hadith 500 is printed
.venv/bin/python tools/render_pages.py 440 442      # page images, in .cache/pages/
.venv/bin/python tools/zoom.py 441 0.30 0.35        # a closer look at part of a page
.venv/bin/python tools/audit.py show 500            # v1's text against the OCR text of its pages
.venv/bin/python tools/audit.py summary             # the audit's totals
.venv/bin/python tools/numbering.py --check          # the hadith numbering against the numbers the OCR kept
.venv/bin/python tools/chapters.py                   # v1's chapters against the book's chapter headings
.venv/bin/python tools/convert_v1.py --force         # rebuild content/hadith/ from v1 (steps 2 and 3)...
.venv/bin/python tools/matn.py apply --all           # ...then apply step 4's decisions again
.venv/bin/python tools/ocr.py                        # Tesseract's reading of the hadith pages, with positions
.venv/bin/python tools/matn.py compare               # step 4: list the words in doubt in every matn not yet checked
.venv/bin/python tools/matn.py next                  # the next round's hadith (up to 12), with crops of the scan
.venv/bin/python tools/matn.py apply                 # apply content/matn/inbox.json
```

### The matn check's long run

Step 4's review is done in rounds (see [docs/matn.md](docs/matn.md)). `tools/long_run.sh` starts a fresh Claude Code session for each round (up to 12 hadith and 800 words of matn), on your Claude subscription, and waits out the usage limits between rounds:

```sh
nohup tools/long_run.sh >> .cache/long-run.log 2>&1 &     # start it; it keeps going after the terminal closes
tail -F .cache/long-run.log                                # follow it: each round's cost, limits used and summary
pkill -f '[t]ools/long_run.sh'; pkill -f '[c]laude -p Do one round'   # stop it
```

On macOS, start it with `nohup caffeinate -i tools/long_run.sh >> .cache/long-run.log 2>&1 &`, so the Mac doesn't go to sleep while it runs. Closing the lid still puts it to sleep.

Look at the first rounds' changes (`git diff content/`) before leaving it unattended. The rounds don't commit, so commit `content/` now and then. A round that finds a rule or a tool wrong says so in its summary in the log. The log isn't in git, so act on it in `docs/` or `tools/`.

### Working together

Only one person runs the long run at a time, because each round takes the next hadith not yet checked. When you stop it:

1. If `content/matn/inbox.json` is there (a round was stopped before applying its decisions), run `.venv/bin/python tools/matn.py apply`. The inbox isn't in git.
2. Commit and push `content/`.

The other person pulls before starting it again.

## Building v1

You need Android Studio Ladybug or newer, JDK 11 and Android SDK 36. Open `v1/` as the project, and put `local.properties` (SDK path and signing settings) in `v1/`.

```sh
cd v1
./gradlew assembleDebug        # debug APK
./gradlew testDebugUnitTest    # unit tests
```

## Contributing

Before starting on something, open an issue to say what you'd like to work on. Keep scans, page images and other downloads in `.cache/`, never in git. Decisions go in git: under `content/`, or in `docs/` with their reasons. `CLAUDE.md` gives Claude Code what it needs to work here.

## Credits and license

- *Riyad al-Salihin*, Imam Yahya ibn Sharaf al-Nawawi (d. 676 AH)
- Word meanings and benefits: *Nuzhat al-Muttaqin Sharh Riyad al-Salihin* by Dr. Mustafa Said al-Khin, Dr. Mustafa al-Bugha, Muhyiddin Mistu, Ali al-Sharbaji and Muhammad Amin Lutfi (Mu'assasat al-Risala)
- Page scans and OCR text: [aljam3.com](https://aljam3.com)
- Cross-checks: [sunnah.com](https://sunnah.com) (through hadith-json) and [hadith-api](https://github.com/fawazahmed0/hadith-api) (public domain, Unlicense)

The MIT License (see [LICENSE](LICENSE)) covers the code only. The text of *Nuzhat al-Muttaqin* belongs to its authors and publisher.

Developed by [Nader Hegazy](https://nadernour.github.io/).
