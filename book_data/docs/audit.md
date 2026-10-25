# Audit of the v1 text

Content step 1 (see the README): 30 v1 hadith compared with the printed book, to find out where v1's mistakes are. The records are in `content/audit/`, one file per v1 hadith, and they are also the test set for the later steps.

## Summary

- **The matn is in good shape.** 7 of the 30 have a v1 mistake, nearly all a single wrong tashkeel mark.
- **The commentary is not a copy of the book.** In 26 of the 30, v1's word meanings and benefits differ from what Nuzhat al-Muttaqin prints. The differences aren't typing mistakes. Someone edited the text: rewording it, adding to it, cutting it, and in 6 hadith changing what it says.
- **The numbering drifts.** Only 2 of the 30 have the book's number. v1 falls 1 to 5 behind as the book goes on, because it merges, skips and adds entries (step 3 maps them all).

So v1's matn is a good base, as planned. v1's commentary can't be used even as a cross-check: the commentary has to come from the scans.

v1's database came from an abandoned app, [com.zad.riyadhsalheen](https://play.google.com/store/apps/details?id=com.zad.riyadhsalheen), so the edits were made before v1.

**The owner's decisions (2026-10-16):**
- v2 shows only the book's text. None of v1's additions are kept.
- v2 is released once the commentary is checked, not with v1's commentary in the meantime.

## Method

1. **The sample** (`tools/audit.py sample`): one random hadith from each 1/30 of v1's 1,893, with a fixed seed: v1 8, 84, 159, 250, 285, 357, 434, 502, 511, 596, 689, 733, 797, 856, 910, 997, 1046, 1108, 1189, 1261, 1311, 1375, 1426, 1480, 1530, 1578, 1680, 1709, 1774 and 1866.
2. **Comparison** (`tools/audit.py show ID`): `tools/locate.py` finds the pages, and v1's text is aligned word by word with the OCR text of those pages. Every word where the two differ in letters or tashkeel is listed.
3. **Settling each difference on the scan:** the page is rendered with `tools/render_pages.py`, and doubtful marks are zoomed with `tools/zoom.py`. The book's number for each hadith was read from the scan, because the OCR garbles digits.
4. **The record** (`tools/audit.py record ID`, then corrected by hand): the book's text, and every difference with its part, kind and cause:
   - **v1:** v1 is wrong.
   - **book:** a misprint in the book; v1 is right.
   - **variant:** both readings are valid; the book's is kept.
5. **Totals:** `tools/audit.py summary`.

**Limits.** Where v1 and the OCR agree on a word, the word was accepted without zooming. Where one has tashkeel and the other doesn't, it isn't counted, because editions mark different letters. Punctuation isn't compared. Nuzhat's source notes («الحديث رواه البخاري …») and footnotes are outside the app's content, so v1's lack of them isn't counted. One word in hadith 1189 («بعشر») should be checked again.

## Findings

Counts of differences: one row per kind, split by who has it wrong.

| Part | Kind | v1 wrong | book wrong | variant |
|---|---|---:|---:|---:|
| matn | tashkeel | 6 | 3 | 5 |
| matn | letters (a word differs) | 1 | 0 | 9 |
| matn | added / missing | 1 | 1 | 4 |
| word meanings | missing | 10 | | |
| word meanings | added | 7 | | |
| word meanings | reworded / replaced | 6 | | |
| word meanings | letters | 2 | | |
| benefits | added | 17 | | |
| benefits | reworded / replaced | 14 | | |
| benefits | meaning changed | 7 | | |
| benefits | missing | 3 | | |
| benefits | letters | | 1 | |
| structure | shared commentary, duplicated text | 4 | | |
| number | differs from the book | 28 | | |

### The matn

- **v1's mistakes:**
  - six wrong marks: «يأتي النبيِّ» for «النبيَّ», «استطعَت», «يسألَه», «القُوم», «المسيء صلاتُه», «مِصَداقه»;
  - one word split by a space: «أَ نَّ»;
  - one verse reference typed into the hadith text.
- **Variants:** 18 places where v1's wording differs from the book's but is a known reading, e.g. «إلى الإسلام» / «للإسلام», «يجاهد» / «مجاهد», «رسول الله» / «النبي». v1's matn seems to follow another edition of Riyad al-Salihin. The book's wording is kept. Step 4 checks each of these against the hadith collections.
- **The book's own slips:**
  - It prints a single kasra on a name where the grammar needs tanween («قيسِ», «إياسِ», «سعيدِ», «جندبِ»). That's a printing habit, and v1's tanween is right.
  - It drops the third «وهكذا» in hadith 691, which its own word meaning explains.

### The commentary

Only 4 of the 30 (v1 8, 285, 1578, 1680) match the book word for word. The other 26 have the kinds of changes in the table. Most rewrite the book's wording or add benefits of the editor's own.

In 6 hadith the change alters what the commentary says:

| v1 | Book | The book says | v1 says |
|---|---|---|---|
| 159 | 160 | Eating with the right hand is «استحباب», with the left «كراهية» | «وجوب» and «تحريم»; the book's «إن مخالفة ما هو مستحب لا يوجب الإثم» is replaced |
| 434 | 437 | «يرضى : يقبل ويثيب» | Drops that and adds «إثبات صفة الرضى لله تعالى إثباتا يليق بجلاله» |
| 596 | 598 | Praises seclusion when one fears trial among people | «اعتزال النّاس لا يمدح مطلقا … واعتزاله مذموم» |
| 856 | 859 | The mosque greeting prayer comes before greeting people | Calls it disputed, and suggests greeting people first |
| 997 | 1000 | Quotes al-Tirmidhi's «حسن صحيح» | Adds «تنبيه: الحديث به ضعف» |
| 1261 | 1265 | Quotes Nawawi's «بإسناد حسن» | Adds «الحديث مختلف في صحته والأقرب ضعفه» |

Some cuts follow the same pattern without being counted as changes of meaning:
- 1709 (book 1714) drops «غضبان : يريد الانتقام منه».
- 1866 (book 1871) cuts Ibn al-Athir's explanation of «ليغان» mid-sentence.

v1 also stores one word in Arabic presentation-form characters, which search can't match.

### The structure

- **Shared commentary is common.** The book sometimes prints one set of benefits for two or three hadith, after the last of them («أفاد الحديث والذي قبله», «أفادت الأحاديث الثلاثة السابقة», «أفادت الأحاديث المتقدمة»). It appears in 3 of the 30 (v1 1189, 1426, 1709) and on the way in a fourth (book 1429). v1 attaches such benefits to one hadith only.
- **Duplicated text.** v1 357 repeats the whole matn of the hadith before it (v1 356, the book's 359) ahead of its own (the book's 360). The audit first read this as two printed hadith merged; step 3 corrected it.

### The numbering

v1 → book: 8→8, 84→84, 159→160, 250→252, 285→287, 357→360, 434→437, 502→504, 511→513, 596→598, 689→691, 733→736, 797→800, 856→859, 910→913, 997→1000, 1046→1049, 1108→1111, 1189→1193, 1261→1265, 1311→1315, 1375→1379, 1426→1430, 1480→1484, 1530→1534, 1578→1583, 1680→1685, 1709→1714, 1774→1779, 1866→1871.

The gap mostly grows, but between v1 434 and 502 it shrinks by one. So v1 both merges and adds entries, and the mapping in step 3 has to come from the text, not from an offset.

### The OCR text

For the commentary, the OCR text is close to the print. Its usual mistakes:
- it reads the ﷺ glyph as «لا», «الا» or «الله»;
- it gets the line order wrong in a few places;
- it garbles digits.

For the matn, its tashkeel is unreliable: most of the tashkeel conflicts it raised were its own misreadings.

## What this changes in the plan

1. **Matn (step 4): as planned.** v1's text is the base. Every place where it differs from the OCR text is settled on the scan, and the book's wording wins unless it's a misprint. The single kasra on names where tanween is due counts as a printing habit, not a reading.
2. **Commentary (step 5): transcribe from the scans.** v1's commentary is a different text, so it can't be a second reading. The OCR text becomes the draft: each page is proofread against the scan and split into word meanings and benefits. The 31 printed hadith of this audit are the test set the pilot is scored on.
3. **Numbering (step 3):** a full mapping from v1's ids to the book's numbers, built from the text. `old_id` is needed.
4. **Format:** `shared_with` is needed. The conversion must recognise the «أفادت الأحاديث …» headings.
