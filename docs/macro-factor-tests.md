# Inflation, spending and dollar tests on broad sectors (free version)

Run on 2026-11-26 on data already in the repo. Full tables: [`results/macro_factor_tests/RESULTS.md`](../results/macro_factor_tests/RESULTS.md). Companion to the [rates test](rates-test.md), with the same structure and checks.

## Headline

- **Spending: v0 holds.** On strong retail sales days, consumer durables, retail, manufacturing and the "Other" group (homebuilders, airlines, transport) beat the market, and healthcare and utilities lag. That is v0's ranking (rank agreement 0.8 across the four groups it covers). Retail again looks more cyclical than v0's average for its types, for the same reason as in the rates test: grocery and discount types pull v0's average down.
- **Dollar: v0 half holds.** Holding the market's own move fixed, a stronger dollar hurts energy, chemicals, manufacturing, consumer staples, utilities and "Other", and helps retail and tech. v0 is right that packaged foods and luxury (staples) are hurt and that importing retailers gain. It misses that the "Other" group (transport, homebuilders) is hurt, and the automaker effect is unclear.
- **Inflation: little to confirm.** Sector reactions to hotter-than-trend core CPI prints are small. Only two are clear: healthcare beats the market and tech lags. v0's strongest inflation calls (restaurants −6, homebuilders −3, airlines −2) don't show up at sector level, and consumer durables lean the other way (beat the market on hot prints).

## Results for the four groups v0 covers

Numbers are percentage points of return per unit of the factor's measure, with a 95% range. Spending and inflation are relative to the market; the dollar holds the market's move fixed (see "How it works").

| Group | Spending: retail-day slope per +10 bp | v0 spending | Dollar: per +1% | v0 dollar | Inflation: per +0.1 point core CPI surprise | v0 inflation |
|---|---|---|---|---|---|---|
| Consumer durables | +0.09 (+0.01 to +0.17), High | Automaker +4: **agrees** | +0.11 (−0.32 to +0.56), Low | Automaker −1: unclear | +0.13 (−0.03 to +0.32), Medium | Automaker −2: unclear, leans opposite |
| Other | +0.05 (+0.01 to +0.10), High | Homebuilder +3, Airline +4: **agrees** | −0.24 (−0.37 to −0.11), High | avg 0: **disagrees**, measured hurt | −0.00 (−0.05 to +0.06), Low | avg −2.5: unclear |
| Retail, wholesale, restaurants | +0.07 (+0.02 to +0.12), Medium | avg +1.6 (below the v0 average): **disagrees**, more cyclical than v0 implies | +0.23 (+0.03 to +0.42), High | avg +0.2: **agrees** | −0.01 (−0.07 to +0.05), Low | avg −1.6: agrees (no clear difference) |
| Consumer staples | −0.02 (−0.08 to +0.04), Low | avg +0.5: unclear | −0.36 (−0.56 to −0.15), High | avg −2: **agrees** | +0.08 (−0.01 to +0.17), Low | avg −1: unclear |

"Agrees" reads v0 relative to the average of its ten types for that factor: more than 0.5 below means "worse than a typical stock", more than 0.5 above means "better", in between means "about the same". Confidence follows the rates test: High when the range excludes zero, the sign holds in every period and out of sample.

## Beyond the v0 groups

- **Spending:** healthcare (−0.11) and utilities (−0.10) lag the market on strong spending days, with high confidence. Holding the rate effect aside (comparing with Fed days), durables (+0.40), retail (+0.28) and "Other" (+0.16) gain even more.
- **Dollar:** energy (−0.76) and chemicals (−0.51) are hit hardest, as commodities priced in dollars fall. Tech gains (+0.45), which doesn't fit its large overseas sales; read it as a gap to explain, not a finding.
- **Inflation:** energy leans positive (+0.12, low confidence). Holding the 2-year yield move fixed, a higher breakeven hurts staples, healthcare, telecom and chemicals and helps durables, which hints that cost pressure shows up once rate news is set aside.

## How it works

- **Inflation surprise:** CPI release days, 1997 to 2026 (310 days). Surprise = core CPI month-on-month as first published minus its average over the prior 12 months, from the event calendar's first prints. Consensus forecasts are paid data; this free stand-in does carry news, since it moves the 2-year yield (correlation 0.25) and the 5-year breakeven (0.37) on release day. Core, not headline, because headline CPI mostly reflects gasoline prices that traders already know. PCE days were left out: PCE prices move no market on release day (correlation about 0), since CPI comes first.
- **Spending surprise:** advance retail sales release days, 1976 to 2026 (536 days). Surprise = the 2-year yield move that day, the market's own reading of the print. The free data surprise (first print minus trend) barely moves yields (correlation 0.08), so it's only a check. A yield jump on these days is partly rate news, so the results also show the difference from the Fed-day slope ("spending beyond rates").
- **Dollar:** no release day, so this is sensitivity, not surprise. Monthly change in the Fed's broad trade-weighted dollar index, 1995 to 2026 (380 months), old index to 2005 and current index after. The whole market falls about 1.4% per 1% dollar rise, so a simple sector-minus-market slope mostly rewards low-beta sectors; the headline holds the market's move fixed instead. These numbers say which sectors do better or worse than their usual market sensitivity implies, so they roughly net to zero across the market.
- **Days dropped:** release days shared with another tracked release or a Fed decision (78 CPI days, 73 retail sales days).
- **Checks for every factor:** periods, an out-of-sample split, crisis days removed, beta-adjusted, equal-weighted, and a news split (growth vs tightening for spending, whether stocks fell on a hot print for inflation, risk-off vs risk-on months for the dollar). The dollar also has weekly changes, the 2-year yield held fixed, and big-move months.

## Limits

- **Surprise measures are stand-ins.** Without consensus forecasts, the inflation surprise misses what forecasters already expected, and the spending surprise mixes in whatever else moved yields that day. Both weaken the measured effects; small results may be measurement, not absence.
- **Dollar tradeoff.** Monthly data has more history and catches slow effects like translating overseas sales, but it can't tell the dollar apart from whatever moved it. Weekly results agree in sign for every clear sector. Big-move months (mostly crises) show no clear effects once the market is held fixed.
- **Inflation is weak and partly unstable.** Most sectors flip sign between 1997–2007 and 2008–2015. Only tech keeps its sign in every period; healthcare and durables keep it in two of three. Treat the rest as unconfirmed.
- **Loose mapping.** As in the rates test, French's 12 groups are broad; this tests v0's ranking at sector level, not each company type. The 49-group rerun (another thread) could do the same here.
- **Original data versions.** The inflation and spending surprises use first prints, as the macro spec asks. Returns, yields and the dollar index aren't revised.

## Rerun

```
python scripts/macro_factor_tests.py
```

Standard library only, about 4 minutes. Writes `results/macro_factor_tests/` (RESULTS.md, events and sensitivity tables per factor, v0_comparison.csv). v0's inflation, spending and dollar scores and their sector mapping are in `config/v0_macro_scores.csv`.
