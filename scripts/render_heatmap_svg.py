"""Renders data/contributions.json into assets/heatmap.svg (53 weeks x 7 days).

Cells drop in along a diagonal once on load and then hold; nothing loops.
"""

import json
import os
from datetime import date

from common import (ACCENT, BORDER, DATA, FG, FONT, HEATMAP_W, LEVELS, MUTED, STATIC, panel,
                    write)

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
LABEL_W = 30
GRID_TOP = 72


def main():
    with open(os.path.join(DATA, "contributions.json"), encoding="utf-8") as f:
        data = json.load(f)
    days = data["days"]

    first = date.fromisoformat(days[0]["date"])
    sunday = first.toordinal() - (first.isoweekday() % 7)
    grid_left = PAD + LABEL_W

    cells, months = [], []
    last_month = None
    for d in days:
        day = date.fromisoformat(d["date"])
        col = (day.toordinal() - sunday) // 7
        row = day.isoweekday() % 7
        x, y = grid_left + col * STEP, GRID_TOP + row * STEP
        anim = "" if STATIC else f' class="c" style="animation-delay:{0.25 + col * 0.014 + row * 0.04:.3f}s"'
        noun = "contribution" if d["count"] == 1 else "contributions"
        cells.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{LEVELS[min(d["level"], 4)]}"{anim}><title>{d["count"]} {noun} on {d["date"]}</title></rect>'
        )
        if row == 0 and day.month != last_month:
            last_month = day.month
            # Skip a label squeezed against the left edge by a partial first month.
            if col < 51 and not (col == 0 and day.day > 7):
                months.append(
                    f'<text x="{x}" y="{GRID_TOP - 9}">{day.strftime("%b")}</text>'
                )

    weekdays = "".join(
        f'<text x="{PAD}" y="{GRID_TOP + r * STEP + CELL - 2}">{name}</text>'
        for r, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    )

    grid_bottom = GRID_TOP + 7 * STEP
    footer_y = grid_bottom + 34
    best = data["best_day"]
    best_day = date.fromisoformat(best["date"]).strftime("%b %d").replace(" 0", " ")
    stats = [
        (f'{data["total"]:,}', "contributions"),
        (f'{data["current_streak"]}d', "current streak"),
        (f'{data["longest_streak"]}d', "longest streak"),
        (f'{best["count"]}', f"best day ({best_day})"),
    ]
    stat_svg = "".join(
        f'<text x="{PAD + k * 150}" y="{footer_y}"><tspan fill="{FG}" font-weight="700">{v}</tspan>'
        f'<tspan fill="{MUTED}"> {label}</tspan></text>'
        for k, (v, label) in enumerate(stats)
    )

    legend_x = HEATMAP_W - PAD - 5 * STEP - 34
    legend = (
        f'<text x="{legend_x - 8}" y="{footer_y}" text-anchor="end">Less</text>'
        + "".join(
            f'<rect x="{legend_x + k * STEP}" y="{footer_y - 10}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{c}"/>'
            for k, c in enumerate(LEVELS)
        )
        + f'<text x="{legend_x + 5 * STEP + 4}" y="{footer_y}">More</text>'
    )

    height = footer_y + 24
    style = "" if STATIC else (
        "<style>"
        ".c{opacity:0;transform-box:fill-box;transform-origin:center;"
        "animation:drop .45s cubic-bezier(.2,.7,.2,1) forwards}"
        "@keyframes drop{from{opacity:0;transform:translateY(-8px) scale(.6)}to{opacity:1;transform:none}}"
        "</style>"
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{HEATMAP_W}" height="{height}" '
        f'viewBox="0 0 {HEATMAP_W} {height}" role="img" '
        f'aria-label="{data["total"]} GitHub contributions in the last year">'
        f"{style}{panel(HEATMAP_W, height)}"
        f'<g font-family="{FONT}" font-size="11" fill="{MUTED}">'
        f'<text x="{PAD}" y="32" font-size="14"><tspan fill="{ACCENT}" font-weight="700">contributions</tspan>'
        f'<tspan> · last 12 months · updated {date.today().isoformat()}</tspan></text>'
        f'<line x1="1" y1="46" x2="{HEATMAP_W - 1}" y2="46" stroke="{BORDER}"/>'
        f'{"".join(months)}{weekdays}{"".join(cells)}{stat_svg}{legend}</g></svg>\n'
    )
    write("heatmap.svg", svg)


if __name__ == "__main__":
    main()
