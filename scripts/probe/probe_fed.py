"""Temporary probe: print every heading-like line on selected Fed historical pages."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_event_calendar as b
from fetch_macro_data import http_get

for year in range(1994, 2021):
    raw = http_get(f"{b.FED}fomchistorical{year}.htm", label=f"Fed {year}").decode("utf-8", "replace")
    heads = re.findall(r"<h5[^>]*>(.*?)</h5>", raw, flags=re.S)
    for h in heads:
        h = " ".join(re.sub(r"<[^>]+>", " ", h).split())
        ok = bool(b.HIST_HEAD.match(h))
        if not ok or "/" in h:
            print(f"H5 {year} match={ok}: {h!r}")
    print(f"YEAR {year}: {len(heads)} h5 headings, {sum(1 for h in heads if 'Meeting' in h)} with Meeting")
