"""Correct the promoter label inside `fig1_circuit.png`.

The circuit schematic came to us as a bitmap from whoever drew it -- there is
no vector source in this repository -- and the label under the lactate
construct reads ``lldPDR``. The operon, and the part, are ``lldPRD`` (lldP,
lldR, lldD); every other document we publish spells it that way, so the figure
contradicts its own legend.

Redrawing the schematic is not ours to do. Repainting four square centimetres
of it is: this script covers the label with the panel's own background and
sets the word again in Liberation Sans, matched to the measured glyph box.

The file as received is kept beside it, unmodified, so the correction can
always be checked against the original or thrown away.

    PYTHONPATH=. .venv/bin/python fix_circuit_label.py

Running it twice is harmless -- the original, not the corrected file, is the
input once the original has been put aside.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FIGURE = ROOT / "outputs" / "figures" / "fig1_circuit.png"
ORIGINAL = ROOT / "outputs" / "figures" / "source" / "fig1_circuit_as_received.png"

WRONG = "lldPDR"
RIGHT = "lldPRD"

#: Measured off the file as received: the ink of the label runs x 364-429,
#: y 409-425, on a panel background of #f2f8fe, in near-black.
INK_BOX = (364, 409, 430, 426)
PATCH_BOX = (358, 403, 438, 431)
BACKGROUND = (242, 248, 254)
INK = (2, 2, 2)

FONT = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")


def _fitted_font(draw: ImageDraw.ImageDraw, text: str) -> ImageFont.FreeTypeFont:
    """The largest size whose ink box is no taller than the original's."""
    target_height = INK_BOX[3] - INK_BOX[1]
    best = ImageFont.truetype(str(FONT), 10)
    for size in range(10, 40):
        candidate = ImageFont.truetype(str(FONT), size)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=candidate)
        if bottom - top > target_height:
            break
        best = candidate
    return best


def main() -> Path:
    ORIGINAL.parent.mkdir(parents=True, exist_ok=True)
    if not ORIGINAL.exists():
        shutil.copy2(FIGURE, ORIGINAL)

    image = Image.open(ORIGINAL).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle(PATCH_BOX, fill=BACKGROUND)

    font = _fitted_font(draw, RIGHT)
    left, top, right, bottom = draw.textbbox((0, 0), RIGHT, font=font)
    # Centre the new ink on the old ink, so the label keeps its place under
    # the construct rather than drifting towards one end of it.
    x = (INK_BOX[0] + INK_BOX[2]) / 2 - (right - left) / 2 - left
    y = INK_BOX[3] - bottom
    draw.text((x, y), RIGHT, font=font, fill=INK)

    image.save(FIGURE)
    return FIGURE


if __name__ == "__main__":
    out = main()
    print(f"wrote {out.relative_to(ROOT)}  ({WRONG} -> {RIGHT})")
