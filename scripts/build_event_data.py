"""Events pillar: pull the 12 v1 event types and line each event up with returns.

Tracker task "Event data". The 12 types were agreed on Nov 27
(docs/event-types.md) and each has a checked source (docs/event-sources.md).
This script pulls every type from its source, writes one clean event table
per level (date, type, level, affected sector or company) and lines each
event up with sector and stock returns around it. Write-up:
docs/event-data.md.

Levels and baselines (docs/event-types.md section 1):
  market-wide  every French group's return minus the market (12 and 49 groups)
  industry     the affected group's return minus the market
  company      the stock's return minus its French industry group (Sharadar's
               famaindustry), plus the all-stock market

Return windows, in trading days from day 0 (the first trading day on or
after the event date): pre20 [-20,-1], m1 [-1], d0 [0], d01 [0,+1],
post20 [+2,+21]. Filing dates carry no time, so d01 is the main company
window: it covers filings made after the 4 PM close.

No look-ahead. Every event is dated when its record became public. Spike and
big-move days are chosen against earlier days only (an expanding window),
and off-cycle guidance and dividend breaks use only earlier filings and
payments. A truncation test reruns those rules on data cut a year back and
checks the events before the cut are unchanged. One rule does look forward
and is flagged on every row it touches: merger announcements are picked out
by the deal filing that follows them (the 8-K itself was public that day).

What is committed (data/events/pull/): the market-wide and industry event
tables with their sector moves (public sources only), counts, and the check
report. Company events come from Sharadar, whose personal licence doesn't
allow sharing its data, and the repository is public: the company event
table with its returns stays on the runner (raw/event_results/) and only
counts and averages are committed, as the company pull does.

Sources and secrets:
  - matteoiacoviello.com (geopolitical and trade policy risk indexes), the
    Federal Register API, SEC EDGAR full-text search: no key.
  - FRED (policy uncertainty index, WTI oil price): FRED_API_KEY.
  - Sharadar (tickers, daily prices, 8-K events, corporate actions):
    SHARADAR_API_KEY. Sent only as a header, never printed.
  - SEC_USER_AGENT (name and contact) is used for SEC if set.

EDGAR search results are cached month by month in raw/event_cache/ (kept
between runs by the workflow's cache step): only the latest months are
fetched again each week. A first run that hits its time budget stops cleanly
and carries on next run.

Run: python scripts/build_event_data.py [--skip-company] [--skip-edgar]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import re
import statistics
import sys
import threading
import time
import traceback
from array import array
from bisect import bisect_left, bisect_right, insort
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_event_sources as ces  # noqa: E402  (source helpers: get, links, sheets, FRED)
import fetch_company_data as fcd  # noqa: E402  (Sharadar download helpers)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "events" / "pull"
RAW = ROOT / "raw" / "event_data"
CACHE = ROOT / "raw" / "event_cache"
RESULTS = ROOT / "raw" / "event_results"
FRENCH = ROOT / "data" / "french"
AGENCY_MAP = ROOT / "config" / "regulation_agencies.csv"
SOURCE_CHECK = ROOT / "data" / "events" / "sources"

TODAY = dt.date.today()
CUTOFF = TODAY - dt.timedelta(days=365)      # truncation test date

FR_API = "https://www.federalregister.gov/api/v1/documents.json"
EDGAR_FTS = "https://efts.sec.gov/LATEST/search-index"

WINDOWS = [("pre20", -20, -1), ("m1", -1, -1), ("d0", 0, 0), ("d01", 0, 1),
           ("post20", 2, 21)]
G12 = ["NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq", "Telcm", "Utils",
       "Shops", "Hlth", "Money", "Other"]

# Event type names as in docs/event-types.md.
GEO = "Geopolitical shocks"
TRADE = "Trade and tariff actions"
ELECT = "Elections and policy shocks"
ENERGY = "Energy and commodity supply shocks"
REG = "Major regulatory actions"
GUIDE = "Guidance changes"
MNA = "Mergers and acquisitions"
LEAD = "Leadership changes"
CAP = "Capital structure breaks"
ACCT = "Accounting and legal trouble"
DIST = "Distress and restructuring"
ACTIV = "Activist stakes"
MARKET_TYPES = [GEO, TRADE, ELECT, ENERGY]
COMPANY_TYPES = [GUIDE, MNA, LEAD, CAP, ACCT, DIST, ACTIV]
ALL_TYPES = MARKET_TYPES + [REG] + COMPANY_TYPES

# Rules (provisional; the event method sets the final cut-offs).
SPIKE_PCT = 0.95          # index above the 95th percentile of all earlier days
SPIKE_MIN_OBS = 730       # at least two years of earlier days
SPIKE_GAP = 10            # a new episode needs 10 quiet days
OIL_PCT = 0.975           # one-day oil move above the 97.5th percentile of earlier moves
OIL_MIN_OBS = 500
OIL_GAP = 5
GUIDE_WINDOWS = [(81, 101), (172, 192), (263, 283), (355, 375)]  # regular release days back
DIV_CUT = 0.75            # next payment at or below 75% of the steady level
DIV_STOP_DAYS = 200
FIRST_DIV_HISTORY = 730
MIN_PRIOR_DAYS = 60       # offerings: the stock traded at least 60 days before
ANNOUNCE_LOOKBACK = 90    # merger announcement: 8-K 1.01 up to 90 days before the deal filing
CLIP_LO, CLIP_HI = -0.5, 1.0   # peer averages: daily returns clipped to this range
MIN_PRICE = 1.0           # peer averages: prior close at least $1 (unadjusted)
MIN_PEERS = 5

# Sharadar 8-K codes (item number without its dot), checked on Nov 27.
CODE_ITEMS = {
    "22": (GUIDE, "results release away from the regular schedule (8-K 2.02)", "main"),
    "71": (GUIDE, "Reg FD disclosure away from results, mostly presentations (8-K 7.01)", "cross-check"),
    "52": (LEAD, "any officer or director change (8-K 5.02)", "cross-check"),
    "21": (MNA, "acquisition or sale completed, either side (8-K 2.01)", "cross-check"),
    "37": (MNA, "tender offer (Sharadar code 37, inferred)", "cross-check"),
    "41": (ACCT, "auditor change (8-K 4.01)", "main"),
    "40": (ACCT, "auditor change, pre-2004 item", "main"),
    "42": (ACCT, "restatement: past results no longer reliable (8-K 4.02)", "main"),
    "31": (ACCT, "delisting or listing-rule notice (8-K 3.01)", "main"),
    "13": (DIST, "bankruptcy or receivership (8-K 1.03)", "main"),
    "24": (DIST, "debt default or acceleration trigger (8-K 2.04)", "main"),
    "25": (DIST, "layoffs, closures or exit costs (8-K 2.05)", "main"),
    "35": (ACTIV, "13D stake (Sharadar code 35, inferred)", "cross-check"),
}

# EDGAR full-text searches. Each is pulled month by month and cached.
FTS_QUERIES = {
    "13d": {"forms": "SC 13D"},
    "13d_new": {"forms": "SCHEDULE 13D"},
    "tender": {"forms": "SC TO-T"},
    "tender_response": {"forms": "SC 14D9"},
    "prem14a": {"forms": "PREM14A"},
    "defm14a": {"forms": "DEFM14A"},
    "nt10k": {"forms": "NT 10-K"},
    "nt10q": {"forms": "NT 10-Q"},
    "424b4": {"forms": "424B4"},
    "424b5_shares": {"forms": "424B5", "q": '"we are offering" "shares of our common stock"'},
    "ceo_resign": {"forms": "8-K", "q": '"chief executive officer" resign'},
    "ceo_retire": {"forms": "8-K", "q": '"chief executive officer" retire'},
    "cfo_resign": {"forms": "8-K", "q": '"chief financial officer" resign'},
    "cfo_retire": {"forms": "8-K", "q": '"chief financial officer" retire'},
    "immediate": {"forms": "8-K", "q": '"effective immediately" resign'},
}
FTS_START = dt.date(2001, 1, 1)
FTS_REFRESH_DAYS = 100        # months touching the last 100 days are fetched again
EDGAR_BUDGET = float(os.environ.get("EDGAR_BUDGET_MIN", "70")) * 60
SEC_RATE = 8.0                # requests per second across threads (SEC allows 10)

checks: list[dict] = []
gaps: list[str] = []
notes: list[str] = []
SEC_UA = os.environ.get("SEC_USER_AGENT", "").strip() or "invest-with-ai-data-pull"


# ----------------------------------------------------------------- helpers --

def check(name: str, ok: bool | None, detail: str) -> None:
    status = "pass" if ok else ("info" if ok is None else "fail")
    checks.append({"check": name, "status": status, "detail": detail})
    print(f"[{status}] {name}: {detail}")


def guarded(label: str):
    """Run one source; a crash is recorded as a failed check, not fatal."""
    def wrap(fn):
        def run(*a, **k):
            try:
                return fn(*a, **k)
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                check(f"Source: {label}", False, f"{type(e).__name__}: {str(e)[:200]}")
                gaps.append(f"{label}: source failed this run ({type(e).__name__}).")
                return None
        return run
    return wrap


def write_csv(path: Path, header: list, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def event_id(*parts) -> str:
    return "E" + hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:10]


def iso(d) -> str:
    return d.isoformat() if isinstance(d, dt.date) else ("" if d is None else str(d))


def fmt(x, nd=3) -> str:
    return "" if x is None else f"{x:.{nd}f}"


def ev(level, etype, subtype, role, date, source, ref="", detail="", public_from=None,
       groups12="", groups49="", **extra) -> dict:
    e = {"event_id": event_id(etype, subtype, iso(date), ref, extra.get("ticker", "")),
         "level": level, "type": etype, "subtype": subtype, "role": role,
         "date": date, "public_from": public_from or date, "source": source,
         "ref": ref, "detail": detail, "groups12": groups12, "groups49": groups49}
    e.update(extra)
    return e


# ------------------------------------------------- point-in-time detectors --

def expanding_spikes(series: dict, pct: float, min_obs: int, gap: int,
                     upto: dt.date | None = None) -> list[tuple[dt.date, float, float]]:
    """Days whose value is above the pct quantile of all earlier days.

    Returns (first day of each episode, value, percentile among earlier days).
    Only data up to `upto` is read when given (the truncation test)."""
    seen: list[float] = []
    out, last = [], None
    for d in sorted(series):
        if upto and d > upto:
            break
        v = series[d]
        if len(seen) >= min_obs:
            cut = seen[int(pct * (len(seen) - 1))]
            if v >= cut:
                if last is None or (d - last).days > gap:
                    out.append((d, v, 100 * bisect_left(seen, v) / len(seen)))
                last = d
        insort(seen, v)
    return out


def oil_moves(prices: dict, upto: dt.date | None = None) -> list[tuple[dt.date, float, float]]:
    """Big one-day WTI moves: |log change| above OIL_PCT of earlier moves."""
    days = sorted(d for d in prices if not upto or d <= upto)
    moves: dict = {}
    for a, b in zip(days, days[1:]):
        pa, pb = prices[a], prices[b]
        if pa > 0 and pb > 0 and (b - a).days <= 7:
            moves[b] = math.log(pb / pa)
    absmoves = {d: abs(r) for d, r in moves.items()}
    return [(d, moves[d], p) for d, _, p in
            expanding_spikes(absmoves, OIL_PCT, OIL_MIN_OBS, OIL_GAP, upto)]


def guidance_offcycle(days: list[int], upto: int | None = None) -> list[int]:
    """2.02 filing days (ordinals) that don't match the company's own schedule.

    A filing is regular if an earlier 2.02 fell about one, two, three or four
    quarters before it (GUIDE_WINDOWS). It needs a year of earlier filings to
    judge, and one within three days after another is the same release."""
    days = sorted(set(d for d in days if upto is None or d <= upto))
    out = []
    for i, d in enumerate(days):
        prior = days[:i]
        if not prior or d - prior[0] < 365:
            continue
        if d - prior[-1] <= 3:
            continue
        regular = False
        for lo, hi in GUIDE_WINDOWS:
            j = bisect_left(prior, d - hi)
            if j < len(prior) and prior[j] <= d - lo:
                regular = True
                break
        if not regular:
            out.append(d)
    return out


def dividend_breaks(pays: list[tuple[int, float]], splits: list[int],
                    price_days, upto: int | None = None) -> list[tuple[int, str, str]]:
    """Cuts, stops and first dividends from one company's payments (ordinals).

    Steady payer: last four payments within 400 days, each within 10% of their
    median, no split in that span. Cut: the next payment at or below 75% of
    that median. Stop: a steady payer with no payment for 200 days while the
    stock still trades, dated the day the 200 days run out. First dividend:
    the first payment on record after two years of trading. All use only
    earlier payments and prices."""
    pays = sorted(p for p in pays if upto is None or p[0] <= upto)
    out = []
    if not pays:
        return out
    pd = price_days
    if pd is not None and len(pd):
        first_px = pd[0]
        if pays[0][0] - first_px >= FIRST_DIV_HISTORY and pays[0][0] >= dt.date(1999, 1, 1).toordinal():
            out.append((pays[0][0], "first dividend", f"{pays[0][1]:.4f} a share"))
    for i in range(4, len(pays) + 1):
        prior = pays[i - 4:i]
        if prior[-1][0] - prior[0][0] > 400:
            continue
        med = statistics.median(x[1] for x in prior)
        if med <= 0 or any(abs(x[1] - med) > 0.10 * med for x in prior):
            continue
        if i < len(pays):
            d, v = pays[i]
            if 0 < v <= DIV_CUT * med and not any(prior[0][0] <= s <= d for s in splits):
                out.append((d, "dividend cut of 25% or more", f"{v:.4f} vs steady {med:.4f}"))
        # A stop is known on the first trading day after 200 days with no payment.
        nxt = pays[i][0] if i < len(pays) else None
        stop_day = prior[-1][0] + DIV_STOP_DAYS
        if (nxt is None or nxt > stop_day) and pd is not None and len(pd):
            k = bisect_left(pd, stop_day)
            if k < len(pd) and pd[k] - stop_day <= 7 and (upto is None or pd[k] <= upto) \
                    and (nxt is None or nxt > pd[k]):
                out.append((pd[k], "dividend stopped (no payment for 200 days)",
                            f"last {dt.date.fromordinal(prior[-1][0])}, steady {med:.4f}"))
    return out


# ------------------------------------------------------- market-wide types --

@guarded("Geopolitical risk index")
def pull_gpr(market: list, series_store: dict) -> None:
    files = ces.links(ces.GPR_PAGE, r"gpr_daily_recent.*\.xlsx?$") or \
        ces.links(ces.GPR_PAGE, r"daily.*\.xlsx?$")
    if not files:
        raise RuntimeError("no daily file linked on the GPR page")
    sheets = ces.read_sheets(ces.get(files[0], timeout=180), files[0])
    _, col, series = ces.daily_series(sheets, ["GPRD", "GPRD_MA7", "GPR"])
    if not series:
        raise RuntimeError("no daily GPRD column found")
    series_store["GPR"] = series
    for d, v, p in expanding_spikes(series, SPIKE_PCT, SPIKE_MIN_OBS, SPIKE_GAP):
        market.append(ev("market", GEO, "risk index spike", "main", d,
                         "Geopolitical risk index, daily (Caldara and Iacoviello)",
                         ref=f"GPRD {d}", detail=f"index {v:.1f}; above {p:.1f}% of earlier days"))
    notes.append(f"Geopolitical risk index: {min(series)} to {max(series)}, column {col}.")


@guarded("Trade policy uncertainty index")
def pull_tpu(market: list, series_store: dict) -> None:
    files = ces.links(ces.TPU_PAGE, r"tpu_web.*\.xlsx?$") or ces.links(ces.TPU_PAGE, r"\.xlsx$")
    best = {}
    for url in files:
        sheets = ces.read_sheets(ces.get(url, timeout=180), url)
        _, _, s = ces.daily_series(sheets, ["TPUD_INDEX", "TPU_DAILY", "TPUD", "TPU"])
        if len(s) > len(best):
            best = s
    if not best:
        raise RuntimeError("no daily TPU series found")
    series_store["TPU"] = best
    for d, v, p in expanding_spikes(best, SPIKE_PCT, SPIKE_MIN_OBS // 2, SPIKE_GAP):
        market.append(ev("market", TRADE, "trade uncertainty spike", "cross-check", d,
                         "Trade policy uncertainty index, daily (Caldara and Iacoviello)",
                         ref=f"TPUD {d}", detail=f"index {v:.1f}; above {p:.1f}% of earlier days"))


@guarded("Economic policy uncertainty index (FRED)")
def pull_epu(market: list, series_store: dict) -> None:
    series = ces.fred("USEPUINDXD")
    series_store["EPU"] = series
    for d, v, p in expanding_spikes(series, SPIKE_PCT, SPIKE_MIN_OBS, SPIKE_GAP):
        market.append(ev("market", ELECT, "policy uncertainty spike", "main", d,
                         "Economic policy uncertainty index, daily (FRED USEPUINDXD)",
                         ref=f"USEPUINDXD {d}", detail=f"index {v:.1f}; above {p:.1f}% of earlier days"))


def election_days() -> list[tuple[dt.date, str]]:
    out = []
    for y in range(1994, TODAY.year + 1, 2):
        nov1 = dt.date(y, 11, 1)
        day = nov1 + dt.timedelta(days=(0 - nov1.weekday()) % 7 + 1)
        if day <= TODAY:
            out.append((day, "presidential election" if y % 4 == 0 else "midterm election"))
    return out


def pull_elections(market: list) -> None:
    for d, kind in election_days():
        market.append(ev("market", ELECT, kind, "main", d,
                         "US federal election day (fixed by law)", ref=f"election {d.year}",
                         detail="results come in overnight, so day +1 carries most of the news"))


@guarded("WTI oil price (FRED)")
def pull_oil(market: list, series_store: dict) -> None:
    wti = ces.fred("DCOILWTICO")
    series_store["WTI"] = wti
    for d, r, p in oil_moves(wti):
        market.append(ev("market", ENERGY, "oil price jump" if r > 0 else "oil price drop", "main",
                         d, "WTI oil price, daily (FRED DCOILWTICO)", ref=f"WTI {d}",
                         detail=f"{100 * (math.exp(r) - 1):+.1f}% in a day; bigger than {p:.1f}% "
                                "of earlier moves; a price move, not a decision record"))


def fr_all(params: dict) -> list[dict]:
    """Every Federal Register document for a query (pages of 1,000)."""
    out, page = [], 1
    fields = ["document_number", "title", "type", "publication_date", "signing_date",
              "agencies", "significant", "presidential_document_type", "executive_order_number"]
    while True:
        p = {"per_page": 1000, "page": page, "order": "oldest", "fields[]": fields}
        p.update(params)
        data = json.loads(ces.get(FR_API, p, timeout=120))
        res = data.get("results") or []
        out.extend(res)
        if page >= int(data.get("total_pages") or 1) or not res:
            return out
        page += 1
        time.sleep(0.2)


PRES_KEEP = re.compile(r"tariff|dut(y|ies)|adjusting imports|imports of|section 232|safeguard|"
                       r"reciprocal|trade agreement|free trade|harmonized tariff schedule|trade act|"
                       r"retaliat|quota|trade relations|most.favored", re.I)
HTS_ONLY = re.compile(r"harmonized tariff schedule|generalized system of preferences|"
                      r"technical (corrections|rectifications)", re.I)
USTR_KEEP = re.compile(r"section (301|201|232)|action|determination|modif|imposition|additional "
                       r"(tariff|dut)|increase|suspension|retaliat|trade agreement|termination", re.I)
USTR_DROP = re.compile(r"request for (public )?comment|hearing|extension of (the )?(comment|exclusion)|"
                       r"exclusion|meeting|advisory committee|correction|information collection|"
                       r"privacy act|procedures|comment period|nominations|generalized system of "
                       r"preferences|\bgsp\b|petition|annual review|public input|request for "
                       r"(information|applications)|tariff-rate quota|sugar|textile|apparel|"
                       r"africa growth|andean|caribbean basin", re.I)


@guarded("Federal Register: tariff actions")
def pull_trade(market: list) -> None:
    docs = []
    years = range(1994, TODAY.year + 1)
    raw_counts = Counter()
    for y in years:
        yr = {"conditions[publication_date][year]": y}
        for label, extra in (("proclamation", {"conditions[type][]": "PRESDOCU",
                                               "conditions[presidential_document_type][]": "proclamation"}),
                             ("executive order", {"conditions[type][]": "PRESDOCU",
                                                  "conditions[presidential_document_type][]": "executive_order"}),
                             ("USTR", {"conditions[agencies][]": "trade-representative-office-of-united-states"})):
            res = fr_all({**yr, **extra, "conditions[term]": "tariff"})
            raw_counts[label] += len(res)
            docs += [(label, r) for r in res]
            time.sleep(0.2)
    kept = defaultdict(list)          # date -> [(subtype, role, doc number, title)]
    for label, r in docs:
        title = r.get("title") or ""
        pub = ces.to_date(r.get("publication_date"))
        if not pub:
            continue
        if label in ("proclamation", "executive order"):
            if not PRES_KEEP.search(title):
                continue
            date = ces.to_date(r.get("signing_date")) or pub
            if re.search(r"section 232|adjusting imports", title, re.I):
                sub = "Section 232 import action"
            elif re.search(r"trade agreement|free trade|trade relations|most.favored", title, re.I):
                sub = "trade agreement"
            elif HTS_ONLY.search(title) and not re.search(r"tariff[^s]|dut(y|ies)|reciprocal|"
                                                         r"safeguard|retaliat", title, re.I):
                sub = "tariff schedule change (technical)"
            else:
                sub = f"tariff {label}"
            role = "cross-check" if "technical" in sub else "main"
        else:
            if not USTR_KEEP.search(title) or USTR_DROP.search(title):
                continue
            date = pub
            sub = "Section 301 action" if "301" in title else "USTR tariff action"
            role = "main"
        kept[date].append((sub, role, r.get("document_number", ""), title, pub))
    n_docs = sum(len(v) for v in kept.values())
    for d, items in sorted(kept.items()):
        main = [i for i in items if i[1] == "main"]
        use = main or items
        subs = sorted({i[0] for i in use})
        market.append(ev("market", TRADE, "; ".join(subs), "main" if main else "cross-check", d,
                         "Federal Register: presidential documents and USTR notices on tariffs",
                         ref=",".join(i[2] for i in use)[:200],
                         detail=f"{len(use)} document(s): " + " | ".join(i[3][:90] for i in use[:3])))
    check("Trade actions: documents read and kept", n_docs >= 30,
          f"{sum(raw_counts.values()):,} documents mention tariffs "
          f"({raw_counts['proclamation']} proclamations, {raw_counts['executive order']} executive "
          f"orders, {raw_counts['USTR']} USTR); {n_docs} kept as actions on {len(kept)} days "
          "(write-up: 274 proclamations and 1,124 USTR documents mention tariffs)")
    notes.append("Trade actions are dated on the signing day for presidential documents (the White "
                 "House releases the text that day) and the publication day for USTR notices.")


def load_agency_map() -> dict:
    out = {}
    with AGENCY_MAP.open() as f:
        for r in csv.DictReader(f):
            out[r["agency_slug"]] = r
            out[slugify(r["agency_name"])] = r
    return out


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", "")).strip("-")


@guarded("Federal Register: significant final rules")
def pull_regulation(industry: list) -> None:
    amap = load_agency_map()
    unmapped = Counter()
    per_year = []
    total_api = 0
    for y in range(1995, TODAY.year + 1):
        params = {"conditions[publication_date][year]": y, "conditions[type][]": "RULE",
                  "conditions[significant]": 1}
        res = fr_all(params)
        count = int(json.loads(ces.get(FR_API, {**params, "per_page": 1,
                                                "fields[]": ["document_number"]})).get("count", 0))
        total_api += count
        per_year.append((y, count, len(res)))
        for r in res:
            d = ces.to_date(r.get("publication_date"))
            if not d:
                continue
            ags = r.get("agencies") or []
            child = [a for a in ags if a.get("parent_id")]
            pick = []
            for group in (child, ags):
                for a in group:
                    m = amap.get(a.get("slug") or "") or amap.get(slugify(a.get("name") or a.get("raw_name") or ""))
                    if m and m not in pick:
                        pick.append(m)
                if pick:
                    break
            g12 = ";".join(sorted({g for m in pick for g in m["groups12"].split(";") if g}))
            g49 = ";".join(sorted({g for m in pick for g in m["groups49"].split(";") if g}))
            names = "; ".join(a.get("name") or a.get("raw_name") or "" for a in ags)
            if not g12:
                for a in (child or ags)[:1]:
                    unmapped[a.get("name") or a.get("raw_name") or "(none)"] += 1
            industry.append(ev("industry", REG, "significant final rule",
                               "main" if g12 else "unmapped", d,
                               "Federal Register: final rules marked significant",
                               ref=r.get("document_number", ""),
                               detail=f"{names[:80]}: {(r.get('title') or '')[:120]}",
                               groups12=g12, groups49=g49))
        time.sleep(0.2)
    got = sum(p[2] for p in per_year)
    short = [f"{y} ({n} of {c})" for y, c, n in per_year if n != c]
    check("Regulation: every significant rule read", not short,
          f"{got:,} rules read; the API counts {total_api:,}"
          + (f"; short years: {', '.join(short)}" if short else "")
          + " (write-up: 9,521)")
    mapped = sum(1 for e in industry if e["role"] == "main")
    check("Regulation: rules tied to an industry group", mapped >= 0.5 * max(got, 1),
          f"{mapped:,} of {got:,} ({100 * mapped / max(got, 1):.0f}%) map to a French group through "
          "config/regulation_agencies.csv")
    if unmapped:
        gaps.append("Regulation: agencies not mapped to an industry (rules kept, role unmapped): "
                    + ", ".join(f"{a} ({n})" for a, n in unmapped.most_common(10)))


# ---------------------------------------------------------- French returns --

def read_french(name: str) -> tuple[list[str], dict]:
    with (FRENCH / name).open() as f:
        r = csv.reader(f)
        header = next(r)
        data = {}
        for row in r:
            d = ces.to_date(row[0])
            if not d:
                continue
            vals = {}
            for h, v in zip(header[1:], row[1:]):
                x = ces.to_float(v)
                if x is not None and x > -99:
                    vals[h] = x / 100
            data[d] = vals
    return header[1:], data


class Calendar:
    """Trading days from French's daily files; weekdays after its last day."""

    def __init__(self, days: list[dt.date]):
        self.days = sorted(days)
        self.last_real = self.days[-1]
        d = self.last_real
        while d < TODAY + dt.timedelta(days=10):
            d += dt.timedelta(days=1)
            if d.weekday() < 5:
                self.days.append(d)

    def day0(self, d: dt.date) -> int | None:
        i = bisect_left(self.days, d)
        if i >= len(self.days) or (self.days[i] - d).days > 5:
            return None
        return i


def compound(rets: list) -> float | None:
    if not rets or any(r is None for r in rets):
        return None
    x = 1.0
    for r in rets:
        x *= 1 + r
    return x - 1


def sector_moves(events: list, groups12: list, d12: dict, groups49: list, d49: dict,
                 mkt: dict, cal: Calendar, all_groups: bool) -> tuple[list, list, dict]:
    """Rows of group-minus-market moves per event and window, in percent."""
    rows12, rows49 = [], []
    pending = Counter()
    for e in events:
        i = cal.day0(e["date"])
        e["day0"] = cal.days[i] if i is not None else None
        if i is None:
            continue
        if i + 21 >= len(cal.days) or cal.days[i + 21] > cal.last_real:
            pending[e["type"]] += 1
        spans = {}
        for w, a, b in WINDOWS:
            if i + a < 0 or i + b >= len(cal.days):
                spans[w] = None
            else:
                spans[w] = [cal.days[k] for k in range(i + a, i + b + 1)]
        mret = {w: (compound([mkt.get(d) for d in s]) if s else None) for w, s in spans.items()}
        for grouping, glist, data, rows in (("12", groups12, d12, rows12),
                                            ("49", groups49, d49, rows49)):
            want = glist if all_groups else [g for g in e.get(f"groups{grouping}", "").split(";") if g]
            if not want:
                continue
            if all_groups:
                rows.append([e["event_id"], grouping, "Market"] +
                            [fmt(None if mret[w] is None else 100 * mret[w]) for w, _, _ in WINDOWS])
            for g in want:
                vals = []
                for w, _, _ in WINDOWS:
                    s = spans[w]
                    gr = compound([data.get(d, {}).get(g) for d in s]) if s else None
                    vals.append(None if gr is None or mret[w] is None else 100 * (gr - mret[w]))
                rows.append([e["event_id"], grouping, g] + [fmt(v) for v in vals])
    return rows12, rows49, pending


def ordinary_vs_event(events: list, groups12: list, d12: dict, mkt: dict) -> list[list]:
    """Mean absolute group-minus-market move on event days vs all days (d0)."""
    all_abs = []
    for d, vals in d12.items():
        if d.year < 1994 or d not in mkt:
            continue
        all_abs += [abs(vals[g] - mkt[d]) for g in groups12 if g in vals]
    base = statistics.mean(all_abs) if all_abs else None
    out = []
    for t in MARKET_TYPES + [REG]:
        es = [e for e in events if e["type"] == t and e["role"] == "main" and e.get("day0")]
        vals = []
        for e in es:
            d = e["day0"]
            if d not in d12 or d not in mkt:
                continue
            gs = groups12 if e["level"] == "market" else [g for g in e["groups12"].split(";") if g]
            vals += [abs(d12[d][g] - mkt[d]) for g in gs if g in d12[d]]
        m = statistics.mean(vals) if vals else None
        out.append([t, len(es), fmt(None if m is None else 100 * m), fmt(None if base is None else 100 * base),
                    fmt(None if not (m and base) else m / base, 2)])
    return out


# ------------------------------------------------------------- SEC search --

class RateLimiter:
    def __init__(self, per_sec: float):
        self.gap = 1.0 / per_sec
        self.lock = threading.Lock()
        self.next = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            t = max(now, self.next)
            self.next = t + self.gap
        if t > now:
            time.sleep(t - now)


SEC_LIMIT = RateLimiter(SEC_RATE)


def sec_get(params: dict) -> dict:
    SEC_LIMIT.wait()
    return json.loads(ces.get(EDGAR_FTS, params, headers={"User-Agent": SEC_UA}, tries=4))


def fts_range(base: dict, start: dt.date, end: dt.date, depth: int = 0) -> tuple[list, int]:
    """All hits for one query between two dates; splits ranges over 9,500 hits."""
    p = dict(base, dateRange="custom", startdt=start.isoformat(), enddt=end.isoformat())
    data = sec_get(p)
    tot = data.get("hits", {}).get("total", {})
    total, rel = int(tot.get("value", 0)), tot.get("relation", "eq")
    if (rel == "gte" or total >= 9500) and end > start and depth < 8:
        mid = start + (end - start) // 2
        a, na = fts_range(base, start, mid, depth + 1)
        b, nb = fts_range(base, mid + dt.timedelta(days=1), end, depth + 1)
        return a + b, na + nb
    hits = list(data.get("hits", {}).get("hits", []))
    frm = len(hits)
    while frm < min(total, 9900) and frm > 0:
        page = sec_get(dict(p, **{"from": frm})).get("hits", {}).get("hits", [])
        if not page:
            break
        hits += page
        frm += len(page)
    slim = []
    for h in hits:
        s = h.get("_source", {})
        slim.append([s.get("file_date", ""), s.get("form", ""),
                     s.get("adsh") or str(h.get("_id", "")).split(":")[0],
                     s.get("ciks") or [], s.get("display_names") or [], s.get("items") or []])
    return slim, len(hits)


def months(start: dt.date, end: dt.date):
    d = dt.date(start.year, start.month, 1)
    while d <= end:
        nxt = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        yield d, min(nxt - dt.timedelta(days=1), end)
        d = nxt


def pull_edgar(skip: bool) -> tuple[dict, dict]:
    """EDGAR full-text search hits per query, from the cache plus fresh months."""
    results: dict = defaultdict(list)
    stats = {"fetched": 0, "cached": 0, "missing": 0, "errors": 0, "doc_hits": Counter()}
    tasks = []
    refresh_from = TODAY - dt.timedelta(days=FTS_REFRESH_DAYS)
    for key, q in FTS_QUERIES.items():
        for a, b in months(FTS_START, TODAY):
            path = CACHE / "fts" / key / f"{a:%Y-%m}.json"
            if path.exists() and (b < refresh_from or skip):
                try:
                    blob = json.loads(path.read_text())
                    results[key] += blob["hits"]
                    stats["doc_hits"][key] += blob.get("doc_hits", len(blob["hits"]))
                    stats["cached"] += 1
                    continue
                except (ValueError, KeyError):
                    pass
            if skip:
                stats["missing"] += 1
                continue
            tasks.append((key, q, a, b, path))
    t0 = time.monotonic()
    lock = threading.Lock()

    def run(task):
        key, q, a, b, path = task
        if time.monotonic() - t0 > EDGAR_BUDGET:
            return key, None, 0, "budget"
        try:
            hits, n = fts_range(q, a, b)
        except Exception as e:  # noqa: BLE001
            return key, None, 0, f"{type(e).__name__}: {str(e)[:80]}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"hits": hits, "doc_hits": n}))
        return key, hits, n, ""

    errors = Counter()
    if tasks:
        print(f"EDGAR: {len(tasks)} query-months to fetch, {stats['cached']} cached")
        with ThreadPoolExecutor(max_workers=8) as pool:
            for fut in as_completed([pool.submit(run, t) for t in tasks]):
                key, hits, n, err = fut.result()
                with lock:
                    if hits is None:
                        stats["missing"] += 1
                        errors[err.split(":")[0]] += 1
                    else:
                        results[key] += hits
                        stats["doc_hits"][key] += n
                        stats["fetched"] += 1
    stats["errors"] = sum(v for k, v in errors.items() if k != "budget")
    if stats["missing"]:
        gaps.append(f"EDGAR search: {stats['missing']} query-months not fetched this run "
                    f"({', '.join(f'{k} {v}' for k, v in errors.items()) or 'skipped'}); "
                    "they are fetched next run and the counts below are short until then.")
    check("EDGAR search pulled", stats["missing"] == 0,
          f"{stats['fetched']} query-months fetched, {stats['cached']} from cache, "
          f"{stats['missing']} missing, in {time.monotonic() - t0:,.0f}s")
    return results, stats


# ---------------------------------------------------------------- Sharadar --

class Prices:
    """Daily total-return closes per ticker, and peer and market averages."""

    def __init__(self):
        self.d = {}          # ticker -> array('i') ordinals
        self.c = {}          # ticker -> array('d') closes adjusted for splits and dividends
        self.group_sum = defaultdict(lambda: defaultdict(float))
        self.group_n = defaultdict(lambda: defaultdict(int))
        self.mkt_sum = defaultdict(float)
        self.mkt_n = defaultdict(int)
        self.ordinary_abs = []   # sorted sample of |stock - peers| over ordinary stock-days

    def peer(self, group: str, day: int) -> float | None:
        n = self.group_n[group].get(day, 0)
        return self.group_sum[group][day] / n if n >= MIN_PEERS else None

    def market(self, day: int) -> float | None:
        n = self.mkt_n.get(day, 0)
        return self.mkt_sum[day] / n if n >= 50 else None

    def ret(self, t: str, k: int) -> float | None:
        ds, cs = self.d[t], self.c[t]
        if k <= 0 or k >= len(ds) or ds[k] - ds[k - 1] > 7 or cs[k - 1] <= 0:
            return None
        return cs[k] / cs[k - 1] - 1


def load_sharadar(info: dict, cik_map: dict) -> tuple[Prices, dict, dict]:
    key = fcd._api_key()
    fcd.RAW = ROOT / "raw" / "sharadar"
    paths = {}
    for t in ("tickers", "stocks", "events", "actions"):
        p = fcd.RAW / f"{t}.zip"
        if not p.exists() or (time.time() - p.stat().st_mtime) > 6 * 3600:
            t0 = time.time()
            p = fcd.download_table(t, key)
            print(f"downloaded {t} in {time.time() - t0:,.0f}s")
        paths[t] = p

    header, rows = fcd.open_rows(paths["tickers"])
    ix = {h: i for i, h in enumerate(header)}
    for r in rows:
        if len(r) < len(header):
            continue
        if r[ix["table"]].strip().upper() not in ("SEP", "SF1"):
            continue
        t = r[ix["ticker"]]
        cat = r[ix["category"]].strip().lower()
        if "common" not in cat or "warrant" in cat or "preferred" in cat:
            continue
        rec = info.setdefault(t, {"group": "", "cik": "", "bench": "secondary" not in cat,
                                  "name": r[ix["name"]] if "name" in ix else ""})
        rec["group"] = rec["group"] or r[ix["famaindustry"]].strip()
        m = re.search(r"cik[=/]?0*(\d{1,10})", r[ix["secfilings"]] if "secfilings" in ix else "", re.I)
        if m and not rec["cik"]:
            rec["cik"] = m.group(1).zfill(10)
    for t, rec in info.items():
        if rec["cik"]:
            cik_map.setdefault(rec["cik"], []).append(t)
    print(f"tickers: {len(info):,} common stocks, {len(cik_map):,} SEC numbers")

    px = Prices()
    t0 = time.time()
    header, rows = fcd.open_rows(paths["stocks"])
    ix = {h: i for i, h in enumerate(header)}
    i_t, i_d = ix["ticker"], ix["date"]
    i_c = ix.get("closeadj", ix["close"])
    i_u = ix.get("closeunadj", ix["close"])
    tmp_d, tmp_c, tmp_u = (defaultdict(lambda: array("i")), defaultdict(lambda: array("d")),
                           defaultdict(lambda: array("f")))
    n = 0
    for r in rows:
        if len(r) < len(header):
            continue
        t = r[i_t]
        if t not in info:
            continue
        try:
            d = dt.date.fromisoformat(r[i_d][:10]).toordinal()
            c = float(r[i_c])
            u = float(r[i_u] or 0)
        except ValueError:
            continue
        if c <= 0:
            continue
        tmp_d[t].append(d)
        tmp_c[t].append(c)
        tmp_u[t].append(u)
        n += 1
    print(f"prices: {n:,} rows, {len(tmp_d):,} tickers in {time.time() - t0:,.0f}s")
    unadj = {}
    for t in list(tmp_d):
        ds = tmp_d.pop(t)
        if all(ds[k] < ds[k + 1] for k in range(len(ds) - 1)):
            px.d[t], px.c[t], unadj[t] = ds, tmp_c.pop(t), tmp_u.pop(t)
        else:
            order = sorted(range(len(ds)), key=ds.__getitem__)
            cs, us = tmp_c.pop(t), tmp_u.pop(t)
            px.d[t] = array("i", (ds[k] for k in order))
            px.c[t] = array("d", (cs[k] for k in order))
            unadj[t] = array("f", (us[k] for k in order))
    # Peer (French group) and market averages: equal-weighted, clipped returns
    # of primary common stocks whose prior close was at least $1.
    for t, ds in px.d.items():
        rec = info[t]
        if not rec["bench"]:
            continue
        g, us = rec["group"], unadj[t]
        gs, gn = px.group_sum[g], px.group_n[g]
        for k in range(1, len(ds)):
            if us[k - 1] < MIN_PRICE:
                continue
            r = px.ret(t, k)
            if r is None:
                continue
            r = min(max(r, CLIP_LO), CLIP_HI)
            day = ds[k]
            if g:
                gs[day] += r
                gn[day] += 1
            px.mkt_sum[day] += r
            px.mkt_n[day] += 1
    # Ordinary-day baseline: |stock - peers| on every 7th stock-day, for a median.
    sample = array("f")
    step = 0
    for t, ds in px.d.items():
        g = info[t]["group"]
        if not g:
            continue
        gs, gn = px.group_sum[g], px.group_n[g]
        for k in range(1, len(ds)):
            step += 1
            if step % 7:
                continue
            n_ = gn.get(ds[k], 0)
            r = px.ret(t, k)
            if r is None or n_ < MIN_PEERS:
                continue
            sample.append(abs(r - gs[ds[k]] / n_))
    px.ordinary_abs = sorted(sample)
    print(f"peer averages built in {time.time() - t0:,.0f}s")

    codes = defaultdict(lambda: defaultdict(list))   # code -> ticker -> [ordinal]
    code_rows = Counter()
    header, rows = fcd.open_rows(paths["events"])
    ix = {h: i for i, h in enumerate(header)}
    want = set(CODE_ITEMS) | {"11"}
    for r in rows:
        if len(r) < len(header):
            continue
        cs = {c.strip() for c in r[ix["eventcodes"]].split("|") if c.strip()}
        for c in cs:
            code_rows[c] += 1
        hit = cs & want
        if not hit:
            continue
        try:
            d = dt.date.fromisoformat(r[ix["date"]][:10]).toordinal()
        except ValueError:
            continue
        for c in hit:
            codes[c][r[ix["ticker"]]].append(d)

    actions = defaultdict(list)                      # action -> [(ticker, ordinal, value, contra)]
    header, rows = fcd.open_rows(paths["actions"])
    ix = {h: i for i, h in enumerate(header)}
    keep = {"dividend", "split", "acquisitionby", "acquisitionof", "mergerfrom", "mergerto",
            "bankruptcyliquidation", "regulatorydelisting"}
    for r in rows:
        if len(r) < len(header):
            continue
        a = r[ix["action"]].strip()
        if a not in keep:
            continue
        try:
            d = dt.date.fromisoformat(r[ix["date"]][:10]).toordinal()
        except ValueError:
            continue
        actions[a].append((r[ix["ticker"]], d, ces.to_float(r[ix["value"]]),
                           r[ix["contraticker"]].strip() if "contraticker" in ix else ""))
    return px, {"codes": codes, "code_rows": code_rows}, actions


# ----------------------------------------------------------- company types --

def pick_ticker(cik_map: dict, px: Prices, cik: str, day: int) -> str | None:
    best, size = None, -1
    for t in cik_map.get(cik.zfill(10), []):
        ds = px.d.get(t)
        if not ds or not (ds[0] <= day <= ds[-1] + 5):
            continue
        if len(ds) > size:
            best, size = t, len(ds)
    return best


def subject_ticker(cik_map, px, ciks: list, day: int) -> tuple[str | None, str]:
    found = {t for t in (pick_ticker(cik_map, px, c, day) for c in ciks) if t}
    if len(found) == 1:
        return found.pop(), ""
    return None, "ambiguous" if found else "no listed company"


def build_company(px: Prices, info: dict, cik_map: dict, sh: dict, actions: dict,
                  fts: dict) -> tuple[list, Counter]:
    out: list[dict] = []
    unmatched = Counter()
    codes = sh["codes"]

    def add(ticker, day, etype, sub, role, source, ref="", detail="", later=False, cik=""):
        if ticker not in info:
            unmatched[f"{sub}: not a common stock in Sharadar's ticker list"] += 1
            return
        d = dt.date.fromordinal(day)
        out.append(ev("company", etype, sub, role, d, source, ref=ref, detail=detail,
                      ticker=ticker, cik=cik or info.get(ticker, {}).get("cik", ""),
                      group=info.get(ticker, {}).get("group", ""),
                      later_filing="yes" if later else ""))

    # 8-K items from Sharadar's events table.
    for code, (etype, sub, role) in CODE_ITEMS.items():
        if code in ("22", "71"):
            continue
        for t, days in codes.get(code, {}).items():
            for day in sorted(set(days)):
                add(t, day, etype, sub, role, "Sharadar 8-K events", ref=f"code {code}")

    # Guidance: 2.02 filings off the company's own schedule; 7.01 alone off it.
    r202 = codes.get("22", {})
    for t, days in r202.items():
        for day in guidance_offcycle(days):
            add(t, day, GUIDE, CODE_ITEMS["22"][1], "main", "Sharadar 8-K events", ref="code 22")
    for t, days in codes.get("71", {}).items():
        res = sorted(set(r202.get(t, [])))
        if len(res) < 4:
            continue
        for day in sorted(set(days)):
            j = bisect_left(res, day - 3)
            if j < len(res) and res[j] <= day + 3:
                continue
            if day - res[0] < 365 or day > res[-1] + 120:
                continue
            add(t, day, GUIDE, CODE_ITEMS["71"][1], "cross-check", "Sharadar 8-K events", ref="code 71")

    # Capital structure: dividend breaks from the dividend history.
    splits = defaultdict(list)
    for t, d, _, _ in actions.get("split", []):
        splits[t].append(d)
    pays = defaultdict(list)
    for t, d, v, _ in actions.get("dividend", []):
        if v and v > 0:
            pays[t].append((d, v))
    for t, ps in pays.items():
        if t not in info:
            continue
        for day, sub, det in dividend_breaks(ps, splits.get(t, []), px.d.get(t)):
            add(t, day, CAP, sub, "main", "Sharadar corporate actions: dividends", detail=det)

    # Corporate actions: completed deals, bankruptcy and regulatory delistings.
    for t, d, _, contra in actions.get("acquisitionby", []) + actions.get("mergerfrom", []):
        add(t, d, MNA, "target: deal completed", "main", "Sharadar corporate actions",
            detail=f"buyer {contra or 'not listed'}")
    for t, d, _, contra in actions.get("acquisitionof", []) + actions.get("mergerto", []):
        if t in info and t not in ("N/A", ""):
            add(t, d, MNA, "buyer: deal completed", "main", "Sharadar corporate actions",
                detail=f"target {contra}")
    for t, d, _, _ in actions.get("bankruptcyliquidation", []):
        add(t, d, DIST, "delisted after bankruptcy or liquidation", "main", "Sharadar corporate actions")
    for t, d, _, _ in actions.get("regulatorydelisting", []):
        add(t, d, ACCT, "delisted by the exchange or regulator", "main", "Sharadar corporate actions")

    # EDGAR: one event per filing (accession number), tied to the subject company.
    def filings(*keys):
        seen = {}
        for k in keys:
            for fd, form, adsh, ciks, names, items in fts.get(k, []):
                if adsh and adsh not in seen:
                    seen[adsh] = (fd, form, ciks, names, items, k)
        return seen

    def edgar_add(keys, etype, sub, role, form_ok=None, need_prior=False):
        n = 0
        for adsh, (fd, form, ciks, names, items, k) in filings(*keys).items():
            if form_ok and form not in form_ok:
                continue
            d = ces.to_date(fd)
            if not d:
                continue
            day = d.toordinal()
            t, why = subject_ticker(cik_map, px, ciks, day)
            if not t:
                unmatched[f"{sub}: {why}"] += 1
                continue
            if need_prior:
                ds = px.d[t]
                if bisect_left(ds, day) < MIN_PRIOR_DAYS:
                    unmatched[f"{sub}: under {MIN_PRIOR_DAYS} days of trading before (IPO)"] += 1
                    continue
            add(t, day, etype, sub, role, f"SEC EDGAR {form}", ref=adsh)
            n += 1
        return n

    edgar_add(["13d", "13d_new"], ACTIV, "13D stake of 5% or more", "main",
              form_ok={"SC 13D", "SCHEDULE 13D"})
    edgar_add(["tender"], MNA, "target: tender offer filed", "main", form_ok={"SC TO-T"})
    edgar_add(["nt10k"], ACCT, "late annual report notice (NT 10-K)", "main", form_ok={"NT 10-K"})
    edgar_add(["nt10q"], ACCT, "late quarterly report notice (NT 10-Q)", "main", form_ok={"NT 10-Q"})
    edgar_add(["424b4", "424b5_shares"], CAP, "new share offering", "main",
              form_ok={"424B4", "424B5"}, need_prior=True)

    # Merger proxies: the first PREM14A or DEFM14A per company within a year.
    proxy = defaultdict(list)
    for adsh, (fd, form, ciks, names, items, k) in filings("prem14a", "defm14a").items():
        d = ces.to_date(fd)
        if not d or form not in ("PREM14A", "DEFM14A"):
            continue
        t, why = subject_ticker(cik_map, px, ciks, d.toordinal())
        if t:
            proxy[t].append((d.toordinal(), adsh))
        else:
            unmatched[f"merger proxy: {why}"] += 1
    for t, items in proxy.items():
        last = None
        for day, adsh in sorted(items):
            if last is None or day - last > 365:
                add(t, day, MNA, "target: merger proxy filed", "main", "SEC EDGAR PREM14A/DEFM14A",
                    ref=adsh)
            last = day

    # Merger announcements: the earliest 8-K item 1.01 in the 90 days before the
    # target's first deal filing (tender offer, board response or proxy).
    anchors = defaultdict(list)
    for e in out:
        if e["type"] == MNA and e["subtype"] in ("target: tender offer filed",
                                                 "target: merger proxy filed"):
            anchors[e["ticker"]].append(e["date"].toordinal())
    for adsh, (fd, form, ciks, names, items, k) in filings("tender_response").items():
        d = ces.to_date(fd)
        if d and form == "SC 14D9":
            t, _ = subject_ticker(cik_map, px, ciks, d.toordinal())
            if t:
                anchors[t].append(d.toordinal())
    c11 = codes.get("11", {})
    announced = {}                     # ticker -> [announcement ordinals]
    for t, days in anchors.items():
        k11 = sorted(set(c11.get(t, [])))
        used = set()
        last_anchor = None
        for a in sorted(set(days)):
            if last_anchor is not None and a - last_anchor <= 180:
                continue
            last_anchor = a
            j = bisect_left(k11, a - ANNOUNCE_LOOKBACK)
            if j < len(k11) and k11[j] <= a and k11[j] not in used:
                used.add(k11[j])
                announced.setdefault(t, []).append(k11[j])
                add(t, k11[j], MNA, "target: deal announced (8-K 1.01 before the deal filing)",
                    "main", "Sharadar 8-K events + SEC EDGAR", ref="code 11",
                    detail=f"picked out by the deal filing on {dt.date.fromordinal(a)}", later=True)
    # Buyers: the target's announcement, when the completed deal names a listed buyer.
    for t, d, _, contra in actions.get("acquisitionby", []):
        if not contra or contra in ("N/A",) or contra not in info:
            continue
        cands = [a for a in announced.get(t, []) if d - 450 <= a <= d]
        if cands:
            add(contra, max(cands), MNA, "buyer: deal announced (from the target's filing)", "main",
                "Sharadar corporate actions + 8-K events", detail=f"target {t}", later=True)

    # Leadership: 8-Ks tagged item 5.02 that name the CEO or CFO with resign or retire.
    lead = defaultdict(set)
    for k, role_name in (("ceo_resign", "CEO"), ("ceo_retire", "CEO"),
                         ("cfo_resign", "CFO"), ("cfo_retire", "CFO")):
        for fd, form, adsh, ciks, names, items in fts.get(k, []):
            if form != "8-K" or "5.02" not in (items or []):
                continue
            lead[(adsh, fd, tuple(ciks))].add(role_name)
    abrupt = {h[2] for h in fts.get("immediate", [])}
    for (adsh, fd, ciks), roles in lead.items():
        d = ces.to_date(fd)
        if not d:
            continue
        t, why = subject_ticker(cik_map, px, list(ciks), d.toordinal())
        if not t:
            unmatched[f"leadership: {why}"] += 1
            continue
        who = "CEO" if "CEO" in roles else "CFO"
        how = "effective immediately" if adsh in abrupt else "other wording"
        add(t, d.toordinal(), LEAD, f"{who} exit ({how})", "main", "SEC EDGAR 8-K item 5.02 text",
            ref=adsh, detail="CEO and CFO" if len(roles) > 1 else "")

    # One row per ticker, day, type and subtype.
    uniq = {}
    for e in out:
        uniq.setdefault((e["ticker"], e["date"], e["type"], e["subtype"]), e)
    return list(uniq.values()), unmatched


def company_returns(events: list, px: Prices) -> None:
    """Stock, peer, market and stock-minus-peer returns per window (decimals)."""
    for e in events:
        t = e["ticker"]
        ds = px.d.get(t)
        e["day0"] = None
        if not ds:
            continue
        day = e["date"].toordinal()
        i = bisect_left(ds, day)
        if i >= len(ds) or ds[i] - day > 5:
            continue
        e["day0"] = dt.date.fromordinal(ds[i])
        g = e.get("group", "")
        for w, a, b in WINDOWS:
            ks = range(i + a, i + b + 1)
            if i + a < 1 or i + b >= len(ds):
                continue
            s = compound([px.ret(t, k) for k in ks])
            p = compound([px.peer(g, ds[k]) for k in ks]) if g else None
            m = compound([px.market(ds[k]) for k in ks])
            e[f"stock_{w}"], e[f"peer_{w}"], e[f"mkt_{w}"] = s, p, m
            e[f"abn_{w}"] = None if s is None or p is None else s - p


# ------------------------------------------------------- look-ahead tests --

def truncation_tests(series_store: dict, sh: dict | None, actions: dict | None,
                     px: Prices | None) -> None:
    """Rerun each point-in-time rule on data cut a year back; compare."""
    for label, key, fn in (("Geopolitical risk spikes", "GPR",
                            lambda s, u: expanding_spikes(s, SPIKE_PCT, SPIKE_MIN_OBS, SPIKE_GAP, u)),
                           ("Policy uncertainty spikes", "EPU",
                            lambda s, u: expanding_spikes(s, SPIKE_PCT, SPIKE_MIN_OBS, SPIKE_GAP, u)),
                           ("Oil price moves", "WTI", lambda s, u: oil_moves(s, u))):
        s = series_store.get(key)
        if not s:
            continue
        full = [x[0] for x in fn(s, None) if x[0] <= CUTOFF]
        cut = [x[0] for x in fn({d: v for d, v in s.items() if d <= CUTOFF}, None)]
        check(f"No look-ahead: {label}", full == cut,
              f"{len(full)} events up to {CUTOFF} with all data, {len(cut)} with data cut at "
              f"{CUTOFF}; {'identical' if full == cut else 'they differ'}")
    if sh:
        cut = CUTOFF.toordinal()
        diff = total = 0
        for t, days in list(sh["codes"].get("22", {}).items())[:3000]:
            a = [d for d in guidance_offcycle(days) if d <= cut]
            b = guidance_offcycle([d for d in days if d <= cut])
            total += len(a)
            diff += a != b
        check("No look-ahead: off-cycle guidance", diff == 0,
              f"3,000 companies' off-cycle 2.02 days up to {CUTOFF} ({total:,} events) rerun with "
              f"later filings deleted: {diff} companies differ")
    if actions and px:
        cut = CUTOFF.toordinal()
        splits = defaultdict(list)
        for t, d, _, _ in actions.get("split", []):
            splits[t].append(d)
        pays = defaultdict(list)
        for t, d, v, _ in actions.get("dividend", []):
            if v and v > 0:
                pays[t].append((d, v))
        diff = total = 0
        for t, ps in list(pays.items())[:3000]:
            pdays = px.d.get(t)
            a = [x for x in dividend_breaks(ps, splits.get(t, []), pdays) if x[0] <= cut]
            tp = array("i", (d for d in pdays if d <= cut)) if pdays is not None else None
            b = dividend_breaks([p for p in ps if p[0] <= cut], [s for s in splits.get(t, []) if s <= cut],
                                tp, cut)
            total += len(a)
            diff += [x[:2] for x in a] != [x[:2] for x in b]
        check("No look-ahead: dividend breaks", diff == 0,
              f"3,000 payers' breaks up to {CUTOFF} ({total:,} events) rerun with later payments "
              f"and prices deleted: {diff} payers differ")


# ------------------------------------------------------------------ checks --

def date_checks(events: list, label: str) -> None:
    bad_future = sum(1 for e in events if e["date"] > TODAY)
    bad_public = sum(1 for e in events if e["public_from"] > e["date"] or
                     (e.get("day0") and e["public_from"] > e["day0"]))
    bad_day0 = sum(1 for e in events if e.get("day0") and e["day0"] < e["date"])
    no_day0 = sum(1 for e in events if not e.get("day0"))
    check(f"Dates: {label}", bad_future == 0 and bad_public == 0 and bad_day0 == 0,
          f"{len(events):,} events; {bad_future} dated after today; {bad_public} public after "
          f"day 0; {bad_day0} with day 0 before the event date; {no_day0:,} with no trading "
          "day within 5 days (no returns)")


def read_prior_codes() -> dict:
    p = SOURCE_CHECK / "sharadar_event_codes.csv"
    if not p.exists():
        return {}
    with p.open() as f:
        return {r["code"]: int(r["rows"]) for r in csv.DictReader(f)}


def count_checks(market: list, industry: list, company: list, sh: dict | None,
                 edgar_stats: dict | None) -> None:
    def n(evs, t, sub=None, role="main"):
        return sum(1 for e in evs if e["type"] == t and (sub is None or e["subtype"] == sub)
                   and (role is None or e["role"] == role))

    # Market-wide: the write-up counted top-5% days over the whole sample;
    # the expanding rule here only compares with earlier days, so counts move.
    for t, sub, wrote, lo in ((GEO, "risk index spike", 135, 30),
                              (ELECT, "policy uncertainty spike", 131, 30)):
        k = n(market, t, sub)
        check(f"Count: {t} ({sub})", k >= lo and 0.4 * wrote <= k <= 2.5 * wrote,
              f"{k} episodes (write-up: {wrote} with whole-sample top-5% days; this rule uses only "
              "earlier days)")
    pres = n(market, ELECT, "presidential election")
    mid = n(market, ELECT, "midterm election")
    exp_p = sum(1 for d, k in election_days() if "presidential" in k)
    exp_m = sum(1 for d, k in election_days() if "midterm" in k)
    check("Count: elections", (pres, mid) == (exp_p, exp_m) and pres >= 8,
          f"{pres} presidential and {mid} midterm since 1994 (write-up: 8 and 9, before the "
          "Nov 3, 2026 midterm)")
    k = n(market, ENERGY)
    check(f"Count: {ENERGY}", k >= 30, f"{k} big one-day oil moves since 1988")
    k = n(market, TRADE)
    check(f"Count: {TRADE}", k >= 30, f"{k} days with tariff actions (main)")
    if company:
        prior = read_prior_codes()
        if sh:
            for code in sorted(CODE_ITEMS):
                now, was = sh["code_rows"].get(code, 0), prior.get(code)
                if was:
                    check(f"Count: Sharadar code {code}", was * 0.98 <= now <= was * 1.05,
                          f"{now:,} rows now vs {was:,} in the Nov 27 source check")
        for t, sub, wrote in ((CAP, "dividend cut of 25% or more", 3137),
                              (CAP, "dividend stopped (no payment for 200 days)", 994),
                              (MNA, "target: deal completed", 8270),
                              (DIST, "delisted after bankruptcy or liquidation", 3337),
                              (ACCT, "delisted by the exchange or regulator", 1010)):
            k = n(company, t, sub)
            check(f"Count: {sub}", 0.5 * wrote <= k <= 1.5 * wrote,
                  f"{k:,} (write-up: {wrote:,}; differences come from the point-in-time rules "
                  "and one row per company and day)")
        for t in COMPANY_TYPES:
            k = n(company, t)
            check(f"Count: {t} (main rows)", k >= 30, f"{k:,} company events")
    if edgar_stats:
        quarters = max(1, ((TODAY - FTS_START).days / 91.3))
        for key, wrote in (("13d", 1586), ("nt10k", None), ("tender", 200)):
            dh = edgar_stats["doc_hits"].get(key, 0)
            if wrote:
                check(f"Count: EDGAR {FTS_QUERIES[key]['forms']}", 0.4 * wrote <= dh / quarters <= 2 * wrote,
                      f"about {dh / quarters:,.0f} documents a quarter (write-up: about {wrote:,})")


# ------------------------------------------------------------------ output --

EVENT_COLS = ["event_id", "level", "type", "subtype", "role", "date", "day0", "public_from",
              "source", "ref", "detail"]


def event_rows(events: list, extra: list) -> list:
    return [[iso(e.get(c)) for c in EVENT_COLS + extra] for e in
            sorted(events, key=lambda e: (e["date"], e["type"], e["subtype"]))]


def company_summary(events: list, px: Prices) -> list:
    o = px.ordinary_abs
    base = o[len(o) // 2] if o else None
    groups = defaultdict(list)
    for e in events:
        groups[(e["type"], e["subtype"], e["role"], e["source"])].append(e)
    rows = []
    for (t, sub, role, src), es in sorted(groups.items(), key=lambda kv: (ALL_TYPES.index(kv[0][0]),
                                                                          kv[0][2], kv[0][1])):
        d0 = [abs(e["abn_d0"]) for e in es if e.get("abn_d0") is not None]
        d01 = [e["abn_d01"] for e in es if e.get("abn_d01") is not None]
        post = [e["abn_post20"] for e in es if e.get("abn_post20") is not None]
        md0 = statistics.median(d0) if d0 else None
        rows.append([t, sub, role, src, len(es), len({e["ticker"] for e in es}),
                     iso(min(e["date"] for e in es)), iso(max(e["date"] for e in es)),
                     len(d01), fmt(100 * md0 if md0 is not None else None),
                     fmt(100 * base if base else None),
                     fmt(md0 / base if md0 is not None and base else None, 2),
                     fmt(100 * statistics.median(d01) if d01 else None),
                     fmt(100 * statistics.mean(d01) if d01 else None),
                     fmt(100 * statistics.median(post) if post else None),
                     sum(1 for e in es if e.get("later_filing"))])
    return rows


def counts_by_year(events: list) -> list:
    c = Counter((e["type"], e["role"], e["date"].year) for e in events)
    years = sorted({y for _, _, y in c})
    rows = []
    for t in ALL_TYPES:
        for role in ("main", "cross-check", "unmapped"):
            if any(c.get((t, role, y)) for y in years):
                rows.append([t, role] + [c.get((t, role, y), 0) for y in years])
    return [["type", "role"] + years] + rows


def spot_checks(market: list, industry: list, d12: dict, mkt: dict) -> None:
    def near(t, day, sub=None, within=3):
        return [e for e in market + industry if e["type"] == t and (sub is None or sub in e["subtype"])
                and abs((e["date"] - day).days) <= within]
    found = []
    for t, d, what, sub in ((GEO, dt.date(2022, 2, 24), "Russia invades Ukraine", None),
                            (ENERGY, dt.date(2020, 3, 9), "oil price war crash", "drop"),
                            (ENERGY, dt.date(2008, 9, 22), "oil jump", None),
                            (ELECT, dt.date(2016, 11, 8), "2016 election", "presidential"),
                            (TRADE, dt.date(2025, 4, 2), "reciprocal tariffs", None),
                            (TRADE, dt.date(2018, 3, 8), "steel and aluminum tariffs (Section 232)", None)):
        hit = near(t, d, sub)
        found.append(f"{what} ({d}): {'found' if hit else 'not found'}")
    ok = sum("found" in f and "not found" not in f for f in found)
    check("Spot check: known events present", ok >= 5, "; ".join(found))
    d = dt.date(2020, 3, 9)
    if d in d12 and d in mkt:
        ex = 100 * (d12[d].get("Enrgy", 0) - mkt[d])
        check("Spot check: energy on the Mar 9, 2020 oil crash", ex < -5,
              f"energy minus market {ex:+.1f}% that day")


def report(market, industry, company, pending, ordinary_rows, comp_rows, unmatched,
           french_last, edgar_stats) -> None:
    by_type = Counter((e["type"], e["role"]) for e in market + industry + company)
    lines = ["# Event data check report", "",
             f"Run: {TODAY}. Written by `scripts/build_event_data.py`. Event types: "
             "`docs/event-types.md`; sources: `docs/event-sources.md`; write-up: `docs/event-data.md`.",
             "", "## Events by type", "",
             "| Type | Level | Main | Cross-check | Unmapped | First | Last |", "|---|---|---|---|---|---|---|"]
    for t in ALL_TYPES:
        es = [e for e in market + industry + company if e["type"] == t]
        if not es:
            lines.append(f"| {t} | | 0 | 0 | 0 | | |")
            continue
        lines.append(f"| {t} | {es[0]['level']} | {by_type[(t, 'main')]:,} | {by_type[(t, 'cross-check')]:,} | "
                     f"{by_type[(t, 'unmapped')]:,} | {iso(min(e['date'] for e in es))} | "
                     f"{iso(max(e['date'] for e in es))} |")
    lines += ["", "## Checks", "", "| Check | Status | Detail |", "|---|---|---|"]
    for c in checks:
        lines.append(f"| {c['check']} | {c['status']} | {c['detail'].replace('|', '/')} |")
    lines += ["", "## Event days against ordinary days (sector level, day 0)", "",
              "Mean absolute group-minus-market move on event days, against every day since 1994, "
              "French's 12 groups. A ratio above 1 means event days move groups more than usual.", "",
              "| Type | Events | Event days (%) | All days (%) | Ratio |", "|---|---|---|---|---|"]
    for r in ordinary_rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    if comp_rows:
        lines += ["", "## Company events: moves against peers", "",
                  "Stock minus its French group (equal-weighted peers). Abs d0 is the median absolute "
                  "day-0 move beyond peers; the ordinary-day figure is the same over a sample of every "
                  "stock-day. "
                  "d01 is days 0 and 1; post20 is days 2 to 21 (drift). Per-company rows stay on the "
                  "runner (licence).", "",
                  "| Type | Subtype | Role | Events | Companies | With returns | Median abs d0 (%) | "
                  "Ordinary (%) | Ratio | Median d01 (%) | Median post20 (%) | Picked with a later filing |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in comp_rows:
            lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[4]:,} | {r[5]:,} | {r[8]:,} | {r[9]} | "
                         f"{r[10]} | {r[11]} | {r[12]} | {r[14]} | {r[15]:,} |")
    lines += ["", "## Gaps", ""]
    if pending:
        gaps.append("Sector moves wait for French's data, which ends "
                    f"{french_last}: " + ", ".join(f"{t} {n}" for t, n in pending.items())
                    + " events have no full set of windows yet.")
    if unmatched:
        gaps.append("Company filings not tied to a stock: " + ", ".join(
            f"{k} {v:,}" for k, v in unmatched.most_common(12)))
    gaps.append("Filing times: Sharadar and EDGAR search give filing dates only, so the main company "
                "window is days 0 and 1, which covers filings after the 4 PM close.")
    gaps.append("Merger announcements are picked out by the deal filing that follows them: the 8-K "
                "was public that day, but choosing it uses a later filing (flagged later_filing).")
    gaps.append("OPEC meeting dates are not in v1 (agreed Nov 27); energy shocks are big oil moves.")
    gaps.append("SEC enforcement actions are not in v1 (names only, no company numbers).")
    for g in gaps:
        lines.append(f"- {g}")
    if notes:
        lines += ["", "## Notes", ""] + [f"- {n_}" for n_ in notes]
    (OUT / "EVENT_DATA_CHECK.md").write_text("\n".join(lines) + "\n")


# -------------------------------------------------------------------- main --

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-company", action="store_true", help="market and industry only")
    ap.add_argument("--skip-edgar", action="store_true", help="use cached EDGAR results only")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    market: list[dict] = []
    industry: list[dict] = []
    series_store: dict = {}
    pull_gpr(market, series_store)
    pull_tpu(market, series_store)
    pull_epu(market, series_store)
    pull_elections(market)
    pull_oil(market, series_store)
    pull_trade(market)
    pull_regulation(industry)

    g12, d12 = read_french("industry12_daily_vw.csv")
    g49, d49 = read_french("industry49_daily_vw.csv")
    _, ff = read_french("ff_factors_daily.csv")
    mkt = {d: v["mkt_rf"] + v["rf"] for d, v in ff.items() if "mkt_rf" in v and "rf" in v}
    cal = Calendar([d for d in mkt if d.year >= 1985])
    rows12, rows49, pending = sector_moves(market, g12, d12, g49, d49, mkt, cal, all_groups=True)
    r12i, r49i, pend_i = sector_moves(industry, g12, d12, g49, d49, mkt, cal, all_groups=False)
    pending.update(pend_i)
    win_cols = [f"ex_{w}" for w, _, _ in WINDOWS]
    write_csv(OUT / "market_events.csv", EVENT_COLS, event_rows(market, []))
    write_csv(OUT / "regulatory_events.csv", EVENT_COLS + ["groups12", "groups49"],
              event_rows(industry, ["groups12", "groups49"]))
    write_csv(OUT / "sector_moves_12.csv", ["event_id", "grouping", "group"] + win_cols, rows12 + r12i)
    write_csv(OUT / "sector_moves_49.csv", ["event_id", "grouping", "group"] + win_cols, rows49 + r49i)
    date_checks(market, "market-wide events")
    date_checks(industry, "regulatory events")
    ordinary_rows = ordinary_vs_event(market + industry, g12, d12, mkt)
    spot_checks(market, industry, d12, mkt)

    company: list[dict] = []
    comp_rows: list = []
    unmatched: Counter = Counter()
    sh = actions = px = None
    edgar_stats = None
    if not args.skip_company:
        try:
            fts, edgar_stats = pull_edgar(args.skip_edgar)
            info, cik_map = {}, {}
            px, sh, actions = load_sharadar(info, cik_map)
            company, unmatched = build_company(px, info, cik_map, sh, actions, fts)
            company_returns(company, px)
            date_checks(company, "company events")
            comp_rows = company_summary(company, px)
            RESULTS.mkdir(parents=True, exist_ok=True)
            ret_cols = [f"{k}_{w}" for w, _, _ in WINDOWS for k in ("stock", "peer", "mkt", "abn")]
            write_csv(RESULTS / "company_events.csv",
                      EVENT_COLS + ["ticker", "cik", "group", "later_filing"] + ret_cols,
                      [[iso(e.get(c)) for c in EVENT_COLS + ["ticker", "cik", "group", "later_filing"]]
                       + [fmt(e.get(c), 5) for c in ret_cols]
                       for e in sorted(company, key=lambda e: (e["date"], e["ticker"]))])
            write_csv(OUT / "company_event_summary.csv",
                      ["type", "subtype", "role", "source", "events", "companies", "first", "last",
                       "with_returns", "median_abs_abn_d0_pct", "ordinary_median_abs_d0_pct", "ratio",
                       "median_abn_d01_pct", "mean_abn_d01_pct", "median_abn_post20_pct",
                       "picked_with_later_filing"], comp_rows)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            check("Company events built", False, f"{type(e).__name__}: {str(e)[:200]}")
            gaps.append("Company events: not built this run; see the failed check.")
    else:
        notes.append("Company events skipped (--skip-company).")

    truncation_tests(series_store, sh, actions, px)
    count_checks(market, industry, company, sh, edgar_stats)
    yr = counts_by_year(market + industry + company)
    write_csv(OUT / "counts_by_year.csv", yr[0], yr[1:])
    write_csv(OUT / "checks.csv", ["check", "status", "detail"],
              [[c["check"], c["status"], c["detail"]] for c in checks])
    report(market, industry, company, pending, ordinary_rows, comp_rows, unmatched,
           cal.last_real, edgar_stats)
    fails = [c for c in checks if c["status"] == "fail"]
    print(f"Wrote {OUT}: {len(market)} market, {len(industry)} industry, {len(company)} company "
          f"events; {len(fails)} failed checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
