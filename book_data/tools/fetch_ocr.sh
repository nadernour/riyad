#!/bin/sh
# Unpack Tesseract into .cache/ocr on Debian or Ubuntu without installing anything system-wide:
# Debian's packages are downloaded (no root needed) and unpacked locally. tools/ocr.py runs this
# when it finds no Tesseract; it downloads the Arabic model itself.
# Taken from the owner's azkar project.
set -e
cd "$(dirname "$0")/.."
mkdir -p .cache/ocr/debs
cd .cache/ocr/debs
apt download tesseract-ocr libtesseract5 libleptonica6
for f in *.deb; do dpkg-deb -x "$f" ../root; done
LD_LIBRARY_PATH="$PWD/../root/usr/lib/x86_64-linux-gnu" ../root/usr/bin/tesseract --version | head -1
