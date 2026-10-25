# Riyad al-Salihin v2

- `README.md` has the plan and its status, the app's design and the repository layout. Read it first, and keep it current: it is the plan the collaborators work from, so update it whenever a step finishes or a decision changes.
- **Two people work on v2:** the owner checks the content, in `book_data/`, on Debian; a collaborator builds the app, on macOS. Their Claude Code sessions share only the repo, so keep what a session needs in these files, the READMEs or `book_data/docs/`, never in Claude Code's memory.
- **`book_data/`** holds the content: the source of truth, the tools that check it and the docs of each step. Its own `CLAUDE.md` and `README.md` say how to work there. It runs only on the owner's Debian machine, so its tools and commands need not work on macOS (the owner's decision, 2026-10-25). The app's must work on both.
- **`database/riyad.db`** is what the app reads. `book_data/tools/build_db.py` builds it from `book_data/content/`, so it is never edited by hand. `database/README.md` describes its tables.
- **Commit only when asked.**

## Decisions the owner has made

- **v2's text is the book's.** It is *Riyad al-Salihin* with *Nuzhat al-Muttaqin*'s word meanings and benefits. None of v1's commentary is used: the audit showed it is an edited version of the book's, with some meanings changed. v2 isn't released with v1's commentary, not even for a while.
- **The order is content, then the app, then the release.** Getting the content right comes first, and a late release is fine, so release timing isn't a trade-off to raise. The collaborator builds the app meanwhile, from the database as the content stands (2026-10-25).
- **The app is React Native with Expo**, so it runs on Android and iPhone, and EAS builds the iPhone app without a Mac.
- **v1 stays on `master`**, tagged `v1.0.0` (live on Google Play). v2 is developed on the branch `v2`.
- **v1's signing key `v1/riyad_keystore.jks` is committed on purpose**, and stays in the repo: don't suggest removing it. Its passwords are in `v1/local.properties`, which is not in git (ask the owner).
