# Rates test on detailed industry groups

Run date: 2026-11-26

**Events:** 270 Fed decision days from 1994-02-04 to 2026-09-16 (event calendar (data/events/fomc_decisions.csv)). Median 2-year yield move 4.0 bp; 117 days moved 5 bp or more.

**Measure:** sector return minus market return on the decision day, regressed on the change in the 2-year Treasury yield that day. Numbers are percentage points of relative return per +10 bp. A negative number means the sector does worse than the market when rates come in higher than expected (and better when they come in lower). Ranges are 95% bootstrap ranges over events. Value-weighted Ken French 49 industries.

The market itself moves -0.15% per +10 bp on these days (95% range -0.48 to +0.23).

## Sensitivity by sector

| Sector | Relative to market | 95% range | 1994-2007 | 2008-2015 | 2016 on | Without crisis days | Beta-adjusted | Equal-weighted | Rate news | Growth news | Confidence | Passes false-discovery check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Precious metals | -0.77 | -1.45 to -0.06 | +0.09 | -0.88 | -1.79 | -0.60 | -0.92 | -0.80 | -1.27 | -0.33 | Medium | no |
| Retail | -0.28 | -0.47 to -0.10 | -0.24 | -0.33 | -0.30 | -0.23 | -0.27 | -0.22 | -0.19 | -0.41 | High | yes |
| Rubber and plastics | -0.27 | -0.42 to -0.13 | -0.23 | -0.37 | -0.27 | -0.24 | -0.29 | +0.05 | -0.40 | -0.12 | High | yes |
| Entertainment | -0.27 | -0.56 to +0.02 | -0.18 | -0.63 | -0.13 | -0.20 | -0.21 | -0.13 | -0.21 | -0.19 | Medium | no |
| Packaging | -0.26 | -0.46 to -0.06 | -0.06 | -0.43 | -0.42 | -0.20 | -0.31 | -0.14 | -0.37 | -0.22 | High | yes |
| Autos and parts | -0.25 | -0.52 to -0.01 | -0.09 | -0.25 | -0.45 | -0.25 | -0.16 | -0.23 | -0.24 | -0.01 | High | no |
| Construction | -0.25 | -0.60 to +0.10 | -0.23 | -0.17 | -0.34 | -0.31 | -0.20 | -0.23 | -0.22 | -0.19 | Medium | no |
| Steel | -0.23 | -0.43 to -0.04 | -0.10 | -0.33 | -0.34 | -0.26 | -0.21 | -0.11 | -0.24 | -0.16 | High | no |
| Metal mining | -0.22 | -0.52 to +0.08 | -0.04 | +0.00 | -0.62 | -0.32 | -0.28 | -0.27 | -0.25 | -0.32 | Low | no |
| Toys and recreation | -0.21 | -0.43 to +0.01 | +0.01 | -0.39 | -0.40 | -0.19 | -0.22 | -0.17 | -0.31 | -0.06 | Low | no |
| Textiles | -0.20 | -0.51 to +0.10 | +0.08 | -0.53 | -0.34 | -0.08 | -0.19 | -0.04 | -0.29 | -0.03 | Low | no |
| Apparel | -0.20 | -0.45 to +0.03 | -0.19 | -0.56 | +0.02 | -0.10 | -0.22 | -0.10 | -0.19 | -0.28 | Low | no |
| Electrical equipment | -0.17 | -0.34 to +0.03 | -0.19 | -0.40 | +0.03 | -0.08 | -0.13 | -0.05 | -0.02 | -0.30 | Low | no |
| Business supplies | -0.14 | -0.32 to +0.02 | -0.04 | -0.16 | -0.27 | -0.09 | -0.23 | -0.23 | -0.25 | -0.21 | Medium | no |
| Beer and liquor | -0.12 | -0.34 to +0.08 | -0.02 | -0.03 | -0.32 | -0.11 | -0.25 | -0.25 | -0.33 | -0.07 | Medium | no |
| Soft drinks | -0.12 | -0.43 to +0.20 | +0.06 | -0.30 | -0.19 | +0.02 | -0.21 | -0.04 | -0.15 | -0.30 | Low | no |
| Fabricated products | -0.12 | -0.45 to +0.20 | -0.00 | -0.19 | -0.26 | -0.02 | -0.13 | +0.08 | -0.12 | -0.17 | Medium | no |
| Building materials | -0.11 | -0.30 to +0.06 | +0.03 | -0.28 | -0.17 | -0.06 | -0.14 | -0.05 | -0.18 | -0.07 | Low | no |
| Household goods | -0.10 | -0.31 to +0.10 | -0.09 | +0.04 | -0.22 | -0.07 | -0.19 | -0.14 | -0.25 | -0.08 | Low | no |
| Measuring equipment | -0.09 | -0.29 to +0.10 | -0.08 | +0.08 | -0.24 | -0.10 | -0.04 | -0.13 | -0.01 | -0.09 | Low | no |
| Other | -0.09 | -0.26 to +0.07 | -0.19 | -0.19 | +0.12 | -0.03 | -0.11 | -0.01 | -0.14 | -0.08 | Low | no |
| Telecom | -0.09 | -0.24 to +0.07 | +0.01 | -0.15 | -0.17 | -0.02 | -0.12 | -0.20 | -0.18 | -0.02 | Low | no |
| Restaurants and hotels | -0.07 | -0.24 to +0.10 | +0.01 | -0.52 | +0.15 | +0.04 | -0.08 | -0.05 | -0.19 | +0.13 | Low | no |
| Business services | -0.06 | -0.20 to +0.05 | +0.02 | -0.08 | -0.16 | -0.08 | -0.06 | +0.00 | -0.13 | +0.04 | Low | no |
| Software | -0.06 | -0.25 to +0.13 | -0.11 | +0.15 | -0.14 | -0.15 | +0.07 | -0.20 | +0.06 | +0.08 | Low | no |
| Machinery | -0.04 | -0.19 to +0.12 | -0.14 | -0.06 | +0.11 | -0.04 | -0.02 | +0.01 | +0.07 | -0.16 | Low | no |
| Transportation | -0.03 | -0.24 to +0.13 | -0.09 | +0.01 | -0.01 | -0.06 | -0.07 | -0.11 | -0.07 | -0.06 | Low | no |
| Printing and publishing | -0.02 | -0.19 to +0.14 | +0.07 | +0.07 | -0.19 | +0.04 | -0.05 | +0.04 | +0.02 | -0.16 | Low | no |
| Medical equipment | -0.02 | -0.16 to +0.13 | +0.15 | -0.04 | -0.21 | +0.01 | -0.05 | -0.05 | -0.11 | +0.03 | Low | no |
| Utilities | -0.01 | -0.24 to +0.22 | +0.26 | -0.31 | -0.14 | +0.03 | -0.12 | -0.01 | -0.27 | +0.15 | Low | no |
| Real estate | +0.00 | -0.28 to +0.28 | +0.40 | -0.44 | -0.20 | +0.07 | -0.05 | -0.13 | -0.18 | +0.17 | Low | no |
| Chemicals | +0.00 | -0.20 to +0.17 | +0.11 | -0.04 | -0.11 | +0.01 | -0.05 | -0.26 | -0.03 | -0.10 | Low | no |
| Aircraft | +0.01 | -0.26 to +0.26 | +0.04 | -0.14 | +0.07 | -0.01 | -0.03 | +0.05 | -0.13 | +0.14 | Low | no |
| Food products | +0.02 | -0.23 to +0.28 | +0.08 | +0.12 | -0.14 | +0.05 | -0.10 | -0.03 | -0.10 | -0.09 | Low | no |
| Chips and electronics | +0.02 | -0.26 to +0.25 | -0.17 | +0.20 | +0.15 | -0.04 | +0.16 | -0.11 | +0.28 | -0.03 | Low | no |
| Coal | +0.05 | -0.50 to +0.58 | +0.47 | +0.05 | -0.45 | +0.15 | -0.01 | -0.07 | +0.41 | -0.76 | Low | no |
| Computers | +0.06 | -0.18 to +0.29 | -0.25 | +0.30 | +0.28 | -0.00 | +0.15 | +0.07 | +0.21 | +0.06 | Low | no |
| Insurance | +0.06 | -0.20 to +0.30 | +0.15 | -0.49 | +0.33 | +0.19 | -0.01 | -0.07 | -0.17 | +0.25 | Low | no |
| Wholesale | +0.07 | -0.06 to +0.19 | +0.20 | -0.11 | +0.03 | +0.12 | +0.00 | -0.04 | -0.02 | +0.05 | Low | no |
| Trading and finance | +0.07 | -0.26 to +0.44 | -0.06 | +0.08 | +0.20 | +0.10 | +0.10 | +0.08 | -0.05 | +0.35 | Low | no |
| Personal services | +0.08 | -0.14 to +0.29 | +0.03 | +0.48 | -0.16 | -0.05 | +0.08 | +0.02 | -0.16 | +0.48 | Low | no |
| Banks | +0.08 | -0.26 to +0.38 | +0.03 | -0.18 | +0.32 | +0.16 | +0.05 | -0.00 | -0.11 | +0.33 | Low | no |
| Drugs | +0.11 | -0.10 to +0.32 | +0.14 | +0.20 | +0.00 | +0.11 | +0.04 | -0.09 | +0.07 | -0.01 | Low | no |
| Healthcare services | +0.15 | -0.06 to +0.39 | +0.20 | -0.01 | +0.22 | +0.14 | +0.12 | +0.07 | +0.05 | +0.22 | Low | no |
| Tobacco | +0.20 | -0.10 to +0.50 | +0.33 | +0.30 | -0.04 | +0.20 | +0.10 | +0.23 | +0.10 | +0.11 | Low | no |
| Oil and gas | +0.22 | -0.01 to +0.44 | +0.09 | +0.29 | +0.36 | +0.17 | +0.06 | +0.09 | +0.06 | +0.05 | Medium | no |
| Defense | +0.25 | -0.06 to +0.63 | +0.54 | -0.24 | +0.22 | +0.38 | +0.14 | +0.16 | +0.27 | -0.04 | Low | no |
| Ships and railcars | +0.29 | +0.06 to +0.54 | +0.54 | +0.15 | +0.07 | +0.32 | +0.24 | -0.01 | +0.34 | +0.09 | High | no |
| Agriculture | +0.33 | -0.02 to +0.70 | +0.23 | +0.66 | +0.24 | +0.20 | +0.17 | +0.12 | +0.19 | +0.13 | Medium | no |

Periods hold 117 (1994-2007), 66 (2008-2015), 87 (2016 on) events. Rate news = yield and stocks moved in opposite directions (141 days); growth news = same direction (103 days); the rest moved under 1 bp. Both news columns are beta-adjusted, because the split uses the market's own move; treat them as a rough cut. Crisis days = 2008-2009 and March 2020. Beta-adjusted = sector return minus its expected move given the market and its beta over the prior year.

Confidence: High when the full-sample range excludes zero, the sign holds in all three periods and the out-of-sample half has the same sign; Medium for two of the three; Low otherwise.

False-discovery check: Benjamini-Hochberg at 10% across all 49 groups, using bootstrap p-values for the relative slope. "yes" means the result is unlikely to be one of the few that clear a 95% range by luck when many groups are tested at once.

## Out of sample

Slopes fitted on events before 2010-01-27 and checked on events from 2010-01-27 on. Rank agreement of sector slopes between the halves (Spearman): 0.16.

| Sector | First half | Second half | Second-half direction hit rate |
|---|---|---|---|
| Precious metals | -0.08 | -1.80 | 68% of 117 |
| Retail | -0.28 | -0.27 | 61% of 116 |
| Rubber and plastics | -0.28 | -0.26 | 63% of 115 |
| Entertainment | -0.37 | -0.11 | 52% of 117 |
| Packaging | -0.15 | -0.45 | 52% of 116 |
| Autos and parts | -0.17 | -0.37 | 52% of 117 |
| Construction | -0.21 | -0.30 | 60% of 116 |
| Steel | -0.15 | -0.36 | 53% of 116 |
| Metal mining | +0.05 | -0.65 | 38% of 117 |
| Toys and recreation | -0.16 | -0.31 | 58% of 116 |
| Textiles | -0.18 | -0.24 | 53% of 115 |
| Apparel | -0.34 | +0.01 | 51% of 117 |
| Electrical equipment | -0.28 | +0.01 | 55% of 117 |
| Business supplies | -0.06 | -0.27 | 63% of 116 |
| Beer and liquor | -0.02 | -0.29 | 58% of 117 |
| Soft drinks | -0.07 | -0.18 | 57% of 116 |
| Fabricated products | -0.06 | -0.22 | 54% of 117 |
| Building materials | -0.10 | -0.13 | 62% of 117 |
| Household goods | -0.03 | -0.20 | 53% of 116 |
| Measuring equipment | -0.01 | -0.21 | 59% of 116 |
| Other | -0.21 | +0.10 | 47% of 117 |
| Telecom | -0.05 | -0.14 | 54% of 117 |
| Restaurants and hotels | -0.20 | +0.13 | 49% of 116 |
| Business services | -0.01 | -0.14 | 51% of 116 |
| Software | -0.01 | -0.14 | 52% of 117 |
| Machinery | -0.11 | +0.07 | 59% of 116 |
| Transportation | -0.02 | -0.07 | 54% of 117 |
| Printing and publishing | +0.02 | -0.08 | 55% of 116 |
| Medical equipment | +0.07 | -0.14 | 45% of 114 |
| Utilities | +0.15 | -0.26 | 42% of 116 |
| Real estate | +0.13 | -0.20 | 49% of 117 |
| Chemicals | +0.08 | -0.12 | 39% of 117 |
| Aircraft | +0.00 | +0.02 | 48% of 117 |
| Food products | +0.12 | -0.13 | 52% of 116 |
| Chips and electronics | -0.07 | +0.17 | 42% of 117 |
| Coal | +0.41 | -0.50 | 46% of 117 |
| Computers | -0.08 | +0.27 | 42% of 114 |
| Insurance | -0.10 | +0.30 | 35% of 116 |
| Wholesale | +0.10 | +0.02 | 48% of 117 |
| Trading and finance | -0.08 | +0.28 | 43% of 115 |
| Personal services | +0.19 | -0.08 | 49% of 116 |
| Banks | -0.12 | +0.39 | 32% of 117 |
| Drugs | +0.18 | -0.00 | 55% of 117 |
| Healthcare services | +0.14 | +0.19 | 54% of 117 |
| Tobacco | +0.36 | -0.04 | 46% of 117 |
| Oil and gas | +0.18 | +0.29 | 56% of 115 |
| Defense | +0.32 | +0.14 | 57% of 115 |
| Ships and railcars | +0.44 | +0.06 | 49% of 116 |
| Agriculture | +0.43 | +0.18 | 46% of 115 |

Hit rate = share of second-half events where the first-half slope got the sign of the sector's relative move right. 50% is a coin flip; most days other news moves sectors more than rates do.

## Compared with the v0 scorecard

The v0 scorecard covers consumer company types only, so 7 of the 49 groups can be compared. v0 score = net rates exposure if rates come in higher than expected (−5 to +5), averaged over the company types mapped to the group.

| Group | v0 company types (rates score) | v0 avg | Mapping | Raw slope (range) | Direction | Relative slope (range) | Relative to market | Confidence |
|---|---|---|---|---|---|---|---|---|
| Construction | Homebuilder (-5) | -5.0 | fair | -0.40 (-0.94 to +0.18) | unclear | -0.25 (-0.60 to +0.10) | unclear | Medium |
| Autos and parts | Automaker (-4) | -4.0 | good | -0.40 (-0.92 to +0.14) | unclear | -0.25 (-0.52 to -0.01) | agrees | High |
| Restaurants and hotels | Restaurant chain (-3) | -3.0 | good | -0.22 (-0.57 to +0.20) | unclear | -0.07 (-0.24 to +0.10) | unclear | Low |
| Transportation | Airline (-3) | -3.0 | fair | -0.18 (-0.59 to +0.22) | unclear | -0.03 (-0.24 to +0.13) | unclear | Low |
| Food products | Packaged foods maker (-2) | -2.0 | good | -0.13 (-0.40 to +0.13) | unclear | +0.02 (-0.23 to +0.28) | agrees (no worse than market) | Low |
| Apparel | Luxury brand (-2) | -2.0 | fair | -0.35 (-0.79 to +0.12) | unclear | -0.20 (-0.45 to +0.03) | agrees (no worse than market) | Low |
| Retail | Home improvement retailer (-4); Online marketplace (-3); Grocery chain (-1); Discount retailer (+0) | -2.0 | mixed | -0.43 (-0.77 to -0.04) | agrees | -0.28 (-0.47 to -0.10) | disagrees | High |

Rank agreement between v0 averages and measured relative slopes across these groups (Spearman, 7 groups): 0.21.

Direction: does the group's own return fall when the 2-year yield rises, as v0's negative scores say? Relative: v0 −3 or below is read as "hurt more than a typical stock", above −3 as "hurt no more than a typical stock"; checked against the relative slope's range.

## Data notes

- 2020-03-15 (unscheduled_rate_change) is not a bond trading day; used 2020-03-16.
