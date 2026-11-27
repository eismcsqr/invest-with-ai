"""Company pillar: the six factor measures and peer percentile ranks.

Runs right after scripts/fetch_company_data.py in the company data workflow,
reading the Sharadar tables it left on the runner (raw/sharadar/*.zip). It
follows docs/company-factors.md (the six factors and the measures for each
group) and docs/company-method.md (percentile ranks within peers, five
reading bands, equal starting weights with a few group tweaks, size floor,
range and confidence). Write-up: docs/company-measures.md.

Point in time: every number is taken only from filings dated (Sharadar's
filing date) on or before the run date, and every price on or before it.
Flow measures use the as-reported trailing twelve months (dimension ART);
nothing restated later (MR dimensions) is used. A truncation test runs the
whole calculation a year back twice, once with all data and once with every
row filed or priced after that date deleted first, and checks the two agree.

What is committed (data/company/measures/): aggregate checks only, because
the repository is public and the Sharadar personal licence does not allow
redistributing its data:

  MEASURES_CHECK_REPORT.md   coverage, missing rates, look-ahead checks,
                             reading and confidence counts, a spot check
  measure_coverage.csv       per detailed group and measure: companies,
                             share with a value, peers used, fallbacks
  factor_coverage.csv        per detailed group and factor: share with a
                             reading, reading bands, confidence labels

The full per-company file (every measure, percentile, reading, score, range
and confidence) is written to raw/company_results/, which stays on the
runner.

Standard library only.

Run: python scripts/company_measures.py [--asof YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import math
import statistics
import sys
import time
import zipfile
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw" / "sharadar"
OUT = ROOT / "data" / "company" / "measures"
RESULTS = ROOT / "raw" / "company_results"

STALE_DAYS = 200            # a filing older than this counts as missing
LISTED_DAYS = 7             # a price within a week before the date = listed
MIN_PEERS = 10
GOOD_PEERS = 20             # confidence check 2
SIZE_FLOOR = 0.2            # smallest fifth by market value left out of peers
SURPRISE_DAYS = 200         # latest results day must be this recent
PEER_SURPRISE_DAYS = 365    # peers' results-day moves from the past year
INSIDER_DAYS = 182
HOLDINGS_LAG = 46           # 13F holdings usable 46 days after quarter end
MIN_HOLDING_COMPANIES = 1000  # a holdings quarter needs this many companies
HISTORY_YEARS = 7           # fundamentals kept for lags (3 years back + test)
PRICE_DAYS = 1100           # prices kept (year-back test needs ~2.7 years)

FACTORS = ["growth", "profitability", "balance", "capital", "surprise", "owner"]
FACTOR_NAMES = {"growth": "Growth", "profitability": "Profitability",
                "balance": "Balance sheet", "capital": "Capital use",
                "surprise": "Earnings surprise", "owner": "Owner signals"}
BANDS = [(80, 1.0), (60, 0.5), (40, 0.0), (20, -0.5), (-1, -1.0)]
CHECK_FILE = ROOT / "data" / "company" / "check" / "factor_check.csv"
CONF_ORDER = {"Low": 0, "Medium": 1, "High": 2}


def load_check() -> tuple[set, str]:
    """(factor, broad group) pairs that pass the measured check, from the
    latest committed check (scripts/company_check.py), and its run date."""
    if not CHECK_FILE.exists():
        return set(), ""
    passed, run_date = set(), ""
    with CHECK_FILE.open(newline="") as f:
        for r in csv.DictReader(f):
            run_date = r.get("check_run", run_date)
            if r.get("passes") == "Y":
                passed.add((r["factor"], r["broad_group"]))
    return passed, run_date

# French's 12 broad groups from SIC codes (his Siccodes12 definitions).
SIC12 = [
    ("NoDur", [(100, 999), (2000, 2399), (2700, 2749), (2770, 2799),
               (3100, 3199), (3940, 3989)]),
    ("Durbl", [(2500, 2519), (2590, 2599), (3630, 3659), (3710, 3711),
               (3714, 3714), (3716, 3716), (3750, 3751), (3792, 3792),
               (3900, 3939), (3990, 3999)]),
    ("Manuf", [(2520, 2589), (2600, 2699), (2750, 2769), (3000, 3099),
               (3200, 3569), (3580, 3629), (3700, 3709), (3712, 3713),
               (3715, 3715), (3717, 3749), (3752, 3791), (3793, 3799),
               (3830, 3839), (3860, 3899)]),
    ("Enrgy", [(1200, 1399), (2900, 2999)]),
    ("Chems", [(2800, 2829), (2840, 2899)]),
    ("BusEq", [(3570, 3579), (3660, 3692), (3694, 3699), (3810, 3829),
               (7370, 7379)]),
    ("Telcm", [(4800, 4899)]),
    ("Utils", [(4900, 4949)]),
    ("Shops", [(5000, 5999), (7200, 7299), (7600, 7699)]),
    ("Hlth", [(2830, 2839), (3693, 3693), (3840, 3859), (8000, 8099)]),
    ("Money", [(6000, 6999)]),
]


def broad_group(sic: str) -> str:
    try:
        code = int(float(sic))
    except (ValueError, TypeError):
        return "Other"
    for name, ranges in SIC12:
        if any(a <= code <= b for a, b in ranges):
            return name
    return "Other"


# Exposure (weight) per factor: 2 everywhere, with the agreed group tweaks
# (company-method.md section 7). Banks and insurers raise capital and credit.
def exposures(broad: str, version: str) -> dict:
    w = {f: 2 for f in FACTORS}
    tweaks = {"Utils": {"balance": 3, "growth": 1}, "Telcm": {"balance": 3},
              "Enrgy": {"balance": 3, "capital": 3},
              "BusEq": {"growth": 3, "balance": 1}, "Hlth": {"growth": 3},
              "NoDur": {"profitability": 3}, "Shops": {"profitability": 3}}
    w.update(tweaks.get(broad, {}))
    if version in ("bank", "insurer"):
        w["balance"] = 3
    return w


# ------------------------------------------------------------------ reading --

def open_rows(path: Path):
    if zipfile.is_zipfile(path):
        zf = zipfile.ZipFile(path)
        csvs = [i for i in zf.infolist() if i.filename.lower().endswith(".csv")]
        name = (max(csvs, key=lambda i: i.file_size).filename if csvs
                else zf.namelist()[0])
        f = io.TextIOWrapper(zf.open(name), encoding="utf-8", newline="")
    else:
        f = path.open(encoding="utf-8", newline="")
    reader = csv.reader(f)
    header = [h.strip().lower() for h in next(reader)]
    return header, reader


def find_table(*names: str) -> Path | None:
    for n in names:
        for ext in (".zip", ".csv"):
            p = RAW / f"{n}{ext}"
            if p.exists():
                return p
    return None


def d2o(s: str) -> int | None:
    try:
        return dt.date.fromisoformat(s[:10]).toordinal()
    except (ValueError, TypeError):
        return None


def num(s: str) -> float | None:
    if s is None or s == "":
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


FUND_FIELDS = ["revenue", "netinc", "equity", "assets", "intangibles", "debt",
               "debtc", "cashneq", "ebit", "ebitda", "intexp", "opinc", "gp",
               "cor", "inventory", "invcap", "ncfo", "fcf", "capex", "depamor",
               "ncfdiv", "ncfcommon", "sbcomp", "rnd", "deferredrev",
               "deposits", "opex", "liabilities", "sharesbas", "marketcap",
               "payoutratio"]


FIX = {f: i for i, f in enumerate(FUND_FIELDS)}
NAN = float("nan")


class FRow:
    """One filing's fields, stored compactly (the measured check loads every
    filing since 1998, so a dict per row would use several gigabytes)."""
    __slots__ = ("a",)

    def __init__(self, values: dict):
        a = array("d", [NAN]) * len(FUND_FIELDS)
        for f, v in values.items():
            if v is not None:
                a[FIX[f]] = v
        self.a = a

    def get(self, field, default=None):
        i = FIX.get(field)
        if i is None:
            return default
        x = self.a[i]
        return default if x != x else x


class Data:
    """Everything the measures need, cut to a window around the run date."""

    def __init__(self):
        self.info = {}            # ticker -> dict(group, broad, version, ...)
        self.art = defaultdict(list)   # ticker -> [(cal, filed, {field: v})]
        self.arq = defaultdict(list)   # ticker -> [(cal, filed, rev, opinc)]
        self.px_d = {}            # ticker -> array of date ordinals
        self.px_c = {}            # ticker -> array of split-adjusted closes
        self.results = defaultdict(list)  # ticker -> sorted results-day ordinals
        self.insiders = defaultdict(list)  # ticker -> [(filed, net shares)]
        self.holdings = defaultdict(dict)  # ticker -> {quarter end: units}
        self.insider_days = []    # every filing date in the insider table
        self.holding_qs = {}      # quarter end -> companies with holdings
        self.notes = []
        self.split_note = ""

    def truncated(self, asof: int) -> "Data":
        """A copy holding only what was filed or priced by asof."""
        t = Data()
        t.info = self.info
        for k, rows in self.art.items():
            t.art[k] = [r for r in rows if r[1] <= asof]
        for k, rows in self.arq.items():
            t.arq[k] = [r for r in rows if r[1] <= asof]
        for k, ds in self.px_d.items():
            n = bisect_right(ds, asof)
            t.px_d[k] = ds[:n]
            t.px_c[k] = self.px_c[k][:n]
        for k, ds in self.results.items():
            t.results[k] = [d for d in ds if d <= asof]
        for k, rows in self.insiders.items():
            t.insiders[k] = [r for r in rows if r[0] <= asof]
        for k, qs in self.holdings.items():
            t.holdings[k] = {q: u for q, u in qs.items()
                             if q + HOLDINGS_LAG <= asof}
        t.insider_days = self.insider_days[:bisect_right(self.insider_days, asof)]
        t.holding_qs = {q: n for q, n in self.holding_qs.items()
                        if q + HOLDINGS_LAG <= asof}
        return t


def load(today: int, start: int | None = None) -> Data:
    """Read the tables. By default only the window the weekly run needs;
    `start` (a date ordinal) keeps everything from that date on instead,
    for the measured check's history runs."""
    data = Data()
    fund_start = start if start is not None else today - 366 * HISTORY_YEARS
    px_start = start if start is not None else today - PRICE_DAYS
    tick_p = find_table("tickers")
    fund_p = find_table("fundamentals", "sf1")
    if not tick_p or not fund_p:
        raise SystemExit("tickers and fundamentals tables are needed in raw/sharadar/.")

    t0 = time.time()
    header, rows = open_rows(tick_p)
    ix = {h: i for i, h in enumerate(header)}
    for r in rows:
        if len(r) < len(header):
            continue
        if r[ix["table"]].strip().lower() not in ("fundamentals", "sf1"):
            continue
        cat = r[ix["category"]].strip().lower()
        if ("common" not in cat or "secondary" in cat or "warrant" in cat
                or "preferred" in cat):
            continue
        group = r[ix["famaindustry"]].strip()
        broad = broad_group(r[ix["siccode"]])
        version = ("bank" if group == "Banking" else
                   "insurer" if group == "Insurance" else "standard")
        data.info[r[ix["ticker"]]] = {"group": group or "(none)", "broad": broad,
                                      "version": version, "category": cat,
                                      "name": r[ix["name"]]}
    print(f"tickers: {len(data.info):,} common stocks in {time.time() - t0:,.0f}s")

    t0 = time.time()
    start_cal = fund_start
    header, rows = open_rows(fund_p)
    ix = {h: i for i, h in enumerate(header)}
    i_key = ix.get("datekey", ix.get("date"))
    i_t, i_dim, i_cal = ix["ticker"], ix["dimension"], ix["calendardate"]
    fields = [(f, ix[f]) for f in FUND_FIELDS if f in ix]
    missing = [f for f in FUND_FIELDS if f not in ix]
    if missing:
        data.notes.append(f"Fundamentals columns not found: {', '.join(missing)}.")
    i_rev, i_op = ix.get("revenue"), ix.get("opinc")
    for r in rows:
        if len(r) < len(header):
            continue
        dim = r[i_dim]
        if dim not in ("ART", "ARQ"):
            continue
        t = r[i_t]
        if t not in data.info:
            continue
        cal, filed = d2o(r[i_cal]), d2o(r[i_key])
        if cal is None or filed is None or cal < start_cal:
            continue
        if dim == "ART":
            data.art[t].append((cal, filed, FRow({f: num(r[i]) for f, i in fields})))
        else:
            data.arq[t].append((cal, filed, num(r[i_rev]) if i_rev is not None else None,
                                num(r[i_op]) if i_op is not None else None))
    for store in (data.art, data.arq):
        for t, rs in store.items():
            # One row per period: the first filed (as first reported).
            best = {}
            for row in rs:
                if row[0] not in best or row[1] < best[row[0]][1]:
                    best[row[0]] = row
            store[t] = sorted(best.values(), key=lambda x: x[0])
    print(f"fundamentals: {sum(map(len, data.art.values())):,} ART rows "
          f"in {time.time() - t0:,.0f}s")

    sep = find_table("stocks", "sep")
    if sep:
        t0 = time.time()
        start = px_start
        header, rows = open_rows(sep)
        ix = {h: i for i, h in enumerate(header)}
        i_t, i_d, i_c = ix["ticker"], ix["date"], ix["close"]
        tmp_d, tmp_c = defaultdict(lambda: array("i")), defaultdict(lambda: array("d"))
        for r in rows:
            if len(r) < len(header):
                continue
            t = r[i_t]
            if t not in data.info:
                continue
            d = d2o(r[i_d])
            c = num(r[i_c])
            if d is None or d < start or c is None or c <= 0:
                continue
            tmp_d[t].append(d)
            tmp_c[t].append(c)
        for t in tmp_d:
            order = sorted(range(len(tmp_d[t])), key=tmp_d[t].__getitem__)
            data.px_d[t] = array("i", (tmp_d[t][i] for i in order))
            data.px_c[t] = array("d", (tmp_c[t][i] for i in order))
        print(f"prices: {len(data.px_d):,} tickers in {time.time() - t0:,.0f}s")
    else:
        data.notes.append("Daily prices not found: market value, yields and "
                          "earnings surprise can't be computed.")

    ev = find_table("events")
    if ev:
        header, rows = open_rows(ev)
        ix = {h: i for i, h in enumerate(header)}
        start = px_start
        for r in rows:
            if len(r) < len(header) or r[ix["ticker"]] not in data.info:
                continue
            codes = {c.strip() for c in r[ix["eventcodes"]].split("|")}
            if "22" not in codes:       # 8-K item 2.02, results of operations
                continue
            d = d2o(r[ix["date"]])
            if d is not None and d >= start:
                data.results[r[ix["ticker"]]].append(d)
        for t in data.results:
            data.results[t] = sorted(set(data.results[t]))
    else:
        data.notes.append("8-K events not found: results days fall back to "
                          "quarterly filing dates.")

    load_insiders(data, px_start)
    load_holdings(data, px_start)
    return data


def load_insiders(data: Data, start: int) -> None:
    p = find_table("insiders", "sf2")
    if not p:
        data.notes.append("Insider trades not downloaded: insider buying is missing.")
        return
    header, rows = open_rows(p)
    ix = {h: i for i, h in enumerate(header)}
    if "filingdate" not in ix and "date" in ix:
        ix["filingdate"] = ix["date"]      # the direct API calls it "date"
    need = ["ticker", "filingdate", "transactioncode", "transactionshares"]
    if any(c not in ix for c in need):
        data.notes.append("Insider table columns not recognised ("
                          + ", ".join(header[:15]) + "...): insider buying is missing.")
        return
    i_sec = ix.get("securityadcode")
    i_form = ix.get("formtype")
    n = total = 0
    first = last = ""
    codes = Counter()
    days = set()
    for r in rows:
        if len(r) < len(header):
            continue
        total += 1
        fd = r[ix["filingdate"]][:10]
        days.add(fd)
        first = min(first, fd) if first else fd
        last = max(last, fd)
        codes[r[ix["transactioncode"]].strip().upper()] += 1
        if r[ix["ticker"]] not in data.info:
            continue
        code = r[ix["transactioncode"]].strip().upper()
        if code not in ("P", "S"):          # open-market buys and sales only
            continue
        if i_sec is not None and r[i_sec].strip().upper() not in ("", "ND", "N"):
            continue                         # non-derivative securities only
        if i_form is not None and r[i_form].strip() not in ("", "4", "4/A"):
            continue
        d = d2o(r[ix["filingdate"]])
        sh = num(r[ix["transactionshares"]])
        if d is None or sh is None or d < start:
            continue
        data.insiders[r[ix["ticker"]]].append((d, abs(sh) if code == "P" else -abs(sh)))
        n += 1
    data.insider_days = sorted(o for o in (d2o(x) for x in days) if o is not None)
    data.notes.append(f"Insider trades: {total:,} rows filed {first} to {last} "
                      f"(codes: {', '.join(f'{k} {v:,}' for k, v in codes.most_common(6))}); "
                      f"{n:,} open-market buys and sales kept.")


def load_holdings(data: Data, start: int) -> None:
    p = find_table("holdings", "sf3")
    if not p:
        data.notes.append("Institutional holdings not downloaded: change in "
                          "institutional ownership is missing.")
        return
    header, rows = open_rows(p)
    ix = {h: i for i, h in enumerate(header)}
    if "calendardate" not in ix and "date" in ix:
        ix["calendardate"] = ix["date"]    # quarter end, "date" in the direct API
    if any(c not in ix for c in ("ticker", "calendardate", "units")):
        data.notes.append("Holdings table columns not recognised ("
                          + ", ".join(header[:15]) + "...): institutional change is missing.")
        return
    i_type = ix.get("securitytype")
    agg = defaultdict(float)
    total = 0
    quarters = Counter()
    for r in rows:
        if len(r) < len(header):
            continue
        total += 1
        quarters[r[ix["calendardate"]][:10]] += 1
        if r[ix["ticker"]] not in data.info:
            continue
        if i_type is not None and r[i_type].strip().upper() not in ("SHR", ""):
            continue
        q = d2o(r[ix["calendardate"]])
        u = num(r[ix["units"]])
        if q is None or u is None or q < start:
            continue
        agg[(r[ix["ticker"]], q)] += u
    per_q = Counter()
    for (t, q), u in agg.items():
        data.holdings[t][q] = u
        per_q[q] += 1
    data.holding_qs = dict(per_q)
    data.notes.append(f"Institutional holdings: {total:,} rows (by quarter: "
                      + ", ".join(f"{q} {c:,}" for q, c in sorted(quarters.items())[-6:])
                      + f"); {len(agg):,} company-quarters kept.")


# ------------------------------------------------------------------- prices --

def close_on(data: Data, t: str, day: int) -> tuple[int, float] | None:
    ds = data.px_d.get(t)
    if not ds:
        return None
    i = bisect_right(ds, day) - 1
    if i < 0:
        return None
    return ds[i], data.px_c[t][i]


def daily_returns(data: Data, t: str, lo: int | None = None,
                  hi: int | None = None) -> dict:
    """Daily returns by date, optionally only for days in [lo, hi]."""
    ds, cs = data.px_d.get(t), data.px_c.get(t)
    if not ds:
        return {}
    a = 1 if lo is None else max(1, bisect_left(ds, lo))
    b = len(ds) if hi is None else bisect_right(ds, hi)
    return {ds[i]: cs[i] / cs[i - 1] - 1 for i in range(a, b)
            if ds[i] - ds[i - 1] <= 5}


# ----------------------------------------------------------------- measures --

def safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


class Ctx:
    """One company's point-in-time rows."""

    def __init__(self, data: Data, t: str, asof: int):
        self.t = t
        self.asof = asof
        rows = [r for r in data.art.get(t, []) if r[1] <= asof]
        self.by_cal = {r[0]: r for r in rows}
        self.cur = rows[-1] if rows else None
        self.fresh = bool(self.cur) and asof - self.cur[1] <= STALE_DAYS
        self.arq = [r for r in data.arq.get(t, []) if r[1] <= asof]
        self.data = data
        self.used_dates = []        # every filing / price date used (look-ahead check)

    def row(self, lag: int):
        """The ART row `lag` years before the latest, filed by asof."""
        if not self.cur:
            return None
        cal = dt.date.fromordinal(self.cur[0])
        try:
            target = cal.replace(year=cal.year - lag).toordinal()
        except ValueError:          # Feb 29
            target = (cal.replace(day=28, year=cal.year - lag)).toordinal()
        r = self.by_cal.get(target)
        if r is None:
            for d in (target - 3, target + 3, target - 6, target + 6):
                r = self.by_cal.get(d)
                if r:
                    break
        if r:
            self.used_dates.append(r[1])
        return r

    def v(self, lag: int, field: str):
        r = self.row(lag)
        return r[2].get(field) if r else None

    def price(self, day: int):
        p = close_on(self.data, self.t, day)
        if p:
            self.used_dates.append(p[0])
        return p

    def mcap(self, lag: int):
        """Market value: at the run date for lag 0, at filing for older rows."""
        r = self.row(lag)
        if not r or r[2].get("marketcap") is None:
            return None
        m = r[2].get("marketcap")
        if lag > 0:
            return m
        then, now = self.price(r[1]), self.price(self.asof)
        if not then or not now:
            return None
        return m * now[1] / then[1]

    def share_ratio(self, lag: int):
        """Shares now ÷ shares a year before `lag`, safe through splits."""
        a, b = self.row(lag), self.row(lag + 1)
        if not a or not b:
            return None
        ma, mb = a[2].get("marketcap"), b[2].get("marketcap")
        pa, pb = self.price(a[1]), self.price(b[1])
        if ma and mb and pa and pb and ma > 0 and mb > 0:
            return (ma / mb) / (pa[1] / pb[1])
        sa, sb = a[2].get("sharesbas"), b[2].get("sharesbas")
        return safe_div(sa, sb) if sa and sb and sb > 0 else None


def growth(c, lag, f):
    a, b = c.v(lag, f), c.v(lag + 1, f)
    if a is None or b is None or b <= 0:
        return None
    return a / b - 1


def m_rev_growth(c, lag):
    return growth(c, lag, "revenue")


def m_rev_accel(c, lag):
    a, b = growth(c, lag, "revenue"), growth(c, lag + 1, "revenue")
    return None if a is None or b is None else a - b


def m_earn_growth(c, lag):
    a, b, m = c.v(lag, "netinc"), c.v(lag + 1, "netinc"), c.mcap(lag + 1)
    if a is None or b is None or not m or m <= 0:
        return None
    return (a - b) / m


def m_deferred_growth(c, lag):
    return growth(c, lag, "deferredrev")


def m_deposit_growth(c, lag):
    return growth(c, lag, "deposits")


def tbv(c, lag):
    e, i = c.v(lag, "equity"), c.v(lag, "intangibles") or 0
    return None if e is None else e - i


def m_tbvps_growth(c, lag):
    a, b, s = tbv(c, lag), tbv(c, lag + 1), c.share_ratio(lag)
    if a is None or b is None or b <= 0 or not s or s <= 0:
        return None
    return (a / b) / s - 1


def m_roe(c, lag):
    ni, e0, e1 = c.v(lag, "netinc"), c.v(lag, "equity"), c.v(lag + 1, "equity")
    if ni is None or e0 is None or e0 <= 0:
        return None
    avg = (e0 + e1) / 2 if e1 and e1 > 0 else e0
    return ni / avg


def m_roa(c, lag):
    ni, a0, a1 = c.v(lag, "netinc"), c.v(lag, "assets"), c.v(lag + 1, "assets")
    if ni is None or not a0 or a0 <= 0:
        return None
    return ni / ((a0 + a1) / 2 if a1 and a1 > 0 else a0)


def ratio_rev(c, lag, f):
    rev = c.v(lag, "revenue")
    if not rev or rev <= 0:
        return None
    x = c.v(lag, f)
    return None if x is None else x / rev


def m_op_margin(c, lag):
    return ratio_rev(c, lag, "opinc")


def m_gross_margin(c, lag):
    return ratio_rev(c, lag, "gp")


def m_ebitda_margin(c, lag):
    return ratio_rev(c, lag, "ebitda")


def m_efficiency(c, lag):
    return ratio_rev(c, lag, "opex")


def m_rnd_share(c, lag):
    return ratio_rev(c, lag, "rnd")


def m_sbc_share(c, lag):
    return ratio_rev(c, lag, "sbcomp")


def m_capex_rev(c, lag):
    x = ratio_rev(c, lag, "capex")
    return None if x is None else abs(x)


def m_roic(c, lag):
    e, k = c.v(lag, "ebit"), c.v(lag, "invcap")
    if e is None or not k or k <= 0:
        return None
    return e / k


def m_incr_margin(c, lag):
    r0, r1 = c.v(lag, "revenue"), c.v(lag + 1, "revenue")
    o0, o1 = c.v(lag, "opinc"), c.v(lag + 1, "opinc")
    if None in (r0, r1, o0, o1) or not r0 or abs(r0 - r1) < 0.01 * abs(r0):
        return None
    return (o0 - o1) / (r0 - r1)


def m_margin_stability(c, lag):
    if lag:
        return None
    qs = [r for r in c.arq if r[2] and r[2] > 0 and r[3] is not None][-12:]
    if len(qs) < 8:
        return None
    for r in qs:
        c.used_dates.append(r[1])
    return statistics.pstdev([r[3] / r[2] for r in qs])


def m_net_debt_ebitda(c, lag):
    debt, cash, ebitda = c.v(lag, "debt"), c.v(lag, "cashneq"), c.v(lag, "ebitda")
    eq = c.v(lag, "equity")
    if debt is None or ebitda is None:
        return None
    nd = debt - (cash or 0)
    if eq is not None and eq < 0:
        return 1e9                  # negative equity: bottom rank on leverage
    if ebitda <= 0:
        return 1e9 if nd > 0 else None
    return nd / ebitda


def m_interest_cover(c, lag):
    ebit, ie, debt = c.v(lag, "ebit"), c.v(lag, "intexp"), c.v(lag, "debt")
    if ebit is None:
        return None
    if (not ie or ie <= 0):
        return 1e9 if debt == 0 else None   # no debt: top rank
    return ebit / ie


def m_short_debt(c, lag):
    debt, dc = c.v(lag, "debt"), c.v(lag, "debtc")
    if debt is None:
        return None
    if debt == 0:
        return 0.0
    return None if dc is None or debt < 0 else dc / debt


def m_inventory_turns(c, lag):
    cor, i0, i1 = c.v(lag, "cor"), c.v(lag, "inventory"), c.v(lag + 1, "inventory")
    if cor is None or not i0 or i0 <= 0:
        return None
    avg = (i0 + i1) / 2 if i1 and i1 > 0 else i0
    return cor / avg


def m_cash_runway(c, lag):
    cash, ncfo = c.v(lag, "cashneq"), c.v(lag, "ncfo")
    if cash is None or ncfo is None:
        return None
    if ncfo >= 0:
        return 99.0                 # not burning cash: top rank
    return cash / -ncfo


def m_payout_yield(c, lag):
    m = c.mcap(lag)
    if not m or m <= 0:
        return None
    div, buy = c.v(lag, "ncfdiv") or 0, c.v(lag, "ncfcommon") or 0
    return -(div + buy) / m


def m_share_change(c, lag):
    s = c.share_ratio(lag)
    return None if s is None or s <= 0 else s - 1


def m_fcf_yield(c, lag):
    m, f = c.mcap(lag), c.v(lag, "fcf")
    return None if not m or m <= 0 or f is None else f / m


def m_tangible_equity(c, lag):
    a, i = c.v(lag, "assets"), c.v(lag, "intangibles") or 0
    e = tbv(c, lag)
    if e is None or not a or a - i <= 0:
        return None
    return e / (a - i)


def m_debt_equity(c, lag):
    d, e = c.v(lag, "debt"), c.v(lag, "equity")
    if d is None or e is None:
        return None
    return 1e9 if e <= 0 else d / e


def m_capex_depr(c, lag):
    cap, dep = c.v(lag, "capex"), c.v(lag, "depamor")
    return None if cap is None or not dep or dep <= 0 else abs(cap) / dep


def m_reinvest(c, lag):
    cap, cfo = c.v(lag, "capex"), c.v(lag, "ncfo")
    return None if cap is None or not cfo or cfo <= 0 else abs(cap) / cfo


def m_payout_ratio(c, lag):
    div, ni = c.v(lag, "ncfdiv"), c.v(lag, "netinc")
    return None if div is None or not ni or ni <= 0 else -div / ni


class M:
    def __init__(self, key, factor, label, fn, direction=1, trend=True,
                 core=False, scored=True, where=None, signed=False):
        self.key, self.factor, self.label, self.fn = key, factor, label, fn
        # Signed: zero means "nothing happened" and reads neutral (50th
        # percentile); positive values rank among positives (50 to 100) and
        # negative among negatives (0 to 50).
        self.signed = signed
        self.direction, self.trend, self.core = direction, trend, core
        self.scored, self.where = scored, where   # where: predicate on info
        # Core and generic measures fall back to the broad group when the
        # detailed group is too small; group-specific ones don't.
        self.fallback = core or where is None or where is std


def std(info):
    return info["version"] == "standard"


def broad_in(*groups):
    return lambda info: info["version"] == "standard" and info["broad"] in groups


def version_is(*vs):
    return lambda info: info["version"] in vs


MEASURES = [
    # Growth
    M("rev_growth", "growth", "Revenue growth", m_rev_growth, trend=False, core=True),
    M("rev_accel", "growth", "Change in revenue growth", m_rev_accel, trend=False),
    M("earn_growth", "growth", "Earnings change ÷ market value", m_earn_growth,
      trend=False, where=std),
    M("deferred_growth", "growth", "Deferred revenue growth", m_deferred_growth,
      trend=False, where=broad_in("BusEq")),
    M("deposit_growth", "growth", "Deposit growth", m_deposit_growth, trend=False,
      where=version_is("bank")),
    M("tbvps_growth", "growth", "Tangible book per share growth", m_tbvps_growth,
      trend=False, where=version_is("bank", "insurer")),
    # Profitability
    M("roe", "profitability", "Return on equity", m_roe, core=True),
    M("op_margin", "profitability", "Operating margin", m_op_margin, where=std),
    M("roic", "profitability", "Return on invested capital", m_roic, where=std),
    M("margin_stability", "profitability", "Operating margin swings (3 years)",
      m_margin_stability, direction=-1, trend=False, where=std),
    M("gross_margin", "profitability", "Gross margin", m_gross_margin,
      where=broad_in("NoDur", "Durbl", "BusEq", "Shops", "Chems")),
    M("incr_margin", "profitability", "Incremental margin", m_incr_margin,
      trend=False, where=broad_in("Manuf")),
    M("ebitda_margin", "profitability", "EBITDA margin", m_ebitda_margin,
      where=broad_in("Telcm")),
    M("roa", "profitability", "Return on assets", m_roa, where=version_is("bank")),
    M("efficiency", "profitability", "Efficiency ratio (costs ÷ revenue)",
      m_efficiency, direction=-1, where=version_is("bank")),
    # Balance sheet / capital and credit
    M("net_debt_ebitda", "balance", "Net debt ÷ EBITDA", m_net_debt_ebitda,
      direction=-1, where=std),
    M("interest_cover", "balance", "Interest cover", m_interest_cover, where=std),
    M("short_debt", "balance", "Share of debt due within a year", m_short_debt,
      direction=-1, trend=False, where=std),
    M("inventory_turns", "balance", "Inventory turns", m_inventory_turns,
      where=broad_in("NoDur", "Durbl", "Shops", "BusEq")),
    M("cash_runway", "balance", "Cash runway (years of cash burn)", m_cash_runway,
      trend=False, where=broad_in("Hlth")),
    M("tangible_equity", "balance", "Tangible equity ÷ tangible assets",
      m_tangible_equity, where=version_is("bank", "insurer")),
    M("debt_equity", "balance", "Debt ÷ equity", m_debt_equity, direction=-1,
      where=version_is("insurer")),
    # Capital use
    M("payout_yield", "capital", "Total payout yield (dividends + buybacks)",
      m_payout_yield, core=True),
    M("share_change", "capital", "Change in share count", m_share_change,
      direction=-1, trend=False, core=True),
    M("fcf_yield", "capital", "Free cash flow yield", m_fcf_yield, where=std),
    M("sbc_share", "capital", "Share-based pay ÷ revenue", m_sbc_share,
      direction=-1, where=broad_in("BusEq")),
    # Computed but not scored: which way is better isn't settled
    M("rnd_share", "profitability", "R&D ÷ revenue", m_rnd_share, scored=False,
      where=broad_in("BusEq", "Hlth")),
    M("capex_depr", "capital", "Capex ÷ depreciation", m_capex_depr, scored=False,
      where=broad_in("Manuf")),
    M("reinvest_rate", "capital", "Reinvestment rate (capex ÷ operating cash)",
      m_reinvest, scored=False, where=broad_in("Enrgy")),
    M("capex_rev", "capital", "Capex ÷ revenue", m_capex_rev, scored=False,
      where=broad_in("Telcm")),
    M("payout_ratio", "capital", "Dividend payout ratio", m_payout_ratio,
      scored=False, where=broad_in("Utils")),
    # Market-based measures, filled in by their own functions below
    M("results_move", "surprise", "Results-day move beyond peers", None,
      trend=False, core=True),
    M("insider_buying", "owner", "Net insider buying, 6 months", None,
      trend=False, core=True, signed=True),
    M("inst_change", "owner", "Change in institutional ownership", None,
      trend=False, core=True),
]
BY_KEY = {m.key: m for m in MEASURES}


def applies(m: M, info: dict) -> bool:
    return m.where is None or m.where(info)


# ------------------------------------------------------------ market based --

def results_moves(data: Data, asof: int, universe: dict, peer_sets: dict) -> dict:
    """Latest results-day move beyond peers ÷ normal daily volatility."""
    # Median daily return of each detailed group's peer set, by day.
    # Only the days the moves need: peers' results days from the past year
    # and the 60 trading days before each (well inside 160 calendar days).
    lo = asof - PEER_SURPRISE_DAYS - 160
    rets = {t: daily_returns(data, t, lo, asof) for t in universe}
    by_group_day = defaultdict(lambda: defaultdict(list))
    for t, info in universe.items():
        if not info["peer"]:
            continue
        for d, r in rets[t].items():
            by_group_day[info["group"]][d].append(r)
    med = {g: {d: statistics.median(v) for d, v in days.items() if len(v) >= 5}
           for g, days in by_group_day.items()}
    out = {}
    for t, info in universe.items():
        ds = data.px_d.get(t)
        gm = med.get(info["group"], {})
        if not ds or not gm:
            continue
        # Results days known by asof; quarterly filing dates when there are none.
        days = [d for d in data.results.get(t, []) if d <= asof]
        if not days:
            days = sorted({r[1] for r in data.arq.get(t, []) if r[1] <= asof})
        days = [d for d in days if d >= asof - PEER_SURPRISE_DAYS]
        if not days:
            continue
        ev = days[-1]
        i = bisect_right(ds, ev - 1)      # first trading day on or after ev
        if i < 61 or i + 1 >= len(ds) or ds[i + 1] > asof:
            continue
        r_t, r_t1 = rets[t].get(ds[i]), rets[t].get(ds[i + 1])
        g_t, g_t1 = gm.get(ds[i]), gm.get(ds[i + 1])
        if None in (r_t, r_t1, g_t, g_t1):
            continue
        excess = (1 + r_t) * (1 + r_t1) - (1 + g_t) * (1 + g_t1)
        hist = [rets[t][ds[j]] - gm[ds[j]] for j in range(i - 61, i - 1)
                if ds[j] in rets[t] and ds[j] in gm]
        if len(hist) < 40:
            continue
        vol = statistics.pstdev(hist)
        if vol <= 0:
            continue
        out[t] = (excess / (vol * math.sqrt(2)), ev, ds[i + 1])
    return out


def insider_coverage(data: Data, asof: int) -> str:
    """Empty if the insider table covers the 6 months to asof, else why not."""
    days = [d for d in data.insider_days if d <= asof]
    if not days:
        return "no insider filings by the run date"
    first, last = days[0], days[-1]
    if first > asof - INSIDER_DAYS or last < asof - 14:
        return (f"insider filings cover only {dt.date.fromordinal(first)} to "
                f"{dt.date.fromordinal(last)}, not the 6 months to the run date")
    return ""


def complete_quarters(data: Data, asof: int) -> list[int]:
    """Quarters known by asof that hold most companies (half the best quarter)."""
    qs = {q: n for q, n in data.holding_qs.items() if q + HOLDINGS_LAG <= asof}
    if not qs or max(qs.values()) < MIN_HOLDING_COMPANIES:
        return []
    top = max(qs.values())
    return sorted(q for q, n in qs.items() if n >= top / 2)


def holdings_coverage(data: Data, asof: int) -> str:
    qs = complete_quarters(data, asof)
    if len(qs) < 2 or qs[-1] - qs[-2] > 100 or asof - qs[-1] > STALE_DAYS:
        known = sorted(q for q in data.holding_qs if q + HOLDINGS_LAG <= asof)
        return ("institutional holdings don't have two complete recent quarters "
                f"({len(known)} quarter(s) known, {len(qs)} complete)")
    return ""


def insider_buying(data: Data, asof: int, t: str, shares: float | None):
    rows = [s for d, s in data.insiders.get(t, []) if asof - INSIDER_DAYS < d <= asof]
    if not shares or shares <= 0:
        return None
    return sum(rows) / shares


def inst_change(data: Data, asof: int, t: str, shares: float | None,
                quarters: list[int]):
    """Change between the two latest complete quarters ÷ shares outstanding."""
    if len(quarters) < 2 or not shares or shares <= 0:
        return None
    a, b = quarters[-1], quarters[-2]
    h = data.holdings.get(t, {})
    if a not in h or b not in h:
        return None
    return (h[a] - h[b]) / shares


# ------------------------------------------------------------------ ranking --

def percentile(value: float, peers: list[float]) -> float:
    """Mid-rank percentile of value among sorted peer values (ties split)."""
    lo, hi = bisect_left(peers, value), bisect_right(peers, value)
    return 100.0 * (lo + 0.5 * (hi - lo)) / max(1, len(peers))


def signed_percentile(value: float, peers: list[float]) -> float:
    """Zero reads 50; positives rank among positive peers into 50 to 100,
    negatives among negative peers into 0 to 50."""
    if value == 0:
        return 50.0
    if value > 0:
        pos = peers[bisect_right(peers, 0):]
        return 50.0 + 0.5 * percentile(value, pos) if pos else 75.0
    neg = peers[:bisect_left(peers, 0)]
    return 0.5 * percentile(value, neg) if neg else 25.0


def rank(m: "M", value: float, peers: list[float]) -> float:
    return (signed_percentile if m.signed else percentile)(value, peers)


def band(p: float) -> float:
    for cut, r in BANDS:
        if p >= cut:
            return r
    return -1.0


def run(data: Data, asof: int, check: set | None = None) -> dict:
    """Measures, percentiles, readings and scores for every company on asof.
    `check` holds the (factor, broad group) pairs that pass the measured
    check (confidence check 3); none pass when it is empty or None."""
    check = check or set()
    universe = {}
    for t, info in data.info.items():
        last = close_on(data, t, asof)
        if not last or asof - last[0] > LISTED_DAYS:
            continue                # not trading on asof
        c = Ctx(data, t, asof)
        universe[t] = dict(info, ctx=c, peer=False, mcap=None,
                           shares=c.v(0, "sharesbas") if c.cur else None)
        if c.cur and c.fresh:
            universe[t]["mcap"] = c.mcap(0)
    caps = sorted(u["mcap"] for u in universe.values() if u["mcap"] and u["mcap"] > 0)
    floor = caps[int(len(caps) * SIZE_FLOOR)] if caps else 0
    for u in universe.values():
        u["peer"] = bool(u["mcap"] and u["mcap"] >= floor and u["group"] != "(none)")
        u["small"] = not u["peer"]

    # Raw values.
    vals = defaultdict(dict)        # key -> {ticker: (level, change)}
    for t, u in universe.items():
        c = u["ctx"]
        for m in MEASURES:
            if m.fn is None or not applies(m, u):
                continue
            if not c.cur or not c.fresh:
                continue
            lvl = m.fn(c, 0)
            if lvl is None:
                continue
            chg = None
            if m.trend:
                old = m.fn(c, 1)
                if old is not None and abs(lvl) < 1e8 and abs(old) < 1e8:
                    chg = lvl - old
            vals[m.key][t] = (lvl, chg)
    moves = results_moves(data, asof, universe, None)
    for t, (z, ev, last_day) in moves.items():
        if asof - ev <= SURPRISE_DAYS:
            vals["results_move"][t] = (z, None)
        universe[t]["ctx"].used_dates += [ev, last_day]
    owner_gaps = {"insider_buying": insider_coverage(data, asof),
                  "inst_change": holdings_coverage(data, asof)}
    quarters = complete_quarters(data, asof) if not owner_gaps["inst_change"] else []
    for t, u in universe.items():
        if not owner_gaps["insider_buying"]:
            ib = insider_buying(data, asof, t, u["shares"])
            if ib is not None:
                vals["insider_buying"][t] = (ib, None)
        if quarters:
            ic = inst_change(data, asof, t, u["shares"], quarters)
            if ic is not None:
                vals["inst_change"][t] = (ic, None)

    # Percentiles within peers.
    pct = defaultdict(dict)         # ticker -> {key: info}
    for m in MEASURES:
        v = vals.get(m.key, {})
        peer_pool = defaultdict(list)
        broad_pool = defaultdict(list)
        chg_pool = defaultdict(list)
        chg_broad = defaultdict(list)
        if m.key == "results_move":
            # Peers' latest moves from the past year count, not only 200 days.
            src = {t: (z, None) for t, (z, ev, _) in moves.items()}
        else:
            src = v
        for t, (lvl, chg) in src.items():
            u = universe[t]
            if not u["peer"]:
                continue
            peer_pool[u["group"]].append(m.direction * lvl)
            broad_pool[u["broad"]].append(m.direction * lvl)
            if chg is not None:
                chg_pool[u["group"]].append(m.direction * chg)
                chg_broad[u["broad"]].append(m.direction * chg)
        for pool in (peer_pool, broad_pool, chg_pool, chg_broad):
            for k in pool:
                pool[k].sort()
        for t, (lvl, chg) in v.items():
            u = universe[t]
            peers, fallback = peer_pool.get(u["group"], []), ""
            cpeers = chg_pool.get(u["group"], [])
            if len(peers) < MIN_PEERS:
                if m.fallback and len(broad_pool.get(u["broad"], [])) >= MIN_PEERS:
                    peers, fallback = broad_pool[u["broad"]], "broad group"
                    cpeers = chg_broad.get(u["broad"], [])
                else:
                    pct[t][m.key] = {"value": lvl, "pct": None, "peers": len(peers),
                                     "fallback": "too few peers"}
                    continue
            p_lvl = rank(m, m.direction * lvl, peers)
            p = p_lvl
            p_chg = None
            if chg is not None and len(cpeers) >= MIN_PEERS:
                p_chg = rank(m, m.direction * chg, cpeers)
                p = 2 / 3 * p_lvl + 1 / 3 * p_chg
            pct[t][m.key] = {"value": lvl, "change": chg, "pct": p,
                             "pct_level": p_lvl, "pct_change": p_chg,
                             "peers": len(peers), "fallback": fallback}

    # Factor readings and company scores.
    companies = {}
    for t, u in universe.items():
        w = exposures(u["broad"], u["version"])
        facs = {}
        for f in FACTORS:
            ms = [m for m in MEASURES if m.factor == f and m.scored and applies(m, u)]
            got = [pct[t][m.key] for m in ms
                   if m.key in pct[t] and pct[t][m.key]["pct"] is not None]
            need = max(1, math.ceil(len(ms) / 2))
            if not ms or len(got) < need:
                facs[f] = {"reading": None, "measures": len(ms), "have": len(got)}
                continue
            fp = statistics.mean(g["pct"] for g in got)
            reads = [band(g["pct"]) for g in got]
            data_ok = len(got) >= 2 / 3 * len(ms)
            peers_ok = (not u["small"] and all(g["peers"] >= GOOD_PEERS and not g["fallback"]
                                               for g in got))
            measured_ok = (f, u["broad"]) in check
            checks = data_ok + peers_ok + measured_ok
            conf = ("Low" if u["small"] else "High" if checks == 3 else
                    "Medium" if checks == 2 else "Low")
            facs[f] = {"reading": band(fp), "pct": fp, "low": min(reads),
                       "high": max(reads), "measures": len(ms), "have": len(got),
                       "confidence": conf,
                       "fallback": any(g["fallback"] for g in got)}
        scored = [f for f in FACTORS if facs[f]["reading"] is not None]
        if scored:
            sw = sum(w[f] for f in scored)
            score = 3 * sum(w[f] * facs[f]["reading"] for f in scored) / sw
            lo = 3 * sum(w[f] * facs[f]["low"] for f in scored) / sw
            hi = 3 * sum(w[f] * facs[f]["high"] for f in scored) / sw
            top = max(w[f] for f in scored)
            confs = [facs[f]["confidence"] for f in scored if w[f] == top]
            conf = min(confs, key=CONF_ORDER.__getitem__)
        else:
            score = lo = hi = None
            conf = ""
        companies[t] = {"info": u, "factors": facs, "score": score, "low": lo,
                        "high": hi, "confidence": conf, "weights": w}
    lookahead = sum(1 for u in universe.values() for d in u["ctx"].used_dates if d > asof)
    return {"asof": asof, "universe": universe, "vals": vals, "pct": pct,
            "companies": companies, "floor": floor, "lookahead": lookahead,
            "owner_gaps": owner_gaps}


# ------------------------------------------------------------------ outputs --

def fmt(x, nd=4):
    return "" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def write_csv(path: Path, header: list, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def company_rows(res: dict) -> tuple[list, list]:
    header = ["ticker", "name", "detailed_group", "broad_group", "version",
              "in_peer_set", "market_value_musd", "score", "score_low",
              "score_high", "confidence"]
    for f in FACTORS:
        header += [f"{f}_reading", f"{f}_pct", f"{f}_confidence", f"{f}_measures"]
    for m in MEASURES:
        header += [f"{m.key}_value", f"{m.key}_pct"]
    header += ["earnings_yield", "price_to_tangible_book"]
    rows = []
    for t, c in sorted(res["companies"].items()):
        u = c["info"]
        row = [t, u["name"], u["group"], u["broad"], u["version"],
               "Y" if u["peer"] else "N",
               fmt(u["mcap"] / 1e6 if u["mcap"] else None, 1),
               fmt(c["score"], 2), fmt(c["low"], 2), fmt(c["high"], 2), c["confidence"]]
        for f in FACTORS:
            fa = c["factors"][f]
            row += [fmt(fa["reading"], 1), fmt(fa.get("pct"), 1),
                    fa.get("confidence", ""), f"{fa['have']}/{fa['measures']}"]
        for m in MEASURES:
            p = res["pct"][t].get(m.key, {})
            row += [fmt(p.get("value"), 4), fmt(p.get("pct"), 1)]
        ctx = u["ctx"]
        ni, mc = (ctx.v(0, "netinc") if ctx.cur else None), u["mcap"]
        tb = tbv(ctx, 0) if ctx.cur else None
        row += [fmt(safe_div(ni, mc)), fmt(safe_div(mc, tb) if tb and tb > 0 else None, 2)]
        rows.append(row)
    return header, rows


def compare(a: dict, b: dict) -> tuple[int, int, list]:
    """Count companies whose results differ between two runs."""
    keys = set(a["companies"]) | set(b["companies"])
    diff, examples = 0, []
    for t in keys:
        ca, cb = a["companies"].get(t), b["companies"].get(t)
        sa = None if not ca else (ca["score"], tuple(ca["factors"][f]["reading"] for f in FACTORS))
        sb = None if not cb else (cb["score"], tuple(cb["factors"][f]["reading"] for f in FACTORS))
        if sa is None or sb is None or sa[1] != sb[1] or (
                sa[0] is not None and sb[0] is not None and abs(sa[0] - sb[0]) > 1e-9) or (
                (sa[0] is None) != (sb[0] is None)):
            diff += 1
            if len(examples) < 5:
                what = "not in both runs"
                if sa and sb:
                    what = ", ".join(FACTOR_NAMES[f] for f, x, y in
                                     zip(FACTORS, sa[1], sb[1]) if x != y) or "score"
                examples.append(f"{t}: {what}")
    return diff, len(keys), examples


def report(res: dict, data: Data, tests: list, spot: list) -> None:
    asof = dt.date.fromordinal(res["asof"])
    U = res["universe"]
    C = res["companies"]
    groups = sorted({u["group"] for u in U.values()})

    # Measure coverage per detailed group.
    mrows = []
    for g in groups:
        members = [t for t, u in U.items() if u["group"] == g]
        for m in MEASURES:
            applic = [t for t in members if applies(m, U[t])]
            if not applic:
                continue
            have = [t for t in applic if t in res["vals"].get(m.key, {})]
            ranked = [t for t in have if res["pct"][t].get(m.key, {}).get("pct") is not None]
            fb = [t for t in ranked if res["pct"][t][m.key]["fallback"]]
            peers = max((res["pct"][t][m.key]["peers"] for t in ranked), default=0)
            mrows.append([g, U[applic[0]]["broad"], m.key, FACTOR_NAMES[m.factor],
                          "Y" if m.scored else "N", len(applic), len(have),
                          f"{100 * (1 - len(have) / len(applic)):.1f}", len(ranked),
                          len(fb), peers])
    write_csv(OUT / "measure_coverage.csv",
              ["detailed_group", "broad_group", "measure", "factor", "scored",
               "companies", "with_value", "missing_pct", "ranked",
               "broad_fallback", "peers_used"], mrows)

    frows = []
    for g in groups:
        members = [t for t, u in U.items() if u["group"] == g]
        for f in FACTORS:
            rs = [C[t]["factors"][f] for t in members]
            got = [r for r in rs if r["reading"] is not None]
            bands = Counter(r["reading"] for r in got)
            confs = Counter(r["confidence"] for r in got)
            frows.append([g, f, len(members), len(got),
                          f"{100 * len(got) / max(1, len(members)):.1f}",
                          *[bands.get(b, 0) for b in (1.0, 0.5, 0.0, -0.5, -1.0)],
                          confs.get("High", 0), confs.get("Medium", 0),
                          confs.get("Low", 0)])
    write_csv(OUT / "factor_coverage.csv",
              ["detailed_group", "factor", "companies", "with_reading",
               "with_reading_pct", "plus1", "plus_half", "zero", "minus_half",
               "minus1", "high_confidence", "medium_confidence",
               "low_confidence"], frows)

    n = len(U)
    peers_n = sum(u["peer"] for u in U.values())
    fresh_n = sum(1 for u in U.values() if u["ctx"].fresh)
    scored_n = sum(1 for c in C.values() if c["score"] is not None)
    lines = ["# Company measures check report", "",
             f"Run: {asof} (every filing and price on or before this date). "
             "Source: Sharadar tables from the weekly pull. Method: "
             "docs/company-method.md; write-up: docs/company-measures.md.", "",
             "## Checks", "", "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {name} | {'pass' if ok else ('not run' if ok is None else 'FAIL')} "
              f"| {detail} |" for name, ok, detail in tests]
    lines += ["", "## Universe", "",
              f"- **Listed common stocks on {asof}:** {n:,} (a price in the week "
              f"before), {fresh_n:,} with a filing in the last {STALE_DAYS} days.",
              f"- **Peer sets:** {peers_n:,} companies above the size floor "
              f"(smallest fifth by market value left out; floor "
              f"${res['floor'] / 1e6:,.0f} million). Smaller companies are still "
              "ranked against their group's peer set, with low confidence.",
              f"- **Companies with a score:** {scored_n:,}. "
              f"{sum(1 for u in U.values() if u['group'] == '(none)'):,} have no "
              "French group in Sharadar and get no peer set.",
              f"- **Groups:** {len([g for g in groups if g != '(none)'])} detailed groups (Sharadar's French "
              "industry field uses his 48-group scheme), 12 broad groups from SIC "
              "codes."]
    # Factor coverage overall.
    lines += ["", "## Factor coverage (all companies)", "",
              "| Factor | With a reading | +1 | +0.5 | 0 | −0.5 | −1 | High | Medium | Low |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for f in FACTORS:
        rs = [c["factors"][f] for c in C.values()]
        got = [r for r in rs if r["reading"] is not None]
        b = Counter(r["reading"] for r in got)
        cf = Counter(r["confidence"] for r in got)
        lines.append(f"| {FACTOR_NAMES[f]} | {100 * len(got) / max(1, n):.0f}% "
                     f"({len(got):,}) | " + " | ".join(
                         str(b.get(x, 0)) for x in (1.0, 0.5, 0.0, -0.5, -1.0))
                     + f" | {cf.get('High', 0):,} | {cf.get('Medium', 0):,} | "
                     f"{cf.get('Low', 0):,} |")
    # Same, peer sets only: companies under the size floor are ranked against
    # bigger peers and lean to the bottom, which skews the table above.
    lines += ["", "Peer-set companies only (above the size floor), share in each band:", "",
              "| Factor | +1 | +0.5 | 0 | −0.5 | −1 |", "|---|---|---|---|---|---|"]
    for f in FACTORS:
        got = [c["factors"][f]["reading"] for c in C.values()
               if c["info"]["peer"] and c["factors"][f]["reading"] is not None]
        b = Counter(got)
        lines.append(f"| {FACTOR_NAMES[f]} | " + " | ".join(
            f"{100 * b.get(x, 0) / max(1, len(got)):.0f}%"
            for x in (1.0, 0.5, 0.0, -0.5, -1.0)) + " |")
    sc = Counter(c["confidence"] for c in C.values() if c["score"] is not None)
    check_note = (f"the measured check of {res['check_run']} sets check 3"
                  if res.get("check_run") else
                  "no measured check yet, so nothing goes above Medium")
    lines += ["", f"Company confidence: High {sc.get('High', 0):,}, Medium "
              f"{sc.get('Medium', 0):,}, Low {sc.get('Low', 0):,} ({check_note})."]
    # Measure missing rates overall.
    lines += ["", "## Measures: missing rates among companies they apply to", "",
              "| Measure | Factor | Scored | Applies to | Missing | Broad fallback |",
              "|---|---|---|---|---|---|"]
    for m in MEASURES:
        applic = [t for t, u in U.items() if applies(m, u)]
        have = [t for t in applic if t in res["vals"].get(m.key, {})]
        fb = sum(1 for t in have if res["pct"][t].get(m.key, {}).get("fallback") == "broad group")
        lines.append(f"| {m.label} | {FACTOR_NAMES[m.factor]} | "
                     f"{'yes' if m.scored else 'no'} | {len(applic):,} | "
                     f"{100 * (1 - len(have) / max(1, len(applic))):.0f}% | {fb:,} |")
    # Thin groups.
    thin = [r for r in frows if r[2] >= 5 and float(r[4]) < 50 and r[1] in
            ("growth", "profitability", "balance", "capital")]
    if thin:
        lines += ["", "## Gaps by group (under half with a reading)", ""]
        for r in thin[:30]:
            lines.append(f"- {r[0]}, {FACTOR_NAMES[r[1]]}: {r[4]}% of {r[2]}")
    if spot:
        lines += ["", "## Spot check (readings only)", "",
                  "Readings on the −1 to +1 scale and the company score (−3 to +3). "
                  "No Sharadar numbers are shown.", "",
                  "| Ticker | Group | Growth | Profit | Balance | Capital | Surprise "
                  "| Owners | Score (range) | Confidence |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for t in spot:
            c = C.get(t)
            if not c:
                lines.append(f"| {t} | not in the universe | | | | | | | | |")
                continue
            r = [fmt(c["factors"][f]["reading"], 1) or "–" for f in FACTORS]
            s = (f"{c['score']:+.1f} ({c['low']:+.1f} to {c['high']:+.1f})"
                 if c["score"] is not None else "–")
            lines.append(f"| {t} | {c['info']['group']} | " + " | ".join(r)
                         + f" | {s} | {c['confidence']} |")
    owner = [f"{BY_KEY[k].label}: not scored this run, because {why}."
             for k, why in res.get("owner_gaps", {}).items() if why]
    lines += ["", "## Notes", ""] + [f"- {x}" for x in owner + data.notes]
    lines += [data.split_note] if data.split_note else []
    lines += ["- Full per-company results stay on the runner "
              "(raw/company_results/): the repository is public and the Sharadar "
              "licence doesn't allow redistributing its data.", ""]
    (OUT / "MEASURES_CHECK_REPORT.md").write_text("\n".join(lines))


SPOT = ["AAPL", "MSFT", "NVDA", "JPM", "BAC", "XOM", "JNJ", "WMT", "HD", "KO",
        "PGR", "NEE", "T", "CAT", "MRNA"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", help="run date (default today)")
    args = ap.parse_args()
    today = (dt.date.fromisoformat(args.asof) if args.asof else dt.date.today()).toordinal()
    t0 = time.time()
    data = load(today)
    print(f"loaded in {time.time() - t0:,.0f}s")
    check, check_run = load_check()

    t0 = time.time()
    res = run(data, today, check)
    res["check_run"] = check_run
    print(f"run for {dt.date.fromordinal(today)} in {time.time() - t0:,.0f}s: "
          f"{len(res['companies']):,} companies")

    tests = []
    tests.append(("No filing or price after the run date", res["lookahead"] == 0,
                  f"{res['lookahead']:,} filing or price dates after "
                  f"{dt.date.fromordinal(today)} among those used"))
    # Truncation test a year back: all data vs data cut at that date.
    back = today - 365
    t0 = time.time()
    full = run(data, back)
    cut = run(data.truncated(back), back)
    diff, total, ex = compare(full, cut)
    tests.append(("Same results with later data deleted (a year back)",
                  diff == 0 and full["lookahead"] == 0,
                  f"run for {dt.date.fromordinal(back)}: {diff:,} of {total:,} "
                  "companies differ between all data and data cut at that date"
                  + (f" (e.g. {', '.join(ex)})" if ex else "")
                  + f"; {full['lookahead']:,} dates after it used"))
    print(f"truncation test in {time.time() - t0:,.0f}s: {diff} differ")
    # Delisted companies stay in history.
    gone = [t for t, u in full["universe"].items() if t not in res["universe"]]
    tests.append(("Companies that later left the market are kept", len(gone) > 0,
                  f"{len(gone):,} companies listed on {dt.date.fromordinal(back)} "
                  "aren't listed now and are still in that run"))
    # Ranks behave: percentiles spread evenly within peer sets.
    signed = {m.key for m in MEASURES if m.signed}
    allp = [p["pct_level"] for t in res["pct"] for k, p in res["pct"][t].items()
            if p.get("pct") is not None and res["universe"][t]["peer"]
            and k not in signed]
    if allp:
        top = sum(p >= 80 for p in allp) / len(allp)
        tests.append(("Peer ranks spread evenly", 0.15 <= top <= 0.25,
                      f"{100 * top:.1f}% of peer-set level ranks in the top fifth "
                      "(expect about 20%)"))
    fresh_t = [t for t, u in res["universe"].items() if u["ctx"].fresh]
    fresh = len(fresh_t)
    coverage = sum(1 for t in fresh_t
                   if res["companies"].get(t, {}).get("score") is not None)
    tests.append(("Most companies with fresh filings get a score",
                  fresh and coverage / fresh >= 0.9,
                  f"{coverage:,} of the {fresh:,} with a filing in the last "
                  f"{STALE_DAYS} days have a score"))

    report(res, data, tests, SPOT)
    header, rows = company_rows(res)
    write_csv(RESULTS / f"company_scores_{dt.date.fromordinal(today)}.csv", header, rows)
    for name, ok, detail in tests:
        print(f"{name}: {'pass' if ok else 'FAIL'} ({detail})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
