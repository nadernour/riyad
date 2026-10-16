# Riyad al-Salihin

A free, offline app for reading Imam al-Nawawi's *Riyad al-Salihin* (رياض الصالحين), one hadith per page. Each hadith comes with its word meanings and benefits from *Nuzhat al-Muttaqin* (نزهة المتقين شرح رياض الصالحين).

## Status

- **v1** (branch `master`, tag `v1.0.0`) is the Android app on [Google Play](https://play.google.com/store/apps/details?id=com.nad.riyadalsalheen), written in Kotlin with Jetpack Compose. Its text was taken from a web page and has many mistakes.
- **v2** (this branch, `v2`) is in planning. It has two goals:
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
5. Search by word, ignoring tashkeel, or by hadith number
6. Browse by book and chapter
7. Font size (14–30), dark mode, and reopening at the last hadith read
8. Share a hadith as text
9. About screen with contact by email
10. Fully offline, with no account, ads or tracking

Fixes:

- **Search also covers the word meanings and benefits**, and highlights what it found. v1's search hint promises the commentary, but v1 only searches the hadith text.
- **Theme setting: System, Light or Dark.** v1's toggle means "the opposite of the phone's setting", so with it on, the app turns light when the phone turns dark at night.
- **The Prophet's words stand out from the rest of the hadith.** v1 marks them, but its hadith font (Amiri) has no semi-bold, so they look the same as the Companion's words.
- **Sharing includes the hadith number.**

New:

- **Tap an explained word** in the hadith to see its meaning.
- **Tap a narrator's name** in the hadith to read their biography.

## Content

The printed book is the reference. Every word in the app is either confirmed by independent sources or checked on a zoomed scan of the page. Misprints in the book are never fixed silently: a correction is stored next to the printed text, with its reason.

### Sources

- **The v1 database** (`v1/app/src/main/assets/databases/riyad_salheen.db`) has 20 books, 366 chapters and 1,893 hadith. The hadith text is fully vocalized, and the commentary is one text field per hadith. Its tags come from the colors of the web page the text was taken from:

  | Tag | In the hadith text | In the commentary |
  |---|---|---|
  | `<p0>` | the Prophet's words | the headings لغة الحديث and أفاد الحديث |
  | `<p1>` | other people's words, such as the Companion's account | the word being explained |
  | `<p2>` | a word Nawawi explains after the hadith, e.g. «ذروة الجبل» in hadith 30 | a few stray uses |
  | `<bullet>` | | a list item |

- **The scans of *Nuzhat al-Muttaqin*** (Mu'assasat al-Risala, Beirut, 14th edition, 1407 AH / 1987): one PDF of 1,433 scanned pages holding both volumes. About 1,270 of them are hadith and commentary, followed by the narrator biographies and indexes.
- **Machine-OCR text of the same PDF**, one page per `PAGE_SEPARATOR`, so text page *n* is PDF page *n*. It is a second, independent reading, with its own mistakes, especially in digits. [aljam3.com](https://aljam3.com/6507/17722/1) shows each page with this text.
- **sunnah.com's Riyad al-Salihin**, through [hadith-json](https://github.com/AhmedBaset/hadith-json), is a check on the letters only. It has almost no tashkeel, and that dataset's numbering doesn't follow the book's.
- **Hadith collections with tashkeel** ([hadith-api](https://github.com/fawazahmed0/hadith-api), [Open-Hadith-Data](https://github.com/mhashim6/Open-Hadith-Data)) check the hadith text's tashkeel wherever the wording matches.

### Steps

1. **Audit the v1 text.** Check 30 random hadith, text and commentary, against the scans, and count the mistakes by kind. This shows where v1's mistakes are, and these 30 hadith become the test set for the steps below.
2. **Convert the v1 database** into the new format (below). This is mechanical: the tags become fields and speaker roles. The app is built on this data while the checking runs.
3. **Number the hadith as printed.** Match each hadith to its number and page in the book. Where v1 numbers a hadith differently, keep v1's number in `old_id`.
4. **Check the hadith text.** It isn't transcribed, because v1 already has it with tashkeel:
   - **Letters:** compare v1's text with sunnah.com and with aljam3's reading of the page. Words that all three agree on are accepted. For the rest, a zoomed crop of the scan decides.
   - **Tashkeel:** compare with the collections wherever the wording matches. Differences go to the scan.
   - **Explained words:** every word under لغة الحديث should be found in the hadith. One that isn't gets checked: either the printed text differs from ours there, or the word has to be matched by hand (e.g. «الهجرة» explains «هجرته»).
5. **Transcribe the word meanings and benefits** from the scans, page by page, in short Claude Code sessions, with a pipeline adapted from the owner's azkar project.
   - v1's commentary and aljam3's reading are the cross-checks. Words that all readings agree on are accepted, and every disagreement is checked on a zoomed crop.
   - A pilot on about 20 pages comes first. It compares two ways of working on the step-1 test set: reading every word, or reading only the disputed ones. The rest of the book uses whichever is more accurate for its cost.
   - The rules will be in `docs/transcription.md`, written before the pilot.
6. **Transcribe the narrator biographies** from the end of the book the same way. v1 doesn't have them, so aljam3's reading is the only cross-check. Each biography is then linked to the narrator's name in every hadith that names them. Names the tool can't match (a kunya, or a name written differently) are linked by hand.
7. **Owner review.** Questions the checks can't settle are listed per book (كتاب) for the owner to decide.

### Format

The source of truth is JSON in `content/`, one file per book (كتاب), so every change can be reviewed in git. A build script turns it into the SQLite database that ships with the app, with full-text search.

Each hadith has these fields:

| Field | Content |
|---|---|
| `id` | The hadith number printed in the book. It never changes once released, so content fixes never break users' bookmarks |
| `old_id` | v1's number for this hadith, if different. Used to carry users' bookmarks over |
| `book`, `chapter` | The book (كتاب) and chapter (باب) it belongs to |
| `page` | The PDF page where it starts. The PDF holds both volumes, so its page numbers are unambiguous; the printed ones restart in volume 2 |
| `title` | The short title shown above it. Taken from v1; it isn't in the book |
| `matn` | The hadith text as a list of pieces, each with a role: `narration`, `prophet` (the Prophet's words), `speech` (other people's words) or `gloss` (a word Nawawi explains) |
| `meanings` | A list of `{term, meaning}` as printed. Each term is linked to its words in the hadith for the tap feature |
| `narrators` | The narrators named in the hadith who have a biography: each one's `id` in `content/narrators.json`, linked to their name in the hadith text |
| `benefits` | A list of items as printed |
| `shared_with` | When one commentary is printed for several hadith (e.g. «أفاد الحديثان»), the hadith it covers. It is shown with each of them |
| `corrections` | Misprints found in the book: the printed words, the correction and the reason. The printed text is kept |
| `notes` | English notes from the checking |

The narrator biographies are in `content/narrators.json`. Each has an `id`, the `name` as printed (with the kunya, if the book gives one), the `biography` as printed, its `page`, and any `corrections` and `notes`.

**Search:** every text also has a simplified copy (tashkeel removed, أ/إ/آ → ا, ة → ه, ى → ي). The app must simplify the search query exactly as the build script does, and shared test cases keep the two in step.

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

- [x] Create branch `v2` and write this plan
- [x] Tag the commit that is live on Google Play (it is tagged `v1.0.0`)
- [x] Move v1 into `v1/`, and get the book's PDF and OCR text
- [ ] Content step 1: audit 30 hadith
- [ ] Content step 2: convert the v1 database, and write the build script for the app's database
- [ ] Content steps 3–4: number the hadith as printed and check the hadith text
- [ ] Write `docs/transcription.md`, run the 20-page pilot, then transcribe the commentary (content step 5)
- [ ] Transcribe the narrator biographies and link them to the hadith (content step 6)
- [ ] Build the Expo app with v1's features, the fixes, tap-a-word and tap-a-narrator, on the converted data (alongside the transcription)
- [ ] Write the native module that carries v1 users' data over
- [ ] Release v2 on Android and iPhone, with the checked hadith text, the narrator biographies and v1's commentary
- [ ] Replace the commentary with the checked one, book by book, in app updates

## Repository layout

Now:

```
v1/                    the v1 Android app (Kotlin, Jetpack Compose), kept for reference until v2 ships
v1/app/src/main/assets/databases/riyad_salheen.db   v1's database, an input to the pipeline
v1/dp_update/          v1's Python script for the database
v1/docs/screenshots/   v1's screenshots
.cache/book/nuzhat.pdf    the book's scans (not in git)
.cache/aljam3/nuzhat.txt  the OCR text of the scans (not in git)
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

Both files come from the [waqfeya-library dataset](https://huggingface.co/datasets/ieasybooks-org/waqfeya-library) on Hugging Face (MIT license), the same files aljam3 serves. The book is in the folder `2ـ 213.6 (230) المسانيد الأخرى والجوامع/01433ـ نزهة المتقين شرح رياض الصالحين --- مصطفى سعيد الخن، مصطفى البغا، محي الدين مستو، علي الشربجي، محمد أمين لطفي.PDF/`. Download `الكتاب.pdf` from that folder under `pdf/` to `.cache/book/nuzhat.pdf`, and `الكتاب.txt` from the same folder under `txt/` to `.cache/aljam3/nuzhat.txt`. You can also use the download buttons on the [aljam3 page](https://aljam3.com/6507/17722/1).

## Building v1

You need Android Studio Ladybug or newer, JDK 11 and Android SDK 36. Open `v1/` as the project, and put `local.properties` (SDK path and signing settings) in `v1/`.

```sh
cd v1
./gradlew assembleDebug        # debug APK
./gradlew testDebugUnitTest    # unit tests
```

## Contributing

Before starting on something, open an issue to say what you'd like to work on. Keep scans, page images and other downloads in `.cache/`, never in git.

## Credits and license

- *Riyad al-Salihin*, Imam Yahya ibn Sharaf al-Nawawi (d. 676 AH)
- Word meanings and benefits: *Nuzhat al-Muttaqin Sharh Riyad al-Salihin* by Dr. Mustafa Said al-Khin, Dr. Mustafa al-Bugha, Muhyiddin Mistu, Ali al-Sharbaji and Muhammad Amin Lutfi (Mu'assasat al-Risala)
- Page scans and OCR text: [aljam3.com](https://aljam3.com)
- Cross-checks: [sunnah.com](https://sunnah.com) (through hadith-json), [hadith-api](https://github.com/fawazahmed0/hadith-api) (public domain, Unlicense) and [Open-Hadith-Data](https://github.com/mhashim6/Open-Hadith-Data) (ODbL)

The MIT License (see [LICENSE](LICENSE)) covers the code only. The text of *Nuzhat al-Muttaqin* belongs to its authors and publisher.

Developed by [Nader Hegazy](https://nadernour.github.io/).
