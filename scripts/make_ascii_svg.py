"""Turns avatar.png into assets/ascii.svg: an ASCII portrait typed row by row.

Run locally once per photo (needs Pillow + numpy). The avatar is already a cutout:
the person is opaque and the card behind is translucent, so alpha is the mask.
"""

import os

import numpy as np
from PIL import Image, ImageFilter

from common import ACCENT, FG, FONT, PANEL_H, PORTRAIT_W, ROOT, STATIC, esc, panel, write

COLS = 100
PAD = 16
# Sparse -> dense. On a dark panel a dense glyph reads as a bright pixel.
RAMP = " .'`,:;-~+=*ixtfLCG08@"
# >1 pushes mid-tones toward sparse glyphs, which carves out the face and the suit.
GAMMA = 1.5

ROW_DUR = 0.42
ROW_STAGGER = 0.035


def load_mask_and_luma(path):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im)
    mask = a[..., 3] >= 200
    ys, xs = np.nonzero(mask)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    im = im.crop(box)
    mask = mask[box[1]:box[3], box[0]:box[2]]
    # Unsharp mask stands in for CLAHE: it lifts local contrast (eyes, collar, tie).
    sharp = im.convert("L").filter(ImageFilter.UnsharpMask(radius=6, percent=160, threshold=2))
    luma = np.asarray(sharp, dtype=np.float32)

    # Equalize only the person's pixels, so the dark suit and the shirt both get range.
    vals = np.sort(luma[mask])
    luma = np.searchsorted(vals, luma) / len(vals)
    luma[~mask] = 0
    return Image.fromarray((luma * 255).astype(np.uint8)), Image.fromarray(mask.astype(np.uint8) * 255)


def fit(img, w, h):
    """Contain img in a w x h canvas, centered horizontally, pinned to the bottom."""
    scale = min(w / img.width, h / img.height)
    nw, nh = max(1, round(img.width * scale)), max(1, round(img.height * scale))
    out = Image.new("L", (w, h), 0)
    out.paste(img.resize((nw, nh), Image.Resampling.BOX), ((w - nw) // 2, h - nh))
    return out


def main():
    cw = (PORTRAIT_W - 2 * PAD) / COLS
    lh = cw * 1.9
    rows = int((PANEL_H - 2 * PAD) / lh)
    lh = (PANEL_H - 2 * PAD) / rows

    luma, mask = load_mask_and_luma(os.path.join(ROOT, "avatar.png"))
    # Work at a fine pixel grid with the cell aspect, then average down to one value per cell.
    gw = COLS * 4
    gh_px = round(gw * (lh / cw) * rows / COLS)
    luma = fit(luma, gw, gh_px).resize((COLS, rows), Image.Resampling.BOX)
    mask = fit(mask, gw, gh_px).resize((COLS, rows), Image.Resampling.BOX)
    luma = np.asarray(luma, dtype=np.float32) / 255
    mask = np.asarray(mask, dtype=np.float32) / 255

    lines = []
    for r in range(rows):
        chars = []
        for c in range(COLS):
            if mask[r, c] < 0.5:
                chars.append(" ")
                continue
            v = luma[r, c] ** GAMMA
            chars.append(RAMP[min(len(RAMP) - 1, 1 + int(v * (len(RAMP) - 1)))])
        lines.append("".join(chars))

    defs, body = [], []
    t = 0.2
    for r, line in enumerate(lines):
        if not line.strip():
            continue
        y = PAD + (r + 1) * lh - lh * 0.22
        top = PAD + r * lh
        # Renderers drop edge whitespace, so start each row at its first glyph and keep
        # the gaps inside it as no-break spaces; textLength then pins it to the grid.
        ink = line.strip()
        x0 = PAD + (len(line) - len(line.lstrip())) * cw
        ink_w = len(ink) * cw
        text = (
            f'<text x="{x0:.2f}" y="{y:.2f}" textLength="{ink_w:.2f}" lengthAdjust="spacingAndGlyphs"'
            f'{{clip}}>{esc(ink).replace(" ", chr(0xA0))}</text>'
        )
        if STATIC:
            body.append(text.format(clip=""))
            continue
        begin = f"{t:.3f}s"
        defs.append(
            f'<clipPath id="r{r}"><rect x="{x0:.2f}" y="{top:.2f}" width="0" height="{lh + 1:.2f}">'
            f'<animate attributeName="width" from="0" to="{ink_w:.2f}" begin="{begin}" '
            f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(text.format(clip=f' clip-path="url(#r{r})"'))
        body.append(
            f'<rect x="{x0:.2f}" y="{top + lh * 0.1:.2f}" width="{cw:.2f}" height="{lh * 0.8:.2f}" '
            f'fill="{ACCENT}" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{begin}"/>'
            f'<animate attributeName="x" from="{x0:.2f}" to="{x0 + ink_w:.2f}" begin="{begin}" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{t + ROW_DUR:.3f}s"/></rect>'
        )
        t += ROW_STAGGER

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PORTRAIT_W}" height="{PANEL_H}" '
        f'viewBox="0 0 {PORTRAIT_W} {PANEL_H}" role="img" aria-label="ASCII portrait of Jean Pereira">'
        f'<defs><linearGradient id="ink" x1="0" y1="0" x2="0" y2="{PANEL_H}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{FG}"/><stop offset="0.55" stop-color="#c4b5fd"/>'
        f'<stop offset="1" stop-color="{ACCENT}"/></linearGradient>{"".join(defs)}</defs>'
        f"{panel(PORTRAIT_W, PANEL_H)}"
        f'<g font-family="{FONT}" font-size="{lh * 1.02:.2f}" fill="url(#ink)" xml:space="preserve">'
        f'{"".join(body)}</g></svg>\n'
    )
    write("ascii.svg", svg)


if __name__ == "__main__":
    main()
