"""Content step 4: check the hadith text (matn) of every hadith against the book.

Usage: python tools/matn.py compare          compare every matn not yet checked; writes .cache/matn.json
       python tools/matn.py stats            totals of the last comparison
       python tools/matn.py next [ID ...]    the next hadith to check, up to 12 and 800 words (--count, --words),
                                             with crops of the scan
       python tools/matn.py apply [--all]    apply content/matn/inbox.json (--all: every decision again)
       python tools/matn.py show ID          one hadith's words in doubt, accepted ones too
       python tools/matn.py crop ID ...      render the matn of these hadith from the scan

The method and the rules for the review rounds are in docs/matn.md.

The matn in content/hadith/ is v1's text (step 2). It is compared word by word with three sources:
- the OCR text of the book's pages (aljam3), the only one that reads this print. Where it has the
  same letters as v1, the letters are accepted: two independent readings rarely make the same
  mistake. Its tashkeel is unreliable (docs/audit.md), so it only confirms a mark of v1's;
- sunnah.com's Riyad al-Salihin, a check on the letters from another edition;
- the vocalized collections (hadith-api): a check on the tashkeel wherever the wording matches,
  and a vocabulary of the ways each word is vocalized.

Doubtful words (settled on the scan, see docs/matn.md):
- letters: the OCR text has other letters for a word of v1's, or none, or has words v1 lacks.
  The OCR text's usual misreadings are left out: the ﷺ glyph read as words, stray letters,
  commentary it puts inside the matn out of line order, and, where sunnah.com has v1's word, a
  word with v1's letters but other dots (accepted, `dots`) or one of its habitual misreadings
  (MISREADINGS; accepted, `misread`). Spellings that don't change the reading (SPELLINGS) are
  accepted the same way: v1's is kept. A letters doubt is also accepted where Tesseract has v1's
  word (`tesseract`): it reads the matn font poorly, but it is a third reading;
- tashkeel: every collection that has the word marks a letter differently (a letter marked in one
  text and bare in the other is not a conflict, because editions mark different letters);
- unattested: no collection vocalizes the word as v1 does, apart from its last letter, whose case
  ending depends on the sentence. Most of these are v1's typos: a mark on the wrong letter.
- ocr-tashkeel: the OCR text marks a letter otherwise than v1, and no collection marks that letter
  as v1 does. The OCR text's tashkeel is often wrong, but it catches v1's wrong case endings.
A tashkeel doubt is accepted (`ocr`) when the OCR text has v1's marks on every letter in question.
- after: the OCR text has words printed like the matn, vocalized, after v1's last word and before
  the commentary: the book may print more than v1 has (matn_after).
- stray: a mark on no letter in v1's text, to be removed.
`next` also lists v1's words with no mark at all, which are given the book's marks.
"""

import argparse
import difflib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from functools import cache

import pymupdf

from arabic import expand_salutation, normalize_word
from numbering import align, book_words, page_lines, page_start, trim
from ocr import HADITH_PAGES, OUT as OCR_OUT, read_pages, words as tesseract_words
from sources import CACHE, ROOT, collections, ocr_pages, pdf_path, sunnah_riyad

CONTENT = ROOT / "content" / "hadith"
CHECKED = ROOT / "content" / "matn"
OUT = CACHE / "matn.json"
VOWELS = set("ًٌٍَُِْ")
SHADDA = "ّ"
MARK = re.compile(r"[ً-ٰۡ]")
LETTER = re.compile(r"[ء-يٱ]")
SALUTATION = {"صلي", "الله", "عليه", "وسلم"}
CANDIDATES = 4     # collection hadith compared with each matn
MIN_BLOCK = 3      # words in a row a collection must share with v1 for its tashkeel to count
ATTESTED = 2       # times a word must occur in the collections for the vocabulary to judge it
LINE = 0.035       # a matn line's height, as a share of the page
SKELETON = str.maketrans("بتثنيىجخذزشضظغفقة", "ٮٮٮٮٮٮححدرسصطعٯٯه")
SEPARATORS = {"رواه", "الحديث", "لغه", "افاد", "افادت"}  # words of a source note or commentary
# Spellings of the same word that don't change its reading: v1's is kept.
SPELLINGS = {("داود", "داوود"), ("داوود", "داود"), ("السماوات", "السموات"), ("مايه", "ميه"), ("مايتي", "ميتي"),
             ("الزنا", "الزني")}
# The OCR text's habitual misreadings of the matn font, checked on the scan: «عنهما» read
# «عنها» (h. 354), «النبي» read «الني», or «التي» / «الذي» beside the ﷺ glyph (h. 84).
MISREADINGS = {("النبي", "التي"), ("النبي", "الذي"), ("النبي", "النيل")}


def misread(v1: str, ocr: str) -> bool:
    """The OCR text's word is one of its habitual misreadings of v1's, or v1's in another spelling."""
    if (v1, ocr) in SPELLINGS or (v1, ocr) in MISREADINGS:
        return True
    if v1.endswith("ما") and ocr == v1[:-2] + "ا":       # the م of «ـهما» dropped
        return True
    return "بي" in v1 and ocr == v1.replace("بي", "ي", 1)  # the tooth of ب in «النبي» dropped


def hadiths() -> list[dict]:
    """Every hadith in content/hadith/, in the book's order, with its matn as one text."""
    out = []
    for f in sorted(CONTENT.glob("*.json")):
        for c in json.loads(f.read_text(encoding="utf-8"))["chapters"]:
            for h in c["hadith"]:
                out.append({"id": h["id"], "old_id": h["old_id"], "book": f.stem, "chapter": c["number"],
                            "page": h["page"], "text": "".join(p["text"] for p in h["matn"])})
    return sorted(out, key=lambda h: h["id"])


def checked() -> set[int]:
    """The hadith whose matn has been checked: those with a decision in content/matn/NN.json."""
    return {int(i) for f in CHECKED.glob("[0-9][0-9].json") for i in json.loads(f.read_text(encoding="utf-8"))}


def todo() -> list[int]:
    """The hadith whose matn isn't checked yet, in the book's order."""
    done = checked()
    return [h["id"] for h in hadiths() if h["id"] not in done]


def tokens(text: str) -> list[dict]:
    """The words of a text: as written (`w`), normalized letters (`n`) and offset (`at`). The
    salutation ﷺ becomes its four words, marked `sal`: the OCR reads the glyph as text or misreads it."""
    out = []
    for m in re.finditer(r"\S+", text):
        if "ﷺ" in m.group():
            out += [{"w": w, "n": normalize_word(w), "at": m.start(), "sal": True} for w in expand_salutation("ﷺ").split()]
            if not normalize_word(m.group().replace("ﷺ", "")):
                continue
        n = normalize_word(m.group())
        if n:
            out.append({"w": m.group(), "n": n, "at": m.start()})
    return out


def bare(text: str) -> list[str]:
    """The runs of words in a matn with no mark at all, as they stand in it (the book's marks are
    written on them, docs/matn.md). A run of one-letter words alone, such as «و», is left out."""
    runs, start, longest = [], None, 0
    for m in re.finditer(r"\S+", text + " ﷺ"):  # the ﷺ closes the last run
        w = m.group()
        letters = len(LETTER.findall(w))
        if "ﷺ" not in w and not letters:
            continue  # punctuation on its own
        if "ﷺ" not in w and not MARK.search(w):
            if start is None:
                start, longest = m.start(), 0
            end, longest = m.end(), max(longest, letters)
            continue
        if start is not None and longest >= 2:
            runs.append(text[start:end])
        start = None
    return runs


def marks(word: str) -> list[str]:
    """The marks on each letter of a word, sorted. The dagger alif counts as a fatha (هٰكذا /
    هَكذا), and a tanween written on the alif after a letter moves to that letter (كتاباً / كتابًا)."""
    word = unicodedata.normalize("NFC", word).replace("ۡ", "ْ").replace("ٰ", "َ")
    out, letters = [], []
    for ch in word:
        if LETTER.fullmatch(ch):
            out.append("")
            letters.append(ch)
        elif MARK.fullmatch(ch) and out:
            out[-1] += ch
    for k in range(1, len(out)):
        if letters[k] == "ا" and "ً" in out[k] and not out[k - 1]:
            out[k - 1], out[k] = "ً", out[k].replace("ً", "")
    return ["".join(sorted(m)) for m in out]


def differ(x: str, y: str) -> bool:
    """Two letters' marks conflict: both marked, with another vowel or a shadda in one only."""
    if not x or not y:
        return False
    vx, vy = set(x) & VOWELS, set(y) & VOWELS
    return bool(vx and vy and vx != vy) or ((SHADDA in x) != (SHADDA in y))


def conflicts(a: str | list, b: str | list) -> list[int]:
    """The letters whose marks conflict in two words (or mark lists) with the same letters."""
    ma = marks(a) if isinstance(a, str) else a
    mb = marks(b) if isinstance(b, str) else b
    if len(ma) != len(mb):
        return []
    return [k for k, (x, y) in enumerate(zip(ma, mb)) if differ(x, y)]


def confirmed(v1: str, ocr: str, letters: list[int]) -> bool:
    """The OCR text marks every one of these letters of v1's word exactly as v1 does."""
    mv, mo = marks(v1), marks(ocr)
    return len(mv) == len(mo) and all(mo[k] and mo[k] == mv[k] for k in letters)


@cache
def ocr_tokens() -> list[tuple[str, str]]:
    """Every OCR word of the book as written, in the same order as numbering.book_words()."""
    out = []
    for n in range(1, len(ocr_pages()) + 1):
        for line in page_lines(n):
            for w in expand_salutation(line).split():
                if normalize_word(w):
                    out.append((w, normalize_word(w)))
    assert [n for _, n in out] == book_words()[0]
    return out


@cache
def sunnah_index() -> tuple[list[list[str]], dict]:
    texts = [[normalize_word(w) for w in expand_salutation(t).split()] for t in sunnah_riyad()]
    texts = [[w for w in t if w] for t in texts]
    index = defaultdict(set)
    for k, t in enumerate(texts):
        for pair in zip(t, t[1:]):
            index[pair].add(k)
    return texts, index


def sunnah_check(v1: list[dict]) -> dict:
    """For each v1 word, whether the sunnah.com hadith that shares the most pairs of words with
    the matn has it, aligned."""
    texts, index = sunnah_index()
    ns = [t["n"] for t in v1]
    pairs = set(zip(ns, ns[1:]))
    votes = Counter(k for p in pairs for k in index.get(p, ()))
    if not votes:
        return {"share": 0.0, "sunnah": None, "same": [False] * len(v1)}
    best, shared = min(votes.items(), key=lambda kv: (-kv[1], kv[0]))  # a tie goes to the first, in every run
    same = [False] * len(v1)
    for b in difflib.SequenceMatcher(None, ns, texts[best], autojunk=False).get_matching_blocks():
        for j in range(b.size):
            same[b.a + j] = True
    return {"share": round(shared / max(1, len(pairs)), 2), "sunnah": best + 1, "same": same}


@cache
def collection_index() -> tuple[list[tuple[str, int, list[tuple[str, str]]]], dict]:
    """The collections' hadith as (collection, number, [(word as written, normalized)]), and an
    index of runs of four normalized words."""
    texts = []
    for name, hs in collections().items():
        for k, t in enumerate(hs):
            ws = [(w, normalize_word(w)) for w in t.split()]
            texts.append((name, k + 1, [(w, n) for w, n in ws if n]))
    index = defaultdict(list)
    for k, (_, _, ws) in enumerate(texts):
        ns = [n for _, n in ws]
        for gram in set(zip(ns, ns[1:], ns[2:], ns[3:])):
            index[gram].append(k)
    return texts, index


@cache
def vocabulary() -> dict[str, Counter]:
    """For each normalized word in the collections, how often each way of marking it occurs."""
    vocab = defaultdict(Counter)
    for _, _, ws in collection_index()[0]:
        for w, n in ws:
            m = tuple(marks(w))
            if any(m):
                vocab[n][m] += 1
    return vocab


def collection_check(v1: list[dict]) -> dict:
    """For each v1 word, the same word in the collection hadith that share the most runs of four
    words with the matn, where they have it inside a shared run of MIN_BLOCK words or more."""
    texts, index = collection_index()
    ns = [t["n"] for t in v1]
    grams = set(zip(ns, ns[1:], ns[2:], ns[3:]))
    votes = Counter(k for g in grams for k in index.get(g, ()) if len(index[g]) < 400)
    forms = [[] for _ in v1]
    used = []
    # Ties go to the first in the collections' order: set order changes from run to run.
    for k, shared in sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))[:CANDIDATES]:
        if shared < 2:
            break
        name, number, ws = texts[k]
        sm = difflib.SequenceMatcher(None, ns, [n for _, n in ws], autojunk=False)
        for b in sm.get_matching_blocks():
            if b.size >= MIN_BLOCK:
                for j in range(b.size):
                    if not v1[b.a + j].get("sal"):
                        forms[b.a + j].append((f"{name} {number}", ws[b.b + j][0]))
        used.append(f"{name} {number}")
    return {"used": used, "forms": forms}


def letter_kind(v1: str, ocr: str, one_each: bool) -> str:
    """How a v1 passage and the OCR text's differ: `split` (same letters, other spaces), `dots`
    (same shapes, other dots), `prefix` (one word with a letter or two more in front) or `other`."""
    if v1 == ocr:
        return "split"
    if v1.translate(SKELETON) == ocr.translate(SKELETON):
        return "dots"
    if one_each and (v1.endswith(ocr) or ocr.endswith(v1)):
        return "prefix"
    return "other"


def letter_items(v1: list[dict], ocr: list[tuple[str, str]], sunnah: list[bool]) -> tuple[list, list]:
    """The places where v1's letters and the OCR text's differ. Returns the items and, for each
    v1 word, the OCR word with the same letters (or None)."""
    sm = difflib.SequenceMatcher(None, [t["n"] for t in v1], [n for _, n in ocr], autojunk=False)
    same = [None] * len(v1)
    items = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal":
            for k in range(a2 - a1):
                same[a1 + k] = ocr[b1 + k][0]
            continue
        mine = [k for k in range(a1, a2) if not v1[k].get("sal")]
        theirs = ocr[b1:b2]
        near_sal = any(v1[k].get("sal") for k in range(max(0, a1 - 1), min(len(v1), a2 + 1)))
        if mine != list(range(a1, a2)):  # v1's ﷺ is here: drop what the OCR made of the glyph
            theirs = [t for t in theirs if t[1] not in SALUTATION | {"لا", "الا"}]
            if not mine and len(theirs) <= 2:
                continue
        if not mine:
            if a1 == 0 or a1 >= len(v1):
                continue  # at the edges: the text around the matn
            if len(theirs) == 1 and len(theirs[0][1]) <= 2:
                continue  # a stray letter or two
            if near_sal and len(theirs) <= 2:
                continue  # the ﷺ glyph misread
            if len(theirs) >= 12 and SEPARATORS & {n for _, n in theirs}:
                continue  # commentary the OCR text put inside the matn, out of the print's line order
            items.append({"k": a1, "n": 0, "kind": "extra", "ocr": " ".join(w for w, _ in theirs), "doubt": True})
            continue
        text_v1 = "".join(v1[k]["n"] for k in mine)
        text_ocr = "".join(n for _, n in theirs)
        kind = "missing" if not theirs else letter_kind(text_v1, text_ocr, len(mine) == len(theirs) == 1)
        agree = all(sunnah[k] for k in mine)
        habit = len(mine) == 1 and agree and misread(text_v1, " ".join(n for _, n in theirs))
        items.append({"k": mine[0], "n": mine[-1] - mine[0] + 1, "kind": kind, "sunnah": agree,
                      "v1": " ".join(v1[k]["w"] for k in mine), "ocr": " ".join(w for w, _ in theirs),
                      "doubt": not ((kind == "dots" and agree) or habit), **({"misread": True} if habit else {})})
    return items, same


def tashkeel_items(v1: list[dict], same: list, forms: list[list]) -> list[dict]:
    """The words whose tashkeel is in doubt, among those whose letters the OCR text confirms."""
    vocab = vocabulary()
    items = []
    for k, t in enumerate(v1):
        o = same[k]
        if t.get("sal") or o is None or not any(marks(t["w"])):
            continue
        against = [(src, w) for src, w in forms[k] if conflicts(t["w"], w)]
        if against and len(against) == len(forms[k]):
            letters = sorted({j for _, w in against for j in conflicts(t["w"], w)})
            items.append({"k": k, "n": 1, "kind": "tashkeel", "v1": t["w"], "ocr": o,
                          "collections": against[:3], "doubt": not confirmed(t["w"], o, letters)})
            continue
        theirs = conflicts(t["w"], o)
        if theirs and not any(all(not differ(marks(w)[j], marks(t["w"])[j]) and marks(w)[j] for j in theirs)
                              for _, w in forms[k] if len(marks(w)) == len(marks(t["w"]))):
            items.append({"k": k, "n": 1, "kind": "ocr-tashkeel", "v1": t["w"], "ocr": o,
                          "collections": against[:3], "doubt": True})
            continue
        if forms[k]:
            continue
        sigs = vocab.get(t["n"])
        if not sigs or sum(sigs.values()) < ATTESTED:
            continue
        inner = marks(t["w"])[:-1]
        if any(not conflicts(inner, list(s[:-1])) for s in sigs):
            continue
        usual = sigs.most_common(1)[0][0]
        letters = conflicts(inner, list(usual[:-1]))
        items.append({"k": k, "n": 1, "kind": "unattested", "v1": t["w"], "ocr": o,
                      "usual": "".join(c + m for c, m in zip(re.sub(r"[^ء-يٱ]", "", t["w"]), usual)),
                      "doubt": not confirmed(t["w"], o, letters)})
    return items


@cache
def tesseract_page(n: int) -> list[dict]:
    """A page's Tesseract words with their normalized letters, in reading order: Tesseract gives
    its words block by block, not always from the top of the page down, so they are grouped into
    printed lines by height on the page, lines from the top, words from the right. [] if the page
    wasn't read."""
    if not (OCR_OUT / f"p{n:04d}.tsv").exists():
        return []
    ws = sorted(tesseract_words(n), key=lambda w: (w["box"][1] + w["box"][3]) / 2)
    lines = []
    for w in ws:
        y = (w["box"][1] + w["box"][3]) / 2
        if lines and abs(y - lines[-1][0]) < LINE / 3:
            lines[-1][1].append(w)
        else:
            lines.append([y, [w]])
    out = []
    for _, line in lines:
        for w in sorted(line, key=lambda w: -w["box"][2]):
            for part in expand_salutation(w["text"]).split():
                if normalize_word(part):
                    out.append({**w, "n": normalize_word(part), "page": n})
    return out


def tesseract_window(span: list[int] | None, page: int) -> tuple[list[dict], dict, dict]:
    """Tesseract's words for the part of the page(s) where the matn is printed, and the anchors
    around it. The OCR text and Tesseract both read the commentary well, so their readings of the
    pages are aligned: the window runs from the last run of three words they share before the matn
    (in the OCR text, `span` of numbering.book_words()) to the first run after it. The anchors are
    {page, y} of the bottom of that last run and the top of that first run ({} if there is none)."""
    if not span:
        return [w for n in (page, page + 1) for w in tesseract_page(n)], {}, {}
    where = book_words()[1]
    first, last = where[span[0]][0], where[span[1] - 1][0]
    starts = page_start()
    a0 = starts[first]
    a1 = next((starts[n] for n in range(last + 1, last + 20) if n in starts), len(where))
    tess = [w for n in range(first, last + 1) for w in tesseract_page(n)]
    sm = difflib.SequenceMatcher(None, book_words()[0][a0:a1], [w["n"] for w in tess], autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= 3]
    before = [b for b in blocks if a0 + b.a + b.size <= span[0]]
    after = [b for b in blocks if a0 + b.a >= span[1]]
    lo = before[-1].b + before[-1].size if before else 0
    hi = after[0].b if after else len(tess)
    top = {"page": tess[lo - 1]["page"], "y": tess[lo - 1]["box"][3]} if before else {}
    bottom = {"page": tess[hi]["page"], "y": tess[hi]["box"][1]} if after else {}
    return (tess[lo:hi] if lo < hi else tess), top, bottom


def tesseract_check(v1: list[dict], window: list[dict]) -> dict:
    """v1's words against Tesseract's reading of the matn (tesseract_window). Tesseract reads the
    matn font poorly, but where it has a v1 word's letters (inside a run of two matched words or
    more, or a word of four letters or more), that is a third reading of the print. Returns, for
    each v1 word, the Tesseract word it matches (or None), and whether the word just before it is
    matched to the Tesseract word just before (nothing printed between them)."""
    match = [None] * len(v1)
    joined = [False] * len(v1)
    sm = difflib.SequenceMatcher(None, [t["n"] for t in v1], [w["n"] for w in window], autojunk=False)
    for b in trim([b for b in sm.get_matching_blocks() if b.size]):
        for j in range(b.size):
            if b.size >= 2 or len(v1[b.a].get("n", "")) >= 4:
                match[b.a + j] = window[b.b + j]
                joined[b.a + j] = j > 0
    keep = down_the_page(match)
    match = [w if k in keep else None for k, w in enumerate(match)]
    joined = [j and k in keep and k - 1 in keep for k, j in enumerate(joined)]
    return {"match": match, "joined": joined}


def down_the_page(match: list) -> set[int]:
    """The longest chain of matched words that moves down the page as the matn goes on, about a
    line for every 10 words: a match off that chain is the same word printed elsewhere, such as
    «رواه الترمذي» in the commentary below."""
    hits = [(k, w["page"] + (w["box"][1] + w["box"][3]) / 2) for k, w in enumerate(match) if w is not None]
    best = [1] * len(hits)
    prev = [-1] * len(hits)
    for j, (kj, yj) in enumerate(hits):
        for i in range(j):
            ki, yi = hits[i]
            room = LINE * (1.5 + (kj - ki) / 8) + (0.3 if int(yj) != int(yi) else 0)
            if -LINE / 2 <= yj - yi <= room and best[i] + 1 > best[j]:
                best[j], prev[j] = best[i] + 1, i
    if not hits:
        return set()
    j = max(range(len(hits)), key=best.__getitem__)
    out = set()
    while j >= 0:
        out.add(hits[j][0])
        j = prev[j]
    return out


CROP_DPI = 230     # enough to read the matn's tashkeel; a full-width crop is then about 1,430 px wide


def page_lines_ink(ink) -> list[tuple[float, float]]:
    """The printed lines of a page as (top, bottom) shares of the page, from its rows of ink. Ink
    that runs down the page, such as the binding's shadow at the side of a scan (p. 1247), is taken
    out first: a row counts only its ink above the least of the rows within a line of it. A band of
    ink at the top or bottom edge of the scan (p. 30) is not a line."""
    size = len(ink.rows)
    reach = int(LINE * size)
    rows = [count - min(ink.rows[max(0, r - reach): r + reach + 1]) for r, count in enumerate(ink.rows)]
    least = (max(rows) or 1) * 0.01
    out, start = [], None
    for r, count in enumerate(rows + [0]):
        if count > least and start is None:
            start = r
        elif count <= least and start is not None:
            if r - start > 2 and start > 0.01 * size and r < 0.99 * size:
                out.append((start / size, r / size))
            start = None
    return out


def text_bottom(page, ink, below: float) -> float:
    """Where a page's text ends below a height: above the short rule that opens its footnotes, if
    there is one below that height (a chapter's footnotes can come in the middle of the page,
    after its verses), else above its last line (the page number). The edges of the scan, which
    can be dark (p. 30), aren't searched."""
    pix = page.get_pixmap(dpi=100, colorspace=pymupdf.csGRAY)
    w, h, data = pix.width, pix.height, pix.samples
    dark = bytes(1 if v < 160 else 0 for v in range(256))
    rows = [data[y * pix.stride: y * pix.stride + w].translate(dark) for y in range(h)]
    counts = [row.count(1) for row in rows]
    for y in range(max(int(below * h) + 1, int(0.02 * h)), int(0.98 * h)):
        run = max(map(len, rows[y].split(b"\x00")))
        down = min(counts[max(0, y - 10): y + 11])  # ink running down the page, such as the binding's shadow
        if run >= 0.14 * w and counts[y] - down <= 1.2 * run:  # alone on its row, unlike a long kashida
            return y / h - 0.005
    lines = page_lines_ink(ink)
    return lines[-1][0] - 0.005 if lines else 1.0


def cut(ink, lo: float, hi: float) -> float:
    """The row with the least ink between two heights on the page (shares of the page)."""
    size = len(ink.rows)
    a, b = max(0, int(lo * size)), min(size - 1, int(hi * size))
    return min(range(a, b + 1), key=lambda r: (ink.rows[r], r)) / size if a <= b else lo


def matn_region(doc, first: int, last: int, top: dict, bottom: dict) -> list[tuple[int, float, float]]:
    """Where the matn is printed: (page, top, bottom) on each page from first to last. It starts
    below the commentary before it (`top`, from tesseract_window) and ends above the commentary
    after it (`bottom`), cut at the gaps between lines; where it runs over a page, it goes to the
    end of the page's text and starts again at the top of the next page's."""
    from zoom import Ink
    out = []
    for n in range(first, last + 1):
        page = doc[n - 1]
        ink = Ink(page)
        lines = page_lines_ink(ink)
        if top and top["page"] == n:
            y0 = cut(ink, top["y"] - 0.005, top["y"] + LINE / 2)
        else:
            y0 = max(0.0, (lines[0][0] if lines else 0.0) - 0.005)
        if bottom and bottom["page"] == n:
            y1 = cut(ink, bottom["y"] - LINE / 2, bottom["y"] + 0.005)
        else:
            y1 = text_bottom(page, ink, y0)
        if y1 - y0 > 0.01:
            out.append((n, y0, y1))
        elif first < n < last and lines:  # the matn fills this page: it is never left out
            out.append((n, max(0.0, lines[0][0] - 0.005), min(1.0, lines[-1][1] + 0.005)))
    return out


def crop_region(doc, h: dict) -> list[tuple[int, float, float]]:
    """Where hadith h's matn is printed: (page, top, bottom) on each of its pages."""
    found = locate(h, tokens(h["text"]))
    span = found["span"]
    if span:  # down to the end of what the book prints after v1's last word (matn_after)
        span = [span[0], span[1] + matn_after(h, span[1])]
    _, top, bottom = tesseract_window(span, h["page"])
    where = book_words()[1]
    first, last = (where[span[0]][0], where[span[1] - 1][0]) if span else (h["page"], h["page"])
    # The words matched around the matn can be the same words printed elsewhere: a match on a page
    # after the matn's first page isn't above it (h. 837), and matches that cross, or leave no room
    # for the matn between them, aren't around it (h. 424). The page's edge is used instead.
    if top and top["page"] > first:
        top = {}
    if bottom and bottom["page"] < last:
        bottom = {}
    if top and bottom and top["page"] == bottom["page"] and bottom["y"] - top["y"] < LINE:
        top, bottom = {}, {}
    if top:  # opening words the OCR text lacks are above where it starts
        top = {**top, "y": max(0.0, top["y"] - LINE * (found["head"] // 6))}
    if bottom:
        bottom = {**bottom, "y": min(1.0, bottom["y"] + LINE * (found["tail"] // 6))}
    return matn_region(doc, first, last, top, bottom) or [(h["page"], 0.0, 1.0)]


def crops(i: int) -> list[str]:
    """Render the matn of hadith i from the scan, one image per page; returns their paths."""
    h = next(h for h in hadiths() if h["id"] == i)
    doc = pymupdf.open(pdf_path())
    out_dir = CACHE / "matn-crops"
    out_dir.mkdir(exist_ok=True)
    for old in out_dir.glob(f"h{i:04d}-*.png"):  # an earlier rendering may have had other pages
        old.unlink()
    paths = []
    for k, (n, y0, y1) in enumerate(crop_region(doc, h)):
        page = doc[n - 1]
        r = page.rect
        clip = pymupdf.Rect(r.x0, r.y0 + r.height * y0, r.x1, r.y0 + r.height * y1)
        path = out_dir / f"h{i:04d}-{k + 1}-p{n:04d}.png"
        page.get_pixmap(dpi=CROP_DPI, clip=clip, colorspace=pymupdf.csGRAY).save(path)
        paths.append(f"{path.relative_to(ROOT)} (p. {n}, {y0:.2f}–{y1:.2f})")
    return paths


def tesseract_confirms(item: dict, tess: dict) -> bool:
    """Tesseract reads the print as v1 has it: it has v1's words, or (for words the OCR text has
    and v1 lacks) nothing between the v1 words around them."""
    k, n = item["k"], item["n"]
    if item["kind"] == "extra":
        return k < len(tess["joined"]) and tess["joined"][k]
    return all(tess["match"][j] is not None for j in range(k, k + n))


def matn_span(h: dict, v1: list[dict], after: int = 0) -> dict:
    """Where the matn is in the OCR text (numbering.align), starting on the page step 3 gives for
    the hadith, and after OCR word `after`, where the matn before it ends: words matched before
    either are the same phrase in the hadith before. Adds `head` and `tail`, the number of v1's
    words before the first word matched and after the last."""
    found = align({"matn": h["text"]}, h["page"], after)
    if not found["span"]:
        return {**found, "head": 0, "tail": 0}
    where = book_words()[1]
    lo, hi = found["span"]
    ocr = [n for _, n in ocr_tokens()[lo:hi]]
    sm = difflib.SequenceMatcher(None, [t["n"] for t in v1], ocr, autojunk=False)
    pairs = [(b.a + j, lo + b.b + j) for b in sm.get_matching_blocks() for j in range(b.size)]
    pairs = [(a, b) for a, b in pairs if where[b][0] >= h["page"]] or pairs
    if pairs:
        lo = pairs[0][1]
    return {**found, "span": [lo, hi], "head": pairs[0][0] if pairs else 0,
            "tail": len(v1) - 1 - pairs[-1][0] if pairs else 0}


@cache
def neighbours() -> dict[int, tuple[dict | None, dict | None]]:
    """For each hadith, the ones before and after it in the book's order (None at either end)."""
    hs = hadiths()
    return {h["id"]: (p, n) for p, h, n in zip([None] + hs[:-1], hs, hs[1:] + [None])}


def locate(h: dict, v1: list[dict]) -> dict:
    """matn_span for h, also looked for after the matn before it, as in step 3: a hadith often
    repeats the words of the one before it, and is then found there (h. 1012, in 1010's words).
    But the matn before can run on into this one's words (h. 863), so the place where more of
    v1's words are found is taken."""
    found = matn_span(h, v1)
    prev = neighbours()[h["id"]][0]
    span = matn_span(prev, tokens(prev["text"]))["span"] if prev else None
    if not span:
        return found
    later = matn_span(h, v1, span[1])
    return later if later["found"] >= found["found"] else found


COMMENTARY = {"لغه", "افاد", "افادت", "يستفاد"}  # headings of the commentary: لغة الحديث, أفاد الحديث
SOURCE_NOTE = ({"الحديث", "الحديثان", "الاحاديث"}, {"رواه", "رواهما", "اخرجه", "اخرجهما", "تقدم", "سبق"})


def matn_after(h: dict, hi: int) -> int:
    """How many OCR words after the last word of h's matn the OCR text matched (hi) are printed like
    the matn, vocalized, before the commentary: text the book prints after v1's last word, such as
    Nawawi's explanation of a word or another narration (h. 145, 465, 1147). The commentary opens
    with its source note («الحديث رواه …») or a heading, and isn't vocalized; the OCR text drops
    some of the matn's marks, so a few bare words in a row don't end it. It stops at the next hadith
    too and, where a chapter ends, at the next chapter's heading, whose verses are vocalized."""
    nxt = neighbours()[h["id"]][1]
    end = matn_span(nxt, tokens(nxt["text"]), hi)["span"] if nxt else None
    end = end[0] if end and end[0] > hi else hi + 200
    new_chapter = nxt is None or (nxt["book"], nxt["chapter"]) != (h["book"], h["chapter"])
    toks = ocr_tokens()
    n = gap = 0
    for k in range(hi, min(end, len(toks))):
        w, norm = toks[k]
        if norm in COMMENTARY or (new_chapter and norm == "باب"):
            break
        if norm in SOURCE_NOTE[0] and k + 1 < len(toks) and toks[k + 1][1] in SOURCE_NOTE[1]:
            break
        m = marks(w)
        if len(m) < 2:
            continue  # a letter on its own, such as «و», tells neither way
        if sum(bool(x) for x in m) * 2 >= len(m):
            n, gap = k + 1 - hi, 0
        else:
            gap += 1
            if gap > 8:
                break
    return n


def check(h: dict) -> dict:
    v1 = tokens(h["text"])
    found = locate(h, v1)
    sunnah = sunnah_check(v1)
    coll = collection_check(v1)
    if found["span"]:
        lo, hi = found["span"]
        letters, same = letter_items(v1, ocr_tokens()[lo:hi], sunnah["same"])
        where = book_words()[1]
        span = [where[lo], where[hi - 1]]
        after = matn_after(h, hi)
        if after - found["tail"] >= 3:  # v1's own last words, if the OCR text misread them, aside
            text = " ".join(w for w, _ in ocr_tokens()[hi:hi + min(after, 15)])
            letters.append({"k": len(v1), "n": 0, "kind": "after", "doubt": True,
                            "note": f"the OCR text has {after} vocalized words after v1's last word, before the"
                                    f" commentary: «{text}{' …' if after > 15 else ''}». Read the matn to its end"})
    else:
        letters = [{"k": 0, "n": len(v1), "kind": "missing", "sunnah": False, "v1": h["text"], "ocr": "", "doubt": True}]
        same, span = [None] * len(v1), None
    if found["span"] and found["found"] < 0.6:
        letters.append({"k": 0, "n": 0, "kind": "align", "doubt": True,
                        "note": f"the OCR text has only {found['found']:.0%} of this matn's words in order: check it all"})
    tess = tesseract_check(v1, tesseract_window(found["span"], h["page"])[0])
    for item in letters:
        if item["doubt"] and item["kind"] not in ("split", "align", "after") and tesseract_confirms(item, tess):
            item["doubt"], item["tesseract"] = False, True
    for item in letters:  # what the collections have for a doubtful word
        if item.get("v1") and item["n"] == 1:
            c = [(s, w) for s, w in coll["forms"][item["k"]] if conflicts(v1[item["k"]]["w"], w)]
            if c:
                item["collections"] = c[:3]
    for m in re.finditer(r"\S+", h["text"]):  # a mark on no letter, such as the kasra in «اللهِ ِ ﷺ»
        if MARK.search(m.group()) and not LETTER.search(m.group()):
            letters.append({"k": sum(t["at"] < m.start() for t in v1), "n": 0, "kind": "stray", "v1": m.group(),
                            "doubt": True, "note": f"a mark on no letter, «{m.group()}»: remove it (rule 4)"})
    items = sorted(letters + tashkeel_items(v1, same, coll["forms"]), key=lambda d: d["k"])
    return {
        "id": h["id"], "book": h["book"], "page": h["page"], "words": sum(not t.get("sal") for t in v1),
        "bare": sum(len(r.split()) for r in bare(h["text"])),
        "ocr_found": found["found"], "ocr_span": span,
        "sunnah": sunnah["sunnah"], "sunnah_share": sunnah["share"],
        "collections": coll["used"], "covered": sum(bool(f) for f in coll["forms"]),
        "items": items,
    }


def compare() -> list[dict]:
    read_pages(range(HADITH_PAGES[0], HADITH_PAGES[1] + 1))  # Tesseract's reading, on first use
    print("Comparing every matn not yet checked with the sources", flush=True)
    done = checked()
    rows = []
    for h in hadiths():
        if h["id"] in done:
            continue
        rows.append(check(h))
        if h["id"] % 200 == 0:
            print(f"… {h['id']}", flush=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
    return rows


def compared() -> dict[int, dict]:
    """The last comparison by hadith, made again if there is none (e.g. in a fresh clone) or this
    tool has changed since it was made (e.g. after a pull)."""
    fresh = OUT.exists() and OUT.stat().st_mtime > (ROOT / "tools" / "matn.py").stat().st_mtime
    rows = json.loads(OUT.read_text(encoding="utf-8")) if fresh else compare()
    return {r["id"]: r for r in rows}


def stats(rows: list[dict]) -> None:
    words = sum(r["words"] for r in rows)
    items = [d for r in rows for d in r["items"]]
    print(f"{len(rows)} hadith not yet checked, {words} words; {sum(r['covered'] for r in rows)} found in a collection")
    print(f"matched badly in the OCR text (under 60%): {[r['id'] for r in rows if r['ocr_found'] < 0.6]}")
    print(f"no sunnah.com match (under 30% of pairs): {[r['id'] for r in rows if r['sunnah_share'] < 0.3]}")
    print()
    print("kind         doubts  accepted (by Tesseract)")
    for kind in ("align", "after", "missing", "extra", "split", "dots", "prefix", "other", "stray", "tashkeel",
                 "unattested", "ocr-tashkeel"):
        k = [d for d in items if d["kind"] == kind]
        print(f"{kind:12} {sum(d['doubt'] for d in k):6} {sum(not d['doubt'] for d in k):9}"
              f" ({sum(bool(d.get('tesseract')) for d in k)})")
    doubtful = [r for r in rows if any(d["doubt"] for d in r["items"])]
    print(f"\nhadith with doubts: {len(doubtful)}, on {len({r['page'] for r in doubtful})} pages;"
          f" doubts in all: {sum(d['doubt'] for d in items)}")
    print(f"words with no mark in v1, to be given the book's: {sum(r.get('bare', 0) for r in rows)},"
          f" in {sum(bool(r.get('bare')) for r in rows)} hadith")


def describe(d: dict) -> str:
    if d["kind"] in ("align", "after", "stray"):
        return d["note"]
    parts = [f"v1 «{d['v1']}»" if d.get("v1") else "v1 —", f"OCR «{d['ocr']}»" if d.get("ocr") else "OCR —"]
    if "sunnah" in d:
        parts.append("sunnah.com as v1" if d["sunnah"] else "sunnah.com differs")
    if d.get("usual"):
        parts.append(f"usually «{d['usual']}»")
    if d.get("collections"):
        parts.append("; ".join(f"{s} «{w}»" for s, w in d["collections"]))
    return ", ".join(parts)


def show(i: int) -> None:
    h = next(h for h in hadiths() if h["id"] == i)
    r = compared().get(i) or check(h)
    print(f"hadith {i}, page {r['page']}; OCR found {r['ocr_found']} at {r['ocr_span']};"
          f" sunnah.com {r['sunnah']} ({r['sunnah_share']}); collections {r['collections']}")
    print(h["text"], "\n")
    for d in r["items"]:
        print(f"  {'DOUBT' if d['doubt'] else 'ok   '} {d['kind']:10} {describe(d)}")


def review(ids: list[int], count: int, words: int) -> None:
    """Print the next hadith to check (or the ones asked for): the matn, its doubts, its words with
    no mark and the crops of the scan to read it on (see docs/matn.md). A round takes up to `count`
    hadith, fewer when they're long: no more than `words` words in all, unless the first is longer."""
    rows = compared()
    texts = {h["id"]: h for h in hadiths()}
    if not ids:
        total = 0
        for i in todo():
            n = rows[i]["words"] if i in rows else len(texts[i]["text"].split())
            if len(ids) == count or (ids and total + n > words):
                break
            ids.append(i)
            total += n
        print(f"{len(checked())} of {len(texts)} hadith checked." + ("" if ids else " All are checked: nothing to do."))
        print()
    for i in ids:
        h = texts[i]
        r = rows.get(i) or check(h)
        v1 = tokens(h["text"])
        doubts = [d for d in r["items"] if d["doubt"]]
        print(f"## {i} (p. {r['page']}): {' '.join(crops(i))}")
        if h["old_id"] is None:
            print("Not in v1: transcribed from the scan in step 3. Check every mark at zoom.")
        print(h["text"])
        for n, d in enumerate(doubts, 1):
            k = d["k"]
            before = " ".join(t["w"] for t in v1[max(0, k - 3):k] if not t.get("sal"))
            after = " ".join(t["w"] for t in v1[k + d["n"]:k + d["n"] + 3] if not t.get("sal"))
            print(f"{n}. {d['kind']}: {describe(d)}   [… {before} ⟦{d.get('v1') or '+'}⟧ {after} …]")
        if not doubts:
            print("No doubts listed.")
        runs = bare(h["text"])
        if runs:
            print("No marks in v1 (write the book's): " + " · ".join(f"«{r}»" for r in runs))
        print()


INBOX = CHECKED / "inbox.json"
WHY = {"v1", "variant", "marks"}


def clusters(text: str) -> list[tuple[int, str]]:
    """A text as (offset, letter with its marks in a fixed order), so that two spellings with the
    same marks in another order compare equal."""
    out = []
    for k, ch in enumerate(text):
        if MARK.fullmatch(ch) and out:
            start, c = out[-1]
            out[-1] = (start, c[0] + "".join(sorted(c[1:] + ch)))
        else:
            out.append((k, ch))
    return out


def find(text: str, part: str) -> list[tuple[int, int]]:
    """Where `part` occurs in `text`, ignoring the order of marks: (start, end) offsets in text."""
    t, p = clusters(text), [c for _, c in clusters(part)]
    hits = []
    for k in range(len(t) - len(p) + 1):
        if [c for _, c in t[k:k + len(p)]] == p:
            end = t[k + len(p)][0] if k + len(p) < len(t) else len(text)
            hits.append((t[k][0], end))
    return hits


def fix_matn(matn: list[dict], old: str, new: str, again: bool = False) -> bool:
    """Replace `old` with `new` in the matn. `old` must occur exactly once; where it runs over two
    pieces or more (speaker roles), `new` goes to the first of them. When a decision is applied
    `again`, a fix whose `old` isn't there but whose `new` is was applied before: returns False."""
    joined = "".join(p["text"] for p in matn)
    hits = find(joined, old)
    if len(hits) > 1:
        raise ValueError(f"«{old}» occurs {len(hits)} times; give more words around it")
    if not hits:
        if again and find(joined, new):
            return False
        raise ValueError(f"«{old}» is not in the matn")
    a, b = hits[0]
    pos = 0
    for k, p in enumerate(matn):  # the pieces the replaced text starts and ends in
        end = pos + len(p["text"])
        if pos <= a < end or (a == end and k == len(matn) - 1):
            first, a_in = k, a - pos
        if pos < b <= end:
            last, b_in = k, b - pos
            break
        pos = end
    if first == last:
        matn[first]["text"] = matn[first]["text"][:a_in] + new + matn[first]["text"][b_in:]
    else:
        matn[first]["text"] = matn[first]["text"][:a_in] + new
        matn[last]["text"] = matn[last]["text"][b_in:]
        for k in range(first + 1, last):
            matn[k]["text"] = ""
    matn[:] = [p for p in matn if p["text"]]
    return True


def settle(h: dict, d: dict, again: bool = False) -> None:
    """Apply one hadith's decision (see docs/matn.md) to its record in content/hadith/."""
    unknown = set(d) - {"fix", "misprint", "note"}
    if unknown:
        raise ValueError(f"unknown keys {sorted(unknown)}")
    matn = json.loads(json.dumps(h["matn"]))
    for f in d.get("fix", []):
        if len(f) != 3 or f[2] not in WHY:
            raise ValueError(f"a fix is [from, to, why] with why one of {sorted(WHY)}: {f}")
        fix_matn(matn, f[0], f[1], again)
    corrections = list(h["corrections"])
    for m in d.get("misprint", []):
        if len(m) != 3:
            raise ValueError(f"a misprint is [printed, correction, reason]: {m}")
        c = {"part": "matn", "printed": m[0], "correction": m[1], "reason": m[2]}
        if c not in corrections:
            corrections.append(c)
    h["matn"], h["corrections"] = matn, corrections
    if d.get("note") and d["note"] not in h["notes"]:
        h["notes"].append(d["note"])


def apply(again: bool) -> None:
    """Apply the decisions in content/matn/inbox.json to content/hadith/ and keep them in
    content/matn/NN.json (with --all, apply every kept decision again, e.g. after convert_v1.py)."""
    books = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(CONTENT.glob("*.json"))}
    where = {h["id"]: (stem, h) for stem, b in books.items() for c in b["chapters"] for h in c["hadith"]}
    kept = {stem: json.loads((CHECKED / f"{stem}.json").read_text(encoding="utf-8"))
            if (CHECKED / f"{stem}.json").exists() else {} for stem in books}
    if again:
        decisions = {i: d for stem in kept for i, d in kept[stem].items()}
    else:
        decisions = json.loads(INBOX.read_text(encoding="utf-8")) if INBOX.exists() else {}
    failed, done = {}, 0
    for key, d in decisions.items():
        try:
            if not key.isdigit() or int(key) not in where:
                raise ValueError("no hadith has this number")
            stem, h = where[int(key)]
            if not again and str(int(key)) in kept[stem]:
                # An inbox left from a stopped round, for a hadith someone has checked since:
                # replacing their decision would lose its fixes at the next apply --all.
                print(f"{key}: already checked (content/matn/{stem}.json); this decision is dropped")
                continue
            settle(h, d, again)
        except ValueError as e:
            print(f"{key}: {e}; nothing applied for this hadith")
            failed[key] = d
            continue
        kept[stem][key] = d
        done += 1
    CHECKED.mkdir(exist_ok=True)
    for stem, b in books.items():
        (CONTENT / f"{stem}.json").write_text(json.dumps(b, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if kept[stem]:
            ordered = dict(sorted(kept[stem].items(), key=lambda kv: int(kv[0])))
            (CHECKED / f"{stem}.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not again:
        if failed:
            INBOX.write_text(json.dumps(failed, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        elif INBOX.exists():
            INBOX.unlink()
    print(f"{done} hadith settled, {len(failed)} failed" + (" (left in content/matn/inbox.json)" if failed and not again else ""))
    print(f"checked: {len(checked())} of {len(where)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("compare")
    sub.add_parser("stats")
    s = sub.add_parser("show")
    s.add_argument("id", type=int)
    c = sub.add_parser("crop")
    c.add_argument("ids", type=int, nargs="+")
    n = sub.add_parser("next")
    n.add_argument("ids", type=int, nargs="*")
    n.add_argument("--count", type=int, default=12, help="the most hadith in a round")
    n.add_argument("--words", type=int, default=800, help="the most words of matn in a round, unless the first is longer")
    a = sub.add_parser("apply")
    a.add_argument("--all", action="store_true", help="apply every decision in content/matn/ again")
    args = parser.parse_args()
    if args.cmd == "crop":
        for i in args.ids:
            print(i, " ".join(crops(i)))
    elif args.cmd == "compare":
        stats(compare())
    elif args.cmd == "stats":
        stats(list(compared().values()))
    elif args.cmd == "next":
        review(args.ids, args.count, args.words)
    elif args.cmd == "apply":
        apply(args.all)
    else:
        show(args.id)


if __name__ == "__main__":
    main()
