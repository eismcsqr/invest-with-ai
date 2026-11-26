# Rates test on broad sectors (free version)

Run on 2026-11-26 with provisional Fed dates. Full tables: [`results/rates_test/RESULTS.md`](../results/rates_test/RESULTS.md).

## Headline

On Fed decision days since 1994, consumer durables, retail and the "Other" group (which holds homebuilders and airlines) do worse than the market when the 2-year yield jumps, and better when it drops. That matches the v0 scorecard, which rates automakers, homebuilders and airlines among the most rate-hurt consumer businesses. Consumer staples move with the market, which also fits v0's milder score.

The one disagreement: retail is more rate-sensitive than v0's average for the retail types (−2.2) implies. Three of the five retail types v0 maps there already score −3 or −4, so the likely fix is to weight the scorecard toward those, not to change the method.

What the test can't confirm: whether these sectors fall in absolute terms. On Fed days the whole market's reaction to rates is noisy (−0.15% per +10 bp, range −0.51 to +0.20), so only the relative ranking is measurable from these days alone.

## Results for the four groups v0 covers

Relative slope = sector return minus market return, per +10 bp move in the 2-year yield, with a 95% range.

| Group | v0 types mapped (rates score) | Relative slope | Agrees with v0? | Confidence |
|---|---|---|---|---|
| Consumer durables | Automaker (−4) | −0.31 (−0.54 to −0.09) | Yes | High |
| Other | Homebuilder (−5), Airline (−3) | −0.11 (−0.22 to −0.02) | Yes, but the mapping is loose | High |
| Retail, wholesale, restaurants | Home improvement (−4), Restaurant (−3), Online marketplace (−3), Grocery (−1), Discount (0) | −0.21 (−0.34 to −0.08) | No: more hurt than v0's average implies | High |
| Consumer staples | Packaged foods (−2), Luxury (−2) | +0.01 (−0.18 to +0.19) | Yes: no worse than the market | Low |

All three negative results hold in every period (1994–2007, 2008–2015, 2016 on), without crisis days, beta-adjusted and equal-weighted, and keep their sign out of sample. Of the eight groups v0 doesn't cover, only energy stands out: it tends to beat the market when rates rise (+0.23, range −0.00 to +0.46, medium confidence). Finance flips sign between periods, so it says little yet.

## How it works

- **Events:** 270 Fed decision days, February 1994 (when the Fed started announcing decisions) to September 2026, where the Ken French data ends. Scheduled meetings plus unscheduled rate changes.
- **Rate move:** change in the 2-year Treasury yield (FRED DGS2) from the previous close to the decision-day close.
- **Sector reaction:** Ken French 12 industries, value-weighted, minus the market return.
- **Sensitivity:** slope of the sector's relative return on the yield move. Ranges come from resampling events 2,000 times.
- **Checks:** three periods, an out-of-sample split (fit before 2010, test after), crisis days removed, beta-adjusted, equal-weighted, and rate news vs growth news (whether stocks and yields moved in opposite or the same directions).
- **v0 comparison:** each v0 company type is mapped to its French group (`config/v0_rates_scores.csv`). "Agrees" uses a simple reading of v0: a score of −3 or below means "hurt more than a typical stock", above −3 means "hurt no more than a typical stock".

## Limits

- **Provisional Fed dates.** `config/fomc_dates_provisional.csv` was entered by hand from the Fed's published schedules, because the Fed's site isn't reachable from the build environment. It hasn't been checked against the Fed's pages. As a sanity check, the 2-year yield moves about 40% more on these days than on other days, and more in every period. When the event calendar is merged (`data/events/fomc_decisions.csv`), the script uses it automatically.
- **Loose mapping.** French's groups are broad. "Other" also holds mining, hotels, business services and entertainment, and "Retail" mixes discounters with home improvement. This tests whether v0's ranking holds at sector level, not each company type.
- **Signal is small next to noise.** Rates move sectors on Fed days, but other news moves them more: using the first half's slopes to call the second half's daily direction is right 55–60% of the time for the three clear groups.
- **Today's data versions.** Returns and yields don't get revised, so original data versions don't matter here.

## Rerun

```
python scripts/rates_test.py
```

Standard library only, about 20 seconds. Writes `results/rates_test/` (RESULTS.md, events.csv, sensitivity.csv, v0_comparison.csv). Rerun after the event calendar merges and after each data refresh.
