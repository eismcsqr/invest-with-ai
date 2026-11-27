"""Industry pillar run: current readings, scores and a measured check for
Kenneth French's 12 industry groups, from the free industry data on main.

Method (agreed Nov 25, tracker task "Industry method"):
  1. Mechanism: how strongly each factor reaches a group's companies, channel
     by channel. config/industry_exposure_v0.csv holds the v0 judgment
     (exposure 0 to 3 = channel scores added up, capped at 3).
  2. Current reading: tailwind (+1), neutral (0) or headwind (-1) per factor,
     from where the group's data sits against its own history: top fifth =
     tailwind, bottom fifth = headwind.
  3. Measured check: the group's monthly return after the market, the 2-year
     yield and the dollar are taken out, tested against the reading over the
     same period ("moves with") and the period after the data comes out
     ("leads"), with bootstrap ranges, a false-discovery check across all
     tests and a sign-flip check between the first and second half.
  4. Confidence from how well the check, the data's coverage and the group
     mapping agree. Score = reading x exposure, shown as a range.

Factors the free data covers:
  Demand cycle   BEA real gross output, year-on-year growth (quarterly, all
                 groups). Cross-check: Census M3 shipments deflated by BLS
                 producer prices (monthly, manufacturing groups).
  Capacity cycle Fed G.17 capacity use, level (monthly). Scored only where
                 the series cover at least half the group's output.
  Coping with    BEA gross output prices, year-on-year growth, minus the same
  shocks         for all industries: is the group raising prices faster than
                 the economy (quarterly, all groups). Cross-check: BLS
                 producer prices against the average of all mapped indexes.
Not scored yet: competition (needs company revenue shares; Census
concentration for 2017 and 2022 is shown as context), regulation (QuantGov
not pulled), technology (PatentsView not pulled).

The mapping from government industries to French's groups is in
config/industry_crosswalk.csv. It follows French's SIC definitions
(Siccodes12); BEA industries that span groups are split by rough output
shares, noted on each row.

Inputs (all in the repo): data/industry/{bea,census,bls,fed_g17}/,
data/french/industry12_monthly_vw.csv, data/french/ff_factors_monthly.csv,
data/fred/{DGS2,DTWEXB,DTWEXBGS}.csv, config/industry_crosswalk.csv,
config/industry_exposure_v0.csv.

Writes results/industry_run/. Standard library only.
Run: python scripts/industry_assessment.py
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IND = DATA / "industry"
CONFIG = ROOT / "config"
OUT = ROOT / "results" / "industry_run"

GROUPS = ["NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq",
          "Telcm", "Utils", "Shops", "Hlth", "Money", "Other"]
GROUP_NAMES = {
    "NoDur": "Consumer staples", "Durbl": "Consumer durables", "Manuf": "Manufacturing",
    "Enrgy": "Energy", "Chems": "Chemicals", "BusEq": "Business equipment and tech",
    "Telcm": "Telecom", "Utils": "Utilities", "Shops": "Retail and wholesale",
    "Hlth": "Healthcare", "Money": "Finance", "Other": "Other",
}
FACTORS = ["demand", "capacity", "competition", "regulation", "technology", "coping"]
FACTOR_NAMES = {
    "demand": "Demand cycle", "capacity": "Capacity cycle", "competition": "Competition",
    "regulation": "Regulation", "technology": "Technology shifts", "coping": "Coping with shocks",
}
NOT_PULLED = {
    "competition": "needs company revenue shares (Sharadar); Census concentration shown as context only",
    "regulation": "QuantGov RegData not pulled yet",
    "technology": "PatentsView not pulled yet",
}

# How each group's industries match French's definition, per measure.
# good: the series are the group's core businesses; partial: a sizable part
# is missing or mixed in; loose: the group is a catch-all.
FIT = defaultdict(lambda: "good")
FIT.update({("Shops", m): "partial" for m in ("demand", "coping")})
FIT.update({("Money", m): "partial" for m in ("demand", "coping")})
FIT.update({("Other", m): "loose" for m in ("demand", "coping")})
FIT.update({("Hlth", "demand"): "partial", ("Hlth", "coping"): "partial"})
FIT[("Chems", "capacity")] = "partial"   # G.17 chemicals include drugs (Hlth)
FIT[("Chems", "demand_m3")] = "partial"

TOP, BOTTOM = 80.0, 20.0     # reading bands: top fifth / bottom fifth
EDGE = 5.0                   # within 5 points of a band edge, the range takes in the next band
MIN_COVER = 0.5              # score a measure only if it covers half the group's output
GOOD_COVER = 0.8
MIN_HIST_Q, MIN_HIST_M = 20, 120   # history before a reading counts in the check
WINDOW_Q, WINDOW_M = 80, 240       # "own history" = the last 20 years (capacity use drifts down over decades)
BETA_MONTHS, BETA_MIN = 60, 36
DOLLAR_SWITCH = "2006-02"
BOOT = 2000
SEED = 20261127
FDR_Q = 0.10
# Publication lags: months after the data period ends before the figure is out.
LAG = {"bea": 3, "g17": 1, "m3": 2}


# ------------------------------------------------------------------ helpers --

def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def wide(path: Path) -> dict[str, dict[str, float]]:
    """Wide file (date + one column per series) -> {series: {date: value}}."""
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for r in read_csv(path):
        d = r["date"]
        for k, v in r.items():
            if k == "date" or v in ("", ".", None):
                continue
            try:
                out[k][d] = float(v)
            except ValueError:
                pass
    return out


def add_months(ym: str, n: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    t = y * 12 + (m - 1) + n
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


def pct_rank(hist: list[float], v: float) -> float:
    lo = sum(1 for h in hist if h < v)
    eq = sum(1 for h in hist if h == v)
    return 100.0 * (lo + 0.5 * eq) / len(hist)


def band(p: float) -> int:
    return 1 if p >= TOP else (-1 if p <= BOTTOM else 0)


def solve(a: list[list[float]], b: list[float]) -> list[float] | None:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[p][c]) < 1e-12:
            return None
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                for k in range(c, n + 1):
                    m[r][k] -= f * m[c][k]
    return [m[i][n] / m[i][i] for i in range(n)]


def olsk(xs: list[list[float]], y: list[float]) -> list[float] | None:
    """OLS with intercept; returns [a, b1, ..., bk]."""
    k = len(xs[0]) + 1
    xtx = [[0.0] * k for _ in range(k)]
    xty = [0.0] * k
    for row, yy in zip(xs, y):
        v = [1.0] + row
        for i in range(k):
            xty[i] += v[i] * yy
            for j in range(k):
                xtx[i][j] += v[i] * v[j]
    return solve(xtx, xty)


def slope(x: list[float], y: list[float]) -> float:
    if len(x) < 3:
        return float("nan")
    mx, my = mean(x), mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    if sxx == 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx


def bh_pass(pvals: list[float], q: float) -> list[bool]:
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m, cut = len(pvals), -1
    for rank, i in enumerate(idx, 1):
        if pvals[i] <= q * rank / m:
            cut = rank
    ok = [False] * m
    for rank, i in enumerate(idx, 1):
        ok[i] = rank <= cut
    return ok


# --------------------------------------------------------------- crosswalk --

def load_crosswalk():
    rows = read_csv(CONFIG / "industry_crosswalk.csv")
    bea = [r for r in rows if r["source"] == "bea"]
    share = {(r["bea_code"], r["group"]): float(r["share"]) for r in bea}
    by_src = defaultdict(list)
    for r in rows:
        by_src[r["source"]].append(r)
    return bea, share, by_src


def bea_weights(nominal, bea_rows, share, quarters: list[str]) -> dict[tuple[str, str], float]:
    """Average nominal output over the given quarters x share, per (code, group)."""
    out = {}
    for r in bea_rows:
        s = nominal.get(r["bea_code"], {})
        vals = [s[q] for q in quarters if q in s]
        out[(r["bea_code"], r["group"])] = (mean(vals) if vals else 0.0) * float(r["share"])
    return out


# ---------------------------------------------------------------- measures --

def quarter_list(series: dict[str, dict[str, float]]) -> list[str]:
    return sorted({d for s in series.values() for d in s})


def bea_measures(bea_rows):
    nominal = wide(IND / "bea" / "gross_output_nominal.csv")
    real = wide(IND / "bea" / "gross_output_real.csv")
    price = wide(IND / "bea" / "gross_output_price_index.csv")
    qs = quarter_list(nominal)
    demand = {g: {} for g in GROUPS}
    coping = {g: {} for g in GROUPS}
    for i, q in enumerate(qs):
        if i < 4:
            continue
        q0 = qs[i - 4]
        allp = price.get("II", {})
        if q in allp and q0 in allp:
            all_infl = allp[q] / allp[q0] - 1
        else:
            all_infl = None
        for g in GROUPS:
            num_d = den_d = num_p = den_p = 0.0
            for r in bea_rows:
                if r["group"] != g:
                    continue
                c, sh = r["bea_code"], float(r["share"])
                w = nominal.get(c, {}).get(q0)
                if not w:
                    continue
                w *= sh
                rl = real.get(c, {})
                if q in rl and q0 in rl and rl[q0]:
                    num_d += w * (rl[q] / rl[q0] - 1)
                    den_d += w
                pr = price.get(c, {})
                if q in pr and q0 in pr and pr[q0]:
                    num_p += w * (pr[q] / pr[q0] - 1)
                    den_p += w
            if den_d:
                demand[g][q] = 100 * num_d / den_d
            if den_p and all_infl is not None:
                coping[g][q] = 100 * (num_p / den_p - all_infl)
    return nominal, qs, demand, coping


def group_total_weight(weights, g) -> float:
    return sum(w for (c, gg), w in weights.items() if gg == g)


def g17_measure(rows, weights):
    cap = wide(IND / "fed_g17" / "capacity_utilization.csv")
    out, cover, start = {}, {}, {}
    for g in GROUPS:
        mine = [r for r in rows if r["group"] == g and r["code"] in cap]
        tot = group_total_weight(weights, g)
        ws = {r["code"]: weights.get((r["bea_code"], g), 0.0) for r in mine}
        cover[g] = (sum(ws.values()) / tot) if tot else 0.0
        if not mine or not sum(ws.values()):
            continue
        common = set.intersection(*[set(cap[r["code"]]) for r in mine])
        series = {}
        for d in sorted(common):
            series[d] = sum(ws[c] * cap[c][d] for c in ws) / sum(ws.values())
        out[g] = series
        start[g] = min(series) if series else ""
    return out, cover


def m3_measure(rows, weights, ppi, share):
    m3 = wide(IND / "census" / "m3.csv")

    def ship(code):
        if code == "36S-MVP":
            a, b = m3.get("36S_VS_SA", {}), m3.get("MVP_VS_SA", {})
            return {d: a[d] - b[d] for d in a if d in b}
        return m3.get(f"{code}_VS_SA", {})

    out, cover = {}, {}
    for g in GROUPS:
        mine = [r for r in rows if r["group"] == g]
        tot = group_total_weight(weights, g)
        codes = {r["bea_code"] for r in mine}
        cover[g] = (sum(weights.get((c, g), 0.0) for c in codes) / tot) if tot else 0.0
        if not mine:
            continue
        sh = {r["code"]: ship(r["code"]) for r in mine}
        dates = sorted({d for s in sh.values() for d in s})
        series = {}
        for d in dates:
            d0 = add_months(d, -12)
            num = den = 0.0
            for r in mine:
                s, p = sh[r["code"]], ppi.get(r["deflator"], {})
                if d in s and d0 in s and s[d0] > 0 and d in p and d0 in p:
                    real_g = (s[d] / s[d0]) / (p[d] / p[d0]) - 1
                    w = s[d0] * share.get((r["bea_code"], g), 1.0)
                    num += w * real_g
                    den += w
            # count a month only when every category in the group reports
            if den and all(d in sh[r["code"]] and d0 in sh[r["code"]] for r in mine):
                series[d] = 100 * num / den
        out[g] = series
    return out, cover


def ppi_measure(rows, weights, ppi):
    per_code = defaultdict(int)
    for r in rows:
        per_code[(r["bea_code"], r["group"])] += 1
    w = {(r["code"], r["group"]): weights.get((r["bea_code"], r["group"]), 0.0) / per_code[(r["bea_code"], r["group"])]
         for r in rows}
    dates = sorted({d for r in rows for d in ppi.get(r["code"], {})})
    group_yoy = {g: {} for g in GROUPS}
    bench = {}
    for d in dates:
        d0 = add_months(d, -12)
        tot_n = tot_d = 0.0
        for g in GROUPS:
            n = den = 0.0
            for r in rows:
                if r["group"] != g:
                    continue
                s = ppi.get(r["code"], {})
                if d in s and d0 in s and s[d0]:
                    ww = w[(r["code"], g)]
                    n += ww * (s[d] / s[d0] - 1)
                    den += ww
            if den:
                group_yoy[g][d] = (n, den)
                tot_n += n
                tot_d += den
        if tot_d:
            bench[d] = tot_n / tot_d
    out, cover = {}, {}
    for g in GROUPS:
        out[g] = {d: 100 * (n / den - bench[d]) for d, (n, den) in group_yoy[g].items() if d in bench}
        tot = group_total_weight(weights, g)
        codes = {r["bea_code"] for r in rows if r["group"] == g}
        cover[g] = (sum(weights.get((c, g), 0.0) for c in codes) / tot) if tot else 0.0
    return out, cover


# ---------------------------------------------------------------- residuals --

def month_end(series: dict[str, float]) -> dict[str, float]:
    out = {}
    for d in sorted(series):
        out[d[:7]] = series[d]
    return out


def monthly_residuals():
    rets = read_csv(DATA / "french" / "industry12_monthly_vw.csv")
    ff = {r["date"]: r for r in read_csv(DATA / "french" / "ff_factors_monthly.csv")}

    def fred(sid):
        return month_end({r["date"]: float(r["value"]) for r in read_csv(DATA / "fred" / f"{sid}.csv")
                          if r["value"] not in ("", ".")})

    y2 = fred("DGS2")
    usd_old, usd_new = fred("DTWEXB"), fred("DTWEXBGS")
    months = [r["date"] for r in rets]
    x = {}
    for m in months:
        p = add_months(m, -1)
        if m not in ff or m not in y2 or p not in y2:
            continue
        src = usd_new if m >= DOLLAR_SWITCH else usd_old
        if m not in src or p not in src:
            continue
        x[m] = [float(ff[m]["mkt_rf"]), y2[m] - y2[p], 100 * (src[m] / src[p] - 1)]
    resid = {g: {} for g in GROUPS}
    ex = {g: {r["date"]: float(r[g]) - float(ff[r["date"]]["rf"]) for r in rets if r["date"] in ff} for g in GROUPS}
    xm = sorted(x)
    for i, m in enumerate(xm):
        win = [w for w in xm[max(0, i - BETA_MONTHS):i]]
        if len(win) < BETA_MIN:
            continue
        for g in GROUPS:
            ws = [w for w in win if w in ex[g]]
            if len(ws) < BETA_MIN or m not in ex[g]:
                continue
            coef = olsk([x[w] for w in ws], [ex[g][w] for w in ws])
            if coef is None:
                continue
            resid[g][m] = ex[g][m] - sum(b * v for b, v in zip(coef[1:], x[m]))
    return resid


# ------------------------------------------------------------------- checks --

def window_hist(series: dict[str, float], upto: str, quarterly: bool) -> list[float]:
    keys = [k for k in sorted(series) if k <= upto]
    return [series[k] for k in keys[-(WINDOW_Q if quarterly else WINDOW_M):]]


def expanding_bands(series: dict[str, float], min_hist: int, quarterly: bool) -> dict[str, int]:
    keys = sorted(series)
    out = {}
    win = WINDOW_Q if quarterly else WINDOW_M
    for i, k in enumerate(keys):
        hist = [series[j] for j in keys[max(0, i + 1 - win): i + 1]]
        if len(hist) < min_hist:
            continue
        out[k] = band(pct_rank(hist, series[k]))
    return out


def avg_resid(resid_g: dict[str, float], start: str, n: int) -> float | None:
    vals = [resid_g.get(add_months(start, i)) for i in range(n)]
    if any(v is None for v in vals):
        return None
    return mean(vals)


def pairs_for(series, resid_g, kind: str):
    """Pairs of (period, reading, residual) for the two checks."""
    quarterly = kind == "bea"
    bands = expanding_bands(series, MIN_HIST_Q if quarterly else MIN_HIST_M, quarterly)
    lag = LAG[kind]
    span = 3 if quarterly else 1
    same, lead = [], []
    for p, b in sorted(bands.items()):
        r0 = avg_resid(resid_g, p, span)
        if r0 is not None:
            same.append((p, b, r0))
        # figure for period p is out at the end of (last month of p) + lag
        known = add_months(p, span - 1 + lag)
        r1 = avg_resid(resid_g, add_months(known, 1), span)
        if r1 is not None:
            lead.append((p, b, r1))
    return same, lead


def boot_slope(pairs, rng, cluster: bool = False):
    if cluster:
        byk = defaultdict(list)
        for p in pairs:
            byk[p[0]].append(p)
        keys = list(byk)
    draws = []
    n = len(pairs)
    for _ in range(BOOT):
        if cluster:
            sample = [q for _k in range(len(keys)) for q in byk[keys[rng.randrange(len(keys))]]]
        else:
            sample = [pairs[rng.randrange(n)] for _ in range(n)]
        b = slope([s[1] for s in sample], [s[2] for s in sample])
        if b == b:
            draws.append(b)
    draws.sort()
    if not draws:
        return float("nan"), float("nan"), float("nan")
    lo, hi = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
    le = sum(1 for d in draws if d <= 0) / len(draws)
    ge = sum(1 for d in draws if d >= 0) / len(draws)
    return lo, hi, min(1.0, 2 * min(le, ge))


def check(pairs, rng, cluster=False):
    if len(pairs) < 12 or len({p[1] for p in pairs}) < 2:
        return None
    b = slope([p[1] for p in pairs], [p[2] for p in pairs])
    lo, hi, pv = boot_slope(pairs, rng, cluster)
    keys = sorted({p[0] for p in pairs})
    mid = keys[len(keys) // 2]
    h1 = [p for p in pairs if p[0] < mid]
    h2 = [p for p in pairs if p[0] >= mid]
    b1 = slope([p[1] for p in h1], [p[2] for p in h1])
    b2 = slope([p[1] for p in h2], [p[2] for p in h2])
    flip = (b1 == b1 and b2 == b2 and b1 * b2 < 0)
    return {
        "n": len(pairs), "first": keys[0], "last": keys[-1],
        "n_tailwind": sum(1 for p in pairs if p[1] == 1),
        "n_headwind": sum(1 for p in pairs if p[1] == -1),
        "slope": b, "lo": lo, "hi": hi, "p": pv,
        "half1": b1, "half2": b2, "sign_flip": "yes" if flip else "no",
    }


# ------------------------------------------------------------ concentration --

NAICS_GROUP = [  # longest prefix wins; follows the crosswalk's SIC basis
    ("3254", "Hlth"), ("3391", "Hlth"), ("3352", "Durbl"), ("3371", "Durbl"),
    ("3361", "Durbl"), ("3362", "Durbl"), ("3363", "Durbl"), ("2121", "Enrgy"),
    ("5112", "BusEq"), ("5132", "BusEq"), ("5111", "NoDur"), ("5131", "NoDur"),
    ("5415", "BusEq"), ("311", "NoDur"), ("312", "NoDur"), ("313", "NoDur"),
    ("314", "NoDur"), ("315", "NoDur"), ("316", "NoDur"), ("325", "Chems"),
    ("334", "BusEq"), ("518", "BusEq"), ("519", "BusEq"), ("515", "Telcm"),
    ("516", "Telcm"), ("517", "Telcm"), ("211", "Enrgy"), ("213", "Enrgy"),
    ("324", "Enrgy"), ("22", "Utils"), ("42", "Shops"), ("44", "Shops"),
    ("45", "Shops"), ("722", "Shops"), ("811", "Shops"), ("812", "Shops"),
    ("621", "Hlth"), ("622", "Hlth"), ("623", "Hlth"), ("52", "Money"),
    ("531", "Money"), ("31", "Manuf"), ("32", "Manuf"), ("33", "Manuf"),
]


def naics_group(code: str) -> str:
    best = ("", "Other")
    for p, g in NAICS_GROUP:
        if code.startswith(p) and len(p) > len(best[0]):
            best = (p, g)
    g = best[1]
    if g == "Manuf" and code[:3] == "321":
        return "Other"
    return g


def concentration():
    out = {}
    for year in ("2017", "2022"):
        rows = [r for r in read_csv(IND / "census" / f"concentration_{year}.csv") if r["type_of_operation"] == "00"]
        rev = {r["naics"]: float(r["revenue_thousands"]) for r in rows
               if r["firm_group"] == "001" and r["revenue_thousands"]}
        top4 = {r["naics"]: float(r["share_of_revenue_pct"]) for r in rows
                if r["firm_group"] == "604" and r["share_of_revenue_pct"]}
        codes = [c for c in top4 if c in rev and c.isdigit()]
        leaves = [c for c in codes if not any(o != c and o.startswith(c) for o in codes)]
        agg = defaultdict(lambda: [0.0, 0.0])
        for c in leaves:
            g = naics_group(c)
            agg[g][0] += rev[c] * top4[c]
            agg[g][1] += rev[c]
        out[year] = {g: (v[0] / v[1], v[1]) for g, v in agg.items() if v[1]}
    rows = []
    for g in GROUPS:
        a, b = out["2017"].get(g), out["2022"].get(g)
        rows.append({
            "group": g, "name": GROUP_NAMES[g],
            "top4_share_2017": f"{a[0]:.1f}" if a else "",
            "top4_share_2022": f"{b[0]:.1f}" if b else "",
            "change_pts": f"{b[0] - a[0]:+.1f}" if a and b else "",
            "revenue_2022_bn": f"{b[1] / 1e6:.0f}" if b else "",
        })
    return rows


# ------------------------------------------------------------------- scores --

def confidence(chk, cover, fit, cap_low=False):
    """High / Medium / Low from the same-period check, coverage and mapping fit."""
    if chk is None:
        return "Low", "no check (too little history)"
    b, lo, hi = chk["slope"], chk["lo"], chk["hi"]
    flip = chk["sign_flip"] == "yes"
    if b > 0 and lo > 0 and chk.get("fdr_pass") == "yes":
        ev = "backs"
    elif b > 0 and lo > 0:
        ev = "backs, not past the false-discovery check"
    elif b > 0 and not flip:
        ev = "leans"
    elif b > 0:
        ev = "weak (halves disagree)"
    elif hi < 0:
        ev = "against"
    else:
        ev = "doesn't back"
    good_map = cover >= GOOD_COVER and fit == "good"
    if ev == "backs" and not flip and good_map:
        conf = "High"
    elif ev.startswith("backs") or (ev == "leans" and cover >= GOOD_COVER and fit != "loose"):
        conf = "Medium"
    else:
        conf = "Low"
    if fit == "loose" and conf == "High":
        conf = "Medium"
    if cap_low:
        conf = "Low"
    return conf, ev


def score_range(readings: set[int], exposure: int, conf: str) -> tuple[int, int]:
    if conf == "High":
        exps = {exposure}
    elif conf == "Medium":
        exps = {max(0, exposure - 1), exposure}
    else:
        exps = {0, exposure}
    vals = [r * e for r in readings for e in exps]
    return min(vals), max(vals)


def readings_set(p: float, cross_p: float | None) -> set[int]:
    s = {band(p)}
    if TOP - EDGE <= p < TOP:
        s.add(1)
    if TOP <= p < TOP + EDGE:
        s.add(0)
    if BOTTOM < p <= BOTTOM + EDGE:
        s.add(-1)
    if BOTTOM - EDGE < p <= BOTTOM:
        s.add(0)
    if cross_p is not None:
        s.add(band(cross_p))
    return s


def fmt(v, d=2, plus=True):
    if v is None or v != v:
        return ""
    return f"{v:+.{d}f}" if plus else f"{v:.{d}f}"


def qlabel(d: str) -> str:
    return f"{d[:4]} Q{(int(d[5:7]) - 1) // 3 + 1}"


# --------------------------------------------------------------------- main --

def main() -> None:
    rng = random.Random(SEED)
    bea_rows, share, by_src = load_crosswalk()
    nominal, qs, demand, coping = bea_measures(bea_rows)
    latest_q = [q for q in qs if any(q in nominal.get(r["bea_code"], {}) for r in bea_rows)][-4:]
    weights = bea_weights(nominal, bea_rows, share, latest_q)
    ppi = wide(IND / "bls" / "ppi_industry.csv")
    cap, cap_cover = g17_measure(by_src["g17"], weights)
    m3, m3_cover = m3_measure(by_src["m3"], weights, ppi, share)
    pp, pp_cover = ppi_measure(by_src["ppi"], weights, ppi)
    resid = monthly_residuals()

    measures = {}  # (group, key) -> (series, kind, factor, cover, label, unit)
    for g in GROUPS:
        measures[(g, "demand")] = (demand[g], "bea", "demand", 1.0, "Real gross output, growth over a year (BEA)", "%")
        measures[(g, "coping")] = (coping[g], "bea", "coping", 1.0, "Output prices vs all industries, growth over a year (BEA)", "pts")
        if g in cap:
            measures[(g, "capacity")] = (cap[g], "g17", "capacity", cap_cover[g], "Capacity use (Fed G.17)", "%")
        if m3.get(g):
            measures[(g, "demand_m3")] = (m3[g], "m3", "demand", m3_cover[g], "Real factory shipments, growth over a year (Census M3 / BLS)", "%")
        if pp.get(g):
            measures[(g, "coping_ppi")] = (pp[g], "ppi", "coping", pp_cover[g], "Producer prices vs all mapped industries, growth over a year (BLS)", "pts")

    # latest readings
    latest_rows, series_rows = [], []
    latest = {}
    for (g, key), (s, kind, factor, cover, label, unit) in measures.items():
        if not s:
            continue
        keys = sorted(s)
        last = keys[-1]
        hist = window_hist(s, last, kind == "bea")
        p = pct_rank(hist, s[last])
        latest[(g, key)] = (last, s[last], p, cover)
        latest_rows.append({
            "group": g, "name": GROUP_NAMES[g], "factor": FACTOR_NAMES[factor], "measure": key,
            "description": label, "latest_period": qlabel(last) if kind == "bea" else last,
            "value": fmt(s[last], 2), "unit": unit,
            "percentile_vs_own_history": f"{p:.0f}", "reading": band(p),
            "history_from": qlabel(keys[-len(hist)]) if kind == "bea" else keys[-len(hist)],
            "coverage_of_group_output": f"{cover:.0%}",
            "scored": "yes" if cover >= MIN_COVER and key in ("demand", "coping", "capacity") else
                      ("cross-check" if cover >= GOOD_COVER else
                       ("shown only (cross-check covers under 80%)" if cover >= MIN_COVER else "no (coverage under half)")),
        })
        for k in keys:
            series_rows.append({"group": g, "measure": key, "period": k, "value": f"{s[k]:.3f}"})

    # measured checks
    checks = []
    for (g, key), (s, kind, factor, cover, label, unit) in measures.items():
        if kind == "ppi" or not s or cover < MIN_COVER:
            continue
        same, lead = pairs_for(s, resid[g], kind)
        for test, prs in (("moves_with", same), ("leads", lead)):
            c = check(prs, rng)
            if c:
                c.update({"group": g, "measure": key, "factor": factor, "test": test})
                checks.append(c)
    for test in ("moves_with", "leads"):
        sub = [c for c in checks if c["test"] == test]
        for c, ok in zip(sub, bh_pass([c["p"] for c in sub], FDR_Q)):
            c["fdr_pass"] = "yes" if ok else "no"

    # pooled checks (all groups together, months resampled as clusters)
    pooled = []
    for key in ("demand", "capacity", "coping", "demand_m3"):
        for ti, test in enumerate(("moves_with", "leads")):
            prs, used = [], 0
            for g in GROUPS:
                if (g, key) not in measures:
                    continue
                s, kind, factor, cover, *_ = measures[(g, key)]
                if cover < MIN_COVER or not s:
                    continue
                prs.extend((p, b, r) for p, b, r in pairs_for(s, resid[g], kind)[ti])
                used += 1
            c = check(prs, rng, cluster=True)
            if c:
                c.update({"measure": key, "test": test, "groups": used})
                pooled.append(c)

    chk = {(c["group"], c["measure"], c["test"]): c for c in checks}

    # scores
    expo = {(r["group"], r["factor"]): r for r in read_csv(CONFIG / "industry_exposure_v0.csv")}
    score_rows = []
    for g in GROUPS:
        for f in FACTORS:
            e = expo[(g, f)]
            exposure = int(e["exposure"])
            channels = ", ".join(f"{c} {e[c]}" for c in ("revenue", "costs", "financing", "currency", "valuation", "position") if e[c] != "0")
            base = {"group": g, "name": GROUP_NAMES[g], "factor": FACTOR_NAMES[f],
                    "exposure": exposure, "channels": channels}
            key = f
            if f in NOT_PULLED or (g, key) not in latest or latest[(g, key)][3] < MIN_COVER:
                why = NOT_PULLED.get(f) or (
                    "no capacity series for this group" if (g, key) not in latest
                    else f"capacity series cover only {latest[(g, key)][3]:.0%} of the group's output")
                score_rows.append({**base, "status": "not scored", "reading": "", "percentile": "",
                                   "latest_period": "", "score": "", "score_low": "", "score_high": "",
                                   "confidence": "", "evidence": "", "cross_check": "", "note": why})
                continue
            last, val, p, cover = latest[(g, key)]
            cross_key = {"demand": "demand_m3", "coping": "coping_ppi"}.get(f)
            cross_p = None
            cross_txt = ""
            if cross_key and (g, cross_key) in latest and latest[(g, cross_key)][3] >= GOOD_COVER:
                cl, cv, cp, _ = latest[(g, cross_key)]
                cross_p = cp
                cross_txt = f"{cross_key} {cl}: {cv:+.1f}, percentile {cp:.0f}"
            c = chk.get((g, key, "moves_with"))
            fit = FIT[(g, f)]
            conf, ev = confidence(c, cover, fit, cap_low=(g == "Enrgy" and f == "coping"))
            r = band(p)
            lo, hi = score_range(readings_set(p, cross_p), exposure, conf)
            lead = chk.get((g, key, "leads"))
            notes = []
            if g == "Enrgy" and f == "coping":
                notes.append("energy's output prices are the oil shock itself, which belongs in macro")
            if fit != "good":
                notes.append(f"mapping fit {fit}")
            if lead and lead["slope"] < 0:
                notes.append("the published reading has gone the other way in the next period")
            score_rows.append({
                **base, "status": "scored", "reading": r, "percentile": f"{p:.0f}",
                "latest_period": qlabel(last) if len(last) == 7 and key != "capacity" else last,
                "score": r * exposure, "score_low": lo, "score_high": hi,
                "confidence": conf, "evidence": ev, "cross_check": cross_txt,
                "note": "; ".join(notes),
            })

    conc = concentration()

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "readings.csv", latest_rows)
    write_csv(OUT / "measure_series.csv", series_rows)
    write_csv(OUT / "checks.csv", [{
        "group": c["group"], "measure": c["measure"], "test": c["test"], "first": c["first"], "last": c["last"],
        "n": c["n"], "n_tailwind": c["n_tailwind"], "n_headwind": c["n_headwind"],
        "slope_pct_per_month": fmt(c["slope"], 3), "range_lo": fmt(c["lo"], 3), "range_hi": fmt(c["hi"], 3),
        "p": f"{c['p']:.3f}", "fdr_pass": c["fdr_pass"], "half1": fmt(c["half1"], 3), "half2": fmt(c["half2"], 3),
        "sign_flip": c["sign_flip"]} for c in checks])
    write_csv(OUT / "pooled_checks.csv", [{
        "measure": c["measure"], "test": c["test"], "groups": c["groups"], "first": c["first"], "last": c["last"],
        "n": c["n"], "n_tailwind": c["n_tailwind"], "n_headwind": c["n_headwind"],
        "slope_pct_per_month": fmt(c["slope"], 3), "range_lo": fmt(c["lo"], 3), "range_hi": fmt(c["hi"], 3),
        "p": f"{c['p']:.3f}", "half1": fmt(c["half1"], 3), "half2": fmt(c["half2"], 3),
        "sign_flip": c["sign_flip"]} for c in pooled])
    write_csv(OUT / "scores.csv", score_rows)
    write_csv(OUT / "concentration.csv", conc)
    write_results_md(latest_rows, checks, pooled, score_rows, conc)
    print(f"wrote {OUT}")


def write_results_md(latest_rows, checks, pooled, score_rows, conc) -> None:
    L = ["# Industry run results", "",
         "Generated by `scripts/industry_assessment.py`. Write-up: `docs/industry-run.md`.", "",
         "Reading: +1 tailwind (top fifth of the group's own history), 0 neutral, −1 headwind (bottom fifth). "
         "Score = reading × exposure (0 to 3, v0 judgment), on the −3 to +3 scale; the range widens for readings near a "
         "band edge, a cross-check in another band, and lower confidence.", "",
         "## Scores", "",
         "| Group | Factor | Reading (percentile) | Exposure | Score | Range | Confidence | Check |",
         "|---|---|---|---|---|---|---|---|"]
    for r in score_rows:
        if r["status"] != "scored":
            continue
        L.append(f"| {r['name']} | {r['factor']} | {r['reading']:+d} ({r['percentile']}) | {r['exposure']} | "
                 f"{r['score']:+d} | {r['score_low']:+d} to {r['score_high']:+d} | {r['confidence']} | {r['evidence']} |")
    L += ["", "Not scored: competition, regulation and technology for every group (data not pulled or paid); "
          "capacity where G.17 covers under half the group's output (telecom, retail, healthcare, finance, other).", "",
          "## Latest readings", "",
          "| Group | Measure | Period | Value | Percentile | Coverage | Used as |", "|---|---|---|---|---|---|---|"]
    for r in latest_rows:
        L.append(f"| {r['name']} | {r['measure']} | {r['latest_period']} | {r['value']} {r['unit']} | "
                 f"{r['percentile_vs_own_history']} | {r['coverage_of_group_output']} | {r['scored']} |")
    L += ["", "## Measured check, by group", "",
          "Slope = the group's monthly return beyond the market, 2-year yield and dollar (percent a month) per band "
          "step of the reading. 95% bootstrap range. False-discovery check: Benjamini-Hochberg at 10% within each test.", "",
          "| Group | Measure | Test | Months or quarters | Tailwind / headwind | Slope | Range | FDR | Halves | Flip |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for c in checks:
        L.append(f"| {GROUP_NAMES[c['group']]} | {c['measure']} | {c['test']} | {c['n']} ({c['first']} to {c['last']}) | "
                 f"{c['n_tailwind']} / {c['n_headwind']} | {fmt(c['slope'], 3)} | {fmt(c['lo'], 3)} to {fmt(c['hi'], 3)} | "
                 f"{c['fdr_pass']} | {fmt(c['half1'], 3)}, {fmt(c['half2'], 3)} | {c['sign_flip']} |")
    L += ["", "## Measured check, all groups pooled", "",
          "| Measure | Test | Groups | Observations | Slope | Range | p | Halves | Flip |", "|---|---|---|---|---|---|---|---|---|"]
    for c in pooled:
        L.append(f"| {c['measure']} | {c['test']} | {c['groups']} | {c['n']} | {fmt(c['slope'], 3)} | "
                 f"{fmt(c['lo'], 3)} to {fmt(c['hi'], 3)} | {c['p']:.3f} | {fmt(c['half1'], 3)}, {fmt(c['half2'], 3)} | {c['sign_flip']} |")
    L += ["", "## Competition context (not scored)", "",
          "Revenue-weighted share of the four largest firms across the most detailed Census industries mapped to each group.", "",
          "| Group | Top 4 share 2017 | 2022 | Change | Revenue 2022 ($bn) |", "|---|---|---|---|---|"]
    for r in conc:
        L.append(f"| {r['name']} | {r['top4_share_2017']} | {r['top4_share_2022']} | {r['change_pts']} | {r['revenue_2022_bn']} |")
    (OUT / "RESULTS.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
