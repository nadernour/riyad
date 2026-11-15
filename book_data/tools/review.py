"""Content step 4: the second reading of every hadith's text against the scan (docs/matn.md, "The second reading").

Usage: python tools/review.py next [ID ...]   the next hadith to read again (--count, --words), each with crops of
                                              the scan, its text, the rounds' decisions and what the sources still
                                              have otherwise
       python tools/review.py zoom SPEC ...   closer looks: ID.CROP:TOP-BOTTOM[:LEFT-RIGHT], e.g. 12.2:0.30-0.38:0.5-1
                                              (TOP and BOTTOM are shares of that crop, LEFT and RIGHT of the page)
       python tools/review.py apply           apply content/matn/review-inbox.json
       python tools/review.py status          how many hadith are read again, and the changes so far

The review rounds (tools/matn.py) corrected v1's text to the book's. This reading judges their decisions: every
hadith is read once more against the scan, as its text now stands. A change is added to the hadith's decision in
content/matn/NN.json (so `matn.py apply --all` makes the same text again), and is kept with its reason in
content/matn/review.json, which also says which hadith have been read.

content/matn/review-inbox.json has one entry per hadith read, keyed by its number:
  {}                                           the text is right as it stands
  "fix": [[from, to, why, reason], ...]        as in docs/matn.md, with the reason for the change
  "misprint": [[printed, correction, reason]]  a misprint of the book's to record
  "drop_misprint": [printed, ...]              a recorded misprint that isn't one
  "note": "..."                                set the hadith's note for the owner ("" removes it)
  "spot": true                                 a change to a hadith that isn't read in full yet: it stays to be read
"""

import argparse
import datetime
import difflib
import hashlib
import json
from collections import Counter

import pymupdf

import matn
from sources import CACHE, ROOT, pdf_path
from zoom import MAX_AUTO_DPI, SHOWN_PX, Ink

REVIEW = matn.CHECKED / "review.json"
INBOX = matn.CHECKED / "review-inbox.json"
OUT = CACHE / "review"
REGIONS = OUT / "regions.json"
CHECKS = OUT / "check.json"


def load(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path, data, indent=1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def decisions() -> dict[int, dict]:
    return {int(i): d for f in sorted(matn.CHECKED.glob("[0-9][0-9].json")) for i, d in load(f, {}).items()}


def sunnah_items(h: dict) -> list[str]:
    """Where sunnah.com's Riyad al-Salihin (another edition) has other words than the text, and the OCR text of the
    scan doesn't have the text's words there: the print may have sunnah.com's. matn.check doesn't list a short word
    the text lacks («فِي فِي امْرَأَتِكَ», h. 6), which is how these were missed."""
    toks = matn.tokens(h["text"])
    ns = [t["n"] for t in toks]
    texts, index = matn.sunnah_index()
    pairs = set(zip(ns, ns[1:]))
    votes = Counter(k for p in pairs for k in index.get(p, ()))
    found = matn.locate(h, toks)
    if not votes or not found["span"]:
        return []
    best, shared = min(votes.items(), key=lambda kv: (-kv[1], kv[0]))
    if shared < 0.3 * max(1, len(pairs)):
        return []
    sun = texts[best]
    lo, hi = found["span"]
    ocr = [n for _, n in matn.ocr_tokens()[lo:hi + matn.matn_after(h, hi)]]
    to_ocr = {b.a + j: b.b + j for b in difflib.SequenceMatcher(None, ns, ocr, autojunk=False).get_matching_blocks()
              for j in range(b.size)}
    sal = lambda k: toks[k].get("sal")
    out = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, ns, sun, autojunk=False).get_opcodes():
        theirs = sun[b1:b2]
        if op == "equal" or (a1 == a2 and (set(theirs) <= matn.SALUTATION or a1 in (0, len(ns)))):
            continue
        lk = next((k for k in range(a1 - 1, max(-1, a1 - 8), -1) if k in to_ocr), None)
        rk = next((k for k in range(a2, min(len(ns), a2 + 8)) if k in to_ocr), None)
        if lk is None or rk is None:
            continue  # the OCR text has little of this passage: read it with care anyway
        seg = ocr[to_ocr[lk] + 1:to_ocr[rk]]
        if any(sal(k) for k in range(lk + 1, rk)):
            seg = [w for w in seg if w not in matn.SALUTATION]
        mine = [ns[k] for k in range(lk + 1, rk) if not sal(k)]
        other = [ns[k] for k in range(lk + 1, a1) if not sal(k)] + theirs + [ns[k] for k in range(a2, rk) if not sal(k)]
        near = lambda x: difflib.SequenceMatcher(None, "".join(x), "".join(seg), autojunk=False).ratio() if x or seg else 1.0
        if seg == mine or near(mine) > near(other) + 0.05:
            continue  # the OCR text has the text's words, or nearly
        verdict = "the OCR text has sunnah.com's words" if seg == other else "the OCR text is nearer sunnah.com's" \
            if near(other) > near(mine) + 0.05 else "the OCR text is unclear"
        ctx = (" ".join(t["w"] for t in toks[max(0, a1 - 3):a1]) + " ⟦" + " ".join(t["w"] for t in toks[a1:a2]) + "⟧ "
               + " ".join(t["w"] for t in toks[a2:a2 + 3]))
        out.append(f"sunnah.com «{' '.join(theirs)}», OCR «{' '.join(seg)}» ({verdict})   [{ctx}]")
    return out


def doubts(h: dict) -> dict:
    """What the sources have otherwise than the hadith's text as it stands (matn.check's doubts and sunnah_items),
    kept in .cache/ with the text it was made for."""
    cache = load(CHECKS, {})
    key = hashlib.sha1(h["text"].encode()).hexdigest()
    row = cache.get(str(h["id"]))
    if not row or row["key"] != key or "sunnah" not in row:
        items = row["items"] if row and row["key"] == key else [d for d in matn.check(h)["items"] if d["doubt"]]
        row = {"key": key, "items": items, "sunnah": sunnah_items(h)}
        cache[str(h["id"])] = row
        save(CHECKS, cache, None)
    return row


def render(doc, h: dict) -> list[str]:
    regions = load(REGIONS, {})
    region = matn.crop_region(doc, h)
    regions[str(h["id"])] = region
    save(REGIONS, regions, None)
    out = []
    for old in OUT.glob(f"h{h['id']:04d}-*.png"):
        old.unlink()
    for k, (n, y0, y1) in enumerate(region, 1):
        page = doc[n - 1]
        r = page.rect
        clip = pymupdf.Rect(r.x0, r.y0 + r.height * y0, r.x1, r.y0 + r.height * y1)
        path = OUT / f"h{h['id']:04d}-{k}-p{n:04d}.png"
        page.get_pixmap(dpi=matn.CROP_DPI, clip=clip, colorspace=pymupdf.csGRAY).save(path)
        out.append(f"{path.relative_to(ROOT)} (p. {n}, {y0:.2f}–{y1:.2f})")
    return out


def show(ids: list[int], count: int, words: int) -> None:
    texts = {h["id"]: h for h in matn.hadiths()}
    read = load(REVIEW, {})
    if not ids:
        total = 0
        for i in texts:
            if "read" in read.get(str(i), {}):
                continue
            n = len(texts[i]["text"].split())
            if len(ids) == count or (ids and total + n > words):
                break
            ids.append(i)
            total += n
        print(f"{sum('read' in r for r in read.values())} of {len(texts)} hadith read again." + ("" if ids else " All are read: nothing to do."))
    decided = decisions()
    doc = pymupdf.open(pdf_path())
    for i in ids:
        h, d = texts[i], decided.get(i, {})
        print(f"\n## {i}: {' '.join(render(doc, h))}")
        print(h["text"])
        fixes = d.get("fix", [])
        shown = [f"«{a}» → «{b}» ({why})" for a, b, why in fixes if why != "marks"]
        if fixes:
            print(f"rounds: {sum(f[2] == 'marks' for f in fixes)} marks fixes" + ("; " + " · ".join(shown) if shown else ""))
        for m in d.get("misprint", []):
            print(f"misprint recorded: printed «{m[0]}», corrected «{m[1]}»: {m[2]}")
        if d.get("note"):
            print(f"note: {d['note']}")
        runs = matn.bare(h["text"])
        if runs:
            print("no marks (write the book's, rule 2): " + " · ".join(f"«{r}»" for r in runs))
        toks = matn.tokens(h["text"])
        found = doubts(h)
        for line in found["sunnah"]:
            print(f"* {line}")
        for n, item in enumerate(found["items"], 1):
            k = item["k"]
            before = " ".join(t["w"] for t in toks[max(0, k - 2):k] if not t.get("sal"))
            after = " ".join(t["w"] for t in toks[k + item["n"]:k + item["n"] + 2] if not t.get("sal"))
            print(f"{n}. {item['kind']}: {matn.describe(item).replace('v1 «', 'text «').replace('v1 —', 'text —')}"
                  f"   [{before} ⟦⟧ {after}]")


def zoom(specs: list[str]) -> None:
    regions = load(REGIONS, {})
    doc = pymupdf.open(pdf_path())
    inks = {}
    for spec in specs:
        parts = spec.split(":")
        i, k = parts[0].split(".")
        t, b = map(float, parts[1].split("-"))
        left, right = map(float, parts[2].split("-")) if len(parts) > 2 else (0.0, 1.0)
        n, y0, y1 = regions[i][int(k) - 1]
        page = doc[n - 1]
        ink = inks.setdefault(n, Ink(page))
        top, bottom = ink.snap(y0 + t * (y1 - y0), -1), ink.snap(y0 + b * (y1 - y0), 1)
        r = page.rect
        clip = pymupdf.Rect(r.x0 + r.width * left, r.y0 + r.height * top, r.x0 + r.width * right, r.y0 + r.height * bottom)
        dpi = min(int(SHOWN_PX * 72 / max(clip.width, clip.height)), MAX_AUTO_DPI)
        path = OUT / f"z{int(i):04d}-{k}-{t:.2f}-{b:.2f}-{left:.2f}-{right:.2f}.png"
        pix = page.get_pixmap(dpi=dpi, clip=clip, colorspace=pymupdf.csGRAY)
        pix.save(path)
        print(f"{path.relative_to(ROOT)}  (h. {i}, p. {n}, {top:.3f}–{bottom:.3f} × {left:.2f}–{right:.2f}, {dpi} dpi)")


def amend(h: dict, d: dict, r: dict) -> None:
    """Apply one hadith's review entry r to its record h and its decision d (both changed in place)."""
    unknown = set(r) - {"fix", "misprint", "drop_misprint", "note", "spot"}
    if unknown:
        raise ValueError(f"unknown keys {sorted(unknown)}")
    for f in r.get("fix", []):
        if len(f) != 4 or f[2] not in matn.WHY or not f[3]:
            raise ValueError(f"a fix is [from, to, why, reason]: {f}")
        matn.fix_matn(h["matn"], f[0], f[1])
        d.setdefault("fix", []).append(f[:3])
    matn.tidy(h["matn"])
    for printed in r.get("drop_misprint", []):
        kept = [m for m in d.get("misprint", []) if m[0] != printed]
        if len(kept) == len(d.get("misprint", [])):
            raise ValueError(f"no misprint «{printed}» is recorded")
        d["misprint"] = kept
        if not kept:
            del d["misprint"]
        h["corrections"] = [c for c in h["corrections"] if not (c.get("part") == "matn" and c["printed"] == printed)]
    for m in r.get("misprint", []):
        if len(m) != 3:
            raise ValueError(f"a misprint is [printed, correction, reason]: {m}")
        d.setdefault("misprint", []).append(m)
        h["corrections"].append({"part": "matn", "printed": m[0], "correction": m[1], "reason": m[2]})
    if "note" in r:
        if d.get("note") in h["notes"]:
            h["notes"].remove(d["note"])
        d.pop("note", None)
        if r["note"]:
            d["note"] = r["note"]
            h["notes"].append(r["note"])


def apply() -> None:
    inbox = load(INBOX, {})
    books = {f.stem: load(f, {}) for f in sorted(matn.CONTENT.glob("*.json"))}
    where = {h["id"]: (stem, h) for stem, b in books.items() for c in b["chapters"] for h in c["hadith"]}
    kept = {stem: load(matn.CHECKED / f"{stem}.json", {}) for stem in books}
    review = load(REVIEW, {})
    failed = {}
    today = datetime.date.today().isoformat()
    for key, r in inbox.items():
        try:
            if not key.isdigit() or int(key) not in where:
                raise ValueError("no hadith has this number")
            stem, h = where[int(key)]
            h2, d2 = json.loads(json.dumps(h)), json.loads(json.dumps(kept[stem][key]))
            amend(h2, d2, r)
        except ValueError as e:
            print(f"{key}: {e}; nothing applied for this hadith")
            failed[key] = r
            continue
        h.clear()
        h.update(h2)
        kept[stem][key] = d2
        log = review.setdefault(key, {})
        if not r.get("spot"):
            log["read"] = today
        for field in ("fix", "misprint", "drop_misprint"):
            if r.get(field):
                log.setdefault(field, []).extend(r[field])
        if "note" in r:
            log["note"] = r["note"]
    for stem, b in books.items():
        save(matn.CONTENT / f"{stem}.json", b)
        save(matn.CHECKED / f"{stem}.json", kept[stem])
    save(REVIEW, dict(sorted(review.items(), key=lambda kv: int(kv[0]))))
    if failed:
        save(INBOX, failed)
    elif INBOX.exists():
        INBOX.unlink()
    print(f"{len(inbox) - len(failed)} applied, {len(failed)} failed" + (" (left in the inbox)" if failed else "")
          + f"; read again: {sum('read' in r for r in review.values())} of {len(where)}")


def status() -> None:
    review = load(REVIEW, {})
    changed = {k: r for k, r in review.items() if set(r) - {"read"}}
    fixes = [f for r in review.values() for f in r.get("fix", [])]
    print(f"read again: {sum('read' in r for r in review.values())} of {len(matn.hadiths())}; changed: {len(changed)} hadith, {len(fixes)} fixes"
          f" ({', '.join(f'{sum(f[2] == w for f in fixes)} {w}' for w in sorted(matn.WHY))}),"
          f" {sum(len(r.get('misprint', [])) for r in review.values())} misprints added,"
          f" {sum(len(r.get('drop_misprint', [])) for r in review.values())} dropped")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("next")
    n.add_argument("ids", type=int, nargs="*")
    n.add_argument("--count", type=int, default=12)
    n.add_argument("--words", type=int, default=900)
    z = sub.add_parser("zoom")
    z.add_argument("specs", nargs="+")
    sub.add_parser("apply")
    sub.add_parser("status")
    args = parser.parse_args()
    if args.cmd == "next":
        show(args.ids, args.count, args.words)
    elif args.cmd == "zoom":
        zoom(args.specs)
    elif args.cmd == "apply":
        apply()
    else:
        status()


if __name__ == "__main__":
    main()
