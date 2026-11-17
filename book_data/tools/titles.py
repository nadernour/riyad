"""Content step 4, the titles pass: the book and chapter titles against the headings on the scan.

Usage: python tools/titles.py compare          every chapter's title against its heading in the OCR text
       python tools/titles.py next [N ...]     the next chapters to read (or these), their headings in one image
       python tools/titles.py books            the book (كتاب) titles, with the pages they start on

v1's chapter titles have typos («الوضو ء») and v1 shortens many of them, the early ones most:
the book prints «باب الإخلاص وإحضار النية في جميع الأعمال والأقوال البارزة والخفية», v1 has
«الإخلاص و إحضار النية». The headings are set in a large display face with hardly any marks, so
only their words are checked, not their marks (docs/matn.md, "Book and chapter titles").

A chapter's heading is found in the OCR text (aljam3) by its number («١٥ - باب …») on the page
of its first hadith or the few before it; where the number was misread, by the «باب» line that
shares most words with v1's title. The heading runs on over the next lines until the chapter's
text starts. Where the OCR heading has v1's words, two independent readings agree, so the title
is accepted (`same`); every other one is read on the scan. Tesseract's words give the heading's
place on the page, so it can be cropped.

The decisions are in content/titles.json, which tools/convert_v1.py applies when it writes
content/hadith/: each chapter's title as printed, and each book's.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from arabic import TASHKEEL, words
from chapters import DIGITS
from matn import tesseract_page
from numbering import page_lines
from sources import CACHE

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "hadith"
TITLES = ROOT / "content" / "titles.json"
OUT = CACHE / "titles.json"
NUMBERED = re.compile(r"^[-–ـ۔]?\s*([0-9٠-٩۰-۹ه]{1,3})\s*[-–ـ۔]\s*(باب\b.*)")
BAB = re.compile(r"^[-–ـ۔]?\s*([0-9٠-٩۰-۹ه]{1,3})?\s*[-–ـ۔]?\s*(باب\b.*)")
BEFORE = 8           # how many pages before its first hadith a chapter's heading is looked for
SHARE = 0.5          # share of v1's title words a heading found by its words must have
DPI = 160            # the headings' display face reads well at this resolution
# a line that starts the chapter's text, after its heading: a verse, Nawawi's words, a hadith
BODY_START = re.compile(r"^(قال|وقال|وعن|عن|وَعَنْ|عَنْ|قَالَ|وَقَالَ|«|\(|[0-9٠-٩۰-۹]+\s*$|PAGE_SEPARATOR)")


def chapters() -> list[dict]:
    out = []
    for f in sorted(CONTENT.glob("*.json")):
        b = json.loads(f.read_text(encoding="utf-8"))
        for c in b["chapters"]:
            out.append({"book": int(f.stem), "number": c["number"], "title": c["title"],
                        "page": c["hadith"][0]["page"], "first": c["hadith"][0]["id"]})
    return out


def heading_lines(page: int, i: int) -> list[str]:
    lines = page_lines(page)
    m = BAB.match(lines[i])
    out = [m.group(2)]
    for line in lines[i + 1:i + 4]:
        if not line or BODY_START.match(line) or len(words(line)) > 22:
            break
        out.append(line)
    return out


def find_heading(c: dict) -> dict | None:
    pages = range(c["page"], max(c["page"] - BEFORE, 1) - 1, -1)
    for p in pages:
        for i, line in enumerate(page_lines(p)):
            m = NUMBERED.match(line)
            if m and int(m.group(1).translate(DIGITS)) == c["number"]:
                return {"page": p, "line": i, "how": "number"}
    want = set(words(c["title"])) - {"باب"}
    best = None
    for p in pages:
        for i, line in enumerate(page_lines(p)):
            if not BAB.match(line) or len(line) > 160:
                continue
            got = set(words(" ".join(heading_lines(p, i))))
            share = len(want & got) / max(len(want), 1)
            if share >= SHARE and (best is None or share > best[0]):
                best = (share, {"page": p, "line": i, "how": "words"})
    return best[1] if best else None


def place(page: int, text: str) -> tuple[float, float, int] | None:
    """The heading's top and bottom on the page, from Tesseract's words, and how many of its words
    Tesseract has: the line that shares most words with the heading, and the lines above and below
    it that share words with it too, or open with «باب» (Tesseract often runs the first line of the
    display face together: «باباسحباب» for «باب استحباب»)."""
    ws = tesseract_page(page)
    if not ws:
        return None
    want = set(words(text)) - {"باب"}
    lines: dict[tuple, list[dict]] = {}
    for w in ws:
        lines.setdefault(w["line"], []).append(w)
    rows = sorted(lines.values(), key=lambda l: min(w["box"][1] for w in l))

    def score(row):
        return len({w["n"] for w in row} & want)

    def opens(row):
        return any(w["n"].startswith("باب") for w in row)

    k = max(range(len(rows)), key=lambda k: (score(rows[k]), opens(rows[k])))
    if score(rows[k]) == 0 and not opens(rows[k]):
        return None
    a = b = k
    while a > 0 and k - a < 3 and (score(rows[a - 1]) or (opens(rows[a - 1]) and not opens(rows[a]))):
        a -= 1
        if opens(rows[a]):
            break
    while b + 1 < len(rows) and b - a < 3 and score(rows[b + 1]) >= max(1, len(rows[b + 1]) // 3) \
            and not opens(rows[b + 1]):
        b += 1
    top = min(w["box"][1] for row in rows[a:b + 1] for w in row)
    bottom = max(w["box"][3] for row in rows[a:b + 1] for w in row)
    return top, bottom, sum(score(r) for r in rows[a:b + 1])


def search(c: dict) -> tuple[int, tuple] | None:
    """A heading the OCR text doesn't give: the page near the chapter's first hadith where
    Tesseract's lines share most words with v1's title."""
    best = None
    for p in range(c["page"], max(c["page"] - 3, 1) - 1, -1):
        got = place(p, c["title"])
        if got and got[2] and (best is None or got[2] > best[1][2]):
            best = (p, got)
    return best


def compare() -> list[dict]:
    rows = []
    for c in chapters():
        h = find_heading(c)
        row = {**c, "heading": None, "status": "not found"}
        if h:
            text = " ".join(heading_lines(h["page"], h["line"]))
            row.update(heading=text, heading_page=h["page"], how=h["how"])
            v1, ocr = words(c["title"]), words(text)
            if v1 and v1[0] != "باب":
                v1 = ["باب"] + v1
            row["status"] = "same" if v1 == ocr else "differs"
            row["missing"] = [w for w in ocr if w not in v1]   # in the OCR heading, not in v1's title
            row["extra"] = [w for w in v1 if w not in ocr]     # in v1's title, not in the OCR heading
            row["place"] = place(h["page"], text)
        else:
            found = search(c)
            if found and found[1][2] >= 2:
                row.update(heading_page=found[0], place=found[1], how="tesseract")
            else:  # the nearest page with a centered line: the first hadith's, the one before, after
                for q in (c["page"], c["page"] - 1, c["page"] + 1, c["page"] - 2):
                    if centered(q):
                        row.update(heading_page=q, how="centered")
                        break
        rows.append(row)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
    return rows


def centered(page_number: int) -> list[float]:
    """The tops of the page's centered short lines, as shares of the page: a heading's first line
    is set centered with wide margins, in the display face (p. 32's «٢ - باب التوبة» spans 0.40-0.60
    of the width). A page number is too narrow to count."""
    import pymupdf
    pix = doc()[page_number - 1].get_pixmap(dpi=60, colorspace=pymupdf.csGRAY)
    width, height, stride, data = pix.width, pix.height, pix.stride, pix.samples
    rows = []
    for y in range(height):
        line = data[y * stride:y * stride + width]
        xs = [x for x in range(width) if line[x] < 128]
        rows.append((xs[0] / width, xs[-1] / width) if xs else None)
    out, start = [], None
    for y, r in enumerate(rows + [None]):
        if r and start is None:
            start = y
        elif not r and start is not None:
            seg = [x for x in rows[start:y] if x]
            left, right = min(x[0] for x in seg), max(x[1] for x in seg)
            if (y - start) / height > 0.015 and 0.08 < right - left < 0.6 and left > 0.2 and right < 0.8 \
                    and abs((left + right) / 2 - 0.5) < 0.1:
                out.append(start / height)
            start = None
    return out


def clip(row: dict, others: list[dict]):
    """The heading's place on its page, full width: from the centered lines on the page (the
    k-th of them for the k-th chapter whose heading is on this page), or from Tesseract's place for
    it where it matches several words, with room below for the lines it runs on to; otherwise the
    top third of the page. The edges are moved out to the gaps between lines."""
    import pymupdf
    from zoom import Ink
    page = doc()[row["heading_page"] - 1]
    tops = centered(row["heading_page"])
    here = [o["number"] for o in others if o.get("heading_page") == row["heading_page"]]
    strong = row.get("place") and row["place"][2] >= 2
    if tops:
        if strong and len(tops) > len(here):
            top = min(tops, key=lambda t: abs(t - row["place"][0]))
        else:
            k = sorted(here).index(row["number"]) if row["number"] in here else 0
            top = tops[min(k, len(tops) - 1)]
        bottom = top + 0.17
    elif strong:
        top, bottom = row["place"][:2]
        bottom = max(bottom, top + 0.06)
    else:
        top, bottom = 0.0, 0.35
    ink = Ink(page)
    top, bottom = ink.snap(max(top - 0.05, 0), -1), ink.snap(min(bottom + 0.0, 1), 1)
    r = page.rect
    return page, pymupdf.Rect(r.x0, r.y0 + r.height * top, r.x1, r.y0 + r.height * bottom)


_doc = None


def doc():
    global _doc
    if _doc is None:
        import pymupdf
        from sources import pdf_path
        _doc = pymupdf.open(pdf_path())
    return _doc


def sheet(rows: list[dict], name: str) -> str:
    """The headings of these chapters stacked in one image, each with its chapter number in the
    margin, at DPI: the display face is large, so it reads well at a low resolution, and one image
    for several headings keeps a round short."""
    import pymupdf
    every = json.loads(OUT.read_text(encoding="utf-8"))
    parts = [(r["number"], *clip(r, every)) for r in rows if r.get("heading_page")]
    width = max(c.width for _, _, c in parts) + 40
    height = sum(c.height + 6 for _, _, c in parts)
    out_doc = pymupdf.open()
    page = out_doc.new_page(width=width, height=height)
    y = 0
    for number, src, c in parts:
        page.show_pdf_page(pymupdf.Rect(40, y, 40 + c.width, y + c.height), doc(), src.number, clip=c)
        page.insert_text((4, y + 18), str(number), fontsize=13, color=(0.8, 0, 0))
        y += c.height + 6
        page.draw_line((0, y - 3), (width, y - 3), color=(0.8, 0, 0), width=0.6)
    out = CACHE / "pages" / f"titles-{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page.get_pixmap(dpi=DPI).save(out)
    return str(out.relative_to(ROOT))


def record(read: dict) -> None:
    """Keep the titles read on the scan, without marks: the headings have hardly any, in a display
    face whose marks are hard to read. {"12": "باب …"} sets chapter 12's, {"book 2": "كتاب …"} a
    book's, {"note 12": "…"} a note on chapter 12 for the owner, {"misprint 12": [printed, correction,
    reason]} (or "misprint book 3") a misprint in a heading: the title has the correction."""
    kept = json.loads(TITLES.read_text(encoding="utf-8")) if TITLES.exists() else {}
    for key in ("books", "chapters", "notes", "misprints"):
        kept.setdefault(key, {})
    for k, v in read.items():
        if k.startswith("book "):
            kept["books"][k[5:]] = v
        elif k.startswith("note "):
            kept["notes"][k[5:]] = v
        elif k.startswith("misprint "):  # "misprint 12" or "misprint book 3": [printed, correction, reason]
            if len(v) != 3:
                raise ValueError(f"a misprint is [printed, correction, reason]: {v}")
            kept["misprints"][k[9:]] = v
        else:
            int(k)
            kept["chapters"][k] = " ".join(TASHKEEL.sub("", v).split())
    for key in ("books", "chapters", "notes", "misprints"):
        kept[key] = dict(sorted(kept[key].items(), key=lambda kv: (kv[0].startswith("book"), int(kv[0].split()[-1]))))
    TITLES.write_text(json.dumps(kept, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"chapters read: {len(kept['chapters'])}, books: {len(kept['books'])}, notes: {len(kept['notes'])},"
          f" misprints: {len(kept['misprints'])}")


def apply(books: dict[int, dict]) -> None:
    """Give the books and chapters built by tools/convert_v1.py (keyed by v1's book id) the titles
    read on the scan, with the misprints and notes kept beside them. A book the print gives no
    heading has the title None (see build_db.py for how the app gets it)."""
    if not TITLES.exists():
        return
    kept = json.loads(TITLES.read_text(encoding="utf-8"))
    for book_id, book in books.items():
        key = str(book_id)
        if key in kept["books"]:
            book["title"] = kept["books"][key]
        if f"book {key}" in kept["misprints"]:
            printed, correction, reason = kept["misprints"][f"book {key}"]
            book["corrections"] = [{"part": "title", "printed": printed, "correction": correction, "reason": reason}]
        for c in book["chapters"]:
            n = str(c["number"])
            if n in kept["chapters"]:
                c["title"] = kept["chapters"][n]
            if n in kept["misprints"]:
                printed, correction, reason = kept["misprints"][n]
                c["corrections"] = [{"part": "title", "printed": printed, "correction": correction, "reason": reason}]
            if n in kept["notes"]:
                c["notes"] = c.get("notes", []) + [kept["notes"][n]]


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("compare")
    sub.add_parser("books")
    sub.add_parser("record", help="merge {number: title as printed} from stdin into content/titles.json")
    n = sub.add_parser("next")
    n.add_argument("numbers", type=int, nargs="*")
    n.add_argument("--count", type=int, default=8)
    args = parser.parse_args()
    if args.cmd == "compare":
        rows = compare()
        for s in ("same", "differs", "not found"):
            print(f"{s}: {sum(r['status'] == s for r in rows)}")
        return
    if args.cmd == "record":
        record(json.load(sys.stdin))
        return
    rows = {r["number"]: r for r in json.loads(OUT.read_text(encoding="utf-8"))}
    if args.cmd == "books":
        for f in sorted(CONTENT.glob("*.json")):
            b = json.loads(f.read_text(encoding="utf-8"))
            print(f.stem, b["chapters"][0]["number"], b["chapters"][0]["hadith"][0]["page"], b["title"])
        return
    done = json.loads(TITLES.read_text(encoding="utf-8")).get("chapters", {}) if TITLES.exists() else {}
    ids = args.numbers or [k for k in rows if str(k) not in done][:args.count]
    if not ids:
        print(f"all {len(rows)} chapters' headings are read (content/titles.json)")
        return
    for k in ids:
        r = rows[k]
        print(f"{k} p{r.get('heading_page')} v1: {r['title']}")
        if r["status"] != "same":
            print(f"    OCR: {r['heading']}")
    print(sheet([rows[k] for k in ids], f"{ids[0]:03d}-{ids[-1]:03d}"))


if __name__ == "__main__":
    sys.exit(main())
