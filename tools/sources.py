"""The content pipeline's inputs: the book's scans, their OCR text and the v1 database.

The scans and the OCR text come from the waqfeya-library dataset on Hugging Face (MIT
license), the same files aljam3.com serves. Both are downloaded into .cache/ on first use.
The PDF holds both volumes (1,433 pages). The OCR text separates pages with
PAGE_SEPARATOR, so its page n is PDF page n.
"""

import json
import pathlib
import re
import sqlite3
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
PDF_PATH = CACHE / "book" / "nuzhat.pdf"
OCR_PATH = CACHE / "aljam3" / "nuzhat.txt"
V1_DB = ROOT / "v1" / "app" / "src" / "main" / "assets" / "databases" / "riyad_salheen.db"

DATASET = "https://huggingface.co/datasets/ieasybooks-org/waqfeya-library/resolve/main"
FOLDER = ("2ـ 213.6 (230) المسانيد الأخرى والجوامع/01433ـ نزهة المتقين شرح رياض الصالحين --- "
          "مصطفى سعيد الخن، مصطفى البغا، محي الدين مستو، علي الشربجي، محمد أمين لطفي.PDF")


def _url(kind: str) -> str:
    return f"{DATASET}/{kind}/{urllib.parse.quote(FOLDER)}/{urllib.parse.quote('الكتاب.' + kind)}"


def _ensure(path: pathlib.Path, kind: str) -> pathlib.Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading the book's {kind} to {path.relative_to(ROOT)}")
        urllib.request.urlretrieve(_url(kind), path)
    return path


def pdf_path() -> pathlib.Path:
    return _ensure(PDF_PATH, "pdf")


def ocr_pages() -> list[str]:
    """The OCR text of every PDF page; index 0 is page 1."""
    text = _ensure(OCR_PATH, "txt").read_text(encoding="utf-8").replace("\r\n", "\n")
    return [page.strip("\n") for page in text.split("PAGE_SEPARATOR")]


TAG = re.compile(r"</?p[0-2]>|<bullet>")


def plain(text: str) -> str:
    """v1 text without its formatting tags; each <bullet> becomes "■ "."""
    return TAG.sub(lambda m: "■ " if m.group() == "<bullet>" else "", text)


HEADINGS = {"meanings": re.compile(r"^\s*لغة\s*الحديث"), "benefits": re.compile(r"^\s*(?:و?أفاد|يستفاد)")}


def v1_sections(sharh: str) -> dict:
    """v1's commentary split into word meanings ({term, meaning}) and benefits. A line's
    <p1> run is the word explained; a line with no <bullet> or <p1> continues the item
    before it. Anything before the first heading, or under a heading of another kind
    (e.g. «تنبيه»), goes to `other` for a person to place."""
    out = {"meanings": [], "benefits": [], "other": []}
    section = "other"
    for line in sharh.split("\n"):
        heading = re.match(r"\s*<p0>(.*?)</p0>\s*(?:<p1>)?\s*:?\s*(?:</p1>)?\s*(.*)", line)
        if heading:
            title = heading.group(1)
            section = next((k for k, rx in HEADINGS.items() if rx.match(title)), "other")
            if section == "other":
                out["other"].append(plain(line).strip())
                continue
            line = heading.group(2)
        bullet = "<bullet>" in line
        line = line.replace("<bullet>", "").strip()
        if not line:
            continue
        items = out[section]
        term = re.match(r"\s*<p1>(.*?)</p1>\s*:?\s*(.*)", line) if section == "meanings" else None
        if term:
            name, meaning = term.group(1).strip(), term.group(2).strip()
            if ":" in name and not meaning.strip():  # "<p1>term :</p1>" with the meaning after it
                name, meaning = name.split(":", 1)
            items.append({"term": name.strip(" :"), "meaning": plain(meaning).strip(" :")})
        elif section == "meanings" and ":" in plain(line) and (bullet or not items):
            name, meaning = plain(line).split(":", 1)
            items.append({"term": name.strip(), "meaning": meaning.strip()})
        elif section == "meanings" and items:
            items[-1]["meaning"] += " " + plain(line).strip()
        elif bullet or not items or section != "benefits":
            items.append(plain(line).strip())
        else:
            items[-1] += " " + plain(line).strip()
    return out


SUNNAH_PATH = CACHE / "sunnah" / "riyad_assalihin.json"
SUNNAH_URL = "https://raw.githubusercontent.com/AhmedBaset/hadith-json/main/db/by_book/other_books/riyad_assalihin.json"
COLLECTIONS_DIR = CACHE / "hadith-api"
COLLECTIONS_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-{}.json"
COLLECTIONS = ("bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah", "malik")


def _download(path: pathlib.Path, url: str, what: str) -> pathlib.Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {what} to {path.relative_to(ROOT)}")
        urllib.request.urlretrieve(url, path)
    return path


def sunnah_riyad() -> list[str]:
    """sunnah.com's Riyad al-Salihin (through hadith-json): the Arabic text of each of its 1,896
    hadith. Its order and numbering don't follow the book's, and it has almost no tashkeel."""
    data = json.loads(_download(SUNNAH_PATH, SUNNAH_URL, "sunnah.com's Riyad al-Salihin").read_text(encoding="utf-8"))
    return [h["arabic"] for h in data["hadiths"]]


def collections() -> dict[str, list[str]]:
    """The vocalized text of each hadith in the six books and the Muwatta (hadith-api), by collection."""
    out = {}
    for name in COLLECTIONS:
        path = _download(COLLECTIONS_DIR / f"ara-{name}.json", COLLECTIONS_URL.format(name), f"hadith-api's {name}")
        out[name] = [h["text"] for h in json.loads(path.read_text(encoding="utf-8"))["hadiths"]]
    return out


def v1_hadiths() -> dict[int, dict]:
    """The v1 database's hadith by id, with their book and chapter titles. `matn` and `sharh`
    keep v1's tags (see README)."""
    db = sqlite3.connect(f"file:{V1_DB}?mode=ro", uri=True)
    rows = db.execute("""
        SELECT h.id, h.book_id, b.title, h.door_id, d.title, h.title, h.hadith, h.sharh
        FROM hadiths h JOIN books b ON b.id = h.book_id JOIN doors d ON d.id = h.door_id
        ORDER BY h.id""")
    keys = ("id", "book_id", "book", "door_id", "door", "title", "matn", "sharh")
    return {row[0]: dict(zip(keys, row)) for row in rows}
