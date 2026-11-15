# The second reading of the hadith text

Content step 4 (see the README, and [matn.md](matn.md) for the first reading and the rules). The review rounds corrected v1's text to the book's. They ran on Opus at medium effort, and the owner asked for all their work to be checked (2026-11-15), as was done in his azkar project: **every hadith is read once more against the scan, as its text now stands, and every decision the rounds made is judged.** Nothing here needs the first reading to be redone: the text in `content/hadith/` is the starting point, and a round only changes what the scan shows to be wrong.

Started by Claude Fable on 2026-11-15, which built the tool, read h. 1–8 and ran the checks below. The rest is done in rounds like the first reading's, by `tools/long_run.sh` with `REVIEW=1` (below).

## What the start found

- **Words v1 lacks were missed.** h. 6 had «تَجْعلُ فِي امْرَأَتكَ» where the print has «فِي فِي ٱمْرَأَتِكَ», and h. 476 «غَطَّيْنَا رِجْلَيْهِ» where the print has «غَطَّيْنَا بِهَا رِجْلَيْهِ». The first reading's tool never listed a short word (one or two letters) that the OCR text has and v1 lacks, and the round's eye skipped it as v1's had. So `tools/review.py` now compares the text with sunnah.com's as well, and lists (with a `*`) every place where sunnah.com has other words and the OCR text doesn't have ours. Of the 61 places where the OCR text has sunnah.com's words exactly, most are spellings (rule 4: «بسم» / «باسم», «أولو» / «أولوا», «ههنا» / «هاهنا») or misprints already recorded (h. 21 «وسار», h. 384, h. 1525). Read on the scan so far: h. 6 and h. 476 (the text was wrong), and h. 72 «طريف», h. 210 (no «إلى اليمن»), h. 1377 «يفقهه», h. 1484 «منيي», h. 1785 «النزغ» (the text is right). Still to read, in their rounds: h. 21 «ولكنني», h. 731 «يديهما», h. 1448 «مما», h. 1869 «بينهما».
- **A dot can need a zoom.** h. 1785's «النَّزْغِ» looks like «النزع» on the crop, and the dot of the ghayn shows only on a zoom. The round had read it right. Don't overturn a round's reading from a crop: zoom first.
- **The pilot's 30 hadith still have bare words** (h. 8: «أبي», «رسول الله», «في», «عليه»). The second reading gives them the book's marks (rule 2), and the shaddas that h. 126–168 and the pilot's hadith lack. So the two passes that [matn.md](matn.md) lists for these are done by this reading.
- Rebuilding `content/hadith/` from v1 and applying every decision again gives the committed text exactly, before and after the changes above.

## What is judged

For each hadith, `tools/review.py next` prints:

- the crops of its matn on the scan, one per page;
- its text as it stands;
- `rounds:` the first reading's fixes that change a letter or a mark of v1's (`v1`, `variant`), and how many fixes only gave marks to bare words;
- `misprint recorded:` and `note:` what the first reading recorded;
- `no marks:` the words still bare, to be given the book's marks;
- `*` lines: sunnah.com has other words here, and the OCR text doesn't have ours;
- numbered lines: what the OCR text or the collections still have otherwise (the kinds are in [matn.md](matn.md)).

Read the whole matn on the crops against the text, word by word, to its end. Then judge:

1. **Every `*` line and every numbered line:** which is right, the text or the source? Most numbered lines are the OCR text's misreadings. A `*` line that says the OCR text has sunnah.com's words is nearly always a spelling or a real difference: zoom on it unless it is a spelling rule 4 leaves alone.
2. **Every `variant` fix and every `v1` fix that changes letters:** does the print have the round's words? Read them on a zoom if the crop leaves any doubt.
3. **Every recorded misprint:** is the printed form really what the print has (zoom), and is it a misprint by rule 1, not the book's wording?
4. **Every note:** is it still true and still worth the owner's time? Set it again in better words, or to "" if the question is settled.
5. **Everything else you see:** a word the text lacks or adds, another letter, a mark that conflicts with the print's (case endings and verb vowels most of all), a bare word the print marks, a letter the print doubles in a word marked in part.

## The rules

The rules of [matn.md](matn.md) ("The rules", 1–7) apply unchanged: read them before the first hadith. What they leave alone stays alone: spelling that doesn't change the reading, punctuation, the speaker roles, the marks v1 has where the print has none, the letters v1 leaves bare in a word it marks in part (except a shadda), and the print's habits (a single kasra for tanween, a sukun before a connecting alif, the wasla, a stretched word). On top of them:

- **Change only what a zoom shows.** A crop is enough to see that the text and the print agree. It is not enough to change a letter, a dot or a mark: zoom on the word (`review.py zoom`), half the page wide at most, and compare a doubtful mark with the same mark on a word whose reading is certain. If the zoom still leaves a doubt, keep the text and say so in the note.
- **Count repeated words** on a zoom («فِي فِي», «هكذا وهكذا وهكذا»): the eye drops one.
- **A round's reading stands unless the zoom contradicts it.** Don't swap one good reading for another: where both are good Arabic and the zoom doesn't settle it, the text stays.
- **Give each change its reason,** in a sentence: what the print has, where you read it, and what the text had.

## One round

`tools/long_run.sh`, started with `REVIEW=1`, starts a fresh Claude Code session for each round with the prompt "Do one round of the second reading: follow docs/matn-review.md exactly." A round reads up to 12 hadith (900 words of matn in all; a longer hadith is a round of its own) and stops.

1. **Read** this file and "The rules" in `docs/matn.md` (rules 1–7 and "The decision for a hadith"), and nothing else the round doesn't need. The tools' usage is here, so don't read their source.
2. If `content/matn/review-inbox.json` exists, an earlier round didn't finish. Run `.venv/bin/python tools/review.py apply`, fix what it reports in the inbox, and run it again until it applies. Then go on.
3. **Run** `.venv/bin/python tools/review.py next`. If it says all are read, stop.
4. **Read all the round's crops at once** (one message with a Read call for each), then each hadith as "What is judged" says.
5. **Zoom** on every word you mean to change and on every doubt the crop doesn't settle: `.venv/bin/python tools/review.py zoom 12.2:0.30-0.38:0.5-1 14.1:0.1-0.2:0-0.5`. Each spot is `HADITH.CROP:TOP-BOTTOM:LEFT-RIGHT`: the crop's number among the hadith's crops, the top and bottom as shares of that crop (0 is its top, 1 its bottom), and the left and right as shares of the page's width. A line is about 0.035 of the page, so on a crop that covers 0.38–0.91 of the page a line is about 0.07 of the crop. The edges move out to the gaps between lines. Do all of the round's spots in one command and read the zooms together.
6. **Write** `content/matn/review-inbox.json`, with an entry for every hadith of the round, in one Write:

   ```json
   {
    "9": {},
    "6": {"fix": [["تَجْعلُ فِي امْرَأَتكَ", "تَجْعلُ فِي فِي امْرَأَتكَ", "v1", "The print has «فِي فِي ٱمْرَأَتِكَ» (zoomed, p. 23); v1 has one «في»."]]},
    "30": {"drop_misprint": ["فَإِنَ آمَنْتَ"], "note": ""},
    "31": {"misprint": [["printed words", "the correction", "the reason"]], "note": "what the owner should know"}
   }
   ```

   - `{}`: the text is right as it stands, and so are its recorded misprints and its note.
   - `fix`: `[from, to, why, reason]`. `from` is copied from the text as `next` printed it and must occur once in it; `why` is `"v1"`, `"variant"` or `"marks"` as in `docs/matn.md`. To take back a round's fix, write the fix that puts the right words back.
   - `misprint`: a misprint of the book's to record. `drop_misprint`: the printed words of a recorded misprint that isn't one (then fix the text too, if it should have the print's words).
   - `note`: sets the hadith's note for the owner; "" removes it.
7. **Run** `.venv/bin/python tools/review.py apply`. It keeps the entries that failed in the inbox and says why. Correct them and run it again.
8. **Stop** with a one-line summary: the hadith read, how many were changed, and each change in a few words.

**What a round may do.** Read any file, write `content/matn/review-inbox.json`, and run the project's tools as plain commands from `book_data/`. Write no `cd`, pipes, `python -c` or other shell commands: anything else is refused, because nobody is there to approve it. Never commit to git, and never change `docs/` or `tools/`. If a rule or a tool seems wrong, say so in the summary and carry on with the rules as they are.

## Running it

```sh
REVIEW=1 EFFORT=high nohup tools/long_run.sh >> .cache/long-run.log 2>&1 &   # Opus, a fresh session per round (ROUNDS=5 to stop after five)
tail -F .cache/long-run.log                                                    # each round's cost, limits, changes and summary
.venv/bin/python tools/review.py status                                        # how many are read again, and the changes so far
pkill -f '[t]ools/long_run.sh'; pkill -f '[c]laude -p Do one round'            # stop it
```

The rounds don't commit. `content/matn/review.json` says which hadith are read and keeps every change with its reason; the changes are also added to the decisions in `content/matn/NN.json`, so `tools/convert_v1.py --force` and `tools/matn.py apply --all` make the same text again. A change to a hadith that isn't read in full yet has `"spot": true` in the inbox, so the hadith stays to be read.

The first round on Opus at high effort (h. 9–18, 2026-11-15) took 3 minutes, 7 zooms, 6% of the 5-hour window and 1% of the weekly limit (≈ $0.78 at API prices). It gave one bare word its mark (h. 12) and recorded one misprint (h. 10, a kasra on the subject of «كانت»); h. 10 was then read again by Claude Fable, which found nothing the round had missed. At that rate the rest is about 190 rounds, which is more than one week's limit: `ROUNDS=N` stops the run after N rounds.

Look at the first rounds' changes before leaving the run unattended (`git diff content/`, and `review.json` for the reasons): a round that changes many marks is more likely misreading the scan than finding the first reading wrong. When all 1,898 are read, the owner reviews `content/matn/review.json`, and the passes after the rounds follow (titles, short titles and speaker roles, in [matn.md](matn.md)).
