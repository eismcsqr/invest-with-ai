"""Tests for the macro factors other than rates: inflation, consumer spending and
the US dollar, on the Ken French 12 broad sectors, compared with the Macro
Exposure Scorecard v0.

Same structure as scripts/rates_test.py (relative-to-market slopes, bootstrap
ranges, periods, out of sample, crisis days, beta-adjusted, equal-weighted,
news split), with one surprise measure per factor. Analyst consensus on release
days is paid data, so each factor uses a free measure instead:

  Inflation  CPI release days, 1997 on. Surprise = core CPI month-on-month as
             first published minus its average over the prior 12 months (as
             known on release day). Checks: the 2-year yield and 5-year
             breakeven moves that day, and breakeven and yield together, to
             separate inflation news from rate news.
  Spending   Advance retail sales release days, 1976 on. Surprise = the 2-year
             yield move that day (the market's own reading of the print). The
             trend-based data surprise barely moves yields, so it is only a
             check. Compared with the same slope on Fed days to separate
             spending news from rate news.
  Dollar     No release day. Monthly sector returns against the monthly change
             in the broad trade-weighted dollar index, 1995 on. Checks: weekly
             changes, controlling for the 2-year yield, and big-move months.

Inputs (all already in the repo): data/events/event_calendar.csv,
data/events/release_first_prints.csv, data/fred/{DGS2,T5YIE,DTWEXB,DTWEXBGS}.csv,
data/french/industry12_{daily,monthly}_{vw,ew}.csv,
data/french/ff_factors_{daily,monthly}.csv, config/v0_macro_scores.csv.

Writes results/macro_factor_tests/ (CSV tables and RESULTS.md). Standard library only.
Run: python scripts/macro_factor_tests.py
"""

from __future__ import annotations

import bisect
import csv
import datetime as dt
import random
from pathlib import Path
from statistics import mean, median, pstdev

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config"
OUT = ROOT / "results" / "macro_factor_tests"

SECTORS = ["NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq",
           "Telcm", "Utils", "Shops", "Hlth", "Money", "Other"]
SECTOR_NAMES = {
    "NoDur": "Consumer staples (food, drink, apparel)",
    "Durbl": "Consumer durables (cars, appliances)",
    "Manuf": "Manufacturing",
    "Enrgy": "Energy",
    "Chems": "Chemicals",
    "BusEq": "Business equipment and tech",
    "Telcm": "Telecom",
    "Utils": "Utilities",
    "Shops": "Retail, wholesale, restaurants",
    "Hlth": "Healthcare",
    "Money": "Finance",
    "Other": "Other (construction, transport, services)",
}
BOOT = 2000
BOOT_WEEKLY = 1000
SEED = 20261126
BETA_DAYS, BETA_GAP = 250, 5        # daily beta window, ending 5 trading days before the event
BETA_MONTHS = 60                    # monthly beta window (prior months)
DOLLAR_SWITCH = "2006-02"           # first month measured on the current dollar index


# ------------------------------------------------------------------ loading --

def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def load_returns(path: Path) -> dict[str, dict[str, float]]:
    return {r["date"]: {s: float(r[s]) for s in SECTORS} for r in read_csv(path)}


def load_market(path: Path) -> dict[str, float]:
    return {r["date"]: float(r["mkt_rf"]) + float(r["rf"]) for r in read_csv(path) if r["mkt_rf"] and r["rf"]}


def load_fred(sid: str) -> dict[str, float]:
    return {r["date"]: float(r["value"]) for r in read_csv(DATA / "fred" / f"{sid}.csv") if r["value"] not in ("", ".")}


# -------------------------------------------------------------------- stats --

def ols(x, y):
    mx, my = mean(x), mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    if sxx == 0:
        return float("nan"), my
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    return b, my - b * mx


def slope(x, y) -> float:
    return ols(x, y)[0] if len(x) >= 3 else float("nan")


def ols2(x1, x2, y) -> tuple[float, float]:
    """Coefficients on x1 and x2 in y = a + b1 x1 + b2 x2."""
    m1, m2, my = mean(x1), mean(x2), mean(y)
    a = [v - m1 for v in x1]
    b = [v - m2 for v in x2]
    c = [v - my for v in y]
    s11 = sum(v * v for v in a)
    s22 = sum(v * v for v in b)
    s12 = sum(u * v for u, v in zip(a, b))
    s1y = sum(u * v for u, v in zip(a, c))
    s2y = sum(u * v for u, v in zip(b, c))
    det = s11 * s22 - s12 * s12
    if det == 0:
        return float("nan"), float("nan")
    return (s22 * s1y - s12 * s2y) / det, (s11 * s2y - s12 * s1y) / det


def boot_draws(x, y, rng, n_boot=BOOT, fn=None) -> list[float]:
    n, draws = len(x), []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        if fn is None:
            b = slope([x[i] for i in idx], [y[i] for i in idx])
        else:
            b = fn(idx)
        if b == b:
            draws.append(b)
    draws.sort()
    return draws


def pct_range(draws: list[float]) -> tuple[float, float]:
    if not draws:
        return float("nan"), float("nan")
    return draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def corr(a, b) -> float:
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else float("nan")


def spearman(a, b) -> float:
    return corr(ranks(a), ranks(b))


def confidence(lo, hi, period_slopes, oos_same_sign) -> str:
    sig = lo > 0 or hi < 0
    sign = 1 if lo + hi > 0 else -1
    periods_agree = all((b == b) and (b * sign > 0) for b in period_slopes if b == b)
    score = sum([sig, periods_agree, oos_same_sign])
    return {3: "High", 2: "Medium"}.get(score, "Low")


# ---------------------------------------------------------- event row maker --

def sector_cols(row, day, m, vw, ew, beta_win, beta_rets, beta_mkt, min_beta):
    """Fill raw, relative, equal-weighted relative and beta-adjusted returns for one period."""
    for s in SECTORS:
        row[f"{s}_raw"] = round(vw[day][s], 3)
        row[f"{s}_xs"] = round(vw[day][s] - m, 3)
        row[f"{s}_xs_ew"] = round(ew[day][s] - m, 3) if day in ew else None
        if len(beta_win) >= min_beta:
            beta, alpha = ols([beta_mkt[d] for d in beta_win], [beta_rets[d][s] for d in beta_win])
            row[f"{s}_xs_beta"] = round(vw[day][s] - alpha - beta * m, 3)
        else:
            row[f"{s}_xs_beta"] = None


class Daily:
    def __init__(self):
        self.vw = load_returns(DATA / "french" / "industry12_daily_vw.csv")
        self.ew = load_returns(DATA / "french" / "industry12_daily_ew.csv")
        self.mkt = load_market(DATA / "french" / "ff_factors_daily.csv")
        self.days = sorted(set(self.vw) & set(self.mkt))

    def row(self, day: str, base: dict) -> dict | None:
        if day not in self.vw or day not in self.mkt:
            return None
        k = bisect.bisect_left(self.days, day)
        win = self.days[max(0, k - BETA_GAP - BETA_DAYS):max(0, k - BETA_GAP)]
        row = dict(base)
        row["mkt_ret_pct"] = round(self.mkt[day], 3)
        sector_cols(row, day, self.mkt[day], self.vw, self.ew, win, self.vw, self.mkt, BETA_DAYS // 2)
        return row


# ----------------------------------------------------------------- analysis --

def xy(rows, col, xkey="x", pred=lambda r: True):
    pts = [(r[xkey], r[col]) for r in rows if pred(r) and r.get(col) is not None and r.get(xkey) is not None]
    return [p[0] for p in pts], [p[1] for p in pts]


def pts(rows, s, ycol, ctrl, pred=lambda r: True):
    """x, market and y lists for one sector. With ctrl, y is the sector's own return (raw or
    equal-weighted) so the market can be held fixed in a two-variable fit; otherwise y is relative."""
    out = []
    for r in rows:
        if not pred(r) or r.get("x") is None:
            continue
        if ycol == "ew":
            v = r.get(f"{s}_xs_ew")
            if v is not None and ctrl:
                v = v + r["mkt_ret_pct"]
        else:
            v = r.get(f"{s}_raw" if ctrl else f"{s}_xs")
        if v is not None:
            out.append((r["x"], r["mkt_ret_pct"], v))
    return [p[0] for p in out], [p[1] for p in out], [p[2] for p in out]


def est(x, m, y, ctrl) -> float:
    if len(x) < 3:
        return float("nan")
    return ols2(x, m, y)[0] if ctrl else slope(x, y)


def est_draws(x, m, y, ctrl, rng, n_boot):
    return boot_draws(x, y, rng, n_boot,
                      fn=lambda idx: est([x[i] for i in idx], [m[i] for i in idx], [y[i] for i in idx], ctrl))


def analyse(rows, periods, crisis, news_labels, min_x, rng, n_boot=BOOT, ctrl=False):
    """Per-sector slopes on the factor measure, with the rates test's checks.

    Default: slope of (sector return - market return). With ctrl=True: coefficient on the factor in a
    fit of the sector's own return on the factor and the market return together, i.e. the factor's
    effect holding the market's move fixed (used for the dollar, which moves the whole market)."""
    n = len(rows)
    half = rows[: n // 2], rows[n // 2:]
    sens = []
    for s in SECTORS:
        x, m, y = pts(rows, s, "vw", ctrl)
        draws = est_draws(x, m, y, ctrl, rng, n_boot)
        lo, hi = pct_range(draws)
        rec = {"sector": s, "name": SECTOR_NAMES[s], "events": len(x), "xs_slope": est(x, m, y, ctrl),
               "xs_lo": lo, "xs_hi": hi, "_draws": draws}
        rx, ry = xy(rows, f"{s}_raw")
        rec["raw_slope"] = slope(rx, ry)
        rec["raw_lo"], rec["raw_hi"] = pct_range(boot_draws(rx, ry, rng, n_boot))
        if ctrl:
            rec["simple_relative_slope"] = slope(*xy(rows, f"{s}_xs"))
        rec["beta_adj_slope"] = slope(*xy(rows, f"{s}_xs_beta"))
        rec["ew_slope"] = est(*pts(rows, s, "ew", ctrl), ctrl)
        for label, a, z in periods:
            px, pm, py = pts(rows, s, "vw", ctrl, lambda r, a=a, z=z: a <= r["day"] <= z)
            rec[f"p:{label}"] = est(px, pm, py, ctrl) if len(px) >= 10 else float("nan")
            rec[f"n:{label}"] = len(px)
        rec["ex_crisis_slope"] = est(*pts(rows, s, "vw", ctrl, lambda r: not crisis(r["day"])), ctrl)
        for news in news_labels:
            nx, ny = xy(rows, f"{s}_xs_beta", pred=lambda r, news=news: r["news"] == news)
            rec[f"news:{news}"] = slope(nx, ny) if len(nx) >= 10 else float("nan")
            rec[f"nn:{news}"] = len(nx)
        rec["train_slope"] = est(*pts(half[0], s, "vw", ctrl), ctrl)
        rec["test_slope"] = est(*pts(half[1], s, "vw", ctrl), ctrl)
        target = f"{s}_xs_beta" if ctrl else f"{s}_xs"
        hits = tot = 0
        for r in half[1]:
            if abs(r["x"]) >= min_x and r.get(target):
                tot += 1
                hits += (rec["train_slope"] * r["x"] > 0) == (r[target] > 0)
        rec["oos_hit_rate"] = hits / tot if tot else float("nan")
        rec["oos_events"] = tot
        rec["confidence"] = confidence(lo, hi, [rec[f"p:{p[0]}"] for p in periods],
                                       rec["train_slope"] * rec["test_slope"] > 0)
        sens.append(rec)
    mx, my = xy(rows, "mkt_ret_pct")
    summary = {
        "market_slope": slope(mx, my),
        "market_range": pct_range(boot_draws(mx, my, rng, n_boot)),
        "split": half[1][0]["day"],
        "spearman": spearman([r["train_slope"] for r in sens], [r["test_slope"] for r in sens]),
    }
    return sens, summary


def check_slopes(rows, xkey, rng, label, pred=lambda r: True, n_boot=BOOT):
    """Relative-return slope on another measure of the same factor, with a range."""
    out = {}
    for s in SECTORS:
        x, y = xy(rows, f"{s}_xs", xkey=xkey, pred=pred)
        out[s] = (slope(x, y), *pct_range(boot_draws(x, y, rng, n_boot)), len(x))
    return out


def olsk(cols: list[list[float]], y: list[float]) -> list[float]:
    """Slope coefficients of y on several regressors (with an intercept), by normal equations."""
    k = len(cols)
    means = [mean(c) for c in cols]
    my = mean(y)
    cc = [[v - mu for v in c] for c, mu in zip(cols, means)]
    yc = [v - my for v in y]
    a = [[sum(u * v for u, v in zip(cc[i], cc[j])) for j in range(k)] + [sum(u * v for u, v in zip(cc[i], yc))]
         for i in range(k)]
    for i in range(k):
        piv = max(range(i, k), key=lambda r: abs(a[r][i]))
        if abs(a[piv][i]) < 1e-12:
            return [float("nan")] * k
        a[i], a[piv] = a[piv], a[i]
        for r in range(k):
            if r != i:
                f = a[r][i] / a[i][i]
                a[r] = [u - f * v for u, v in zip(a[r], a[i])]
    return [a[i][k] / a[i][i] for i in range(k)]


def joint_slopes(rows, k1, k2, rng, pred=lambda r: True, ctrl=False):
    """Coefficient on k1 holding k2 fixed (and the market too, with ctrl), per sector, with a range."""
    out = {}
    for s in SECTORS:
        ycol = f"{s}_raw" if ctrl else f"{s}_xs"
        sel = [r for r in rows if pred(r) and r.get(k1) is not None and r.get(k2) is not None and r.get(ycol) is not None]
        cols = [[r[k1] for r in sel], [r[k2] for r in sel]] + ([[r["mkt_ret_pct"] for r in sel]] if ctrl else [])
        y = [r[ycol] for r in sel]
        b = olsk(cols, y)[0]
        draws = boot_draws(cols[0], y, rng, BOOT,
                           fn=lambda idx: olsk([[c[i] for i in idx] for c in cols], [y[i] for i in idx])[0])
        out[s] = (b, *pct_range(draws), len(sel))
    return out


def ctrl_check(rows, rng, pred=lambda r: True, n_boot=BOOT):
    """Factor coefficient holding the market fixed, on a subset or another frequency."""
    out = {}
    for s in SECTORS:
        x, m, y = pts(rows, s, "vw", True, pred)
        out[s] = (est(x, m, y, True), *pct_range(est_draws(x, m, y, True, rng, n_boot)), len(x))
    return out


# ------------------------------------------------------------------ factors --

def crisis_day(day: str) -> bool:
    return day[:4] in ("2008", "2009") or day.startswith("2020-03")


def release_rows(event: str, daily: Daily) -> list[dict]:
    """Release days from the event calendar that share the day with no other tracked event."""
    out, dropped = [], 0
    for r in read_csv(DATA / "events" / "event_calendar.csv"):
        if r["event"] != event or r["subtype"] != "data release":
            continue
        if r["same_day_events"]:
            dropped += 1
            continue
        out.append(r)
    return out, dropped


def num(v):
    return float(v) if v not in ("", None) else None


def inflation_events(daily: Daily):
    core = {r["release_date"]: float(r["data_surprise_pp"])
            for r in read_csv(DATA / "events" / "release_first_prints.csv")
            if r["series_id"] == "CPILFESL" and r["data_surprise_pp"]}
    cal, dropped = release_rows("cpi", daily)
    rows, notes = [], []
    for r in cal:
        if r["date"] not in core:
            continue
        sur = core[r["date"]]
        base = {"date": r["date"], "day": r["trading_day"], "core_surprise_pp": round(sur, 4),
                "x": sur / 0.1, "dgs2_chg_bp": num(r["dgs2_chg_bp"]), "t5yie_chg_bp": num(r["t5yie_chg_bp"])}
        base["y10"] = base["dgs2_chg_bp"] / 10 if base["dgs2_chg_bp"] is not None else None
        base["be5"] = base["t5yie_chg_bp"] / 5 if base["t5yie_chg_bp"] is not None else None
        row = daily.row(r["trading_day"], base)
        if row is None:
            continue
        m = row["mkt_ret_pct"]
        if abs(sur) < 0.03:
            row["news"] = "flat"
        else:
            row["news"] = "stocks fell on a hot print" if (sur > 0) == (m < 0) else "stocks rose on a hot print"
        rows.append(row)
    notes.append(f"{dropped} CPI release days that fell on the same day as retail sales, PCE or a Fed decision were left out.")
    return rows, notes


def spending_events(daily: Daily):
    rs = {r["release_date"]: float(r["data_surprise_pp"])
          for r in read_csv(DATA / "events" / "release_first_prints.csv")
          if r["series_id"] == "RSAFS" and r["data_surprise_pp"]}
    cal, dropped = release_rows("retail_sales", daily)
    rows = []
    for r in cal:
        dy = num(r["dgs2_chg_bp"])
        if dy is None:
            continue
        sur = rs.get(r["date"])
        base = {"date": r["date"], "day": r["trading_day"], "dgs2_chg_bp": dy, "x": dy / 10,
                "retail_surprise_pp": sur, "data_x": sur / 0.5 if sur is not None else None}
        row = daily.row(r["trading_day"], base)
        if row is None:
            continue
        m = row["mkt_ret_pct"]
        if abs(dy) < 1:
            row["news"] = "flat"
        else:
            row["news"] = "growth news" if (dy > 0) == (m > 0) else "tightening news"
        rows.append(row)
    notes = [f"{dropped} retail sales release days that fell on the same day as CPI, PCE or a Fed decision were left out."]
    return rows, notes


def fed_events(daily: Daily):
    rows, seen = [], set()
    for r in read_csv(DATA / "events" / "event_calendar.csv"):
        if r["event"] != "fomc" or r["in_rates_test"] != "yes" or r["trading_day"] in seen:
            continue
        dy = num(r["dgs2_chg_bp"])
        if dy is None:
            continue
        seen.add(r["trading_day"])
        row = daily.row(r["trading_day"], {"date": r["date"], "day": r["trading_day"], "x": dy / 10})
        if row is not None:
            rows.append(row)
    return rows


def period_last(series: dict[str, float], keyfn) -> dict:
    out = {}
    for d in sorted(series):
        out[keyfn(d)] = series[d]
    return out


def dollar_changes(keyfn, keys: list, switch_key) -> dict:
    b = period_last(load_fred("DTWEXB"), keyfn)
    gs = period_last(load_fred("DTWEXBGS"), keyfn)
    out = {}
    for prev, cur in zip(keys, keys[1:]):
        src = gs if cur >= switch_key else b
        if prev in src and cur in src:
            out[cur] = 100 * (src[cur] / src[prev] - 1)
    return out


def month_key(d: str) -> str:
    return d[:7]


def week_key(d: str) -> str:
    y, w, _ = dt.date.fromisoformat(d).isocalendar()
    return f"{y}-W{w:02d}"


def compound(daily_rets: list[float]) -> float:
    g = 1.0
    for r in daily_rets:
        g *= 1 + r / 100
    return 100 * (g - 1)


def dollar_rows():
    vw = load_returns(DATA / "french" / "industry12_monthly_vw.csv")
    ew = load_returns(DATA / "french" / "industry12_monthly_ew.csv")
    mkt = load_market(DATA / "french" / "ff_factors_monthly.csv")
    months = sorted(set(vw) & set(mkt))
    all_months = sorted({month_key(d) for d in load_fred("DTWEXB")} | {month_key(d) for d in load_fred("DTWEXBGS")})
    dchg = dollar_changes(month_key, all_months, DOLLAR_SWITCH)
    y2 = period_last(load_fred("DGS2"), month_key)
    rows = []
    for k, mo in enumerate(months):
        if mo not in dchg:
            continue
        prev = months[k - 1] if k else None
        win = months[max(0, k - BETA_MONTHS):k]
        row = {"day": mo, "x": round(dchg[mo], 4), "dollar_chg_pct": round(dchg[mo], 4),
               "dgs2_chg_bp": round((y2[mo] - y2[prev]) * 100, 1) if prev in y2 and mo in y2 else None,
               "mkt_ret_pct": round(mkt[mo], 3)}
        row["y10"] = row["dgs2_chg_bp"] / 10 if row["dgs2_chg_bp"] is not None else None
        sector_cols(row, mo, mkt[mo], vw, ew, win, vw, mkt, 36)
        if abs(row["x"]) < 0.25:
            row["news"] = "flat"
        else:
            row["news"] = "risk-off (dollar and stocks opposite)" if (row["x"] > 0) == (mkt[mo] < 0) \
                else "risk-on (dollar and stocks together)"
        rows.append(row)
    return rows


def dollar_weekly_rows(daily: Daily):
    weeks: dict[str, list[str]] = {}
    for d in daily.days:
        if d >= "1995-01-01":
            weeks.setdefault(week_key(d), []).append(d)
    keys = sorted(weeks)
    all_weeks = sorted({week_key(d) for d in load_fred("DTWEXB") if d >= "1995"} |
                       {week_key(d) for d in load_fred("DTWEXBGS")})
    dchg = dollar_changes(week_key, all_weeks, week_key("2006-01-09"))
    rows = []
    for wk in keys:
        if wk not in dchg:
            continue
        days = weeks[wk]
        m = compound([daily.mkt[d] for d in days])
        row = {"day": days[-1], "x": dchg[wk], "mkt_ret_pct": m}
        for s in SECTORS:
            row[f"{s}_raw"] = compound([daily.vw[d][s] for d in days])
            row[f"{s}_xs"] = row[f"{s}_raw"] - m
        rows.append(row)
    return rows


# ------------------------------------------------------------- v0 compare --

def compare_v0(factor: str, sens, measure_note: str):
    by = {r["sector"]: r for r in sens}
    v0 = [r for r in read_csv(CONFIG / "v0_macro_scores.csv") if r["factor"] == factor]
    avg_all = mean(float(r["net"]) for r in v0)
    groups: dict[str, list[dict]] = {}
    for r in v0:
        groups.setdefault(r["french_group"], []).append(r)
    out = []
    for g, items in groups.items():
        score = mean(float(i["net"]) for i in items)
        rec = by[g]
        if score < avg_all - 0.5:
            expect = "worse than market"
        elif score > avg_all + 0.5:
            expect = "better than market"
        else:
            expect = "about the market"
        if rec["xs_hi"] < 0:
            measured = "worse than market"
        elif rec["xs_lo"] > 0:
            measured = "better than market"
        else:
            measured = "no clear difference"
        if measured == "no clear difference":
            verdict = "agrees" if expect == "about the market" else "unclear"
        elif expect == "about the market":
            verdict = "disagrees"
        else:
            verdict = "agrees" if measured == expect else "disagrees (opposite)"
        out.append({
            "factor": factor, "french_group": g, "name": SECTOR_NAMES[g],
            "v0_types": "; ".join(f"{i['company_type']} ({int(float(i['net'])):+d})" for i in items),
            "v0_avg": score, "v0_all_types_avg": avg_all, "mapping": items[0]["mapping_fit"],
            "v0_expects": expect, "xs_slope": rec["xs_slope"], "xs_lo": rec["xs_lo"], "xs_hi": rec["xs_hi"],
            "measured": measured, "verdict": verdict, "confidence": rec["confidence"],
        })
    out.sort(key=lambda r: r["v0_avg"])
    rho = spearman([r["v0_avg"] for r in out], [r["xs_slope"] for r in out])
    return out, rho


# ------------------------------------------------------------------ output --

def f2(v, plus=True) -> str:
    if v is None or v != v:
        return "n/a"
    return f"{v:+.2f}" if plus else f"{v:.2f}"


def rng_txt(lo, hi) -> str:
    return f"{f2(lo)} to {f2(hi)}"


def write_table(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [k for k in rows[0].keys() if not k.startswith("_")]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items() if k in header})


def sens_table(sens, periods, news_labels, checks: list[tuple[str, dict]], main_label="Relative to market") -> list[str]:
    head = (f"| Sector | {main_label} | 95% range | " + " | ".join(p[0] for p in periods) +
            " | Without crisis | Beta-adjusted | Equal-weighted | " + " | ".join(n.capitalize() for n in news_labels) +
            "".join(f" | {c[0]}" for c in checks) + " | Confidence |")
    sep = "|---|---|---|" + "---|" * (len(periods) + 3 + len(news_labels) + len(checks)) + "---|"
    lines = [head, sep]
    for r in sorted(sens, key=lambda r: r["xs_slope"]):
        cells = [r["name"], f2(r["xs_slope"]), rng_txt(r["xs_lo"], r["xs_hi"])]
        cells += [f2(r[f"p:{p[0]}"]) for p in periods]
        cells += [f2(r["ex_crisis_slope"]), f2(r["beta_adj_slope"]), f2(r["ew_slope"])]
        cells += [f2(r[f"news:{n}"]) for n in news_labels]
        for _, c in checks:
            b, lo, hi, _n = c[r["sector"]]
            star = "*" if (lo > 0 or hi < 0) else ""
            cells.append(f"{f2(b)}{star}")
        cells.append(r["confidence"])
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def oos_table(sens, summary) -> list[str]:
    lines = [f"Fitted before {summary['split']}, checked from {summary['split']} on. Rank agreement of sector "
             f"slopes between the halves (Spearman): {f2(summary['spearman'], False)}.", "",
             "| Sector | First half | Second half | Second-half direction hit rate |", "|---|---|---|---|"]
    for r in sorted(sens, key=lambda r: r["xs_slope"]):
        hr = f"{r['oos_hit_rate']:.0%} of {r['oos_events']}" if r["oos_events"] else "n/a"
        lines.append(f"| {r['name']} | {f2(r['train_slope'])} | {f2(r['test_slope'])} | {hr} |")
    return lines


def v0_table(comp, rho) -> list[str]:
    lines = ["| Group | v0 company types (score) | v0 avg | Mapping | v0 implies | Measured (range) | Result | Confidence |",
             "|---|---|---|---|---|---|---|---|"]
    for c in comp:
        lines.append(f"| {c['name']} | {c['v0_types']} | {c['v0_avg']:+.1f} | {c['mapping']} | {c['v0_expects']} | "
                     f"{c['measured']}: {f2(c['xs_slope'])} ({rng_txt(c['xs_lo'], c['xs_hi'])}) | {c['verdict']} | "
                     f"{c['confidence']} |")
    lines += ["", f"Rank agreement between v0 averages and measured slopes ({len(comp)} groups, Spearman): {f2(rho, False)}. "
              f"v0 implies \"worse than market\" when the group's average is more than 0.5 below the average of all ten "
              f"v0 types for this factor ({comp[0]['v0_all_types_avg']:+.1f}), \"better\" when more than 0.5 above."]
    return lines


def main() -> None:
    rng = random.Random(SEED)
    daily = Daily()
    OUT.mkdir(parents=True, exist_ok=True)
    md = ["# Macro factor tests on broad sectors: inflation, spending and the dollar", "",
          f"Run date: {dt.date.today().isoformat()}", "",
          "All numbers are a sector's return minus the market's return (percentage points), per unit of the "
          "factor's surprise measure, with 95% bootstrap ranges. Value-weighted Ken French 12 industries unless "
          "noted. A positive number means the sector beats the market when the factor comes in higher than "
          "expected. Confidence: High when the range excludes zero, the sign holds in every period and the "
          "out-of-sample half has the same sign; Medium for two of three; Low otherwise. In check columns, * marks "
          "a range that excludes zero.", ""]
    v0_all = []

    # ---------------------------------------------------------- inflation
    inf_rows, inf_notes = inflation_events(daily)
    inf_periods = [("1997-2007", "1997-01-01", "2007-12-31"), ("2008-2015", "2008-01-01", "2015-12-31"),
                   ("2016 on", "2016-01-01", "2099-12-31")]
    inf_news = ["stocks fell on a hot print", "stocks rose on a hot print"]
    inf_sens, inf_sum = analyse(inf_rows, inf_periods, crisis_day, inf_news, 0.25, rng)
    inf_y = check_slopes(inf_rows, "y10", rng, "2y")
    inf_be = check_slopes(inf_rows, "be5", rng, "be5")
    inf_joint = joint_slopes(inf_rows, "be5", "y10", rng)
    xs_ = [r["core_surprise_pp"] for r in inf_rows]
    c_y = corr(*[list(t) for t in zip(*[(r["core_surprise_pp"], r["dgs2_chg_bp"]) for r in inf_rows if r["dgs2_chg_bp"] is not None])])
    c_be = corr(*[list(t) for t in zip(*[(r["core_surprise_pp"], r["t5yie_chg_bp"]) for r in inf_rows if r["t5yie_chg_bp"] is not None])])
    n_be = sum(r["t5yie_chg_bp"] is not None for r in inf_rows)
    for r in inf_sens:
        r["vs_2y_slope"], r["vs_2y_lo"], r["vs_2y_hi"], _ = inf_y[r["sector"]]
        r["vs_breakeven_slope"], r["vs_breakeven_lo"], r["vs_breakeven_hi"], _ = inf_be[r["sector"]]
        r["breakeven_beyond_rates"], r["bbr_lo"], r["bbr_hi"], _ = inf_joint[r["sector"]]
    inf_comp, inf_rho = compare_v0("inflation", inf_sens, "core CPI surprise")
    v0_all += inf_comp
    write_table(OUT / "inflation_events.csv", inf_rows)
    write_table(OUT / "inflation_sensitivity.csv", inf_sens)
    md += ["## Inflation", "",
           f"**Events:** {len(inf_rows)} CPI release days from {inf_rows[0]['day']} to {inf_rows[-1]['day']}. "
           f"**Surprise:** core CPI month-on-month as first published minus its average over the prior 12 months, "
           f"per +0.1 point (typical size {pstdev(xs_):.2f} point). It moves markets the way a real surprise should: "
           f"correlation {f2(c_y, False)} with the 2-year yield move and {f2(c_be, False)} with the 5-year breakeven "
           f"move that day ({n_be} days since 2003).", "",
           f"The market itself moves {f2(inf_sum['market_slope'])}% per +0.1 point "
           f"(range {rng_txt(*inf_sum['market_range'])}).", "",
           "Checks: *2y* = slope on the 2-year yield move per +10 bp, same days. *Breakeven* = slope on the 5-year "
           "breakeven move per +5 bp (2003 on). *Inflation beyond rates* = breakeven slope holding the 2-year yield "
           "move fixed, per +5 bp. News columns split days by whether stocks fell on a hot print (or rose on a cool "
           "one), and are beta-adjusted.", ""]
    md += sens_table(inf_sens, inf_periods, inf_news,
                     [("2y", inf_y), ("Breakeven", inf_be), ("Inflation beyond rates", inf_joint)])
    md += ["", f"Periods hold {', '.join(str(inf_sens[0]['n:' + p[0]]) + ' (' + p[0] + ')' for p in inf_periods)} events.",
           "", "### Out of sample", ""] + oos_table(inf_sens, inf_sum)
    md += ["", "### Compared with v0 (inflation)", ""] + v0_table(inf_comp, inf_rho) + [""]

    # ----------------------------------------------------------- spending
    sp_rows, sp_notes = spending_events(daily)
    fed_rows = fed_events(daily)
    sp_periods = [("1976-1993", "1976-01-01", "1993-12-31"), ("1994-2007", "1994-01-01", "2007-12-31"),
                  ("2008-2015", "2008-01-01", "2015-12-31"), ("2016 on", "2016-01-01", "2099-12-31")]
    sp_news = ["growth news", "tightening news"]
    sp_sens, sp_sum = analyse(sp_rows, sp_periods, crisis_day, sp_news, 0.1, rng)
    sp_data = check_slopes(sp_rows, "data_x", rng, "data")
    fed_sens, _ = analyse(fed_rows, [], crisis_day, [], 0.1, rng)
    fed_by = {r["sector"]: r for r in fed_sens}
    beyond = {}
    for r in sp_sens:
        f = fed_by[r["sector"]]
        k = min(len(r["_draws"]), len(f["_draws"]))
        a, b = r["_draws"][:], f["_draws"][:]
        rng.shuffle(a)
        rng.shuffle(b)
        diff = sorted(x - y for x, y in zip(a[:k], b[:k]))
        beyond[r["sector"]] = (r["xs_slope"] - f["xs_slope"], *pct_range(diff), r["events"])
        r["fed_day_slope"], r["fed_day_lo"], r["fed_day_hi"] = f["xs_slope"], f["xs_lo"], f["xs_hi"]
        r["spending_beyond_rates"], r["sbr_lo"], r["sbr_hi"], _ = beyond[r["sector"]]
        r["data_surprise_slope"], r["data_lo"], r["data_hi"], r["data_events"] = sp_data[r["sector"]]
    fed_tab = {s: (fed_by[s]["xs_slope"], fed_by[s]["xs_lo"], fed_by[s]["xs_hi"], 0) for s in SECTORS}
    pts = [(r["retail_surprise_pp"], r["dgs2_chg_bp"]) for r in sp_rows if r["retail_surprise_pp"] is not None]
    c_rs = corr([p[0] for p in pts], [p[1] for p in pts])
    sp_comp, sp_rho = compare_v0("spending", sp_sens, "2-year yield move")
    # Same comparison on the spending-beyond-rates measure.
    alt = [dict(r, xs_slope=beyond[r["sector"]][0], xs_lo=beyond[r["sector"]][1], xs_hi=beyond[r["sector"]][2])
           for r in sp_sens]
    sp_comp2, sp_rho2 = compare_v0("spending", alt, "beyond rates")
    for c in sp_comp2:
        c["factor"] = "spending (beyond rates)"
    v0_all += sp_comp + sp_comp2
    write_table(OUT / "spending_events.csv", sp_rows)
    write_table(OUT / "spending_sensitivity.csv", sp_sens)
    md += ["## Consumer spending", "",
           f"**Events:** {len(sp_rows)} advance retail sales release days from {sp_rows[0]['day']} to "
           f"{sp_rows[-1]['day']}. **Surprise:** the 2-year yield move that day, per +10 bp: a stronger print than "
           f"expected pushes yields up. Median move {median(abs(r['dgs2_chg_bp']) for r in sp_rows):.1f} bp. The free "
           f"data surprise (first print minus the prior 12-month average, {len(pts)} prints since 2001) is a weak "
           f"stand-in for the consensus surprise: correlation with the yield move is only {f2(c_rs, False)}, so it "
           "is shown as a check only.", "",
           f"The market itself moves {f2(sp_sum['market_slope'])}% per +10 bp on these days "
           f"(range {rng_txt(*sp_sum['market_range'])}).", "",
           "Because a yield jump on these days is partly rate news, the table also shows the same slope on Fed "
           f"decision days ({len(fed_rows)} days, the rates test's events) and the difference, *spending beyond "
           "rates*: how much better a sector does on a strong spending day than on a hawkish Fed day with the same "
           "yield move. *Data surprise* = slope on the first-print surprise per +0.5 point. Growth news = yield and "
           "stocks moved the same way; tightening news = opposite ways (beta-adjusted).", ""]
    md += sens_table(sp_sens, sp_periods, sp_news,
                     [("Fed days", fed_tab), ("Spending beyond rates", beyond), ("Data surprise", sp_data)])
    md += ["", f"Periods hold {', '.join(str(sp_sens[0]['n:' + p[0]]) + ' (' + p[0] + ')' for p in sp_periods)} events.",
           "", "### Out of sample", ""] + oos_table(sp_sens, sp_sum)
    md += ["", "### Compared with v0 (spending)", "", "On the retail-day slope:", ""] + v0_table(sp_comp, sp_rho)
    md += ["", "On spending beyond rates:", ""] + v0_table(sp_comp2, sp_rho2) + [""]

    # ------------------------------------------------------------- dollar
    d_rows = dollar_rows()
    w_rows = dollar_weekly_rows(daily)
    d_periods = [("1995-2007", "1995-01", "2007-12"), ("2008-2015", "2008-01", "2015-12"), ("2016 on", "2016-01", "2099-12")]
    d_news = ["risk-off (dollar and stocks opposite)", "risk-on (dollar and stocks together)"]
    d_sens, d_sum = analyse(d_rows, d_periods, crisis_day, d_news, 0.1, rng, ctrl=True)
    d_week = ctrl_check(w_rows, rng, n_boot=BOOT_WEEKLY)
    d_ctrl = joint_slopes(d_rows, "x", "y10", rng, ctrl=True)
    d_big = ctrl_check(d_rows, rng, pred=lambda r: abs(r["x"]) >= 2)
    d_simple = check_slopes(d_rows, "x", rng, "simple")
    for r in d_sens:
        r["weekly_slope"], r["weekly_lo"], r["weekly_hi"], r["weeks"] = d_week[r["sector"]]
        r["rates_controlled"], r["rc_lo"], r["rc_hi"], _ = d_ctrl[r["sector"]]
        r["big_move_slope"], r["big_lo"], r["big_hi"], r["big_months"] = d_big[r["sector"]]
        _, r["simple_relative_lo"], r["simple_relative_hi"], _ = d_simple[r["sector"]]
    d_comp, d_rho = compare_v0("dollar", d_sens, "monthly dollar change")
    v0_all += d_comp
    write_table(OUT / "dollar_months.csv", d_rows)
    write_table(OUT / "dollar_sensitivity.csv", d_sens)
    md += ["## US dollar", "",
           f"**Periods:** {len(d_rows)} months from {d_rows[0]['day']} to {d_rows[-1]['day']}. **Measure:** percent "
           f"change in the Fed's broad trade-weighted dollar index over the month, per +1% (typical month "
           f"{pstdev([r['x'] for r in d_rows]):.1f}%). The dollar has no release day, so this measures sensitivity to "
           "dollar moves, not to dollar surprises. The old index (1995 to 2005) and the current one (2006 on) are "
           "each used only for changes within their own span.", "",
           f"The market itself moves {f2(d_sum['market_slope'])}% per +1% dollar move "
           f"(range {rng_txt(*d_sum['market_range'])}). Because the whole market moves this much with the dollar, "
           "the simple sector-minus-market slope mostly rewards low-beta sectors (utilities, healthcare, staples) for "
           "falling less than the market in strong-dollar months. So the headline here is different from the other "
           "factors: the dollar coefficient in a fit of the sector's own return on the dollar move and the market "
           "return together, i.e. the dollar's effect holding the market's move fixed. The simple slope is kept as a "
           "check.", "",
           f"Checks: *Simple relative* = sector minus market, as for the other factors. *Weekly* = headline method on "
           f"{len(w_rows)} weeks. *Rates held fixed* = also holding the month's 2-year yield move fixed. *Big months* "
           f"= only months with a move of 2% or more ({d_sens[0]['big_months']} months). Beta-adjusted uses each "
           "sector's beta over the prior 60 months instead of the full-sample fit. Risk-off months = dollar and stocks "
           "moved opposite ways (beta-adjusted).", ""]
    md += sens_table(d_sens, d_periods, d_news,
                     [("Simple relative", d_simple), ("Weekly", d_week), ("Rates held fixed", d_ctrl),
                      ("Big months", d_big)], main_label="Holding the market fixed")
    md += ["", f"Periods hold {', '.join(str(d_sens[0]['n:' + p[0]]) + ' (' + p[0] + ')' for p in d_periods)} months.",
           "", "### Out of sample", ""] + oos_table(d_sens, d_sum)
    md += ["", "### Compared with v0 (dollar)", ""] + v0_table(d_comp, d_rho) + [""]

    write_table(OUT / "v0_comparison.csv", v0_all)
    notes = inf_notes + sp_notes
    md += ["## Data notes", ""] + [f"- {n}" for n in notes]
    (OUT / "RESULTS.md").write_text("\n".join(md) + "\n")

    for name, sens in (("inflation", inf_sens), ("spending", sp_sens), ("dollar", d_sens)):
        print(f"--- {name}")
        for r in sorted(sens, key=lambda r: r["xs_slope"]):
            print(f"{r['sector']:6s} {r['xs_slope']:+.3f} [{r['xs_lo']:+.3f}, {r['xs_hi']:+.3f}] {r['confidence']}")
    print("fed check", {s: round(fed_by[s]["xs_slope"], 2) for s in SECTORS})
    print(f"rho inflation {inf_rho:.2f} spending {sp_rho:.2f}/{sp_rho2:.2f} dollar {d_rho:.2f}")


if __name__ == "__main__":
    main()
