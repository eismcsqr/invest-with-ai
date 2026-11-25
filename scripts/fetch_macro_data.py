"""Fetch the macro pillar's data and write a check report.

What it pulls:
  - FRED series listed in config/fred_series.csv (needs the FRED_API_KEY
    environment variable; the key is never printed or written anywhere).
  - Kenneth French's 12 industry portfolios (daily and monthly, value- and
    equal-weighted) and the Fama-French market factors, which give the
    market return that sector moves are compared against.

What it writes (all under data/):
  fred/<SERIES_ID>.csv            date,value  (blank value = no observation)
  french/industry12_<freq>_<w>.csv  date + one column per industry, % returns
  french/ff_factors_<freq>.csv    date,mkt_rf,smb,hml,rf  (% returns)
  CHECK_REPORT.md                 series count, date ranges, gaps, stale series

Uses only the Python standard library.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config" / "fred_series.csv"

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
FRENCH_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"

# French files: (zip name, {section title prefix: output file stem})
FRENCH_FILES = [
    ("12_Industry_Portfolios_daily_CSV.zip", {
        "Average Value Weighted Returns -- Daily": "industry12_daily_vw",
        "Average Equal Weighted Returns -- Daily": "industry12_daily_ew",
    }),
    ("12_Industry_Portfolios_CSV.zip", {
        "Average Value Weighted Returns -- Monthly": "industry12_monthly_vw",
        "Average Equal Weighted Returns -- Monthly": "industry12_monthly_ew",
    }),
    ("F-F_Research_Data_Factors_daily_CSV.zip", {"": "ff_factors_daily"}),
    ("F-F_Research_Data_Factors_CSV.zip", {"": "ff_factors_monthly"}),
]
FRENCH_MAX_LAG_DAYS = 100  # French updates monthly, about two months behind
GAP_FLAG_DAYS = 7          # flag calendar gaps longer than this in daily data
MISSING_CODES = {"-99.99", "-999", "-999.0", "-999.00"}


# ---------------------------------------------------------------- download --

def http_get(url: str, params: dict | None = None, label: str = "") -> bytes:
    """GET with a few retries. Error messages never include the query string."""
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(full, headers={"User-Agent": "invest-with-ai-data-pull"})
    last = ""
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body = e.read()[:500].decode("utf-8", "replace")
            try:
                body = json.loads(body).get("error_message", body)
            except ValueError:
                pass
            last = f"HTTP {e.code}: {body}"
            if e.code < 500 and e.code != 429:
                break
        except (urllib.error.URLError, TimeoutError) as e:
            last = str(e)
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Download failed for {label or url}: {last}")


# -------------------------------------------------------------------- FRED --

def load_fred_config() -> list[dict]:
    with CONFIG.open(newline="") as f:
        return list(csv.DictReader(f))


def fetch_fred(series_id: str, api_key: str) -> list[tuple[str, str]]:
    raw = http_get(FRED_URL, {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "limit": 100000,
    }, label=f"FRED {series_id}")
    obs = json.loads(raw)["observations"]
    # FRED marks a day with no value (e.g. a market holiday) as "."
    return [(o["date"], "" if o["value"] == "." else o["value"]) for o in obs]


def write_rows(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


# ------------------------------------------------------------ Ken French --

def parse_french_csv(text: str) -> dict[str, tuple[list[str], list[list[str]]]]:
    """Split a French data-library CSV into its titled sections.

    Each section is: an optional title line, a header line starting with ",",
    then rows whose first cell is a date (YYYYMMDD, YYYYMM or YYYY), ending at
    a blank line. Returns {title: (column names, rows)}.
    """
    sections: dict[str, tuple[list[str], list[list[str]]]] = {}
    title, header, rows = "", None, []
    for line in text.splitlines():
        cells = [c.strip() for c in line.split(",")]
        if header is None:
            if line.startswith(","):
                header = cells[1:]
                rows = []
            elif line.strip():
                title = line.strip()
            continue
        if cells[0].isdigit():
            rows.append(cells)
            continue
        # blank line or new title ends the section
        sections.setdefault(title, (header, rows))
        header, title = None, line.strip()
    if header is not None:
        sections.setdefault(title, (header, rows))
    return sections


def french_date(code: str) -> str:
    if len(code) == 8:
        return f"{code[:4]}-{code[4:6]}-{code[6:]}"
    if len(code) == 6:
        return f"{code[:4]}-{code[4:]}"
    return code


def fetch_french() -> dict[str, tuple[list[str], list[list[str]]]]:
    out = {}
    for zip_name, wanted in FRENCH_FILES:
        raw = http_get(FRENCH_URL + zip_name, label=f"Ken French {zip_name}")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            text = z.read(z.namelist()[0]).decode("latin-1")
        sections = parse_french_csv(text)
        for prefix, stem in wanted.items():
            match = next((t for t in sections if t.startswith(prefix)), None)
            if prefix == "":  # factor files: the first, untitled-ish section
                match = next(iter(sections), None)
            if match is None:
                raise RuntimeError(f"Section '{prefix}' not found in {zip_name}")
            header, rows = sections[match]
            # keep only rows whose date matches the section's frequency
            date_len = len(rows[0][0])
            clean = []
            for r in rows:
                if len(r[0]) != date_len:
                    continue
                vals = ["" if v in MISSING_CODES else v for v in r[1:]]
                clean.append([french_date(r[0])] + vals)
            cols = [c.lower().replace("-", "_") for c in header] if stem.startswith("ff_") else header
            out[stem] = (cols, clean)
    return out


# ------------------------------------------------------------------ checks --

def to_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s if len(s) == 10 else s + "-01")


def check_series(name: str, source: str, dates: list[str], has_value: list[bool],
                 max_lag: int | None, today: dt.date, daily: bool,
                 discontinued: bool = False) -> dict:
    valid = [d for d, ok in zip(dates, has_value) if ok]
    first, last = (valid[0], valid[-1]) if valid else ("", "")
    gaps = []
    if daily and len(valid) > 1:
        prev = to_date(valid[0])
        for d in valid[1:]:
            cur = to_date(d)
            if (cur - prev).days > GAP_FLAG_DAYS:
                gaps.append(f"{prev} to {cur}")
            prev = cur
    if not valid:
        status = "EMPTY"
    elif discontinued:
        status = "discontinued (expected)"
    else:
        # monthly rows are dated to the month; count lag from month end
        last_d = to_date(last)
        if not daily:
            last_d = (last_d.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
        lag = (today - last_d).days
        status = "STALE" if max_lag is not None and lag > max_lag else "ok"
    return {
        "name": name, "source": source, "first": first, "last": last,
        "rows": len(dates), "missing": len(dates) - len(valid),
        "gaps": gaps, "status": status,
    }


def write_report(results: list[dict], today: dt.date) -> str:
    stale = [r for r in results if r["status"] in ("STALE", "EMPTY")]
    gappy = [r for r in results if r["gaps"]]
    lines = [
        "# Macro data check report",
        "",
        f"Run date: {today.isoformat()}",
        "",
        f"**{len(results)} datasets pulled. "
        f"{len(stale)} stale or empty. {len(gappy)} with gaps over {GAP_FLAG_DAYS} days to review.**",
        "",
        "Missing counts the dates in the source file with no value (FRED lists market holidays this way). "
        "Gaps list stretches longer than a week between values in daily data, usually market closures.",
        "",
        "| Dataset | Source | First | Latest | Rows | Missing | Gaps > 7 days | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['name']} | {r['source']} | {r['first']} | {r['last']} | "
                     f"{r['rows']} | {r['missing']} | {len(r['gaps'])} | {r['status']} |")
    if gappy:
        lines += ["", "## Gaps to review", ""]
        for r in gappy:
            shown = ", ".join(r["gaps"][:10]) + (" ..." if len(r["gaps"]) > 10 else "")
            lines.append(f"- **{r['name']}:** {shown}")
    lines.append("")
    return "\n".join(lines)


# -------------------------------------------------------------------- main --

def main() -> int:
    today = dt.date.today()
    api_key = os.environ.get("FRED_API_KEY", "")
    if not api_key:
        print("::error::FRED_API_KEY is not set.")
        return 1

    results = []

    for s in load_fred_config():
        sid = s["series_id"]
        obs = fetch_fred(sid, api_key)
        write_rows(DATA / "fred" / f"{sid}.csv", ["date", "value"], [list(o) for o in obs])
        disc = s["discontinued"].strip().lower() == "yes"
        results.append(check_series(
            sid, "FRED", [d for d, _ in obs], [v != "" for _, v in obs],
            int(s["max_lag_days"]), today, daily=True, discontinued=disc))
        print(f"FRED {sid}: {len(obs)} rows, latest {results[-1]['last']}")

    for stem, (cols, rows) in fetch_french().items():
        write_rows(DATA / "french" / f"{stem}.csv", ["date"] + cols, rows)
        daily = "daily" in stem
        # a date counts as present when every column has a value
        results.append(check_series(
            stem, "Ken French", [r[0] for r in rows], [all(v != "" for v in r[1:]) for r in rows],
            FRENCH_MAX_LAG_DAYS, today, daily=daily))
        print(f"French {stem}: {len(rows)} rows, latest {results[-1]['last']}")

    report = write_report(results, today)
    (DATA / "CHECK_REPORT.md").write_text(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(report)
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
