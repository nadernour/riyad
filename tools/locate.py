"""Find the PDF pages where each v1 hadith and its commentary are printed.

Usage: python tools/locate.py [ID ...]

Every v1 hadith is located in the OCR text, in book order: its first words give the page
where it starts, and the last words of its commentary the page where it ends. The OCR text
has mistakes, so pages are matched on shared runs of three words rather than exact text.
Each search looks near the previous hadith first, so a short hadith quoted elsewhere in the
book isn't mistaken for its own page. The result is saved to .cache/locate.json; the share
of runs found is kept as a confidence, and hadith below LOW are listed for checking by hand.
"""

import argparse
import json
from collections import Counter, defaultdict

from arabic import words
from sources import CACHE, ocr_pages, plain, v1_hadiths

PROBE = 30     # words taken from each end of a text
AHEAD = 25     # pages after the previous hadith searched first
LOW = 0.3      # confidence below which a page is doubtful
OUT = CACHE / "locate.json"


def trigrams(ws: list[str]) -> list[tuple[str, str, str]]:
    return list(zip(ws, ws[1:], ws[2:]))


def page_index() -> dict[tuple[str, str, str], set[int]]:
    """Which PDF pages (1-based) each run of three OCR words is on."""
    pages = defaultdict(set)
    for n, text in enumerate(ocr_pages(), start=1):
        for t in trigrams(words(text)):
            pages[t].add(n)
    return pages


def best_page(index, ws: list[str], first: int, last: int) -> tuple[int | None, float]:
    """The page in first..last sharing the most three-word runs with ws, and the share found."""
    runs = trigrams(ws)
    if not runs:
        return None, 0.0
    votes = Counter(p for t in runs for p in index.get(t, ()) if first <= p <= last)
    if not votes:
        return None, 0.0
    page, hits = max(votes.items(), key=lambda kv: (kv[1], -kv[0]))
    return page, round(hits / len(runs), 2)


def locate_all() -> dict[int, dict]:
    index = page_index()
    pages = len(ocr_pages())
    found, previous = {}, 1
    for i, h in v1_hadiths().items():
        matn, sharh = words(plain(h["matn"])), words(plain(h["sharh"]))
        start, start_conf = best_page(index, matn[:PROBE], previous, previous + AHEAD)
        if start_conf < LOW:  # not near the previous hadith: search the whole book
            start, start_conf = max([(start, start_conf), best_page(index, matn[:PROBE], 1, pages)],
                                    key=lambda r: r[1])
        end, end_conf = best_page(index, (sharh or matn)[-PROBE:], start or previous, (start or previous) + 30)
        if end_conf < LOW:  # the commentary's end wasn't found: v1 may have added to it
            end = start
        found[i] = {"start": start, "end": end or start, "start_confidence": start_conf,
                    "end_confidence": end_conf}
        if start and start_conf >= LOW:
            previous = start
    OUT.write_text(json.dumps(found, indent=1), encoding="utf-8")
    return found


def load() -> dict[int, dict]:
    if not OUT.exists():
        return locate_all()
    return {int(k): v for k, v in json.loads(OUT.read_text(encoding="utf-8")).items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", type=int, nargs="*")
    args = parser.parse_args()
    found = locate_all()
    for i in args.ids or [i for i, f in found.items()
                           if min(f["start_confidence"], f["end_confidence"]) < LOW]:
        f = found[i]
        print(f"{i}: pages {f['start']}–{f['end']} "
              f"(confidence {f['start_confidence']} / {f['end_confidence']})")


if __name__ == "__main__":
    main()
