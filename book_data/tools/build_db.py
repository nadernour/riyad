"""Build the app's database, ../database/riyad.db, from content/ (../database/README.md has its schema).

Usage: python tools/build_db.py

The app reads only this database. It holds the books, chapters and hadith of content/hadith/: each
hadith's text as pieces with their speaker roles (the text is kept only there: a second copy of it
whole would add a third to the file), and a copy simplified for search (arabic.simplify,
whose test cases in ../database/simplify.json the app's own simplify must pass too), indexed with
SQLite's full-text search. The word meanings and benefits have their tables already, empty until
step 5 transcribes them, and so has the narrators' (step 6). A hadith's short title is a phrase of
its text, taken from the text with its spelling and marks (title_text).

The database is made anew each time, and the same content makes the same file. It is committed, so
the app can be built without the content tools: build it again when the app should get the latest
content (each commit of it adds its whole size to the repository).
"""

import hashlib
import json
import re
import sqlite3

from arabic import simplify, words
from sources import REPO, ROOT

CONTENT = ROOT / "content"
OUT = REPO / "database" / "riyad.db"
CASES = REPO / "database" / "simplify.json"
SCHEMA_VERSION = 2   # raise it whenever the tables change, so the app can tell
WORD = re.compile(r"[ء-يٱً-ْٰ]+|ﷺ")  # a word of the text, its marks included, without the punctuation around it

SCHEMA = f"""
PRAGMA user_version = {SCHEMA_VERSION};
CREATE TABLE info (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);
CREATE TABLE chapters (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books (id),
    title TEXT NOT NULL
);
CREATE INDEX chapters_book ON chapters (book_id);
CREATE TABLE hadith (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books (id),
    chapter_id INTEGER NOT NULL REFERENCES chapters (id),
    title TEXT NOT NULL,
    page INTEGER NOT NULL,
    search_text TEXT NOT NULL
);
CREATE INDEX hadith_book ON hadith (book_id);
CREATE INDEX hadith_chapter ON hadith (chapter_id);
CREATE TABLE matn_pieces (
    hadith_id INTEGER NOT NULL REFERENCES hadith (id),
    seq INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('narration', 'prophet', 'speech', 'gloss')),
    text TEXT NOT NULL,
    PRIMARY KEY (hadith_id, seq)
) WITHOUT ROWID;
CREATE TABLE meanings (
    hadith_id INTEGER NOT NULL REFERENCES hadith (id),
    seq INTEGER NOT NULL,
    term TEXT NOT NULL,
    meaning TEXT NOT NULL,
    PRIMARY KEY (hadith_id, seq)
) WITHOUT ROWID;
CREATE TABLE benefits (
    hadith_id INTEGER NOT NULL REFERENCES hadith (id),
    seq INTEGER NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (hadith_id, seq)
) WITHOUT ROWID;
CREATE TABLE narrators (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    biography TEXT NOT NULL,
    page INTEGER NOT NULL
);
CREATE VIRTUAL TABLE hadith_search USING fts5 (search_text, content = 'hadith', content_rowid = 'id',
                                               tokenize = 'trigram');
"""


def check_simplify() -> None:
    """simplify() must pass the test cases the app's own simplify is held to."""
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    wrong = [f"«{text}» gives «{simplify(text)}», not «{want}»" for text, want in cases if simplify(text) != want]
    if wrong:
        raise SystemExit(f"simplify() fails {CASES.relative_to(REPO)}: " + "; ".join(wrong))


def joined(found: list[tuple[str, int, int]]) -> list[tuple[str, int, int]]:
    """Normalized words with their place in the text, a lone «و» or «ف» joined to the word after it,
    because the titles taken from v1 often space it off («نعم،و لك أجر»)."""
    out = []
    for w, start, end in found:
        if out and out[-1][0] in ("و", "ف"):
            out[-1] = (out[-1][0] + w, out[-1][1], end)
        else:
            out.append((w, start, end))
    return out


def title_text(title: str, matn: str) -> str | None:
    """The short title as the hadith's text prints it. The titles come from v1, and most are a phrase
    of the hadith («إنما الأعمال بالنيات»), so the phrase is taken from the text, with its spelling and
    marks. None when the title isn't a phrase of the text."""
    want = [w for w, _, _ in joined([(w, 0, 0) for m in WORD.finditer(title) for w in words(m.group())])]
    have = joined([(w, m.start(), m.end()) for m in WORD.finditer(matn) for w in words(m.group())])
    seq = [w for w, _, _ in have]
    for k in range(len(have) - len(want) + 1 if want else 0):
        if seq[k:k + len(want)] == want:
            return " ".join(matn[have[k][1]:have[k + len(want) - 1][2]].split())
    return None


def content_version() -> str:
    """A short hash of the content the database is built from."""
    digest = hashlib.sha256()
    for f in sorted((CONTENT / "hadith").glob("*.json")):
        digest.update(f.read_bytes())
    return digest.hexdigest()[:12]


def main() -> None:
    check_simplify()
    OUT.parent.mkdir(exist_ok=True)
    tmp = OUT.with_name(OUT.name + ".tmp")
    tmp.unlink(missing_ok=True)
    db = sqlite3.connect(tmp)
    db.executescript(SCHEMA)
    ids, from_v1 = [], 0
    for book_id, f in enumerate(sorted((CONTENT / "hadith").glob("*.json")), 1):
        book = json.loads(f.read_text(encoding="utf-8"))
        db.execute("INSERT INTO books VALUES (?, ?)", (book_id, book["title"]))
        for c in book["chapters"]:
            db.execute("INSERT INTO chapters VALUES (?, ?, ?)", (c["number"], book_id, c["title"]))
            for h in c["hadith"]:
                matn = "".join(p["text"] for p in h["matn"])
                title = title_text(h["title"], matn)
                from_v1 += title is None
                db.execute("INSERT INTO hadith VALUES (?, ?, ?, ?, ?, ?)",
                           (h["id"], book_id, c["number"], title or h["title"], h["page"], simplify(matn)))
                db.executemany("INSERT INTO matn_pieces VALUES (?, ?, ?, ?)",
                               [(h["id"], k, p["role"], p["text"]) for k, p in enumerate(h["matn"], 1)])
                db.executemany("INSERT INTO meanings VALUES (?, ?, ?, ?)",
                               [(h["id"], k, m["term"], m["meaning"]) for k, m in enumerate(h["meanings"], 1)])
                db.executemany("INSERT INTO benefits VALUES (?, ?, ?)",
                               [(h["id"], k, b) for k, b in enumerate(h["benefits"], 1)])
                ids.append(h["id"])
    if ids != list(range(1, len(ids) + 1)):
        raise SystemExit("the hadith aren't numbered 1, 2, 3, … in the book's order")
    db.execute("INSERT INTO hadith_search (hadith_search) VALUES ('rebuild')")
    checked = sum(len(json.loads(f.read_text(encoding="utf-8"))) for f in (CONTENT / "matn").glob("[0-9][0-9].json"))
    info = {"schema": SCHEMA_VERSION, "content": content_version(), "hadith": len(ids), "matn_checked": checked}
    db.executemany("INSERT INTO info VALUES (?, ?)", [(k, str(v)) for k, v in info.items()])
    broken = db.execute("PRAGMA foreign_key_check").fetchall()
    if broken:
        raise SystemExit(f"rows that refer to nothing: {broken[:5]}")
    db.commit()
    db.execute("VACUUM")
    db.close()
    tmp.replace(OUT)
    counts = {t: sqlite3.connect(OUT).execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ("books", "chapters", "hadith", "matn_pieces", "meanings", "benefits", "narrators")}
    print(f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1e6:.1f} MB, content {info['content']},"
          f" matn checked in {checked} of {len(ids)} hadith")
    print(", ".join(f"{t} {n}" for t, n in counts.items()))
    print(f"short titles that aren't a phrase of their hadith, so still v1's: {from_v1}")


if __name__ == "__main__":
    main()
