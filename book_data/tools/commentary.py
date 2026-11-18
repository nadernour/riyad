"""Content step 5: transcribe the commentary, Nuzhat al-Muttaqin's word meanings and benefits (docs/transcription.md).

Usage: python tools/commentary.py next [ID ...]   the next hadith to transcribe, up to 6 and 4 pages (--count, --pages):
                                                  their drafts go to content/commentary/inbox.json, with crops of the scan
       python tools/commentary.py done            check the inbox's entries and file them in content/commentary/NN.json
       python tools/commentary.py check           check every transcribed hadith
       python tools/commentary.py crop ID ...     render the commentary of these hadith from the scan
       python tools/commentary.py draft ID ...    print the OCR text's draft of these hadith
       python tools/commentary.py score           the pilot: the audit's hadith against the book's text in content/audit/
       python tools/commentary.py left            how many hadith are left to transcribe, of all

The OCR text (aljam3) is the draft: it reads the commentary's font well (95% of the audit's words), and its usual
mistakes are dotted letters, words dropped or run together, the ﷺ glyph and lines out of order (docs/audit.md).
A hadith's commentary is what the OCR text has from the end of its matn (matn.locate, with matn.matn_after) to the
start of the next hadith's matn, or to the next chapter's heading. Its source note («الحديث رواه …») and footnotes
aren't kept. The draft is split at the headings: «لغة الحديث» opens the word meanings, each «term : meaning .», and
«أفاد الحديث» (or «أفادت الأحاديث …», «أفاد الحديثان», «وأفاد هنا») the benefits, one per bullet. Where the heading
says the benefits cover the hadith before too, the draft proposes them in shared_with. The round corrects the
draft against the crops (docs/transcription.md has the rules).
"""

import argparse
import difflib
import json
import os
import re
from functools import cache

import pymupdf

import matn
from arabic import TASHKEEL, expand_salutation, normalize_word
from numbering import book_words, page_lines
from sources import CACHE, ROOT, ocr_pages, pdf_path

KEPT = ROOT / "content" / "commentary"
INBOX = KEPT / "inbox.json"
AUDIT = ROOT / "content" / "audit"
CROPS = CACHE / "commentary-crops"
CROP_DPI = 300     # the commentary's small font, with its dots; a full-width crop is then about 1,860 px wide
SOURCE = 0.08     # how far above the end of the matn's crop the commentary's crop starts
CHUNK = 0.3        # the most of a page's height one crop shows, so the Read tool doesn't scale it down
FIELDS = ("id", "pages", "see", "meanings", "benefits", "shared_with", "corrections", "notes")
# Letters, the book's marks, Arabic-Indic digits, the punctuation it prints, ﷺ.
ALLOWED = re.compile(r"[ء-غف-يً-ْٰٱ٠-٩ﷺ «»()\[\]﴿﴾،؛؟:.\-/!…\"]")
PREFIXES = ("وبال", "فبال", "وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك")
NUMBERS = {"الحديثان": 1, "الثلاثه": 2, "الاربعه": 3, "الخمسه": 4, "السته": 5}


# ---------------------------------------------------------------- the OCR draft

@cache
def raw_tokens() -> tuple[list[tuple[str, str, int, int]], list[int]]:
    """Every OCR token of the book, punctuation too, as (token, normalized or "", page, line), and for each word of
    numbering.book_words() its index here. Lines with no letter (page and hadith numbers) are left out."""
    toks, index = [], []
    for n in range(1, len(ocr_pages()) + 1):
        for i, line in enumerate(page_lines(n)):
            parts = expand_salutation(line).split()
            if not any(normalize_word(p) for p in parts):
                continue
            for p in parts:
                norm = normalize_word(p)
                if norm:
                    index.append(len(toks))
                toks.append((p, norm, n, i))
    assert len(index) == len(book_words()[0])
    return toks, index


@cache
def records() -> dict[int, dict]:
    """Every hadith in content/hadith/ by id, with its chapter's title and its matn as one text."""
    out = {}
    for f in sorted(matn.CONTENT.glob("*.json")):
        for c in json.loads(f.read_text(encoding="utf-8"))["chapters"]:
            for h in c["hadith"]:
                out[h["id"]] = {**h, "book": f.stem, "chapter": c["number"], "chapter_title": c["title"],
                                "text": "".join(p["text"] for p in h["matn"])}
    return out


@cache
def ocr_span(i: int) -> tuple[int, int] | None:
    """Where hadith i's commentary is in the OCR text: (first, end) indexes of numbering.book_words()."""
    hs = {h["id"]: h for h in matn.hadiths()}
    h = hs[i]
    found = matn.locate(h, matn.tokens(h["text"]))["span"]
    if not found:
        return None
    start = found[1] + matn.matn_after(h, found[1])
    nxt = matn.neighbours()[i][1]
    end = None
    if nxt:
        after = matn.matn_span(nxt, matn.tokens(nxt["text"]), start)["span"]
        end = vocalized_from(after[0]) if after and after[0] > start else None
    toks, index = raw_tokens()
    if end is None:
        end = min(len(index), start + 600)
    if nxt is None or (nxt["book"], nxt["chapter"]) != (h["book"], h["chapter"]):
        end = chapter_heading(start, end) or end
    return start, end


def vocalized_from(k: int) -> int:
    """Where the next hadith's matn starts, from word k on: the first word with a mark that opens a run of marked
    words, three in four. Its words can be found earlier, in the commentary before it, when the two hadith share
    their subject (h. 160's benefits hold h. 161's words); the commentary is hardly ever marked, while the OCR text
    keeps some marks on most of the matn's words."""
    toks, index = raw_tokens()

    def marked(j: int) -> bool | None:
        m = matn.marks(toks[index[j]][0])
        return None if len(m) < 2 else any(m)

    def run_at(j: int) -> int:
        return sum([v for v in (marked(x) for x in range(j, min(j + 8, len(index)))) if v is not None][:4])

    if run_at(k) >= 2:
        return k
    for j in range(k, min(k + 400, len(index))):
        if marked(j) and run_at(j) >= 3:
            return j
    return k


def chapter_heading(start: int, end: int) -> int | None:
    """The word where a chapter heading («٢١٥ - باب …») opens a line between two words, if there is one."""
    toks, index = raw_tokens()
    for k in range(start, end):
        t = index[k]
        if toks[t][1] == "باب":
            before = [x for x in toks[:t][::-1][:3] if x[3] == toks[t][3] and x[2] == toks[t][2]]
            if all(not x[1] for x in before) and (not before or any(re.search(r"[٠-٩\d\-]", x[0]) for x in before)):
                if t == 0 or toks[t - 1][3] != toks[t][3] or before:
                    return k
    return None


def ocr_text(i: int) -> str:
    """Hadith i's commentary as the OCR text has it, with its tokens joined by single spaces."""
    span = ocr_span(i)
    if not span:
        return ""
    toks, index = raw_tokens()
    lo = index[span[0]]
    hi = index[span[1]] if span[1] < len(index) else len(toks)
    while hi > lo and not toks[hi - 1][1]:  # the next hadith's number, read as «/190»
        hi -= 1
    return " ".join(t for t, _, _, _ in toks[lo:hi])


HEADING_MEANINGS = re.compile(r"^ل[غفقع]ه$")
BULLETS = re.compile(r"\s*[•·∙●]\s*")
JUNK = re.compile(r"[A-Za-zͰ-Ͽ<>=*_|]+")


def tidy(text: str) -> str:
    text = JUNK.sub(" ", text)
    text = BULLETS.sub(" • ", text)
    text = re.sub(r"\s*([،؛:.؟])\s*", r" \1 ", text)   # the book's punctuation, with a space on each side
    text = re.sub(r"(?<=[.،:]) (?=[.،:] )", "", text)
    return " ".join(text.split()).strip(" .،:")


def tidy_item(text: str) -> str:
    return tidy(text.replace("•", " "))


def benefits_heading(norm: list[str], k: int) -> bool:
    """Word k opens the benefits' heading: «أفاد» or «أفادت» (read loosely: the OCR text has «افلات», «أفَادَ»),
    then «الحديث», «الحديثان», «الأحاديث», «هنا» or «سابقه»."""
    w = norm[k][1:] if norm[k].startswith("و") else norm[k]
    if not any(difflib.SequenceMatcher(None, w, x).ratio() >= 0.75 for x in ("افاد", "افادت")):
        return False
    nxt = norm[k + 1] if k + 1 < len(norm) else ""
    return nxt.startswith(("الح", "الاح", "التح")) or nxt in ("هنا", "سابقه")


def split_sections(text: str) -> dict:
    """The draft's source note, word meanings and benefits, cut at their headings."""
    words = tidy(text).split()
    norm = [normalize_word(w) for w in words]
    out = {"source": [], "meanings": [], "benefits": [], "benefits_heading": []}
    part = "source"
    k = 0
    while k < len(words):
        n = norm[k]
        nxt = norm[k + 1] if k + 1 < len(words) else ""
        if part == "source" and HEADING_MEANINGS.match(n) and nxt.startswith("الحد"):
            part, k = "meanings", k + 2
            while k < len(words) and words[k] in (":", "."):
                k += 1
            continue
        if part != "benefits" and benefits_heading(norm, k):
            # the heading runs to its colon: «أفاد الحديث :», «أفادت الأحاديث الثلاثة السابقة :», «وأفاد هنا :»
            end = next((j for j in range(k + 1, min(k + 7, len(words))) if words[j] in (":", ".", "•")), k + 1)
            out["benefits_heading"] = [w for w in words[k:end + 1] if w != "•"]
            part, k = "benefits", end + 1
            continue
        out[part].append(words[k])
        k += 1
    return out


def split_meanings(words: list[str]) -> list[dict]:
    """«term : meaning .» items: a sentence with a colon opens an item, one without is the meaning's next sentence."""
    items = []
    for sentence in re.split(r"(?<= \.) ", " ".join(words)):
        sentence = sentence.strip()
        if not sentence or sentence == ".":
            continue
        if ":" in sentence and (not items or len(sentence.split(":")[0].split()) <= 6):
            term, meaning = sentence.split(":", 1)
            items.append({"term": tidy_item(term), "meaning": tidy_item(meaning) + " ."})
        elif items:
            items[-1]["meaning"] = items[-1]["meaning"] + " " + tidy_item(sentence) + " ."
        else:
            items.append({"term": "", "meaning": tidy_item(sentence) + " ."})
    for m in items:
        m["meaning"] = m["meaning"].replace(" . .", " .")
    return items


def split_benefits(words: list[str]) -> list[str]:
    parts = " ".join(words).split("•")
    out = []
    for p in parts:
        p = tidy(p)
        if p:
            out.append(p + " .")
    return out


def see_note(source: list[str]) -> str | None:
    """A source note that sends the reader to the hadith's earlier place («تقدم شرح الحديث في باب … رقم …»)."""
    text = " ".join(source)
    m = re.search(r"(?:وقد\s+)?(?:تقدم|سبق|انظر|أنظر|مر)\s.*", text)
    return tidy(m.group()) + " ." if m else None


def proposed_shared(i: int, heading: list[str]) -> list[int]:
    """The hadith before i that a shared heading covers: «أفاد الحديثان» one, «… الثلاثة» two; «المتقدمة»,
    «السابقة» or «أفادت الأحاديث» with no number, each one before it in the chapter since the last that has
    benefits of its own."""
    norm = [normalize_word(w) for w in heading]
    if not norm or not ({"الاحاديث", "الحديثان", "قبله", "سابقه"} & set(norm) or norm[0].endswith("ت")):
        return []
    before = []
    h = records()[i]
    prev = matn.neighbours()[i][0]
    while prev and (prev["book"], prev["chapter"]) == (h["book"], h["chapter"]):
        before.append(prev["id"])
        prev = matn.neighbours()[prev["id"]][0]
    count = next((NUMBERS[n] for n in norm if n in NUMBERS), None)
    if "قبله" in norm:
        count = 1
    if count is None:  # every hadith since the last with benefits of its own
        count = 0
        for j in before:
            if split_sections(ocr_text(j))["benefits_heading"]:
                break
            count += 1
    return sorted(before[:count])


def draft(i: int) -> dict:
    h = records()[i]
    parts = split_sections(ocr_text(i))
    span = ocr_span(i)
    where = book_words()[1]
    pages = sorted({where[k][0] for k in range(*span)}) if span and span[1] > span[0] else [h["page"]]
    entry = {"id": i, "pages": [pages[0], pages[-1]] if len(pages) > 1 else [pages[0]],
             "see": see_note(parts["source"]),
             "meanings": split_meanings(parts["meanings"]),
             "benefits": split_benefits(parts["benefits"]),
             "shared_with": proposed_shared(i, parts["benefits_heading"]),
             "corrections": [], "notes": []}
    return {"entry": entry, "source": tidy(" ".join(parts["source"])),
            "heading": " ".join(parts["benefits_heading"])}


# ---------------------------------------------------------------- the scan

def region(doc, i: int) -> list[tuple[int, float, float]]:
    """Where hadith i's commentary is printed: (page, top, bottom) on each of its pages, from the end of its matn
    to the start of the next hadith's, or to the next chapter's heading."""
    from zoom import Ink
    h = records()[i]
    mine = matn.crop_region(doc, next(x for x in matn.hadiths() if x["id"] == i))
    nxt = matn.neighbours()[i][1]
    n0, y0 = mine[-1][0], mine[-1][2]
    if nxt:
        theirs = matn.crop_region(doc, nxt)
        n1, y1 = theirs[0][0], theirs[0][1]
        found = draft_end(doc, i, n0, max(n1, n0 + 1))
        if found and ((nxt["book"], nxt["chapter"]) != (h["book"], h["chapter"]) or found > (n1, y1)):
            # where a chapter ends, so the crop stops before its heading and verses; and where the next hadith's
            # crop starts above the draft's end, which happens when its words are found in this commentary
            n1, y1 = found
    else:
        n1, y1 = n0, 1.0
    if (n1, y1) <= (n0, y0):  # the matn crops overlap: the next hadith's own page is shown whole
        n1, y1 = n0, 1.0
    out = []
    for n in range(n0, n1 + 1):
        page = doc[n - 1]
        ink = Ink(page)
        lines = matn.page_lines_ink(ink)
        top = max(0.0, (lines[0][0] if lines else 0.0) - 0.005)
        if n == n0:  # a few lines higher: the matn's crop can take in the source note, where a cross-reference is
            top = max(top, matn.cut(matn.text_rows(ink), y0 - SOURCE - 0.03, y0 - SOURCE)) if y0 > SOURCE else top
        # the next hadith's crop can start inside the commentary's last line: down to the gap below it
        # (from a little below it: the next crop can start at the top of that line, h. 1714)
        bottom = matn.cut(matn.text_rows(ink), y1 + 0.01, y1 + 0.035) if n == n1 else matn.text_bottom(page, ink, top)
        bottom = min(bottom, matn.text_bottom(page, ink, top))  # never the footnotes
        if bottom - top > 0.01:
            out.append((n, top, bottom))
    return out


def draft_end(doc, i: int, first: int, last: int) -> tuple[int, float] | None:
    """Where the draft's last words are printed, from Tesseract's reading of the pages: the bottom of the last run
    of three words it shares with the draft, moved down to the gap below that line. Used where a chapter ends, so
    the crop stops before the next chapter's heading and verses."""
    from zoom import Ink
    span = ocr_span(i)
    if not span:
        return None
    want = book_words()[0][span[0]:span[1]]
    tess = [w for n in range(first, last + 1) for w in matn.tesseract_page(n)]
    sm = difflib.SequenceMatcher(None, want, [w["n"] for w in tess], autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= 3]
    if not blocks:
        return None
    # a run far past the one before it, in Tesseract's words more than in the draft's, is the same three words
    # printed later (the next hadith's commentary, h. 1534), not the draft's end
    kept = blocks[:1]
    for b in blocks[1:]:
        p = kept[-1]
        if b.b - (p.b + p.size) <= 2 * (b.a - (p.a + p.size)) + 10:
            kept.append(b)
    w = tess[kept[-1].b + kept[-1].size - 1]
    n = w["page"]
    rows = matn.text_rows(Ink(doc[n - 1]))
    return n, matn.cut(rows, w["box"][3], w["box"][3] + 0.03)


def chunks(doc, n: int, top: float, bottom: float) -> list[tuple[float, float]]:
    """A page's part cut into crops of at most CHUNK of the page, at the gaps between lines."""
    from zoom import Ink
    out = []
    rows = None
    while bottom - top > CHUNK + 0.03:
        rows = rows or matn.text_rows(Ink(doc[n - 1]))
        y = matn.cut(rows, top + CHUNK - 0.06, top + CHUNK)
        out.append((top, y))
        top = y
    out.append((top, bottom))
    return out


def crops(i: int) -> list[str]:
    doc = pymupdf.open(pdf_path())
    CROPS.mkdir(parents=True, exist_ok=True)
    for old in CROPS.glob(f"h{i:04d}-*.png"):
        old.unlink()
    paths = []
    k = 0
    for n, y0, y1 in region(doc, i):
        page = doc[n - 1]
        r = page.rect
        for a, b in chunks(doc, n, y0, y1):
            k += 1
            clip = pymupdf.Rect(r.x0, r.y0 + r.height * a, r.x1, r.y0 + r.height * b)
            path = CROPS / f"h{i:04d}-{k}-p{n:04d}.png"
            page.get_pixmap(dpi=CROP_DPI, clip=clip, colorspace=pymupdf.csGRAY).save(path)
            paths.append(f"{path.relative_to(ROOT)} (p. {n}, {a:.2f}–{b:.2f})")
    return paths


# ---------------------------------------------------------------- the transcription

def book_file(i: int) -> str:
    return records()[i]["book"]


def kept() -> dict[int, dict]:
    out = {}
    for f in sorted(KEPT.glob("[0-9][0-9].json")):
        out.update({int(k): v for k, v in json.loads(f.read_text(encoding="utf-8")).items()})
    return out


def inbox() -> dict[int, dict]:
    if not INBOX.exists():
        return {}
    return {int(k): v for k, v in json.loads(INBOX.read_text(encoding="utf-8")).items()}


def write(path, entries: dict[int, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({str(k): v for k, v in sorted(entries.items())}, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")


def todo(filed_only: bool = False) -> list[int]:
    """The hadith not transcribed yet, in the book's order; with PILOT=1 in the environment, the audit's only."""
    done = set(kept()) | (set() if filed_only else set(inbox()))
    pilot = pilot_ids() if os.environ.get("PILOT") else None
    return [h["id"] for h in matn.hadiths() if h["id"] not in done and (pilot is None or h["id"] in pilot)]


def core(word: str) -> str:
    w = normalize_word(word)
    for p in PREFIXES:
        if w.startswith(p) and len(w) - len(p) >= 2:
            return w[len(p):]
    return w


def found_in(phrase: str, text: str) -> bool:
    """The phrase's words are a run of the text's, each word compared without its prefixes (و ف ب ل ك ال)."""
    want = [core(w) for w in expand_salutation(phrase).split() if normalize_word(w)]
    have = [core(w) for w in expand_salutation(text).split() if normalize_word(w)]
    if not want:
        return False
    return any(have[k:k + len(want)] == want for k in range(len(have) - len(want) + 1))


def problems(e: dict, ids: set[int]) -> list[str]:
    """What is wrong with an entry: its format, its characters, terms not found in its hadith, shared_with."""
    out = []
    i = e.get("id")
    if set(e) - set(FIELDS) - {"in_text"} or any(f not in e for f in FIELDS):
        out.append(f"fields must be {', '.join(FIELDS)}")
    if i not in records():
        return out + ["no such hadith"]
    texts = [("see", e.get("see") or "")]
    for k, m in enumerate(e.get("meanings", [])):
        if not m.get("term") or not m.get("meaning"):
            out.append(f"meanings.{k}: a term and a meaning are both needed")
        texts += [(f"meanings.{k}.term", m.get("term", "")), (f"meanings.{k}.meaning", m.get("meaning", ""))]
        place = m.get("in_text") or m.get("term", "")
        if m.get("in_text") != "" and not found_in(place, records()[i]["text"]):
            out.append(f"meanings.{k}: «{place}» isn't in the hadith: give in_text, the hadith's words it explains "
                       f"(\"\" if none)")
        if set(m) - {"term", "meaning", "in_text"}:
            out.append(f"meanings.{k}: only term, meaning and in_text")
    texts += [(f"benefits.{k}", b) for k, b in enumerate(e.get("benefits", []))]
    for name, t in texts:
        bad = sorted(set(ALLOWED.sub("", t)))
        if bad:
            out.append(f"{name}: characters the book doesn't print: {' '.join(f'U+{ord(c):04X}' for c in bad)}")
        if "  " in t or t != t.strip():
            out.append(f"{name}: extra spaces")
    order = [h["id"] for h in matn.hadiths()]
    shared = e.get("shared_with", [])
    if shared:
        k = order.index(i)
        if sorted(shared) != order[k - len(shared):k]:
            out.append("shared_with: the hadith just before it, in order")
        elif any(records()[j]["chapter"] != records()[i]["chapter"] for j in shared):
            out.append("shared_with: the hadith of its own chapter only")
        if not e.get("benefits"):
            out.append("shared_with: but no benefits")
    for c in e.get("corrections", []):
        if set(c) != {"part", "printed", "correction", "reason"}:
            out.append("corrections: each is {part, printed, correction, reason}")
        part = c.get("part", "")
        value = field_value(e, part)
        if value is None or not c.get("printed") or value.count(c["printed"]) != 1:
            out.append(f"corrections: «{c.get('printed')}» must occur once in {part}")
    return out


def field_value(e: dict, field: str) -> str | None:
    parts = field.split(".")
    try:
        if parts[0] == "see":
            return e["see"]
        if parts[0] == "benefits":
            return e["benefits"][int(parts[1])]
        if parts[0] == "meanings":
            return e["meanings"][int(parts[1])][parts[2]]
    except (IndexError, KeyError, ValueError, TypeError):
        return None
    return None


def corrected(e: dict) -> dict:
    """The entry with its corrections applied: the text the app shows."""
    e = json.loads(json.dumps(e))
    for c in e.get("corrections", []):
        parts = c["part"].split(".")
        if parts[0] == "see":
            e["see"] = e["see"].replace(c["printed"], c["correction"])
        elif parts[0] == "benefits":
            k = int(parts[1])
            e["benefits"][k] = e["benefits"][k].replace(c["printed"], c["correction"])
        else:
            m = e["meanings"][int(parts[1])]
            m[parts[2]] = m[parts[2]].replace(c["printed"], c["correction"])
    return e


def words_changed(e: dict) -> int:
    """How many of the draft's words the transcription changed, letters or marks."""
    d = draft(e["id"])["entry"]
    def flat(x):
        return (" ".join([x.get("see") or ""] + [m["term"] + " " + m["meaning"] for m in x["meanings"]]
                         + x["benefits"])).split()
    a, b = flat(d), flat(e)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")


# ---------------------------------------------------------------- commands

def cmd_next(ids: list[int], count: int, pages: int) -> None:
    box = inbox()
    if box:
        print(f"content/commentary/inbox.json already holds {sorted(box)}: finish them, then run `done`.")
        ids = sorted(box)
    else:
        if not ids:
            first = todo()
            seen = set()
            for i in first:
                span = draft(i)["entry"]["pages"]
                more = set(range(span[0], span[-1] + 1))
                if ids and (len(ids) >= count or len(seen | more) > pages):
                    break
                ids.append(i)
                seen |= more
        for i in ids:
            box[i] = draft(i)["entry"]
        write(INBOX, box)
    for i in ids:
        d = draft(i)
        h = records()[i]
        print(f"\n=== h. {i} (p. {h['page']}; commentary on p. {'–'.join(map(str, box[i]['pages']))})")
        print(f"source note (not kept): {d['source'] or '—'}")
        print(f"benefits heading: {d['heading'] or '—'}")
        for p in crops(i):
            print(f"crop: {p}")
    print(f"\n{len(ids)} hadith in content/commentary/inbox.json. Left after them: {len(todo())}")


def cmd_done() -> None:
    box = inbox()
    if not box:
        raise SystemExit("content/commentary/inbox.json is empty")
    ids = set(box)
    bad = {i: problems(e, ids) for i, e in box.items()}
    bad = {i: p for i, p in bad.items() if p}
    for i, ps in bad.items():
        for p in ps:
            print(f"h. {i}: {p}")
    if bad:
        raise SystemExit("Nothing filed: fix these in content/commentary/inbox.json and run `done` again.")
    by_book = {}
    for i, e in box.items():
        by_book.setdefault(book_file(i), {})[i] = e
    for book, entries in by_book.items():
        path = KEPT / f"{book}.json"
        have = {int(k): v for k, v in json.loads(path.read_text(encoding="utf-8")).items()} if path.exists() else {}
        have.update(entries)
        write(path, have)
    for i, e in sorted(box.items()):
        print(f"h. {i}: {len(e['meanings'])} meanings, {len(e['benefits'])} benefits"
              + (f", shared with {e['shared_with']}" if e["shared_with"] else "")
              + f"; {words_changed(e)} words changed from the OCR draft")
    INBOX.unlink()
    print(f"filed {len(box)}; left: {len(todo())}")


def cmd_check() -> None:
    entries = kept()
    n = 0
    for i, e in sorted(entries.items()):
        for p in problems(e, set(entries)):
            print(f"h. {i}: {p}")
            n += 1
    print(f"{len(entries)} hadith transcribed, {n} problems")


def audit_texts() -> dict[int, dict]:
    out = {}
    for f in sorted(AUDIT.glob("*.json")):
        a = json.loads(f.read_text(encoding="utf-8"))
        for p in a["printed"]:
            out[p["number"]] = p
    return out


def pilot_ids() -> set[int]:
    """The audit's hadith, and the hadith after them whose benefits the book prints for them too (h. 1431 for 1430)."""
    out = set()
    for i, p in audit_texts().items():
        out.add(i)
        out |= {int(x) for x in re.findall(r"\d+", (p.get("shared_with") or "").split(":")[0]) if int(x) > i}
    return out


def flat(meanings: list[dict], benefits: list[str]) -> list[str]:
    text = " ".join([m["term"] + " : " + m["meaning"] for m in meanings] + benefits)
    return [w for w in tidy(text).split() if normalize_word(w) or w in "،؛؟:."]


def cmd_score() -> None:
    truth = audit_texts()
    have = {**kept(), **inbox()}
    total = wrong = letters = 0
    for i in sorted(truth):
        if i not in have:
            print(f"h. {i}: not transcribed yet")
            continue
        t, e = truth[i], corrected(have[i])
        benefits = e["benefits"] or next((corrected(x)["benefits"] for x in have.values() if i in x["shared_with"]), [])
        a = flat(t.get("meanings", []), t.get("benefits", []))
        b = flat(e["meanings"], benefits)
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        total += len(a)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            x, y = " ".join(a[i1:i2]), " ".join(b[j1:j2])
            wrong += max(i2 - i1, j2 - j1)
            same = [normalize_word(w) for w in a[i1:i2] if normalize_word(w)] == \
                   [normalize_word(w) for w in b[j1:j2] if normalize_word(w)]
            letters += 0 if same else max(i2 - i1, j2 - j1)
            print(f"h. {i}: audit «{x}» · transcribed «{y}»" + (" (marks or punctuation)" if same else ""))
        if len(t.get("meanings", [])) != len(e["meanings"]) or len(t.get("benefits", [])) != len(benefits):
            print(f"h. {i}: {len(t.get('meanings', []))}/{len(t.get('benefits', []))} meanings/benefits in the audit,"
                  f" {len(e['meanings'])}/{len(benefits)} transcribed")
    if total:
        print(f"\n{total} words in the audit's text; {wrong} differ ({wrong / total:.1%}), "
              f"{letters} in their letters ({letters / total:.1%})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["next", "done", "check", "crop", "draft", "score", "left"])
    parser.add_argument("ids", type=int, nargs="*")
    parser.add_argument("--count", type=int, default=6)
    parser.add_argument("--pages", type=int, default=4)
    args = parser.parse_args()
    if args.cmd == "next":
        cmd_next(args.ids, args.count, args.pages)
    elif args.cmd == "done":
        cmd_done()
    elif args.cmd == "check":
        cmd_check()
    elif args.cmd == "crop":
        for i in args.ids:
            for p in crops(i):
                print(p)
    elif args.cmd == "draft":
        for i in args.ids:
            d = draft(i)
            print(json.dumps(d, ensure_ascii=False, indent=1))
    elif args.cmd == "score":
        cmd_score()
    else:
        print(f"{len(todo())} left of {len(matn.hadiths())}")


if __name__ == "__main__":
    main()
