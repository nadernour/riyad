"""The v1 audit: compare a sample of v1 hadith with the printed book.

Usage: python tools/audit.py sample            the audit's 30 v1 ids
       python tools/audit.py show ID           v1's text next to the OCR of its pages, and their differences
       python tools/audit.py record ID         start content/audit/NNNN.json from v1's text
       python tools/audit.py summary           totals of the audit records

The sample is one random hadith from each 1/30 of v1's 1,893, with a fixed seed, so it is
the same on every run and covers the whole book. `show` aligns v1's words (matn, then
commentary) with the OCR text of the pages where the hadith is printed, and lists every
word where they differ in letters or tashkeel. Each difference is then settled on the scan.
v1 is wrong only where the scan says so: the OCR text has mistakes of its own.

`record` writes v1's version as the start of the hadith's audit record, which is then
corrected to what the book prints, with each difference listed (see docs/audit.md).
"""

import argparse
import difflib
import json
import random
import re

from arabic import normalize_word
from locate import load
from sources import ROOT, ocr_pages, plain, v1_hadiths, v1_sections

AUDIT_DIR = ROOT / "content" / "audit"
SIZE = 30
SEED = 2026
MARKS = re.compile(r"[ً-ٰٕ]")
SALUTATION = re.compile(r"-?\s*صَ?ل[َّ]*ى\s+ال?ل[َّ]*هُ?\s+عَ?لَ?يْ?هِ?\s+و[َ]?سَ?ل[َّ]*َ?مَ?\s*-?|ﷺ")


def sample() -> list[int]:
    ids = sorted(v1_hadiths())
    rng = random.Random(SEED)
    size = len(ids) / SIZE
    return [ids[rng.randrange(int(k * size), int((k + 1) * size))] for k in range(SIZE)]


def tokens(text: str) -> list[tuple[str, str]]:
    """(word as written, its letters normalized) for each word of a text; the salutation
    formula is dropped, since the book prints it as one glyph that the OCR misreads."""
    text = SALUTATION.sub(" ", text)
    out = []
    for w in text.split():
        n = normalize_word(w)
        if n:
            out.append((w, n))
    return out


def marks(word: str) -> list[str]:
    """The marks on each letter of a word, each letter's marks sorted, so that the order
    of shadda and vowel doesn't count as a difference."""
    out = []
    for ch in re.sub(r"[^ء-يً-ٰٕ]", "", word):
        if MARKS.fullmatch(ch):
            if out:
                out[-1] += ch
        else:
            out.append("")
    return ["".join(sorted(m)) for m in out]


def tashkeel_conflict(a: str, b: str) -> bool:
    """True when the same letters carry different marks in both words (a letter marked in
    one and bare in the other isn't a conflict: editions mark different letters)."""
    ma, mb = marks(a), marks(b)
    return len(ma) == len(mb) and any(x and y and x != y for x, y in zip(ma, mb))


def show(i: int) -> None:
    h = v1_hadiths()[i]
    loc = load()[i]
    pages = ocr_pages()
    print(f"v1 {i}: {h['book']} › {h['door']} › {h['title']}")
    print(f"pages {loc['start']}–{loc['end']} (confidence {loc['start_confidence']} / {loc['end_confidence']})\n")
    matn, sharh = plain(h["matn"]), plain(h["sharh"])
    print("V1 MATN:\n" + matn + "\n\nV1 COMMENTARY:\n" + sharh + "\n")

    v1 = tokens(matn) + tokens(sharh)
    ocr_text = "\n".join(pages[n - 1] for n in range(loc["start"], loc["end"] + 2))
    ocr = tokens(ocr_text)
    sm = difflib.SequenceMatcher(None, [n for _, n in ocr], [n for _, n in v1], autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size]
    lo, hi = blocks[0].a, blocks[-1].a + blocks[-1].size  # the OCR span the hadith covers
    sm = difflib.SequenceMatcher(None, [n for _, n in ocr[lo:hi]], [n for _, n in v1], autojunk=False)

    def ctx(seq, a, b):
        return " ".join(w for w, _ in seq[max(0, a - 3):a]) + " ⟦" + " ".join(w for w, _ in seq[a:b]) + "⟧ " \
            + " ".join(w for w, _ in seq[b:b + 3])

    span = ocr[lo:hi]
    print(f"DIFFERENCES (v1 against OCR; {len(v1)} v1 words, {len(span)} OCR words):")
    agree = conflicts = 0
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal":
            for k in range(a2 - a1):
                if tashkeel_conflict(span[a1 + k][0], v1[b1 + k][0]):
                    conflicts += 1
                    print(f"  tashkeel  v1 {v1[b1 + k][0]}  |  ocr {span[a1 + k][0]}   — {ctx(v1, b1 + k, b1 + k + 1)}")
                else:
                    agree += 1
            continue
        print(f"  {op:8}  v1 {ctx(v1, b1, b2)}\n            ocr {ctx(span, a1, a2)}")
    print(f"\n{agree} words agree, {conflicts} tashkeel conflicts")


def record(i: int) -> None:
    """Start the audit record of a hadith from v1's text, to be corrected against the scan."""
    path = AUDIT_DIR / f"{i:04d}.json"
    if path.exists():
        raise SystemExit(f"{path.relative_to(ROOT)} exists; edit it instead")
    h, loc = v1_hadiths()[i], load()[i]
    sections = v1_sections(h["sharh"])
    rec = {
        "v1_id": i,
        "pages": [loc["start"], loc["end"]],
        "printed": [{  # one item per hadith the book prints for this v1 entry
            "number": None,
            "matn": plain(h["matn"]).strip(),
            "meanings": sections["meanings"],
            "benefits": sections["benefits"],
        }],
        "differences": [],
        "notes": [f"v1 text outside the two sections: {t}" for t in sections["other"]],
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))


def summary() -> None:
    """Totals of the audit records: differences by part, kind and who is wrong."""
    from collections import Counter
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(AUDIT_DIR.glob("*.json"))]
    by = Counter((d["part"], d["kind"], d["who"]) for r in recs for d in r["differences"])
    print(f"{len(recs)} v1 entries audited, {sum(len(r['printed']) for r in recs)} printed hadith\n")
    print(f"{'part':10} {'kind':16} {'v1':>4} {'book':>5} {'variant':>8}")
    for part, kind in sorted({(p, k) for p, k, _ in by}):
        print(f"{part:10} {kind:16} {by[part, kind, 'v1']:>4} {by[part, kind, 'book']:>5} {by[part, kind, 'variant']:>8}")

    def hit(r, parts, who="v1"):
        return any(d["part"] in parts and d["who"] == who for d in r["differences"])
    commentary = ("meanings", "benefits", "structure")
    print()
    print("entries with v1 errors in the matn:      ", sum(hit(r, ("matn",)) for r in recs))
    print("entries with v1 changes to the commentary:", sum(hit(r, commentary) for r in recs))
    print("entries whose meaning v1 changes:         ",
          sum(any(d["kind"] == "meaning changed" for d in r["differences"]) for r in recs))
    print("entries numbered as the book:             ", sum(not hit(r, ("number",)) for r in recs))
    offsets = []
    for r in recs:
        first = r["printed"][0]["number"]
        offsets.append(f"{r['v1_id']}→{first}" + ("+" if len(r["printed"]) > 1 else ""))
    print("v1 → book numbers:", " ".join(offsets))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sample")
    sub.add_parser("summary")
    for name in ("show", "record"):
        s = sub.add_parser(name)
        s.add_argument("id", type=int)
    args = parser.parse_args()
    if args.cmd == "sample":
        print(" ".join(map(str, sample())))
    elif args.cmd == "summary":
        summary()
    elif args.cmd == "show":
        show(args.id)
    else:
        record(args.id)


if __name__ == "__main__":
    main()
