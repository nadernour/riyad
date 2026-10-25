# Working on the content

- `README.md` (in this folder) has the content's sources, steps, format, setup and tools. Each content step has its own doc: `docs/audit.md` (step 1), `docs/numbering.md` (step 3) and `docs/matn.md` (step 4, the matn check now under way, with the rules its review rounds follow). Keep them current, and the plan in the root `README.md` too.
- **Work from this folder.** Run the tools with `.venv/bin/python tools/...` from here. They run only on the owner's Debian machine.
- **The printed book is the source of truth.** Read words from the scans (`tools/render_pages.py`, `tools/zoom.py`), never from memory. A misprint is never fixed silently: it goes to `corrections` with the printed words and the reason.
- **Decisions belong in git:** under `content/`, or in `docs/` with their reasons. `.cache/` holds only downloads and files the tools can make again. Never put anything there that can't be remade.
- **Compare Arabic words through the tools.** `arabic.normalize_word` compares letters, and `matn.find` ignores the order of the marks on a letter. Texts store the marks in different orders, so plain string comparison misses matches.
- **The matn check's long run** (`tools/long_run.sh`) runs from this folder. When it stops, apply any `content/matn/inbox.json` left by a stopped round (`tools/matn.py apply`) before `content/` is committed.
- **The app's database** (`../database/riyad.db`) is built from `content/` by `tools/build_db.py`. It is committed, and each commit of it adds its whole size to the repository, so build it again when the app should get the latest content, not after every change.
