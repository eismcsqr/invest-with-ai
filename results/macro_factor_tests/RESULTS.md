# Macro factor tests on broad sectors: inflation, spending and the dollar

Run date: 2026-11-26

All numbers are a sector's return minus the market's return (percentage points), per unit of the factor's surprise measure, with 95% bootstrap ranges. Value-weighted Ken French 12 industries unless noted. A positive number means the sector beats the market when the factor comes in higher than expected. Confidence: High when the range excludes zero, the sign holds in every period and the out-of-sample half has the same sign; Medium for two of three; Low otherwise. In check columns, * marks a range that excludes zero.

## Inflation

**Events:** 310 CPI release days from 1997-02-19 to 2026-09-11. **Surprise:** core CPI month-on-month as first published minus its average over the prior 12 months, per +0.1 point (typical size 0.13 point). It moves markets the way a real surprise should: correlation 0.25 with the 2-year yield move and 0.37 with the 5-year breakeven move that day (248 days since 2003).

The market itself moves -0.10% per +0.1 point (range -0.28 to +0.06).

Checks: *2y* = slope on the 2-year yield move per +10 bp, same days. *Breakeven* = slope on the 5-year breakeven move per +5 bp (2003 on). *Inflation beyond rates* = breakeven slope holding the 2-year yield move fixed, per +5 bp. News columns split days by whether stocks fell on a hot print (or rose on a cool one), and are beta-adjusted.

| Sector | Relative to market | 95% range | 1997-2007 | 2008-2015 | 2016 on | Without crisis | Beta-adjusted | Equal-weighted | Stocks fell on a hot print | Stocks rose on a hot print | 2y | Breakeven | Inflation beyond rates | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Business equipment and tech | -0.09 | -0.17 to -0.02 | -0.22 | -0.03 | -0.05 | -0.09 | -0.03 | -0.12 | -0.03 | -0.04 | +0.01 | -0.02 | +0.02 | High |
| Retail, wholesale, restaurants | -0.01 | -0.07 to +0.05 | +0.10 | -0.06 | -0.04 | -0.01 | -0.01 | -0.04 | -0.03 | +0.01 | -0.10 | -0.08 | -0.06 | Low |
| Utilities | -0.00 | -0.10 to +0.09 | +0.17 | -0.35 | +0.00 | +0.04 | -0.10 | +0.01 | -0.13 | -0.07 | -0.15 | -0.14 | -0.12 | Low |
| Other (construction, transport, services) | -0.00 | -0.05 to +0.06 | +0.05 | +0.11 | -0.04 | -0.02 | -0.01 | -0.02 | -0.02 | -0.01 | -0.09* | +0.05 | +0.10 | Low |
| Manufacturing | +0.01 | -0.05 to +0.08 | +0.12 | -0.04 | -0.02 | +0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.07 | +0.02 | +0.04 | Low |
| Chemicals | +0.02 | -0.04 to +0.08 | +0.13 | -0.11 | +0.01 | +0.04 | -0.03 | -0.03 | -0.04 | +0.00 | -0.04 | -0.09* | -0.12* | Low |
| Finance | +0.04 | -0.05 to +0.14 | -0.18 | +0.49 | +0.03 | -0.02 | +0.02 | +0.05 | +0.03 | -0.00 | +0.06 | +0.14 | +0.11 | Low |
| Telecom | +0.05 | -0.02 to +0.12 | +0.04 | -0.00 | +0.06 | +0.06 | +0.02 | -0.07 | +0.01 | +0.03 | +0.14 | -0.05 | -0.10* | Low |
| Consumer staples (food, drink, apparel) | +0.08 | -0.01 to +0.17 | +0.16 | -0.10 | +0.08 | +0.10 | +0.03 | +0.02 | +0.04 | +0.02 | +0.04 | -0.09 | -0.15* | Low |
| Energy | +0.12 | -0.01 to +0.25 | +0.45 | -0.30 | +0.09 | +0.16 | +0.06 | +0.06 | +0.11 | -0.03 | +0.18 | +0.19 | +0.16 | Low |
| Healthcare | +0.12 | +0.04 to +0.21 | +0.29 | -0.10 | +0.11 | +0.15 | +0.11 | -0.08 | +0.13 | +0.10 | -0.00 | -0.10 | -0.15* | Medium |
| Consumer durables (cars, appliances) | +0.13 | -0.03 to +0.32 | +0.03 | +0.29 | +0.13 | +0.09 | +0.15 | -0.03 | +0.14 | +0.17 | +0.05 | +0.25* | +0.29* | Medium |

Periods hold 118 (1997-2007), 82 (2008-2015), 110 (2016 on) events.

### Out of sample

Fitted before 2011-10-19, checked from 2011-10-19 on. Rank agreement of sector slopes between the halves (Spearman): 0.64.

| Sector | First half | Second half | Second-half direction hit rate |
|---|---|---|---|
| Business equipment and tech | -0.16 | -0.05 | 60% of 119 |
| Retail, wholesale, restaurants | +0.04 | -0.04 | 51% of 117 |
| Utilities | -0.02 | +0.00 | 53% of 118 |
| Other (construction, transport, services) | +0.08 | -0.03 | 48% of 116 |
| Manufacturing | +0.07 | -0.02 | 48% of 118 |
| Chemicals | +0.06 | +0.01 | 52% of 117 |
| Finance | +0.06 | +0.03 | 50% of 119 |
| Telecom | +0.02 | +0.07 | 56% of 117 |
| Consumer staples (food, drink, apparel) | +0.07 | +0.08 | 52% of 119 |
| Energy | +0.25 | +0.07 | 49% of 119 |
| Healthcare | +0.16 | +0.11 | 58% of 119 |
| Consumer durables (cars, appliances) | +0.14 | +0.13 | 54% of 117 |

### Compared with v0 (inflation)

| Group | v0 company types (score) | v0 avg | Mapping | v0 implies | Measured (range) | Result | Confidence |
|---|---|---|---|---|---|---|---|
| Other (construction, transport, services) | Homebuilder (-3); Airline (-2) | -2.5 | loose | worse than market | no clear difference: -0.00 (-0.05 to +0.06) | unclear | Low |
| Consumer durables (cars, appliances) | Automaker (-2) | -2.0 | good | about the market | no clear difference: +0.13 (-0.03 to +0.32) | agrees | Medium |
| Retail, wholesale, restaurants | Home improvement retailer (-1); Restaurant chain (-6); Online marketplace (-2); Grocery chain (+0); Discount retailer (+1) | -1.6 | mixed | about the market | no clear difference: -0.01 (-0.07 to +0.05) | agrees | Low |
| Consumer staples (food, drink, apparel) | Packaged foods maker (-2); Luxury brand (+0) | -1.0 | fair | better than market | no clear difference: +0.08 (-0.01 to +0.17) | unclear | Low |

Rank agreement between v0 averages and measured slopes (4 groups, Spearman): 0.00. v0 implies "worse than market" when the group's average is more than 0.5 below the average of all ten v0 types for this factor (-1.7), "better" when more than 0.5 above.

## Consumer spending

**Events:** 536 advance retail sales release days from 1976-06-10 to 2026-08-14. **Surprise:** the 2-year yield move that day, per +10 bp: a stronger print than expected pushes yields up. Median move 4.0 bp. The free data surprise (first print minus the prior 12-month average, 266 prints since 2001) is a weak stand-in for the consensus surprise: correlation with the yield move is only 0.08, so it is shown as a check only.

The market itself moves +0.05% per +10 bp on these days (range -0.10 to +0.21).

Because a yield jump on these days is partly rate news, the table also shows the same slope on Fed decision days (270 days, the rates test's events) and the difference, *spending beyond rates*: how much better a sector does on a strong spending day than on a hawkish Fed day with the same yield move. *Data surprise* = slope on the first-print surprise per +0.5 point. Growth news = yield and stocks moved the same way; tightening news = opposite ways (beta-adjusted).

| Sector | Relative to market | 95% range | 1976-1993 | 1994-2007 | 2008-2015 | 2016 on | Without crisis | Beta-adjusted | Equal-weighted | Growth news | Tightening news | Fed days | Spending beyond rates | Data surprise | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Healthcare | -0.11 | -0.19 to -0.04 | -0.01 | -0.30 | -0.64 | -0.25 | -0.09 | -0.08 | -0.00 | -0.16 | -0.02 | +0.09 | -0.20 | -0.01 | High |
| Utilities | -0.10 | -0.18 to -0.01 | -0.04 | -0.19 | -0.14 | -0.34 | -0.12 | -0.08 | -0.04 | -0.06 | -0.10 | -0.01 | -0.08 | -0.01 | High |
| Telecom | -0.02 | -0.12 to +0.07 | +0.03 | -0.07 | -0.05 | -0.41 | -0.02 | -0.04 | +0.08 | -0.01 | -0.06 | -0.09 | +0.06 | -0.01 | Low |
| Consumer staples (food, drink, apparel) | -0.02 | -0.08 to +0.04 | +0.05 | -0.11 | -0.34 | -0.15 | -0.01 | +0.02 | +0.04 | +0.05 | -0.01 | +0.01 | -0.03 | +0.00 | Low |
| Chemicals | -0.01 | -0.06 to +0.04 | -0.01 | +0.07 | -0.08 | -0.10 | -0.02 | +0.02 | +0.06 | +0.05 | +0.00 | -0.03 | +0.02 | -0.00 | Low |
| Finance | +0.00 | -0.04 to +0.05 | -0.01 | -0.15 | +0.19 | +0.24 | -0.00 | -0.04 | +0.02 | +0.03 | -0.08 | +0.09 | -0.08 | +0.01 | Low |
| Business equipment and tech | +0.01 | -0.06 to +0.08 | -0.03 | +0.25 | -0.19 | -0.02 | +0.02 | +0.02 | +0.03 | -0.04 | +0.06 | -0.02 | +0.03 | -0.00 | Low |
| Energy | +0.03 | -0.11 to +0.18 | -0.01 | -0.11 | +0.72 | +0.26 | +0.00 | +0.03 | +0.07 | +0.02 | +0.03 | +0.23 | -0.20 | +0.00 | Low |
| Other (construction, transport, services) | +0.05 | +0.01 to +0.10 | +0.05 | +0.07 | +0.06 | +0.01 | +0.06 | +0.05 | +0.04 | +0.07 | +0.04 | -0.11* | +0.16* | +0.01 | High |
| Manufacturing | +0.06 | +0.02 to +0.11 | +0.01 | +0.13 | +0.43 | +0.17 | +0.05 | +0.05 | +0.08 | +0.10 | +0.01 | -0.04 | +0.10 | +0.02* | High |
| Retail, wholesale, restaurants | +0.07 | +0.02 to +0.12 | +0.05 | +0.25 | -0.00 | -0.10 | +0.08 | +0.08 | +0.07 | +0.10 | +0.07 | -0.21* | +0.28* | +0.00 | Medium |
| Consumer durables (cars, appliances) | +0.09 | +0.01 to +0.17 | +0.03 | +0.28 | +0.28 | +0.10 | +0.10 | +0.07 | +0.08 | +0.08 | +0.07 | -0.31* | +0.40* | +0.00 | High |

Periods hold 200 (1976-1993), 142 (1994-2007), 85 (2008-2015), 109 (2016 on) events.

### Out of sample

Fitted before 2001-05-11, checked from 2001-05-11 on. Rank agreement of sector slopes between the halves (Spearman): 0.37.

| Sector | First half | Second half | Second-half direction hit rate |
|---|---|---|---|
| Healthcare | -0.03 | -0.40 | 65% of 229 |
| Utilities | -0.05 | -0.27 | 57% of 230 |
| Telecom | +0.01 | -0.14 | 48% of 229 |
| Consumer staples (food, drink, apparel) | +0.02 | -0.15 | 48% of 227 |
| Chemicals | -0.01 | -0.03 | 53% of 230 |
| Finance | -0.04 | +0.17 | 43% of 229 |
| Business equipment and tech | +0.01 | -0.00 | 48% of 227 |
| Energy | -0.01 | +0.15 | 46% of 229 |
| Other (construction, transport, services) | +0.05 | +0.05 | 52% of 227 |
| Manufacturing | +0.01 | +0.22 | 56% of 226 |
| Retail, wholesale, restaurants | +0.07 | +0.08 | 51% of 229 |
| Consumer durables (cars, appliances) | +0.06 | +0.20 | 53% of 227 |

### Compared with v0 (spending)

On the retail-day slope:

| Group | v0 company types (score) | v0 avg | Mapping | v0 implies | Measured (range) | Result | Confidence |
|---|---|---|---|---|---|---|---|
| Consumer staples (food, drink, apparel) | Packaged foods maker (-1); Luxury brand (+2) | +0.5 | fair | worse than market | no clear difference: -0.02 (-0.08 to +0.04) | unclear | Low |
| Retail, wholesale, restaurants | Home improvement retailer (+3); Restaurant chain (+3); Online marketplace (+3); Grocery chain (-1); Discount retailer (+0) | +1.6 | mixed | about the market | better than market: +0.07 (+0.02 to +0.12) | disagrees | Medium |
| Other (construction, transport, services) | Homebuilder (+3); Airline (+4) | +3.5 | loose | better than market | better than market: +0.05 (+0.01 to +0.10) | agrees | High |
| Consumer durables (cars, appliances) | Automaker (+4) | +4.0 | good | better than market | better than market: +0.09 (+0.01 to +0.17) | agrees | High |

Rank agreement between v0 averages and measured slopes (4 groups, Spearman): 0.80. v0 implies "worse than market" when the group's average is more than 0.5 below the average of all ten v0 types for this factor (+2.0), "better" when more than 0.5 above.

On spending beyond rates:

| Group | v0 company types (score) | v0 avg | Mapping | v0 implies | Measured (range) | Result | Confidence |
|---|---|---|---|---|---|---|---|
| Consumer staples (food, drink, apparel) | Packaged foods maker (-1); Luxury brand (+2) | +0.5 | fair | worse than market | no clear difference: -0.03 (-0.22 to +0.15) | unclear | Low |
| Retail, wholesale, restaurants | Home improvement retailer (+3); Restaurant chain (+3); Online marketplace (+3); Grocery chain (-1); Discount retailer (+0) | +1.6 | mixed | about the market | better than market: +0.28 (+0.13 to +0.43) | disagrees | Medium |
| Other (construction, transport, services) | Homebuilder (+3); Airline (+4) | +3.5 | loose | better than market | better than market: +0.16 (+0.06 to +0.28) | agrees | High |
| Consumer durables (cars, appliances) | Automaker (+4) | +4.0 | good | better than market | better than market: +0.40 (+0.17 to +0.63) | agrees | High |

Rank agreement between v0 averages and measured slopes (4 groups, Spearman): 0.80. v0 implies "worse than market" when the group's average is more than 0.5 below the average of all ten v0 types for this factor (+2.0), "better" when more than 0.5 above.

## US dollar

**Periods:** 380 months from 1995-02 to 2026-09. **Measure:** percent change in the Fed's broad trade-weighted dollar index over the month, per +1% (typical month 1.6%). The dollar has no release day, so this measures sensitivity to dollar moves, not to dollar surprises. The old index (1995 to 2005) and the current one (2006 on) are each used only for changes within their own span.

The market itself moves -1.42% per +1% dollar move (range -1.68 to -1.12). Because the whole market moves this much with the dollar, the simple sector-minus-market slope mostly rewards low-beta sectors (utilities, healthcare, staples) for falling less than the market in strong-dollar months. So the headline here is different from the other factors: the dollar coefficient in a fit of the sector's own return on the dollar move and the market return together, i.e. the dollar's effect holding the market's move fixed. The simple slope is kept as a check.

Checks: *Simple relative* = sector minus market, as for the other factors. *Weekly* = headline method on 1656 weeks. *Rates held fixed* = also holding the month's 2-year yield move fixed. *Big months* = only months with a move of 2% or more (64 months). Beta-adjusted uses each sector's beta over the prior 60 months instead of the full-sample fit. Risk-off months = dollar and stocks moved opposite ways (beta-adjusted).

| Sector | Holding the market fixed | 95% range | 1995-2007 | 2008-2015 | 2016 on | Without crisis | Beta-adjusted | Equal-weighted | Risk-off (dollar and stocks opposite) | Risk-on (dollar and stocks together) | Simple relative | Weekly | Rates held fixed | Big months | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Energy | -0.76 | -1.18 to -0.36 | -1.05 | -0.96 | -0.01 | -0.73 | -0.33 | -1.30 | -0.19 | -0.76 | -0.34 | -0.80* | -0.95* | +0.24 | High |
| Chemicals | -0.51 | -0.72 to -0.32 | -0.30 | -0.30 | -0.60 | -0.49 | -0.26 | -0.59 | -0.13 | -0.50 | +0.00 | -0.26* | -0.49* | -0.21 | High |
| Utilities | -0.39 | -0.65 to -0.14 | -0.30 | -0.07 | -0.52 | -0.42 | -0.18 | -0.31 | -0.14 | -0.19 | +0.53* | -0.43* | -0.37* | -0.11 | High |
| Manufacturing | -0.36 | -0.55 to -0.16 | -0.31 | -0.16 | -0.27 | -0.33 | -0.13 | -0.38 | -0.07 | -0.30 | -0.45* | -0.36* | -0.42* | -0.06 | High |
| Consumer staples (food, drink, apparel) | -0.36 | -0.56 to -0.15 | -0.12 | -0.15 | -0.64 | -0.34 | -0.18 | -0.29 | -0.07 | -0.42 | +0.33* | -0.19* | -0.32* | -0.32 | High |
| Other (construction, transport, services) | -0.24 | -0.37 to -0.11 | -0.07 | -0.07 | -0.42 | -0.22 | -0.14 | -0.21 | -0.11 | -0.23 | -0.23* | -0.15* | -0.26* | -0.03 | High |
| Finance | -0.05 | -0.29 to +0.19 | +0.23 | +0.11 | +0.03 | +0.04 | +0.08 | -0.11 | +0.05 | +0.20 | -0.11 | +0.02 | -0.06 | +0.23 | Low |
| Telecom | -0.02 | -0.29 to +0.22 | +0.42 | +0.08 | -0.65 | -0.06 | -0.03 | -0.08 | -0.01 | +0.04 | +0.13 | -0.10 | +0.02 | +0.28 | Low |
| Healthcare | -0.00 | -0.19 to +0.19 | +0.40 | +0.02 | -0.29 | +0.02 | +0.05 | -0.00 | +0.07 | +0.19 | +0.49* | +0.11 | +0.08 | -0.08 | Low |
| Consumer durables (cars, appliances) | +0.11 | -0.32 to +0.56 | +0.31 | +0.12 | +0.69 | +0.16 | +0.18 | -0.32 | +0.19 | +0.40 | -0.53* | -0.30* | +0.02 | -0.09 | Low |
| Retail, wholesale, restaurants | +0.23 | +0.03 to +0.42 | +0.21 | +0.36 | +0.17 | +0.22 | +0.18 | -0.13 | +0.15 | +0.25 | +0.35* | +0.30* | +0.25* | +0.04 | High |
| Business equipment and tech | +0.45 | +0.18 to +0.72 | +0.09 | +0.27 | +0.29 | +0.36 | +0.18 | +0.31 | +0.14 | +0.18 | -0.15 | +0.28* | +0.43* | +0.01 | High |

Periods hold 155 (1995-2007), 96 (2008-2015), 129 (2016 on) months.

### Out of sample

Fitted before 2010-12, checked from 2010-12 on. Rank agreement of sector slopes between the halves (Spearman): 0.43.

| Sector | First half | Second half | Second-half direction hit rate |
|---|---|---|---|
| Energy | -0.96 | -0.42 | 60% of 178 |
| Chemicals | -0.49 | -0.50 | 57% of 178 |
| Utilities | -0.34 | -0.42 | 54% of 178 |
| Manufacturing | -0.43 | -0.27 | 54% of 177 |
| Consumer staples (food, drink, apparel) | -0.27 | -0.44 | 56% of 178 |
| Other (construction, transport, services) | -0.17 | -0.31 | 54% of 178 |
| Finance | -0.09 | +0.01 | 47% of 178 |
| Telecom | +0.39 | -0.51 | 43% of 178 |
| Healthcare | +0.11 | -0.09 | 50% of 177 |
| Consumer durables (cars, appliances) | -0.08 | +0.46 | 49% of 178 |
| Retail, wholesale, restaurants | +0.21 | +0.29 | 54% of 178 |
| Business equipment and tech | +0.52 | +0.24 | 57% of 178 |

### Compared with v0 (dollar)

| Group | v0 company types (score) | v0 avg | Mapping | v0 implies | Measured (range) | Result | Confidence |
|---|---|---|---|---|---|---|---|
| Consumer staples (food, drink, apparel) | Packaged foods maker (-2); Luxury brand (-2) | -2.0 | fair | worse than market | worse than market: -0.36 (-0.56 to -0.15) | agrees | High |
| Consumer durables (cars, appliances) | Automaker (-1) | -1.0 | good | worse than market | no clear difference: +0.11 (-0.32 to +0.56) | unclear | Low |
| Other (construction, transport, services) | Homebuilder (+1); Airline (-1) | +0.0 | loose | about the market | worse than market: -0.24 (-0.37 to -0.11) | disagrees | High |
| Retail, wholesale, restaurants | Home improvement retailer (+1); Restaurant chain (-1); Online marketplace (-2); Grocery chain (+1); Discount retailer (+2) | +0.2 | mixed | better than market | better than market: +0.23 (+0.03 to +0.42) | agrees | High |

Rank agreement between v0 averages and measured slopes (4 groups, Spearman): 0.80. v0 implies "worse than market" when the group's average is more than 0.5 below the average of all ten v0 types for this factor (-0.4), "better" when more than 0.5 above.

## Data notes

- 78 CPI release days that fell on the same day as retail sales, PCE or a Fed decision were left out.
- 73 retail sales release days that fell on the same day as CPI, PCE or a Fed decision were left out.
