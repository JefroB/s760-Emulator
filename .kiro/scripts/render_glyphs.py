"""
render_glyphs.py - render a region of the image as bitmap glyphs (ASCII art) to
visually identify the monitor's tile/font data.

Usage:
  python render_glyphs.py <off_hex> [cell_bytes=8] [count=16] [--lsb] [--wide]
  <cell_bytes>: bytes per glyph (8 for 8x8, 16 for 8x16, etc.)
  --lsb: LSB-first bit order (default MSB-first)
  --wide: treat cell as 16px wide (2 bytes/row)

Renders each glyph as '#'/'.' so letterforms are visible by eye.
"""
import sys
IMG="S760224.IMG"; data=open(IMG,'rb').read()
off=int(sys.argv[1],16)
cell=int(sys.argv[2]) if len(sys.argv)>2 and not sys.argv[2].startswith('--') else 8
count=int(sys.argv[3]) if len(sys.argv)>3 and not sys.argv[3].startswith('--') else 16
msb = '--lsb' not in sys.argv
wide = '--wide' in sys.argv
rowbytes = 2 if wide else 1
rows = cell//rowbytes

def render(cellbytes):
    for g in range(count):
        c=data[off+g*cell:off+(g+1)*cell]
        print(f"glyph {g} @0x{off+g*cell:06X}:")
        for r in range(rows):
            rowval=0
            for rb in range(rowbytes):
                rowval=(rowval<<8)|c[r*rowbytes+rb]
            width=8*rowbytes
            bits=range(width-1,-1,-1) if msb else range(0,width)
            line=''.join('#' if (rowval>>b)&1 else '.' for b in bits)
            print("  "+line)
        print()

print(f"=== 0x{off:06X} cell={cell}B rows={rows} width={8*rowbytes} {'MSB' if msb else 'LSB'} ===")
render(cell)
