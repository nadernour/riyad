# Checking the hadith text

Content step 4 (see the README). The matn in `content/hadith/` is v1's text (step 2). In this step every hadith is read against the printed book, and v1's text is corrected to what the book prints. The decisions are kept in `content/matn/NN.json`, one file per book (كتاب), so the step can be applied again on top of `tools/convert_v1.py` (`tools/matn.py apply --all`).

## How it works

1. **Comparison** (`tools/matn.py compare`). Each matn is compared word by word with three sources:
   - the OCR text of the book's pages, the only one that reads this print;
   - sunnah.com's Riyad al-Salihin, from another edition;
   - the vocalized collections (hadith-api's six books and the Muwatta), wherever the wording matches.

   The comparison lists the words in doubt, and the kinds are below. A word whose letters the OCR text confirms, and whose marks no source contradicts, is not listed.
2. **Review rounds.** Every hadith is then read against a crop of its matn on the scan, starting with its doubts. The pilot on the audit's 30 hadith showed why every hadith is read in full: the doubts held all but 4 of the audit's differences in the matn, and the 4 they missed were case endings no source contradicts («عالِيَةً», «فَيَحْمَدُهُ») and a wording variant.
3. **Decisions.** Each round writes its decisions to `content/matn/inbox.json`. `tools/matn.py apply` checks them, applies them to `content/hadith/`, and keeps them in `content/matn/NN.json`. A hadith with a decision there counts as checked, and `apply` drops a new decision for it. To change one, edit it in `content/matn/NN.json`, then run `tools/convert_v1.py --force` and `tools/matn.py apply --all`.

### Kinds of doubt

| Kind | What the sources show |
|---|---|
| `missing` | The OCR text has nothing for these words of v1's. Usually the OCR lost a line; sometimes v1 adds words the book doesn't have. |
| `extra` | The OCR text has words here that v1 lacks. Usually the OCR read a line twice; sometimes the book has words v1 lacks. |
| `split` | The same letters, spaced differently: «يارسول» / «يا رسول». |
| `dots` | The same letter shapes with other dots. Listed only where sunnah.com doesn't have v1's word. |
| `prefix`, `other` | The OCR text has another word. Most are OCR misreadings, but this is where the book's other readings are found: «للإسلام» for «إلى الإسلام», «مجاهد» for «يجاهد». |
| `tashkeel` | Every collection that has the word marks a letter differently from v1. |
| `ocr-tashkeel` | The OCR text marks a letter differently from v1, and no collection marks it as v1 does. The OCR text's marks are often wrong, but they catch v1's wrong case endings («يَسْأَلَهُ» for «يَسْأَلُهُ»). |
| `unattested` | No collection marks the word as v1 does, its last letter aside. Most of these are v1's typos: a mark on the wrong letter («قَالَوا», «سَِمعَ»). |
| `align` | The OCR text has under 60% of the matn's words in order: read all of it with care. |

Not listed, though the full read still covers them: a `dots` difference where sunnah.com has v1's word; the OCR text's habitual misreadings, checked on the scan («عنهما» read «عنها», «النبي» read «الني» or «التي»); a word Tesseract reads as v1 has it; and a tashkeel conflict where the OCR text has v1's marks on the letters in question.

`tools/matn.py stats` gives the totals. After the pilot there were 5,751 doubts, in 1,562 of the 1,868 hadith left.

**Chapter titles** are checked after the hadith, in a pass of their own: v1's titles against the headings on the scan. v1 has typos in them («وتفديمهم», «الوضو ء»), and it shortens some of the early ones.

## The rules

The book is the reference. v1's text stays wherever the book agrees with it.

1. **Letters.** Where the book's words differ from v1's, put the book's.
   - `"v1"`: v1's mistake, such as a wrong letter, words run together or split («يارسول», «أَ نَّ»), or a word added or dropped.
   - `"variant"`: v1 follows another edition, so v1's reading is also known. sunnah.com often has it too.
   - A misprint in the book (a dropped word its own commentary shows, an impossible form) isn't copied. Keep v1's correct text and record the misprint (below).
2. **Tashkeel.** Where the book and v1 both mark a letter and the marks differ, put the book's (`"v1"` if v1's mark is wrong, `"variant"` if both are good Arabic).
   - The print often puts a single kasra where the grammar needs tanween (e.g. «بْنِ قَيْسِ», «بِإِسْنادِ حَسَنٍ»). That's a printing habit, so keep v1's tanween.
   - Where the book leaves a letter bare, keep v1's mark, unless it is plainly wrong (a mark on the wrong letter, «يْومٍ» for «يَوْمٍ»). Then write the word correctly, as the collections have it (`"v1"`).
3. **A word you change** is written as the book prints it, with all its marks.
4. **Not checked:** spelling that doesn't change the reading, where v1's spelling stays (مائة / مئة, داود / داوود, السماوات / السموات, الزنا / الزنى, يا بن / يا ابن, final ى / ي, هكذا / هٰكذا); punctuation; and the speaker roles. But remove a stray mark that breaks the text, such as a lone «, or a verse reference in brackets («[آل عمران: 77]»), which the book gives in a footnote.
5. **The whole matn** is checked: the narrator, the hadith, Nawawi's source line («متفق عليه», «رواه الترمذي وقال: حديث حسن»), and his explanation of words after it («المِرْطُ: كساء …»).
6. **Hadith not in v1** (153, 172, 1126 and 1548) were transcribed from the scan in step 3. Check every mark of theirs at zoom.
7. **If a word can't be read** even zoomed, keep v1's and say so in a note.

### The decision for a hadith

`content/matn/inbox.json` holds one entry per hadith, keyed by its number:

```json
{
 "84": {"fix": [["يأْتِي النبيِّ", "يَأْتِي النَّبِيَّ", "v1"], ["التِّرْمذيُّ", "التَّرْمِذِيُّ", "variant"]]},
 "85": {},
 "691": {"fix": [["قالَ لي النَّبِيُّ", "قالَ رَسُولُ اللهِ", "variant"]],
         "misprint": [["هٰكَذا وَهٰكَذا", "هٰكَذا وَهٰكَذا وَهٰكَذا", "The print drops the third «وهكذا»; its own word meanings explain it as «ثلاثاً»."]]}
}
```

- `{}`: the matn is right as it is.
- `fix`: `[from, to, why]`, with why `"v1"` or `"variant"`. `from` is copied from the matn as printed by `next`; the order of the marks on a letter doesn't matter. It must occur once in the matn, so take a neighbouring word with it when needed. `to` is empty to delete.
- `misprint`: `[printed, correction, reason]` for a misprint in the book. The matn keeps the correct text, and the misprint goes to the hadith's `corrections`.
- `note`: a short English note for the owner, added to the hadith's `notes`. Use it only for something the owner should know or decide.

## One round

`tools/long_run.sh` starts a fresh Claude Code session for each round, with the prompt "Do one round of the matn check: follow docs/matn.md exactly." (README, "The matn check's long run"). A round checks 12 hadith and stops. Rounds are kept short because every step re-reads everything the session has read so far.

1. **Read** this file and nothing else that the round doesn't need. The tools' usage is here, so don't read their source.
2. If `content/matn/inbox.json` exists, an earlier round didn't finish. Run `.venv/bin/python tools/matn.py apply`, fix what it reports in the inbox, and run it again until it applies. Then go on.
3. **Run** `.venv/bin/python tools/matn.py next`. It prints how many hadith are checked, then the next 12. For each one it gives:
   - the crops of its matn on the scan: one image per page, with the page and the part of the page the crop covers;
   - v1's matn;
   - its doubts.

   If it says all are checked, stop.
4. **Read all the round's crops at once**: one message with a Read call for each crop. Every step re-reads everything before it, so reading them one by one costs several times as much. Then, for each hadith, read the matn on the scan word by word against v1's text:
   - Settle each listed doubt first, then any other difference you see.
   - Zoom on any mark you're not sure of. `tools/zoom.py PAGE TOP BOTTOM --left L --right R` takes the page and fractions of it: the crop's range is printed next to it, and a line is about 0.035 of the page. Do all of a page's doubtful spots in one command, with `--crop TOP BOTTOM LEFT RIGHT` for each, and read all the zooms of the round together too.
   - If a crop doesn't show the whole matn (it starts or ends mid-sentence), zoom out over a wider range of the page.
5. **Write** `content/matn/inbox.json` with a decision for each of the round's hadith, in one Write.
6. **Run** `.venv/bin/python tools/matn.py apply`. It keeps the entries that failed in the inbox and says why. Correct them and run apply again.
7. **Stop** with a one-line summary: the hadith checked, and how many fixes of each kind.

**What a round may do.** Read any file, write `content/matn/inbox.json`, and run the project's tools as plain commands from the project folder, e.g. `.venv/bin/python tools/zoom.py 96 0.30 0.35`. Write no `cd`, pipes, `python -c` or other shell commands: anything else is refused, because nobody is there to approve it. Never commit to git, and never change `docs/` or `tools/`. If a rule or a tool seems wrong, say so in the summary and carry on with the rules as they are.
