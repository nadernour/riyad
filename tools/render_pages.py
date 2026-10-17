"""Render PDF pages of the book to PNG images.

Usage: python tools/render_pages.py FIRST_PAGE [LAST_PAGE] [--dpi 220] [--strips N]

Page numbers are PDF pages (1-based). The PDF holds both volumes, so they don't match the
printed page numbers. Images are written to .cache/pages/pNNNN.png, or with --strips to
pNNNN-K.png: N overlapping horizontal strips, for reading small marks at a higher dpi.
The scans are about 320 dpi, so rendering above that shows nothing more.
"""

import argparse

import pymupdf

from sources import CACHE, ROOT, pdf_path

PAGES_DIR = CACHE / "pages"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=int)
    parser.add_argument("last", type=int, nargs="?")
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument("--strips", type=int, default=1)
    args = parser.parse_args()

    doc = pymupdf.open(pdf_path())
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for n in range(args.first, (args.last or args.first) + 1):
        page = doc[n - 1]
        if args.strips == 1:
            out = PAGES_DIR / f"p{n:04d}.png"
            page.get_pixmap(dpi=args.dpi).save(out)
            print(out.relative_to(ROOT))
            continue
        r = page.rect
        height = r.height / args.strips
        overlap = height * 0.08  # so a line cut at a strip edge appears whole in one strip
        for k in range(args.strips):
            clip = pymupdf.Rect(r.x0, max(r.y0, r.y0 + k * height - overlap),
                                r.x1, min(r.y1, r.y0 + (k + 1) * height + overlap))
            out = PAGES_DIR / f"p{n:04d}-{k + 1}.png"
            page.get_pixmap(dpi=args.dpi, clip=clip).save(out)
            print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
