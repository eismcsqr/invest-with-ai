"""Build the macro event calendar and its surprise series.

Runs after scripts/fetch_macro_data.py, which writes the daily FRED series and
Kenneth French returns this script reads from data/.

What it builds (all under data/events/):
  fomc_meetings_raw.csv     every meeting, conference call and notation vote
                            listed on the Fed's FOMC pages since 1994
  fomc_decisions.csv        Fed decision days: scheduled meetings plus
                            unscheduled actions, with the target rate before
                            and after (FRED DFEDTAR / DFEDTARU / DFEDTARL)
  release_first_prints.csv  CPI, core CPI, PCE price, core PCE price, PCE
                            spending and retail sales as first published
                            (ALFRED vintages), with a simple data surprise
  event_calendar.csv        one row per event day with the market-reaction
                            surprise the macro spec uses: the change in the
                            2-year Treasury yield (and breakevens) from the
                            previous close to the event-day close
  EVENTS_CHECK_REPORT.md    coverage, gaps, cross-checks and spot checks

Sources: federalreserve.gov FOMC calendars and historical materials; the FRED
API (release dates, ALFRED vintages, target-rate series). Needs FRED_API_KEY;
the key is never printed or written anywhere. Standard library only.
"""

from __future__ import annotations

import bisect
import csv
import datetime as dt
import html
import json
import os
import re
import sys
import time
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_macro_data import http_get  # noqa: E402  (shared retrying downloader)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "events"
FRED = "https://api.stlouisfed.org/fred/"
FED = "https://www.federalreserve.gov/monetarypolicy/"
FIRST_FED_YEAR = 1994  # the FOMC started announcing its decisions in February 1994

# Releases on the calendar: FRED release id, event name, and the series whose
# first prints we keep (the first one is the headline used in the calendar).
RELEASES = [
    (10, "cpi", "Consumer price index", ["CPIAUCSL", "CPILFESL"]),
    (54, "pce", "Personal income and outlays (PCE)", ["PCEPI", "PCEPILFE", "PCE"]),
    (9, "retail_sales", "Advance retail sales", ["RSAFS"]),
]
SERIES_NAMES = {
    "CPIAUCSL": "CPI", "CPILFESL": "Core CPI", "PCEPI": "PCE prices",
    "PCEPILFE": "Core PCE prices", "PCE": "PCE spending", "RSAFS": "Retail sales",
}
ON_TIME_DAYS = 75     # first print within this many days of the month's start
TREND_MONTHS = 12     # data surprise = first-print m/m minus the prior 12-month average m/m
SCENARIO_MIN_BP = 1.0  # smaller 2-year moves are labelled "flat"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MONTH_NUM = {m: i + 1 for i, m in enumerate(MONTHS)}
MONTH_NUM.update({m[:3]: i + 1 for i, m in enumerate(MONTHS)})
MONTH_RE = "|".join(MONTHS)


# ------------------------------------------------------------------ helpers --

def d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def write_csv(path: Path, header: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: fmt(r.get(k)) for k in header})


def fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".") if v == v else ""
    if isinstance(v, bool):
        return "yes" if v else "no"
    return str(v)


def read_fred_csv(sid: str) -> dict[str, float]:
    """date -> value for a series written by fetch_macro_data.py."""
    out = {}
    with (DATA / "fred" / f"{sid}.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            if r["value"] != "":
                out[r["date"]] = float(r["value"])
    return out


def fred_api(path: str, api_key: str, **params) -> dict:
    params.update(api_key=api_key, file_type="json")
    return json.loads(http_get(FRED + path, params, label=f"FRED {path} {params.get('series_id') or params.get('release_id', '')}"))


def fred_all(path: str, key: str, api_key: str, **params) -> list[dict]:
    """Page through a FRED list endpoint."""
    rows, offset = [], 0
    while True:
        res = fred_api(path, api_key, limit=100000, offset=offset, **params)
        batch = res.get(key, [])
        rows += batch
        offset += len(batch)
        if not batch or offset >= int(res.get("count", offset)):
            return rows


def add_months(first_of_month: str, n: int) -> str:
    y, m = int(first_of_month[:4]), int(first_of_month[5:7]) + n
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    return f"{y:04d}-{m:02d}-01"


# --------------------------------------------------------- Fed FOMC pages --

def html_lines(text: str) -> list[str]:
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>|</?(div|p|h\d|li|tr|td|ul|section|header|strong)\b[^>]*>", "\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return [" ".join(line.split()) for line in text.split("\n") if line.strip()]


HIST_HEAD = re.compile(
    rf"^(?P<m1>{MONTH_RE})\s+(?P<d1>\d{{1,2}})"
    rf"(?:\s*-\s*(?:(?P<m2>{MONTH_RE})\s+)?(?P<d2>\d{{1,2}}))?\s*"
    r"(?:\((?P<flag>unscheduled|cancelled|notation vote)\)\s*)?"
    r"(?P<kind>Meeting|Conference Call)?\s*-\s*(?P<year>\d{4})$")
RELEASED = re.compile(rf"Released\s+(?P<m>{MONTH_RE})\s+(?P<d>\d{{1,2}}),\s*(?P<y>\d{{4}})")
CAL_YEAR = re.compile(r"^(\d{4}) FOMC Meetings$")
CAL_MONTH = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
                       r"(?:/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)?$")
CAL_DATE = re.compile(r"^(\d{1,2})(?:-(\d{1,2}))?\*?\s*(?:\((unscheduled|cancelled|notation vote)\))?")


def panel_info(body: list[str]) -> tuple[bool, str | None]:
    statement = any(line.startswith("Statement") for line in body)
    released = None
    for line in body:
        m = RELEASED.search(line)
        if m:
            released = dt.date(int(m["y"]), MONTH_NUM[m["m"]], int(m["d"])).isoformat()
            break
    return statement, released


def parse_historical(text: str, year: int) -> list[dict]:
    lines, out = html_lines(text), []
    heads = [(i, HIST_HEAD.match(l)) for i, l in enumerate(lines)]
    heads = [(i, m) for i, m in heads if m]
    for n, (i, m) in enumerate(heads):
        if int(m["year"]) != year:
            continue
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        statement, released = panel_info(lines[i + 1:end])
        start = dt.date(year, MONTH_NUM[m["m1"]], int(m["d1"]))
        last = dt.date(year, MONTH_NUM[m["m2"] or m["m1"]], int(m["d2"] or m["d1"]))
        if last < start:  # e.g. December 31-January 1 would cross the year
            last = last.replace(year=year + 1)
        kind = {"Meeting": "meeting", "Conference Call": "conference call"}.get(m["kind"] or "", "notation vote")
        out.append({"label": lines[i], "start": start.isoformat(), "end": last.isoformat(),
                    "kind": kind, "flag": m["flag"] or "", "statement": statement,
                    "released": released, "source": f"{FED}fomchistorical{year}.htm"})
    return out


def parse_calendars(text: str) -> list[dict]:
    lines, out, year = html_lines(text), [], None
    starts = []
    for i, l in enumerate(lines):
        if CAL_YEAR.match(l):
            starts.append((i, "year", int(CAL_YEAR.match(l)[1])))
        elif starts:
            m = CAL_MONTH.match(l)
            if m and i + 1 < len(lines) and CAL_DATE.match(lines[i + 1]):
                starts.append((i, "meeting", m))
    for n, (i, what, val) in enumerate(starts):
        if what == "year":
            year = val
            continue
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        m, dm = val, CAL_DATE.match(lines[i + 1])
        m1 = MONTH_NUM[m[1]]
        d1 = int(dm[1])
        d2 = int(dm[2]) if dm[2] else d1
        m2 = MONTH_NUM[m[2]] if m[2] and d2 < d1 else m1
        flag = dm[3] or ""
        statement, released = panel_info(lines[i + 2:end])
        kind = "notation vote" if flag == "notation vote" else "meeting"
        out.append({"label": f"{lines[i]} {lines[i + 1]} {year}", "start": dt.date(year, m1, d1).isoformat(),
                    "end": dt.date(year, m2, d2).isoformat(), "kind": kind, "flag": flag,
                    "statement": statement, "released": released, "source": f"{FED}fomccalendars.htm"})
    return out


def fetch_fomc_pages() -> list[dict]:
    cal_text = http_get(FED + "fomccalendars.htm", label="Fed FOMC calendars").decode("utf-8", "replace")
    recent = parse_calendars(cal_text)
    if not recent:
        raise RuntimeError("No meetings parsed from the Fed's FOMC calendars page; its layout may have changed.")
    first_recent = min(int(r["start"][:4]) for r in recent)
    rows = []
    for year in range(FIRST_FED_YEAR, first_recent):
        text = http_get(f"{FED}fomchistorical{year}.htm", label=f"Fed FOMC {year}").decode("utf-8", "replace")
        parsed = parse_historical(text, year)
        if not any(p["kind"] == "meeting" for p in parsed):
            raise RuntimeError(f"No meetings parsed from the Fed's {year} historical page; its layout may have changed.")
        rows += parsed
        time.sleep(0.3)
    return rows + recent


# ------------------------------------------------------- Fed target rates --

def target_series() -> dict[str, tuple[float, float]]:
    """date -> (low, high) of the federal funds target (a point target before Dec 16, 2008)."""
    out = {k: (v, v) for k, v in read_fred_csv("DFEDTAR").items()}
    lo, hi = read_fred_csv("DFEDTARL"), read_fred_csv("DFEDTARU")
    for k in hi:
        if k in lo:
            out[k] = (lo[k], hi[k])
    return out


def build_decisions(meetings: list[dict], target: dict, today: dt.date) -> tuple[list[dict], list[str]]:
    one = dt.timedelta(days=1)

    def tgt(day: dt.date):
        return target.get(day.isoformat())

    def changed(day: dt.date) -> bool:
        a, b = tgt(day), tgt(day - one)
        return a is not None and b is not None and a != b

    decisions = []
    for m in meetings:
        if m["flag"] == "cancelled":
            continue
        end = d(m["end"])
        if m["released"]:
            ann = d(m["released"])
        elif m["kind"] != "meeting" and end <= dt.date(2008, 12, 15) and changed(end + one) and not changed(end):
            ann = end + one  # e.g. the Jan 21, 2008 call was announced the next morning
        else:
            ann = end
        if ann > today:
            continue
        before, after = tgt(ann - one), tgt(ann + one) or tgt(ann)
        rate_change = before is not None and after is not None and before != after
        if m["kind"] == "meeting" and m["flag"] != "unscheduled":
            typ = "scheduled"
        elif rate_change:
            typ = "unscheduled_rate_change"
        elif m["statement"]:
            typ = "unscheduled_statement"
        else:
            continue  # a call or vote with no announced action
        change_bp = round((after[1] - before[1]) * 100) if rate_change else 0
        decisions.append({
            "date": ann.isoformat(), "type": typ,
            "in_rates_test": typ in ("scheduled", "unscheduled_rate_change"),
            "fed_label": m["label"],
            "target_low_before": before[0] if before else None, "target_high_before": before[1] if before else None,
            "target_low_after": after[0] if after else None, "target_high_after": after[1] if after else None,
            "change_bp": change_bp if before and after else None,
            "date_note": ("released date from the Fed page" if m["released"] else
                          "day after the call (target changed then)" if ann != end else
                          "last day of the meeting" if m["kind"] == "meeting" else
                          "date of the call; announcement may have come the next morning"),
            "source": m["source"],
        })
    decisions.sort(key=lambda r: r["date"])

    # Cross-check: every target change since Feb 1994 should sit on, or the day
    # after, a decision day (since 2008 changes take effect the next day).
    dec_days = {r["date"] for r in decisions}
    unmatched = []
    for k in sorted(target):
        day = d(k)
        if day < dt.date(FIRST_FED_YEAR, 2, 1) or not changed(day):
            continue
        if k not in dec_days and (day - one).isoformat() not in dec_days:
            unmatched.append(f"{k}: {fmt_target(tgt(day - one))} to {fmt_target(tgt(day))}")
    return decisions, unmatched


def fmt_target(t) -> str:
    if not t:
        return "?"
    lo, hi = t
    return f"{lo:.2f}%" if lo == hi else f"{lo:.2f}-{hi:.2f}%"


# --------------------------------------------------- releases and vintages --

def build_first_prints(api_key: str) -> list[dict]:
    rows = []
    for rid, event, _, series in RELEASES:
        for sid in series:
            first = fred_all("series/observations", "observations", api_key, series_id=sid,
                             realtime_start="1776-07-04", realtime_end="9999-12-31", output_type=4)
            vint = fred_all("series/observations", "observations", api_key, series_id=sid,
                            realtime_start="1776-07-04", realtime_end="9999-12-31")
            by_date: dict[str, list[tuple[str, str, float | None]]] = {}
            for o in vint:
                val = None if o["value"] == "." else float(o["value"])
                by_date.setdefault(o["date"], []).append((o["realtime_start"], o["realtime_end"], val))

            def asof(obs: str, v: str):
                for rs, re_, val in by_date.get(obs, []):
                    if rs <= v <= re_:
                        return val
                return None

            for o in first:
                v, obs = o["realtime_start"], o["date"]
                val = None if o["value"] == "." else float(o["value"])
                prior = asof(add_months(obs, -1), v)
                mom = 100 * (val / prior - 1) if val is not None and prior else None
                hist = []
                for k in range(1, TREND_MONTHS + 1):
                    a, b = asof(add_months(obs, -k), v), asof(add_months(obs, -k - 1), v)
                    if a is not None and b:
                        hist.append(100 * (a / b - 1))
                trend = mean(hist) if len(hist) >= TREND_MONTHS - 2 else None
                lag = (d(v) - d(obs)).days
                rows.append({
                    "series_id": sid, "series": SERIES_NAMES[sid], "event": event, "release_id": rid,
                    "obs_month": obs[:7], "release_date": v, "first_print": val,
                    "prior_month_as_of_release": prior, "mom_pct": mom,
                    "trend_mom_pct": trend,
                    "data_surprise_pp": mom - trend if mom is not None and trend is not None else None,
                    "timing": "on time" if lag <= ON_TIME_DAYS else f"late ({lag} days after month start)",
                })
            print(f"ALFRED {sid}: {len(first)} first prints, {len(vint)} vintage rows")
            time.sleep(0.3)
    return rows


def build_release_dates(api_key: str, today: dt.date) -> dict[str, list[str]]:
    out = {}
    for rid, event, _, _ in RELEASES:
        res = fred_all("release/dates", "release_dates", api_key, release_id=rid,
                       realtime_start="1776-07-04", include_release_dates_with_no_data="true",
                       sort_order="asc")
        out[event] = sorted({r["date"] for r in res if d(r["date"]) <= today})
    return out


# ------------------------------------------------------------ the calendar --

class Market:
    def __init__(self):
        self.y2 = read_fred_csv("DGS2")
        self.be5 = read_fred_csv("T5YIE")
        self.be10 = read_fred_csv("T10YIE")
        self.days = sorted(self.y2)  # bond-market trading days
        self.mkt = {}
        with (DATA / "french" / "ff_factors_daily.csv").open(newline="") as f:
            for r in csv.DictReader(f):
                if r["mkt_rf"] and r["rf"]:
                    self.mkt[r["date"]] = float(r["mkt_rf"]) + float(r["rf"])

    def event_day(self, day: str) -> tuple[str | None, str | None]:
        """First trading day on or after the announcement, and the trading day before it."""
        i = bisect.bisect_left(self.days, day)
        if i >= len(self.days) or i == 0:
            return None, None
        return self.days[i], self.days[i - 1]

    @staticmethod
    def chg(series: dict, td: str, prev: str):
        if td in series and prev in series:
            return round((series[td] - series[prev]) * 100, 2)
        return None

    def reaction(self, day: str) -> dict:
        td, prev = self.event_day(day)
        if td is None:
            return {}
        dy = self.chg(self.y2, td, prev)
        mkt = self.mkt.get(td)
        scen = None
        if dy is not None and mkt is not None:
            if abs(dy) < SCENARIO_MIN_BP:
                scen = "flat"
            elif dy > 0:
                scen = "growth news" if mkt > 0 else "tightening or inflation news"
            else:
                scen = "easing or cooling inflation" if mkt > 0 else "weaker growth"
        return {"trading_day": td, "prev_trading_day": prev, "dgs2_prev": self.y2.get(prev),
                "dgs2": self.y2.get(td), "dgs2_chg_bp": dy,
                "t5yie_chg_bp": self.chg(self.be5, td, prev), "t10yie_chg_bp": self.chg(self.be10, td, prev),
                "mkt_ret_pct": round(mkt, 2) if mkt is not None else None, "scenario": scen}


def build_calendar(decisions, release_dates, first_prints, market) -> list[dict]:
    rows = []
    start = market.days[0]
    for r in decisions:
        rows.append({"date": r["date"], "event": "fomc", "subtype": r["type"],
                     "in_rates_test": r["in_rates_test"],
                     "detail": (f"Target {fmt_target((r['target_low_before'], r['target_high_before']))} to "
                                f"{fmt_target((r['target_low_after'], r['target_high_after']))}"
                                if r["target_low_before"] is not None else "Target not available"),
                     "change_bp": r["change_bp"], "status": r["date_note"]})
    fp = {}
    for p in first_prints:
        fp.setdefault((p["event"], p["release_date"]), []).append(p)
    names = {e: n for _, e, n, _ in RELEASES}
    for _, event, _, series in RELEASES:
        dates = set(release_dates[event]) | {k[1] for k in fp if k[0] == event}
        cover = min((p["release_date"] for p in first_prints if p["series_id"] == series[0]), default="9999")
        for day in sorted(dates):
            if day < start:
                continue
            prints = fp.get((event, day), [])
            head = next((p for p in prints if p["series_id"] == series[0]), None)
            if prints:
                parts = [f"{p['series']} {p['obs_month']}: "
                         + (f"{p['mom_pct']:+.2f}% m/m" if p["mom_pct"] is not None else "no value")
                         for p in prints]
                status = "first print" + ("" if day in release_dates[event] else " (date from ALFRED only)")
            else:
                parts = [names[event]]
                status = "release date before vintage coverage" if day < cover else "no new month in this release"
            rows.append({"date": day, "event": event, "subtype": "data release", "in_rates_test": False,
                         "detail": "; ".join(parts), "status": status,
                         "data_surprise_pp": head["data_surprise_pp"] if head else None,
                         "first_print_mom_pct": head["mom_pct"] if head else None})
    for r in rows:
        r.update(market.reaction(r["date"]))
    by_day: dict[str, list[str]] = {}
    for r in rows:
        by_day.setdefault(r.get("trading_day") or r["date"], []).append(r["event"])
    for r in rows:
        others = [e for e in by_day.get(r.get("trading_day") or r["date"], []) if e != r["event"]]
        r["same_day_events"] = " ".join(sorted(set(others)))
    rows.sort(key=lambda r: (r["date"], r["event"]))
    return rows


# ----------------------------------------------------------------- checks --

FOMC_SPOT = [  # (announcement date, target before, target after), from the Fed's statements
    ("1994-02-04", (3.00, 3.00), (3.25, 3.25)),
    ("2001-01-03", (6.50, 6.50), (6.00, 6.00)),
    ("2001-09-17", (3.50, 3.50), (3.00, 3.00)),
    ("2008-12-16", (1.00, 1.00), (0.00, 0.25)),
    ("2015-12-16", (0.00, 0.25), (0.25, 0.50)),
    ("2020-03-03", (1.50, 1.75), (1.00, 1.25)),
    ("2020-03-15", (1.00, 1.25), (0.00, 0.25)),
    ("2022-06-15", (0.75, 1.00), (1.50, 1.75)),
    ("2024-09-18", (5.25, 5.50), (4.75, 5.00)),
]
PRINT_SPOT = [  # (series, release date, obs month, m/m as published, rounded to 0.1)
    ("CPIAUCSL", "2022-06-10", "2022-05", 1.0),
    ("CPIAUCSL", "2022-09-13", "2022-08", 0.1),
    ("CPILFESL", "2022-09-13", "2022-08", 0.6),
    ("CPIAUCSL", "2023-11-14", "2023-10", 0.0),
    ("RSAFS", "2020-05-15", "2020-04", -16.4),
]


def abs_mean(xs):
    xs = [abs(x) for x in xs if x is not None]
    return (mean(xs), len(xs)) if xs else (None, 0)


def report(meetings, decisions, unmatched, release_dates, first_prints, calendar, market, today) -> str:
    L = []
    by_type = {}
    for r in decisions:
        by_type.setdefault(r["type"], []).append(r)
    rt = [r for r in decisions if r["in_rates_test"]]
    fomc_cal = [r for r in calendar if r["event"] == "fomc" and r["in_rates_test"]]
    fomc_ok = sum(1 for (day, b, a) in FOMC_SPOT
                  if any(r["date"] == day and (r["target_low_before"], r["target_high_before"]) == b
                         and (r["target_low_after"], r["target_high_after"]) == a for r in decisions))
    print_ok = 0
    print_lines = []
    for sid, day, obs, want in PRINT_SPOT:
        got = next((p for p in first_prints if p["series_id"] == sid and p["release_date"] == day
                    and p["obs_month"] == obs), None)
        val = got["mom_pct"] if got else None
        ok = val is not None and abs(round(val, 1) - want) < 0.051
        print_ok += ok
        print_lines.append(f"| {SERIES_NAMES[sid]} {obs} | {day} | {want:+.1f}% | "
                           f"{'' if val is None else f'{val:+.2f}%'} | {'pass' if ok else 'FAIL'} |")

    L += ["# Event calendar check report", "", f"Run date: {today.isoformat()}", "",
          f"**{len(rt)} Fed decision days for the rates test ({rt[0]['date']} to {rt[-1]['date']}), "
          f"{len(unmatched)} target changes without a decision day, "
          f"{fomc_ok} of {len(FOMC_SPOT)} Fed spot checks and {print_ok} of {len(PRINT_SPOT)} first-print spot checks pass.**",
          ""]

    L += ["## Fed decision days", "",
          f"Parsed {len(meetings)} meetings, calls and notation votes from the Fed's FOMC pages "
          f"({FIRST_FED_YEAR} onward; the FOMC began announcing decisions in February {FIRST_FED_YEAR}).", "",
          "| Type | Count | With a rate change | In the rates test |", "|---|---|---|---|"]
    for t in ("scheduled", "unscheduled_rate_change", "unscheduled_statement"):
        rs = by_type.get(t, [])
        L.append(f"| {t.replace('_', ' ')} | {len(rs)} | {sum(1 for r in rs if r['change_bp'])} | "
                 f"{'yes' if t != 'unscheduled_statement' else 'no'} |")
    L += ["", "Unscheduled rate changes:", ""]
    for r in by_type.get("unscheduled_rate_change", []):
        L.append(f"- {r['date']}: {fmt_target((r['target_low_before'], r['target_high_before']))} to "
                 f"{fmt_target((r['target_low_after'], r['target_high_after']))} ({r['fed_label']})")
    L += ["", "Unscheduled statements with no rate change (kept, but left out of the rates test; dates are "
          "the call date unless the Fed page gives a release date):", ""]
    for r in by_type.get("unscheduled_statement", []):
        L.append(f"- {r['date']}: {r['fed_label']} ({r['date_note']})")
    L += ["", "**Cross-check against FRED's target rate:** every change in DFEDTAR / DFEDTARU / DFEDTARL "
          "since February 1994 should fall on a decision day or the day after.", ""]
    L += [f"- {u}" for u in unmatched] or ["- All target changes matched a decision day."]
    L += ["", "**Spot checks** (target before and after, from the Fed's statements):", "",
          "| Date | Expected | Pass |", "|---|---|---|"]
    for day, b, a in FOMC_SPOT:
        ok = any(r["date"] == day and (r["target_low_before"], r["target_high_before"]) == b
                 and (r["target_low_after"], r["target_high_after"]) == a for r in decisions)
        L.append(f"| {day} | {fmt_target(b)} to {fmt_target(a)} | {'pass' if ok else 'FAIL'} |")

    L += ["", "## Data releases and first prints", "",
          "| Release | Release dates on file | First prints from | First prints | Late first prints | "
          "Dates with no new month | First-print dates missing from FRED's release calendar |",
          "|---|---|---|---|---|---|---|"]
    start = market.days[0]
    for _, event, name, series in RELEASES:
        fps = [p for p in first_prints if p["series_id"] == series[0]]
        rdates = [x for x in release_dates[event] if x >= start]
        cal = [r for r in calendar if r["event"] == event]
        no_new = sum(1 for r in cal if r["status"] == "no new month in this release")
        missing = sum(1 for p in fps if p["release_date"] not in release_dates[event])
        late = sum(1 for p in fps if p["timing"] != "on time")
        L.append(f"| {name} | {len(rdates)} (from {rdates[0] if rdates else '-'}) | "
                 f"{min(p['release_date'] for p in fps) if fps else '-'} | {len(fps)} | {late} | {no_new} | {missing} |")
    L += ["", "Months with no first print (a skipped month in the vintage history):", ""]
    gaps = []
    for sid in SERIES_NAMES:
        months = sorted(p["obs_month"] for p in first_prints if p["series_id"] == sid and p["first_print"] is not None)
        for a, b in zip(months, months[1:]):
            if add_months(a + "-01", 1)[:7] != b:
                gaps.append(f"- {SERIES_NAMES[sid]}: after {a}, next is {b}")
    L += gaps or ["- None."]
    late_lines = sorted({f"- {p['series']} {p['obs_month']}: released {p['release_date']}, {p['timing']}"
                         for p in first_prints if p["timing"] != "on time" and p["release_date"] >= "2010"})
    if late_lines:
        L += ["", "Late first prints since 2010 (delayed releases, for example during government shutdowns):", ""]
        L += late_lines[:40]
    L += ["", "**Spot checks** (month-on-month change as first published, rounded to 0.1):", "",
          "| Print | Released | Published | Computed | Pass |", "|---|---|---|---|---|"] + print_lines

    L += ["", "## Market-reaction surprise (the spec's measure)", "",
          "Change in the 2-year Treasury yield from the previous trading day's close to the event day's close. "
          "Ordinary days are trading days with none of these events, over the same years.", "",
          "| Event | Days with a 2-year move | Average size on event days (bp) | Average size on ordinary days (bp) | "
          "Days sharing another event |", "|---|---|---|---|---|"]
    event_tds = {r.get("trading_day") for r in calendar if r.get("trading_day")}
    for label, sel in [("Fed decision (rates test)", fomc_cal)] + [
            (name, [r for r in calendar if r["event"] == event]) for _, event, name, _ in RELEASES]:
        if not sel:
            continue
        first = min(r["date"] for r in sel)
        ev, n = abs_mean([r.get("dgs2_chg_bp") for r in sel])
        ordinary = [market.chg(market.y2, td, prev) for prev, td in zip(market.days, market.days[1:])
                    if td >= first and td not in event_tds]
        od, _ = abs_mean(ordinary)
        shared = sum(1 for r in sel if r["same_day_events"])
        L.append(f"| {label} | {n} | {ev:.1f} | {od:.1f} | {shared} |" if ev is not None and od is not None
                 else f"| {label} | {n} | - | - | {shared} |")
    no_y = [r for r in calendar if r.get("dgs2_chg_bp") is None]
    L += ["", f"Event days without a 2-year move: {len(no_y)}"
          + (f" (latest: {', '.join(r['date'] + ' ' + r['event'] for r in no_y[-5:])})" if no_y else "") + ".",
          "Stock-market returns come from Kenneth French's daily file, which runs about two months behind, "
          "so recent events have no scenario label yet.", ""]
    ex = [r for r in calendar if r["date"] in ("2022-09-13", "2022-06-15", "2020-03-16", "2008-12-16")]
    if ex:
        L += ["Examples:", "", "| Date | Event | Detail | 2-year change (bp) | Market return (%) | Scenario |",
              "|---|---|---|---|---|---|"]
        for r in ex:
            L.append(f"| {r['date']} | {r['event']} | {r['detail']} | {fmt(r.get('dgs2_chg_bp'))} | "
                     f"{fmt(r.get('mkt_ret_pct'))} | {fmt(r.get('scenario'))} |")
    L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------- main --

def main() -> int:
    today = dt.date.today()
    api_key = os.environ.get("FRED_API_KEY", "")
    if not api_key:
        print("::error::FRED_API_KEY is not set.")
        return 1

    meetings = fetch_fomc_pages()
    write_csv(OUT / "fomc_meetings_raw.csv",
              ["label", "start", "end", "kind", "flag", "statement", "released", "source"], meetings)
    print(f"Fed pages: {len(meetings)} meetings, calls and votes")

    decisions, unmatched = build_decisions(meetings, target_series(), today)
    write_csv(OUT / "fomc_decisions.csv",
              ["date", "type", "in_rates_test", "change_bp", "target_low_before", "target_high_before",
               "target_low_after", "target_high_after", "fed_label", "date_note", "source"], decisions)
    print(f"Fed decision days: {len(decisions)}, unmatched target changes: {len(unmatched)}")

    first_prints = build_first_prints(api_key)
    write_csv(OUT / "release_first_prints.csv",
              ["series_id", "series", "event", "release_id", "obs_month", "release_date", "first_print",
               "prior_month_as_of_release", "mom_pct", "trend_mom_pct", "data_surprise_pp", "timing"],
              first_prints)

    release_dates = build_release_dates(api_key, today)
    market = Market()
    calendar = build_calendar(decisions, release_dates, first_prints, market)
    write_csv(OUT / "event_calendar.csv",
              ["date", "event", "subtype", "in_rates_test", "trading_day", "prev_trading_day", "detail",
               "change_bp", "first_print_mom_pct", "data_surprise_pp", "dgs2_prev", "dgs2", "dgs2_chg_bp",
               "t5yie_chg_bp", "t10yie_chg_bp", "mkt_ret_pct", "scenario", "same_day_events", "status"],
              calendar)

    text = report(meetings, decisions, unmatched, release_dates, first_prints, calendar, market, today)
    (OUT / "EVENTS_CHECK_REPORT.md").write_text(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("\n" + text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
