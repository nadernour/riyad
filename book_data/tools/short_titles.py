"""Content step 4: the short titles, a phrase of each hadith shown above it (docs/matn.md, "Short titles").

Usage: python tools/short_titles.py propose     the hadith whose title isn't a phrase of their text, each with the
                                                 phrase of the text that best matches v1's title; writes
                                                 .cache/short_titles.json
       python tools/short_titles.py record      take the proposals, with the spans set by hand in SPANS, and keep
                                                 them in content/short_titles.json
       python tools/short_titles.py check       every hadith's title is a phrase of its text

A short title is a phrase of its hadith: tools/build_db.py takes its words from the text, with the text's
spelling and marks (title_text). v1's titles are mostly such phrases, but some are a summary or another wording
(«الرسول» for «رسول الله ﷺ», words dropped or swapped, typos). For those, the phrase of the text that matches
v1's title best is taken: the span of the text, of about the title's length, that shares the most words with it
in order, widened by the title's words missing at either end. content/short_titles.json keeps the titles chosen
(hadith number → phrase); tools/convert_v1.py applies it.
"""

import argparse
import difflib
import json

import matn
from arabic import normalize_word
from build_db import WORD, joined, title_text, words
from sources import CACHE, ROOT

KEPT = ROOT / "content" / "short_titles.json"
OUT = CACHE / "short_titles.json"

# Spans set by hand, where the proposal starts or stops mid-phrase: (first word, last word, where), the words
# normalized (arabic.normalize_word, a leading و or ف ignored). where is "near": the first word nearest the
# proposal; or "first": its first occurrence in the text. The span runs to the first last word after it, or to
# the n-th, where the last word is given as (word, n).
SPANS = {
    78: ("من", "مني", "near"), 83: ("بسم", ("الله", 2), "near"), 86: ("ولا", "برحمه", "near"),
    172: ("حديثه", "السنه", "near"), 228: ("اتقبلون", "صبيانكم", "near"), 375: ("كان", "وماشيا", "near"),
    537: ("ليس", "الناس", "near"), 547: ("ما", "لا", "near"), 555: ("اعطوني", "ردايي", "near"),
    567: ("اكسنيها", "احسنها", "near"), 604: ("مر", "عليهم", "first"), 653: ("كلكم", "رعيته", "near"),
    713: ("رحيما", "اهلنا", "near"), 722: ("كانت", "وطعامه", "near"), 770: ("رايت", "وقاعدا", "near"),
    809: ("نهانا", "والفضه", "near"), 828: ("لا", "الجمعه", "near"), 830: ("لعن", "الحلقه", "first"),
    842: ("الرويا", "الصالحه", "near"), 862: ("مر", "عليهم", "first"), 863: ("تاخذ", "السلق", "near"),
    888: ("فياخذ", "ويصافحه", "near"), 898: ("لم", "الجنه", "near"), 908: ("باسم", "ارقيك", "near"),
    940: ("كان", "هكذا", "near"), 942: ("اذا", "الرجال", "near"), 950: ("مروا", "خيرا", "first"),
    954: ("ذهب", "بحديثك", "first"), 1019: ("اتدري", "اعظم", "near"), 1072: ("ولو", "لاتوهما", "near"),
    1155: ("لا", "الجمعه", "near"), 1183: ("من", "حزبه", "near"), 1199: ("كنا", "وطهوره", "near"),
    1243: ("اذا", "شرب", "near"), 1258: ("كان", "والخميس", "near"), 1280: ("افاحج", "عنه", "near"),
    1290: ("مومن", "الله", "near"), 1360: ("الايمان", "الله", "near"), 1364: ("للعبد", "اجران", "near"),
    1492: ("الظوا", "والاكرام", "near"), 1518: ("ما", "علي", "first"), 1532: ("ايذنوا", "العشيره", "near"),
    1617: ("لعن", "وموكله", "near"), 1728: ("مالك", "تزفزفين", "near"), 1764: ("انهي", "الجمعه", "first"),
    1833: ("كان", "النبي", "near"), 1840: ("يصلون", "فلكم", "near"), 1844: ("لا", "السوق", "first"),
}


def text_words(text: str) -> list[tuple[str, int, int]]:
    """The text's normalized words with their place, as build_db.title_text reads them."""
    return joined([(w, m.start(), m.end()) for m in WORD.finditer(text) for w in words(m.group())])


def proposal(title: str, text: str) -> tuple[int, int, float] | None:
    """The span of the text (first and last word) that matches v1's title best, and the share of its words found."""
    want = [w for w in (normalize_word(x) for x in title.replace("الرسول", "رسول الله").split()) if w]
    seq = [w for w, _, _ in text_words(text)]
    if not want or not seq:
        return None
    best = (0.0, None)
    for size in range(max(1, len(want) - 2), len(want) + 7):
        for k in range(max(1, len(seq) - size + 1)):
            blocks = [b for b in difflib.SequenceMatcher(None, want, seq[k:k + size], autojunk=False).get_matching_blocks()
                      if b.size]
            score = sum(b.size for b in blocks) / len(want) - 0.02 * size
            if blocks and score > best[0]:
                best = (score, (k, blocks))
    if best[1] is None:
        return None
    k, blocks = best[1]
    lead, trail = blocks[0].a, len(want) - (blocks[-1].a + blocks[-1].size)
    first = max(0, k + blocks[0].b - lead)
    last = min(len(seq) - 1, k + blocks[-1].b + blocks[-1].size - 1 + trail)
    return first, last, round(sum(b.size for b in blocks) / len(want), 2)


def same(word: str, want: str) -> bool:
    return word in (want, "و" + want, "ف" + want)


def phrase(text: str, first: int, last: int) -> str:
    have = text_words(text)
    if have[first][0] in ("صلي", "الله", "عليه", "وسلم") and "ﷺ" in text[have[first][1]:have[first][2]]:
        while first <= last and "ﷺ" in text[have[first][1]:have[first][2]]:
            first += 1  # a span that starts on the ﷺ starts after it
    return " ".join(text[have[first][1]:have[last][2]].split())


def hadiths() -> list[dict]:
    return [h for h in matn.hadiths()]


def records() -> dict[int, dict]:
    out = {}
    for f in sorted(matn.CONTENT.glob("*.json")):
        for c in json.loads(f.read_text(encoding="utf-8"))["chapters"]:
            for h in c["hadith"]:
                out[h["id"]] = h
    return out


def propose() -> list[dict]:
    rows = []
    for i, h in records().items():
        text = "".join(p["text"] for p in h["matn"])
        if title_text(h["title"] or "", text) is not None:
            continue
        p = proposal(h["title"] or "", text)
        if p is None:
            rows.append({"id": i, "v1": h["title"], "proposal": None})
            continue
        first, last, share = p
        if i in SPANS:
            start, end, where = SPANS[i]
            have = [w for w, _, _ in text_words(text)]
            starts = [k for k, w in enumerate(have) if same(w, start)]
            if not starts:
                raise SystemExit(f"h. {i}: «{start}» is not in the text")
            first = starts[0] if where == "first" else min(starts, key=lambda k: abs(k - first))
            end, nth = end if isinstance(end, tuple) else (end, 1)
            ends = [k for k in range(first, len(have)) if same(have[k], end)]
            last = ends[nth - 1] if len(ends) >= nth else None
            if last is None:
                raise SystemExit(f"h. {i}: «{end}» is not in the text after «{start}»")
        rows.append({"id": i, "v1": h["title"], "proposal": phrase(text, first, last), "share": share,
                     "by_hand": i in SPANS})
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


def record() -> None:
    kept = {int(k): v for k, v in json.loads(KEPT.read_text(encoding="utf-8")).items()} if KEPT.exists() else {}
    for r in propose():
        if r["proposal"]:
            kept[r["id"]] = r["proposal"]
    KEPT.write_text(json.dumps({str(k): v for k, v in sorted(kept.items())}, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(f"{len(kept)} titles in {KEPT.relative_to(ROOT)}")


def apply(books: dict[int, dict]) -> None:
    """Give the hadith built by tools/convert_v1.py the short titles kept in content/short_titles.json."""
    if not KEPT.exists():
        return
    kept = {int(k): v for k, v in json.loads(KEPT.read_text(encoding="utf-8")).items()}
    for book in books.values():
        for c in book["chapters"]:
            for h in c["hadith"]:
                if h["id"] in kept:
                    h["title"] = kept[h["id"]]


def check() -> None:
    wrong = []
    for i, h in records().items():
        if title_text(h["title"] or "", "".join(p["text"] for p in h["matn"])) is None:
            wrong.append(i)
    print(f"titles that aren't a phrase of their hadith: {len(wrong)}" + (f" {wrong}" if wrong else ""))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["propose", "record", "check"])
    args = parser.parse_args()
    if args.cmd == "propose":
        rows = propose()
        for r in rows:
            print(f"{r['id']:>4} {'*' if r.get('by_hand') else ' '} «{r['v1']}» → «{r['proposal']}»")
        print(f"{len(rows)} → {OUT}")
    else:
        {"record": record, "check": check}[args.cmd]()


if __name__ == "__main__":
    main()
