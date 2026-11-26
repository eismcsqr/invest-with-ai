"""Rates test on broad sectors: how each sector moves against the market when
the 2-year Treasury yield moves on Fed decision days, compared with the
Macro Exposure Scorecard v0's rates scores.

Inputs (all already in the repo, refreshed by the macro data pull):
  data/fred/DGS2.csv                    2-year Treasury yield, daily
  data/french/industry12_daily_vw.csv   Ken French 12 industries, value-weighted, % returns
  data/french/industry12_daily_ew.csv   same, equal-weighted (robustness check)
  data/french/ff_factors_daily.csv      market return = mkt_rf + rf
  config/v0_rates_scores.csv            v0 scorecard rates scores and the mapping to French groups

Fed decision days come from data/events/fomc_decisions.csv (rows with
in_rates_test = yes) once the event calendar is merged. Until then the test
falls back to config/fomc_dates_provisional.csv, a hand-entered list of
scheduled decision days plus unscheduled rate changes, and says so in every
output.

What it measures, per sector:
  sensitivity = slope of (sector return - market return) on the 2-year yield
  change, in percentage points of relative return per +10 basis points.
  Ranges are 95% bootstrap ranges over events. It also reports the slope by
  period, out of sample, for rate news and growth news separately, beta
  adjusted, equal-weighted, and the raw (not market-relative) slope.

Writes results/rates_test/ (CSV tables and RESULTS.md). Standard library only.
Run: python scripts/rates_test.py
"""

from __future__ import annotations

import bisect
import csv
import datetime as dt
import random
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config"
OUT = ROOT / "results" / "rates_test"

CALENDAR = DATA / "events" / "fomc_decisions.csv"
PROVISIONAL = CONFIG / "fomc_dates_provisional.csv"
V0 = CONFIG / "v0_rates_scores.csv"

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
PERIODS = [("1994-2007", "1994-01-01", "2007-12-31"),
           ("2008-2015", "2008-01-01", "2015-12-31"),
           ("2016 on", "2016-01-01", "2099-12-31")]
PER_BP = 10.0          # report slopes per +10 bp move in the 2-year yield
BOOT = 2000            # bootstrap draws
SEED = 20261126
MIN_MOVE_BP = 1.0      # smaller moves count as "flat" for the sign checks
BETA_DAYS = 250        # trading days used to estimate each sector's beta
BETA_GAP = 5           # beta window ends this many trading days before the event


# ------------------------------------------------------------------ loading --

def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def load_events() -> tuple[list[tuple[str, str]], str]:
    if CALENDAR.exists():
        rows = [r for r in read_csv(CALENDAR) if r.get("in_rates_test", "").lower() in ("yes", "true", "1")]
        return sorted((r["date"], r["type"]) for r in rows), "event calendar (data/events/fomc_decisions.csv)"
    rows = read_csv(PROVISIONAL)
    return sorted((r["date"], r["type"]) for r in rows), "PROVISIONAL hand-entered list (config/fomc_dates_provisional.csv)"


def load_returns(path: Path) -> dict[str, dict[str, float]]:
    out = {}
    for r in read_csv(path):
        out[r["date"]] = {s: float(r[s]) for s in SECTORS}
    return out


def load_market() -> dict[str, float]:
    return {r["date"]: float(r["mkt_rf"]) + float(r["rf"]) for r in read_csv(DATA / "french" / "ff_factors_daily.csv")
            if r["mkt_rf"] and r["rf"]}


def load_dgs2() -> dict[str, float]:
    return {r["date"]: float(r["value"]) for r in read_csv(DATA / "fred" / "DGS2.csv") if r["value"]}


# -------------------------------------------------------------------- stats --

def ols(x: list[float], y: list[float]) -> tuple[float, float]:
    """Slope and intercept of y on x."""
    mx, my = mean(x), mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    if sxx == 0:
        return float("nan"), my
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    return b, my - b * mx


def slope(x, y) -> float:
    return ols(x, y)[0]


def boot_range(x: list[float], y: list[float], rng: random.Random) -> tuple[float, float]:
    n, draws = len(x), []
    for _ in range(BOOT):
        idx = [rng.randrange(n) for _ in range(n)]
        b = slope([x[i] for i in idx], [y[i] for i in idx])
        if b == b:
            draws.append(b)
    draws.sort()
    return draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]


def ranks(v: list[float]) -> list[float]:
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


def corr(a: list[float], b: list[float]) -> float:
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else float("nan")


def spearman(a, b) -> float:
    return corr(ranks(a), ranks(b))


# ------------------------------------------------------------------- events --

def build_event_rows(events, dgs2, vw, ew, mkt) -> tuple[list[dict], list[str]]:
    bond_days = sorted(dgs2)
    stock_days = sorted(set(vw) & set(mkt))
    notes, rows, seen = [], [], set()
    for date, typ in events:
        i = bisect.bisect_left(bond_days, date)
        if i == 0 or i >= len(bond_days):
            continue
        td, prev = bond_days[i], bond_days[i - 1]
        if td not in vw or td not in mkt:
            continue  # outside the French data's range
        if td != date:
            notes.append(f"{date} ({typ}) is not a bond trading day; used {td}.")
        if td in seen:
            notes.append(f"{date} falls on the same trading day as an earlier event; counted once.")
            continue
        seen.add(td)
        dy = round((dgs2[td] - dgs2[prev]) * 100, 2)
        m = mkt[td]
        k = bisect.bisect_left(stock_days, td)
        win = stock_days[max(0, k - BETA_GAP - BETA_DAYS):max(0, k - BETA_GAP)]
        row = {"date": date, "type": typ, "trading_day": td, "dgs2_chg_bp": dy, "mkt_ret_pct": round(m, 3)}
        if dy >= MIN_MOVE_BP:
            row["news"] = "rate news" if m < 0 else "growth news"
        elif dy <= -MIN_MOVE_BP:
            row["news"] = "rate news" if m > 0 else "growth news"
        else:
            row["news"] = "flat"
        for s in SECTORS:
            row[f"{s}_raw"] = vw[td][s]
            row[f"{s}_xs"] = round(vw[td][s] - m, 3)
            row[f"{s}_xs_ew"] = round(ew[td][s] - m, 3) if td in ew else None
            if len(win) >= BETA_DAYS // 2:
                beta, alpha = ols([mkt[d] for d in win], [vw[d][s] for d in win])
                row[f"{s}_beta"] = round(beta, 3)
                row[f"{s}_xs_beta"] = round(vw[td][s] - alpha - beta * m, 3)
            else:
                row[f"{s}_beta"] = row[f"{s}_xs_beta"] = None
        rows.append(row)
    return rows, notes


# ------------------------------------------------------------------ analysis --

def xy(rows, col, pred=lambda r: True):
    pts = [(r["dgs2_chg_bp"] / PER_BP, r[col]) for r in rows if pred(r) and r[col] is not None]
    return [p[0] for p in pts], [p[1] for p in pts]


def in_crisis(day: str) -> bool:
    """2008-2009 financial crisis and the March 2020 emergency cuts."""
    return day[:4] in ("2008", "2009") or day.startswith("2020-03")


def confidence(full_lo, full_hi, period_slopes, oos_same_sign) -> str:
    sig = full_lo > 0 or full_hi < 0
    sign = 1 if full_lo + full_hi > 0 else -1
    periods_agree = all((b == b) and (b * sign > 0) for b in period_slopes)
    score = sum([sig, periods_agree, oos_same_sign])
    return {3: "High", 2: "Medium"}.get(score, "Low")


def analyse(rows, rng):
    n = len(rows)
    half = rows[: n // 2], rows[n // 2:]
    split_date = half[1][0]["trading_day"]
    sens = []
    for s in SECTORS:
        x, y = xy(rows, f"{s}_xs")
        b = slope(x, y)
        lo, hi = boot_range(x, y, rng)
        rec = {"sector": s, "name": SECTOR_NAMES[s], "events": len(x),
               "xs_slope": b, "xs_lo": lo, "xs_hi": hi}
        rec["raw_slope"] = slope(*xy(rows, f"{s}_raw"))
        rec["raw_lo"], rec["raw_hi"] = boot_range(*xy(rows, f"{s}_raw"), rng)
        rec["beta_adj_slope"] = slope(*xy(rows, f"{s}_xs_beta"))
        rec["ew_slope"] = slope(*xy(rows, f"{s}_xs_ew"))
        for label, a, z in PERIODS:
            px, py = xy(rows, f"{s}_xs", lambda r, a=a, z=z: a <= r["trading_day"] <= z)
            rec[f"p:{label}"] = slope(px, py) if len(px) >= 10 else float("nan")
            rec[f"n:{label}"] = len(px)
        rec["ex_crisis_slope"] = slope(*xy(rows, f"{s}_xs", lambda r: not in_crisis(r["trading_day"])))
        for news in ("rate news", "growth news"):
            # Beta-adjusted, because the split itself depends on the market's move.
            nx, ny = xy(rows, f"{s}_xs_beta", lambda r, news=news: r["news"] == news)
            rec[f"news:{news}"] = slope(nx, ny) if len(nx) >= 10 else float("nan")
            rec[f"nn:{news}"] = len(nx)
        rec["train_slope"] = slope(*xy(half[0], f"{s}_xs"))
        rec["test_slope"] = slope(*xy(half[1], f"{s}_xs"))
        # Out of sample: predict the second half's relative moves from the first half's slope.
        hits = tot = 0
        for r in half[1]:
            if abs(r["dgs2_chg_bp"]) >= MIN_MOVE_BP and r[f"{s}_xs"] != 0:
                pred = rec["train_slope"] * r["dgs2_chg_bp"] / PER_BP
                tot += 1
                hits += (pred > 0) == (r[f"{s}_xs"] > 0)
        rec["oos_hit_rate"] = hits / tot if tot else float("nan")
        rec["oos_events"] = tot
        oos_same = rec["train_slope"] * rec["test_slope"] > 0
        rec["confidence"] = confidence(lo, hi, [rec[f"p:{p[0]}"] for p in PERIODS], oos_same)
        sens.append(rec)
    mx, my = xy(rows, "mkt_ret_pct")
    oos = {
        "market_slope": slope(mx, my),
        "market_range": boot_range(mx, my, rng),
        "split": split_date,
        "spearman": spearman([r["train_slope"] for r in sens], [r["test_slope"] for r in sens]),
    }
    return sens, oos


def compare_v0(sens):
    by = {r["sector"]: r for r in sens}
    v0 = read_csv(V0)
    groups: dict[str, list[dict]] = {}
    for r in v0:
        groups.setdefault(r["french_group"], []).append(r)
    out = []
    for g, items in groups.items():
        score = mean(float(i["rates_net"]) for i in items)
        rec = by[g]
        # Direction: a negative v0 score says the group falls when rates come in higher.
        if rec["raw_hi"] < 0:
            direction = "agrees" if score < 0 else "disagrees"
        elif rec["raw_lo"] > 0:
            direction = "disagrees" if score < 0 else "agrees"
        else:
            direction = "unclear"
        # Relative to the market: v0 -3 or below means hurt more than a typical stock;
        # above -3 means hurt no more than a typical stock.
        expect_worse = score <= -3
        if rec["xs_hi"] < 0:
            relative = "agrees" if expect_worse else "disagrees"
        elif rec["xs_lo"] > 0:
            relative = "disagrees" if expect_worse else "agrees"
        else:
            relative = "unclear" if expect_worse else "agrees (no worse than market)"
        out.append({
            "french_group": g, "name": SECTOR_NAMES[g],
            "v0_types": "; ".join(f"{i['company_type']} ({int(float(i['rates_net'])):+d})" for i in items),
            "v0_avg": score, "mapping": items[0]["mapping_fit"],
            "xs_slope": rec["xs_slope"], "xs_lo": rec["xs_lo"], "xs_hi": rec["xs_hi"],
            "raw_slope": rec["raw_slope"], "raw_lo": rec["raw_lo"], "raw_hi": rec["raw_hi"],
            "direction": direction, "relative": relative, "confidence": rec["confidence"],
        })
    out.sort(key=lambda r: r["v0_avg"])
    rho = spearman([r["v0_avg"] for r in out], [r["xs_slope"] for r in out]) if len(out) >= 3 else float("nan")
    return out, rho


# ------------------------------------------------------------------- output --

def f2(v, plus=True) -> str:
    if v is None or v != v:
        return "n/a"
    return f"{v:+.2f}" if plus else f"{v:.2f}"


def write_table(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = list(rows[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})


def write_report(rows, notes, source, sens, oos, comp, rho, provisional):
    moves = [abs(r["dgs2_chg_bp"]) for r in rows]
    big = sum(m >= 5 for m in moves)
    lines = [
        "# Rates test on broad sectors",
        "",
        f"Run date: {dt.date.today().isoformat()}",
        "",
    ]
    if provisional:
        lines += ["> **Provisional Fed dates.** This run uses a hand-entered list of Fed decision days, "
                  "not the event calendar. Rerun once `data/events/fomc_decisions.csv` is merged; "
                  "the script switches to it automatically.", ""]
    lines += [
        f"**Events:** {len(rows)} Fed decision days from {rows[0]['trading_day']} to {rows[-1]['trading_day']} "
        f"({source}). Median 2-year yield move {median(moves):.1f} bp; {big} days moved 5 bp or more.",
        "",
        "**Measure:** sector return minus market return on the decision day, regressed on the change in the "
        f"2-year Treasury yield that day. Numbers are percentage points of relative return per +{PER_BP:.0f} bp. "
        "A negative number means the sector does worse than the market when rates come in higher than expected "
        "(and better when they come in lower). Ranges are 95% bootstrap ranges over events. Value-weighted "
        "Ken French 12 industries.",
        "",
        f"The market itself moves {f2(oos['market_slope'])}% per +{PER_BP:.0f} bp on these days "
        f"(95% range {f2(oos['market_range'][0])} to {f2(oos['market_range'][1])}).",
        "",
        "## Sensitivity by sector",
        "",
        "| Sector | Relative to market | 95% range | " + " | ".join(p[0] for p in PERIODS) +
        " | Without crisis days | Beta-adjusted | Equal-weighted | Rate news | Growth news | Confidence |",
        "|---|---|---|" + "---|" * len(PERIODS) + "---|---|---|---|---|---|",
    ]
    for r in sorted(sens, key=lambda r: r["xs_slope"]):
        lines.append(
            f"| {r['name']} | {f2(r['xs_slope'])} | {f2(r['xs_lo'])} to {f2(r['xs_hi'])} | "
            + " | ".join(f2(r[f"p:{p[0]}"]) for p in PERIODS)
            + f" | {f2(r['ex_crisis_slope'])} | {f2(r['beta_adj_slope'])} | {f2(r['ew_slope'])} | "
              f"{f2(r['news:rate news'])} | {f2(r['news:growth news'])} | {r['confidence']} |")
    n_rate = sum(r["news"] == "rate news" for r in rows)
    n_growth = sum(r["news"] == "growth news" for r in rows)
    lines += [
        "",
        f"Periods hold {', '.join(str(sens[0][f'n:{p[0]}']) + ' (' + p[0] + ')' for p in PERIODS)} events. "
        f"Rate news = yield and stocks moved in opposite directions ({n_rate} days); growth news = same direction "
        f"({n_growth} days); the rest moved under {MIN_MOVE_BP:.0f} bp. Both news columns are beta-adjusted, because "
        "the split uses the market's own move; treat them as a rough cut. Crisis days = 2008-2009 and March 2020. "
        "Beta-adjusted = sector return minus its expected move given the market and its beta over the prior year.",
        "",
        "Confidence: High when the full-sample range excludes zero, the sign holds in all three periods and "
        "the out-of-sample half has the same sign; Medium for two of the three; Low otherwise.",
        "",
        "## Out of sample",
        "",
        f"Slopes fitted on events before {oos['split']} and checked on events from {oos['split']} on. "
        f"Rank agreement of sector slopes between the halves (Spearman): {f2(oos['spearman'], False)}.",
        "",
        "| Sector | First half | Second half | Second-half direction hit rate |",
        "|---|---|---|---|",
    ]
    for r in sorted(sens, key=lambda r: r["xs_slope"]):
        lines.append(f"| {r['name']} | {f2(r['train_slope'])} | {f2(r['test_slope'])} | "
                     f"{r['oos_hit_rate']:.0%} of {r['oos_events']} |")
    lines += [
        "",
        "Hit rate = share of second-half events where the first-half slope got the sign of the sector's "
        "relative move right. 50% is a coin flip; most days other news moves sectors more than rates do.",
        "",
        "## Compared with the v0 scorecard",
        "",
        "The v0 scorecard covers consumer company types only, so four of the twelve groups can be compared. "
        "v0 score = net rates exposure if rates come in higher than expected (−5 to +5), averaged over the "
        "company types mapped to the group.",
        "",
        "| Group | v0 company types (rates score) | v0 avg | Mapping | Raw slope (range) | Direction | "
        "Relative slope (range) | Relative to market | Confidence |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for c in comp:
        lines.append(
            f"| {c['name']} | {c['v0_types']} | {c['v0_avg']:+.1f} | {c['mapping']} | "
            f"{f2(c['raw_slope'])} ({f2(c['raw_lo'])} to {f2(c['raw_hi'])}) | {c['direction']} | "
            f"{f2(c['xs_slope'])} ({f2(c['xs_lo'])} to {f2(c['xs_hi'])}) | {c['relative']} | {c['confidence']} |")
    lines += [
        "",
        f"Rank agreement between v0 averages and measured relative slopes across these groups (Spearman, "
        f"{len(comp)} groups): {f2(rho, False)}.",
        "",
        "Direction: does the group's own return fall when the 2-year yield rises, as v0's negative scores say? "
        "Relative: v0 −3 or below is read as \"hurt more than a typical stock\", above −3 as \"hurt no more "
        "than a typical stock\"; checked against the relative slope's range.",
    ]
    if notes:
        lines += ["", "## Data notes", ""] + [f"- {n}" for n in notes]
    (OUT / "RESULTS.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    events, source = load_events()
    provisional = source.startswith("PROVISIONAL")
    dgs2 = load_dgs2()
    vw = load_returns(DATA / "french" / "industry12_daily_vw.csv")
    ew = load_returns(DATA / "french" / "industry12_daily_ew.csv")
    mkt = load_market()
    rows, notes = build_event_rows(events, dgs2, vw, ew, mkt)
    rng = random.Random(SEED)
    sens, oos = analyse(rows, rng)
    comp, rho = compare_v0(sens)
    OUT.mkdir(parents=True, exist_ok=True)
    write_table(OUT / "events.csv", rows)
    write_table(OUT / "sensitivity.csv", sens)
    write_table(OUT / "v0_comparison.csv", comp)
    write_report(rows, notes, source, sens, oos, comp, rho, provisional)
    print(f"{len(rows)} events from {source}")
    for r in sorted(sens, key=lambda r: r["xs_slope"]):
        print(f"{r['sector']:6s} {r['xs_slope']:+.3f} [{r['xs_lo']:+.3f}, {r['xs_hi']:+.3f}] raw {r['raw_slope']:+.3f} {r['confidence']}")
    print(f"OOS spearman {oos['spearman']:.2f}; v0 rank rho {rho:.2f}")


if __name__ == "__main__":
    main()
