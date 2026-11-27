# Company measured check

Run: 2026-11-27. 102 quarter ends, 2001-03-31 to 2026-06-30, each scored with only the filings and prices known that day, then compared with the next quarter's return relative to the company's detailed peer group (the group's median). Method: docs/company-method.md section 9; write-up: docs/company-check.md. Code: scripts/company_check.py.

## Checks

| Check | Result | Detail |
|---|---|---|
| No filing or price after each run date | pass | 0 later dates used across 102 runs |
| Companies that later left the market are kept | pass | 5,108 company-quarters where the company stopped trading during the next quarter (return to its last close) |
| Enough companies each quarter | pass | 3,670 to 5,105 peer-set companies tested per quarter |

## Factors: top fifth minus bottom fifth, next quarter, relative to peers

Percent per quarter. Range: 95% bootstrap. FDR: Benjamini-Hochberg at 10% across the six factors.

| Factor | Quarters | Spread | Range | FDR | Up quarters | 2001-07 | 2008-19 | 2020 on |
|---|---|---|---|---|---|---|---|---|
| Growth | 102 | +0.36% | -0.39 to +1.06 | no | 69% | +1.07 | -0.11 | +0.45 |
| Profitability | 102 | +1.28% | -0.13 to +2.69 | no | 64% | +1.63 | +1.04 | +1.35 |
| Balance sheet | 102 | +1.03% | +0.05 to +1.99 | pass | 68% | +1.04 | +0.69 | +1.65 |
| Capital use | 102 | +1.76% | +0.65 to +2.84 | pass | 61% | +2.02 | +1.20 | +2.49 |
| Earnings surprise | 102 | +0.40% | -0.10 to +0.81 | no | 60% | -0.02 | +0.51 | +0.63 |
| Owner signals | 71 | -0.54% | -1.10 to +0.01 | no | 41% | – | -0.31 | -0.93 |
| Company score | 102 | +1.50% | +0.34 to +2.64 | – | 70% | +1.66 | +1.16 | +1.96 |

## Average next-quarter return relative to peers, by reading

| Factor | +1 | +0.5 | 0 | −0.5 | −1 |
|---|---|---|---|---|---|
| Growth | +1.24% | +1.74% | +1.62% | +1.38% | +1.05% |
| Profitability | +1.33% | +1.77% | +1.70% | +1.25% | -0.34% |
| Balance sheet | +1.38% | +1.65% | +1.65% | +1.26% | -0.47% |
| Capital use | +2.21% | +1.86% | +1.55% | +0.98% | -0.59% |
| Earnings surprise | +1.76% | +1.52% | +1.04% | +1.25% | +1.36% |
| Owner signals | – | +0.04% | +1.35% | +1.68% | +0.99% |

## Confidence check 3 by broad group

Y = passes (pooled test passed, and positive in this group overall and in at least two of three periods).

| Factor | Consumer nondurables | Consumer durables | Manufacturing | Energy | Chemicals | Business equipment | Telecom | Utilities | Shops | Healthcare | Money | Other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Growth | +0.9 | -0.0 | +0.2 | -1.7 | -1.6 | +0.7 | -0.1 | -0.8 | +0.7 | +0.1 | +1.0 | +0.1 |
| Profitability | +0.7 | +3.5 | +0.2 | +0.5 | +1.1 | +1.4 | +0.9 | +0.3 | +1.9 | +2.5 | +0.7 | +1.4 |
| Balance sheet | Y | Y | Y | Y | Y | Y | Y | -0.1 | Y | Y | Y | Y |
| Capital use | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| Earnings surprise | +0.5 | -0.2 | -0.5 | +1.2 | +0.2 | +0.1 | +1.2 | +0.4 | +0.8 | +0.2 | +0.6 | +0.4 |
| Owner signals | -0.5 | -1.7 | -0.6 | -0.4 | -0.3 | -0.6 | -1.5 | +0.0 | -1.8 | -1.0 | -0.6 | +0.8 |

Cells without Y show the group's average spread (percent per quarter).

## Measures whose direction isn't settled

Direction read from 2001 to 2013 only, then tested on 2014 on.

| Measure | Applies to | Quarters | 2001-13 | 2014 on | 2014-on range | Call |
|---|---|---|---|---|---|---|
| R&D ÷ revenue | business equipment, healthcare | 102 | -0.87 | +0.46 | -1.28 to +2.31 | no direction: the two halves disagree |
| Reinvestment rate (capex ÷ operating cash) | energy | 102 | +0.37 | +0.19 | -2.02 to +2.49 | leans higher is better; second half agrees but its range crosses zero |
| Dividend payout ratio | utilities | 102 | +0.39 | -1.07 | -3.56 to +1.48 | no direction: the two halves disagree |

Spreads here are higher value minus lower value, so a positive number means higher is better.

## Every measure

| Measure | Scored | Quarters | Spread | Range | 2001-07 | 2008-19 | 2020 on |
|---|---|---|---|---|---|---|---|
| Revenue growth | yes | 102 | +0.04 | -0.69 to +0.84 | +0.08 | -0.09 | +0.25 |
| Change in revenue growth | yes | 102 | +0.15 | -0.37 to +0.64 | +0.76 | -0.12 | -0.02 |
| Earnings change ÷ market value | yes | 102 | +0.50 | -0.26 to +1.15 | +1.31 | -0.31 | +1.14 |
| Deferred revenue growth | yes | 102 | +1.83 | +0.97 to +2.76 | +1.75 | +1.48 | +2.57 |
| Deposit growth | yes | 102 | +0.44 | -0.25 to +1.12 | +0.65 | -0.10 | +1.21 |
| Tangible book per share growth | yes | 102 | +1.21 | +0.29 to +2.09 | +1.79 | +0.74 | +1.46 |
| Return on equity | yes | 102 | +0.77 | -0.51 to +2.00 | +1.12 | +0.44 | +1.01 |
| Operating margin | yes | 102 | +0.86 | -0.55 to +2.23 | +1.59 | +0.14 | +1.40 |
| Return on invested capital | yes | 102 | +0.98 | -0.39 to +2.34 | +1.39 | +0.67 | +1.10 |
| Operating margin swings (3 years) | yes | 102 | +1.10 | -0.36 to +2.48 | +1.47 | +1.22 | +0.49 |
| Gross margin | yes | 102 | +0.73 | -0.03 to +1.46 | +1.15 | +0.58 | +0.55 |
| Incremental margin | yes | 102 | -0.05 | -1.03 to +1.05 | -0.31 | -0.56 | +1.18 |
| EBITDA margin | yes | 102 | +0.31 | -2.58 to +3.01 | +4.75 | -1.11 | -1.84 |
| Return on assets | yes | 102 | +0.12 | -0.84 to +1.06 | +0.40 | +0.77 | -1.37 |
| Efficiency ratio (costs ÷ revenue) | yes | 102 | +0.35 | -0.53 to +1.23 | +0.07 | +1.11 | -0.74 |
| Net debt ÷ EBITDA | yes | 102 | +0.80 | -0.38 to +1.96 | +1.50 | +0.26 | +1.04 |
| Interest cover | yes | 102 | +0.81 | -0.42 to +2.05 | +1.31 | +0.37 | +1.10 |
| Share of debt due within a year | yes | 102 | +0.68 | +0.21 to +1.17 | -0.07 | +0.22 | +2.33 |
| Inventory turns | yes | 102 | +0.67 | -0.15 to +1.46 | +0.81 | +0.27 | +1.25 |
| Cash runway (years of cash burn) | yes | 88 | +2.78 | +0.50 to +5.14 | +3.66 | +1.66 | +3.37 |
| Tangible equity ÷ tangible assets | yes | 102 | +0.43 | -0.31 to +1.15 | +0.35 | +1.10 | -0.72 |
| Debt ÷ equity | yes | 102 | -0.26 | -1.96 to +1.30 | +0.10 | -0.12 | -0.92 |
| Total payout yield (dividends + buybacks) | yes | 102 | +0.84 | +0.01 to +1.61 | +0.75 | +0.61 | +1.36 |
| Change in share count | yes | 102 | +1.80 | +0.83 to +2.77 | +1.68 | +1.41 | +2.65 |
| Free cash flow yield | yes | 102 | +2.01 | +1.12 to +2.95 | +2.44 | +1.46 | +2.56 |
| Share-based pay ÷ revenue | yes | 102 | +0.12 | -1.12 to +1.33 | +0.75 | -0.64 | +0.82 |
| Capex ÷ depreciation | yes | 102 | +1.00 | +0.00 to +1.97 | +0.37 | +0.82 | +1.99 |
| Capex ÷ revenue | yes | 102 | +1.81 | -0.63 to +4.28 | +1.72 | +1.71 | +2.11 |
| R&D ÷ revenue | no | 102 | -0.22 | -1.67 to +1.29 | -1.46 | +0.34 | +0.08 |
| Reinvestment rate (capex ÷ operating cash) | no | 102 | +0.28 | -1.15 to +1.84 | -0.81 | +0.08 | +1.81 |
| Dividend payout ratio | no | 102 | -0.32 | -1.80 to +1.16 | -0.26 | -0.90 | +0.67 |
| Results-day move beyond peers | yes | 102 | +0.40 | -0.10 to +0.81 | -0.02 | +0.51 | +0.63 |
| Net insider buying, 6 months | yes | 72 | -0.54 | -1.35 to +0.36 | – | -0.13 | -1.27 |
| Change in institutional ownership | yes | 51 | -1.10 | -1.85 to -0.40 | – | -0.53 | -1.64 |

For scored measures the spread is better minus worse (direction applied).

## Limits

- Peer groups use each company's industry as Sharadar lists it today, not as it was then.
- Companies that stop trading get the return to their last close; Sharadar has no delisting returns, so failures may look a little better than they were.
- Before August 2004 there are no 8-K results filings, so the earnings surprise uses the quarterly filing date, which comes after the results announcement.
- Insider trades start in 2008 and institutional holdings later, so owner signals are tested on fewer quarters.
- Only peer-set companies (above the size floor) are tested.
- Per-company results are not saved: the repository is public and the Sharadar licence doesn't allow redistributing its data.
