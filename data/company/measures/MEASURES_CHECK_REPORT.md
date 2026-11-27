# Company measures check report

Run: 2026-11-27 (every filing and price on or before this date). Source: Sharadar tables from the weekly pull. Method: docs/company-method.md; write-up: docs/company-measures.md.

## Checks

| Check | Result | Detail |
|---|---|---|
| No filing or price after the run date | pass | 0 filing or price dates after 2026-11-27 among those used |
| Same results with later data deleted (a year back) | FAIL | run for 2025-11-27: 141 of 5,474 companies differ between all data and data cut at that date (e.g. MRLN, EQBK, UROY, SCNX, EMAT); 0 dates after it used |
| Companies that later left the market are kept | pass | 377 companies listed on 2025-11-27 aren't listed now and are still in that run |
| Peer ranks spread evenly | pass | 19.9% of peer-set level ranks in the top fifth (expect about 20%) |
| Most companies with fresh filings get a score | pass | 5,278 scored of 5,352 with a filing in the last 200 days |

## Universe

- **Listed common stocks on 2026-11-27:** 5,503 (a price in the week before), 5,352 with a filing in the last 200 days.
- **Peer sets:** 4,207 companies above the size floor (smallest fifth by market value left out; floor $48 million). Smaller companies are still ranked against their group's peer set, with low confidence.
- **Companies with a score:** 5,278. 97 have no French group in Sharadar and get no peer set.
- **Groups:** 49 detailed groups (Sharadar's French industry field uses his 48-group scheme), 12 broad groups from SIC codes.

## Factor coverage (all companies)

| Factor | With a reading | +1 | +0.5 | 0 | −0.5 | −1 | Medium | Low |
|---|---|---|---|---|---|---|---|---|
| Growth | 76% (4,180) | 346 | 998 | 1358 | 997 | 481 | 3,225 | 955 |
| Profitability | 84% (4,619) | 138 | 1208 | 1369 | 1175 | 729 | 3,371 | 1,248 |
| Balance sheet | 85% (4,705) | 266 | 937 | 1721 | 1157 | 624 | 3,347 | 1,358 |
| Capital use | 92% (5,077) | 325 | 1098 | 1496 | 1261 | 897 | 3,804 | 1,273 |
| Earnings surprise | 92% (5,072) | 887 | 976 | 1168 | 1078 | 963 | 3,952 | 1,120 |
| Owner signals | 0% (0) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Company confidence: Medium 3,753, Low 1,525, High 0 (High needs the measured check, which hasn't run).

## Measures: missing rates among companies they apply to

| Measure | Factor | Scored | Applies to | Missing | Broad fallback |
|---|---|---|---|---|---|
| Revenue growth | Growth | yes | 5,503 | 23% | 75 |
| Change in revenue growth | Growth | yes | 5,503 | 27% | 0 |
| Earnings change ÷ market value | Growth | yes | 4,902 | 16% | 0 |
| Deferred revenue growth | Growth | yes | 821 | 38% | 0 |
| Deposit growth | Growth | yes | 466 | 29% | 0 |
| Tangible book per share growth | Growth | yes | 601 | 13% | 0 |
| Return on equity | Profitability | yes | 5,503 | 19% | 80 |
| Operating margin | Profitability | yes | 4,902 | 20% | 0 |
| Return on invested capital | Profitability | yes | 4,902 | 15% | 0 |
| Operating margin swings (3 years) | Profitability | yes | 4,902 | 29% | 0 |
| Gross margin | Profitability | yes | 1,584 | 6% | 0 |
| Incremental margin | Profitability | yes | 394 | 19% | 0 |
| EBITDA margin | Profitability | yes | 91 | 20% | 0 |
| Return on assets | Profitability | yes | 466 | 8% | 0 |
| Efficiency ratio (costs ÷ revenue) | Profitability | yes | 466 | 10% | 0 |
| Net debt ÷ EBITDA | Balance sheet | yes | 4,902 | 32% | 0 |
| Interest cover | Balance sheet | yes | 4,902 | 28% | 0 |
| Share of debt due within a year | Balance sheet | yes | 4,902 | 9% | 0 |
| Inventory turns | Balance sheet | yes | 1,477 | 33% | 0 |
| Cash runway (years of cash burn) | Balance sheet | yes | 963 | 7% | 0 |
| Tangible equity ÷ tangible assets | Balance sheet | yes | 601 | 5% | 0 |
| Debt ÷ equity | Balance sheet | yes | 135 | 1% | 0 |
| Total payout yield (dividends + buybacks) | Capital use | yes | 5,503 | 3% | 138 |
| Change in share count | Capital use | yes | 5,503 | 8% | 90 |
| Free cash flow yield | Capital use | yes | 4,902 | 12% | 0 |
| Share-based pay ÷ revenue | Capital use | yes | 821 | 15% | 0 |
| R&D ÷ revenue | Profitability | no | 1,784 | 21% | 0 |
| Capex ÷ depreciation | Capital use | no | 394 | 10% | 0 |
| Reinvestment rate (capex ÷ operating cash) | Capital use | no | 145 | 20% | 0 |
| Capex ÷ revenue | Capital use | no | 91 | 15% | 0 |
| Dividend payout ratio | Capital use | no | 131 | 33% | 0 |
| Results-day move beyond peers | Earnings surprise | yes | 5,503 | 8% | 56 |
| Net insider buying, 6 months | Owner signals | yes | 5,503 | 100% | 0 |
| Change in institutional ownership | Owner signals | yes | 5,503 | 100% | 0 |

## Gaps by group (under half with a reading)

- (none), Growth: 0.0% of 97
- (none), Profitability: 0.0% of 97
- (none), Balance sheet: 0.0% of 97
- (none), Capital use: 25.8% of 97
- Almost Nothing, Growth: 0.0% of 15
- Almost Nothing, Profitability: 0.0% of 15
- Almost Nothing, Balance sheet: 0.0% of 15
- Candy & Soda, Growth: 0.0% of 11
- Candy & Soda, Profitability: 0.0% of 11
- Candy & Soda, Balance sheet: 0.0% of 11
- Coal, Growth: 0.0% of 8
- Coal, Profitability: 0.0% of 8
- Coal, Balance sheet: 0.0% of 8
- Fabricated Products, Growth: 0.0% of 9
- Fabricated Products, Profitability: 0.0% of 9
- Fabricated Products, Balance sheet: 0.0% of 9
- Non-Metallic and Industrial Metal Mining, Growth: 46.1% of 76
- Precious Metals, Growth: 47.2% of 72
- Shipbuilding Railroad Equipment, Growth: 0.0% of 12
- Shipbuilding Railroad Equipment, Profitability: 0.0% of 12
- Shipbuilding Railroad Equipment, Balance sheet: 0.0% of 12
- Textiles, Growth: 0.0% of 6
- Textiles, Profitability: 0.0% of 6
- Textiles, Balance sheet: 0.0% of 6
- Tobacco Products, Growth: 0.0% of 8
- Tobacco Products, Profitability: 0.0% of 8
- Tobacco Products, Balance sheet: 0.0% of 8
- Trading, Growth: 49.3% of 619

## Spot check (readings only)

Readings on the −1 to +1 scale and the company score (−3 to +3). No Sharadar numbers are shown.

| Ticker | Group | Growth | Profit | Balance | Capital | Surprise | Owners | Score (range) | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| AAPL | Computers | 0.0 | 0.5 | 0.0 | 0.0 | -0.5 | – | +0.0 (-0.6 to +1.2) | Medium |
| MSFT | Business Services | 0.5 | 0.5 | 0.5 | 0.0 | 0.0 | – | +0.9 (-0.3 to +1.6) | Medium |
| NVDA | Electronic Equipment | 0.5 | 1.0 | 0.5 | 0.5 | -0.5 | – | +1.2 (+0.3 to +2.1) | Medium |
| JPM | Banking | 0.5 | 0.5 | -1.0 | 0.5 | 0.5 | – | +0.3 (-0.5 to +0.5) | Medium |
| BAC | Banking | 0.0 | 0.0 | -0.5 | 1.0 | -1.0 | – | -0.4 (-1.0 to -0.1) | Medium |
| XOM | Petroleum and Natural Gas | 0.0 | 0.5 | 0.5 | 0.5 | 1.0 | – | +1.5 (-0.2 to +2.8) | Medium |
| JNJ | Pharmaceutical Products | 0.0 | 0.5 | 0.5 | 0.5 | 0.5 | – | +1.1 (+0.5 to +1.9) | Medium |
| WMT | Retail | 0.0 | 0.0 | 0.0 | -0.5 | 0.5 | – | +0.0 (-1.0 to +1.4) | Medium |
| HD | Retail | -0.5 | 0.5 | 0.0 | 0.0 | -0.5 | – | -0.1 (-1.5 to -0.1) | Medium |
| KO | Beer & Liquor | 0.0 | 0.5 | 0.5 | -0.5 | 0.5 | – | +0.7 (-0.3 to +1.9) | Low |
| PGR | Insurance | -0.5 | 0.5 | 0.0 | 0.0 | -1.0 | – | -0.5 (-0.8 to +0.0) | Medium |
| NEE | Utilities | 0.5 | 0.5 | 0.0 | 0.5 | 0.5 | – | +1.1 (-0.3 to +2.4) | Medium |
| T | Communication | 0.0 | 0.0 | 0.0 | 0.5 | -1.0 | – | -0.3 (-1.2 to +0.5) | Medium |
| CAT | Machinery | 0.5 | 0.5 | 0.0 | 0.5 | -1.0 | – | +0.3 (-0.6 to +1.8) | Medium |
| MRNA | Pharmaceutical Products | 0.5 | 0.0 | 0.0 | 0.5 | 0.0 | – | +0.7 (+0.0 to +1.9) | Medium |

## Notes

- Insider table columns not recognised (ticker, date, formtype, ownername, officertitle, isdirector, isofficer, istenpercentowner, transactiondate, securityadcode, transactioncode, sharesownedbeforetransaction, transactionshares, sharesownedfollowingtransaction, transactionpricepershare...): insider buying is missing.
- Holdings table columns not recognised (ticker, investorid, securitytype, date, value, units...): institutional change is missing.
- Full per-company results stay on the runner (raw/company_results/): the repository is public and the Sharadar licence doesn't allow redistributing its data.
