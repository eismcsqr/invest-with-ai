"""Temporary probe: find Fed historical-page headings the parser misses."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_event_calendar as b
from fetch_macro_data import http_get

LOOSE = re.compile(rf"^({b.MONTH_RE})\b.*-\s*(\d{{4}})$")
for year in range(1994, 2021):
    raw = http_get(f"{b.FED}fomchistorical{year}.htm", label=f"Fed {year}").decode("utf-8", "replace")
    lines = b.html_lines(raw)
    for i, l in enumerate(lines):
        if LOOSE.match(l) and not b.HIST_HEAD.match(l):
            print(f"MISS {year}: {l!r}")
    if year in (2003, 2013, 2017):
        for i, l in enumerate(lines):
            if re.search(r"September 1[56]|April 30|January 31|October 31", l):
                print(f"CTX {year} L{i}: {l!r} | next: {lines[i+1:i+4]!r}")
        for m in re.finditer(r"(September 1[56]|April 30|January 31|October 31)", raw):
            s = m.start()
            print(f"RAW {year}: {raw[max(0,s-150):s+120]!r}")
cal = b.html_lines(http_get(b.FED + "fomccalendars.htm", label="cal").decode("utf-8", "replace"))
for i, l in enumerate(cal):
    if "/" in l and b.CAL_MONTH.match(l):
        print(f"CAL L{i}: {l!r} next {cal[i+1:i+2]!r}")
