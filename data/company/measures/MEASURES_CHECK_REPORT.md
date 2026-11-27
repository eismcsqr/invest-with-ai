# Company measures check report

Run: 2026-11-27 (every filing and price on or before this date). Source: Sharadar tables from the weekly pull. Method: docs/company-method.md; write-up: docs/company-measures.md.

## Checks

| Check | Result | Detail |
|---|---|---|
| No filing or price after the run date | pass | 0 filing or price dates after 2026-11-27 among those used |
| Same results with later data deleted (a year back) | pass | run for 2025-11-27: 0 of 5,474 companies differ between all data and data cut at that date; 0 dates after it used |
| Companies that later left the market are kept | pass | 377 companies listed on 2025-11-27 aren't listed now and are still in that run |
| Peer ranks spread evenly | pass | 18.4% of peer-set level ranks in the top fifth (expect about 20%) |
| Most companies with fresh filings get a score | pass | 5,501 scored of 5,352 with a filing in the last 200 days |

## Universe

- **Listed common stocks on 2026-11-27:** 5,503 (a price in the week before), 5,352 with a filing in the last 200 days.
- **Peer sets:** 4,207 companies above the size floor (smallest fifth by market value left out; floor $48 million). Smaller companies are still ranked against their group's peer set, with low confidence.
- **Companies with a score:** 5,501. 97 have no French group in Sharadar and get no peer set.
- **Groups:** 48 detailed groups (Sharadar's French industry field uses his 48-group scheme), 12 broad groups from SIC codes.

## Factor coverage (all companies)

| Factor | With a reading | +1 | +0.5 | 0 | −0.5 | −1 | Medium | Low |
|---|---|---|---|---|---|---|---|---|
| Growth | 77% (4,254) | 353 | 1016 | 1379 | 1014 | 492 | 3,225 | 1,029 |
| Profitability | 85% (4,705) | 144 | 1231 | 1383 | 1197 | 750 | 3,371 | 1,334 |
| Balance sheet | 87% (4,787) | 269 | 953 | 1747 | 1176 | 642 | 3,347 | 1,440 |
| Capital use | 92% (5,077) | 319 | 1096 | 1507 | 1262 | 893 | 3,804 | 1,273 |
| Earnings surprise | 92% (5,072) | 887 | 976 | 1168 | 1078 | 963 | 3,952 | 1,120 |
| Owner signals | 100% (5,501) | 0 | 924 | 4102 | 9 | 466 | 0 | 5,501 |

Company confidence: Medium 2,113, Low 3,388, High 0 (High needs the measured check, which hasn't run).

## Measures: missing rates among companies they apply to

| Measure | Factor | Scored | Applies to | Missing | Broad fallback |
|---|---|---|---|---|---|
| Revenue growth | Growth | yes | 5,503 | 23% | 75 |
| Change in revenue growth | Growth | yes | 5,503 | 27% | 68 |
| Earnings change ÷ market value | Growth | yes | 4,902 | 16% | 74 |
| Deferred revenue growth | Growth | yes | 821 | 38% | 0 |
| Deposit growth | Growth | yes | 466 | 29% | 0 |
| Tangible book per share growth | Growth | yes | 601 | 13% | 0 |
| Return on equity | Profitability | yes | 5,503 | 19% | 80 |
| Operating margin | Profitability | yes | 4,902 | 20% | 83 |
| Return on invested capital | Profitability | yes | 4,902 | 15% | 87 |
| Operating margin swings (3 years) | Profitability | yes | 4,902 | 29% | 66 |
| Gross margin | Profitability | yes | 1,584 | 6% | 0 |
| Incremental margin | Profitability | yes | 394 | 19% | 0 |
| EBITDA margin | Profitability | yes | 91 | 20% | 0 |
| Return on assets | Profitability | yes | 466 | 8% | 0 |
| Efficiency ratio (costs ÷ revenue) | Profitability | yes | 466 | 10% | 0 |
| Net debt ÷ EBITDA | Balance sheet | yes | 4,902 | 32% | 82 |
| Interest cover | Balance sheet | yes | 4,902 | 28% | 91 |
| Share of debt due within a year | Balance sheet | yes | 4,902 | 9% | 149 |
| Inventory turns | Balance sheet | yes | 1,477 | 33% | 0 |
| Cash runway (years of cash burn) | Balance sheet | yes | 963 | 7% | 0 |
| Tangible equity ÷ tangible assets | Balance sheet | yes | 601 | 5% | 0 |
| Debt ÷ equity | Balance sheet | yes | 135 | 1% | 0 |
| Total payout yield (dividends + buybacks) | Capital use | yes | 5,503 | 3% | 138 |
| Change in share count | Capital use | yes | 5,503 | 8% | 90 |
| Free cash flow yield | Capital use | yes | 4,902 | 12% | 84 |
| Share-based pay ÷ revenue | Capital use | yes | 821 | 15% | 0 |
| R&D ÷ revenue | Profitability | no | 1,784 | 21% | 0 |
| Capex ÷ depreciation | Capital use | no | 394 | 10% | 0 |
| Reinvestment rate (capex ÷ operating cash) | Capital use | no | 145 | 20% | 0 |
| Capex ÷ revenue | Capital use | no | 91 | 15% | 0 |
| Dividend payout ratio | Capital use | no | 131 | 33% | 0 |
| Results-day move beyond peers | Earnings surprise | yes | 5,503 | 8% | 56 |
| Net insider buying, 6 months | Owner signals | yes | 5,503 | 0% | 166 |
| Change in institutional ownership | Owner signals | yes | 5,503 | 100% | 0 |

## Gaps by group (under half with a reading)

- (none), Growth: 14.4% of 97
- (none), Profitability: 26.8% of 97
- (none), Balance sheet: 23.7% of 97
- (none), Capital use: 25.8% of 97
- Non-Metallic and Industrial Metal Mining, Growth: 46.1% of 76
- Precious Metals, Growth: 47.2% of 72
- Trading, Growth: 49.3% of 619

## Spot check (readings only)

Readings on the −1 to +1 scale and the company score (−3 to +3). No Sharadar numbers are shown.

| Ticker | Group | Growth | Profit | Balance | Capital | Surprise | Owners | Score (range) | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| AAPL | Computers | 0.0 | 0.5 | 0.0 | 0.0 | -0.5 | -1.0 | -0.5 (-1.0 to +0.5) | Medium |
| MSFT | Business Services | 0.5 | 0.5 | 0.5 | 0.0 | 0.0 | 0.5 | +1.0 (+0.0 to +1.6) | Medium |
| NVDA | Electronic Equipment | 0.5 | 1.0 | 0.5 | 0.5 | -0.5 | -1.0 | +0.5 (-0.2 to +1.2) | Medium |
| JPM | Banking | 0.5 | 0.5 | -1.0 | 0.5 | 0.5 | 0.0 | +0.2 (-0.5 to +0.5) | Medium |
| BAC | Banking | 0.0 | 0.0 | -0.5 | 1.0 | -1.0 | 0.0 | -0.3 (-0.8 to -0.1) | Medium |
| XOM | Petroleum and Natural Gas | 0.0 | 0.5 | 0.5 | 0.5 | 1.0 | 0.0 | +1.3 (-0.2 to +2.4) | Medium |
| JNJ | Pharmaceutical Products | 0.0 | 0.5 | 0.5 | 0.5 | 0.5 | 0.0 | +0.9 (+0.5 to +1.6) | Medium |
| WMT | Retail | 0.0 | 0.0 | 0.0 | -0.5 | 0.5 | -1.0 | -0.5 (-1.3 to +0.7) | Medium |
| HD | Retail | -0.5 | 0.5 | 0.0 | 0.0 | -0.5 | -1.0 | -0.6 (-1.7 to -0.6) | Medium |
| KO | Beer & Liquor | 0.0 | 0.5 | 0.5 | -0.5 | 0.5 | 0.0 | +0.6 (-0.2 to +1.6) | Low |
| PGR | Insurance | -0.5 | 0.5 | 0.0 | 0.0 | -1.0 | -1.0 | -0.9 (-1.2 to -0.5) | Medium |
| NEE | Utilities | 0.5 | 0.5 | 0.0 | 0.5 | 0.5 | 0.0 | +0.9 (-0.2 to +2.0) | Medium |
| T | Communication | 0.0 | 0.0 | 0.0 | 0.5 | -1.0 | 0.0 | -0.2 (-1.0 to +0.5) | Medium |
| CAT | Machinery | 0.5 | 0.5 | 0.0 | 0.5 | -1.0 | 0.0 | +0.2 (-0.5 to +1.5) | Low |
| MRNA | Pharmaceutical Products | 0.5 | 0.0 | 0.0 | 0.5 | 0.0 | -1.0 | +0.1 (-0.5 to +1.2) | Medium |

## Notes

- Insider trades: 10,000 rows filed 2026-11-18 to 2026-11-25 (codes:  2,547, S 2,226, M 1,503, A 1,134, P 1,073, F 695); 2,171 open-market buys and sales kept.
- Institutional holdings: 10,000 rows (by quarter: 2026-09-30 10,000); 131 company-quarters kept.
- Full per-company results stay on the runner (raw/company_results/): the repository is public and the Sharadar licence doesn't allow redistributing its data.
