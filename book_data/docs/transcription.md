# Content step 5: transcribing the commentary

Each hadith's commentary in *Nuzhat al-Muttaqin* is transcribed from the scans: its word meanings (لغة الحديث) and its benefits (أفاد الحديث). The OCR text of the page (aljam3) is the draft, and each round corrects it against crops of the scan. The pipeline is adapted from the owner's azkar project (`book_data/README.md`, step 5).

A round is one fresh Claude Code session, started by `tools/long_run.sh` with `COMMENTARY=1` (and `PILOT=1` for the pilot). It transcribes up to 6 hadith or 4 pages, then stops. It works only from the files: this doc is all it needs to read.

## A round

1. **Run** `.venv/bin/python tools/commentary.py next`. It writes the drafts of the round's hadith to `content/commentary/inbox.json`. For each hadith it prints the source note and the benefits' heading as the OCR read them, and the paths of its crops. If the inbox already holds hadith (a round that was cut off), it gives you those again: finish them.
2. **Read** `content/commentary/inbox.json` and every crop it lists. A crop runs from the end of the hadith's matn (with its source note) to the start of the next hadith, so it can show the matn's last line, a chapter heading or the next hadith's first line: leave those out.
3. **Correct each draft** against its crops, word by word and line by line, with Edit. Every word must be the one printed. The draft is the OCR text, cut and split by a tool, so expect:
   - **dotted letters** read wrong: ث/ن/ت/ب/ي, ف/ق, ج/ح/خ, د/ذ, ر/ز, ص/ض, ط/ظ, ع/غ («حنية» for «حثية», «مهمة» for «مبهمة», «لطب» for «لطلب»);
   - **words** dropped, run together («ماحرم») or split («رؤيا كم»), and letters dropped («وهذ» where the book prints «وهذه»; but see misprints below);
   - **the ﷺ glyph** read as «لا», «الا», «الله», «علالالال» or left out: write ﷺ wherever the book prints the glyph;
   - **lines out of order**: a line of the benefits can be in the meanings, or in the wrong place among the benefits (h. 84);
   - **the split**: two meanings joined where the OCR lost the full stop between them, a meaning cut at a colon inside it, two benefits joined where it lost the bullet, the heading of the benefits left inside the meanings.
   Zoom on any word you can't read for certain on the crop, the page's doubtful spots in one command: `.venv/bin/python tools/zoom.py PAGE --crop TOP BOTTOM [LEFT RIGHT] --crop …` (fractions of the page; a crop's position on the page is printed with it, e.g. `p. 847, 0.78–0.93`). Then read all the zooms in one step.
4. **Run** `.venv/bin/python tools/commentary.py done`. It checks the inbox and files its entries in `content/commentary/NN.json`. If it lists problems, fix them in the inbox and run it again.
5. **Stop.** Don't start more hadith.

**What a round may do.** Read any file, edit `content/commentary/inbox.json`, and run the project's tools as plain commands from `book_data/`, e.g. `.venv/bin/python tools/zoom.py 847 --crop 0.30 0.36`. No `cd`, pipes, `python -c` or other shell commands: they are refused, because nobody is there to approve them. Never commit, and never change `docs/` or `tools/`. If a rule or a tool seems wrong, say so in the entry's `notes` and carry on with the rules as they are.

## What is transcribed

Everything the book prints between a hadith's matn and the next hadith (or the next chapter's heading), except what is listed as left out.

- **`meanings`**: the items under «لغة الحديث», in printed order, each `{"term": …, "meaning": …}`. The term is the words before the colon, the meaning everything after it up to the next term. A new item starts after a full stop with a word or phrase of the hadith and a colon. Where the book leaves out that full stop but the words before the colon are the hadith's («… بيمينه الكاذبة غضبان : يريد الانتقام منه», h. 1714), a new item starts there all the same, and the one before ends with « .» as every item does; say so in `notes`. So does a word or phrase of the hadith printed after a full stop with no colon and glossed by what follows it («تكسر : أي تطوى وتثنى . أفواهها جمع فم .», h. 762; «قبضت أخذت .», h. 938): it is an item of its own, with no colon added; say so in `notes`. Where an item's first words aren't the hadith's but the book plainly starts an item there with no colon («الآية / ٢٨٤ من سورة البقرة .», h. 169), the word it explains («الآية») is the term and the rest the meaning; a slash used as its colon isn't kept. A word of the meaning explained in turn («متحريها : التحري : القصد …») stays inside the meaning.
- A paragraph between the meanings and the benefits with a label of its own («سبب الحديث :», h. 1) is one more item of the meanings: its label, without the colon, is the term, and `in_text` is "" since it explains no word of the hadith.
- Word meanings printed under the heading «أفاد الحديث» (terms with colons, no bullets, h. 989) are a misprinted heading: they go in `meanings`, and the benefits are empty unless bullets follow. Say so in `notes`.
- **`benefits`**: the items under «أفاد الحديث», one per bullet, in printed order. A paragraph printed after them with a label of its own («فائدة :», «تنبيه :», «ملاحظة :») is one more item, with its label. So is a benefit printed as «ما أفاد سابقه …».
- **`shared_with`**: the hadith before it that its benefits are printed for too, when the heading says so: «أفاد الحديثان» (the one before), «أفادت الأحاديث الثلاثة» (the two before), «أفاد الحديث والذي قبله», «أفادت الأحاديث المتقدمة» or «السابقة» (each one before it in the chapter since the last that has benefits of its own). The draft proposes it; check it against the heading on the scan and the hadith numbers before it. The benefits stay with the hadith they are printed after; the app shows them with each.
- **`see`**: where the book sends the reader to the hadith's earlier place instead of, or besides, a source note («تقدم شرح الحديث في باب الخوف رقم ٤٤٧ .», «انظر الحديث في الباب المذكور برقم ٣ .»), that sentence as printed, else `null`. Its benefits are often headed «وأفاد هنا»: they are the benefits as usual.
- **Left out**: the source note («الحديث رواه البخاري في …»), footnotes, the headings themselves («لغة الحديث», «أفاد الحديث»), the bullets, hadith and page numbers, and a chapter's verses and their commentary (the app shows no verses: root `README.md`). If the book prints something else, such as a paragraph of explanation with no heading, keep it where it falls (inside the meaning or benefit it follows) and say so in `notes`.

## Text conventions

| What | Rule | Example |
|---|---|---|
| Letters | Exactly as printed: hamza seats, final «ى» or «ي», «ة» or «ه» | «يهيء», «الانسان» |
| Marks | Only the marks the book prints, where it prints them. Never add one. The commentary prints few: tanween on an alif, a shadda, a damma to tell a passive verb | «جمعاً», «يُرزق» |
| ﷺ | The glyph is written ﷺ (U+FDFA) | «يأتي النبي ﷺ» |
| Kashida | Not kept: a word stretched with tatweel is written plain | «قيـــل» → «قيل» |
| Punctuation | As printed: «،» «؛» «؟» «:» «.» with a space before and after; brackets ( ) and « » with a space inside | «أبصر ( من الرؤية ) .» |
| Item ends | Every meaning and every benefit ends with « .». The book's full stop and its bullet are the same dot, so where items run on in one paragraph, the dot between them ends the one before | «أي بسببه .» |
| Digits | Arabic-Indic, as printed | «رقم ٤٤٧» |
| Lines | Printed lines are joined into one text; a word broken across lines is joined | |
| Words after «ما», «لا» and «يا» | Two words, though the print often shows no space after the alif: the letter doesn't join, so a lost space can't be told from a narrow one. A word that begins with these letters stays whole | «ما بين», «لا يخلو», «يا أيها»; but «ماتت», «لاحق», «لاستكباره», «يابسة» |

`done` refuses characters the book doesn't print (Latin letters, ASCII digits, the bullet «•», Persian look-alike letters), doubled spaces and spaces at either end.

## Misprints

A misprint is never fixed silently: the text keeps the printed words, and a correction is added next to them, which the app shows instead. Correct only what is plainly wrong: a word that isn't one («وهذ هي» → «وهذه هي»), a broken grammar, a name misspelled. Not the style, nor a spelling the book uses throughout («الانسان»).

```json
"corrections": [{"part": "benefits.1", "printed": "وهذ هي", "correction": "وهذه هي", "reason": "a letter dropped: «وهذ» isn't a word"}]
```

`part` is `see`, `meanings.N.term`, `meanings.N.meaning` or `benefits.N` (N from 0). `printed` must occur exactly once in that part: take in a neighbouring word if needed.

## Terms and the hadith

The app links each term to its words in the hadith, so a reader can tap a word and see its meaning. `done` looks for each term in the hadith's text (from `content/hadith/`), ignoring the marks and the prefixes و ف ب ل ك ال. Where it isn't found, add `"in_text"` to the item: the hadith's words that the term explains, written as in the hadith's text («الهجرة» explains «هجرته»: `"in_text": "هجرته"`). Where the term explains no word of the hadith's text (a word of another narration, or of the source note), set `"in_text": ""` and say why in `notes`. Never change the term itself: it is what the book prints.

## The entry

`content/commentary/NN.json` holds one book's (كتاب) entries, by hadith number; `inbox.json` the round's.

```json
"1193": {
 "id": 1193,
 "pages": [847, 848],
 "see": null,
 "meanings": [{"term": "في الوتر", "meaning": "أي في الليالي المفردة ؛ كإحدى وعشرين ، وثلاث وعشرين وهكذا ."}],
 "benefits": ["أن ليلة القدر تكون في العشر الأواخر من رمضان …", "الحث على الاعتكاف وإحياء ليالي العشر الأواخر …"],
 "shared_with": [1191, 1192],
 "corrections": [{"part": "benefits.1", "printed": "وهذ هي", "correction": "وهذه هي", "reason": "…"}],
 "notes": []
}
```

| Field | Content |
|---|---|
| `id` | The hadith's number |
| `pages` | The first and last PDF page of its commentary (one if it fits on a page) |
| `see` | The cross-reference, or `null` |
| `meanings` | `{term, meaning}`, with `in_text` where the term isn't found in the hadith |
| `benefits` | The benefits, in order |
| `shared_with` | The hadith before it that its benefits cover too, or `[]` |
| `corrections` | Misprints, as above |
| `notes` | English notes: anything unusual, words zoomed on and what they showed, why a field is empty |

A hadith with no word meanings or no benefits has an empty list: the book doesn't give every hadith both.

## The pilot

The pilot transcribes the 30 hadith of the v1 audit (`COMMENTARY=1 PILOT=1 tools/long_run.sh`), whose commentary was read with the book's text in `content/audit/` (docs/audit.md). `.venv/bin/python tools/commentary.py score` lists every word where a transcription differs from the audit's text. Each difference is settled on the scan: the audit's text can be wrong too (it fixed «وهذ» silently, and left «بعشر» in h. 1193 to check again). The rest of the book follows once the rounds' error rate is acceptable.

**The pilot's result (2026-11-18).** 11 rounds transcribed the 33 hadith for $3.6 at API prices (about $0.11 a hadith), 26% of the 5-hour window and about 2% of the weekly one. Against the audit's 1,800 words, after each difference was settled on the scan, the rounds misread one word («الكلاً» for «الكلأ», h. 1379). The other differences were the audit's: a meaning it left out (h. 160), marks it left out or added, hamza seats and tanween it normalized, misprints it fixed silently, and ﷺ written out. The pilot also settled three things, now in this doc and the tool: the rounds split «ما»/«لا» run-togethers differently (now always two words); two rounds kept a term inside the meaning before it where the book lost a full stop (now an item of its own); and the crop of a commentary could stop a line short (h. 1714) or run on into the next hadith's (h. 1534).
