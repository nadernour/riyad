# Book data

The content of v2: the text of *Riyad al-Salihin* and *Nuzhat al-Muttaqin*'s word meanings and benefits, checked against the printed book, with the tools that check it and the record of each step. The plan for the whole project is in the [root README](../README.md).

This folder is the owner's: the content is checked on the owner's Debian machine, and the tools aren't meant to run elsewhere (the owner's decision, 2026-10-25). The app doesn't read anything here: it reads `../database/riyad.db`, which `tools/build_db.py` builds from `content/` (see [its README](../database/README.md)). Everything below runs from this folder.

## Content

The printed book is the reference. Every word in the app is either confirmed by independent sources or checked on a zoomed scan of the page. Misprints in the book are never fixed silently: a correction is stored next to the printed text, with its reason.

The app shows only the book's text. v1's additions to the commentary (extra word meanings and benefits, grading notes) are not kept (the owner's decision, 2026-10-16).

### Sources

- **The v1 database** (`../v1/app/src/main/assets/databases/riyad_salheen.db`) has 20 books, 366 chapters and 1,893 hadith. The hadith text is vocalized, though about one word in eight has no mark at all, and the commentary is one text field per hadith. Its tags come from the colors of the HTML the text was stored as:

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
4. **Check the hadith text** (in progress: 172 of the 1,898 hadith are checked; see [docs/matn.md](docs/matn.md)). It isn't transcribed, because v1 already has it with tashkeel. Instead, every hadith is read against its matn on the scan, and v1's text is corrected to the book's:
   - **Doubts first.** `tools/matn.py` compares each matn with the OCR text of its pages, sunnah.com and the collections, and lists the words in doubt: other letters in the OCR text, marks no collection agrees with, words vocalized as nowhere in the collections, and text the book prints after v1's last word, such as Nawawi's explanation of a word, which v1 sometimes lacks. Before the rounds there were 5,775, in 1,559 of the 1,868 hadith left.
   - **Then the whole matn.** In short Claude Code rounds (`tools/long_run.sh`), each hadith is read against a crop of its matn on the scan, starting with its doubts, and every word changed is read on a zoom. The pilot on the audit's 30 hadith showed this is needed: the doubts missed 4 of the audit's differences, all case endings or wordings that no source contradicts.
   - **The book's wording is kept** where v1 follows another edition (e.g. «إلى الإسلام» for the book's «للإسلام»), unless it's a misprint. The book's single kasra where the grammar needs tanween («بن قيسِ») is a printing habit, so v1's tanween stays. Spelling that doesn't change the reading (مائة / مئة) stays as v1 has it.
   - **Words v1 leaves without tashkeel get the book's** (the owner's decision, 2026-10-22): 12,637 words, in 1,371 hadith. A word v1 marks in part keeps its marks unless one conflicts with the book's, but gets the book's shaddas, which change the reading («أَن» / «أَنَّ»; the owner's decision, 2026-10-23).
   - **The ordinals are left out.** In some chapters the book numbers the hadith in words («فالأول:», «الثاني:»). v1 keeps 29 of them, but the app shows every hadith's number, so `tools/convert_v1.py` removes them (the owner's decision, 2026-10-23).
   - **Every decision is kept** in `content/matn/`, one file per book, so the step can be applied again after rebuilding `content/hadith/`.
   - **Then the speaker roles.** The app sets the Prophet's words apart, but v1's roles aren't checked yet, and some are wrong: a piece tagged as the Prophet's words can take in the narrator's «فقال رسول الله ﷺ:» (h. 8) or a Companion's report (h. 1617), and his words can be left untagged (h. 37). A pass of its own settles them after the rounds (see [docs/matn.md](docs/matn.md)).
5. **Transcribe the word meanings and benefits** from the scans, page by page, in short Claude Code sessions, with a pipeline adapted from the owner's azkar project. That project isn't in this repo. It transcribed a 470-page scanned book in rounds of 5 pages at low effort, with chapter reviews at xhigh. A round cost about $0.9 at API prices (4–10% of the 5-hour limit, under 1% of the weekly one), and a chapter review about $1.7.
   - The OCR text of each page is the draft. It is proofread against the scan, with doubtful words zoomed, and split into word meanings and benefits, including commentary shared by several hadith (`shared_with`). v1's commentary isn't used, even as a cross-check, because the audit showed it is a different text.
   - A pilot on the audit's pages comes first, scored against the book's text in `content/audit/`. The rest of the book follows once the pilot's error rate is acceptable.
   - The rules will be in `docs/transcription.md`, written before the pilot.
   - **Explained words:** every word under لغة الحديث should be found in the hadith. One that isn't gets checked: either the printed text differs from ours there, or the word has to be matched by hand (e.g. «الهجرة» explains «هجرته»).
6. **Transcribe the narrator biographies** from the end of the book the same way. v1 doesn't have them, so aljam3's reading is the only cross-check. Each biography is then linked to the narrator's name in every hadith that names them. Names the tool can't match (a kunya, or a name written differently) are linked by hand.
7. **Owner review.** Questions the checks can't settle are listed per book (كتاب) for the owner to decide.

### Format

The source of truth is JSON in `content/hadith/`, one file per book (كتاب), so every change can be reviewed in git. Each file holds the book's `title` and its `chapters`. Each chapter has the book's chapter `number`, its `title`, v1's `old_id`, and its `hadith`. `tools/build_db.py` turns it into the SQLite database the app reads, with full-text search ([../database/README.md](../database/README.md)).

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

**Search** covers the hadith text only, as in v1: not the word meanings, benefits or titles (the owner's decision, 2026-10-17). The database has a simplified copy of the text for it (tashkeel removed, أ/إ/آ → ا, ة → ه, ى → ي). The app must simplify the search query exactly as the build script does, and shared test cases keep the two in step (`../database/simplify.json`).

## Layout

```
content/hadith/        the content, one JSON file per book (source of truth)
content/numbering.json where v1's hadith and chapters differ from the book's (step 3)
content/matn/          step 4: the decisions from checking each hadith's text against the scan
content/audit/         the v1 audit: the book's text for 30 v1 hadith and how v1 differs (the test set)
docs/audit.md          step 1: the audit's findings
docs/numbering.md      step 3: numbering, pages, chapters and titles
docs/matn.md           step 4: how the hadith text is checked, and the rules for the review rounds
tools/                 the Python scripts (setup below)
.venv/                 their Python environment (not in git)
.cache/                downloads and files the tools make again (not in git); nothing that can't be remade
.cache/book/nuzhat.pdf    the book's scans
.cache/aljam3/nuzhat.txt  the OCR text of the scans
.cache/sunnah/, .cache/hadith-api/   sunnah.com's Riyad al-Salihin and the collections, downloaded by the tools
.cache/ocr/               Tesseract and its reading of the pages
```

## Getting the book

Both files come from the [waqfeya-library dataset](https://huggingface.co/datasets/ieasybooks-org/waqfeya-library) on Hugging Face (MIT license), the same files aljam3 serves. The book is in the folder `2ـ 213.6 (230) المسانيد الأخرى والجوامع/01433ـ نزهة المتقين شرح رياض الصالحين --- مصطفى سعيد الخن، مصطفى البغا، محي الدين مستو، علي الشربجي، محمد أمين لطفي.PDF/`. Download `الكتاب.pdf` from that folder under `pdf/` to `.cache/book/nuzhat.pdf`, and `الكتاب.txt` from the same folder under `txt/` to `.cache/aljam3/nuzhat.txt`. You can also use the download buttons on the [aljam3 page](https://aljam3.com/6507/17722/1). The tools download both on first use, and the cross-check sources too. `tools/ocr.py` fetches Tesseract into `.cache/ocr/` with `tools/fetch_ocr.sh` (Debian packages, nothing installed system-wide).

## Setting up

On Debian (or Ubuntu), the system Python will do (3.10 or newer). Tesseract can be installed with apt; if it isn't, `tools/ocr.py` unpacks it into `.cache/ocr/` on first use, without installing anything system-wide. The matn check's long run also needs Claude Code, logged in to the owner's Claude subscription.

```sh
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/matn.py compare   # first run: downloads the book and the sources, and reads every page with Tesseract
```

The first `compare` takes a while, because Tesseract reads the 1,278 hadith pages (10 minutes on the owner's 18 cores). After that it takes about two minutes, and the tools make it again whenever `tools/matn.py` or `tools/numbering.py` has changed, e.g. after a pull. Everything it downloads or makes goes to `.cache/`, and every tool makes again what it needs if `.cache/` is empty.

## Content tools

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
.venv/bin/python tools/build_db.py                   # build the app's database, ../database/riyad.db
```

## The matn check's long run

Step 4's review is done in rounds (see [docs/matn.md](docs/matn.md)). `tools/long_run.sh` starts a fresh Claude Code session for each round (up to 12 hadith and 800 words of matn), on the owner's Claude subscription, and waits out the usage limits between rounds:

```sh
nohup tools/long_run.sh >> .cache/long-run.log 2>&1 &     # start it; it keeps going after the terminal closes
tail -F .cache/long-run.log                                # follow it: each round's cost, limits used, fixes, zooms and summary
pkill -f '[t]ools/long_run.sh'; pkill -f '[c]laude -p Do one round'   # stop it
```

The rounds run at medium effort. The first rounds, at low, often skipped the zooms the rules ask for: h. 21's round zoomed 4 spots for 103 words it gave marks to. So the 123 hadith they checked were checked again at medium (the owner's decision, 2026-10-23). Each round's line in the log gives its fixes and the zooms it read, and how many of those were too wide to read marks on, so the rounds can be compared. To go back to low, start the run with `EFFORT=low nohup tools/long_run.sh ...`.

Look at the first rounds' changes (`git diff content/`) before leaving it unattended. The rounds don't commit, so commit `content/` now and then. If a round was stopped before applying its decisions, `content/matn/inbox.json` is left (it isn't in git): run `.venv/bin/python tools/matn.py apply` before committing. A round that finds a rule or a tool wrong says so in its summary in the log. The log isn't in git, so act on it in `docs/` or `tools/`.

The rounds' sessions are saved under `~/.claude/projects/` (in the folder for `book_data`), and one can be opened from this folder with `claude --resume <its session id in the log>`.

## Building the app's database

`tools/build_db.py` builds `../database/riyad.db` from `content/`, and checks the search simplification against `../database/simplify.json` first. The same content makes the same file. It is committed, so that the app can be built without these tools, and each commit of it adds its whole size to the repository: build it again when the app should get the latest content, not after every change. [../database/README.md](../database/README.md) describes its tables.
