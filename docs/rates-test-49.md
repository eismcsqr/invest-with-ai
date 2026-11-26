# Rates test on detailed industry groups

Run on 2026-11-26: the same Fed-day test as the [broad-sector run](rates-test.md), on Ken French's 49 industry groups instead of 12. Full tables: [`results/rates_test_49/RESULTS.md`](../results/rates_test_49/RESULTS.md).

## Headline

Splitting the 12 sectors into 49 groups shows where the rate sensitivity actually sits. The broad "Retail, wholesale, restaurants" result comes from retail stores, not restaurants. The broad "Other" result doesn't come from transportation, which is flat; construction, entertainment, mining and precious metals lean the most negative inside it. Autos holds up on its own.

Only a few groups carry a signal that survives the extra noise of testing 49 at once. Seven of 49 clear a 95% range, against two or three expected by luck, and three pass the false-discovery check: retail, rubber and plastics, and packaging. Treat everything else as a lean, not a finding.

## Most and least rate-sensitive groups

Relative slope = group return minus market return, per +10 bp move in the 2-year yield, with a 95% range. Negative means the group lags the market when yields jump on a Fed day.

**Most hurt by higher yields**

| Group | Relative slope (range) | Confidence | Passes false-discovery check |
|---|---|---|---|
| Precious metals | −0.77 (−1.45 to −0.06) | Medium | no |
| Retail | −0.28 (−0.47 to −0.10) | High | yes |
| Rubber and plastics | −0.27 (−0.42 to −0.13) | High | yes |
| Entertainment | −0.27 (−0.56 to +0.02) | Medium | no |
| Packaging | −0.26 (−0.46 to −0.07) | High | yes |
| Autos and parts | −0.25 (−0.52 to −0.01) | High | no |
| Construction | −0.25 (−0.60 to +0.10) | Medium | no |
| Steel | −0.23 (−0.43 to −0.04) | High | no |

**Least hurt (beat the market when yields jump)**

| Group | Relative slope (range) | Confidence | Passes false-discovery check |
|---|---|---|---|
| Agriculture | +0.33 (−0.02 to +0.70) | Medium | no |
| Ships and railcars | +0.29 (+0.06 to +0.54) | High | no |
| Defense | +0.25 (−0.07 to +0.64) | Low | no |
| Oil and gas | +0.22 (−0.01 to +0.44) | Medium | no |

Precious metals has the biggest number but it comes almost entirely from 2008 on (−0.88 and −1.79 in the two later periods, +0.09 before), which fits gold's link to real yields. Ships and railcars leans on 1994–2007 and is a small group. Banks, real estate, utilities, software, computers and chips all sit near zero and flip sign between periods, so Fed days alone don't show a stable rate effect for them.

## Compared with the v0 scorecard

Seven of the 49 groups map to v0's consumer company types, up from four in the broad run.

| Group | v0 types mapped (rates score) | Relative slope | What it says about v0 | Confidence |
|---|---|---|---|---|
| Autos and parts | Automaker (−4) | −0.25 (−0.52 to −0.01) | Confirmed | High |
| Retail | Home improvement (−4), Online marketplace (−3), Grocery (−1), Discount (0) | −0.28 (−0.47 to −0.10) | v0 too mild: retail stores are among the most rate-hurt groups, but v0 averages −2.0 | High |
| Construction | Homebuilder (−5) | −0.25 (−0.60 to +0.10) | Leans confirmed: negative in all three periods and both halves, range just crosses zero | Medium |
| Restaurants and hotels | Restaurant chain (−3) | −0.07 (−0.24 to +0.10) | Not supported: no worse than the market outside 2008–2015 | Low |
| Transportation | Airline (−3) | −0.03 (−0.24 to +0.13) | Can't tell: the group is mostly railroads, trucking and delivery | Low |
| Food products | Packaged foods maker (−2) | +0.02 (−0.23 to +0.28) | Confirmed: no worse than the market | Low |
| Apparel | Luxury brand (−2) | −0.20 (−0.45 to +0.03) | Leans more hurt than v0, but US apparel makers aren't luxury brands | Low |

What this suggests for v0, once the user decides:

- **Retail types:** the strongest consumer result. The group mixes all four retail types, so it can't say which one v0 has wrong, only that the average is too mild. Discount (0) and grocery (−1) are the likeliest to be off.
- **Restaurant chain:** the −3 isn't backed at group level. Low confidence, so a reason to look again, not to change it yet.
- **Airline and homebuilder:** need company-level data (Sharadar) to test, because their French groups mix in other businesses.

Rank agreement between v0's scores and the measured slopes across the seven groups is weak (0.21), mostly because of restaurants and transportation.

## How it works

Same events, measures and checks as the broad run, so the two can be read side by side:

- **Events:** the same 270 Fed decision days, February 1994 to September 2026.
- **Returns:** Ken French's 49 industry portfolios, value-weighted, with equal-weighted as a check. The data pull now fetches them daily from 1990 on (`data/french/industry49_daily_*.csv`).
- **Checks:** three periods, out of sample (fit before 2010, test after), crisis days removed, beta-adjusted, equal-weighted, and rate news vs growth news.
- **New for 49 groups:** a false-discovery check (Benjamini-Hochberg at 10%, using bootstrap p-values), because testing 49 groups at 95% lets two or three through by luck. The broad-sector results now show the same column; their numbers didn't change, and all three of their clear groups pass.
- **Mapping:** `config/v0_rates_scores.csv` gains a 49-group column (`french49_group`) next to the 12-sector one.

## Limits

- **Noise grows with detail.** Smaller groups swing more on single-stock news. Rank agreement of the 49 slopes between the two halves of the sample is only 0.16 (0.27 for the 12), so the overall ranking is not stable; only the handful of groups above are.
- **Groups still mix businesses.** Construction includes contractors as well as homebuilders, transportation holds few airlines, and retail can't be split by store type.
- **42 groups have no v0 type.** v0 covers consumer businesses only; the industry and company pillars will need their own scores to compare against.
- **Relative, not absolute.** As in the broad run, the market's own Fed-day reaction is too noisy to say whether these groups fall in absolute terms.

## Rerun

```
python scripts/rates_test.py --groups 49
```

Standard library only, about a minute. Writes `results/rates_test_49/`. `--groups all` runs both the 12 and the 49.
