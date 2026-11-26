# Rates test on broad sectors

Run date: 2026-11-26

**Events:** 266 Fed decision days from 1994-02-04 to 2026-09-16 (event calendar (data/events/fomc_decisions.csv)). Median 2-year yield move 4.0 bp; 117 days moved 5 bp or more.

**Measure:** sector return minus market return on the decision day, regressed on the change in the 2-year Treasury yield that day. Numbers are percentage points of relative return per +10 bp. A negative number means the sector does worse than the market when rates come in higher than expected (and better when they come in lower). Ranges are 95% bootstrap ranges over events. Value-weighted Ken French 12 industries.

The market itself moves -0.15% per +10 bp on these days (95% range -0.49 to +0.21).

## Sensitivity by sector

| Sector | Relative to market | 95% range | 1994-2007 | 2008-2015 | 2016 on | Without crisis days | Beta-adjusted | Equal-weighted | Rate news | Growth news | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Consumer durables (cars, appliances) | -0.31 | -0.53 to -0.08 | -0.15 | -0.40 | -0.43 | -0.28 | -0.21 | -0.20 | -0.31 | -0.05 | High |
| Retail, wholesale, restaurants | -0.20 | -0.34 to -0.08 | -0.16 | -0.31 | -0.20 | -0.15 | -0.21 | -0.13 | -0.17 | -0.29 | High |
| Other (construction, transport, services) | -0.11 | -0.22 to -0.02 | -0.11 | -0.15 | -0.10 | -0.11 | -0.12 | -0.06 | -0.17 | -0.05 | High |
| Telecom | -0.09 | -0.24 to +0.07 | +0.02 | -0.15 | -0.18 | -0.02 | -0.12 | -0.20 | -0.19 | -0.01 | Low |
| Manufacturing | -0.04 | -0.14 to +0.05 | -0.06 | -0.16 | +0.07 | -0.02 | -0.06 | -0.03 | -0.02 | -0.12 | Low |
| Chemicals | -0.03 | -0.22 to +0.14 | +0.03 | +0.04 | -0.18 | -0.01 | -0.11 | -0.24 | -0.12 | -0.11 | Low |
| Business equipment and tech | -0.02 | -0.22 to +0.16 | -0.15 | +0.18 | -0.01 | -0.10 | +0.09 | -0.13 | +0.14 | +0.02 | Low |
| Utilities | -0.01 | -0.23 to +0.23 | +0.26 | -0.31 | -0.13 | +0.04 | -0.11 | -0.01 | -0.26 | +0.16 | Low |
| Consumer staples (food, drink, apparel) | +0.01 | -0.17 to +0.20 | +0.09 | +0.09 | -0.14 | +0.04 | -0.09 | -0.06 | -0.10 | -0.07 | Low |
| Healthcare | +0.08 | -0.10 to +0.26 | +0.14 | +0.15 | -0.04 | +0.08 | +0.03 | -0.07 | +0.04 | +0.00 | Low |
| Finance | +0.09 | -0.19 to +0.34 | +0.06 | -0.20 | +0.30 | +0.17 | +0.05 | -0.01 | -0.10 | +0.32 | Low |
| Energy | +0.23 | +0.02 to +0.45 | +0.10 | +0.28 | +0.37 | +0.18 | +0.07 | +0.09 | +0.08 | +0.03 | High |

Periods hold 118 (1994-2007), 65 (2008-2015), 83 (2016 on) events. Rate news = yield and stocks moved in opposite directions (140 days); growth news = same direction (101 days); the rest moved under 1 bp. Both news columns are beta-adjusted, because the split uses the market's own move; treat them as a rough cut. Crisis days = 2008-2009 and March 2020. Beta-adjusted = sector return minus its expected move given the market and its beta over the prior year.

Confidence: High when the full-sample range excludes zero, the sign holds in all three periods and the out-of-sample half has the same sign; Medium for two of the three; Low otherwise.

## Out of sample

Slopes fitted on events before 2009-09-23 and checked on events from 2009-09-23 on. Rank agreement of sector slopes between the halves (Spearman): 0.27.

| Sector | First half | Second half | Second-half direction hit rate |
|---|---|---|---|
| Consumer durables (cars, appliances) | -0.26 | -0.37 | 55% of 115 |
| Retail, wholesale, restaurants | -0.22 | -0.18 | 54% of 116 |
| Other (construction, transport, services) | -0.12 | -0.10 | 60% of 115 |
| Telecom | -0.04 | -0.15 | 54% of 116 |
| Manufacturing | -0.09 | +0.02 | 56% of 114 |
| Chemicals | +0.06 | -0.17 | 42% of 113 |
| Business equipment and tech | -0.03 | -0.01 | 52% of 115 |
| Utilities | +0.15 | -0.25 | 43% of 115 |
| Consumer staples (food, drink, apparel) | +0.11 | -0.13 | 46% of 116 |
| Healthcare | +0.16 | -0.03 | 54% of 115 |
| Finance | -0.09 | +0.35 | 28% of 116 |
| Energy | +0.19 | +0.30 | 56% of 116 |

Hit rate = share of second-half events where the first-half slope got the sign of the sector's relative move right. 50% is a coin flip; most days other news moves sectors more than rates do.

## Compared with the v0 scorecard

The v0 scorecard covers consumer company types only, so four of the twelve groups can be compared. v0 score = net rates exposure if rates come in higher than expected (−5 to +5), averaged over the company types mapped to the group.

| Group | v0 company types (rates score) | v0 avg | Mapping | Raw slope (range) | Direction | Relative slope (range) | Relative to market | Confidence |
|---|---|---|---|---|---|---|---|---|
| Consumer durables (cars, appliances) | Automaker (-4) | -4.0 | good | -0.45 (-0.93 to +0.04) | unclear | -0.31 (-0.53 to -0.08) | agrees | High |
| Other (construction, transport, services) | Homebuilder (-5); Airline (-3) | -4.0 | loose | -0.26 (-0.61 to +0.13) | unclear | -0.11 (-0.22 to -0.02) | agrees | High |
| Retail, wholesale, restaurants | Home improvement retailer (-4); Restaurant chain (-3); Online marketplace (-3); Grocery chain (-1); Discount retailer (+0) | -2.2 | mixed | -0.35 (-0.69 to +0.01) | unclear | -0.20 (-0.34 to -0.08) | disagrees | High |
| Consumer staples (food, drink, apparel) | Packaged foods maker (-2); Luxury brand (-2) | -2.0 | fair | -0.14 (-0.38 to +0.12) | unclear | +0.01 (-0.17 to +0.20) | agrees (no worse than market) | Low |

Rank agreement between v0 averages and measured relative slopes across these groups (Spearman, 4 groups): 0.63.

Direction: does the group's own return fall when the 2-year yield rises, as v0's negative scores say? Relative: v0 −3 or below is read as "hurt more than a typical stock", above −3 as "hurt no more than a typical stock"; checked against the relative slope's range.

## Data notes

- 2020-03-15 (unscheduled_rate_change) is not a bond trading day; used 2020-03-16.
- 2013-05-01 is in the hand-entered list but not in the event calendar.
- 2017-02-01 is in the hand-entered list but not in the event calendar.
- 2017-11-01 is in the hand-entered list but not in the event calendar.
- 2018-08-01 is in the hand-entered list but not in the event calendar.
- 2019-05-01 is in the hand-entered list but not in the event calendar.
- 2003-09-15 is in the event calendar but not in the hand-entered list.
