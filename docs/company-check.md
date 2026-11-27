# Company pillar: the measured check

**First run November 27, 2026.** Do the company factor readings say anything about how a stock does next, compared with its own industry peers? This is check 3 in the confidence rule (`docs/company-method.md` sections 8 and 9). Code: `scripts/company_check.py`, run on the 1st of every month (`.github/workflows/company-check.yml`). Full results: `data/company/check/CHECK_REPORT.md`.

## How it works

- **102 quarter ends, March 2001 to June 2026.** On each one the whole weekly calculation (`scripts/company_measures.py`) runs as if it were that day: only filings dated and prices on or before it, every company listed then, including ones that later left the market. 0 later dates were used across the 102 runs.
- **Outcome:** each company's return over the next quarter (91 days) minus its detailed peer group's median return. Taking out the group takes out the market and the industry. Returns are trimmed at the 1st and 99th percentiles.
- **Test:** inside each detailed group, the top fifth by a factor reading against the bottom fifth; the gap in next-quarter return, pooled across groups, is one number per quarter. Its average over all quarters is the **spread**.
- **Range:** 95% bootstrap range of the average spread (2,000 draws).
- **Periods:** 2001 to 2007, 2008 to 2019, 2020 on, as the method asks, plus two halves (to 2013, 2014 on).
- **False discoveries:** Benjamini-Hochberg at 10% across the six factors.
- **Out of sample:** the six factors' directions were fixed in advance (the factors doc), so nothing is fitted to these returns. For the five held-out measures, the direction is read from 2001 to 2013 only and then tested on 2014 on.

## Results

| Factor | Spread per quarter | Range | Positive in all 3 periods | Passes |
|---|---|---|---|---|
| Growth | +0.36% | −0.39 to +1.06 | no (2008 to 2019 −0.11) | no |
| Profitability | +1.28% | −0.13 to +2.69 | yes | no: range touches zero |
| Balance sheet | +1.03% | +0.05 to +1.99 | yes | yes |
| Capital use | +1.75% | +0.64 to +2.86 | yes | yes |
| Earnings surprise | +0.40% | −0.10 to +0.81 | no (2001 to 2007 −0.02) | no |
| Owner signals | −0.54% | −1.10 to +0.01 | no, negative in both periods it covers | no |
| Company score | +1.49% | +0.33 to +2.63 | yes | (not a factor) |

- **The company score works as a whole.** The top fifth of each group beat the bottom fifth by about 1.5% a quarter, positive in all three periods and in 71% of quarters.
- **Capital use and balance sheet pass.** The strongest single measures are free cash flow yield (+2.0%), change in share count (+1.8%, fewer shares is better), deferred revenue growth (+1.8%) and cash runway (+2.8%, healthcare).
- **Profitability nearly passes.** Positive in every period and every broad group, but its range just touches zero; its weakest band (−1) does clearly worse (−0.34% vs about +1.3% to +1.8% for the rest).
- **Growth and earnings surprise are weak.** Small positive spreads that flip sign in one period.
- **Owner signals point the wrong way.** Both measures have negative spreads: institutional buying −1.10% (range −1.85 to −0.40, clear of zero), insider buying −0.54%. Companies with heavy insider selling or institutional buying did somewhat worse than peers the next quarter, not better. See "Open questions".

## What changes in the weekly run

- `data/company/check/factor_check.csv` lists, for each factor and broad group, whether check 3 passes. The weekly run reads it: a factor is High confidence when it also has its data (two thirds of measures, fresh) and at least 20 peers.
- **Passes:** capital use in all 12 broad groups; balance sheet in 11 (not utilities, where its spread is −0.1%).
- A company's confidence is the lowest among the factors carrying most of its weight, so a company reaches High only when every one of those factors does. With growth, profitability and earnings surprise not passing, few companies reach High yet; that's intended.
- **Rule for passing** (a factor, for one broad group): pooled over all groups, the spread is positive, its range is above zero, it passes the false-discovery check and it's positive in all three periods; and inside that broad group the spread is positive overall and in at least two of the three periods, with at least 20 usable quarters.

## The five held-out measures

Direction read from 2001 to 2013, then tested on 2014 on. A positive spread means higher is better.

| Measure | Applies to | 2001 to 2013 | 2014 on (range) | Proposal |
|---|---|---|---|---|
| R&D ÷ revenue | business equipment, healthcare | −0.87 | +0.46 (−1.28 to +2.31) | keep out: the halves disagree |
| Capex ÷ depreciation | manufacturing | −1.32 | −0.84 (−2.23 to +0.53) | lower is better, low confidence |
| Reinvestment rate | energy | +0.37 | +0.19 (−2.02 to +2.49) | keep out: tiny and noisy |
| Capex ÷ revenue | telecom | −2.61 | −0.92 (−3.66 to +1.81) | lower is better, low confidence |
| Dividend payout ratio | utilities | +0.39 | −1.07 (−3.56 to +1.48) | keep out: the halves disagree |

Over the whole period, capex ÷ depreciation is −1.08% (range −2.04 to −0.11, clear of zero) and capex ÷ revenue −1.78% (range −4.21 to +0.63): heavy spenders did worse than their peers, which fits the factors doc's worry about empire building. None of the five is switched on; that's a call for Kshitij.

## Open questions

1. **Held-out measures:** switch on capex ÷ depreciation and capex ÷ revenue as "lower is better"; keep the other three out.
2. **Owner signals:** the factor points the wrong way. Options: leave it scored and Low confidence (it can't pass check 3); drop it from the score until it's rebuilt; or flip it. Before deciding, one suspected data issue is worth fixing: institutional holdings are share counts as filed, so a stock split between two quarters can look like heavy institutional buying. Measuring the change as a share of shares outstanding at each quarter would remove that.
3. **The check-3 rule** above, which is stricter than the method's wording ("the same sign across periods") because it also asks for a range above zero and the false-discovery check.

## How it differs from the method doc

- **Residual:** next-quarter return minus the detailed group's median, not a regression on the market, macro exposures and industry each month. The group median takes out market and industry; differences in macro sensitivity inside a group stay in.
- **Per detailed group:** the method asks for the test per detailed group where there are enough companies; most of the 48 groups are too small for a reliable quarter-by-quarter test, so check 3 is decided per broad group (French's 12), on top of the pooled test. Spreads by broad group, with ranges and periods, are in `group_tests.csv`.
- **Quarterly, not monthly,** to keep the run inside GitHub's time limit.

## Limits

- Peer groups use each company's industry as Sharadar lists it today, not as it was then.
- Companies that stop trading get the return to their last close; Sharadar has no delisting returns, so failures may look a little better than they were.
- Before August 2004 there are no 8-K results filings, so earnings surprise uses the quarterly filing date, which comes after the results announcement.
- Insider trades start in 2008 and institutional holdings later, so owner signals are tested on fewer quarters (72 and 51).
- Only peer-set companies (above the size floor) are tested.
- Per-company results aren't saved: the repository is public and the Sharadar licence doesn't allow redistributing its data.
