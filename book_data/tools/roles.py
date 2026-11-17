"""Content step 4: the speaker roles of the matn's pieces (docs/matn.md, "Speaker roles").

Usage: python tools/roles.py compare        where the `prophet` role disagrees with al-Fahl's «»; writes .cache/roles.json
       python tools/roles.py show ID ...    a hadith's pieces with their roles, and its disagreements in context
       python tools/roles.py record         turn the disagreements into decisions (content/roles.json), but for KEEP
       python tools/roles.py check          what still disagrees

v1 gives each piece of the matn a role: `narration` (Nawawi's frame: «وعن فلان قال:», the source line, his
explanations), `speech` (the Companion's account, and anyone else's words), `prophet` (the Prophet's words) and
`gloss` (a word Nawawi explains). v1's roles were never checked, and some are wrong: a `prophet` piece that takes in
the narrator's «فقال رسول الله ﷺ:», a Companion's report tagged `prophet` («لعن رسول الله ﷺ آكل الربا»), the
Prophet's words left in a `narration` or `speech` piece.

al-Fahl's edition (tools/riyad.py) puts the Prophet's words in «», and nothing else but the words Nawawi explains
(a short quote after the source line, or after «قوله») and al-Tirmidhi's verdicts («حديث حسن»), which are left
out here. So the text is aligned with al-Fahl's word by word, and every run of words where one says `prophet` and
the other doesn't is a disagreement. Each is settled for al-Fahl, unless KEEP lists it: a run where the text's role
is `gloss`, a Quran verse the Prophet recites in his own words (al-Fahl never puts a verse in «»), or a quote of
al-Fahl's that isn't the Prophet's. A run settled for al-Fahl becomes `prophet`, or, where al-Fahl has no «», the
role of the piece next to it that isn't `prophet` (the narrator's lead-in «قال:» goes to the `speech` before it).

content/roles.json keeps the decisions: hadith number → [[phrase, role, n], …], the n-th occurrence of the phrase
in the text gets the role. tools/matn.py applies them after the text's fixes (settle), so they survive a rebuild.
"""

import argparse
import difflib
import json
import re
from functools import cache

import matn
import riyad
from arabic import normalize_word
from sources import CACHE, ROOT

KEPT = ROOT / "content" / "roles.json"
OUT = CACHE / "roles.json"
ROLES = {"narration", "speech", "prophet", "gloss"}
SOURCE = re.compile(r"(مُ?تَّ?فَ?قٌ?\s*عَ?لَ?يْ?هِ?|رَ?وَ?ا?هُ?\s)")

# Disagreements kept as the text has them: (hadith, the run's words), with the reason.
KEEP: dict[tuple[int, str], str] = {
    (1544, '«بَابِ الْوَفَاءِ بِالْعَهْدِ»'): 'a chapter\'s name, which al-Fahl quotes',
    (265, '«الْيَتِيمِ لَه أَوْ لِغَيرهِ»'): 'the words Nawawi explains: a gloss, set by hand in content/roles.json',
    (44, '«بَاركَ اللَّه'): "the Prophet's words; al-Fahl doesn't quote them here",
    (44, 'فِي ليْلتِكُما».'): "the Prophet's words; al-Fahl doesn't quote them here",
    (78, '«لَا»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (78, '«اللَّه».'): "the Prophet's words; al-Fahl doesn't quote them here",
    (78, '«اللَّهُ» قال:'): "the Prophet's words; al-Fahl doesn't quote them here",
    (78, '«منْ يمنعُكَ مِنِّي'): "the Prophet's words; al-Fahl doesn't quote them here",
    (150, 'الْقَني بِهِ»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (150, 'كيفَ تَصُومُ؟»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (150, 'وَكيْفَ تَخْتِم؟»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (167, 'إِنَّهَا لَا تَصِيدُ صَيْداً»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (317, '«إِنَّ اللهَ تَعَالى خَلَقَ الخَلْقَ حَتَّى إِذَا فَرَغَ مِنْهُمْ قَامَتِ الرَّحِمُ، فَقَالَتْ: هٰذَا مَقَامُ الْعَائِذِ بِكَ مِنَ الْقَطِيعةِ، قالَ: نَعَمْ أَمَا تَرْضينَ أَنْ أَصِلَ مَنْ وَصَلَكِ، وَأَقْطَعَ مَنْ قَطَعَكِ؟ قالَتْ: بَلَى، قالَ فذلِكِ لَكِ»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (317, 'إِنْ شِئتُمْ: {فهَلْ عَسَيْتمْ إِن تَولَّيتُم أَنْ تُفسِدُوا فِي الأَرْضِ وتُقطِّعُوا أَرْحامكُمْ أُولَئِكَ الَّذِينَ لَعنَهُم اللهُ فأَصَمَّهُمْ وَأَعْمَى أَبْصَارَهُمْ}'): "the Prophet's words; al-Fahl doesn't quote them here",
    (317, '«منْ وَصلَكِ، وَصلْتُهُ، ومنْ قَطَعكِ قطعتُهُ»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (323, '«أَحيٌّ والِداكَ؟»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (323, 'ففِيهِما فَجاهِدْ»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (337, '«نَبيٌّ»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (337, '«أَرسلَني اللهُ تَعالَى»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (345, '«اللهُمَّ هَالَةُ بِنْتُ خوَيْلِدٍ».'): "the Prophet's words; al-Fahl doesn't quote them here",
    (369, '«المَرْءُ مَعَ مَنْ أَحَبَّ'): "the Prophet's words; al-Fahl doesn't quote them here",
    (452, 'إِنَّ اللهَ عَزَّ وجَلَّ أَمَرَنِي أَنْ أَقْرَأَ علَيْكَ: { لَمْ يَكُنِ الَّذِينَ كَفَرُوا'): "the Prophet's words; al-Fahl doesn't quote them here",
    (452, 'نَعَمْ'): "the Prophet's words; al-Fahl doesn't quote them here",
    (858, 'أوْلاهُمَا باللهِ تَعالَى'): "the Prophet's words; al-Fahl doesn't quote them here",
    (1137, '«قُومِي فَأَوْتِرِي يَا عَائِشَةُ»'): "the Prophet's words; al-Fahl doesn't quote them here",
    (1716, '«الإِشْراكُ بِاللَّهِ'): "the Prophet's words; al-Fahl doesn't quote them here",
    (1716, 'الْيَمِينُ الْغَمُوسُ'): "the Prophet's words; al-Fahl doesn't quote them here",
    (1853, 'أيُّهَا النَّاسُ إنَّ اللَّه طيِّبٌ لَا يقْبلُ إلاَّ طيِّباً ، وَإنَّ اللَّه أمَر المُؤمِنِينَ بِمَا أمَر بِهِ المُرْسلِينَ ، فَقَال تَعَالى: {يَا أيُّها الرُّسُلُ كُلُوا مِنَ الطَّيِّباتِ واعملوا صَالحاً } وَقَال تَعالَى: { يَا أَيُّهَا الَّذِينَ آمنُوا كُلُوا مِنْ طَيِّبَات مَا رزَقْنَاكُمْ'): "the Prophet's words; al-Fahl doesn't quote them here",
    (1853, 'الرَّجُلَ يُطِيلُ السَّفَر أشْعَثَ أغْبر يمُدُّ يدَيْهِ إلَى السَّمَاءِ: يا رَبِّ يا رَبِّ ، وَمَطْعَمُهُ حَرامٌ ، ومَشْرَبُه حرَامٌ ، ومَلْبسُهُ حرامٌ ، وغُذِيَ بِالْحَرامِ، فَأَنَّى يُسْتَجابُ لِذَلِكَ؟'): "the Prophet's words; al-Fahl doesn't quote them here",
    (1869, '«وَلَمْ يكنْ لهُمْ يوْمَئِذٍ حَبٌّ وَلَوْ كَانَ لهُمْ دَعَا لَهُمْ فيهِ'): "the Prophet's words; al-Fahl doesn't quote them here",
    (1869, '«بركَةُ دعْوةِ إِبراهِيم'): "the Prophet's words; al-Fahl doesn't quote them here",
    (178, 'أَعْطِني الَّذِي تجَهَّزْتَ بِهِ،'): "the Prophet's message, which a man relays",
    (198, '{لُعِنَ الَّذِينَ كَفَرُوا مِنْ بَنِي إِسْرَائِيلَ عَلَى لِسَانِ'): 'a verse the Prophet recites in his own words',
    (198, 'وَعِيسَى ابْنِ مَرْيَمَ ذَلِكَ بِمَا عَصَوْا وَكَانُوا يَعْتَدُونَ كَانُوا لَا يَتَنَاهَوْنَ عَنْ مُنْكَرٍ فَعَلُوهُ لَبِئْسَ مَا كَانُوا يَفْعَلُونَ تَرى كثِيراً مِنْهُمْ يَتَوَلَّوْنَ الَّذينَ كَفَرُوا لَبِئْسَ مَا قَدَّمتْ لَهُمْ أَنْفُسُهُمْ}'): 'a verse the Prophet recites in his own words',
    (198, '{فَاسِقُونَ}'): 'a verse the Prophet recites in his own words',
    (380, '«إِنَّ اللهَ قَدْ أَحَبَّكَ كَمَا أَحْبَبْتَهُ فِيهِ»'): "words of God or an angel inside the Prophet's account",
    (1373, '«مَاذَا عَمِلْتَ فِي الدُّنْيَا؟»'): "words of God or an angel inside the Prophet's account",
    (101, '«حُجِبتْ»'): "another narration's wording of the Prophet's words, after «وفي رواية»",
    (920, '«الميِّتَ»'): "another narration's wording of the Prophet's words, after «وفي رواية»",
    (1460, '«التَّسْبِيحُ أَرْبَعاً وَثَلاَثِينَ»'): "another narration's wording of the Prophet's words, after «وفي رواية»",
    (1460, '«التَّكْبِيرُ أَرْبَعاً وَثَلاَثِينَ»'): "another narration's wording of the Prophet's words, after «وفي رواية»",
    (342, '«وأَقْطَعُ مَنْ قَطَعكِ»'): "the Prophet's words that Nawawi cites",
    (1710, 'هذِهِ طاغِيةُ دوْسٍ'): "the Prophet's words that Nawawi cites",
    (1713, 'الرِّيَاءُ شِرْكٌ'): "the Prophet's words that Nawawi cites",
    (1792, 'أرْجُو أنْ تَكُونَ مِنْهُمْ'): "the Prophet's words that Nawawi cites",
    (1792, 'لَسْتَ مِنْهُمْ'): "the Prophet's words that Nawawi cites",
    (31, '«تَبْكِي عَلَى صَبيٍّ لَهَا»'): "a Companion's words, which al-Fahl quotes",
    (41, '«وهُوَ مُتَوسِّدٌ بُرْدةً وقَدْ لقِينَا مِنَ الْمُشْركِين شِدَّةً»'): "a Companion's words, which al-Fahl quotes",
    (1035, '«إنِّي أراكَ تُحِبُّ الْغَنَم والْبادِيَةَ فإِذا كُنْتَ فِي غَنَمِكَ - أَوْ بادِيَتِكَ - فَأَذَّنْتَ لِلصَّلاَةِ.. فَارْفَعْ صَوْتَكَ بالنِّدَاءِ؛ فَإِنَّهُ لاَ يَسْمَعُ مَدَى صَوْتِ المُؤَذِّنِ جِنٌّ ولاَ إِنْسٌ وَلاَ شَيْءٌ.. إِلاَّ شَهِدَ لَهُ يَوْمَ الْقِيَامَةِ»'): "a Companion's words, which al-Fahl quotes",
    (1605, '«سابِع إخْوةٍ لِي»'): "a Companion's words, which al-Fahl quotes",
    (1665, 'وَأشَارَ إِلَى لِسانِهِ'): "a Companion's words, which al-Fahl quotes",
    (19, 'ﷺ'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (21, 'يُريدُ بذلكَ الدِّيوَانَ'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (476, '«النَّمِرَةُ»'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (631, 'هُوَ طَلاقَةُ الوجهِ ، وبذلُ المَعرُوفِ ، وكَفُّ الأَذَى'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (702, 'إِنَّهُ حديثٌ حسنٌ صحيحٌ'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (852, '(وَبَرَكَاتُهُ)'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (936, 'قالَ البُخارِيُّ: أَصحُّ رِواياتِ هٰذَا الحديثِ رِوايةُ الأَشْهَليِّ ، قالَ البُخارِيُّ: وَأَصَحُّ شيءٍ فِي هٰذَا البابِ حديثُ عوْفِ بنِ مالكٍ.'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (977, 'الغَلِيظُ المُرْتَفِعُ مِنَ الأرْضِ.'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (1147, '«الدَّفُّ»'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (1166, '«قَافِيَةُ الرَّأْسِ»:'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (1204, '«الاسْتِحْدَاد»:'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (1537, 'مُتَّفَقٌ'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (1548, 'مُتَّفَقٌ'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (1599, 'إِذَا كانَتِ الْهِجْرَةُ للهِ تَعَالَى .. فَليْسَ مِنْ هَذَا فِي شَيْءٍ.'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (1695, '«الْبَحْرِ»،'): "a gloss or a later scholar's words, which al-Fahl quotes",
    (1741, 'خبُثَتْ'): "a gloss or a later scholar's words, which al-Fahl quotes",
}


def quotes(text: str) -> list[tuple[int, int]]:
    """The outermost «…» of a text, as (start, end): a quote inside another is part of it."""
    out, depth, start = [], 0, 0
    for k, ch in enumerate(text):
        if ch == "«":
            if depth == 0:
                start = k
            depth += 1
        elif ch == "»" and depth:
            depth -= 1
            if depth == 0:
                out.append((start, k + 1))
    return out


def fahl_quotes(text: str) -> tuple[list[dict], list[bool]]:
    """al-Fahl's words, each True where it is inside «» that hold the Prophet's words (see the module's doc)."""
    toks = matn.tokens(text)
    inside = [False] * len(toks)
    src = SOURCE.search(text)
    src = src.start() if src else len(text)
    for a, b in quotes(text):
        inner = [normalize_word(w) for w in text[a + 1:b - 1].split() if normalize_word(w)]
        last = [normalize_word(w) for w in text[max(0, a - 30):a].split() if normalize_word(w)][-3:]
        narration = any(w in ("روايه", "لمسلم", "للبخاري", "لهما") for w in last)
        if not inner or inner[0] == "حديث" or "قوله" in last or "وقوله" in last \
                or (a > src and len(inner) <= 4 and not narration):
            continue
        for k, t in enumerate(toks):
            if a <= t["at"] < b:
                inside[k] = True
    return toks, inside


@cache
def records() -> dict[int, dict]:
    out = {}
    for f in sorted(matn.CONTENT.glob("*.json")):
        for c in json.loads(f.read_text(encoding="utf-8"))["chapters"]:
            for h in c["hadith"]:
                out[h["id"]] = h
    return out


def role_of(pieces: list[dict], at: int) -> str:
    pos, role = 0, pieces[0]["role"]
    for p in pieces:
        if pos <= at:
            role = p["role"]
        pos += len(p["text"])
    return role


def runs(h: dict) -> list[dict]:
    """The runs of words where the text's `prophet` role and al-Fahl's «» disagree, with their place in the text."""
    text = "".join(p["text"] for p in h["matn"])
    ours = matn.tokens(text)
    ends = riyad.ends(text, ours)
    ft, fq = fahl_quotes(riyad.edition()[riyad.matches()[h["id"]]]["text"])
    sm = difflib.SequenceMatcher(None, [t["n"] for t in ours], [t["n"] for t in ft], autojunk=False)
    out = []
    for block in sm.get_matching_blocks():
        for j in range(block.size):
            i, k = block.a + j, block.b + j
            role = role_of(h["matn"], ours[i]["at"])
            if (role == "prophet") == fq[k]:
                continue
            side = "fahl" if fq[k] else "ours"
            last = out[-1] if out else None
            if last and last["side"] == side and last["_last"] == i - 1 and last["role"] == role:
                last["end"], last["_last"] = ends[i], i
            else:
                out.append({"side": side, "role": role, "start": ours[i]["at"], "end": ends[i], "_last": i})
    for n, r in enumerate(out, 1):
        r["n"] = n
        r["text"] = text[r["start"]:r["end"]]
        del r["_last"]
    return out


def neighbour(pieces: list[dict], start: int, end: int) -> str:
    """The role, not `prophet`, of the piece just before a run, or just after it, or else the nearest one before."""
    text = "".join(p["text"] for p in pieces)
    for at in (start - 1, end):
        while 0 <= at < len(text) and text[at].isspace():
            at += -1 if at < start else 1
        if 0 <= at < len(text) and role_of(pieces, at) not in ("prophet",):
            return role_of(pieces, at)
    for at in range(start - 1, -1, -1):
        if role_of(pieces, at) != "prophet":
            return role_of(pieces, at)
    return "speech"


def nth(text: str, phrase: str, start: int) -> int:
    """Which occurrence of phrase in text starts at start (1-based)."""
    hits = matn.find(text, phrase)
    return next(k for k, (a, _) in enumerate(hits, 1) if a == start)


def compare() -> list[dict]:
    rows = []
    for i, h in records().items():
        r = runs(h)
        if r:
            rows.append({"id": i, "runs": r})
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


def show(ids: list[int]) -> None:
    for i in ids:
        h = records()[i]
        print(f"h. {i}")
        for p in h["matn"]:
            print(f"   {p['role']:9} {' '.join(p['text'].split())}")
        text = "".join(p["text"] for p in h["matn"])
        for r in runs(h):
            keep = KEEP.get((i, " ".join(r["text"].split())))
            print(f"  #{r['n']} {r['side']}:{r['role']} «{' '.join(r['text'].split())}»"
                  f"   ‹{' '.join(text[max(0, r['start'] - 60):r['start']].split())}›" + (f"  KEEP: {keep}" if keep else ""))
        print()


def record() -> None:
    kept = {}
    for i, h in records().items():
        text = "".join(p["text"] for p in h["matn"])
        for r in runs(h):
            if (i, " ".join(r["text"].split())) in KEEP or r["role"] == "gloss":
                continue
            role = "prophet" if r["side"] == "fahl" else neighbour(h["matn"], r["start"], r["end"])
            kept.setdefault(str(i), []).append([r["text"], role, nth(text, r["text"], r["start"])])
    old = json.loads(KEPT.read_text(encoding="utf-8")) if KEPT.exists() else {}
    for k, v in old.items():  # decisions set by hand stay
        kept[k] = v + [d for d in kept.get(k, []) if d not in v]
    KEPT.write_text(json.dumps(dict(sorted(kept.items(), key=lambda kv: int(kv[0]))), ensure_ascii=False, indent=1)
                    + "\n", encoding="utf-8")
    print(f"{sum(len(v) for v in kept.values())} decisions for {len(kept)} hadith in {KEPT.relative_to(ROOT)}")


def set_role(pieces: list[dict], phrase: str, role: str, n: int = 1) -> None:
    """Give the n-th occurrence of phrase in the matn the role: the pieces are cut at its edges, and pieces next to
    each other with the same role are joined."""
    if role not in ROLES:
        raise ValueError(f"no role «{role}»")
    text = "".join(p["text"] for p in pieces)
    hits = matn.find(text, phrase)
    if len(hits) < n:
        raise ValueError(f"«{phrase}» occurs {len(hits)} times, not {n}")
    a, b = hits[n - 1]
    out, pos = [], 0
    for p in pieces:
        s, e = pos, pos + len(p["text"])
        for lo, hi, r in ((s, min(e, a), p["role"]), (max(s, a), min(e, b), role), (max(s, b), e, p["role"])):
            if lo < hi:
                out.append({"role": r, "text": text[lo:hi]})
        pos = e
    joined = []
    for p in out:
        if joined and joined[-1]["role"] == p["role"]:
            joined[-1]["text"] += p["text"]
        else:
            joined.append(dict(p))
    pieces[:] = joined


@cache
def decisions() -> dict[int, list]:
    return {int(k): v for k, v in json.loads(KEPT.read_text(encoding="utf-8")).items()} if KEPT.exists() else {}


def apply(h: dict, pieces: list[dict]) -> None:
    """Apply the hadith's role decisions to its pieces (called by matn.settle after the text's fixes). A piece with no
    letter (a «», a full stop) has no speaker: it joins the piece before it, or the one after if it is the first or
    holds an opening « alone."""
    before = "".join(p["text"] for p in pieces)
    for phrase, role, n in decisions().get(h["id"], []):
        set_role(pieces, phrase, role, n)
    k = 0
    while k < len(pieces):
        if len(pieces) > 1 and not matn.LETTER.search(pieces[k]["text"]):
            opening = pieces[k]["text"].strip().endswith("«") and k + 1 < len(pieces)
            if k > 0 and not opening:
                pieces[k - 1]["text"] += pieces.pop(k)["text"]
            else:
                alone = pieces.pop(k)
                pieces[k]["text"] = alone["text"] + pieces[k]["text"]
            continue
        if k > 0 and pieces[k - 1]["role"] == pieces[k]["role"]:
            pieces[k - 1]["text"] += pieces.pop(k)["text"]
            continue
        k += 1
    if "".join(p["text"] for p in pieces) != before:
        raise ValueError(f"h. {h['id']}: the roles changed the text")


def check() -> None:
    left = compare()
    open_runs = [(r["id"], x["n"]) for r in left for x in r["runs"]
                 if (r["id"], " ".join(x["text"].split())) not in KEEP and x["role"] != "gloss"]
    print(f"disagreements with al-Fahl: {sum(len(r['runs']) for r in left)} in {len(left)} hadith;"
          f" not kept on purpose: {len(open_runs)}" + (f" {open_runs[:20]}" if open_runs else ""))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("compare")
    sub.add_parser("record")
    sub.add_parser("check")
    s = sub.add_parser("show")
    s.add_argument("ids", type=int, nargs="+")
    args = parser.parse_args()
    if args.cmd == "compare":
        rows = compare()
        for r in rows:
            print(r["id"], " || ".join(f"#{x['n']} {x['side']}:{x['role']}: {' '.join(x['text'].split())[:60]}" for x in r["runs"]))
        print(f"{sum(len(r['runs']) for r in rows)} runs in {len(rows)} hadith → {OUT}")
    elif args.cmd == "show":
        show(args.ids)
    else:
        {"record": record, "check": check}[args.cmd]()


if __name__ == "__main__":
    main()
