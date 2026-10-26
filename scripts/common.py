"""Shared palette and sizes for the profile SVGs, so the panels line up and match."""

import os

# Portrait + card sit side by side and together match the heatmap width.
PORTRAIT_W = 370
CARD_W = 490
HEATMAP_W = PORTRAIT_W + CARD_W
PANEL_H = 470

BG = "#0d1117"
BORDER = "#30363d"
FG = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#a78bfa"
ACCENT_2 = "#7c5cdb"

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# STATIC=1 writes a frozen final frame (no animation) for local previews.
STATIC = os.environ.get("STATIC") == "1"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "data")


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def panel(width, height):
    return (
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" '
        f'fill="{BG}" stroke="{BORDER}"/>'
    )


def write(name, svg):
    os.makedirs(ASSETS, exist_ok=True)
    path = os.path.join(ASSETS, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"wrote {path} ({len(svg) // 1024} KiB)")
