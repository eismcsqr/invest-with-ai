"""Fetch the industry pillar's free government data and write a check report.

Sources (agreed Nov 25, tracker row "Industry sources"):
  - BEA gross output by industry, quarterly (demand cycle).
      Secret: BEA_API_KEY.
  - Census M3 manufacturers' new orders, shipments and unfilled orders,
    monthly, by M3 category (demand cycle, manufacturing).
      Secret: CENSUS_API_KEY.
  - Census Economic Census concentration of largest firms, 2017 and 2022
    (HHI and share of the largest firms, by NAICS industry; competition
    cross-check). Secret: CENSUS_API_KEY.
  - BLS producer price indexes by NAICS industry, monthly (coping with
    shocks). Secret: BLS_API_KEY. Which industry indexes exist is looked up
    in FRED's copy of the PPI series list (FRED_API_KEY), because the BLS
    list files block automated downloads.
  - Federal Reserve G.17 capacity utilization by industry, monthly,
    seasonally adjusted, from FRED (capacity cycle). Secret: FRED_API_KEY.

Each source runs only when its key is set. A missing key skips that source
with a message and leaves its earlier files as they are, so keys can be added
one at a time. Keys are read from the environment only and never printed,
logged or written to a file.

Not covered here: Sharadar (paid), a free services capacity measure (none
exists), QuantGov RegData, the Federal Register, PatentsView, and the
NAICS-to-French-industry crosswalk.

What it writes (all under data/industry/):
  bea/gross_output_<measure>.csv      date + one column per BEA industry code
  bea/industries.csv                  BEA industry code, description
  bea/tables.csv                      BEA table id, description, measure
  census/m3.csv                       date + one column per category_type_adj
  census/m3_columns.csv               column, category, data type, adjustment
  census/concentration_<year>.csv     one row per NAICS industry and firm group
  bls/ppi_industry.csv                date + one column per BLS series id
  bls/ppi_series.csv                  series id, NAICS code, name, preliminary months
  fed_g17/capacity_utilization.csv    date + one column per FRED series id
  fed_g17/series.csv                  series id, name
  INDUSTRY_CHECK_REPORT.md            what was pulled, ranges, checks, skips

Uses only the Python standard library.

Run: python scripts/fetch_industry_data.py
     python scripts/fetch_industry_data.py --smoke   (keyless BLS v1 check of
     three indexes; writes nothing to data/)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "industry"

FRED_BASE = "https://api.stlouisfed.org/fred/"
BEA_URL = "https://apps.bea.gov/api/data"
CENSUS_BASE = "https://api.census.gov/data/"
BLS_V2 = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_V1 = "https://api.bls.gov/publicAPI/v1/timeseries/data/"

USER_AGENT = "invest-with-ai-data-pull"

M3_DATA_TYPES = {"NO": "new orders", "VS": "shipments", "UO": "unfilled orders"}
M3_START = "1992"
PPI_START_YEAR = 1985
BLS_BATCH = 50          # series per request with a key
BLS_YEARS = 20          # years per request with a key
CONCENTRATION_YEARS = [2017, 2022]

# Days a dataset's latest period may lag today before it counts as stale.
MAX_LAG = {"monthly": 75, "quarterly": 200}
# A series whose latest value is this far behind its dataset's latest is
# counted as discontinued rather than stale.
DISCONTINUED_DAYS = 400


class SourceError(RuntimeError):
    """A source failed; the message never contains a key."""


# ---------------------------------------------------------------- download --

def _request(req: urllib.request.Request, label: str) -> tuple[bytes, str]:
    last = ""
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.read(), resp.geturl()
        except urllib.error.HTTPError as e:
            body = e.read()[:400].decode("utf-8", "replace")
            try:
                parsed = json.loads(body)
                body = parsed.get("error_message") or parsed.get("message") or body
            except (ValueError, AttributeError):
                pass
            last = f"HTTP {e.code}: {body}"
            if e.code < 500 and e.code != 429:
                break
        except (urllib.error.URLError, TimeoutError) as e:
            last = str(e)
        time.sleep(2 ** attempt)
    raise SourceError(f"{label} download failed: {last}")


def http_get(url: str, params: dict, label: str) -> tuple[bytes, str]:
    """GET; error messages show the label only, never the query string."""
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": USER_AGENT})
    raw, final_url = _request(req, label)
    return raw, final_url.split("?")[0]


def http_post_json(url: str, payload: dict, label: str) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"User-Agent": USER_AGENT,
                                          "Content-Type": "application/json"})
    raw, _ = _request(req, label)
    return json.loads(raw)


# ------------------------------------------------------------------ helpers --

def num(s) -> str:
    """Normalise a numeric string; '' when it is not a number."""
    if s is None:
        return ""
    t = str(s).replace(",", "").strip()
    try:
        float(t)
    except ValueError:
        return ""
    return t


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def wide(series: dict[str, dict[str, str]]) -> tuple[list[str], list[list[str]]]:
    """{column: {date: value}} -> header, rows sorted by date."""
    cols = sorted(series)
    dates = sorted({d for s in series.values() for d in s})
    rows = [[d] + [series[c].get(d, "") for c in cols] for d in dates]
    return ["date"] + cols, rows


def period_end(date: str, freq: str) -> dt.date:
    y, m = int(date[:4]), int(date[5:7])
    if freq == "quarterly":
        m = m + 2
    nxt = dt.date(y + (m // 12), m % 12 + 1, 1)
    return nxt - dt.timedelta(days=1)


def quarter_date(year: str, quarter: str) -> str:
    q = {"I": 1, "II": 2, "III": 3, "IV": 4}.get(quarter.strip().upper())
    if q is None:
        q = int(quarter.strip().lstrip("Qq"))
    return f"{int(year):04d}-{3 * q - 2:02d}"


# ------------------------------------------------------------------- checks --

def check_wide(name: str, source: str, freq: str, series: dict[str, dict[str, str]],
               today: dt.date, bounds: tuple[float, float] | None = None,
               note: str = "") -> dict:
    """Summarise a {column: {date: value}} dataset for the report."""
    all_dates = sorted({d for s in series.values() for d, v in s.items() if v != ""})
    if not all_dates:
        return {"name": name, "source": source, "status": "EMPTY", "series": len(series),
                "first": "", "last": "", "rows": 0, "missing": 0, "issues": [], "note": note}
    last = all_dates[-1]
    lag = (today - period_end(last, freq)).days
    status = "STALE" if lag > MAX_LAG[freq] else "ok"
    last_end = period_end(last, freq)
    discontinued, behind, out_of_bounds = [], [], []
    missing = 0
    for col, s in series.items():
        vals = {d: v for d, v in s.items() if v != ""}
        missing += sum(1 for v in s.values() if v == "")
        if not vals:
            discontinued.append(col)
            continue
        gap = (last_end - period_end(max(vals), freq)).days
        if gap > DISCONTINUED_DAYS:
            discontinued.append(col)
        elif gap > 0:
            behind.append(col)
        if bounds:
            lo, hi = bounds
            out_of_bounds += [f"{col} {d}={v}" for d, v in vals.items() if not lo <= float(v) <= hi]
    issues = []
    if out_of_bounds:
        issues.append(f"{len(out_of_bounds)} values outside {bounds[0]:g} to {bounds[1]:g}: "
                      + ", ".join(out_of_bounds[:5]) + (" ..." if len(out_of_bounds) > 5 else ""))
    if behind:
        issues.append(f"{len(behind)} series a period or more behind the latest "
                      f"(often normal right after a release): " + ", ".join(sorted(behind)[:8])
                      + (" ..." if len(behind) > 8 else ""))
    if discontinued:
        issues.append(f"{len(discontinued)} series with no value in the last "
                      f"{DISCONTINUED_DAYS} days (likely discontinued)")
    return {"name": name, "source": source, "status": status, "series": len(series),
            "first": all_dates[0], "last": last, "rows": len(all_dates),
            "missing": missing, "issues": issues, "note": note}


def skipped(name: str, source: str, reason: str, existing: Path | None = None) -> dict:
    note = reason
    if existing is not None and existing.exists():
        note += " Earlier file kept."
    return {"name": name, "source": source, "status": "skipped", "series": "", "first": "",
            "last": "", "rows": "", "missing": "", "issues": [], "note": note}


def failed(name: str, source: str, err: Exception) -> dict:
    return {"name": name, "source": source, "status": "FAILED", "series": "", "first": "",
            "last": "", "rows": "", "missing": "", "issues": [str(err)],
            "note": "Earlier file kept."}


# --------------------------------------------------------------------- FRED --

def fred_search_ids(pattern: str, key: str) -> list[dict]:
    """Every FRED series whose id matches pattern (FRED wildcard search)."""
    out, offset = [], 0
    while True:
        raw, _ = http_get(FRED_BASE + "series/search", {
            "search_text": pattern, "search_type": "series_id", "api_key": key,
            "file_type": "json", "limit": 1000, "offset": offset,
        }, label=f"FRED search {pattern}")
        d = json.loads(raw)
        batch = d.get("seriess", [])
        out += batch
        offset += len(batch)
        if not batch or offset >= int(d.get("count", 0)) or offset >= 20000:
            return out
        time.sleep(0.6)


def fred_observations(series_id: str, key: str) -> dict[str, str]:
    raw, _ = http_get(FRED_BASE + "series/observations", {
        "series_id": series_id, "api_key": key, "file_type": "json", "limit": 100000,
    }, label=f"FRED {series_id}")
    return {o["date"][:7]: ("" if o["value"] == "." else o["value"])
            for o in json.loads(raw)["observations"]}


def pull_g17(key: str, today: dt.date) -> dict:
    found = fred_search_ids("CAPUTL*", key)
    keep = sorted({s["id"]: s for s in found
                   if s["id"].startswith("CAPUTL")
                   and s.get("frequency_short") == "M"
                   and s.get("seasonal_adjustment_short") == "SA"}.values(),
                  key=lambda s: s["id"])
    if not keep:
        raise SourceError("FRED search returned no monthly seasonally adjusted capacity "
                          "utilization series")
    series = {}
    for s in keep:
        series[s["id"]] = fred_observations(s["id"], key)
        time.sleep(0.6)  # FRED allows about 120 requests a minute
    header, rows = wide(series)
    write_csv(OUT / "fed_g17" / "capacity_utilization.csv", header, rows)
    write_csv(OUT / "fed_g17" / "series.csv", ["series_id", "name"],
              [[s["id"], s["title"]] for s in keep])
    print(f"G.17: {len(keep)} capacity utilization series")
    return check_wide("capacity_utilization", "Fed G.17 via FRED", "monthly", series, today,
                      bounds=(0, 110), note="Percent of capacity, seasonally adjusted.")


def ppi_series_from_fred(key: str) -> list[dict]:
    """Industry-level PPI indexes, as FRED lists them.

    BLS industry-level ids repeat the industry code, padded with dashes to six
    characters: PCU325---325---. FRED drops the dashes: PCU325325.
    """
    found = fred_search_ids("PCU*", key)
    out = {}
    for s in found:
        m = re.fullmatch(r"PCU(\d{3,6})\1", s["id"])
        if not m or s.get("frequency_short") != "M":
            continue
        code = m.group(1)
        bls_id = "PCU" + code.ljust(6, "-") * 2
        name = s["title"].replace("Producer Price Index by Industry: ", "").strip()
        out[bls_id] = {"series_id": bls_id, "naics": code, "name": name}
    return sorted(out.values(), key=lambda r: r["series_id"])


# ---------------------------------------------------------------------- BLS --

def bls_fetch(series_ids: list[str], key: str | None, start: int, end: int,
              batch: int = BLS_BATCH, years: int = BLS_YEARS
              ) -> tuple[dict[str, dict[str, str]], dict[str, set[str]], list[str]]:
    """Monthly values for each series, preliminary months, and missing ids."""
    url = BLS_V2 if key else BLS_V1
    values: dict[str, dict[str, str]] = {s: {} for s in series_ids}
    prelim: dict[str, set[str]] = {s: set() for s in series_ids}
    absent: set[str] = set()
    windows = [(y, min(y + years - 1, end)) for y in range(start, end + 1, years)]
    for i in range(0, len(series_ids), batch):
        chunk = series_ids[i:i + batch]
        for y0, y1 in windows:
            payload = {"seriesid": chunk, "startyear": str(y0), "endyear": str(y1)}
            if key:
                payload["registrationkey"] = key
            d = http_post_json(url, payload, label="BLS")
            if d.get("status") != "REQUEST_SUCCEEDED":
                msg = "; ".join(d.get("message", []))
                raise SourceError(f"BLS request not accepted: {d.get('status')}: {msg[:300]}")
            for m in d.get("message", []):
                hit = re.search(r"Series does not exist for Series (\S+)", m)
                if hit:
                    absent.add(hit.group(1))
            for s in d["Results"]["series"]:
                sid = s["seriesID"]
                for o in s["data"]:
                    p = o["period"]
                    if not p.startswith("M") or p == "M13":
                        continue
                    date = f"{o['year']}-{p[1:]}"
                    values[sid][date] = num(o["value"])
                    if any(f.get("code") == "P" for f in o.get("footnotes", []) if f):
                        prelim[sid].add(date)
            time.sleep(0.5)
    # a series with data in any window exists
    absent = {s for s in absent if not any(v for v in values[s].values())}
    return values, prelim, sorted(absent)


def pull_ppi(bls_key: str, fred_key: str | None, today: dt.date) -> dict:
    list_path = OUT / "bls" / "ppi_series.csv"
    if fred_key:
        meta = ppi_series_from_fred(fred_key)
        source_note = "Series list from FRED's PPI listing."
    elif list_path.exists():
        with list_path.open(newline="") as f:
            meta = list(csv.DictReader(f))
        source_note = "Series list reused from the last run (FRED key not set)."
    else:
        raise SourceError("No PPI series list: needs FRED_API_KEY on the first run")
    if not meta:
        raise SourceError("FRED listed no industry-level PPI series")
    ids = [m["series_id"] for m in meta]
    values, prelim, absent = bls_fetch(ids, bls_key, PPI_START_YEAR, today.year)
    for a in absent:
        values.pop(a, None)
    header, rows = wide(values)
    write_csv(OUT / "bls" / "ppi_industry.csv", header, rows)
    write_csv(list_path, ["series_id", "naics", "name", "preliminary_months"],
              [[m["series_id"], m["naics"], m["name"], len(prelim.get(m["series_id"], ()))]
               for m in meta if m["series_id"] in values])
    print(f"BLS PPI: {len(values)} industry indexes ({len(absent)} listed by FRED but not at BLS)")
    note = source_note + " Not seasonally adjusted (BLS publishes industry indexes unadjusted)."
    if absent:
        note += f" {len(absent)} ids FRED lists were not found at BLS: {', '.join(absent[:5])}."
    return check_wide("ppi_industry", "BLS", "monthly", values, today,
                      bounds=(0.001, 1e6), note=note)


# ---------------------------------------------------------------------- BEA --

def bea_call(params: dict, key: str, label: str):
    raw, _ = http_get(BEA_URL, {"UserID": key, "ResultFormat": "JSON", **params}, label=label)
    d = json.loads(raw).get("BEAAPI", {})
    res = d.get("Results")
    err = d.get("Error")
    if not err and isinstance(res, dict):
        err = res.get("Error")
    if err:
        if isinstance(err, list):
            err = err[0]
        desc = err.get("APIErrorDescription") or err.get("ErrorDetail", {}).get("Description") or str(err)
        raise SourceError(f"{label}: BEA said: {str(desc)[:300]}")
    if isinstance(res, list):
        res = res[0]
    return res or {}


def classify_go_table(desc: str) -> str | None:
    t = desc.lower()
    if "gross output" not in t or "intermediate" in t or "percent" in t or "contribution" in t:
        return None
    if "price" in t:
        return "price_index"
    if "quantity" in t:
        return "quantity_index"
    if t.startswith("real") or "chained" in t:
        return "real"
    return "nominal"


def pull_bea(key: str, today: dt.date) -> list[dict]:
    res = bea_call({"method": "GetParameterValues", "datasetname": "GDPbyIndustry",
                    "ParameterName": "TableID"}, key, "BEA table list")
    params = res.get("ParamValue", [])
    tables = {}
    for p in params:
        measure = classify_go_table(p.get("Desc", ""))
        if measure and measure not in tables:
            tables[measure] = (str(p["Key"]), p["Desc"])
    if "nominal" not in tables:
        raise SourceError("BEA table list has no gross output by industry table; "
                          f"saw {len(params)} tables")
    results, industries = [], {}
    for measure, (tid, desc) in sorted(tables.items()):
        res = bea_call({"method": "GetData", "datasetname": "GDPbyIndustry", "TableID": tid,
                        "Frequency": "Q", "Year": "ALL", "Industry": "ALL"},
                       key, f"BEA table {tid}")
        series: dict[str, dict[str, str]] = {}
        for r in res.get("Data", []):
            if r.get("Frequency", "Q") != "Q":
                continue
            code = r["Industry"]
            industries.setdefault(code, r.get("IndustrYDescription") or r.get("IndustryDescription", ""))
            series.setdefault(code, {})[quarter_date(r["Year"], r["Quarter"])] = num(r.get("DataValue"))
        if not series:
            results.append({"name": f"gross_output_{measure}", "source": "BEA", "status": "EMPTY",
                            "series": 0, "first": "", "last": "", "rows": 0, "missing": 0,
                            "issues": [f"Table {tid} returned no quarterly rows"], "note": desc})
            continue
        header, rows = wide(series)
        write_csv(OUT / "bea" / f"gross_output_{measure}.csv", header, rows)
        results.append(check_wide(f"gross_output_{measure}", "BEA", "quarterly", series, today,
                                  note=f"Table {tid}: {desc}."))
        print(f"BEA {measure}: table {tid}, {len(series)} industries")
        time.sleep(1)
    write_csv(OUT / "bea" / "industries.csv", ["industry", "description"], sorted(industries.items()))
    write_csv(OUT / "bea" / "tables.csv", ["table_id", "description", "measure"],
              [[tid, desc, m] for m, (tid, desc) in sorted(tables.items())])
    return results


# ------------------------------------------------------------------- Census --

def census_get(path: str, params: dict, key: str, label: str) -> list[list[str]]:
    raw, final = http_get(CENSUS_BASE + path, {**params, "key": key}, label=label)
    if "missing_key" in final or "invalid_key" in final:
        raise SourceError(f"{label}: Census did not accept the key (check CENSUS_API_KEY)")
    try:
        return json.loads(raw)
    except ValueError:
        raise SourceError(f"{label}: Census sent something other than data: "
                          f"{raw[:200].decode('utf-8', 'replace')}")


def pull_m3(key: str, today: dt.date) -> dict:
    series: dict[str, dict[str, str]] = {}
    cols_meta = {}
    for dtype in M3_DATA_TYPES:
        rows = census_get("timeseries/eits/m3", {
            "get": "cell_value,data_type_code,time_slot_id,error_data,category_code,seasonally_adj",
            "for": "us:*", "time": f"from {M3_START}", "data_type_code": dtype,
        }, key, f"Census M3 {dtype}")
        head, body = rows[0], rows[1:]
        ix = {h: i for i, h in enumerate(head)}
        for r in body:
            if r[ix["error_data"]].lower() == "yes":
                continue
            adj = "SA" if r[ix["seasonally_adj"]].lower() == "yes" else "NSA"
            cat = r[ix["category_code"]]
            col = f"{cat}_{dtype}_{adj}"
            cols_meta[col] = [col, cat, dtype, M3_DATA_TYPES[dtype], adj]
            series.setdefault(col, {})[r[ix["time"]][:7]] = num(r[ix["cell_value"]])
        print(f"Census M3 {dtype}: {len(body)} rows")
        time.sleep(1)
    if not series:
        raise SourceError("Census M3 returned no rows")
    header, rows = wide(series)
    write_csv(OUT / "census" / "m3.csv", header, rows)
    write_csv(OUT / "census" / "m3_columns.csv",
              ["column", "category_code", "data_type", "meaning", "adjustment"],
              [cols_meta[c] for c in sorted(cols_meta)])
    cats = len({m[1] for m in cols_meta.values()})
    return check_wide("m3", "Census", "monthly", series, today,
                      note=f"{cats} M3 categories; millions of dollars. Category codes are "
                           "Census M3 codes; mapping to NAICS and French groups comes next.")


def pull_concentration(key: str, year: int) -> dict:
    naics = f"NAICS{year}"
    fields = [naics, f"{naics}_LABEL", "INDLEVEL", "SECTOR", "TYPOP", "TYPOP_LABEL",
              "CONCENFI", "CONCENFI_LABEL", "FIRM", "RCPTOT", "VAL_PCT", "HHI"]
    rows = census_get(f"{year}/ecnsize", {"get": ",".join(fields), "for": "us:*"},
                      key, f"Census concentration {year}")
    head, body = rows[0], rows[1:]
    ix = {h: i for i, h in enumerate(head)}
    keep = [[r[ix[f]] for f in fields] for r in body]
    keep.sort(key=lambda r: (r[0], r[4], r[6]))
    write_csv(OUT / "census" / f"concentration_{year}.csv",
              ["naics", "naics_label", "level", "sector", "type_of_operation",
               "type_of_operation_label", "firm_group", "firm_group_label", "firms",
               "revenue_thousands", "share_of_revenue_pct", "hhi"], keep)
    hhi = [num(r[11]) for r in keep]
    pct = [num(r[10]) for r in keep]
    bad = [r[0] for r, h in zip(keep, hhi) if h and not 0 <= float(h) <= 10000]
    bad += [r[0] for r, p in zip(keep, pct) if p and not 0 <= float(p) <= 100]
    issues = []
    if bad:
        issues.append(f"{len(bad)} rows with HHI outside 0 to 10,000 or share outside 0 to 100")
    industries = len({r[0] for r in keep})
    with_hhi = len({r[0] for r, h in zip(keep, hhi) if h})
    print(f"Census concentration {year}: {len(keep)} rows, {industries} industries")
    return {"name": f"concentration_{year}", "source": "Census", "status": "ok" if keep else "EMPTY",
            "series": industries, "first": str(year), "last": str(year), "rows": len(keep),
            "missing": sum(1 for h in hhi if not h), "issues": issues,
            "note": f"{with_hhi} of {industries} NAICS industries have an HHI; the rest give only "
                    "the largest firms' share of revenue (or are withheld)."}


# ------------------------------------------------------------------- report --

def write_report(results: list[dict], today: dt.date) -> str:
    bad = [r for r in results if r["status"] in ("STALE", "EMPTY", "FAILED")]
    skips = [r for r in results if r["status"] == "skipped"]
    pulled = [r for r in results if r["status"] not in ("skipped", "FAILED")]
    lines = [
        "# Industry data check report", "",
        f"Run date: {today.isoformat()}", "",
        f"**{len(pulled)} datasets pulled. {len(bad)} failed, stale or empty. "
        f"{len(skips)} skipped for a missing key.**", "",
        "Series counts columns (industries, categories or indexes). Missing counts blank cells "
        "inside a series's own history. Stale means the newest value is older than expected "
        f"({MAX_LAG['monthly']} days for monthly data, {MAX_LAG['quarterly']} for quarterly).", "",
        "| Dataset | Source | Series | First | Latest | Periods | Missing | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['name']} | {r['source']} | {r['series']} | {r['first']} | {r['last']} | "
                     f"{r['rows']} | {r['missing']} | {r['status']} |")
    lines += ["", "## Notes and checks", ""]
    for r in results:
        text = r["note"]
        if r["issues"]:
            text += " " + " ".join(i if i.endswith(".") else i + "." for i in r["issues"])
        lines.append(f"- **{r['name']}:** {text.strip()}")
    lines += ["", "## Known gaps", "",
              "- Services capacity: no free measure; G.17 covers manufacturing, mining and utilities only.",
              "- Competition from company revenue shares needs Sharadar (paid, not bought).",
              "- Regulation (QuantGov RegData, Federal Register) and technology (PatentsView) "
              "are not in this pull yet.",
              "- Government data uses NAICS; matching it to French's 12 and 49 groups needs a "
              "crosswalk, not built yet.", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------- main --

def smoke() -> int:
    ids = ["PCU325---325---", "PCU3311--3311--", "PCU311---311---"]
    year = dt.date.today().year
    values, prelim, absent = bls_fetch(ids, None, year - 1, year, batch=25, years=10)
    for sid in ids:
        v = {d: x for d, x in values[sid].items() if x}
        latest = max(v) if v else "none"
        print(f"{sid}: {len(v)} months, latest {latest} = {v.get(latest, '')}, "
              f"{len(prelim[sid])} preliminary")
    print("Not found:", absent or "none")
    return 0 if all(values[s] for s in ids) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="keyless BLS v1 check; writes nothing")
    args = ap.parse_args()
    if args.smoke:
        return smoke()

    today = dt.date.today()
    keys = {k: os.environ.get(k, "").strip() for k in
            ("FRED_API_KEY", "BEA_API_KEY", "CENSUS_API_KEY", "BLS_API_KEY")}
    for k, v in keys.items():
        print(f"{k}: {'set' if v else 'not set'}")

    results: list[dict] = []

    def run(name, source, need, fn, existing):
        missing = [k for k in need if not keys[k]]
        if missing:
            results.append(skipped(name, source, f"Skipped: {' and '.join(missing)} not set.", existing))
            print(f"::warning::{name} skipped: {', '.join(missing)} not set")
            return
        try:
            out = fn()
            results.extend(out if isinstance(out, list) else [out])
        except Exception as e:  # keep going with the other sources
            msg = str(e)
            for v in keys.values():
                if v:
                    msg = msg.replace(v, "***")
            print(f"::error::{name} failed: {msg}")
            results.append(failed(name, source, SourceError(msg)))

    run("gross_output", "BEA", ["BEA_API_KEY"],
        lambda: pull_bea(keys["BEA_API_KEY"], today), OUT / "bea")
    run("m3", "Census", ["CENSUS_API_KEY"],
        lambda: pull_m3(keys["CENSUS_API_KEY"], today), OUT / "census" / "m3.csv")
    for year in CONCENTRATION_YEARS:
        run(f"concentration_{year}", "Census", ["CENSUS_API_KEY"],
            lambda y=year: pull_concentration(keys["CENSUS_API_KEY"], y),
            OUT / "census" / f"concentration_{year}.csv")
    run("ppi_industry", "BLS", ["BLS_API_KEY"],
        lambda: pull_ppi(keys["BLS_API_KEY"], keys["FRED_API_KEY"] or None, today),
        OUT / "bls" / "ppi_industry.csv")
    run("capacity_utilization", "Fed G.17 via FRED", ["FRED_API_KEY"],
        lambda: pull_g17(keys["FRED_API_KEY"], today), OUT / "fed_g17" / "capacity_utilization.csv")

    report = write_report(results, today)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "INDUSTRY_CHECK_REPORT.md").write_text(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(report)
    print(report)
    # Fail the job only when a source that had its key failed outright.
    return 1 if any(r["status"] == "FAILED" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
