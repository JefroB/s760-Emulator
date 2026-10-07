"""
ocr_pages.py - OCR rendered PDF page images and dump text.

Usage:
  python ocr_pages.py <image_dir> <out_dir> [page_start] [page_end]

Reads page_NN.png files from <image_dir>, OCRs each with easyocr, writes
<out_dir>/page_NN.txt, and prints a keyword hunt for CPU/memory-map terms.
Requires: pip install easyocr  (pulls torch; CPU inference is slow but works).
"""
import sys, os, glob, re

img_dir = sys.argv[1]
out_dir = sys.argv[2]
p_start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
p_end = int(sys.argv[4]) if len(sys.argv) > 4 else 9999
os.makedirs(out_dir, exist_ok=True)

import easyocr
reader = easyocr.Reader(['en'], gpu=False)

KEYWORDS = [
    r"80C196", r"MCS", r"CPU", r"ROM", r"RAM", r"DRAM", r"SRAM", r"EPROM",
    r"address", r"memory", r"map", r"[0-9A-Fa-f]{4,5}H\b", r"0x[0-9A-Fa-f]+",
    r"gate array", r"boot", r"reset", r"vector", r"bank", r"decode",
    r"[0-9A-Fa-f]{2,}\s*[-~]\s*[0-9A-Fa-f]{2,}",  # address ranges
]

imgs = sorted(glob.glob(os.path.join(img_dir, "page_*.png")))
for img in imgs:
    m = re.search(r"page_(\d+)\.png", img)
    n = int(m.group(1)) if m else -1
    if n < p_start or n > p_end:
        continue
    print(f"=== OCR page {n:02d} ({os.path.basename(img)}) ===", flush=True)
    try:
        result = reader.readtext(img, detail=0, paragraph=True)
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
        continue
    text = "\n".join(result)
    outpath = os.path.join(out_dir, f"page_{n:02d}.txt")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(text)
    hits = []
    for kw in KEYWORDS:
        for mm in re.finditer(kw, text, re.IGNORECASE):
            s = max(0, mm.start() - 30); e = min(len(text), mm.end() + 30)
            hits.append(f"    [{kw}] ...{text[s:e]}...".replace("\n", " "))
    print(f"  wrote {outpath} ({len(text)} chars, {len(hits)} keyword hits)", flush=True)
    for h in hits[:20]:
        print(h, flush=True)

print("=== OCR COMPLETE ===", flush=True)
