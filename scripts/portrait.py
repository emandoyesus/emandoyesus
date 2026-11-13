"""Generate a text-only ASCII portrait SVG and plain-text copy from a photo.

Usage: python3 scripts/portrait.py /path/to/photo.png
Requires Pillow: python3 -m pip install Pillow
"""
import argparse
from html import escape
from pathlib import Path

from PIL import Image, ImageOps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('photo', type=Path)
    args = parser.parse_args()
    photo = ImageOps.exif_transpose(Image.open(args.photo)).convert('L')
    photo = ImageOps.fit(photo, (600, 600), method=Image.Resampling.LANCZOS)
    # Characters are roughly twice as tall as they are wide.
    photo = photo.resize((120, 64), Image.Resampling.LANCZOS)
    photo = ImageOps.autocontrast(photo, cutoff=1)
    ramp = ' .,:;ox%#@'
    rows = [''.join(ramp[round((photo.getpixel((x, y)) / 255) ** 0.85 * (len(ramp) - 1))]
                    for x in range(photo.width)) for y in range(photo.height)]
    output = Path(__file__).resolve().parents[1] / 'assets'
    (output / 'portrait.txt').write_text('\n'.join(rows) + '\n')
    lines = '\n'.join(f'<text x="22" y="{65 + y * 6.2:.1f}" textLength="396" lengthAdjust="spacingAndGlyphs">{escape(row)}</text>'
                      for y, row in enumerate(rows))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 490" role="img" aria-labelledby="title desc">
<title id="title">Emandoyesus — ASCII portrait</title>
<desc id="desc">A portrait of Emandoyesus rendered entirely in monospace characters from his photograph.</desc>
<rect x="1" y="1" width="438" height="488" rx="14" fill="#0d1524" stroke="#24384d"/>
<path d="M1 42H439" stroke="#24384d"/>
<circle cx="21" cy="22" r="4" fill="#fb7185"/><circle cx="37" cy="22" r="4" fill="#fbbf24"/><circle cx="53" cy="22" r="4" fill="#34d399"/>
<text x="80" y="26" font-family="monospace" font-size="11" fill="#94a3b8">emandoyesus / portrait.txt</text>
<g font-family="DejaVu Sans Mono,monospace" font-size="6" fill="#67e8f9" xml:space="preserve">
{lines}
</g>
<text x="22" y="475" font-family="monospace" font-size="10" fill="#34d399">$ hello, world_</text>
</svg>
'''
    (output / 'portrait.svg').write_text(svg)


if __name__ == '__main__':
    main()
