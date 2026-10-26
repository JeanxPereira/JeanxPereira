"""Shared palette and sizes for the profile SVGs, so the panels line up and match."""

import os

# Portrait + card sit side by side and together match the heatmap width.
PORTRAIT_W = 370
CARD_W = 490
HEATMAP_W = PORTRAIT_W + CARD_W
PANEL_H = 470

THEMES = {
    "violet": {
        "bg": "#0d1117", "border": "#30363d", "fg": "#e6edf3", "muted": "#8b949e",
        "accent": "#a78bfa", "accent_2": "#7c5cdb",
        "levels": ["#161b22", "#2e1f5e", "#4c2f9e", "#7c5cdb", "#b39dff"],
        "swatches": ["#161b22", "#f85149", "#3fb950", "#d29922", "#58a6ff", "#a78bfa", "#39c5cf", "#e6edf3"],
    },
    # Singed's flask: acid lime on pure black.
    "toxic": {
        "bg": "#000000", "border": "#1c3a1a", "fg": "#e4ffd9", "muted": "#6f8f68",
        "accent": "#9dff2f", "accent_2": "#46c41f",
        "levels": ["#101a10", "#16461a", "#22801f", "#55cc22", "#b8ff3c"],
        "swatches": ["#101a10", "#16461a", "#22801f", "#39ff14", "#9dff2f", "#c8ff7a", "#e4ffd9", "#f2ff00"],
    },
    # Bordeaux on pure black, with a lighter blood tone so text stays legible.
    "wine": {
        "bg": "#000000", "border": "#3a1a20", "fg": "#f5e6e8", "muted": "#9a7a7f",
        "accent": "#e0405e", "accent_2": "#a01c34",
        "levels": ["#1a1013", "#4a0e1b", "#7a1428", "#b31f3a", "#ff4d6a"],
        "swatches": ["#1a1013", "#3d0a14", "#5e0f1f", "#7a1428", "#a01c34", "#e0405e", "#f08a9c", "#f5e6e8"],
    },
}

THEME = os.environ.get("THEME", "violet")
_t = THEMES[THEME]
BG, BORDER, FG, MUTED = _t["bg"], _t["border"], _t["fg"], _t["muted"]
ACCENT, ACCENT_2 = _t["accent"], _t["accent_2"]
LEVELS, SWATCHES = _t["levels"], _t["swatches"]
# The default theme keeps the plain file names the README already points at.
SUFFIX = "" if THEME == "violet" else f"-{THEME}"

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
    stem, ext = os.path.splitext(name)
    path = os.path.join(ASSETS, f"{stem}{SUFFIX}{ext}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"wrote {path} ({len(svg) // 1024} KiB)")
