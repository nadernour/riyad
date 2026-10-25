# Numbering the hadith as printed

Content step 3 (see the README): every hadith gets the book's number and page, and every chapter the book's chapter number. The result is in `content/hadith/`, built by `tools/convert_v1.py`. The places where v1 doesn't map one to one onto the book are in `content/numbering.json`.

## Result

- **Hadith:** the book numbers 1,898 hadith; v1 has 1,893 entries. Every one of the book's numbers is used exactly once.
- **Pages:** each hadith's page is the PDF page where its matn starts, and pages rise with the numbers.
- **Chapters:** the book numbers 372 chapters (373 is the narrator biographies). v1 has 366; the six it lacks are listed below. Only one of them holds a hadith, so the content has 367 chapters.
- **Titles:** every hadith has a short title. 48 of v1's titles were moved to the hadith they belong to, and 8 were written in this step (listed below).

## How it was checked

1. **Alignment.** Each v1 matn was aligned word by word with the book's OCR text, in book order (`tools/numbering.py`). Where the OCR kept the number printed above a hadith (about 45% of them), it was read.
2. **The gap.** The difference between the book's number and v1's id holds steady over long runs. Each of the seven places where it changes was settled on the scan.
3. **The mapping.** Built from `content/numbering.json`, it was compared with all 864 numbers the OCR kept:
   - 817 agree;
   - each of the other 47 is a number the reader attached to the neighbouring hadith, an OCR misread (e.g. «٧٤٠» for ٧٤٤), or the book's own misprint below.
4. **Chapters** (`tools/chapters.py`). v1's chapters were matched to the chapter headings in the OCR text by their titles. All 235 headings whose number the OCR kept agree with the chapter numbers given.
5. **The audit.** The 30 hadith of the audit, whose numbers and pages were read from the scans by hand, all agree with the built content.

## Where v1 and the book differ

| Book | v1 | What | Effect on the gap |
|---|---|---|---|
| 153 | — | A cross-reference the book numbers («حديث عائشة … وقد سبق في الباب قبله»); v1 skips it | +1 |
| 172 | — | A cross-reference the book numbers («وعن العرباض بن سارية … حديثه السابق»); v1 skips it | +1 |
| 297, 298 | 295 | Two printed hadith in one v1 entry | +1 |
| — | 454 | A cross-reference v1 makes an entry of, but the book doesn't number; left out | −1 |
| 712, 713 | 710 | Two printed hadith in one v1 entry | +1 |
| 1126 | — | A cross-reference the book numbers, opening chapter 203; v1 skips it | +1 |
| 1548 | — | Umm Kulthum's hadith in chapter 261, which v1 lacks (v1 has the same hadith as 249) | +1 |

Other differences that don't change the count:

- **v1 357 repeats v1 356's matn** (the book's 359) ahead of its own (the book's 360). The repeat is dropped.
- **v1 1529 is filed under the wrong chapter.** It belongs to باب ما يباح من الغيبة.
- **Numbers left in v1's text.** v1 23, 555, 646, 1014, 1033, 1823 and 710 start with a number from v1's source («23-»). It is removed; v1 1823's «1826-» was wrong anyway (it is the book's 1828).
- **The book prints ٧٢٧ twice**, for the 6th and 7th hadith of its chapter. The first is 726 in the sequence.

The four hadith v1 lacks were transcribed from the scan in this step, and step 4 checks their tashkeel at high zoom.

### Chapters v1 lacks

| Chapter | Title | Why |
|---|---|---|
| 9 | باب التفكر في عظيم مخلوقات الله تعالى | Verses only, no numbered hadith |
| 70 | باب فضل الاختلاط بالناس | No numbered hadith |
| 126 | باب استحباب الابتداء باليمين في اللباس | No numbered hadith |
| 202 | باب سنة العشاء بعدها وقبلها | A cross-reference only |
| 261 | باب بيان ما يجوز من الكذب | Holds hadith 1548; added to the content |
| 265 | باب جواز لعن أصحاب المعاصي غير المعينين | No numbered hadith |

The chapters with no hadith aren't in the content, since the app shows hadith.

### Titles

The short titles aren't in the book; v1 has them, and the app shows them above each hadith.

- **v1's titles slip out of step with its texts in places.** From v1 454 to 485 each entry carries the next hadith's title, and the same happens at v1 1570 and 1598–1615. It looks like v1's source added an entry to its texts without adding one to its titles. The build pairs titles and texts again in order, each title going to the text it fits best (48 titles moved).
- **8 hadith have no v1 title:**
  - the four v1 lacks;
  - the second half of each merged entry;
  - two whose title was lost to the slip.

  Step 3 wrote these titles from the hadith's own words, for the owner to review:

| Book | Title |
|---|---|
| 153 | أحب الدين إليه ما داوم صاحبه عليه |
| 172 | وعظنا الرسول موعظة وجلت منها القلوب |
| 298 | اليد العليا خير من اليد السفلى |
| 712 | أذكركم الله في أهل بيتي |
| 1126 | صلى مع النبي ركعتين بعد الجمعة |
| 1548 | ليس الكذاب الذي يصلح بين الناس |
| 1575 | إياكم والظن فإن الظن أكذب الحديث |
| 1603 | لعن من اتخذ شيئاً فيه الروح غرضاً |

## For step 4

- **Poorly matched entries.** 29 v1 entries matched the OCR text poorly (under half their words found): 97, 244, 245, 357, 454, 478, 506, 530, 726, 744, 745, 773, 803, 807, 808, 829, 860, 1149, 1178, 1181, 1272, 1273, 1326, 1327, 1336, 1341, 1347, 1364 and 1579 (`.venv/bin/python tools/numbering.py` lists them). Their numbers are confirmed by the markers around them, but their matn may differ from the print more than usual.
- **The four added hadith** need their tashkeel checked at high zoom.
- **Chapter titles** are v1's for now. They are checked against the headings in step 4.
