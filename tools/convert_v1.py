"""Content steps 2 and 3: build content/hadith/ from the v1 database and content/numbering.json.

Usage: python tools/convert_v1.py [--force]

Writes content/hadith/NN.json, one file per book (كتاب), with its chapters and hadith.

Step 2 takes over what v1 has right: the matn (as pieces with speaker roles, from v1's tags),
the short titles, the book and chapter structure and v1's ids. v1's commentary is not taken
over: the audit (docs/audit.md) showed it is an edited version of the book's, so the word
meanings and benefits are transcribed from the scans in step 5. Text changes:
- the salutation, which v1 writes out in several spellings, becomes the glyph ﷺ, as the book prints it;
- Arabic presentation forms (a few v1 words are stored in them) become ordinary letters;
- runs of spaces become one space; a number v1's source left at the start of a hadith («23-») goes.

Step 3 gives every hadith the book's number and page, and every chapter the book's number,
following content/numbering.json (tools/numbering.py and tools/chapters.py found and check it):
v1 hadith holding two printed ones are split at v1's separator line, a repeated matn is dropped,
a cross-reference the book doesn't number is left out, hadith v1 lacks are added from the file,
and a chapter v1 lacks is added where it holds a hadith.

The build checks that every word of v1's matn survives, that the book's numbers 1–1898 are each
used once, that pages rise with the numbers, and that the chapter numbers agree with the
numbered chapter headings in the OCR text. It refuses to overwrite content/hadith/ once
word meanings, benefits or corrections have been added to it (steps 4 and 5), unless --force.
"""

import argparse
import json
import re
import unicodedata

from arabic import words
from chapters import anchors, headings, match, moved, v1_chapters
from numbering import EXCEPTIONS, align, mapping
from sources import ROOT, v1_hadiths

OUT_DIR = ROOT / "content" / "hadith"
TOTAL = 1898
ROLES = {"p0": "prophet", "p1": "speech", "p2": "gloss"}
SALUTATION = re.compile(r"صَ?ل[َّ]*ى\s+ال?ل[َّ]*هُ?\s+عَ?لَ?يْ?هِ?\s+و[َ]?سَ?ل[َّ]*َ?مَ?")
PRESENTATION = re.compile(r"[ﭐ-ﷹﷻ-﷿ﹰ-﻿]+")
SEPARATOR = re.compile(r"\n?[ \t]*(?:_{4,}|ـ{4,})[ \t]*\n?")
NUMBER_PREFIX = re.compile(r"^(\s*(?:</?p[0-2]>)?\s*)[0-9٠-٩]{1,4}\s*-\s*")


def clean(text: str) -> str:
    text = PRESENTATION.sub(lambda m: unicodedata.normalize("NFKC", m.group()), text)
    text = SALUTATION.sub("ﷺ", text)
    text = re.sub(r"\s*-\s*ﷺ\s*-\s*", " ﷺ ", text)  # «الرسول -صلى الله عليه وسلم-»
    return re.sub(r"[ \t ]+", " ", text)


def matn_pieces(matn: str) -> list[dict]:
    """v1's matn as [{role, text}]: <p0> the Prophet's words, <p1> other people's words,
    <p2> a word Nawawi explains, and untagged text the narration."""
    pieces, role = [], "narration"
    for token in re.split(r"(</?p[0-2]>)", matn):
        tag = re.fullmatch(r"<(/?)(p[0-2])>", token)
        if tag:
            role = "narration" if tag.group(1) else ROLES[tag.group(2)]
            continue
        text = clean(token)
        if not text.strip():
            if pieces:
                pieces[-1]["text"] += text  # keep the space between two pieces
            continue
        if pieces and pieces[-1]["role"] == role:
            pieces[-1]["text"] += text
        else:
            pieces.append({"role": role, "text": text})
    for p in pieces:
        p["text"] = re.sub(r" *\n *", "\n", p["text"])
    if pieces:
        pieces[0]["text"] = pieces[0]["text"].lstrip()
        pieces[-1]["text"] = pieces[-1]["text"].rstrip()
    return [p for p in pieces if p["text"]]


def text_words(raw: str) -> list[str]:
    return words(clean(re.sub(r"</?p[0-2]>", " ", raw)))


def parts(i: int, raw: str, ex: dict, hadiths: dict) -> list[str]:
    """v1 hadith i's raw matn, as one part per printed hadith it holds."""
    merged = {m["v1"]: m["numbers"] for m in ex["merged"]}
    repeats = {d["v1"]: d["repeats"] for d in ex["duplicated"]}
    out = [raw]
    if i in merged:
        out = [p for p in SEPARATOR.split(raw) if p.strip()]
        if len(out) != merged[i]:
            raise SystemExit(f"v1 {i}: {len(out)} parts at its separator lines, content/numbering.json says {merged[i]}")
    if i in repeats:
        repeated = text_words(hadiths[repeats[i]]["matn"])
        lines = raw.split("\n")
        k = next(k for k in range(1, len(lines)) if text_words("\n".join(lines[:k])) == repeated)
        out = ["\n".join(lines[k:])]
    return [NUMBER_PREFIX.sub(r"\1", p.strip("\n")) for p in out]


def check_words(raw: str, kept: list[str], pieces: list[list[dict]], i: int, dropped: bool) -> None:
    """Every word of the parts must survive the conversion into pieces."""
    for part, ps in zip(kept, pieces):
        if text_words(part) != words("".join(p["text"] for p in ps)):
            raise SystemExit(f"v1 {i}: the conversion lost or changed words")
    if not dropped:
        joined = [w for part in kept for w in text_words(part)]
        before = [w for w in text_words(raw) if not w.isdigit()]
        if [w for w in joined if not w.isdigit()] != before:
            raise SystemExit(f"v1 {i}: splitting lost or changed words")


TITLE_BAND = 4    # how far from its own hadith a v1 title may have slipped
TITLE_FIT = 0.5   # share of a title's words that must be in the matn it is given to


def stem(w: str) -> str:
    """A word without a leading conjunction or preposition and without the article, so that
    «و ماله» meets «وماله» and «الرسول» meets «رسول»."""
    w = re.sub(r"^[وف]?[بلك]?(?=..)", "", w)
    return re.sub(r"^ال(?=..)", "", w)


def title_fit(title: str, matn: str) -> float:
    t = [stem(w) for w in words(re.sub(r"[^\w\s]|_", " ", title)) if len(w) > 1]
    m = {stem(w) for w in text_words(matn)}
    return sum(w in m for w in t) / max(1, len(t))


def realign_titles(hadiths: dict) -> dict[int, str | None]:
    """The short title for each v1 hadith. v1's titles slip out of step with its texts in places
    (e.g. v1 455–486 each carry the next hadith's title), so titles and texts are paired again in
    order, each title going to the text it fits best within TITLE_BAND; a text whose best title
    fits less than TITLE_FIT gets none."""
    ids = sorted(hadiths)
    n = len(ids)
    fit = {}
    for a in range(n):
        for b in range(max(0, a - TITLE_BAND), min(n, a + TITLE_BAND + 1)):
            fit[a, b] = title_fit(hadiths[ids[a]]["title"], hadiths[ids[b]]["matn"])
    # order-keeping pairing of titles (a) with texts (b) that maximizes the total fit
    score = {(-1, -1): 0.0}
    back = {}
    for a in range(-1, n):
        for b in range(max(-1, a - TITLE_BAND - 1), min(n, a + TITLE_BAND + 2)):
            if (a, b) == (-1, -1):
                continue
            options = []
            if a >= 0 and (a - 1, b) in score:
                options.append((score[a - 1, b], (a - 1, b), None))           # title a unused
            if b >= 0 and (a, b - 1) in score:
                options.append((score[a, b - 1], (a, b - 1), None))           # text b without a title
            if a >= 0 and b >= 0 and (a - 1, b - 1) in score and (a, b) in fit:
                options.append((score[a - 1, b - 1] + fit[a, b], (a - 1, b - 1), (a, b)))
            if options:
                best = max(options, key=lambda o: o[0])
                score[a, b], back[a, b] = best[0], best[1:]
    out = {i: None for i in ids}
    cell = (n - 1, n - 1)
    while cell != (-1, -1):
        prev, pair = back[cell]
        if pair and fit[pair] >= TITLE_FIT:
            out[ids[pair[1]]] = hadiths[ids[pair[0]]]["title"]
        cell = prev
    used = set(out.values())
    for i in ids:  # a hadith left without a title keeps its own, unless another text took it
        if out[i] is None and hadiths[i]["title"] not in used:
            out[i] = hadiths[i]["title"]
    return out


def chapter_numbers(chapters: list[dict], ex: dict) -> dict[int, int]:
    """The book's number for each v1 chapter, in order, skipping the chapters v1 lacks."""
    skip = {c["number"] for c in ex["chapters_missing"]}
    out, n = {}, 1
    for c in chapters:
        while n in skip:
            n += 1
        out[c["door_id"]] = n
        n += 1
    return out


def pages_in_order(records: list[dict]) -> None:
    """Pages must rise with the book's numbers. Keep the longest run of pages that does, and
    re-align every other hadith between the trusted pages around it: its first alignment found
    a similar passage elsewhere in the book."""
    n = len(records)
    best, prev = [1] * n, [-1] * n
    tails, tail_idx = [], []  # longest non-decreasing subsequence, O(n log n)
    import bisect
    for k, r in enumerate(records):
        j = bisect.bisect_right(tails, r["page"])
        if j == len(tails):
            tails.append(r["page"]); tail_idx.append(k)
        else:
            tails[j] = r["page"]; tail_idx[j] = k
        prev[k] = tail_idx[j - 1] if j else -1
    trusted, k = set(), tail_idx[-1]
    while k >= 0:
        trusted.add(k)
        k = prev[k]
    for k, r in enumerate(records):
        if k in trusted:
            continue
        lo = next((records[j]["page"] for j in range(k - 1, -1, -1) if j in trusted), 1)
        hi = next((records[j]["page"] for j in range(k + 1, n) if j in trusted), lo)
        found = align({"matn": r["_raw"]}, lo + 1, last_page=hi) if r["_raw"] else {"span": None}
        page = r["_where"](found) if found["span"] else lo
        r["page"] = min(max(page, lo), hi)


def build() -> list[dict]:
    ex = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    hadiths = v1_hadiths()
    numbers = mapping()
    move = moved()
    unnumbered = {u["v1"] for u in ex["unnumbered"]}
    from numbering import book_words, cached
    rows = {r["old_id"]: r for r in cached()}
    where = book_words()[1]

    def page_of(found):
        return where[found["span"][0]][0]

    titles = realign_titles(hadiths)
    written = {int(k): v for k, v in ex["titles"].items() if k.isdigit()}
    records = []
    for i, h in hadiths.items():
        if i in unnumbered:
            continue
        kept = parts(i, h["matn"], ex, hadiths)
        pieces = [matn_pieces(k) for k in kept]
        check_words(h["matn"], kept, pieces, i, dropped=i in {d["v1"] for d in ex["duplicated"]})
        own = titles[i] and max(range(len(kept)), key=lambda k: title_fit(titles[i], kept[k]))
        for k, (part, ps, number) in enumerate(zip(kept, pieces, numbers[i])):
            row = rows[i]
            title = clean(titles[i]).strip() if titles[i] and k == own else written.get(number)
            page = row["page"] if k == 0 else page_of(align({"matn": part}, row["page"])) if part else row["page"]
            records.append({
                "id": number, "old_id": i, "page": page,
                "title": title,
                "matn": ps, "meanings": [], "benefits": [], "shared_with": None, "corrections": [],
                "notes": ([] if k == 0 else [f"Split from v1 {i}, which holds two printed hadith."])
                         + ([f"v1's title «{clean(h['title']).strip()}» belongs to another hadith (v1's titles slip here)."]
                            if titles[i] is not None and titles[i] != h["title"] and k == own else [])
                         + (["Short title written in step 3 (not from v1), for the owner to review."] if number in written else []),
                "_door": move.get(i, h["door_id"]), "_raw": part, "_where": page_of,
            })
    for m in ex["missing"]:
        records.append({
            "id": m["number"], "old_id": None, "page": m["page"], "title": written[m["number"]], "matn": m["matn"],
            "meanings": [], "benefits": [], "shared_with": None, "corrections": [],
            "notes": [f"Not in v1 ({m['kind']}); added in step 3 from the scan. {m['note']} Step 4 checks its matn"
                      " at high zoom.", "Short title written in step 3 (not from v1), for the owner to review."],
            "_chapter_number": m["chapter"], "_raw": "", "_where": page_of,
        })
    records.sort(key=lambda r: r["id"])
    pages_in_order(records)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    for f in OUT_DIR.glob("*.json"):
        book = json.loads(f.read_text(encoding="utf-8"))
        edited = any(h["meanings"] or h["benefits"] or h["corrections"]
                     for c in book["chapters"] for h in c["hadith"])
        if edited and not args.force:
            raise SystemExit(f"{f.relative_to(ROOT)} already has transcribed content; rerun with --force to overwrite it")

    ex = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    records = build()
    ids = [r["id"] for r in records]
    if sorted(ids) != list(range(1, TOTAL + 1)):
        raise SystemExit(f"the book's numbers don't run 1–{TOTAL} once each")
    late = [(a["id"], b["id"]) for a, b in zip(records, records[1:]) if b["page"] < a["page"]]
    print(f"{len(records)} hadith; pages that go back: {late or 'none'}")

    chapters = v1_chapters()
    numbers = chapter_numbers(chapters, ex)
    match(chapters, headings())
    disagree = [(numbers[chapters[k]["door_id"]], n) for k, n in anchors(chapters) if numbers[chapters[k]["door_id"]] != n]
    print(f"{len(chapters)} v1 chapters numbered; OCR headings that disagree: {disagree or 'none'}")

    hadiths = v1_hadiths()
    door_book = {h["door_id"]: (h["book_id"], h["book"]) for h in hadiths.values()}
    door_title = {h["door_id"]: h["door"] for h in hadiths.values()}
    by_number = {numbers[d]: d for d in numbers}
    added = {c["number"]: c for c in ex["chapters_missing"] if "after_chapter" in c}
    books: dict[int, dict] = {}
    chapter_rec: dict[int, dict] = {}
    for n in sorted(set(numbers.values()) | set(added)):
        if n in added:
            door, book_id = None, door_book[by_number[added[n]["after_chapter"]]][0]
            title, old = added[n]["title"], None
        else:
            door = by_number[n]
            book_id = door_book[door][0]
            title, old = clean(door_title[door]).strip(), door
        book = books.setdefault(book_id, {"old_id": book_id, "title": clean(door_book[by_number[min(
            k for k in numbers.values() if door_book[by_number[k]][0] == book_id)]][1]).strip(), "chapters": []})
        rec = {"number": n, "old_id": old, "title": title, "hadith": []}
        if old is None:
            rec["notes"] = [f"Not in v1; added in step 3. {added[n]['note']} Its title is from the scan (page {added[n]['page']})."]
        book["chapters"].append(rec)
        chapter_rec[n] = rec
    for r in records:
        n = r.pop("_chapter_number", None) or numbers[r["_door"]]
        for key in ("_door", "_raw", "_where"):
            r.pop(key, None)
        chapter_rec[n]["hadith"].append(r)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in OUT_DIR.glob("*.json"):
        f.unlink()
    for n, book in sorted(books.items()):
        out = OUT_DIR / f"{n:02d}.json"
        out.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{out.relative_to(ROOT)}  chapters {book['chapters'][0]['number']}–{book['chapters'][-1]['number']},"
              f" hadith {book['chapters'][0]['hadith'][0]['id']}–{book['chapters'][-1]['hadith'][-1]['id']}  {book['title']}")


if __name__ == "__main__":
    main()
