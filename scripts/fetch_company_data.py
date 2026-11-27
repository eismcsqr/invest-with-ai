"""Pull Sharadar company data and check it before the company pillar uses it.

Source (agreed Nov 25, bought Nov 27, tracker row "Company sources"):
Sharadar's direct API at api.sharadar.com/v1.0 (not Nasdaq Data Link), with
the repository secret SHARADAR_API_KEY. Each table is downloaded whole with
the bulk route (years=full), which answers with a redirect to a zip file.

Tables pulled: tickers (company list with French industry group and
delisting flag), fundamentals (SF1), stocks (daily prices, SEP), events (8-K
filing dates and item codes) and actions (splits, delistings, mergers).
Insider trades and institutional holdings are not pulled yet: they are only
needed for owner signals and are very large in bulk.

The raw zips stay on the runner (raw/sharadar/, ignored by git): they are
too big for the repository and the personal licence does not allow
redistributing them. Only small files built from them are committed, under
data/company/:

  fields.csv               every column of each table, as Sharadar sends it
  field_check.csv          each field the company factors doc names: present?
  coverage_by_group.csv    companies per French industry group (Sharadar's
                           famaindustry field): total, delisted, domestic
                           common stock, first quarter of data
  edgar_check.csv          a handful of companies' yearly revenue, net income
                           and equity as first reported by Sharadar, against
                           the first SEC filing of the same number
  COMPANY_CHECK_REPORT.md  the six data checks proposed on Nov 25, pass/fail

The six checks: matches EDGAR within 1%, no number dated before its filing,
splits handled, delisted names present, under 2% missing quarters, new
filings within 5 days.

The key is read from the environment, sent only as a request header to
api.sharadar.com, and never printed, logged or written to a file. The
download link Sharadar redirects to is fetched without the key and never
printed either.

SEC asks automated clients to name themselves with a contact in the
User-Agent. Set the optional secret SEC_USER_AGENT (for example
"Your Name you@example.com") if SEC refuses the generic one; the EDGAR check
is skipped with a note when SEC refuses.

Uses only the Python standard library.

Run: python scripts/fetch_company_data.py
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "company"
RAW = ROOT / "raw" / "sharadar"

API = "https://api.sharadar.com/v1.0"
SEC_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
USER_AGENT = "invest-with-ai-data-pull"

TABLES = ["tickers", "fundamentals", "stocks", "events", "actions"]

# Fields named in docs/company-factors.md (section 3 and the financials
# table), with the factor that uses each.
NEEDED_FIELDS = {
    "ticker": "key", "dimension": "key", "calendardate": "key",
    "date": "point in time (filing date)", "reportperiod": "point in time",
    "lastupdated": "point in time",
    "revenue": "growth", "netinc": "growth", "epsdil": "growth",
    "grossmargin": "profitability", "gp": "profitability",
    "opinc": "profitability", "ebitda": "profitability",
    "invcap": "profitability", "roe": "profitability",
    "debt": "balance sheet", "debtc": "balance sheet",
    "debtnc": "balance sheet", "cashneq": "balance sheet",
    "equity": "balance sheet", "ebit": "balance sheet",
    "intexp": "balance sheet", "workingcapital": "balance sheet",
    "ncfo": "capital use", "fcf": "capital use", "capex": "capital use",
    "depamor": "capital use", "ncfcommon": "capital use",
    "ncfdiv": "capital use", "dps": "capital use",
    "shareswa": "capital use", "sbcomp": "capital use",
    "marketcap": "capital use and peer size",
    "revenueusd": "exposure profile",
    "pe": "valuation baseline", "pb": "valuation baseline (financials)",
    "intangibles": "valuation baseline (financials)",
    "deposits": "financials", "investments": "financials",
}

# Companies for the EDGAR cross-check: a spread of industries, one bank.
EDGAR_TICKERS = ["AAPL", "WMT", "XOM", "JNJ", "HD", "JPM"]
FINANCIALS = {"JPM"}            # revenue means something else for a bank
EDGAR_YEARS = 5
REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
]
EDGAR_TAGS = {"netinc": ["NetIncomeLoss"], "equity": ["StockholdersEquity"]}

# Known splits for the split check: ticker, last day before, first day after,
# split ratio (new shares per old share).
SPLITS = [("AAPL", "2020-08-28", "2020-08-31", 4.0),
          ("AAPL", "2014-06-06", "2014-06-09", 7.0),
          ("NVDA", "2024-06-07", "2024-06-10", 10.0)]

MISSING_LIMIT = 0.02            # under 2% missing quarters
EDGAR_TOLERANCE = 0.01          # within 1%
FRESH_DAYS = 5                  # newest filing in the data within 5 days


class SourceError(RuntimeError):
    """A download failed; the message never contains the key or a link."""


# ---------------------------------------------------------------- download --

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401
        return None


def _api_key() -> str:
    key = os.environ.get("SHARADAR_API_KEY", "").strip()
    if not key:
        raise SourceError("Repository secret SHARADAR_API_KEY is missing or empty.")
    return key


def _error_text(e: urllib.error.HTTPError) -> str:
    body = e.read()[:300].decode("utf-8", "replace")
    try:
        parsed = json.loads(body)
        body = parsed.get("error") or parsed.get("message") or body
    except (ValueError, AttributeError):
        pass
    hints = {401: " (no key or a bad key)",
             403: " (free tier, or this table is not in the plan)"}
    return f"HTTP {e.code}{hints.get(e.code, '')}: {str(body)[:200]}"


def download_table(table: str, key: str) -> Path:
    """Bulk-download one table to raw/sharadar/<table>.zip."""
    RAW.mkdir(parents=True, exist_ok=True)
    dest = RAW / f"{table}.zip"
    url = f"{API}/data/{table}?" + urllib.parse.urlencode({"years": "full"})
    opener = urllib.request.build_opener(_NoRedirect)
    location = None
    last = ""
    for attempt in range(4):
        req = urllib.request.Request(url, headers={"x-api-key": key,
                                                   "User-Agent": USER_AGENT})
        try:
            with opener.open(req, timeout=120) as resp:
                # Some tables may come straight back as a zip.
                _stream_to(resp, dest)
                return dest
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                location = e.headers.get("Location")
                break
            last = _error_text(e)
            if e.code < 500 and e.code != 429:
                break
        except (urllib.error.URLError, TimeoutError) as e:
            last = type(e).__name__
        time.sleep(2 ** attempt)
    if not location:
        raise SourceError(f"{table}: bulk request failed: {last or 'no redirect'}")
    if not location.startswith("https://"):
        raise SourceError(f"{table}: download link is not https; not followed.")
    # The pre-signed link carries its own signature: fetch it without the key.
    for attempt in range(4):
        req = urllib.request.Request(location, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                _stream_to(resp, dest)
                return dest
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code < 500:
                break
        except (urllib.error.URLError, TimeoutError) as e:
            last = type(e).__name__
        time.sleep(2 ** attempt)
    raise SourceError(f"{table}: zip download failed: {last}")


def _stream_to(resp, dest: Path) -> None:
    tmp = dest.with_suffix(".part")
    with tmp.open("wb") as f:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dest)


def open_rows(path: Path):
    """Yield (header, row iterator) for the CSV inside a zip (or a bare CSV)."""
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


# ------------------------------------------------------------------ helpers --

def to_date(s: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def to_float(s: str) -> float | None:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def quarter_index(d: dt.date) -> int:
    return d.year * 4 + (d.month - 1) // 3


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def pct(x: float) -> str:
    return f"{100 * x:.2f}%"


# ------------------------------------------------------------------ tables --

def scan_tickers(path: Path) -> dict:
    header, rows = open_rows(path)
    ix = {h: i for i, h in enumerate(header)}
    need = ["table", "ticker", "isdelisted", "category", "famaindustry",
            "firstquarter", "secfilings"]
    missing = [c for c in need if c not in ix]
    if missing:
        raise SourceError(f"tickers: columns missing: {', '.join(missing)}")
    groups = defaultdict(lambda: {"companies": 0, "delisted": 0,
                                  "domestic_common": 0, "first_quarter": ""})
    sf1_delisted, sep_delisted, domestic = set(), set(), set()
    ciks = {}
    sf1_count = 0
    for r in rows:
        if len(r) < len(header):
            continue
        table, ticker = r[ix["table"]], r[ix["ticker"]]
        delisted = r[ix["isdelisted"]].strip().upper() == "Y"
        if table == "SEP" and delisted:
            sep_delisted.add(ticker)
        if table != "SF1":
            continue
        sf1_count += 1
        g = groups[r[ix["famaindustry"]].strip() or "(none)"]
        g["companies"] += 1
        g["delisted"] += delisted
        if r[ix["category"]].strip().lower().startswith("domestic common"):
            g["domestic_common"] += 1
            domestic.add(ticker)
        fq = r[ix["firstquarter"]][:10]
        if fq and (not g["first_quarter"] or fq < g["first_quarter"]):
            g["first_quarter"] = fq
        if delisted:
            sf1_delisted.add(ticker)
        if ticker in EDGAR_TICKERS:
            link = r[ix["secfilings"]]
            q = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
            cik = (q.get("CIK") or q.get("cik") or [""])[0]
            if cik.isdigit():
                ciks[ticker] = cik.zfill(10)
    return {"header": header, "groups": dict(groups), "sf1_count": sf1_count,
            "sf1_delisted": sf1_delisted, "sep_delisted": sep_delisted,
            "domestic": domestic, "ciks": ciks}


def scan_fundamentals(path: Path, domestic: set) -> dict:
    header, rows = open_rows(path)
    ix = {h: i for i, h in enumerate(header)}
    # The direct API calls the SEC filing date "date" (older exports: "datekey").
    if "datekey" not in ix and "date" in ix:
        ix["datekey"] = ix["date"]
    for c in ("ticker", "dimension", "calendardate", "datekey", "reportperiod"):
        if c not in ix:
            raise SourceError(f"fundamentals: column {c} missing; "
                              f"columns are {', '.join(header[:12])}...")
    i_t, i_dim, i_cal = ix["ticker"], ix["dimension"], ix["calendardate"]
    i_key, i_rep = ix["datekey"], ix["reportperiod"]
    keep = [c for c in ("revenue", "netinc", "equity") if c in ix]
    quarters: dict[str, set] = defaultdict(set)
    before_filing = 0
    before_examples = []
    lags = []
    newest = None
    arq_rows = 0
    dims = Counter()
    edgar_rows = defaultdict(list)
    for r in rows:
        if len(r) < len(header):
            continue
        dim = r[i_dim]
        dims[dim] += 1
        ticker = r[i_t]
        if dim == "ARY" and ticker in EDGAR_TICKERS:
            edgar_rows[ticker].append({"reportperiod": r[i_rep][:10],
                                       "datekey": r[i_key][:10],
                                       **{c: r[ix[c]] for c in keep}})
        if dim != "ARQ":
            continue
        arq_rows += 1
        cal, key, rep = to_date(r[i_cal]), to_date(r[i_key]), to_date(r[i_rep])
        if cal:
            quarters[ticker].add(quarter_index(cal))
        if key and rep:
            if key < rep:
                before_filing += 1
                if len(before_examples) < 5:
                    before_examples.append(f"{ticker} period {rep} filed {key}")
            elif len(lags) < 2_000_000:
                lags.append((key - rep).days)
            if newest is None or key > newest:
                newest = key
    # Missing quarters between each company's first and last quarter.
    expected = present = 0
    worst = []
    for ticker, qs in quarters.items():
        # Domestic filers only: foreign filers report twice a year or yearly.
        if len(qs) < 4 or ticker not in domestic:
            continue
        span = max(qs) - min(qs) + 1
        expected += span
        present += len(qs)
        worst.append((span - len(qs), ticker))
    worst.sort(reverse=True)
    return {"header": header, "dims": dims, "arq_rows": arq_rows,
            "companies": len(quarters), "before_filing": before_filing,
            "before_examples": before_examples,
            "lag_median": statistics.median(lags) if lags else None,
            "lag_p90": (statistics.quantiles(lags, n=10)[-1]
                        if len(lags) >= 10 else None),
            "newest": newest, "expected_q": expected, "present_q": present,
            "worst_gaps": worst[:5], "edgar_rows": dict(edgar_rows)}


def scan_stocks(path: Path, delisted: set) -> dict:
    header, rows = open_rows(path)
    ix = {h: i for i, h in enumerate(header)}
    for c in ("ticker", "date", "close", "closeunadj"):
        if c not in ix:
            raise SourceError(f"stocks: column {c} missing")
    i_t, i_d, i_c, i_u = ix["ticker"], ix["date"], ix["close"], ix["closeunadj"]
    split_days = {(t, d) for t, a, b, _ in SPLITS for d in (a, b)}
    split_px = {}
    tickers = set()
    delisted_with_prices = set()
    first = last = ""
    n = 0
    per_decade = Counter()
    for r in rows:
        if len(r) < len(header):
            continue
        n += 1
        t, d = r[i_t], r[i_d][:10]
        tickers.add(t)
        if t in delisted:
            delisted_with_prices.add(t)
        if d:
            if not first or d < first:
                first = d
            if d > last:
                last = d
            per_decade[d[:3] + "0s"] += 1
        if (t, d) in split_days:
            split_px[(t, d)] = (to_float(r[i_c]), to_float(r[i_u]))
    splits = []
    for t, before, after, ratio in SPLITS:
        b, a = split_px.get((t, before)), split_px.get((t, after))
        if not b or not a or None in b or None in a or not b[0] or not b[1]:
            splits.append((t, after, ratio, None, None, "no prices found"))
            continue
        adj_move = a[0] / b[0]          # split-adjusted: should be near 1
        raw_move = a[1] / b[1]          # unadjusted: should be near 1/ratio
        ok = 0.8 < adj_move < 1.25 and abs(raw_move * ratio - 1) < 0.25
        splits.append((t, after, ratio, adj_move, raw_move, "ok" if ok else "FAIL"))
    return {"header": header, "rows": n, "tickers": len(tickers),
            "first": first, "last": last, "per_decade": per_decade,
            "delisted_with_prices": len(delisted_with_prices), "splits": splits}


def scan_simple(path: Path, date_col: str, count_col: str | None) -> dict:
    header, rows = open_rows(path)
    ix = {h: i for i, h in enumerate(header)}
    i_d = ix.get(date_col)
    i_c = ix.get(count_col) if count_col else None
    n = 0
    first = last = ""
    counts = Counter()
    for r in rows:
        if len(r) < len(header):
            continue
        n += 1
        if i_d is not None:
            d = r[i_d][:10]
            if d and (not first or d < first):
                first = d
            if d > last:
                last = d
        if i_c is not None:
            for code in r[i_c].split("|"):
                if code.strip():
                    counts[code.strip()] += 1
    return {"header": header, "rows": n, "first": first, "last": last,
            "counts": counts}


# ------------------------------------------------------------------- EDGAR --

def edgar_check(fund: dict, ciks: dict) -> tuple[list[list], str]:
    """Compare Sharadar's first-reported yearly numbers with SEC filings."""
    ua = os.environ.get("SEC_USER_AGENT", "").strip() or USER_AGENT
    out = []
    for ticker in EDGAR_TICKERS:
        cik = ciks.get(ticker)
        rows = sorted(fund["edgar_rows"].get(ticker, []),
                      key=lambda x: x["reportperiod"])[-EDGAR_YEARS:]
        if not cik or not rows:
            out.append([ticker, "", "", "", "", "", "", "", "", "",
                        "no CIK or no yearly rows in Sharadar"])
            continue
        req = urllib.request.Request(SEC_FACTS.format(cik=cik),
                                     headers={"User-Agent": ua,
                                              "Accept-Encoding": "identity"})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                facts = json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                return [], ("SEC refused the request (HTTP 403). Add a "
                            "SEC_USER_AGENT secret with a name and contact.")
            out.append([ticker, cik, "", "", "", "", "", "", "", "",
                        f"SEC HTTP {e.code}"])
            continue
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            out.append([ticker, cik, "", "", "", "", "", "", "", "",
                        f"SEC {type(e).__name__}"])
            continue
        time.sleep(0.2)
        gaap = facts.get("facts", {}).get("us-gaap", {})
        measures = dict(EDGAR_TAGS)
        if ticker not in FINANCIALS:
            measures = {"revenue": REVENUE_TAGS, **measures}
        for row in rows:
            end = row["reportperiod"]
            for measure, tags in measures.items():
                shar = to_float(row.get(measure, ""))
                fact, tag_used = _first_filed(gaap, tags, end,
                                              instant=(measure == "equity"))
                if fact is None:
                    out.append([ticker, cik, end, measure, shar, "", "", "",
                                row["datekey"], "", "no matching SEC fact"])
                    continue
                edgar = float(fact["val"])
                diff = (shar - edgar) / abs(edgar) if shar is not None and edgar else None
                filed = fact.get("filed", "")
                lag = ""
                kd, fd = to_date(row["datekey"]), to_date(filed)
                if kd and fd:
                    lag = (kd - fd).days
                out.append([ticker, cik, end, measure, shar, edgar,
                            "" if diff is None else f"{100 * diff:.3f}",
                            "" if diff is None else
                            ("Y" if abs(diff) <= EDGAR_TOLERANCE else "N"),
                            row["datekey"], filed, f"{tag_used}; lag {lag} days"])
    return out, ""


def _first_filed(gaap: dict, tags: list[str], end: str, instant: bool):
    """The earliest-filed 10-K fact for this period end, across tags in order."""
    for tag in tags:
        units = gaap.get(tag, {}).get("units", {}).get("USD", [])
        best = None
        for f in units:
            if f.get("end") != end or not str(f.get("form", "")).startswith("10-K"):
                continue
            if not instant:
                s, e = to_date(f.get("start", "")), to_date(f.get("end", ""))
                if not s or not e or not 330 <= (e - s).days <= 380:
                    continue
            if best is None or f.get("filed", "") < best.get("filed", ""):
                best = f
        if best is not None:
            return best, tag
    return None, ""


# ------------------------------------------------------------------ report --

def main() -> int:
    today = dt.date.today()
    try:
        key = _api_key()
    except SourceError as e:
        print(f"::error::{e}")
        return 1

    paths, failures = {}, []
    for table in TABLES:
        t0 = time.time()
        try:
            paths[table] = download_table(table, key)
            size = paths[table].stat().st_size / 1e6
            print(f"{table}: downloaded {size:,.0f} MB in {time.time() - t0:,.0f}s")
        except SourceError as e:
            failures.append(str(e))
            print(f"::error::{e}")
    del key
    if "tickers" not in paths or "fundamentals" not in paths:
        print("::error::tickers and fundamentals are needed for the checks; stopping.")
        return 1

    t0 = time.time()
    tick = scan_tickers(paths["tickers"])
    print(f"tickers scanned in {time.time() - t0:,.0f}s")
    t0 = time.time()
    fund = scan_fundamentals(paths["fundamentals"], tick["domestic"])
    print(f"fundamentals scanned in {time.time() - t0:,.0f}s")
    stocks = events = actions = None
    if "stocks" in paths:
        t0 = time.time()
        stocks = scan_stocks(paths["stocks"], tick["sep_delisted"])
        print(f"stocks scanned in {time.time() - t0:,.0f}s")
    if "events" in paths:
        events = scan_simple(paths["events"], "date", "eventcodes")
    if "actions" in paths:
        actions = scan_simple(paths["actions"], "date", "action")
    edgar_rows, edgar_note = edgar_check(fund, tick["ciks"])

    # ---- files
    field_rows = []
    for table, info in (("tickers", tick), ("fundamentals", fund),
                        ("stocks", stocks), ("events", events),
                        ("actions", actions)):
        if info:
            field_rows += [[table, c] for c in info["header"]]
    write_csv(OUT / "fields.csv", ["table", "column"], field_rows)
    have = set(fund["header"])
    write_csv(OUT / "field_check.csv", ["field", "used_for", "in_sharadar"],
              [[f, use, "Y" if f in have else "N"] for f, use in NEEDED_FIELDS.items()])
    write_csv(OUT / "coverage_by_group.csv",
              ["famaindustry", "companies", "delisted", "domestic_common",
               "first_quarter"],
              [[g, v["companies"], v["delisted"], v["domestic_common"],
                v["first_quarter"]] for g, v in sorted(tick["groups"].items())])
    write_csv(OUT / "edgar_check.csv",
              ["ticker", "cik", "period_end", "measure", "sharadar", "edgar",
               "diff_pct", "within_1pct", "sharadar_filed", "edgar_filed", "note"],
              edgar_rows)

    # ---- checks
    checks = []
    compared = [r for r in edgar_rows if r[7] in ("Y", "N")]
    within = sum(r[7] == "Y" for r in compared)
    if compared:
        share = within / len(compared)
        checks.append(("Matches EDGAR within 1%", share >= 0.95,
                       f"{within} of {len(compared)} numbers within 1% "
                       f"({pct(share)}) across {len(EDGAR_TICKERS)} companies; "
                       "see edgar_check.csv"))
    else:
        checks.append(("Matches EDGAR within 1%", None,
                       edgar_note or "no numbers could be compared"))
    checks.append(("No number dated before its filing", fund["before_filing"] == 0,
                   f"{fund['before_filing']:,} of {fund['arq_rows']:,} as-first-reported "
                   "quarterly rows have a filing date before the period end"
                   + (f" (e.g. {'; '.join(fund['before_examples'])})"
                      if fund["before_examples"] else "")))
    if stocks:
        split_ok = all(s[5] == "ok" for s in stocks["splits"])
        checks.append(("Splits handled", split_ok, "; ".join(
            f"{t} {r:g}-for-1 on {d}: adjusted close moved "
            f"{'n/a' if a is None else f'{a:.3f}x'}, unadjusted "
            f"{'n/a' if u is None else f'{u:.3f}x'} ({st})"
            for t, d, r, a, u, st in stocks["splits"])))
    else:
        checks.append(("Splits handled", None, "prices not downloaded"))
    n_del = len(tick["sf1_delisted"])
    checks.append(("Delisted names present", n_del > 0,
                   f"{n_del:,} of {tick['sf1_count']:,} companies with fundamentals "
                   "are delisted"
                   + (f"; {stocks['delisted_with_prices']:,} delisted tickers have "
                      "daily prices" if stocks else "")))
    if fund["expected_q"]:
        miss = 1 - fund["present_q"] / fund["expected_q"]
        checks.append(("Under 2% missing quarters", miss < MISSING_LIMIT,
                       f"{pct(miss)} of quarters missing between each company's "
                       f"first and last quarter ({fund['expected_q'] - fund['present_q']:,} "
                       f"of {fund['expected_q']:,}), domestic common stocks with at "
                       "least 4 quarters"))
    newest = fund["newest"]
    fresh = newest is not None and (today - newest).days <= FRESH_DAYS
    checks.append(("New filings within 5 days", fresh,
                   f"newest filing date in the data is {newest} "
                   f"({(today - newest).days if newest else 'n/a'} days before this run). "
                   "A recent date means filings are arriving; the delay for each "
                   "new filing shows up week to week."))

    # ---- report
    def mark(ok):
        return "pass" if ok else ("not run" if ok is None else "FAIL")

    lines = [
        "# Company data check report",
        "",
        f"Run: {today}. Source: Sharadar (direct API, bulk download of each table).",
        "",
        "## The six checks",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    lines += [f"| {name} | {mark(ok)} | {detail} |" for name, ok, detail in checks]
    lines += ["", "## Tables", ""]
    lines.append(f"- **Tickers:** {tick['sf1_count']:,} companies with fundamentals, "
                 f"{len(tick['groups'])} French industry groups (famaindustry).")
    d = fund["dims"]
    lines.append(f"- **Fundamentals:** {fund['companies']:,} companies with "
                 f"as-first-reported quarterly rows ({fund['arq_rows']:,} rows). Rows by "
                 "dimension: " + ", ".join(f"{k} {v:,}" for k, v in sorted(d.items()))
                 + ".")
    if fund["lag_median"] is not None:
        p90 = fund["lag_p90"]
        lines.append(f"- **Filing lag:** median {fund['lag_median']:.0f} days from "
                     "period end to filing"
                     + (f", 90th percentile {p90:.0f}." if p90 is not None else "."))
    if stocks:
        dec = ", ".join(f"{k} {v:,}" for k, v in sorted(stocks["per_decade"].items()))
        lines.append(f"- **Daily prices:** {stocks['rows']:,} rows, "
                     f"{stocks['tickers']:,} tickers, {stocks['first']} to "
                     f"{stocks['last']}. Rows by decade: {dec}.")
    if events:
        lines.append(f"- **8-K events:** {events['rows']:,} rows, {events['first']} to "
                     f"{events['last']}. Most common codes: " + ", ".join(
                         f"{c} ({n:,})" for c, n in events["counts"].most_common(6))
                     + ". Code meanings are on Sharadar's events page.")
    if actions:
        lines.append(f"- **Corporate actions:** {actions['rows']:,} rows, "
                     f"{actions['first']} to {actions['last']}. By type: " + ", ".join(
                         f"{c} {n:,}" for c, n in actions["counts"].most_common(8)) + ".")
    missing_fields = [f for f in NEEDED_FIELDS if f not in have]
    lines += ["", "## Fields named in the company factors doc", ""]
    lines.append(f"{len(NEEDED_FIELDS) - len(missing_fields)} of {len(NEEDED_FIELDS)} "
                 "present in fundamentals."
                 + (f" Missing: {', '.join(missing_fields)}." if missing_fields else "")
                 + " Full list in field_check.csv; every column of every table in "
                 "fields.csv.")
    if fund["worst_gaps"]:
        lines += ["", "## Largest gaps in quarterly data", ""]
        lines += [f"- {t}: {g} quarters missing" for g, t in fund["worst_gaps"]]
    lines += ["", "## Not pulled yet", "",
              "- Insider trades and institutional holdings (owner signals): very "
              "large in bulk; pulled when the owner-signal measure is built.",
              "- Raw tables stay on the runner and are not committed (size and "
              "licence)."]
    if failures:
        lines += ["", "## Download failures", ""] + [f"- {f}" for f in failures]
    lines.append("")
    (OUT / "COMPANY_CHECK_REPORT.md").write_text("\n".join(lines))
    for name, ok, detail in checks:
        print(f"{name}: {mark(ok)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
