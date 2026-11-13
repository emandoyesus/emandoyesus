"""Generate a text-only ASCII portrait SVG and plain-text copy from a photo.

Usage: python3 scripts/portrait.py /path/to/photo.png
Requires Pillow: python3 -m pip install Pillow
"""
import argparse
from itertools import groupby
from html import escape
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps


COLUMNS = 220
ROWS = 120
PORTRAIT_SIZE = 396
# A larger grid retains curl highlights and the separation between the lips.
# Match the monospace advance to the cell width to keep the photo square.
CELL_WIDTH = PORTRAIT_SIZE / COLUMNS
CELL_HEIGHT = PORTRAIT_SIZE / ROWS
FONT_SIZE = CELL_WIDTH / 0.602
RAMP = ' .,:;ox%#@'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('photo', type=Path)
    args = parser.parse_args()
    with Image.open(args.photo) as source:
        photo = ImageOps.exif_transpose(source).convert('L')
    # Crop to a square before compensating for the tall character cells.
    side = min(photo.size)
    photo = ImageOps.fit(photo, (side, side), method=Image.Resampling.LANCZOS)
    photo = ImageOps.autocontrast(photo, cutoff=0.2)
    # Lift shadows before sampling so fine curl highlights survive averaging.
    photo = photo.point([round((v / 255) ** 0.50 * 255) for v in range(256)])
    # Enhance real small-scale detail before downsampling, especially dark curls.
    photo = photo.filter(ImageFilter.UnsharpMask(radius=5, percent=170, threshold=2))
    photo = photo.resize((COLUMNS, ROWS), Image.Resampling.LANCZOS)
    photo = photo.filter(ImageFilter.UnsharpMask(radius=1, percent=70, threshold=2))
    rows = []
    shaded_rows = []
    for y in range(ROWS):
        row = []
        shades = []
        for x in range(COLUMNS):
            tone = photo.getpixel((x, y)) / 255
            # Retain low-light texture rather than rounding the hair to blanks.
            char = RAMP[max(1, round(tone * (len(RAMP) - 1)))]
            row.append(char)
            shade = round(tone * 31)
            shades.append((shade, char))
        rows.append(''.join(row))
        shaded_rows.append(shades)

    output = Path(__file__).resolve().parents[1] / 'assets'
    (output / 'portrait.txt').write_text('\n'.join(rows) + '\n')
    lines = []
    for y, cells in enumerate(shaded_rows):
        spans = []
        for shade, run in groupby(cells, key=lambda cell: cell[0]):
            # Cyan shades supplement character density for smoother lips.
            strength = 0.65 + 0.35 * shade / 31
            color = '#' + ''.join(f'{round(a + (b - a) * strength):02x}'
                                  for a, b in zip((13, 21, 36), (103, 232, 249)))
            characters = escape(''.join(char for _, char in run))
            spans.append(f'<tspan fill="{color}">{characters}</tspan>')
        lines.append(f'<text x="22" y="{60 + y * CELL_HEIGHT + FONT_SIZE:.2f}">{"".join(spans)}</text>')
    portrait = '\n'.join(lines)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 490" role="img" aria-labelledby="title desc">
<title id="title">Emandoyesus — ASCII portrait</title>
<desc id="desc">A portrait of Emandoyesus rendered entirely in {COLUMNS} by {ROWS} shaded monospace characters sampled from his photograph.</desc>
<rect x="1" y="1" width="438" height="488" rx="14" fill="#0d1524" stroke="#24384d"/>
<path d="M1 42H439" stroke="#24384d"/>
<circle cx="21" cy="22" r="4" fill="#fb7185"/><circle cx="37" cy="22" r="4" fill="#fbbf24"/><circle cx="53" cy="22" r="4" fill="#34d399"/>
<text x="80" y="26" font-family="monospace" font-size="11" fill="#94a3b8">emandoyesus / portrait.txt</text>
<g font-family="DejaVu Sans Mono,monospace" font-size="{FONT_SIZE:.4f}" style="font-variant-ligatures:none" xml:space="preserve">
{portrait}
</g>
<text x="22" y="475" font-family="monospace" font-size="10" fill="#34d399">$ hello, world_</text>
</svg>
'''
    (output / 'portrait.svg').write_text(svg)


if __name__ == '__main__':
    main()
