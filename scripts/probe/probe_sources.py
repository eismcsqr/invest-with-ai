"""Temporary probe: shows the structure of the Fed's FOMC pages and the FRED
vintage endpoints, so the event-calendar parser can be written against them.
Prints no secrets. Removed before review."""
import json, os, re, urllib.parse, urllib.request, html

def get(url, params=None):
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0 invest-with-ai-data-pull"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def show_fed(url, n=80):
    print("=" * 30, url)
    try:
        t = get(url)
    except Exception as e:
        print("ERR", e); return
    print("len", len(t))
    for m in re.finditer(r'<(h\d|div|p|a|strong)\b([^>]*)>(.{0,160}?)</\1>', t, re.S):
        tag, attrs, inner = m.groups()
        txt = html.unescape(re.sub(r"<[^>]+>", " ", inner))
        txt = " ".join(txt.split())
        if re.search(r"Meeting|Conference Call|unscheduled|fomc-meeting|panel-heading|Statement", attrs + " " + txt, re.I):
            print(f"[{tag} {attrs.strip()[:70]}] {txt[:120]}")
            n -= 1
            if n <= 0: break

for y in (1994, 2001, 2008, 2020, 2021):
    show_fed(f"https://www.federalreserve.gov/monetarypolicy/fomchistorical{y}.htm", 60)
show_fed("https://www.federalreserve.gov/monetarypolicy/fomc_historical_year.htm", 30)
show_fed("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", 120)

key = os.environ["FRED_API_KEY"]
base = "https://api.stlouisfed.org/fred/"
def fred(path, **p):
    p.update(api_key=key, file_type="json")
    try:
        return json.loads(get(base + path, p))
    except Exception as e:
        return {"error": str(e)[:200]}

for rid in (10, 9, 54):
    d = fred("release/dates", release_id=rid, realtime_start="1776-07-04", include_release_dates_with_no_data="true", limit=10000, sort_order="asc")
    ds = d.get("release_dates", [])
    print("release", rid, fred("release", release_id=rid).get("releases", [{}])[0].get("name"), len(ds), ds[:3], ds[-3:])
for sid in ("CPIAUCSL", "PCEPI", "PCE", "RSAFS", "CPILFESL", "PCEPILFE"):
    d = fred("series/observations", series_id=sid, realtime_start="1776-07-04", realtime_end="9999-12-31", output_type=4, limit=100000)
    o = d.get("observations", [])
    print(sid, "initial-release rows", len(o), d.get("error", ""))
    for r in o[:2] + o[-3:]:
        print("   ", r)
    # find first observation whose release lag looks genuine
    import datetime as dt
    for r in o:
        if r["value"] != "." and (dt.date.fromisoformat(r["realtime_start"]) - dt.date.fromisoformat(r["date"])).days < 80:
            print("    first genuine-looking:", r); break
    d = fred("series/observations", series_id=sid, realtime_start="1776-07-04", realtime_end="9999-12-31", limit=100000)
    print(sid, "all-vintage rows", d.get("count"), len(d.get("observations", [])))
    d = fred("series/vintagedates", series_id=sid, limit=10000)
    v = d.get("vintage_dates", [])
    print(sid, "vintage dates", len(v), v[:2], v[-2:])
for sid in ("DFEDTAR", "DFEDTARU", "DFEDTARL"):
    d = fred("series", series_id=sid)
    s = d.get("seriess", [{}])[0]
    print(sid, s.get("observation_start"), s.get("observation_end"), s.get("frequency"))
d = fred("series/observations", series_id="DFEDTARU", observation_start="2022-03-14", observation_end="2022-03-19")
print("DFEDTARU Mar2022", [(o["date"], o["value"]) for o in d.get("observations", [])])
d = fred("series/observations", series_id="DFEDTAR", observation_start="2001-01-01", observation_end="2001-01-05")
print("DFEDTAR Jan2001", [(o["date"], o["value"]) for o in d.get("observations", [])])
d = fred("series/observations", series_id="DFEDTARU", observation_start="2020-03-13", observation_end="2020-03-17")
print("DFEDTARU Mar2020", [(o["date"], o["value"]) for o in d.get("observations", [])])
