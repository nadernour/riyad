"""Content step 3: the book's number for each v1 hadith.

Usage: python tools/numbering.py                     align v1 with the OCR text and list where the numbering shifts
       python tools/numbering.py --show FIRST LAST   v1 hadith FIRST..LAST in the OCR text, and what lies between them
       python tools/numbering.py --check            compare content/numbering.json with the numbers the OCR kept

The book prints each hadith's number above it, as a fraction: its number in the chapter over
its number in the book. The OCR text keeps these numbers only now and then, and garbles some.

Each v1 matn is aligned word by word with the OCR text, in book order, each search starting
where the previous hadith's matn ended; the alignment gives the hadith's page and line, and the
number printed just above that line is read where the OCR kept it (only a value close to v1's
id is believed). The gap between the book's number and v1's id holds steady over long runs and
changes only where v1 merges, skips or adds a hadith; those places are listed so they can be
settled on the scan, and what was found is recorded in content/numbering.json. --check then
rebuilds the full mapping from that file and compares it with every number the OCR kept.
The alignment is saved to .cache/numbering.json.
"""

import argparse
import difflib
import json
import re
from functools import cache

from arabic import words
from locate import load as load_pages
from sources import CACHE, ROOT, ocr_pages, plain, v1_hadiths

OUT = CACHE / "numbering.json"
EXCEPTIONS = ROOT / "content" / "numbering.json"
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
NUMBER = re.compile(r"[0-9٠-٩۰-۹]{1,4}")
NEAR = (-3, 12)  # the book's number minus v1's id, as far as it is believed to go


@cache
def page_lines(n: int) -> list[str]:
    return [l.strip() for l in ocr_pages()[n - 1].split("\n")]


@cache
def book_words() -> tuple[list[str], list[tuple[int, int]]]:
    """Every OCR word of the book, normalized, with the (page, line) it is on."""
    ws, where = [], []
    for n in range(1, len(ocr_pages()) + 1):
        for i, line in enumerate(page_lines(n)):
            for w in words(line):
                ws.append(w)
                where.append((n, i))
    return ws, where


@cache
def line_start_index() -> dict[tuple[int, int], int]:
    """The index in book_words() of the first word of each (page, line)."""
    first = {}
    for k, pos in enumerate(book_words()[1]):
        first.setdefault(pos, k)
    return first


@cache
def page_start() -> dict[int, int]:
    """The index in book_words() of the first word on each page (pages with no words are left out)."""
    first = {}
    for k, (page, _) in enumerate(book_words()[1]):
        first.setdefault(page, k)
    return first


SEPARATORS = {"رواه", "اخرجه", "لغه", "افاد", "افادت", "تقدم"}  # words of a source note or commentary
BREAK = 12  # OCR words inside a hadith's span, not matched, that may hide another hadith


def align(h: dict, page: int, after: int = 0, last_page: int | None = None) -> dict:
    """Where a v1 matn lies in the OCR text: the span of OCR words it matches, the share of
    its words found, and the unmatched stretches of BREAK or more OCR words inside the span.
    The matn is matched against the page before its start page (from locate.py) and the pages
    after it, as many as its length may need, but not before `after` (where the previous
    hadith's matn ends): the hadith are in the book's order, and a hadith often shares
    phrases with the one before it."""
    ws, where = book_words()
    entry = words(plain(h["matn"]))
    starts = page_start()
    pages = len(ocr_pages())

    def at(n: int) -> int:  # the first word on page n, or on the next page with words
        return next((starts[k] for k in range(n, pages + 1) if k in starts), len(ws))
    lo = at(max(1, page - 1))
    if lo < after <= at(page + 1):
        lo = after
    end_page = min(pages, page + 2 + len(entry) // 200, last_page or pages)
    hi = at(end_page + 1)
    window = ws[lo:hi]
    sm = difflib.SequenceMatcher(None, window, entry, autojunk=False)
    blocks = trim([b for b in sm.get_matching_blocks() if b.size >= 2])
    if not blocks:
        return {"span": None, "found": 0.0, "breaks": []}
    breaks = []
    for a, b in zip(blocks, blocks[1:]):
        gap = b.a - (a.a + a.size)
        if gap >= BREAK:
            text = window[a.a + a.size:b.a]
            breaks.append({"at": where[lo + a.a + a.size], "words": gap,
                           "separators": sorted(SEPARATORS & set(text))})
    return {"span": [lo + blocks[0].a, lo + blocks[-1].a + blocks[-1].size],
            "found": round(sum(b.size for b in blocks) / max(1, len(entry)), 2), "breaks": breaks}


def trim(blocks: list) -> list:
    """Drop matches cut off from the rest by BREAK or more OCR words and holding a small share
    of the matched words: stray matches of common phrases in the hadith before or after."""
    def clusters(bs):
        out = [[bs[0]]] if bs else []
        for a, b in zip(bs, bs[1:]):
            if b.a - (a.a + a.size) >= BREAK:
                out.append([])
            out[-1].append(b)
        return out
    groups = clusters(blocks)
    if not groups:
        return []
    total = sum(b.size for b in blocks)
    keep = [g for g in groups if sum(b.size for b in g) >= 0.2 * total]
    if not keep:
        keep = [max(groups, key=lambda g: sum(b.size for b in g))]
    first, last = groups.index(keep[0]), groups.index(keep[-1])
    return [b for g in groups[first:last + 1] for b in g]


def marker(page: int, line: int, near: int) -> int | None:
    """The book's number printed just above a line, if the OCR kept it: a line of digits among
    the three before it (or the end of the page before), within NEAR of `near`."""
    spots = [(page, page_lines(page)[i]) for i in range(max(0, line - 3), line)]
    if line < 3 and page > 1:
        spots = [(page - 1, l) for l in page_lines(page - 1)[-3:]] + spots
    found = []
    for p, l in spots:
        for m in NUMBER.findall(l):
            n = int(m.translate(DIGITS))
            if n != p and NEAR[0] <= n - near <= NEAR[1]:  # not the page number in the footer
                found.append(n)
    return found[-1] if found else None


def run() -> list[dict]:
    pages = load_pages()
    rows = []
    where = book_words()[1]
    after = 0
    for i, h in v1_hadiths().items():
        found = align(h, pages[i]["start"], after)
        if found["span"]:
            after = found["span"][1]
        page, line = where[found["span"][0]] if found["span"] else (pages[i]["start"], 0)
        rows.append({"old_id": i, "page": page, "line": line, "marker": marker(page, line, i), **found})
    ws = book_words()[0]
    for r, nxt in zip(rows, rows[1:]):  # what lies between one hadith's matn and the next one's
        if r["span"] and nxt["span"]:
            between = ws[r["span"][1]:nxt["span"][0]]
            r["next_gap"] = len(between)
            r["next_separators"] = sorted(SEPARATORS & set(between))
    smooth(rows)
    OUT.write_text(json.dumps(rows, indent=0), encoding="utf-8")
    return rows


CHANGE = 1.5  # the cost of one change of the gap, against 1 for each marker that disagrees


def smooth(rows: list[dict]) -> None:
    """The gap (book number - v1 id) for every v1 hadith: the step function with the fewest
    changes that fits the markers, so that one or two misread markers don't count. A change
    costs CHANGE, a marker that disagrees 1. Sets `gap` and, for the markers it overrules,
    `outlier`."""
    anchors = [r for r in rows if r["marker"] is not None]
    values = range(NEAR[0], NEAR[1] + 1)
    cost = {g: (0 if anchors[0]["marker"] - anchors[0]["old_id"] == g else 1) for g in values}
    back = []
    for a in anchors[1:]:
        seen = a["marker"] - a["old_id"]
        best_prev = min(cost, key=cost.get)
        new, choice = {}, {}
        for g in values:
            stay, move = cost[g], cost[best_prev] + CHANGE
            new[g], choice[g] = (stay, g) if stay <= move else (move, best_prev)
            new[g] += 0 if seen == g else 1
        back.append(choice)
        cost = new
    g = min(cost, key=cost.get)
    gaps = [g]
    for choice in reversed(back):
        g = choice[g]
        gaps.append(g)
    gaps.reverse()
    for a, g in zip(anchors, gaps):
        a["anchor_gap"] = g
        a["outlier"] = a["marker"] - a["old_id"] != g
    gap = gaps[0]
    for r in rows:  # carry each anchor's gap forward to the hadith after it
        gap = r.get("anchor_gap", gap)
        r["gap"] = gap


def report(rows: list[dict]) -> None:
    anchored = [r for r in rows if r["marker"] is not None]
    print(f"{len(rows)} v1 hadith, {len(anchored)} with the book's number read from the OCR")
    print("matched badly (under half their words found):", [r["old_id"] for r in rows if r["found"] < 0.5])
    print("markers overruled as misread:", sum(r["outlier"] for r in anchored))
    print("\nruns of the same gap (book number - v1 id), and where each change lies:")
    runs = []
    for a in anchored:
        if runs and runs[-1]["gap"] == a["anchor_gap"]:
            runs[-1]["last"] = a["old_id"]
            runs[-1]["markers"] += 1
        else:
            runs.append({"gap": a["anchor_gap"], "first": a["old_id"], "last": a["old_id"], "markers": 1})
    for k, run in enumerate(runs):
        print(f"  v1 {run['first']:4}–{run['last']:4}: gap {run['gap']:+d}  ({run['markers']} markers)")
        if k + 1 < len(runs):
            nxt = runs[k + 1]
            print(f"      change {run['gap']:+d} → {nxt['gap']:+d} between v1 {run['last']} and {nxt['first']}")


def show(first: int, last: int) -> None:
    """For v1 hadith first..last: where each matn lies, the number above it, and the OCR text
    between one matn and the next (shortened), to find a merge, split or missing hadith."""
    rows = {r["old_id"]: r for r in json.loads(OUT.read_text(encoding="utf-8"))}
    ws, where = book_words()
    for i in range(first, last + 1):
        r = rows[i]
        span = r["span"] or [0, 0]
        a, b = where[span[0]], where[max(span[0], span[1] - 1)]
        print(f"v1 {i}: {a[0]}:{a[1]}–{b[0]}:{b[1]}  found {r['found']}  marker {r['marker']}  gap {r['gap']:+d}"
              f"  {' '.join(ws[span[0]:span[0] + 6])} … {' '.join(ws[max(span[0], span[1] - 4):span[1]])}")
        for br in r["breaks"]:
            print(f"     inside: {br['words']} words unmatched at {br['at']}, {br['separators']}")
        if i < last and rows[i + 1]["span"] and r["span"]:
            between = ws[span[1]:rows[i + 1]["span"][0]]
            text = " ".join(between) if len(between) <= 30 else " ".join(between[:12]) + " … " + " ".join(between[-12:])
            print(f"     then {len(between)} words: {text}")


def mapping() -> dict[int, list[int]]:
    """The book's numbers for each v1 hadith, from content/numbering.json: one number per v1
    hadith in order, except where the file lists a number v1 lacks, a v1 hadith holding
    several printed ones, or one the book doesn't number."""
    ex = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    missing = {}
    for m in ex["missing"]:
        missing.setdefault(m["before_v1"], []).append(m["number"])
    merged = {m["v1"]: m["numbers"] for m in ex["merged"]}
    unnumbered = {u["v1"] for u in ex["unnumbered"]}
    out, n = {}, 1
    for i in sorted(v1_hadiths()):
        for number in sorted(missing.get(i, [])):
            if number != n:
                raise SystemExit(f"content/numbering.json: missing number {number} comes where the count is {n}")
            n += 1
        if i in unnumbered:
            out[i] = []
            continue
        k = merged.get(i, 1)
        out[i] = list(range(n, n + k))
        n += k
    return out


def check() -> None:
    """Compare the mapping with the numbers the OCR kept above each hadith."""
    rows = json.loads(OUT.read_text(encoding="utf-8"))
    numbers = mapping()
    last = max(n for ns in numbers.values() for n in ns)
    marked = [r for r in rows if r["marker"] is not None]
    wrong = [r for r in marked if not numbers[r["old_id"]] or numbers[r["old_id"]][0] != r["marker"]]
    print(f"the mapping ends at {last}; {len(marked) - len(wrong)} of {len(marked)} OCR markers agree")
    for r in wrong:
        got = numbers[r["old_id"]]
        print(f"  v1 {r['old_id']}: mapped to {got[0] if got else '—'}, the OCR has {r['marker']}"
              f" (page {r['page']}, line {r['line']})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", type=int, nargs=2, metavar=("FIRST", "LAST"))
    parser.add_argument("--check", action="store_true", help="compare content/numbering.json with the OCR's numbers")
    args = parser.parse_args()
    if args.check:
        check()
    elif args.show:
        show(*args.show)
    else:
        report(run())


if __name__ == "__main__":
    main()
