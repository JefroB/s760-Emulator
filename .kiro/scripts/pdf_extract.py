import sys, re
from pypdf import PdfReader

path = sys.argv[1]
outpath = sys.argv[2] if len(sys.argv) > 2 else None

reader = PdfReader(path)
print(f"# {path}: {len(reader.pages)} pages")

all_text = []
for i, page in enumerate(reader.pages):
    try:
        t = page.extract_text() or ""
    except Exception as e:
        t = ""
        print(f"  page {i}: extract error {e}")
    all_text.append((i, t))

full = "\n".join(f"\n===== PAGE {i} =====\n{t}" for i, t in all_text)

if outpath:
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(full)
    print(f"# wrote {outpath} ({len(full)} chars)")

# Keyword hunt for CPU / memory info
keywords = [
    r"CPU", r"MPU", r"micro ?processor", r"uPD\w+", r"HD64\w+", r"HD63\w+",
    r"MC680\d+", r"68\d{3}", r"TMP\w+", r"V\d{2,3}\b", r"ROM", r"RAM",
    r"gate array", r"custom", r"IC\d+", r"processor", r"MB\d{5}", r"LH\w+",
]
print("\n# ---- keyword hits ----")
for i, t in all_text:
    for kw in keywords:
        for m in re.finditer(kw, t, re.IGNORECASE):
            s = max(0, m.start() - 40)
            e = min(len(t), m.end() + 40)
            snippet = t[s:e].replace("\n", " ")
            print(f"p{i} [{kw}]: ...{snippet}...")
