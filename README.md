# Riyad al-Salihin

A free, offline app for reading Imam al-Nawawi's *Riyad al-Salihin* (رياض الصالحين), one hadith per page. Each hadith comes with its word meanings and benefits from *Nuzhat al-Muttaqin* (نزهة المتقين شرح رياض الصالحين).

## Status

- **v1** (branch `master`, tag `v1.0.0`) is the Android app on [Google Play](https://play.google.com/store/apps/details?id=com.nad.riyadalsalheen), written in Kotlin with Jetpack Compose. Its text came from the database of an abandoned app, [com.zad.riyadhsalheen](https://play.google.com/store/apps/details?id=com.zad.riyadhsalheen). The audit showed that its commentary is an edited version of the book's (see [book_data/docs/audit.md](book_data/docs/audit.md)).
- **v2** (this branch, `v2`) is under way: the text is being checked against the printed book (content step 4: 164 of the 1,898 hadith are checked), and the app can be started on a first build of its database (`database/`). It has two goals:
  1. Replace the text with one checked against the printed book.
  2. Rebuild the app in React Native with Expo, so that the same app runs on Android and iPhone.

The plan is below. Until the Expo app replaces it, the v1 code stays in `v1/`.

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

The printed book is the reference. Every word in the app is either confirmed by independent sources or checked on a zoomed scan of the page. Misprints in the book are never fixed silently: a correction is stored next to the printed text, with its reason. The app shows only the book's text: none of v1's commentary is kept (the owner's decision, 2026-10-16).

The content is checked in [book_data/](book_data/README.md), on the owner's Debian machine: its README has the sources, the steps and the tools, and `book_data/docs/` the method and rules of each step. `book_data/tools/build_db.py` builds the database the app reads from it, [database/riyad.db](database/README.md).

## The v2 app

- **React Native with Expo, in TypeScript:** one codebase for Android and iPhone. Expo's cloud build service (EAS) builds and submits the iPhone app without a Mac.
- **expo-sqlite** for the bundled database and its full-text search.
- **Arabic only, right to left,** with Amiri for the hadith text and Cairo for the interface, as in v1.
- **Room for tashkeel:** iOS clips the marks when the line height is too tight.

**Why not Kotlin Multiplatform?** It would keep about half of v1's code. But building and testing the iPhone app needs a Mac, and the owner works on Linux. Also, on iOS it draws its own text instead of using the phone's, which matters in an app that is all text.

### The database

The app reads all its text from `database/riyad.db`, which [database/README.md](database/README.md) describes: its tables, the common queries, how search must simplify the query, and how to bundle it with Expo. It holds every hadith with its text as the content now stands, so the app can be built while the content is finished. Each new build replaces the file. The word meanings, benefits and narrators have their tables already, empty until content steps 5 and 6.

**User data** (bookmarks, last hadith read, settings) is stored apart from the database, so content updates never touch it.

### Releasing

v2 replaces v1 on the same Google Play listing, so v1's users get it as an update, and the listing keeps its installs and ratings:

- **Same package and key:** package `com.nad.riyadalsalheen` and a `versionCode` above v1's. It is signed with v1's key, `v1/riyad_keystore.jks`, whose passwords are in `v1/local.properties` (not in git). EAS is given this keystore.
- **v1's saved data isn't carried over** (the owner's decision, 2026-10-25: no backward compatibility). v1's bookmarks, last hadith read and settings stay behind, so users who update start afresh: the release notes say so.
- **Careful release:** internal testers first, then a staged rollout. v1 stays on `master` (tag `v1.0.0`) to roll back to.

On iPhone, this needs an Apple Developer account ($99 a year), and the app goes through TestFlight before the App Store.

## Plan

The order is: make the content clean, then build the app, then ship. The app is built meanwhile from the database as the content stands, and the release waits for the content.

- [x] Create branch `v2` and write this plan
- [x] Tag the commit that is live on Google Play (it is tagged `v1.0.0`)
- [x] Move v1 into `v1/`, and get the book's PDF and OCR text
- [x] Content step 1: audit 30 hadith ([book_data/docs/audit.md](book_data/docs/audit.md))
- [x] Content step 2: convert the v1 database (`book_data/content/hadith/`)
- [x] Content step 3: number the hadith as printed ([book_data/docs/numbering.md](book_data/docs/numbering.md))
- [ ] Content step 4: check the hadith text ([book_data/docs/matn.md](book_data/docs/matn.md); 164 of the 1,898 hadith are checked)
- [ ] Write `book_data/docs/transcription.md`, run the pilot on the audit's pages, then transcribe the commentary (content step 5)
- [ ] Transcribe the narrator biographies and link them to the hadith (content step 6)
- [ ] Owner review of the questions the checks couldn't settle (content step 7)

The app:

- [x] Move the content pipeline into `book_data/`, so the repository's root is the app's (2026-10-25)
- [x] Write the build script that turns the content into the app's database, `book_data/tools/build_db.py`: a first build for the app to start on (2026-10-25). The commentary and narrators come with content steps 5 and 6.
- [ ] Build the Expo app with v1's features, the fixes, tap-a-word and tap-a-narrator
- [ ] Release v2 on Android and iPhone, once the content is done. It isn't released with v1's commentary, which is an edited version of the book's (the owner's decision, 2026-10-16).

## Repository layout

```
book_data/   the content: the checked text of the book, the tools that check it and the docs of each step (book_data/README.md)
database/    the SQLite database the app reads, built from book_data/content/ (database/README.md)
v1/          the v1 Android app (Kotlin, Jetpack Compose), kept for reference until v2 ships; v1's database is an input to the content
CLAUDE.md    what a Claude Code session working here needs to know (book_data/CLAUDE.md for the content)
```

The Expo app (TypeScript) goes at the root, next to these. Once v2 is released, `v1/` is deleted; it stays on `master` and the `v1.0.0` tag.

## Building v1

You need Android Studio Ladybug or newer, JDK 11 and Android SDK 36. Open `v1/` as the project, and put `local.properties` (SDK path and signing settings) in `v1/`.

```sh
cd v1
./gradlew assembleDebug        # debug APK
./gradlew testDebugUnitTest    # unit tests
```

## Contributing

Before starting on something, open an issue to say what you'd like to work on. Keep scans, page images and other downloads in `book_data/.cache/`, never in git. Decisions go in git: under `book_data/content/`, or in `book_data/docs/` with their reasons. `CLAUDE.md` gives Claude Code what it needs to work here.

## Credits and license

- *Riyad al-Salihin*, Imam Yahya ibn Sharaf al-Nawawi (d. 676 AH)
- Word meanings and benefits: *Nuzhat al-Muttaqin Sharh Riyad al-Salihin* by Dr. Mustafa Said al-Khin, Dr. Mustafa al-Bugha, Muhyiddin Mistu, Ali al-Sharbaji and Muhammad Amin Lutfi (Mu'assasat al-Risala)
- Page scans and OCR text: [aljam3.com](https://aljam3.com)
- Cross-checks: [sunnah.com](https://sunnah.com) (through hadith-json) and [hadith-api](https://github.com/fawazahmed0/hadith-api) (public domain, Unlicense)

The MIT License (see [LICENSE](LICENSE)) covers the code only. The text of *Nuzhat al-Muttaqin* belongs to its authors and publisher.

Developed by [Nader Hegazy](https://nadernour.github.io/).
