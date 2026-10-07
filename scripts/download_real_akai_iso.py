"""
scripts/download_real_akai_iso.py — Downloads and verifies a real Akai S1000 CD-ROM ISO volume
from archive.org (Invision Interactive 40 Oz Phat Slammin Hip Hop S1000 library).
"""
import os
import sys
import urllib.request
import urllib.parse

AKAI_URL = "https://archive.org/download/invision-interactive-40-oz-phat-slammin-hip-hop/Invision%20Interactive%20-%2040%20Oz%20Phat%20Slammin%20Hip%20Hop/Invision%20Interactive%20-%2040%20Oz%20Phat%20Slammin%20Hip%20Hop.iso"

akai_charmap = {}
for i in range(10): akai_charmap[i] = chr(ord('0') + i)
for i in range(26): akai_charmap[10 + i] = chr(ord('A') + i)
akai_charmap[36] = ' '
akai_charmap[37] = '#'
akai_charmap[38] = '+'
akai_charmap[39] = '-'
akai_charmap[40] = '.'

def decode_akai_name(raw_bytes):
    chars = []
    for b in raw_bytes:
        if b in akai_charmap: chars.append(akai_charmap[b])
        elif 32 <= b <= 126: chars.append(chr(b))
        else: chars.append('?')
    return ''.join(chars).strip()

def download_real_akai_iso(target_path="roms/SCSI/akai.iso", num_mb=8):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    num_bytes = num_mb * 1024 * 1024
    print(f"Downloading {num_mb}MB of real Akai S1000 CD-ROM ISO from archive.org to {target_path}...")
    
    req = urllib.request.Request(AKAI_URL, headers={"User-Agent": "Mozilla/5.0", "Range": f"bytes=0-{num_bytes - 1}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    
    with open(target_path, "wb") as f:
        f.write(data)
    print(f"Saved {len(data)} bytes to {target_path}")

    # Verify directory entries at Sector 12 (0x6000)
    if len(data) >= 0x8000:
        sec12 = data[0x6000:0x6800]
        print("\nReal Akai S1000 Directory Records in ISO:")
        for e in range(0, min(512, len(sec12)), 24):
            entry = sec12[e:e+24]
            name = decode_akai_name(entry[:12])
            tag = chr(entry[12]) if 32 <= entry[12] <= 126 else f"0x{entry[12]:02x}"
            cluster = entry[16] | (entry[17] << 8)
            print(f"  [{e//24:02d}] Tag={tag} Name='{name:<14}' Cluster={cluster}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "roms/SCSI/akai.iso"
    download_real_akai_iso(out, num_mb=8)
