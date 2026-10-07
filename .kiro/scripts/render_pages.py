import sys, os
import fitz  # PyMuPDF

pdf = sys.argv[1]
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)

doc = fitz.open(pdf)
print(f"{pdf}: {len(doc)} pages")
for i, page in enumerate(doc):
    # Check for any embedded text
    txt = page.get_text().strip()
    # Render at 200 DPI for OCR
    pix = page.get_pixmap(dpi=200)
    out = os.path.join(outdir, f"page_{i:02d}.png")
    pix.save(out)
    print(f"  page {i:02d}: {pix.width}x{pix.height}px, embedded_text_chars={len(txt)}")
