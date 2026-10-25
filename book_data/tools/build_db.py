"""Build the app's database, ../database/riyad.db, from content/ (../database/README.md has its schema).

Usage: python tools/build_db.py

The app reads only this database. It holds the books, chapters and hadith of content/hadith/: each
hadith's text as pieces with their speaker roles (the text is kept only there: a second copy of it
whole would add a third to the file), and a copy simplified for search (arabic.simplify,
whose test cases in ../database/simplify.json the app's own simplify must pass too), indexed with
SQLite's full-text search. The word meanings and benefits have their tables already, empty until
step 5 transcribes them, and so has the narrators' (step 6). Every v1 hadith id is mapped to the
hadith to open, to carry v1 users' bookmarks over.

The database is made anew each time, and the same content makes the same file. It is committed, so
the app can be built without the content tools: build it again when the app should get the latest
content (each commit of it adds its whole size to the repository).
"""

import hashlib
import json
import sqlite3

from arabic import simplify
from sources import REPO, ROOT, V1_DB

CONTENT = ROOT / "content"
OUT = REPO / "database" / "riyad.db"
CASES = REPO / "database" / "simplify.json"
SCHEMA_VERSION = 1   # raise it whenever the tables change, so the app can tell

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
    old_id INTEGER,
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
CREATE TABLE v1_ids (
    v1_id INTEGER PRIMARY KEY,
    hadith_id INTEGER NOT NULL REFERENCES hadith (id)
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


def v1_targets(first: dict[int, int]) -> dict[int, int]:
    """Every v1 hadith id, with the hadith to open for it: the one with that old_id (the first, where
    a v1 entry holds two printed hadith), or, for v1 454, a cross-reference the book doesn't number
    (content/numbering.json), the hadith of the v1 entry before it."""
    v1 = sqlite3.connect(f"file:{V1_DB}?mode=ro", uri=True)
    out, last = {}, None
    for (i,) in v1.execute("SELECT id FROM hadiths ORDER BY id"):
        last = first.get(i, last)
        if last is None:
            raise SystemExit(f"v1 {i} has no hadith to open")
        out[i] = last
    return out


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
    first, ids = {}, []
    for book_id, f in enumerate(sorted((CONTENT / "hadith").glob("*.json")), 1):
        book = json.loads(f.read_text(encoding="utf-8"))
        db.execute("INSERT INTO books VALUES (?, ?)", (book_id, book["title"]))
        for c in book["chapters"]:
            db.execute("INSERT INTO chapters VALUES (?, ?, ?)", (c["number"], book_id, c["title"]))
            for h in c["hadith"]:
                matn = "".join(p["text"] for p in h["matn"])
                db.execute("INSERT INTO hadith VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (h["id"], book_id, c["number"], h["title"], h["page"], h["old_id"], simplify(matn)))
                db.executemany("INSERT INTO matn_pieces VALUES (?, ?, ?, ?)",
                               [(h["id"], k, p["role"], p["text"]) for k, p in enumerate(h["matn"], 1)])
                db.executemany("INSERT INTO meanings VALUES (?, ?, ?, ?)",
                               [(h["id"], k, m["term"], m["meaning"]) for k, m in enumerate(h["meanings"], 1)])
                db.executemany("INSERT INTO benefits VALUES (?, ?, ?)",
                               [(h["id"], k, b) for k, b in enumerate(h["benefits"], 1)])
                if h["old_id"] is not None:
                    first.setdefault(h["old_id"], h["id"])
                ids.append(h["id"])
    if ids != list(range(1, len(ids) + 1)):
        raise SystemExit("the hadith aren't numbered 1, 2, 3, … in the book's order")
    db.executemany("INSERT INTO v1_ids VALUES (?, ?)", sorted(v1_targets(first).items()))
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
              for t in ("books", "chapters", "hadith", "matn_pieces", "meanings", "benefits", "narrators", "v1_ids")}
    print(f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1e6:.1f} MB, content {info['content']},"
          f" matn checked in {checked} of {len(ids)} hadith")
    print(", ".join(f"{t} {n}" for t, n in counts.items()))


if __name__ == "__main__":
    main()
