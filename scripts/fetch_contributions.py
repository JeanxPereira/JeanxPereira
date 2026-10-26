"""Scrapes the public contribution calendar into data/contributions.json.

No token: https://github.com/users/<user>/contributions is a public HTML fragment.
It is not an official API, so this breaks if GitHub changes the markup — and fails loudly.
"""

import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser

from common import DATA

USER = os.environ.get("GH_USER", "JeanxPereira")


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}  # cell id -> {date, level}
        self.counts = {}  # cell id -> count
        self._tip_for = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in (a.get("class") or "") and a.get("data-date"):
            self.days[a["id"]] = {"date": a["data-date"], "level": int(a.get("data-level") or 0)}
        elif tag == "tool-tip":
            self._tip_for = a.get("for")

    def handle_data(self, data):
        if self._tip_for:
            m = re.match(r"\s*(\d[\d,]*) contribution", data)
            self.counts[self._tip_for] = int(m.group(1).replace(",", "")) if m else 0

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self._tip_for = None


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    # Today may not have activity yet; the streak is still alive if yesterday did.
    current = 0
    tail = days[:-1] if days and not days[-1]["count"] else days
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1
    return current, longest


def main():
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "profile-readme-bot"},
    )
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    cal = Calendar()
    cal.feed(html)
    if len(cal.days) < 300:
        sys.exit(f"parsed only {len(cal.days)} days; did the contributions markup change?")

    days = sorted(
        ({**d, "count": cal.counts.get(cid, 0)} for cid, d in cal.days.items()),
        key=lambda d: d["date"],
    )
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    out = {
        "user": USER,
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"]),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "months": months,
        "days": days,
    }
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, "contributions.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    print(f"wrote {path}: {out['total']} contributions, {len(days)} days, streak {current}/{longest}")


if __name__ == "__main__":
    main()
