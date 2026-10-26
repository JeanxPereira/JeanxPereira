"""Turns glyph.svg into assets/ascii.svg: the JXP glyph as ASCII, typed row by row.

Run locally whenever the glyph changes (needs Pillow + numpy). The glyph is a flat
shape, so shading comes from distance to its edge: sparse at the rim, dense inside.
"""

import os
import re
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from common import ACCENT, ACCENT_2, FONT, PANEL_H, PORTRAIT_W, ROOT, STATIC, esc, panel, write

COLS = 64
PAD = 16
# Share of the panel left empty around the glyph.
INSET = 0.04
# Sparse -> dense. On a dark panel a dense glyph reads as a bright pixel.
RAMP = " .:-=+*xX#%@"

ROW_DUR = 0.42
ROW_STAGGER = 0.035

SVG_NS = "{http://www.w3.org/2000/svg}"


def matrix(transform):
    """Only matrix(...) is handled; that is all the glyph's export uses."""
    m = np.identity(3)
    for args in re.findall(r"matrix\(([^)]*)\)", transform or ""):
        a, b, c, d, e, f = (float(v) for v in re.split(r"[\s,]+", args.strip()))
        m = m @ np.array([[a, c, e], [b, d, f], [0, 0, 1]])
    return m


def subpaths(d):
    """Flattens an absolute M/L/C/Z path into closed polygons."""
    tokens = re.findall(r"[MLCZ]|-?\d*\.?\d+(?:e-?\d+)?", d)
    if any(t.isalpha() and t not in "MLCZ" for t in tokens):
        raise SystemExit("glyph.svg path uses commands other than M/L/C/Z")
    polys, cur, i, cmd = [], [], 0, None
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd == "Z":
                polys.append(cur)
                cur = []
            continue
        if cmd == "M":
            if cur:
                polys.append(cur)
            cur = [(float(tokens[i]), float(tokens[i + 1]))]
            cmd, i = "L", i + 2
        elif cmd == "L":
            cur.append((float(tokens[i]), float(tokens[i + 1])))
            i += 2
        elif cmd == "C":
            p0 = np.array(cur[-1])
            p1, p2, p3 = (np.array([float(tokens[i + k]), float(tokens[i + k + 1])]) for k in (0, 2, 4))
            for t in np.linspace(0, 1, 25)[1:]:
                cur.append(tuple((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3))
            i += 6
    if cur:
        polys.append(cur)
    return polys


def load_polygons(path):
    polys = []

    def walk(node, m):
        m = m @ matrix(node.get("transform"))
        if node.tag == SVG_NS + "path":
            for poly in subpaths(node.get("d")):
                pts = np.c_[np.array(poly), np.ones(len(poly))] @ m.T
                polys.append(pts[:, :2])
        for child in node:
            walk(child, m)

    walk(ET.parse(path).getroot(), np.identity(3))
    return polys


def rasterize(polys, w, h):
    """Contains the glyph in a w x h canvas, centered; even-odd fill via XOR of subpaths."""
    pts = np.vstack(polys)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    scale = min(w, h) * (1 - 2 * INSET) / max(hi - lo)
    offset = np.array([w, h]) / 2 - (lo + hi) / 2 * scale
    mask = Image.new("1", (w, h), 0)
    for poly in polys:
        layer = Image.new("1", (w, h), 0)
        ImageDraw.Draw(layer).polygon([tuple(p) for p in poly * scale + offset], fill=1)
        mask = ImageChops.logical_xor(mask, layer)
    return mask.convert("L")


def edge_distance(mask, steps):
    """Approximate distance to the edge by counting how many erosions each pixel survives."""
    dist = np.zeros((mask.height, mask.width), dtype=np.float32)
    cur = mask
    for _ in range(steps):
        dist += np.asarray(cur, dtype=np.float32) / 255
        cur = cur.filter(ImageFilter.MinFilter(3))
    return Image.fromarray((dist / max(dist.max(), 1) * 255).astype(np.uint8))


def main():
    cw = (PORTRAIT_W - 2 * PAD) / COLS
    lh = cw * 1.9
    rows = int((PANEL_H - 2 * PAD) / lh)
    lh = (PANEL_H - 2 * PAD) / rows

    # Work at a fine pixel grid with the cell aspect, then average down to one value per cell.
    sub = 8
    gw = COLS * sub
    gh_px = round(gw * (lh / cw) * rows / COLS)
    fine = rasterize(load_polygons(os.path.join(ROOT, "glyph.svg")), gw, gh_px)
    dist = edge_distance(fine, steps=sub * 4).resize((COLS, rows), Image.Resampling.BOX)
    cover = fine.resize((COLS, rows), Image.Resampling.BOX)
    dist = np.asarray(dist, dtype=np.float32) / 255
    cover = np.asarray(cover, dtype=np.float32) / 255

    lines = []
    for r in range(rows):
        chars = []
        for c in range(COLS):
            if cover[r, c] < 0.3:
                chars.append(" ")
                continue
            # Partly covered cells sit on the rim: keep them light so the outline stays crisp.
            v = cover[r, c] * (0.3 + 0.7 * dist[r, c] ** 0.5)
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
        f'viewBox="0 0 {PORTRAIT_W} {PANEL_H}" role="img" aria-label="JXP glyph in ASCII">'
        f'<defs><linearGradient id="ink" x1="0" y1="0" x2="0" y2="{PANEL_H}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient>{"".join(defs)}</defs>'
        f"{panel(PORTRAIT_W, PANEL_H)}"
        f'<g font-family="{FONT}" font-size="{lh * 1.02:.2f}" fill="url(#ink)" xml:space="preserve">'
        f'{"".join(body)}</g></svg>\n'
    )
    write("ascii.svg", svg)


if __name__ == "__main__":
    main()
