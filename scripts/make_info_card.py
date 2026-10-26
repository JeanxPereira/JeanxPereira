"""Writes assets/info-card.svg: a neofetch-style panel whose lines fade in one by one."""

from common import (ACCENT, ACCENT_2, BORDER, CARD_W, FG, FONT, MUTED, PANEL_H, STATIC, SWATCHES,
                    esc, panel, write)

USER = "jean"
HOST = "github"

# (label, value). Keep values under ~44 chars or they run off the panel.
ROWS = [
    ("Role", "IT pro · reverse engineer · 3D rigger"),
    ("Now", "CrystalOSD: PS2 OSDSYS in C++26 + Vulkan"),
    ("Also", "Watson · GoWToolkit · Icon-Composer"),
    ("Prev", "ReCap: reviving Darkspore's servers"),
    ("Stack", "C++26 · C# · Python · TypeScript"),
    ("Graphics", "Vulkan · Blender · rigging"),
    ("RE", "IDA Pro · Ghidra · PCSX2 · ImHex"),
    ("Formats", "binary parsers, decompilers, unpackers"),
    ("Music", "guitar · rock · metal · MPB"),
]

PAD_X = 26
TOP = 74
LINE_H = 24
FONT_SIZE = 14
CHAR_W = FONT_SIZE * 0.6
LABEL_COLS = 11

STAGGER = 0.11
START = 0.35


def line(i, content):
    if STATIC:
        return f"<g>{content}</g>"
    return f'<g class="l" style="animation-delay:{START + i * STAGGER:.2f}s">{content}</g>'


def main():
    out = []
    y = TOP
    i = 0

    title = f"{USER}@{HOST}"
    out.append(line(i, (
        f'<text x="{PAD_X}" y="{y}"><tspan fill="{ACCENT}" font-weight="700">{USER}</tspan>'
        f'<tspan fill="{MUTED}">@</tspan><tspan fill="{ACCENT}" font-weight="700">{HOST}</tspan></text>'
    )))
    y += LINE_H
    i += 1
    out.append(line(i, f'<text x="{PAD_X}" y="{y}" fill="{MUTED}">{"-" * len(title)}</text>'))
    y += LINE_H
    i += 1

    value_x = PAD_X + LABEL_COLS * CHAR_W
    for label, value in ROWS:
        out.append(line(i, (
            f'<text x="{PAD_X}" y="{y}" fill="{ACCENT}" font-weight="700">{esc(label)}:</text>'
            f'<text x="{value_x:.1f}" y="{y}" fill="{FG}">{esc(value)}</text>'
        )))
        y += LINE_H
        i += 1

    y += LINE_H // 2
    sw = 26
    blocks = "".join(
        f'<rect x="{PAD_X + k * sw}" y="{y - 15}" width="{sw}" height="18" fill="{c}"/>'
        for k, c in enumerate(SWATCHES)
    )
    out.append(line(i, blocks))
    i += 1

    prompt_y = PANEL_H - 30
    cursor = (
        f'<rect class="cur" x="{PAD_X + 17 * CHAR_W:.1f}" y="{prompt_y - 13}" '
        f'width="{CHAR_W:.1f}" height="17" fill="{ACCENT}"/>'
    )
    out.append(line(i, (
        f'<text x="{PAD_X}" y="{prompt_y}"><tspan fill="{ACCENT_2}">{USER}@{HOST}</tspan>'
        f'<tspan fill="{MUTED}"> ~ $ </tspan></text>{cursor}'
    )))

    style = "" if STATIC else (
        "<style>"
        ".l{opacity:0;animation:in .5s cubic-bezier(.2,.7,.2,1) forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
        ".cur{animation:blink 1.1s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}"
        "</style>"
    )

    dots = "".join(
        f'<circle cx="{22 + k * 18}" cy="20" r="5.5" fill="{c}"/>'
        for k, c in enumerate(["#f85149", "#d29922", "#3fb950"])
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{PANEL_H}" '
        f'viewBox="0 0 {CARD_W} {PANEL_H}" role="img" aria-label="neofetch-style profile card">'
        f"{style}{panel(CARD_W, PANEL_H)}{dots}"
        f'<text x="{CARD_W / 2}" y="24" text-anchor="middle" font-family="{FONT}" font-size="12" '
        f'fill="{MUTED}">{USER}@{HOST}: ~ — neofetch</text>'
        f'<line x1="1" y1="40" x2="{CARD_W - 1}" y2="40" stroke="{BORDER}"/>'
        f'<g font-family="{FONT}" font-size="{FONT_SIZE}" xml:space="preserve">{"".join(out)}</g>'
        "</svg>\n"
    )
    write("info-card.svg", svg)


if __name__ == "__main__":
    main()
