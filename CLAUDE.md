# Riyad al-Salihin v2

- `README.md` has the plan, its status, the content format, the setup and the tools. Read it first, and keep it current: it is the plan the collaborators work from, so update it whenever a step finishes or a decision changes.
- **Two people work on v2:** the owner on Linux and a collaborator on macOS. Their Claude Code sessions share only the repo, so keep what a session needs in this file, `README.md` or `docs/`, never in Claude Code's memory. Tools and commands must work on both systems.
- The content steps each have their own doc: `docs/audit.md` (step 1), `docs/numbering.md` (step 3) and `docs/matn.md` (step 4, the matn check now under way, with the rules its review rounds follow).

## Decisions the owner has made

- **v2's text is the book's.** It is *Riyad al-Salihin* with *Nuzhat al-Muttaqin*'s word meanings and benefits. None of v1's commentary is used: the audit showed it is an edited version of the book's, with some meanings changed. v2 isn't released with v1's commentary, not even for a while.
- **The order is content, then the app, then the release.** Getting the content right comes first, and a late release is fine, so release timing isn't a trade-off to raise.
- **The app is React Native with Expo**, so it runs on Android and iPhone, and EAS builds the iPhone app without a Mac.
- **v1 stays on `master`**, tagged `v1.0.0` (live on Google Play). v2 is developed on the branch `v2`.
- **v1's signing key `v1/riyad_keystore.jks` is committed on purpose**, and stays in the repo: don't suggest removing it. Its passwords are in `v1/local.properties`, which is not in git (ask the owner).

## Working on the content

- **The printed book is the source of truth.** Read words from the scans (`tools/render_pages.py`, `tools/zoom.py`), never from memory. A misprint is never fixed silently: it goes to `corrections` with the printed words and the reason.
- **Decisions belong in git:** under `content/`, or in `docs/` with their reasons. `.cache/` holds only downloads and files the tools can make again. Never put anything there that can't be remade.
- **Run the tools** with `.venv/bin/python tools/...` from the project folder. They need Python 3.10 or newer: on macOS, the system `python3` is too old, so use Homebrew's.
- **Compare Arabic words through the tools.** `arabic.normalize_word` compares letters, and `matn.find` ignores the order of the marks on a letter. Texts store the marks in different orders, so plain string comparison misses matches.
- **Only one person runs the matn check's long run at a time** (README, "Working together"). When they stop, they apply any `content/matn/inbox.json` left by a stopped round, then commit and push `content/`. The other pulls before starting.
- **Commit only when asked.**
