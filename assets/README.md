# Application icon

`s760-studio.png` is the original transparent artwork, generated with the built-in
image-generation tool. `s760-studio.ico` contains 16, 24, 32, 48, 64, 128 and 256
pixel versions for Windows Explorer, the taskbar and the standalone window.
The standalone build embeds the ICO in the executable. WebView2 extracts that
embedded icon for its Windows window.

Regenerate the ICO from the PNG with Pillow:

```python
from PIL import Image

Image.open('assets/s760-studio.png').convert('RGBA').save(
    'assets/s760-studio.ico',
    sizes=[(size, size) for size in (16, 24, 32, 48, 64, 128, 256)],
)
```

Generation prompt:

> Use case: logo-brand. Asset type: Windows application icon. Create a crisp bold
> 3.5-inch floppy disk icon for the S-760 sampler emulator. Square upright dark
> charcoal floppy with chamfered top right corner, silver metal shutter at top,
> large ivory label filling the middle/lower half. Exact label text on two centered
> lines: "S" then "760", in very heavy condensed black sans-serif lettering, huge
> and readable at small icon sizes. Together these form the S-760 mark. Small blue
> accent stripe across the top of the paper label, inspired by vintage sampler
> labeling. Front view, clean simplified dimensional illustration, only broad
> shapes, sharp silhouette, strong contrast. The floppy fills 90% of a square
> canvas. No rack hardware, no knobs, no drum pads, no background tile, no extra
> text, no watermark, no cast shadow outside the disk. Truly transparent background.
