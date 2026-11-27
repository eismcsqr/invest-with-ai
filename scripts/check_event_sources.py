"""Check a source for each of the 12 v1 event types (tracker task E2).

The event types were agreed on Nov 27 (docs/event-types.md): official
records only, at three levels. This script opens each candidate source and
records whether it returns the data an event study needs, with how much
history. It writes small summary files only, under data/events/sources/:

  source_checks.csv            one row per source: status, first and last
                               date, rows, events found, note
  sharadar_event_codes.csv     Sharadar's 8-K events table by item code
  sharadar_actions.csv         Sharadar's corporate actions by type
  sharadar_vs_edgar_8k.csv     8-K items for a few companies: Sharadar
                               against SEC's own filing index
  edgar_form_counts.csv        filings per quarter for the non-8-K forms
                               (13D stakes, tender offers, merger proxies,
                               offerings, late filing notices)
  federal_register_counts.csv  rules and tariff documents per year
  index_spikes.csv             spike days in the daily risk indexes, with
                               a few known events as a check
  EVENT_SOURCES_CHECK.md       the summary

Sources and secrets:
  - Sharadar (events, actions, tickers tables): SHARADAR_API_KEY. The key is
    read from the environment and only sent as a header, never printed.
  - FRED (daily policy uncertainty, oil price): FRED_API_KEY.
  - SEC EDGAR: no key. SEC_USER_AGENT (name and contact) is used if set.
  - Federal Register API, matteoiacoviello.com (GPR, TPU), Kaenzig's site
    (OPEC announcement dates): no key.

A source that fails is recorded as failed with the reason; the others still
run. Reading the Excel files needs xlrd (.xls) and openpyxl (.xlsx); the
workflow installs them.

Run: python scripts/check_event_sources.py
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import html
import io
import json
import os
import re
import statistics
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_company_data as fcd  # noqa: E402  (Sharadar download helpers)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "events" / "sources"
RAW = ROOT / "raw" / "event_sources"

UA = os.environ.get("SEC_USER_AGENT", "").strip() or "invest-with-ai-data-pull"
TODAY = dt.date.today()
ITEMS_START = dt.date(2004, 8, 23)   # current 8-K item numbers start here

GPR_PAGE = "https://www.matteoiacoviello.com/gpr.htm"
TPU_PAGE = "https://www.matteoiacoviello.com/tpu.htm"
OPEC_HOME = "https://www.opec.org/"
FRED_OBS = "https://api.stlouisfed.org/fred/series/observations"
FR_API = "https://www.federalregister.gov/api/v1/documents.json"
EDGAR_INDEX = "https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx"
EDGAR_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_FTS = "https://efts.sec.gov/LATEST/search-index"

# Known days each daily index should flag (a sanity check, not a test).
KNOWN = {
    "GPR": [("2001-09-11", "September 11 attacks"),
            ("2003-03-20", "Iraq invasion"),
            ("2014-03-01", "Crimea annexation"),
            ("2022-02-24", "Russia invades Ukraine"),
            ("2023-10-09", "Hamas attack on Israel (first weekday)")],
    "TPU": [("2018-03-01", "steel and aluminum tariffs announced"),
            ("2018-07-06", "first China tariffs take effect"),
            ("2019-05-06", "China tariff increase announced"),
            ("2025-04-03", "reciprocal tariffs announced (day after)")],
    "EPU": [("2008-09-29", "House rejects bank bailout"),
            ("2016-11-09", "day after 2016 election"),
            ("2020-03-16", "Covid market crash")],
}

# Sharadar codes: the 8-K item number without its dot (5.02 -> 52), checked
# below against SEC's own index. Items each company event type uses.
EVENT_ITEMS = {
    "Guidance changes": ["2.02", "7.01"],
    "Mergers and acquisitions": ["1.01", "2.01"],
    "Leadership changes": ["5.02"],
    "Capital structure breaks": ["8.01", "3.02"],
    "Accounting and legal trouble": ["4.01", "4.02", "3.01"],
    "Distress and restructuring": ["1.03", "2.04", "2.05"],
}

# Non-8-K forms in SEC's quarterly index, by event type.
FORMS = {
    "Activist stakes": ["SC 13D", "SCHEDULE 13D"],
    "Mergers (tender offers)": ["SC TO-T", "SC 14D9"],
    "Mergers (merger proxies)": ["DEFM14A", "PREM14A"],
    "Offerings": ["424B4", "424B5", "S-3"],
    "Late filings": ["NT 10-K", "NT 10-Q"],
    "All 8-Ks": ["8-K"],
}
INDEX_QUARTERS = [(1994, 1), (1997, 1), (2001, 1), (2004, 4), (2008, 4),
                  (2012, 1), (2016, 1), (2020, 2), (2024, 1), (2025, 1),
                  (2025, 3)]
XCHECK_TICKERS = ["AAPL", "WMT", "XOM", "JNJ", "HD", "JPM", "BA", "GE"]



def item_code(item: str) -> str:
    """8-K item number to Sharadar's code: 5.02 -> 52, 1.01 -> 11."""
    a, b = item.split(".")
    return f"{int(a)}{int(b)}"


checks: list[dict] = []
notes: dict[str, list[str]] = defaultdict(list)


# ----------------------------------------------------------------- helpers --

def get(url: str, params: dict | None = None, headers: dict | None = None,
        timeout: int = 90, tries: int = 4) -> bytes:
    """GET with retries. Errors name the host only, never a query string."""
    full = url + ("?" + urllib.parse.urlencode(params, doseq=True) if params else "")
    h = {"User-Agent": UA, "Accept-Encoding": "identity"}
    h.update(headers or {})
    host = urllib.parse.urlparse(url).netloc
    last = ""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(full, headers=h),
                                        timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code < 500 and e.code != 429:
                break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = type(e).__name__
        time.sleep(2 ** attempt)
    raise RuntimeError(f"{host}: {last}")


def links(page_url: str, pattern: str) -> list[str]:
    """Absolute links on a page whose href matches a regex."""
    text = get(page_url).decode("utf-8", "replace")
    found = []
    for href in re.findall(r'href\s*=\s*["\']([^"\']+)["\']', text, re.I):
        href = html.unescape(href.strip())
        if re.search(pattern, href, re.I):
            found.append(urllib.parse.urljoin(page_url, href))
    return list(dict.fromkeys(found))


def record(event_type: str, source: str, status: str, first="", last="",
           rows="", events="", cost="free", note=""):
    checks.append({"event_type": event_type, "source": source, "status": status,
                   "first": str(first)[:10], "last": str(last)[:10],
                   "rows": rows, "events": events, "cost": cost, "note": note})
    print(f"[{status}] {event_type}: {source} {first}..{last} {note}")


def guarded(fn):
    """Run one source check; a crash is recorded, not fatal."""
    def run(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            record(fn.__name__, fn.__doc__.splitlines()[0] if fn.__doc__ else "",
                   "fail", note=f"{type(e).__name__}: {str(e)[:160]}")
    return run


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def to_date(v) -> dt.date | None:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(s[:19] if "%H" in fmt else s[:10], fmt).date()
        except ValueError:
            continue
    return None


def to_float(v) -> float | None:
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError):
        return None


# ----------------------------------------------------- daily index helpers --

def read_sheets(data: bytes, url: str) -> dict[str, list[list]]:
    """All sheets of an xls/xlsx/csv file as lists of rows."""
    low = url.lower().split("?")[0]
    if low.endswith(".csv"):
        return {"csv": list(csv.reader(io.StringIO(data.decode("utf-8", "replace"))))}
    if low.endswith(".xlsx"):
        import openpyxl  # noqa: PLC0415
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        return {ws.title: [list(r) for r in ws.iter_rows(values_only=True)]
                for ws in wb.worksheets}
    import xlrd  # noqa: PLC0415
    book = xlrd.open_workbook(file_contents=data)
    out = {}
    for sh in book.sheets():
        rows = []
        for i in range(sh.nrows):
            row = []
            for c in sh.row(i):
                if c.ctype == xlrd.XL_CELL_DATE:
                    row.append(xlrd.xldate.xldate_as_datetime(c.value, book.datemode))
                else:
                    row.append(c.value)
            rows.append(row)
        out[sh.name] = rows
    return out


def daily_series(sheets: dict, want: list[str]) -> tuple[str, str, dict]:
    """Find a daily date column and the first value column named in want.

    Returns (sheet name, column name, {date: value})."""
    for name, rows in sheets.items():
        for hi, header in enumerate(rows[:15]):
            labels = [str(h).strip() for h in header]
            dcol = next((i for i, h in enumerate(labels)
                         if h.lower() in ("date", "day", "dates")), None)
            vcol = None
            for w in want:
                vcol = next((i for i, h in enumerate(labels) if h.upper() == w.upper()), None)
                if vcol is not None:
                    break
            if dcol is None:
                dcol = next((i for i, h in enumerate(labels) if "date" in h.lower()), None)
            if vcol is None and dcol is not None:
                vcol = next((i for i, h in enumerate(labels) if i != dcol and any(
                    w.upper() in h.upper() for w in want)), None)
            if dcol is None or vcol is None:
                continue
            series = {}
            for r in rows[hi + 1:]:
                if len(r) <= max(dcol, vcol):
                    continue
                d, v = to_date(r[dcol]), to_float(r[vcol])
                if d and v is not None:
                    series[d] = v
            if len(series) > 1000:
                gaps = sorted(series)
                step = statistics.median((b - a).days for a, b in zip(gaps, gaps[1:]))
                if step <= 3:
                    return name, labels[vcol], series
    return "", "", {}


def spikes(series: dict, pct: float = 0.99, gap_days: int = 10) -> list[dt.date]:
    """First day of each episode above the given percentile."""
    vals = sorted(series.values())
    cut = vals[int(pct * (len(vals) - 1))]
    starts, last = [], None
    for d in sorted(series):
        if series[d] >= cut:
            if last is None or (d - last).days > gap_days:
                starts.append(d)
            last = d
    return starts


def percentile_of(series: dict, d: dt.date) -> tuple[float | None, str]:
    """Value's percentile rank on that day (or the next day with data)."""
    for k in range(4):
        day = d + dt.timedelta(days=k)
        if day in series:
            v = series[day]
            vals = sorted(series.values())
            below = sum(1 for x in vals if x < v)
            return 100 * below / len(vals), day.isoformat()
    return None, ""


spike_rows: list[list] = []


def summarize_index(label: str, event_type: str, source: str, series: dict,
                    column: str) -> None:
    eps = spikes(series)
    eps5 = spikes(series, 0.95)
    for d, what in KNOWN.get(label, []):
        p, used = percentile_of(series, dt.date.fromisoformat(d))
        spike_rows.append([label, "known event", d, used, what,
                           "" if p is None else f"{p:.1f}"])
    for d in eps:
        spike_rows.append([label, "spike episode (top 1%)", d.isoformat(),
                           d.isoformat(), "", ""])
    known_hits = [percentile_of(series, dt.date.fromisoformat(d))[0]
                  for d, _ in KNOWN.get(label, [])]
    known_hits = [p for p in known_hits if p is not None]
    flagged = sum(1 for p in known_hits if p >= 95)
    first, last = min(series), max(series)
    stale = (TODAY - last).days
    status = "pass" if len(eps5) >= 30 and stale <= 21 and flagged >= len(known_hits) - 1 else "partial"
    record(event_type, source, status, first, last, len(series), len(eps5),
           note=(f"column {column}; {len(eps)} spike episodes in the top 1% of days, "
                 f"{len(eps5)} in the top 5% (10-day gap); {flagged} of {len(known_hits)} known events in "
                 f"the top 5% of days; last value {stale} days old"))


# ------------------------------------------------------------------ checks --

@guarded
def check_gpr():
    """Caldara and Iacoviello geopolitical risk index, daily"""
    files = links(GPR_PAGE, r"gpr_daily_recent.*\.xlsx?$")
    if not files:
        files = links(GPR_PAGE, r"daily.*\.xlsx?$")
    if not files:
        raise RuntimeError("no daily Excel file linked on the GPR page")
    url = files[0]
    sheets = read_sheets(get(url, timeout=180), url)
    sheet, col, series = daily_series(sheets, ["GPRD", "GPRD_MA7", "GPR"])
    if not series:
        raise RuntimeError("no daily date and GPRD column found; sheets: "
                           + ", ".join(sheets))
    notes["gpr"].append(f"File: {url.rsplit('/', 1)[-1]} (sheet {sheet}).")
    summarize_index("GPR", "Geopolitical shocks",
                    "Geopolitical risk index, daily (matteoiacoviello.com)",
                    series, col)


@guarded
def check_tpu():
    """Trade policy uncertainty index, daily"""
    files = links(TPU_PAGE, r"\.(xlsx?|csv)$")
    notes["tpu"].append("Files linked on the TPU page: "
                        + (", ".join(u.rsplit("/", 1)[-1] for u in files) or "none"))
    best = None
    for url in files:
        try:
            sheets = read_sheets(get(url, timeout=180), url)
        except Exception as e:  # noqa: BLE001
            notes["tpu"].append(f"{url.rsplit('/', 1)[-1]}: {type(e).__name__}")
            continue
        sheet, col, series = daily_series(sheets, ["TPUD_INDEX", "TPU", "TPU_DAILY", "TPUD",
                                                   "DAILY_TPU", "TPU_INDEX"])
        for nm, rows in sheets.items():
            if "DAILY" in nm.upper():
                notes["tpu"].append(f"{nm} first rows: " + " / ".join(
                    ", ".join(str(c) for c in r[:6]) for r in rows[:4]))
        notes["tpu"].append(f"{url.rsplit('/', 1)[-1]}: sheets "
                            + ", ".join(f"{k} ({len(v)} rows)" for k, v in sheets.items())
                            + (f"; daily column {col} in {sheet}" if series else
                               "; no daily date/TPU column found"))
        if series and (best is None or len(series) > len(best[1])):
            best = (col, series)
    if not best:
        raise RuntimeError("no daily TPU series found in the linked files")
    summarize_index("TPU", "Trade and tariff actions",
                    "Trade policy uncertainty index, daily (matteoiacoviello.com)",
                    best[1], best[0])


def fred(series_id: str) -> dict:
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        raise RuntimeError("FRED_API_KEY secret missing")
    data = json.loads(get(FRED_OBS, {"series_id": series_id, "api_key": key,
                                     "file_type": "json"}))
    out = {}
    for o in data.get("observations", []):
        d, v = to_date(o.get("date")), to_float(o.get("value"))
        if d and v is not None:
            out[d] = v
    if not out:
        raise RuntimeError(f"FRED {series_id}: no observations")
    return out


@guarded
def check_epu():
    """Economic policy uncertainty index, daily (FRED USEPUINDXD)"""
    series = fred("USEPUINDXD")
    summarize_index("EPU", "Elections and policy shocks",
                    "Economic policy uncertainty index, daily (FRED USEPUINDXD)",
                    series, "USEPUINDXD")


@guarded
def check_elections():
    """US federal election days, from statute"""
    days = []
    for y in range(1990, TODAY.year + 1, 2):
        nov1 = dt.date(y, 11, 1)
        first_monday = nov1 + dt.timedelta(days=(0 - nov1.weekday()) % 7)
        days.append((first_monday + dt.timedelta(days=1), y % 4 == 0))
    expected = {dt.date(2000, 11, 7), dt.date(2016, 11, 8), dt.date(2020, 11, 3),
                dt.date(2024, 11, 5), dt.date(2022, 11, 8)}
    ok = expected <= {d for d, _ in days}
    pres = sum(1 for d, p in days if p and d.year >= 1994)
    mid = sum(1 for d, p in days if not p and d.year >= 1994)
    write_csv("election_days.csv", ["date", "kind"],
              [[d.isoformat(), "presidential" if p else "midterm"] for d, p in days])
    record("Elections and policy shocks",
           "US federal election days (fixed by law: first Tuesday after the first Monday in November)",
           "pass" if ok else "fail", days[0][0], days[-1][0], len(days),
           f"{pres} presidential, {mid} midterm since 1994",
           note="computed; matches 5 known dates" if ok else "computed dates do not match known dates")


@guarded
def check_oil():
    """Oil price and OPEC meeting dates"""
    wti = fred("DCOILWTICO")
    record("Energy and commodity supply shocks", "WTI oil price, daily (FRED DCOILWTICO)",
           "pass" if (TODAY - max(wti)).days <= 14 else "partial",
           min(wti), max(wti), len(wti), "",
           note=f"last value {(TODAY - max(wti)).days} days old")
    # OPEC's own site, for meeting press releases (the official record of
    # meeting dates). Kaenzig's dated list sits on openICPSR behind a sign-in.
    try:
        page = get(OPEC_HOME, timeout=60).decode("utf-8", "replace")
        press = [u for u in re.findall(r'href\s*=\s*["\']([^"\']+)["\']', page, re.I)
                 if re.search(r"press|meeting|conference", u, re.I)]
        record("Energy and commodity supply shocks", "OPEC website: meeting press releases",
               "partial", note=(f"site reachable; {len(press)} press or meeting links on the "
                                "home page; dates need entering from the press releases"))
    except Exception as e:  # noqa: BLE001
        record("Energy and commodity supply shocks", "OPEC website: meeting press releases",
               "fail", note=f"{e}")


def fr_count(params: dict) -> int:
    p = {"per_page": 1, "fields[]": ["document_number"]}
    p.update(params)
    return int(json.loads(get(FR_API, p)).get("count", 0))


@guarded
def check_federal_register():
    """Federal Register API: significant rules and tariff documents"""
    rows = []
    for y in range(1994, TODAY.year + 1):
        yr = {"conditions[publication_date][year]": y}
        rules = fr_count({**yr, "conditions[type][]": "RULE"})
        sig = fr_count({**yr, "conditions[type][]": "RULE",
                        "conditions[significant]": 1})
        tariff_notices = fr_count({**yr, "conditions[term]": "tariff",
                                   "conditions[agencies][]": "trade-representative-office-of-united-states"})
        procl = fr_count({**yr, "conditions[type][]": "PRESDOCU",
                          "conditions[presidential_document_type][]": "proclamation",
                          "conditions[term]": "tariff"})
        rows.append([y, rules, sig, tariff_notices, procl])
        time.sleep(0.2)
    write_csv("federal_register_counts.csv",
              ["year", "final_rules", "significant_final_rules",
               "ustr_documents_mentioning_tariff", "proclamations_mentioning_tariff"], rows)
    sig_years = [r for r in rows if r[2] > 0]
    total_sig = sum(r[2] for r in rows)
    record("Major regulatory actions",
           "Federal Register API: final rules marked significant, by agency",
           "pass" if total_sig >= 300 else "partial",
           sig_years[0][0] if sig_years else "", rows[-1][0], sum(r[1] for r in rows),
           total_sig,
           note=(f"significant flag present from {sig_years[0][0] if sig_years else 'never'}; "
                 f"median {statistics.median(r[2] for r in sig_years) if sig_years else 0:.0f} a year"))
    total_tariff = sum(r[3] + r[4] for r in rows)
    record("Trade and tariff actions",
           "Federal Register API: USTR documents and presidential proclamations mentioning tariffs",
           "pass" if total_tariff >= 30 else "partial", rows[0][0], rows[-1][0], "",
           total_tariff,
           note=f"{sum(r[4] for r in rows)} proclamations, {sum(r[3] for r in rows)} USTR documents")
    # Which agencies issue the significant rules (for mapping to industries).
    try:
        facets = json.loads(get("https://www.federalregister.gov/api/v1/documents/facets/agency",
                                {"conditions[type][]": "RULE", "conditions[significant]": 1}))
        top = sorted(facets.items(), key=lambda kv: -int(kv[1].get("count", 0)))[:12]
        notes["fr"].append("Agencies with the most significant final rules: "
                           + ", ".join(f"{v.get('name', k)} ({v.get('count')})" for k, v in top))
    except Exception as e:  # noqa: BLE001
        notes["fr"].append(f"Agency counts not read: {e}")


# ------------------------------------------------------------- Sharadar ----

SHARADAR = {}


def sharadar_tables():
    key = fcd._api_key()
    fcd.RAW = RAW / "sharadar"
    for t in ("tickers", "events", "actions"):
        SHARADAR[t] = fcd.download_table(t, key)


def ticker_ciks() -> tuple[dict, dict]:
    header, rows = fcd.open_rows(SHARADAR["tickers"])
    ix = {h: i for i, h in enumerate(header)}
    ciks, groups = {}, {}
    for r in rows:
        if len(r) < len(header):
            continue
        t = r[ix["ticker"]]
        groups.setdefault(t, r[ix.get("famaindustry", 0)])
        link = r[ix["secfilings"]] if "secfilings" in ix else ""
        m = re.search(r"cik[=/]?0*(\d{1,10})", link, re.I)
        if m and t not in ciks:
            ciks[t] = m.group(1).zfill(10)
    return ciks, groups


@guarded
def check_sharadar_events():
    """Sharadar 8-K events table"""
    header, rows = fcd.open_rows(SHARADAR["events"])
    ix = {h: i for i, h in enumerate(header)}
    notes["sharadar"].append("Events table columns: " + ", ".join(header))
    stats = defaultdict(lambda: {"rows": 0, "since": 0, "tickers": set(),
                                 "first": None, "last": None})
    by_ticker = defaultdict(set)
    for r in rows:
        if len(r) < len(header):
            continue
        d = to_date(r[ix["date"]])
        if not d:
            continue
        t = r[ix["ticker"]]
        for code in r[ix["eventcodes"]].split("|"):
            code = code.strip()
            if not code:
                continue
            s = stats[code]
            s["rows"] += 1
            s["since"] += d >= ITEMS_START
            s["tickers"].add(t)
            s["first"] = d if s["first"] is None or d < s["first"] else s["first"]
            s["last"] = d if s["last"] is None or d > s["last"] else s["last"]
            if t in XCHECK_TICKERS:
                by_ticker[t].add((d, code))
    write_csv("sharadar_event_codes.csv",
              ["code", "as_8k_item", "rows", "rows_since_2004_08_23", "tickers",
               "first", "last"],
              [[c, f"{c[0]}.0{c[1]}" if c.isdigit() and len(c) == 2 else "",
                s["rows"], s["since"], len(s["tickers"]), s["first"], s["last"]]
               for c, s in sorted(stats.items(), key=lambda kv: kv[0])])
    SHARADAR["by_ticker"] = by_ticker
    SHARADAR["code_stats"] = stats
    for etype, items in EVENT_ITEMS.items():
        codes = [item_code(i) for i in items]
        n = sum(stats[c]["since"] for c in codes if c in stats)
        firsts = [stats[c]["first"] for c in codes if c in stats]
        missing = [i for i, c in zip(items, codes) if c not in stats]
        record(etype, "Sharadar 8-K events table (items " + ", ".join(items) + ")",
               "pass" if n >= 30 and not missing else "partial",
               min(firsts) if firsts else "", max((stats[c]["last"] for c in codes if c in stats), default=""),
               "", n, cost="already paid (Sharadar bundle)",
               note=(f"{n:,} item filings since Aug 2004"
                     + (f"; codes not found: {', '.join(missing)}" if missing else "")))


@guarded
def check_sharadar_actions():
    """Sharadar corporate actions table"""
    header, rows = fcd.open_rows(SHARADAR["actions"])
    ix = {h: i for i, h in enumerate(header)}
    notes["sharadar"].append("Actions table columns: " + ", ".join(header))
    types = defaultdict(lambda: [0, None, None])
    divs = defaultdict(list)
    splits = defaultdict(list)
    delisted = {}
    acq_samples = []
    for r in rows:
        if len(r) < len(header):
            continue
        d = to_date(r[ix["date"]])
        a = r[ix["action"]].strip()
        if not d:
            continue
        t = types[a]
        t[0] += 1
        t[1] = d if t[1] is None or d < t[1] else t[1]
        t[2] = d if t[2] is None or d > t[2] else t[2]
        if a == "split":
            splits[r[ix["ticker"]]].append(d)
        if a in ("delisted", "bankruptcyliquidation", "regulatorydelisting",
                 "voluntarydelisting", "acquisitionby", "mergerfrom"):
            delisted[r[ix["ticker"]]] = max(d, delisted.get(r[ix["ticker"]], d))
        if a == "acquisitionby" and d.year >= 2025 and len(acq_samples) < 3:
            acq_samples.append(f"{d} {r[ix['ticker']]} ({r[ix['name']][:30]}) "
                               f"acquisitionby {r[ix['contraticker']]} ({r[ix['contraname']][:30]})")
        if a == "dividend":
            v = to_float(r[ix["value"]]) if "value" in ix else None
            if v:
                divs[r[ix["ticker"]]].append((d, v))
    write_csv("sharadar_actions.csv", ["action", "rows", "first", "last"],
              [[a, n, f, l] for a, (n, f, l) in sorted(types.items(), key=lambda kv: -kv[1][0])])
    # Dividend breaks. A steady payer: its last four payments within 400
    # days, all within 10% of their median, and no split in that window. A
    # cut: the next regular payment at least 25% below that median. A stop:
    # a steady payer with no payment for 200+ days while still listed.
    cuts = stops = 0
    for t, ps in divs.items():
        ps.sort()
        sp = splits.get(t, [])
        for i in range(4, len(ps)):
            d, v = ps[i]
            prior = ps[i - 4:i]
            if (d - prior[0][0]).days > 400:
                continue
            med = statistics.median(x[1] for x in prior)
            if any(abs(x[1] - med) > 0.10 * med for x in prior):
                continue
            if any(prior[0][0] <= s_ <= d for s_ in sp):
                continue
            if 0 < v <= 0.75 * med:
                cuts += 1
        for i in range(4, len(ps) + 1):
            prior = ps[i - 4:i]
            nxt = ps[i][0] if i < len(ps) else min(TODAY, delisted.get(t, TODAY))
            med = statistics.median(x[1] for x in prior)
            steady = ((prior[-1][0] - prior[0][0]).days <= 400 and
                      all(abs(x[1] - med) <= 0.10 * med for x in prior))
            if steady and (nxt - prior[-1][0]).days > 200 and nxt != delisted.get(t):
                stops += 1
    record("Capital structure breaks", "Sharadar corporate actions: dividend history",
           "pass" if cuts >= 30 else "partial",
           types["dividend"][1], types["dividend"][2], types["dividend"][0], cuts + stops,
           cost="already paid (Sharadar bundle)",
           note=(f"{len(divs):,} payers; {cuts:,} cuts of 25% or more by steady payers "
                 f"and {stops:,} stops (200+ days without a payment), splits removed"))
    notes["sharadar"].append("Sample acquisitionby rows (date, ticker, other party): "
                             + "; ".join(acq_samples))

    def tot(names):
        return (sum(types[a][0] for a in names),
                min((types[a][1] for a in names if types[a][1]), default=""),
                max((types[a][2] for a in names if types[a][2]), default=""))
    n, f, l = tot(["acquisitionby", "mergerfrom"])
    record("Mergers and acquisitions",
           "Sharadar corporate actions: completed acquisitions and mergers (target side)",
           "pass" if n >= 30 else "partial", f, l, n, n, cost="already paid (Sharadar bundle)",
           note=(f"acquisitionby {types['acquisitionby'][0]:,} and mergerfrom "
                 f"{types['mergerfrom'][0]:,}, each with the other party's ticker; "
                 f"completion dates, not announcement dates"))
    n, f, l = tot(["bankruptcyliquidation"])
    record("Distress and restructuring", "Sharadar corporate actions: bankruptcy or liquidation delistings",
           "pass" if n >= 30 else "partial", f, l, n, n, cost="already paid (Sharadar bundle)",
           note="the delisting end of a bankruptcy; the filing itself is 8-K item 1.03")
    n, f, l = tot(["regulatorydelisting"])
    record("Accounting and legal trouble", "Sharadar corporate actions: regulatory delistings",
           "pass" if n >= 30 else "partial", f, l, n, n, cost="already paid (Sharadar bundle)",
           note="the delisting itself; the earlier exchange notice is 8-K item 3.01")


@guarded
def check_items_crosscheck():
    """Sharadar 8-K items against SEC's own filing index"""
    ciks, _ = ticker_ciks()
    by_ticker = SHARADAR.get("by_ticker", {})
    out = []
    agree_f = agree_r = total_edgar = total_shar = times = 0
    other_forms = defaultdict(Counter)   # Sharadar code -> SEC forms that day
    owner_forms = Counter()
    for t in XCHECK_TICKERS:
        cik = ciks.get(t)
        if not cik:
            out.append([t, "", "", "", "", "", "", "no CIK in Sharadar tickers"])
            continue
        try:
            sub = json.loads(get(EDGAR_SUBMISSIONS.format(cik=cik)))
        except Exception as e:  # noqa: BLE001
            out.append([t, cik, "", "", "", "", "", str(e)])
            continue
        time.sleep(0.2)
        rec = sub.get("filings", {}).get("recent", {})
        cols = [rec.get(k, []) for k in ("form", "filingDate", "reportDate", "items",
                                         "acceptanceDateTime")]
        edgar_f, edgar_r, lo = set(), set(), None
        forms_on = defaultdict(set)
        end = TODAY - dt.timedelta(days=7)
        for form, fdate, rdate, items, acc in zip(*cols):
            d = to_date(fdate)
            if not d:
                continue
            forms_on[d].add(form)
            if form.startswith(("SC 13", "SCHEDULE 13")):
                owner_forms[form] += 1
            if form != "8-K" or d < dt.date(2015, 1, 1) or d > end:
                continue
            lo = d if lo is None or d < lo else lo
            times += bool(acc)
            rd = to_date(rdate) or d
            for it in str(items).split(","):
                it = it.strip()
                if re.fullmatch(r"\d\.\d\d", it) and it != "9.01":
                    edgar_f.add((d, item_code(it)))
                    edgar_r.add((rd, item_code(it)))
        if lo is None:
            out.append([t, cik, "", "", "", "", "", "no 8-Ks since 2015 in SEC's recent list"])
            continue
        shar = {(d, c) for d, c in by_ticker.get(t, set())
                if lo <= d <= end and c.isdigit() and c != "91"}
        for d, c in shar - edgar_f - edgar_r:
            for f in forms_on.get(d, {"(nothing filed that day)"}):
                other_forms[c][f] += 1
        bf, br = len(edgar_f & shar), len(edgar_r & shar)
        agree_f += bf
        agree_r += br
        total_edgar += len(edgar_f)
        total_shar += len(shar)
        out.append([t, cik, lo, len(edgar_f), len(shar), bf, br,
                    f"{100 * max(bf, br) / len(edgar_f):.0f}% of SEC items found in Sharadar"
                    if edgar_f else ""])
    write_csv("sharadar_vs_edgar_8k.csv",
              ["ticker", "cik", "from", "sec_items", "sharadar_items",
               "match_on_filing_date", "match_on_event_date", "note"], out)
    for c, forms in sorted(other_forms.items(), key=lambda kv: -sum(kv[1].values())):
        notes["sharadar"].append(f"Sharadar code {c} rows with no matching 8-K item: "
                                 + ", ".join(f"{f} {n}" for f, n in forms.most_common(5))
                                 + " (SEC forms that company filed that day)")
    notes["edgar"].append("Ownership filings listed under the 8 companies' own SEC numbers: "
                          + (", ".join(f"{f} {n}" for f, n in owner_forms.most_common())
                             or "none"))
    best = max(agree_f, agree_r)
    rate = best / total_edgar if total_edgar else 0
    record("Company events (all 8-K types)",
           "Cross-check: Sharadar item codes vs SEC filing index, 8 companies since 2015",
           "pass" if rate >= 0.9 else ("partial" if rate >= 0.6 else "fail"),
           "2015-01-01", TODAY, total_edgar, best,
           note=(f"{100 * rate:.0f}% of SEC's (date, item) pairs found in Sharadar "
                 f"({agree_f} on filing date, {agree_r} on event date); Sharadar has "
                 f"{total_shar} pairs; SEC gives the acceptance time for {times} 8-Ks "
                 f"(needed for the after-4 PM rule)"))


# ----------------------------------------------------------------- EDGAR ----

def parse_form_idx(text: str) -> Counter:
    counts = Counter()
    body = False
    for line in text.splitlines():
        if line.startswith("-----"):
            body = True
            continue
        if not body or not line.strip():
            continue
        form = re.split(r"\s{2,}", line.strip())[0]
        counts[form] += 1
    return counts


def fts(params: dict) -> dict:
    """One EDGAR full-text search call; tries without a query word first."""
    last = None
    for q in (None, "*", '"the"'):
        p = dict(params)
        if q:
            p["q"] = q
        try:
            data = json.loads(get(EDGAR_FTS, p, tries=2))
        except Exception as e:  # noqa: BLE001
            last = e
            continue
        if data.get("hits", {}).get("total", {}).get("value", 0) > 0:
            data["_q"] = q or "(none)"
            return data
    if last:
        raise last
    return {"hits": {"total": {"value": 0}, "hits": []}, "_q": "none worked"}


@guarded
def check_edgar_forms():
    """SEC EDGAR: non-8-K forms per quarter"""
    # SEC's quarterly index files are the complete list, from 1993, but
    # www.sec.gov refuses a client that does not name a contact.
    y0, q0 = INDEX_QUARTERS[-1]
    try:
        parse_form_idx(get(EDGAR_INDEX.format(y=y0, q=q0), timeout=300, tries=2)
                       .decode("latin-1"))
        notes["edgar"].append("Quarterly index files (complete list from 1993): readable.")
        index_ok = True
    except Exception as e:  # noqa: BLE001
        notes["edgar"].append(f"Quarterly index files (complete list from 1993): {e}. "
                              "SEC wants a contact in the User-Agent; set the "
                              "SEC_USER_AGENT secret to read them.")
        index_ok = False
    # Full-text search (from 2001) gives counts per form and date range.
    rows = []
    two_ciks = seen_13d = 0
    used_q = set()
    for y, q in INDEX_QUARTERS + [(TODAY.year, (TODAY.month - 1) // 3 + 1)]:
        if y < 2001:
            continue
        start = dt.date(y, 3 * q - 2, 1)
        end = min(TODAY, (dt.date(y + (q == 4), 1 if q == 4 else 3 * q + 1, 1)
                          - dt.timedelta(days=1)))
        row = [f"{y}Q{q}"]
        detail = []
        for etype, forms in FORMS.items():
            n = 0
            for f in forms:
                try:
                    data = fts({"forms": f, "dateRange": "custom",
                                "startdt": start.isoformat(), "enddt": end.isoformat()})
                except Exception as e:  # noqa: BLE001
                    detail.append(f"{f} {e}")
                    continue
                used_q.add(data.get("_q", ""))
                k = data.get("hits", {}).get("total", {}).get("value", 0)
                rel = data.get("hits", {}).get("total", {}).get("relation", "eq")
                n += k
                detail.append(f"{f} {k}{'+' if rel == 'gte' else ''}")
                if "13D" in f:
                    for h in data.get("hits", {}).get("hits", [])[:50]:
                        seen_13d += 1
                        two_ciks += len(set(h.get("_source", {}).get("ciks") or [])) >= 2
                time.sleep(0.15)
            row.append(n)
        rows.append(row + ["; ".join(detail)])
    write_csv("edgar_form_counts.csv", ["quarter"] + list(FORMS) + ["by_form"], rows)
    notes["edgar"].append("Full-text search query word used for form counts: "
                          + ", ".join(sorted(used_q)) + ". Counts of 10,000 show as 10000+ "
                          "(the search caps its totals there).")
    if seen_13d:
        notes["edgar"].append(f"13D subject company: {two_ciks} of {seen_13d} sampled 13D "
                              "hits list two or more SEC numbers (filer and subject), so the "
                              "target can be tied to a stock without opening the filing.")
    got = [r for r in rows if isinstance(r[1], int)]
    labels = {"Activist stakes": "Activist stakes",
              "Mergers (tender offers)": "Mergers and acquisitions",
              "Mergers (merger proxies)": "Mergers and acquisitions",
              "Offerings": "Capital structure breaks",
              "Late filings": "Accounting and legal trouble"}
    for i, (etype, forms) in enumerate(FORMS.items(), start=1):
        if etype not in labels:
            continue
        vals = [r[i] for r in got]
        avg = statistics.mean(vals) if vals else 0
        record(labels[etype], f"SEC EDGAR full-text search: {', '.join(forms)}",
               "pass" if avg >= 30 else "partial", "2001-01-01" if got else "",
               TODAY if got else "", "", f"about {avg:,.0f} a quarter",
               note=(f"{len(got)} sample quarters, 2001 on"
                     + ("; quarterly index files also readable (from 1993)" if index_ok
                        else "; complete index from 1993 needs SEC_USER_AGENT")))


@guarded
def check_fulltext():
    """SEC EDGAR full-text search: CEO and CFO departures in 8-K item 5.02"""
    res = {}
    for role in ("chief executive officer", "chief financial officer"):
        data = json.loads(get(EDGAR_FTS, {"q": f'"{role}" resign', "forms": "8-K",
                                          "dateRange": "custom", "startdt": "2015-01-01",
                                          "enddt": "2015-12-31"}))
        hits = data.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        sample = hits.get("hits", [])
        with_502 = sum(1 for h in sample if "5.02" in (h.get("_source", {}).get("items") or []))
        res[role] = (total, with_502, len(sample))
        time.sleep(0.5)
    earliest = json.loads(get(EDGAR_FTS, {"q": '"chief executive officer" resign',
                                          "forms": "8-K", "dateRange": "custom",
                                          "startdt": "2001-01-01", "enddt": "2001-12-31"}))
    e_total = earliest.get("hits", {}).get("total", {}).get("value", 0)
    ceo = res["chief executive officer"]
    record("Leadership changes",
           "SEC EDGAR full-text search: 8-Ks naming the CEO or CFO with 'resign'",
           "pass" if ceo[0] >= 30 else "partial", "2001-01-01", TODAY, "",
           f"{ceo[0]:,} CEO hits in 2015",
           note=(f"2015: CEO {ceo[0]:,} hits ({ceo[1]} of {ceo[2]} sampled tagged item 5.02), "
                 f"CFO {res['chief financial officer'][0]:,} hits; 2001: {e_total:,} CEO hits "
                 f"(search covers 2001 on)"))


# ---------------------------------------------------------------- report ----

def report():
    write_csv("source_checks.csv", list(checks[0].keys()) if checks else ["status"],
              [list(c.values()) for c in checks])
    write_csv("index_spikes.csv", ["index", "kind", "date", "date_with_data",
                                   "what", "percentile_that_day"], spike_rows)
    lines = [
        "# Event sources check report",
        "",
        f"Run: {TODAY}. One row per candidate source for the 12 agreed event types "
        "(docs/event-types.md). Written by scripts/check_event_sources.py.",
        "",
        "| Event type | Source | Status | First | Last | Events | Cost | Note |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in checks:
        lines.append("| " + " | ".join(str(c[k]).replace("|", "/") for k in
                                       ("event_type", "source", "status", "first", "last",
                                        "events", "cost", "note")) + " |")
    lines += ["", "## Notes", ""]
    for group, items in notes.items():
        for n in items:
            lines.append(f"- **{group}:** {n}")
    stats = SHARADAR.get("code_stats")
    if stats:
        lines += ["", "## Sharadar 8-K codes (all, by rows)", ""]
        for c, s in sorted(stats.items(), key=lambda kv: -kv[1]["rows"]):
            lines.append(f"- {c}: {s['rows']:,} rows, {len(s['tickers']):,} tickers, "
                         f"{s['first']} to {s['last']}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "EVENT_SOURCES_CHECK.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    check_gpr()
    check_tpu()
    check_epu()
    check_elections()
    check_oil()
    check_federal_register()
    try:
        sharadar_tables()
        check_sharadar_events()
        check_sharadar_actions()
        check_items_crosscheck()
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        record("Company events", "Sharadar tables", "fail",
               note=f"{type(e).__name__}: {str(e)[:160]}")
    check_edgar_forms()
    check_fulltext()
    report()
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
