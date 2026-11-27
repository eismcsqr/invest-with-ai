# Industry run: first readings and the measured check

Run on 2026-11-27 with the free industry data on main (PR 11). Code: `scripts/industry_assessment.py`. Results: [`results/industry_run/`](../results/industry_run/RESULTS.md). Method: tracker task "Industry method" (agreed Nov 25). Groups: Kenneth French's 12 broad industry groups (Decisions: "Industry vs. macro boundary").

## Headline

The free data gives a current reading for three of the six industry factors in every group, and for capacity in six of the twelve. Today it points to a few clear tailwinds and headwinds, listed below. But the measured check doesn't back the readings yet: none of the 70 group tests passes the false-discovery check, and the pooled tests across groups are flat. So no industry score reaches High confidence. Treat these as readings of where each industry stands, not yet as evidence that the reading moves its stocks.

The one pattern close to the line runs against the method: when capacity use is in its top fifth, durables, manufacturing and chemicals have tended to do worse than the market afterwards, not better (pooled, p = 0.06). That fits "tight capacity is late in the cycle" better than "tight capacity means pricing power".

## Where each industry stands now

Scored readings that aren't neutral (score = reading × exposure, on the −3 to +3 scale):

| Group | Factor | What the data shows | Score | Range | Confidence |
|---|---|---|---|---|---|
| Manufacturing | Capacity cycle | Plants 79% used in October, top fifth of the last 20 years | +3 | 0 to +3 | Low |
| Energy | Coping with shocks | Energy prices rose 30 points faster than all prices over the year to Q2 2026 | +2 | 0 to +2 | Low (this is the oil shock, which belongs in macro) |
| Retail and wholesale | Demand cycle | Real output up 5.7% over the year to Q2 2026, top fifth | +2 | 0 to +2 | Low |
| Consumer staples | Coping with shocks | Prices rising 1.8 points slower than all prices; producer prices in their bottom 1% | −3 | −3 to 0 | Low |
| Chemicals | Capacity cycle | Plants 71% used, bottom fifth | −3 | −3 to 0 | Low |
| Telecom | Demand cycle | Real output down 0.5% over the year | −1 | −1 to 0 | Medium |
| Utilities | Capacity cycle | 69% used, the lowest in 20 years | −1 | −1 to 0 | Medium |
| Healthcare | Coping with shocks | Prices rising 1.2 points slower than all prices | −1 | −1 to 0 | Low |

Everything else scored is neutral today; durables demand (76th percentile), business equipment demand (76th) and healthcare demand (78th) sit just under the tailwind line, so their ranges reach up to the full exposure. Full table: `results/industry_run/scores.csv`.

## How it was built

1. **Mapping.** `config/industry_crosswalk.csv` maps 63 BEA industries, 27 Fed capacity series, 21 Census factory categories and 43 producer price indexes to French's groups, following French's SIC definitions. BEA industries that span groups are split by rough output shares, noted on each row (for example chemicals: 65% Chemicals, 35% Healthcare for drugs; publishing: 75% tech for software). Farms and owner-occupied housing are left out: French counts farms in staples and real estate in finance, but few listed companies do that work.
2. **Readings.** Each measure is ranked against the group's own last 20 years. Top fifth = tailwind (+1), bottom fifth = headwind (−1), else neutral. Twenty years rather than all history, because capacity use has drifted down for decades and would otherwise read as a headwind almost every month.
   - **Demand cycle:** BEA real gross output, growth over a year (quarterly, to Q2 2026, all groups). Cross-check: Census factory shipments deflated by producer prices (monthly, to September).
   - **Capacity cycle:** Fed G.17 capacity use (monthly, to October). Scored only where the series cover at least half the group's output: staples, durables, manufacturing, energy, chemicals, utilities. Tech hardware is only 16% of the tech group (software and services are the rest), so tech isn't scored.
   - **Coping with shocks:** BEA output prices, growth over a year, minus the same for all industries: is the group raising prices faster than the economy. Cross-check: producer prices against the average of all mapped indexes (monthly, to October).
   - A cross-check counts only where it covers at least 80% of the group.
3. **Exposure.** `config/industry_exposure_v0.csv` is a v0 judgment, like the macro scorecard: each factor's channel scores (revenue, costs, financing, currency, valuation, competitive position) added up and capped at 3. It hasn't been reviewed; see the calls below.
4. **Measured check.** Each group's monthly return after the market, the 2-year yield and the dollar are taken out (betas from the prior 60 months, so nothing is fitted on the future). The reading is then compared with that leftover return two ways: over the same period ("moves with"), and over the period after the figure is published ("leads"). Readings in the check use only the history known at the time. 95% bootstrap ranges, Benjamini-Hochberg at 10% across all tests of a kind, and a sign-flip check between the first and second half.
5. **Confidence.** High needs the "moves with" check to agree with a range that excludes zero, pass the false-discovery check, hold in both halves, and the data to cover 80% of a well-mapped group. Medium: agrees but not past the false-discovery check, or agrees in both halves with good coverage. Low otherwise. Energy's coping score is capped at Low because energy prices are the oil shock itself.
6. **Range.** The score range takes in the next band when a reading is within 5 points of a band edge or its cross-check is in another band, and allows a smaller exposure when confidence is below High (Medium: one less; Low: down to zero).

## What the check found

- **Nothing passes the false-discovery check** at group level, in either test.
- **Pooled across groups:** demand and coping show no link with leftover returns (slopes within ±0.13% a month, ranges across zero). Capacity leans the wrong way after publication (−0.29% a month per band, range −0.58 to +0.01).
- **Closest to backing the method:** staples demand (+0.7% a month per band in the same quarter and +0.5% in the quarter after publication, both ranges exclude zero, both halves agree, but neither passes the false-discovery check) and energy capacity (+0.7%, range just crosses zero).
- **Leaning against the method:** durables. Strong shipments (−0.9% a month per band, range −1.9 to +0.2) and tight capacity (−0.9% after publication, range −2.1 to +0.2) both go with durables lagging the market: durables stocks move before their sales, so by the time the data is strong the stocks have had their run.

Why the check is weak: the BEA data starts in 2005, so its tests cover about 15 years (63 quarters). Stocks price industry news before government data comes out, so a reading taken from published data is often already in the price. And French's broad groups mix businesses: tech mixes chips with software, "Other" mixes construction with hotels.

## Not scored yet

- **Competition:** needs company revenue shares (Sharadar). Census concentration for 2017 and 2022 is in `results/industry_run/concentration.csv` as context: concentration rose most in energy (+5.6 points of revenue held by the four largest firms) and finance (+3.9), and fell most in durables (−5.1) and telecom (−3.9).
- **Regulation:** QuantGov RegData isn't pulled yet.
- **Technology:** PatentsView isn't pulled yet.
- **Capacity** for telecom, retail, healthcare, finance, tech and other: no free measure covers most of these groups.

## Calls for you

1. **Capacity's direction.** The method says top-fifth capacity is a tailwind. The check leans the other way (not significant). Options: keep it as is with Low confidence (my pick until a 49-group or company test), or read top-fifth capacity as a late-cycle warning.
2. **Exposure review.** The v0 exposures are untested judgment. They could get the same review the macro scorecard got, once the check has more power.
3. **Next data.** Regulation (QuantGov, free bulk file) and technology (PatentsView) would fill two more factors; a 49-group run would test with less mixing, though Decisions keeps the industry pillar on 12 groups for now.

## Limits

- **Current data, not first prints.** BEA, Census and BLS revise their figures; the check uses today's numbers, which flatters it a little.
- **Publication lags are approximate:** BEA 3 months, Census 2 months, Fed capacity 1 month after the period ends.
- **French returns run to September 2026**, so the check stops there; readings run to October.
- **Splits of mixed BEA industries are rough** (for example drugs as 35% of chemicals output).
