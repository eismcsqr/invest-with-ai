"""Company pillar: the measured check (docs/company-method.md section 9).

Do company factor readings tell us anything about how a stock does next,
compared with its own industry peers?

Every quarter end from 2001 on, the whole weekly calculation in
scripts/company_measures.py runs as if it were that day (only filings dated
and prices on or before it), on every company listed then, including ones
that later left the market. Each company's return over the next quarter is
then compared with its detailed peer group's median return over the same
quarter (the "peer-relative return"). Taking out the group's return also
takes out the market and the industry, which is the layering the method
asks for; differences in macro sensitivity inside a group are not taken out.

Tests, for each factor, the company score, and every measure (including the
measures whose direction isn't settled):

  Spread     Within each detailed group, companies are sorted by the item;
             the top fifth's average peer-relative return minus the bottom
             fifth's, pooled across groups, one number per quarter.
  Bands      Average peer-relative return for each reading (+1 ... -1).
  Range      95% bootstrap range of the average quarterly spread.
  Periods    2001 to 2007, 2008 to 2019, 2020 on, and the two halves
             (to 2013, 2014 on).
  FDR        Benjamini-Hochberg at 10% across the six factor tests.

Out of sample: the scored factors' directions were fixed in advance, so
nothing is fitted. For the held-out measures, the direction is read
from the first half only and then tested on the second half.

Confidence check 3 (written to data/company/check/factor_check.csv, read by
the weekly run): a factor passes for a broad group when, pooled over all
groups, its spread is positive with a range above zero, passes the false
discovery check, and is positive in all three periods; and inside that broad
group its spread is positive overall and in at least two of the three
periods (with at least 20 usable quarters).

Only aggregate results are written (data/company/check/): the repository is
public and the Sharadar personal licence doesn't allow redistributing its
data.

Standard library only. Run: python scripts/company_check.py
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import random
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import company_measures as cm  # noqa: E402

OUT = cm.ROOT / "data" / "company" / "check"
LOAD_FROM = dt.date(1997, 6, 1)
FIRST_DATE = dt.date(2001, 3, 31)
HORIZON = 91                 # days: the next quarter
MIN_GROUP = 10               # companies with a value in a group to sort it
MIN_TAIL = 20                # companies per tail (pooled) for a quarter to count
MIN_TAIL_GROUP = 5           # per tail inside one broad group
MIN_TAIL_MEASURE = 8         # per tail for one measure (some apply to ~100 companies)
MIN_QUARTERS = 20
BOOT = 2000
FDR = 0.10
PERIODS = [("2001 to 2007", 2001, 2007), ("2008 to 2019", 2008, 2019),
           ("2020 on", 2020, 2100)]
HALF = 2013                  # first half to 2013, second half 2014 on
BROADS = ["NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq", "Telcm",
          "Utils", "Shops", "Hlth", "Money", "Other"]
BROAD_NAMES = {"NoDur": "Consumer nondurables", "Durbl": "Consumer durables",
               "Manuf": "Manufacturing", "Enrgy": "Energy", "Chems": "Chemicals",
               "BusEq": "Business equipment", "Telcm": "Telecom",
               "Utils": "Utilities", "Shops": "Shops", "Hlth": "Healthcare",
               "Money": "Money", "Other": "Other"}
HELD_OUT = [m.key for m in cm.MEASURES if not m.scored]


def quarter_ends(first: dt.date, last: dt.date) -> list[dt.date]:
    out, y, q = [], first.year, (first.month - 1) // 3
    while True:
        month = 3 * q + 3
        d = (dt.date(y, month % 12 + 1, 1) if month < 12 else dt.date(y + 1, 1, 1)) \
            - dt.timedelta(days=1)
        if d > last:
            return out
        if d >= first:
            out.append(d)
        q += 1
        if q == 4:
            q, y = 0, y + 1


def forward_return(data: cm.Data, t: str, asof: int) -> float | None:
    """Return from the last close on or before asof to the last close on or
    before asof + HORIZON. A company that stops trading in between gets the
    return to its last close (no delisting return is available)."""
    a = cm.close_on(data, t, asof)
    b = cm.close_on(data, t, asof + HORIZON)
    if not a or not b or asof - a[0] > cm.LISTED_DAYS or b[0] <= a[0]:
        return None
    return b[1] / a[1] - 1


def winsorize(xs: list[float], p: float = 0.01) -> list[float]:
    s = sorted(xs)
    lo, hi = s[int(p * (len(s) - 1))], s[int((1 - p) * (len(s) - 1))]
    return [min(hi, max(lo, x)) for x in xs]


def snapshot(data: cm.Data, asof: int) -> tuple[list, dict]:
    """One quarter's rows: (group, broad, rel return, {item: percentile},
    {factor: reading}) for peer-set companies with a forward return."""
    res = cm.run(data, asof)
    rows, rets = [], {}
    for t, c in res["companies"].items():
        u = c["info"]
        if not u["peer"]:
            continue
        r = forward_return(data, t, asof)
        if r is not None:
            rets[t] = r
    by_group = defaultdict(list)
    for t, r in rets.items():
        by_group[res["companies"][t]["info"]["group"]].append(r)
    med = {g: statistics.median(v) for g, v in by_group.items() if len(v) >= 5}
    keep = [t for t in rets if res["companies"][t]["info"]["group"] in med]
    rel = dict(zip(keep, winsorize([rets[t] - med[res["companies"][t]["info"]["group"]]
                                    for t in keep]))) if keep else {}
    for t, x in rel.items():
        c = res["companies"][t]
        items, reads = {}, {}
        for f in cm.FACTORS:
            fa = c["factors"][f]
            if fa["reading"] is not None:
                items[f] = fa["pct"]
                reads[f] = fa["reading"]
        if c["score"] is not None:
            items["score"] = c["score"]
            reads["score"] = c["score"]
        for k, p in res["pct"][t].items():
            if p.get("pct") is not None:
                items["m:" + k] = p["pct"]
        rows.append((c["info"]["group"], c["info"]["broad"], x, items, reads))
    gone = sum(1 for t in rel if not cm.close_on(data, t, asof + HORIZON) or
               cm.close_on(data, t, asof + HORIZON)[0] < asof + HORIZON - cm.LISTED_DAYS)
    meta = {"universe": len(res["universe"]), "peer_rows": len(rows),
            "lookahead": res["lookahead"], "left_market": gone}
    return rows, meta


def tails(rows: list, item: str) -> list[tuple[str, float, int]]:
    """(broad group, rel return, +1 top fifth / -1 bottom fifth) for companies
    in the top or bottom fifth of `item` within their detailed group."""
    by_group = defaultdict(list)
    for g, b, x, items, _ in rows:
        if item in items:
            by_group[g].append((items[item], x, b))
    out = []
    for g, v in by_group.items():
        if len(v) < MIN_GROUP:
            continue
        v.sort(key=lambda z: z[0])
        n = len(v)
        i = 0
        while i < n:
            # mid-rank, so ties (e.g. no insider trades) share a position
            j = i
            while j + 1 < n and v[j + 1][0] == v[i][0]:
                j += 1
            r = (i + j) / 2 / (n - 1)
            side = 1 if r >= 0.8 else (-1 if r < 0.2 else 0)
            if side:
                out += [(b, x, side) for _, x, b in v[i:j + 1]]
            i = j + 1
    return out


def spread(tl: list, broad: str | None = None, min_tail: int = MIN_TAIL) -> float | None:
    top = [x for b, x, s in tl if s == 1 and (broad is None or b == broad)]
    bot = [x for b, x, s in tl if s == -1 and (broad is None or b == broad)]
    if len(top) < min_tail or len(bot) < min_tail:
        return None
    return statistics.mean(top) - statistics.mean(bot)


def summarize(series: list[tuple[dt.date, float]], seed: int = 1) -> dict:
    xs = [x for _, x in series]
    out = {"quarters": len(xs)}
    if len(xs) < 4:
        return out
    m = statistics.mean(xs)
    sd = statistics.stdev(xs)
    t = m / (sd / math.sqrt(len(xs))) if sd > 0 else 0.0
    rng = random.Random(seed)
    boots = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(BOOT))
    out.update(mean=m, low=boots[int(0.025 * BOOT)], high=boots[int(0.975 * BOOT)],
               t=t, p=math.erfc(abs(t) / math.sqrt(2)),
               hit=sum(x > 0 for x in xs) / len(xs))
    for name, a, b in PERIODS:
        sub = [x for d, x in series if a <= d.year <= b]
        out[name] = statistics.mean(sub) if len(sub) >= 4 else None
    first = [x for d, x in series if d.year <= HALF]
    second = [x for d, x in series if d.year > HALF]
    out["first_half"] = statistics.mean(first) if len(first) >= 4 else None
    out["second_half"] = statistics.mean(second) if len(second) >= 4 else None
    if len(second) >= 4:
        b2 = sorted(statistics.mean(rng.choices(second, k=len(second)))
                    for _ in range(BOOT))
        out["second_low"], out["second_high"] = b2[int(0.025 * BOOT)], b2[int(0.975 * BOOT)]
    return out


def bh(pvals: dict, q: float = FDR) -> set:
    items = sorted((p, k) for k, p in pvals.items() if p is not None)
    n, passed = len(items), set()
    cut = 0
    for i, (p, k) in enumerate(items, 1):
        if p <= q * i / n:
            cut = i
    for i, (p, k) in enumerate(items, 1):
        if i <= cut:
            passed.add(k)
    return passed


def pc(x, nd=2):
    return "" if x is None else f"{100 * x:+.{nd}f}"


def fmt(x, nd=4):
    return "" if x is None else f"{x:.{nd}f}"


def main() -> int:
    t0 = time.time()
    today = dt.date.today()
    data = cm.load(today.toordinal(), start=LOAD_FROM.toordinal())
    print(f"loaded full history in {time.time() - t0:,.0f}s")
    last_px = max((ds[-1] for ds in data.px_d.values() if len(ds)), default=0)
    dates = [d for d in quarter_ends(FIRST_DATE, today)
             if d.toordinal() + HORIZON <= last_px]
    print(f"{len(dates)} quarter ends, {dates[0]} to {dates[-1]}")

    quarters = []      # (date, rows)
    metas = []
    for d in dates:
        t1 = time.time()
        rows, meta = snapshot(data, d.toordinal())
        quarters.append((d, rows))
        metas.append((d, meta))
        print(f"{d}: {meta['peer_rows']:,} peer-set companies tested "
              f"({meta['universe']:,} listed) in {time.time() - t1:,.1f}s", flush=True)

    # Spreads per item and quarter.
    items = (cm.FACTORS + ["score"] + ["m:" + m.key for m in cm.MEASURES])
    series = defaultdict(list)            # item -> [(date, spread)]
    gseries = defaultdict(list)           # (factor, broad) -> [(date, spread)]
    band_sum = defaultdict(list)          # (factor, reading) -> [quarter mean]
    for d, rows in quarters:
        for it in items:
            tl = tails(rows, it)
            s = spread(tl, None, MIN_TAIL_MEASURE if it.startswith("m:") else MIN_TAIL)
            if s is not None:
                series[it].append((d, s))
            if it in cm.FACTORS:
                for b in BROADS:
                    s = spread(tl, b, MIN_TAIL_GROUP)
                    if s is not None:
                        gseries[(it, b)].append((d, s))
        for f in cm.FACTORS:
            by = defaultdict(list)
            for g, b, x, its, reads in rows:
                if f in reads:
                    by[reads[f]].append(x)
            for r, xs in by.items():
                if len(xs) >= MIN_TAIL:
                    band_sum[(f, r)].append(statistics.mean(xs))

    stats = {it: summarize(series[it]) for it in items}
    fpass = bh({f: stats[f].get("p") for f in cm.FACTORS})
    gstats = {k: summarize(v) for k, v in gseries.items()}

    def pooled_ok(f):
        s = stats[f]
        return bool(s.get("mean") and s["mean"] > 0 and s["low"] > 0 and f in fpass
                    and all((s.get(n) or 0) > 0 for n, _, _ in PERIODS))

    check_rows = []
    run_date = today.isoformat()
    for f in cm.FACTORS:
        for b in BROADS:
            g = gstats.get((f, b), {"quarters": 0})
            why = []
            if not pooled_ok(f):
                why.append("pooled test not passed")
            if g["quarters"] < MIN_QUARTERS:
                why.append(f"only {g['quarters']} usable quarters in this group")
            else:
                pos_periods = sum(1 for n, _, _ in PERIODS if (g.get(n) or 0) > 0)
                if g["mean"] <= 0:
                    why.append("negative in this group")
                if pos_periods < 2:
                    why.append(f"positive in {pos_periods} of 3 periods in this group")
            check_rows.append([f, b, "N" if why else "Y", "; ".join(why) or "passes",
                               g["quarters"], pc(g.get("mean")), run_date])

    OUT.mkdir(parents=True, exist_ok=True)
    cm.write_csv(OUT / "factor_check.csv",
                 ["factor", "broad_group", "passes", "why", "quarters",
                  "mean_spread_pct", "check_run"], check_rows)

    head = ["item", "kind", "scored", "quarters", "mean_spread_pct", "low_pct",
            "high_pct", "t", "p", "fdr_pass", "positive_share"] + \
           [n for n, _, _ in PERIODS] + ["first_half", "second_half",
                                         "second_low", "second_high"]
    trows = []
    for it in items:
        s = stats[it]
        kind = "factor" if it in cm.FACTORS else ("score" if it == "score" else "measure")
        scored = "yes" if kind != "measure" or cm.BY_KEY[it[2:]].scored else "no"
        trows.append([it.removeprefix("m:"), kind, scored, s["quarters"],
                      pc(s.get("mean")), pc(s.get("low")), pc(s.get("high")),
                      fmt(s.get("t"), 2), fmt(s.get("p")),
                      "Y" if it in fpass else ("N" if kind == "factor" else ""),
                      fmt(s.get("hit"), 2)] +
                     [pc(s.get(n)) for n, _, _ in PERIODS] +
                     [pc(s.get("first_half")), pc(s.get("second_half")),
                      pc(s.get("second_low")), pc(s.get("second_high"))])
    cm.write_csv(OUT / "spread_tests.csv", head, trows)

    grows = []
    for (f, b), s in sorted(gstats.items()):
        grows.append([f, b, s["quarters"], pc(s.get("mean")), pc(s.get("low")),
                      pc(s.get("high"))] + [pc(s.get(n)) for n, _, _ in PERIODS])
    cm.write_csv(OUT / "group_tests.csv",
                 ["factor", "broad_group", "quarters", "mean_spread_pct", "low_pct",
                  "high_pct"] + [n for n, _, _ in PERIODS], grows)

    brows = []
    for f in cm.FACTORS:
        for r in (1.0, 0.5, 0.0, -0.5, -1.0):
            xs = band_sum.get((f, r), [])
            brows.append([f, r, len(xs), pc(statistics.mean(xs) if xs else None)])
    cm.write_csv(OUT / "band_returns.csv",
                 ["factor", "reading", "quarters", "mean_rel_return_pct"], brows)

    qrows = [[d.isoformat()] + [pc(dict(series[f]).get(d)) for f in cm.FACTORS + ["score"]]
             for d, _ in quarters]
    cm.write_csv(OUT / "quarterly_spreads.csv",
                 ["quarter_end"] + cm.FACTORS + ["score"], qrows)

    # Held-out measures: direction from the first half, tested on the second.
    held = []
    for k in HELD_OUT:
        s = stats["m:" + k]
        m = cm.BY_KEY[k]
        f1, f2 = s.get("first_half"), s.get("second_half")
        if f1 is None or f2 is None:
            call, direction = "not enough data", ""
        else:
            direction = "higher is better" if f1 > 0 else "lower is better"
            agree = (f1 > 0) == (f2 > 0)
            lo2, hi2 = s.get("second_low"), s.get("second_high")
            clear2 = lo2 is not None and (lo2 > 0 or hi2 < 0)
            if agree and clear2:
                call = f"{direction} (second half agrees, range clear of zero)"
            elif agree:
                call = f"leans {direction}; second half agrees but its range crosses zero"
            else:
                call = "no direction: the two halves disagree"
        held.append((m, s, direction, call))

    write_report(metas, stats, fpass, gstats, check_rows, band_sum, held, run_date)
    print(f"done in {time.time() - t0:,.0f}s")
    return 0


def write_report(metas, stats, fpass, gstats, check_rows, band_sum, held, run_date):
    look = sum(m["lookahead"] for _, m in metas)
    d0, d1 = metas[0][0], metas[-1][0]
    rows_n = [m["peer_rows"] for _, m in metas]
    gone = sum(m["left_market"] for _, m in metas)
    L = ["# Company measured check", "",
         f"Run: {run_date}. {len(metas)} quarter ends, {d0} to {d1}, each scored "
         "with only the filings and prices known that day, then compared with the "
         "next quarter's return relative to the company's detailed peer group "
         "(the group's median). Method: docs/company-method.md section 9; "
         "write-up: docs/company-check.md. Code: scripts/company_check.py.", "",
         "## Checks", "", "| Check | Result | Detail |", "|---|---|---|",
         f"| No filing or price after each run date | {'pass' if look == 0 else 'FAIL'} "
         f"| {look:,} later dates used across {len(metas)} runs |",
         f"| Companies that later left the market are kept | "
         f"{'pass' if gone > 0 else 'FAIL'} | {gone:,} company-quarters where the "
         "company stopped trading during the next quarter (return to its last close) |",
         f"| Enough companies each quarter | {'pass' if min(rows_n) >= 1000 else 'FAIL'} "
         f"| {min(rows_n):,} to {max(rows_n):,} peer-set companies tested per quarter |",
         "", "## Factors: top fifth minus bottom fifth, next quarter, relative to peers", "",
         "Percent per quarter. Range: 95% bootstrap. FDR: Benjamini-Hochberg at 10% "
         "across the six factors.", "",
         "| Factor | Quarters | Spread | Range | FDR | Up quarters | 2001-07 | 2008-19 | 2020 on |",
         "|---|---|---|---|---|---|---|---|---|"]
    for f in cm.FACTORS + ["score"]:
        s = stats[f]
        name = cm.FACTOR_NAMES.get(f, "Company score")
        if "mean" not in s:
            L.append(f"| {name} | {s['quarters']} | not enough data | | | | | | |")
            continue
        L.append(f"| {name} | {s['quarters']} | {pc(s['mean'])}% | {pc(s['low'])} to "
                 f"{pc(s['high'])} | {'pass' if f in fpass else ('–' if f == 'score' else 'no')} "
                 f"| {100 * s['hit']:.0f}% | " +
                 " | ".join(pc(s.get(n)) or "–" for n, _, _ in PERIODS) + " |")
    L += ["", "## Average next-quarter return relative to peers, by reading", "",
          "| Factor | +1 | +0.5 | 0 | −0.5 | −1 |", "|---|---|---|---|---|---|"]
    for f in cm.FACTORS:
        cells = []
        for r in (1.0, 0.5, 0.0, -0.5, -1.0):
            xs = band_sum.get((f, r), [])
            cells.append(f"{pc(statistics.mean(xs))}%" if xs else "–")
        L.append(f"| {cm.FACTOR_NAMES[f]} | " + " | ".join(cells) + " |")
    L += ["", "## Confidence check 3 by broad group", "",
          "Y = passes (pooled test passed, and positive in this group overall and in "
          "at least two of three periods).", "",
          "| Factor | " + " | ".join(BROAD_NAMES[b] for b in BROADS) + " |",
          "|---|" + "---|" * len(BROADS)]
    by = {(r[0], r[1]): r for r in check_rows}
    for f in cm.FACTORS:
        L.append(f"| {cm.FACTOR_NAMES[f]} | " + " | ".join(
            "Y" if by[(f, b)][2] == "Y" else (pc(gstats.get((f, b), {}).get("mean"), 1) or "–")
            for b in BROADS) + " |")
    L += ["", "Cells without Y show the group's average spread (percent per quarter).",
          "", "## Measures whose direction isn't settled", "",
          "Direction read from 2001 to 2013 only, then tested on 2014 on.", "",
          "| Measure | Applies to | Quarters | 2001-13 | 2014 on | 2014-on range | Call |",
          "|---|---|---|---|---|---|---|"]
    applies_to = {"rnd_share": "business equipment, healthcare",
                  "capex_depr": "manufacturing", "reinvest_rate": "energy",
                  "capex_rev": "telecom", "payout_ratio": "utilities"}
    for m, s, direction, call in held:
        L.append(f"| {m.label} | {applies_to.get(m.key, '')} | {s['quarters']} | "
                 f"{pc(s.get('first_half'))} | {pc(s.get('second_half'))} | "
                 f"{pc(s.get('second_low'))} to {pc(s.get('second_high'))} | {call} |")
    L += ["", "Spreads here are higher value minus lower value, so a positive number "
          "means higher is better.", "",
          "## Every measure", "",
          "| Measure | Scored | Quarters | Spread | Range | 2001-07 | 2008-19 | 2020 on |",
          "|---|---|---|---|---|---|---|---|"]
    for m in cm.MEASURES:
        s = stats["m:" + m.key]
        if "mean" not in s:
            L.append(f"| {m.label} | {'yes' if m.scored else 'no'} | {s['quarters']} "
                     "| not enough data | | | | |")
            continue
        L.append(f"| {m.label} | {'yes' if m.scored else 'no'} | {s['quarters']} | "
                 f"{pc(s['mean'])} | {pc(s['low'])} to {pc(s['high'])} | " +
                 " | ".join(pc(s.get(n)) or "–" for n, _, _ in PERIODS) + " |")
    L += ["", "For scored measures the spread is better minus worse (direction "
          "applied).", "",
          "## Limits", "",
          "- Peer groups use each company's industry as Sharadar lists it today, "
          "not as it was then.",
          "- Companies that stop trading get the return to their last close; "
          "Sharadar has no delisting returns, so failures may look a little "
          "better than they were.",
          "- Before August 2004 there are no 8-K results filings, so the earnings "
          "surprise uses the quarterly filing date, which comes after the results "
          "announcement.",
          "- Insider trades start in 2008 and institutional holdings later, so owner "
          "signals are tested on fewer quarters.",
          "- Only peer-set companies (above the size floor) are tested.",
          "- Per-company results are not saved: the repository is public and the "
          "Sharadar licence doesn't allow redistributing its data.", ""]
    (OUT / "CHECK_REPORT.md").write_text("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())
