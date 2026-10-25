"""Read the book's pages with Tesseract, keeping each word's position on the page.

Usage: python tools/ocr.py [FIRST_PAGE LAST_PAGE] [--jobs N]     (default: the hadith pages, 19-1296)

Tesseract reads the vocalized matn poorly, so it isn't a reading of the text: it gives the lines
of each page and their positions, so a word can be found on the scan (tools/matn.py crops the
matn of each hadith from them). The large matn font reads best at 200 dpi. Each page's word table
goes to .cache/ocr/out/pNNNN.tsv; pages already done are skipped.

Tesseract: install it with apt (tesseract-ocr), or let tools/fetch_ocr.sh unpack Debian's
packages into .cache/ocr (run on first use, nothing installed system-wide). The high-accuracy
Arabic model (tessdata_best) is downloaded into .cache/ocr/tessdata on first use, so every run
reads the pages with the same model.
"""

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from concurrent.futures import ProcessPoolExecutor

import pymupdf

from sources import CACHE, ROOT, pdf_path

OCR = CACHE / "ocr"
OUT = OCR / "out"
DPI = 200
HADITH_PAGES = (19, 1296)   # the pages with hadith and commentary (content/hadith/)
LOCAL = OCR / "root" / "usr" / "bin" / "tesseract"   # unpacked by tools/fetch_ocr.sh
MODEL = OCR / "tessdata" / "ara.traineddata"
MODEL_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/ara.traineddata"


def tesseract() -> str:
    """The Tesseract program, fetched on Debian/Ubuntu if missing; the Arabic model is downloaded."""
    if not MODEL.exists():
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading Tesseract's Arabic model to {MODEL.relative_to(ROOT)}")
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    if LOCAL.exists():
        return str(LOCAL)
    if shutil.which("tesseract"):
        return shutil.which("tesseract")
    if sys.platform.startswith("linux") and shutil.which("apt"):
        subprocess.run([str(ROOT / "tools" / "fetch_ocr.sh")], check=True)
        return str(LOCAL)
    raise SystemExit("Tesseract is needed: `sudo apt install tesseract-ocr`")


def read_page(n: int) -> int:
    out = OUT / f"p{n:04d}"
    if out.with_suffix(".tsv").exists():
        return n
    exe = tesseract()
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    if exe == str(LOCAL):
        env["LD_LIBRARY_PATH"] = str(OCR / "root" / "usr" / "lib" / "x86_64-linux-gnu")
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "page.png")
        pymupdf.open(pdf_path())[n - 1].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY).save(png)
        subprocess.run([exe, png, str(out), "--tessdata-dir", str(MODEL.parent), "-l", "ara", "--psm", "4",
                        "-c", "tessedit_create_tsv=1", "-c", "tessedit_create_txt=0"],
                       env=env, check=True, capture_output=True)
    return n


def words(n: int) -> list[dict]:
    """A page's Tesseract words in reading order, with confidence and box (as fractions of the page)."""
    path = OUT / f"p{n:04d}.tsv"
    out = []
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    page = next(r for r in rows if r["level"] == "1")
    width, height = int(page["width"]), int(page["height"])
    for r in rows:
        if r["level"] == "5" and r["text"].strip():
            left, top, w, h = (int(r[k]) for k in ("left", "top", "width", "height"))
            out.append({
                "text": r["text"], "conf": float(r["conf"]),
                "line": (int(r["block_num"]), int(r["par_num"]), int(r["line_num"])),
                "box": (left / width, top / height, (left + w) / width, (top + h) / height),
            })
    return out


def read_pages(pages: range, jobs: int = max(1, (os.cpu_count() or 2) - 2)) -> None:
    """Read the pages not read yet, several at a time."""
    todo = [n for n in pages if not (OUT / f"p{n:04d}.tsv").exists()]
    if not todo:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    tesseract()
    pdf_path()  # downloaded here first, not by every worker at once into the same file
    print(f"Reading {len(todo)} pages with Tesseract ({jobs} at a time)", flush=True)
    with ProcessPoolExecutor(jobs) as pool:
        for k, n in enumerate(pool.map(read_page, todo), 1):
            if k % 50 == 0 or k == len(todo):
                print(f"{k}/{len(todo)} pages (p. {n})", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=int, nargs="?", default=HADITH_PAGES[0])
    parser.add_argument("last", type=int, nargs="?", default=HADITH_PAGES[1])
    parser.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = parser.parse_args()
    read_pages(range(args.first, args.last + 1), args.jobs)


if __name__ == "__main__":
    main()
