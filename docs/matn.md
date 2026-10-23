# Checking the hadith text

Content step 4 (see the README). The matn in `content/hadith/` is v1's text (step 2). In this step every hadith is read against the printed book, and v1's text is corrected to what the book prints. The decisions are kept in `content/matn/NN.json`, one file per book (كتاب), so the step can be applied again on top of `tools/convert_v1.py` (`tools/matn.py apply --all`).

## How it works

1. **Comparison** (`tools/matn.py compare`). Each matn is compared word by word with three sources:
   - the OCR text of the book's pages, the only one that reads this print;
   - sunnah.com's Riyad al-Salihin, from another edition;
   - the vocalized collections (hadith-api's six books and the Muwatta), wherever the wording matches.

   The comparison lists the words in doubt, and the kinds are below. A word whose letters the OCR text confirms, and whose marks no source contradicts, is not listed. The words v1 leaves without any mark are listed too, to be given the book's marks (rule 2).
2. **Review rounds.** Every hadith is then read against a crop of its matn on the scan, starting with its doubts. The pilot on the audit's 30 hadith showed why every hadith is read in full: the doubts held all but 4 of the audit's differences in the matn, and the 4 they missed were case endings no source contradicts («عالِيَةً», «فَيَحْمَدُهُ») and a wording variant.
3. **Decisions.** Each round writes its decisions to `content/matn/inbox.json`. `tools/matn.py apply` checks them, applies them to `content/hadith/`, and keeps them in `content/matn/NN.json`. A hadith with a decision there counts as checked, and `apply` drops a new decision for it. To change one, edit it in `content/matn/NN.json`, then run `tools/convert_v1.py --force` and `tools/matn.py apply --all`.

### Kinds of doubt

| Kind | What the sources show |
|---|---|
| `missing` | The OCR text has nothing for these words of v1's. Usually the OCR lost a line; sometimes v1 adds words the book doesn't have. |
| `extra` | The OCR text has words here that v1 lacks. Usually the OCR read a line twice; sometimes the book has words v1 lacks. |
| `after` | The OCR text has words printed like the matn, with marks, after v1's last word and before the commentary. The book may print more than v1 has, such as Nawawi's explanation of a word (h. 145) or another narration (h. 830). Sometimes the OCR text has put a line of the matn out of order. |
| `split` | The same letters, spaced differently: «يارسول» / «يا رسول». |
| `stray` | A mark on no letter, such as the kasra in «اللهِ ِ ﷺ»: remove it (rule 4). |
| `dots` | The same letter shapes with other dots. Listed only where sunnah.com doesn't have v1's word. |
| `prefix`, `other` | The OCR text has another word. Most are OCR misreadings, but this is where the book's other readings are found: «للإسلام» for «إلى الإسلام», «مجاهد» for «يجاهد». |
| `tashkeel` | Every collection that has the word marks a letter differently from v1. |
| `ocr-tashkeel` | The OCR text marks a letter differently from v1, and no collection marks it as v1 does. The OCR text's marks are often wrong, but they catch v1's wrong case endings («يَسْأَلَهُ» for «يَسْأَلُهُ»). |
| `unattested` | No collection marks the word as v1 does, its last letter aside. Most of these are v1's typos: a mark on the wrong letter («قَالَوا», «سَِمعَ»). |
| `align` | The OCR text has under 60% of the matn's words in order: read all of it with care. |

Not listed, though the full read still covers them: a `dots` difference where sunnah.com has v1's word; the OCR text's habitual misreadings, checked on the scan («عنهما» read «عنها», «النبي» read «الني» or «التي»); a word Tesseract reads as v1 has it; and a tashkeel conflict where the OCR text has v1's marks on the letters in question.

`tools/matn.py stats` gives the totals. Before the rounds there were 5,775 doubts, in 1,559 of the 1,868 hadith left, and 12,637 words with no mark, in 1,371 of them.

**After the rounds**, two passes of their own:
- **Chapter titles:** v1's titles against the headings on the scan. v1 has typos in them («وتفديمهم», «الوضو ء»), and it shortens some of the early ones.
- **The pilot's 30 hadith** were checked before the rule on words with no mark (rule 2), so their bare words still need the book's marks. Their decisions are changed in `content/matn/NN.json` (see "Decisions" above).

## The rules

The book is the reference. v1's text stays wherever the book agrees with it.

1. **Letters.** Where the book's words differ from v1's, put the book's.
   - `"v1"`: v1's mistake, such as a wrong letter, words run together or split («يارسول», «أَ نَّ»), or a word added or dropped.
   - `"variant"`: v1 follows another edition, so v1's reading is also known. sunnah.com often has it too.
   - A misprint in the book (a dropped word its own commentary shows, an impossible form) isn't copied. Keep v1's correct text and record the misprint (below).
2. **Tashkeel.** Where the book and v1 both mark a letter and the marks differ, put the book's (`"v1"` if v1's mark is wrong, `"variant"` if both are good Arabic).
   - **A word v1 leaves bare,** with no mark at all, is written as the book prints it, with all its marks (`"marks"`; the owner's decision, 2026-10-22). `next` lists these words. Where the book leaves the word bare too, nothing changes. A word v1 marks in part keeps its marks: the book's marks on the letters v1 leaves bare aren't added.
   - The print often puts a single kasra where the grammar needs tanween (e.g. «بْنِ قَيْسِ», «بِإِسْنادِ حَسَنٍ»). That's a printing habit, so keep v1's tanween, and write the tanween in a bare word you give marks to.
   - In this print a kasra with a shadda is set under the shadda, above the letter, so on a zoom it can look like a damma («المُزَنِيِّ», h. 14). A damma sits on top of the shadda («قَطُّ», h. 20). Before taking a case ending for a misprint, compare its mark with a word on the same page whose case is certain.
   - Where the book leaves a letter bare, keep v1's mark, unless it is plainly wrong (a mark on the wrong letter, «يْومٍ» for «يَوْمٍ»). Then write the word correctly, as the collections have it (`"v1"`).
3. **A word you change or give marks to** is written as the book prints it, with all its marks, read on a zoom.
4. **Not checked:** spelling that doesn't change the reading, where v1's spelling stays (مائة / مئة, داود / داوود, السماوات / السموات, الزنا / الزنى, يا بن / يا ابن, final ى / ي, هكذا / هٰكذا); punctuation; and the speaker roles. The marks on such a word are still checked (rule 2): where the book prints «سَبْعِ مِئَةِ» and v1 «سَبْعِمَائِةِ», write «سَبْعِمِائَةِ». But remove a stray mark that breaks the text, such as a lone «, or a verse reference in brackets («[آل عمران: 77]»), which the book gives in a footnote.
5. **The whole matn** is checked: the narrator, the hadith, Nawawi's source line («متفق عليه», «رواه الترمذي وقال: حديث حسن»), and his explanation of words after it («المِرْطُ: كساء …»). The book sometimes prints more of it than v1 has, such as Nawawi's whole explanation (h. 145) or another narration (`after` doubts): add what v1 lacks, as printed (`"v1"`).
6. **Hadith not in v1** (153, 172, 1126 and 1548) were transcribed from the scan in step 3. Check every mark of theirs at zoom.
7. **If a word can't be read** even zoomed, keep v1's and say so in a note.

### The decision for a hadith

`content/matn/inbox.json` holds one entry per hadith, keyed by its number:

```json
{
 "84": {"fix": [["يأْتِي النبيِّ", "يَأْتِي النَّبِيَّ", "v1"], ["التِّرْمذيُّ", "التَّرْمِذِيُّ", "variant"]]},
 "85": {},
 "145": {"fix": [["عن أبي هريرة", "عَنْ أَبِي هُرَيْرَةَ", "marks"]]},
 "691": {"fix": [["قالَ لي النَّبِيُّ", "قالَ رَسُولُ اللهِ", "variant"]],
         "misprint": [["هٰكَذا وَهٰكَذا", "هٰكَذا وَهٰكَذا وَهٰكَذا", "The print drops the third «وهكذا»; its own word meanings explain it as «ثلاثاً»."]]}
}
```

- `{}`: the matn is right as it is.
- `fix`: `[from, to, why]`, with why `"v1"`, `"variant"` or `"marks"` (the fix only gives the book's marks to words v1 leaves bare). `from` is copied from the matn as printed by `next`; the order of the marks on a letter doesn't matter. It must occur once in the matn, so take a neighbouring word with it when needed. It may run over the speaker roles («قَالَ: لا، قُلْتُ»): `apply` keeps each word in its role. `to` is empty to delete. Where a hadith has many bare words, one fix can take a whole phrase.
- `misprint`: `[printed, correction, reason]` for a misprint in the book. The matn keeps the correct text, and the misprint goes to the hadith's `corrections`.
- `note`: a short English note for the owner, added to the hadith's `notes`. Use it only for something the owner should know or decide.

## One round

`tools/long_run.sh` starts a fresh Claude Code session for each round, with the prompt "Do one round of the matn check: follow docs/matn.md exactly." (README, "The matn check's long run"). A round checks up to 12 hadith, fewer when they're long (800 words of matn in all), and stops. Rounds are kept short because every step re-reads everything the session has read so far.

1. **Read** this file and nothing else that the round doesn't need. The tools' usage is here, so don't read their source.
2. If `content/matn/inbox.json` exists, an earlier round didn't finish. Run `.venv/bin/python tools/matn.py apply`, fix what it reports in the inbox, and run it again until it applies. Then go on.
3. **Run** `.venv/bin/python tools/matn.py next`. It prints how many hadith are checked, then the round's hadith. For each one it gives:
   - the crops of its matn on the scan: one image per page, with the page and the part of the page the crop covers;
   - v1's matn;
   - its doubts;
   - the words v1 leaves with no mark, run by run.

   If it says all are checked, stop.
4. **Read all the round's crops at once**: one message with a Read call for each crop. Every step re-reads everything before it, so reading them one by one costs several times as much. Then, for each hadith, read the matn on the scan word by word against v1's text:
   - Check that its crops hold the whole matn: from the hadith's number in the margin (its number in the chapter over its number in the book, e.g. ٤ over ١٤٥) to where the commentary starts, in smaller print without marks («الحديث رواه …», «لغة الحديث», «أفاد الحديث»), or to the next hadith. When the tools can't place a matn, its crop is the whole page: find the hadith by its number. If a crop cuts the matn off, zoom out over a wider range of the page.
   - Settle each listed doubt first, then any other difference you see, and read on to the end of the matn: the book can print more than v1 has (rule 5).
   - Give the book's marks to the words v1 leaves bare (rule 2).
   - **Zoom on every word you change or give marks to,** and on any other mark you're not sure of: a crop is too small to be sure of every mark. `tools/zoom.py PAGE TOP BOTTOM --left L --right R` takes the page and fractions of it: the crop's range is printed next to it, and a line is about 0.035 of the page. Do all of a page's spots in one command, with `--crop TOP BOTTOM LEFT RIGHT` for each, and read all the zooms of the round together too.
5. **Write** `content/matn/inbox.json` with a decision for each of the round's hadith, in one Write.
6. **Run** `.venv/bin/python tools/matn.py apply`. It keeps the entries that failed in the inbox and says why. Correct them and run apply again.
7. **Stop** with a one-line summary: the hadith checked, and how many fixes for each reason (`v1`, `variant`, `marks`).

**What a round may do.** Read any file, write `content/matn/inbox.json`, and run the project's tools as plain commands from the project folder, e.g. `.venv/bin/python tools/zoom.py 96 0.30 0.35`. Write no `cd`, pipes, `python -c` or other shell commands: anything else is refused, because nobody is there to approve it. Never commit to git, and never change `docs/` or `tools/`. If a rule or a tool seems wrong, say so in the summary and carry on with the rules as they are.
