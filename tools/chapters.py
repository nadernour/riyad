"""Content step 3: the book's chapter (باب) numbers for v1's chapters.

Usage: python tools/chapters.py      match v1's chapters to the book's and list where they differ

The book numbers its chapters 1–372 (373 is the narrator biographies). v1 has the chapters in
the book's order but without numbers, and lacks a few. Each v1 chapter is matched to a heading
in the OCR text («١٥ - باب …», sometimes with ٥ read as ه) by the words of its title, near the
page of its first hadith; where the heading's number survived, the chapter takes it. Between two
such anchors, v1 should have as many chapters as the numbers between them; where it has fewer,
the book has chapters v1 lacks, and the bracket is listed for checking. The result is saved to
.cache/chapters.json.
"""

import json
import re

from arabic import words
from numbering import OUT as NUMBERING, page_lines
from sources import CACHE, v1_hadiths

OUT = CACHE / "chapters.json"
LAST = 372
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹ه", "012345678901234567895")
HEADING = re.compile(r"^[-–ـ۔]?\s*([0-9٠-٩۰-۹ه]{1,3})?\s*[-–ـ۔]?\s*(باب\b.*)")
BODY = (15, 1300)     # pages before the indexes
NEAR_PAGES = 6        # how far from its first hadith a chapter's heading is looked for
SHARE = 0.6           # share of a heading's words that must be in the v1 title



def moved() -> dict[int, int]:
    """v1 hadith filed under the wrong chapter (content/numbering.json): v1 id -> v1 chapter id."""
    from numbering import EXCEPTIONS
    hadiths = v1_hadiths()
    return {m["v1"]: hadiths[m["to_chapter_of"]]["door_id"]
            for m in json.loads(EXCEPTIONS.read_text(encoding="utf-8"))["moved"]}


def v1_chapters() -> list[dict]:
    """v1's chapters in book order, each with its hadith and the page of its first one."""
    rows = {r["old_id"]: r for r in json.loads(NUMBERING.read_text(encoding="utf-8"))}
    MOVED = moved()
    chapters: dict[int, dict] = {}
    for i, h in v1_hadiths().items():
        door = MOVED.get(i, h["door_id"])
        c = chapters.setdefault(door, {"door_id": door, "title": h["door"] if door == h["door_id"] else None,
                                       "hadith": [], "page": rows[i]["page"]})
        c["title"] = c["title"] or h["door"]
        c["hadith"].append(i)
    return sorted(chapters.values(), key=lambda c: c["hadith"][0])


def headings() -> list[dict]:
    out = []
    for n in range(BODY[0], BODY[1] + 1):
        for i, line in enumerate(page_lines(n)):
            m = HEADING.match(line)
            if not m or len(line) > 120:
                continue
            raw = m.group(1)
            number = int(raw.translate(DIGITS)) if raw and re.search(r"[0-9٠-٩۰-۹]|^ه$", raw) else None
            out.append({"page": n, "line": i, "number": number if number and number <= LAST else None,
                        "words": words(m.group(2))[1:]})
    return out


def match(chapters: list[dict], heads: list[dict]) -> None:
    """Give each v1 chapter the OCR heading that best fits its title, near its first hadith."""
    for c in chapters:
        title = set(words(c["title"])[1:])
        best = None
        for h in heads:
            if not h["words"] or abs(h["page"] - c["page"]) > NEAR_PAGES:
                continue
            share = len(set(h["words"]) & title) / len(set(h["words"]))
            key = (share, -abs(h["page"] - c["page"]))
            if share >= SHARE and (best is None or key > best[0]):
                best = (key, h)
        c["heading"] = best[1] if best else None


def anchors(chapters: list[dict]) -> list[tuple[int, int]]:
    """(index in v1's chapters, the book's chapter number) where the heading's number survived,
    keeping the longest run that rises in both."""
    cand = [(k, c["heading"]["number"]) for k, c in enumerate(chapters) if c["heading"] and c["heading"]["number"]]
    best, prev = [1] * len(cand), [-1] * len(cand)
    for j, (kj, nj) in enumerate(cand):
        for i, (ki, ni) in enumerate(cand[:j]):
            if ni < nj and nj - ni >= kj - ki and best[i] + 1 > best[j]:
                best[j], prev[j] = best[i] + 1, i
    j = max(range(len(cand)), key=best.__getitem__)
    out = []
    while j >= 0:
        out.append(cand[j])
        j = prev[j]
    return out[::-1]


def main() -> None:
    chapters = v1_chapters()
    match(chapters, headings())
    fixed = anchors(chapters)
    print(f"{len(chapters)} v1 chapters; {sum(1 for c in chapters if c['heading'])} matched to a heading,"
          f" {len(fixed)} anchored by its number")
    # number the chapters between anchors; list brackets where v1 lacks chapters
    bounds = [(-1, 0)] + fixed + [(len(chapters), LAST + 1)]
    brackets = []
    for (k0, n0), (k1, n1) in zip(bounds, bounds[1:]):
        inside = k1 - k0 - 1
        free = n1 - n0 - 1
        if inside == free:
            for step in range(1, inside + 1):
                chapters[k0 + step]["number"] = n0 + step
        else:
            brackets.append((k0, n0, k1, n1, inside, free))
        if 0 <= k1 < len(chapters):
            chapters[k1]["number"] = n1
    print(f"{len(brackets)} stretches where v1 has fewer chapters than the book:")
    for k0, n0, k1, n1, inside, free in brackets:
        first = chapters[k0 + 1]["hadith"][0] if k0 + 1 < len(chapters) else None
        print(f"  between book chapters {n0} and {n1}: v1 has {inside}, the book {free}"
              f" (v1 hadith from {chapters[k0]['hadith'][0] if k0 >= 0 else 1} to"
              f" {chapters[k1]['hadith'][0] if k1 < len(chapters) else 'end'})")
    OUT.write_text(json.dumps(chapters, ensure_ascii=False, indent=0), encoding="utf-8")


if __name__ == "__main__":
    main()
