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

### Running it

It is developed on the branch `v2-app`, which merges into `v2`. You need Node.js 22.13 or newer (React Native 0.88's minimum); Xcode and CocoaPods for the iPhone simulator, or Android Studio for an Android emulator.

```sh
npm install
npx expo run:ios        # or run:android: builds a development app and starts it on a simulator or emulator
npx expo start          # later runs, once the development app is installed
npm test                # unit tests
npm run lint
npm run typecheck
```

The app forces right-to-left layout, which Expo Go doesn't apply reliably, so use a development build (`expo run:ios`, `expo run:android`, or `eas build --profile development`) rather than Expo Go. `ios/` and `android/` are generated from `app.json` by `npx expo prebuild` and are not in git: configure native settings in `app.json`, never in those folders.

Every build but the release is a test build, «رياض الصالحين (تجربة)» with the id `com.nad.riyadalsalheen.dev`, so it installs next to the app from the store instead of conflicting with it (`app.config.js`). Only `APP_VARIANT=production` gives the release id, name and link scheme: the `production` build profile in `eas.json` sets it, and `npm run submit` sets it for EAS Submit, whose profiles can't. Submit with `npm run submit`, not `eas submit` directly.

`npm run typecheck` checks twice: everything, and the app's code alone (`tsconfig.app.json`), without Node's types, so code that would only work in Node (`Buffer`, `fs`) fails before it reaches a phone.

**The app's data:**
- `src/db/content.ts` reads `riyad.db`. Its tests run the same SQL against the real file with Node's own SQLite, so `npm test` checks them whenever the database is rebuilt.
- On the phone, the copy of `riyad.db` is named after the bundled file's hash (`src/db/ContentProvider.tsx`). An app version with a new `riyad.db` copies it afresh and deletes the old copy, with no version number to raise by hand.
- At startup the app checks the database's `user_version`. A database with a schema the code isn't written for stops the app with an error, rather than showing wrong data.
- The user's bookmarks and settings are in their own `user.db` (`src/db/user.ts`), which content updates never touch. Its tables change only through a new entry at the end of `MIGRATIONS`.

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
- [ ] Build the Expo app with v1's features, the fixes, tap-a-word and tap-a-narrator, in phases on the branch `v2-app`:
  - [x] P0: project setup (Expo SDK 58, Expo Router with a drawer, forced right-to-left, Amiri and Cairo, Jest, ESLint, `eas.json`), checked on the iPhone simulator (2026-10-30)
  - [x] P1: data layer: open `database/riyad.db`, typed queries, the user's own database, and `simplify()` passing `database/simplify.json`, checked on the iPhone simulator and an Android phone (2026-10-30)
  - [x] P2: the reader: swipe between hadith, the text styled by speaker, word meanings and benefits, full screen, reopening at the last hadith, opening a hadith by link (`/?id=12`), checked on a Galaxy A17 (0.3% janky frames over 30 fast swipes) and the iPhone simulator (2026-10-30)
  - [ ] P3: browse by book and chapter, search, bookmarks
  - [ ] P4: settings (font size; System, Light or Dark), About, sharing
  - [ ] P5: polish and tests: accessibility, large fonts, dark mode, device tests, icon and splash screen
  - [ ] P6: internal test builds on Google Play and TestFlight, signed with v1's key
- [ ] Release v2 on Android and iPhone, once the content is done. It isn't released with v1's commentary, which is an edited version of the book's (the owner's decision, 2026-10-16).

## Repository layout

```
src/app/     the Expo app's screens (Expo Router: every file is a route, _layout.tsx files are navigators)
src/         the rest of the app: theme now, then the database queries, reader, search and settings
assets/      the app's icons, splash image and fonts (Amiri and Cairo, from v1)
book_data/   the content: the checked text of the book, the tools that check it and the docs of each step (book_data/README.md)
database/    the SQLite database the app reads, built from book_data/content/ (database/README.md)
v1/          the v1 Android app (Kotlin, Jetpack Compose), kept for reference until v2 ships; v1's database is an input to the content
CLAUDE.md    what a Claude Code session working here needs to know (book_data/CLAUDE.md for the content)
```

The Expo app (TypeScript) is at the root, next to these: `app.json`, `eas.json`, `package.json` and `metro.config.js`, which keeps Metro out of `book_data/` and `v1/`. Once v2 is released, `v1/` is deleted; it stays on `master` and the `v1.0.0` tag.

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
