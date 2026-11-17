"""Content step 4: Riyad al-Salihin's own text, to settle what the print leaves in dispute (docs/matn.md, rule 8).

Usage: python tools/riyad.py show ID ...     a hadith's text beside al-Fahl's, with the words they differ in
       python tools/riyad.py judge [ID ...]  every change and misprint of the second reading (content/matn/review.json)
                                             weighed against al-Fahl's text; writes .cache/fahl/judged.json
       python tools/riyad.py alone [ID ...]  where the print stands alone: al-Fahl has other words than the text,
                                             and v1 or sunnah.com has al-Fahl's, not the text's; each with a fix
                                             proposed (v1's words where v1 has them); writes .cache/fahl/alone.json

The print is Nuzhat al-Muttaqin, a commentary on Riyad al-Salihin, and its hadith text is meant to be
Riyad al-Salihin's. Where the print is in doubt (a reading v1 or the collections have otherwise, a misprint,
marks the scan can't settle), the hadith text of Riyad al-Salihin itself decides: al-Fahl's critical edition
(Dar Ibn Kathir, 2007), as al-Maktaba al-Shamila serves it (sources.fahl_pages).

The edition is split into its numbered hadith; its numbers are near the book's but not the same, so each of
the book's hadith is matched to the one of al-Fahl's that shares the most pairs of words with it, among
the 40 numbered around it. A phrase of the text is found in al-Fahl's by aligning the two word by word.

al-Fahl's edition vocalizes fewer letters than the print, so a mark it leaves out settles nothing.
"""

import argparse
import difflib
import html
import json
import re
from collections import Counter
from functools import cache

import matn
from arabic import normalize_word
from sources import CACHE, fahl_pages

OUT = CACHE / "fahl"
EDITION = OUT / "hadith.json"
MATCH = OUT / "match.json"
JUDGED = OUT / "judged.json"
ALONE = OUT / "alone.json"
SPELLING = {("الرحمن", "الرحمان"), ("داوود", "داود")}
LONGEST = 6        # words: a longer difference is a gloss, an ordinal block or a narration, left alone
REVIEW = matn.CHECKED / "review.json"
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
WINDOW = 20


def clean(text: str) -> str:
    """Shamela's text as the book's text is written: the salutation as ﷺ, and «إلَاّ» as «إلَّا»."""
    text = re.sub(r"-?\s*صلى الله عليه وسلم\s*-?", " ﷺ ", text)
    text = re.sub(r"ل([ًٌٍَُِْ]?)اّ", r"لّ\1ا", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def parse() -> list[dict]:
    """al-Fahl's numbered hadith: {n, page (Shamela's page), printed (the edition's page), text}. A chapter
    heading («١ - باب …», «كتاب …») ends the hadith before it; Nawawi's words after a hadith stay with it."""
    out, current = [], None
    for k, page in enumerate(fahl_pages(), 1):
        m = re.search(r'class="nass[^"]*"[^>]*data-page-num="(\d+)">(.*?)(?:<hr><p class="hamesh">|</div>)', page, re.S)
        if not m:
            continue
        for p in re.findall(r"<p>(.*?)</p>", m.group(2), re.S):
            p = re.sub(r'<span class="c2">\s*\([٠-٩]+\)\s*</span>', "", p)
            text = clean(html.unescape(re.sub(r"<[^>]+>", "", p)))
            numbered = re.match(r"([٠-٩]+)\s*-\s*(.*)", text, re.S)
            body = numbered.group(2) if numbered else text
            if re.match(r"\[?(باب|كتاب)\s", body):
                current = None
            elif numbered:
                current = {"n": int(numbered.group(1).translate(DIGITS)), "page": k, "printed": int(m.group(1)), "text": body}
                out.append(current)
            elif current and text:
                current["text"] += "\n" + text
    return out


@cache
def edition() -> dict[int, dict]:
    if not EDITION.exists():
        EDITION.write_text(json.dumps(parse(), ensure_ascii=False, indent=0), encoding="utf-8")
    return {h["n"]: h for h in json.loads(EDITION.read_text(encoding="utf-8"))}


def pairs(text: str) -> set[tuple[str, str]]:
    w = [t["n"] for t in matn.tokens(text)]
    return set(zip(w, w[1:]))


@cache
def matches() -> dict[int, int]:
    """The book's hadith number → al-Fahl's, by the most pairs of words shared."""
    if MATCH.exists():
        return {int(k): v for k, v in json.loads(MATCH.read_text(encoding="utf-8")).items()}
    ed = edition()
    theirs = {n: pairs(h["text"]) for n, h in ed.items()}
    out = {}
    for h in matn.hadiths():
        ours = pairs(h["text"])
        near = [n for n in range(h["id"] - WINDOW, h["id"] + WINDOW + 1) if n in theirs]
        best = max(near, key=lambda n: len(ours & theirs[n]) / max(1, min(len(ours), len(theirs[n]))), default=None)
        if best is not None and len(ours & theirs[best]) >= min(3, len(ours) // 2):
            out[h["id"]] = best
    MATCH.write_text(json.dumps(out, indent=0), encoding="utf-8")
    return out


def url(n: int) -> str:
    return f"https://shamela.ws/book/2348/{edition()[n]['page']}"


@cache
def ours() -> dict[int, str]:
    return {h["id"]: h["text"] for h in matn.hadiths()}


def ends(text: str, toks: list[dict]) -> list[int]:
    """Where each token's word ends in the text (the four words of a ﷺ end where the ﷺ does)."""
    return [w["at"] + re.match(r"\S+", text[w["at"]:]).end() for w in toks]


def counterpart(i: int, new: str, old: str) -> dict | None:
    """Where the text of hadith i has `new` (once), the whole words around it (`text`), the same words
    with `old` in its place (`other`), and the words al-Fahl's hadith has there (`fahl`), with a few more
    on each side (`context`). The two are aligned word by word; al-Fahl's words run from the last word
    they share before the place to the first they share after it. None where `new` isn't in the text
    once, or the hadith isn't matched."""
    if i not in matches():
        return None
    text, theirs = ours()[i], edition()[matches()[i]]["text"]
    hits = matn.find(text, new)
    if len(hits) != 1:
        return None
    a, b = hits[0]
    t, f = matn.tokens(text), matn.tokens(theirs)
    te, fe = ends(text, t), ends(theirs, f)
    span = [k for k, w in enumerate(t) if w["at"] < b and te[k] > a]
    if not span:
        return None
    lo, hi = span[0], span[-1] + 1
    start, end = min(t[k]["at"] for k in span), max(te[k] for k in span)
    sm = difflib.SequenceMatcher(None, [w["n"] for w in t], [w["n"] for w in f], autojunk=False)
    same = {i1 + k: j1 + k for i1, j1, size in sm.get_matching_blocks() for k in range(size)}
    before = [k for k in same if k < lo]
    after = [k for k in same if k >= hi]
    j_lo = same[lo] if lo in same else same[max(before)] + 1 if before else 0
    j_hi = same[hi - 1] + 1 if hi - 1 in same else same[min(after)] if after else len(f)
    fahl = theirs[f[j_lo]["at"]:fe[j_hi - 1]] if j_hi > j_lo else ""
    c_lo, c_hi = max(0, j_lo - 3), min(len(f), max(j_hi, j_lo) + 3)
    return {"text": text[start:end], "other": text[start:a] + old + text[b:end], "fahl": fahl,
            "context": theirs[f[c_lo]["at"]:fe[c_hi - 1]] if c_hi > c_lo else ""}


def side(new: str, old: str, fahl: str) -> str:
    """Which of two readings al-Fahl's words have: "new" (the text's), "old", "both" (al-Fahl's words don't
    tell them apart: the letters are the same and it leaves the marks in question out), "neither" (other
    letters), or "against" (the same letters, with marks of its own on letters where the text's differ).
    Where the two differ only in marks, they are compared on the words al-Fahl has with the same letters,
    letter by letter; a letter the text or al-Fahl leaves bare settles nothing."""
    tn, to, tf = matn.tokens(new), matn.tokens(old), matn.tokens(fahl)
    ln, lo, lf = [w["n"] for w in tn], [w["n"] for w in to], [w["n"] for w in tf]
    if ln != lo:
        return "new" if lf == ln else "old" if lf == lo else "neither"
    score = {"new": 0, "old": 0, "against": 0}
    sm = difflib.SequenceMatcher(None, ln, lf, autojunk=False)
    for i1, j1, size in sm.get_matching_blocks():
        for k in range(size):
            mn, mo, mf = matn.marks(tn[i1 + k]["w"]), matn.marks(to[i1 + k]["w"]), matn.marks(tf[j1 + k]["w"])
            if not (len(mn) == len(mo) == len(mf)):
                continue
            for x, y, z in zip(mn, mo, mf):
                if x == y or not x or not z:
                    continue  # the readings agree, the text leaves the letter bare, or al-Fahl does
                agree_n, agree_o = not matn.differ(x, z), bool(y) and not matn.differ(y, z)
                if agree_n and not agree_o:
                    score["new"] += 1
                elif agree_o and not agree_n:
                    score["old"] += 1
                elif not agree_n and not agree_o:
                    score["against"] += 1  # al-Fahl marks the letter otherwise than the text, and the other reading has no mark or another
    if score["new"] and not score["old"]:
        return "new"
    if score["old"] and not score["new"]:
        return "old"
    if score["against"] and not (score["new"] or score["old"]):
        return "against"
    return "both"


def disputes(ids: list[int]) -> list[dict]:
    """The second reading's changes and misprints, as {id, kind, old, new, reason}: `new` is what the text has."""
    out = []
    for key, r in json.loads(REVIEW.read_text(encoding="utf-8")).items():
        i = int(key)
        if ids and i not in ids:
            continue
        for k, f in enumerate(r.get("fix", [])):
            out.append({"id": i, "item": f"r-{i}-f{k}", "kind": f[2], "old": f[0], "new": f[1], "reason": f[3]})
        for k, m in enumerate(r.get("misprint", [])):
            out.append({"id": i, "item": f"r-{i}-m{k}", "kind": "misprint", "old": m[0], "new": m[1], "reason": m[2]})
    return out


def judge(ids: list[int]) -> None:
    rows = []
    for d in disputes(ids):
        c = counterpart(d["id"], d["new"], d["old"])
        d.update(c or {})
        d["verdict"] = side(c["text"], c["other"], c["fahl"]) if c else "not found"
        d["url"] = url(matches()[d["id"]]) if d["id"] in matches() else None
        rows.append(d)
    JUDGED.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    for kind in sorted({r["kind"] for r in rows}):
        of = [r for r in rows if r["kind"] == kind]
        counts = {v: sum(r["verdict"] == v for r in of) for v in ("new", "old", "both", "neither", "against", "not found")}
        print(f"{kind}: {len(of)}  " + ", ".join(f"{v} {n}" for v, n in counts.items() if n))
    print(f"(new: al-Fahl has the text's reading; old: the other one) → {JUDGED}")


def spelling(a: list[str], b: list[str]) -> bool:
    """Words that differ only in spelling (rule 4): «الرحمن» / «الرحمان», or an alif more or less."""
    return len(a) == len(b) and all(x == y or (x, y) in SPELLING or (y, x) in SPELLING
                                    or x.replace("ا", "") == y.replace("ا", "") for x, y in zip(a, b))


def at(seq: list[str], sub: list[str]) -> int:
    """Where `sub` starts in `seq`, or -1."""
    return next((k for k in range(len(seq) - len(sub) + 1) if seq[k:k + len(sub)] == sub), -1) if sub else -1


def alone(ids: list[int]) -> None:
    """The text's words that al-Fahl has otherwise, where v1 or sunnah.com has al-Fahl's words and neither has the
    text's (each checked with two words on either side): the print stands alone against two editions of Riyad
    al-Salihin, so it is the print's slip (rule 8). Spelling, differences of more than LONGEST words, verse
    references and the ﷺ are left out. Each comes with a fix: the words around it in the text, and the same with
    v1's words for the place (al-Fahl's where only sunnah.com has them)."""
    from sources import plain, v1_hadiths
    stexts, sindex = matn.sunnah_index()
    v1 = v1_hadiths()
    old = {h["id"]: h["old_id"] for h in matn.hadiths()}
    rows = []
    for i, text in ours().items():
        if ids and i not in ids:
            continue
        theirs = edition()[matches()[i]]["text"]
        t, f = matn.tokens(text), matn.tokens(theirs)
        te, fe = ends(text, t), ends(theirs, f)
        vtext = plain(v1[old[i]]["matn"]) if old.get(i) in v1 else ""
        vt = matn.tokens(vtext)
        ve = ends(vtext, vt)
        a, b, c = [w["n"] for w in t], [w["n"] for w in f], [w["n"] for w in vt]
        votes = Counter(k for pair in zip(a, a[1:]) for k in sindex.get(pair, ()))
        sw = stexts[votes.most_common(1)[0][0]] if votes else []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag == "equal" or spelling(a[i1:i2], b[j1:j2]) or max(i2 - i1, j2 - j1) > LONGEST:
                continue
            if any(w.get("sal") for w in t[i1:i2] + f[j1:j2]):
                continue
            fahl = theirs[f[j1]["at"]:fe[j2 - 1]] if j2 > j1 else ""
            if "[" in fahl:
                continue
            pre, post = a[max(0, i1 - 2):i1], a[i2:i2 + 2]
            printed, riyad = pre + a[i1:i2] + post, pre + b[j1:j2] + post
            k = at(c, riyad)
            if at(c, printed) >= 0 or at(sw, printed) >= 0 or (k < 0 and at(sw, riyad) < 0):
                continue
            if k >= 0:
                k0, k1 = k + len(pre), k + len(pre) + (j2 - j1)
                words, source = (vtext[vt[k0]["at"]:ve[k1 - 1]] if k1 > k0 else ""), "v1"
            else:
                words, source = fahl, "sunnah.com"
            lo, hi = max(0, i1 - 1), min(len(t), i2 + 1)
            while True:
                frm = text[t[lo]["at"]:te[hi - 1]]
                if len(matn.find(text, frm)) == 1 or (lo == 0 and hi == len(t)):
                    break
                lo, hi = max(0, lo - 1), min(len(t), hi + 1)
            start = t[lo]["at"]
            if i2 > i1:
                to = text[start:t[i1]["at"]] + words + text[te[i2 - 1]:te[hi - 1]]
            elif i1 > 0:
                to = text[start:te[i1 - 1]] + (" " + words if words else "") + text[te[i1 - 1]:te[hi - 1]]
            else:
                to = words + " " + frm
            rows.append({"id": i, "text": text[t[i1]["at"]:te[i2 - 1]] if i2 > i1 else "", "fahl": fahl,
                         "words": words, "source": source, "from": frm, "to": re.sub(r"[ \t]{2,}", " ", to),
                         "page": edition()[matches()[i]]["printed"], "url": url(matches()[i])})
    ALONE.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        print(f"{r['id']:>4}  «{r['text']}» → «{r['words']}» ({r['source']}; al-Fahl «{r['fahl']}»)")
    print(f"{len(rows)} places in {len({r['id'] for r in rows})} hadith → {ALONE}")


def show(ids: list[int]) -> None:
    for i in ids:
        if i not in matches():
            print(f"h. {i}: no hadith of al-Fahl's matched")
            continue
        n = matches()[i]
        print(f"h. {i} = al-Fahl {n} ({url(n)}, his p. {edition()[n]['printed']})")
        t, f = matn.tokens(ours()[i]), matn.tokens(edition()[n]["text"])
        sm = difflib.SequenceMatcher(None, [w["n"] for w in t], [w["n"] for w in f], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            a = " ".join(w["w"] for w in t[i1:i2] if not w.get("sal")) or ("ﷺ" if i2 > i1 else "")
            b = " ".join(w["w"] for w in f[j1:j2] if not w.get("sal")) or ("ﷺ" if j2 > j1 else "")
            if tag != "equal":
                print(f"  {tag:8} text «{a}»  al-Fahl «{b}»")
            else:
                for x, y in zip(t[i1:i2], f[j1:j2]):
                    if not x.get("sal") and matn.conflicts(x["w"], y["w"]):
                        print(f"  marks    text «{x['w']}»  al-Fahl «{y['w']}»")
        print()


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("ids", type=int, nargs="+")
    for name in ("judge", "alone"):
        sub.add_parser(name).add_argument("ids", type=int, nargs="*")
    args = parser.parse_args()
    {"show": show, "judge": judge, "alone": alone}[args.cmd](args.ids)


if __name__ == "__main__":
    main()
