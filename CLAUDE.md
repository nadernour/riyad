# Riyad al-Salihin v2

- `README.md` has the plan and its status, the app's design and the repository layout. Read it first, and keep it current: it is the plan the collaborators work from, so update it whenever a step finishes or a decision changes.
- **Two people work on v2:** the owner checks the content, in `book_data/`, on Debian; a collaborator builds the app, on macOS. Their Claude Code sessions share only the repo, so keep what a session needs in these files, the READMEs or `book_data/docs/`, never in Claude Code's memory.
- **`book_data/`** holds the content: the source of truth, the tools that check it and the docs of each step. Its own `CLAUDE.md` and `README.md` say how to work there. It runs only on the owner's Debian machine, so its tools and commands need not work on macOS (the owner's decision, 2026-10-25). The app's must work on both.
- **`database/riyad.db`** is what the app reads. `book_data/tools/build_db.py` builds it from `book_data/content/`, so it is never edited by hand. `database/README.md` describes its tables.
- **The Expo app** is at the repo root (`src/app/` for screens, `src/` for the rest), developed on `v2-app`. It uses Expo SDK 58, newer than most training data: before using an Expo, EAS or React Native API, read the docs for that version (https://docs.expo.dev/versions/v58.0.0/, index at https://docs.expo.dev/llms.txt). Add packages with `npx expo install`, never `npm install <pkg>`, so versions match the SDK. Run `npm run lint`, `npm run typecheck` and `npm test` before calling app work done. The README's "Running it" says how to start it.
- **Commit only when asked.**

## Decisions the owner has made

- **v2's text is the book's.** It is *Riyad al-Salihin* with *Nuzhat al-Muttaqin*'s word meanings and benefits. None of v1's commentary is used: the audit showed it is an edited version of the book's, with some meanings changed. v2 isn't released with v1's commentary, not even for a while.
- **The hadith text is v1's, corrected to the book's.** Every letter, and every mark that conflicts with the book's, is the book's, and the words v1 leaves bare get the book's marks; v1's other marks, its spelling and its punctuation stay. Copying all of the book's marks, spelling and punctuation was weighed and dropped (2026-10-25): it would roughly double the usage per hadith, and what it adds is fuller vocalization, not correctness (`book_data/README.md`, step 4).
- **No backward compatibility with v1** (2026-10-25). v2 keeps v1's Google Play listing, package and key, so it reaches v1's users as an update, but v1 users' saved data (bookmarks, last hadith read, settings) isn't carried over. v2's spec builds on v1's: v1's code, in `v1/`, is the reference for how its features work.
- **The order is content, then the app, then the release.** Getting the content right comes first, and a late release is fine, so release timing isn't a trade-off to raise. The collaborator builds the app meanwhile, from the database as the content stands (2026-10-25).
- **The app is React Native with Expo**, so it runs on Android and iPhone, and EAS builds the iPhone app without a Mac.
- **v1 stays on `master`**, tagged `v1.0.0` (live on Google Play). v2 is developed on the branch `v2`.
- **v1's signing key `v1/riyad_keystore.jks` is committed on purpose**, and stays in the repo: don't suggest removing it. Its passwords are in `v1/local.properties`, which is not in git (ask the owner).
