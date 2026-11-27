# Company data check report

Run: 2026-11-27. Source: Sharadar (direct API, bulk download of each table).

## The six checks

| Check | Result | Detail |
|---|---|---|
| Matches EDGAR within 1% | pass | 79 of 80 numbers within 1% (98.75%) across 6 companies; see edgar_check.csv |
| No number dated before its filing | pass | 0 of 686,995 as-first-reported quarterly rows have a filing date before the period end |
| Splits handled | pass | AAPL 4-for-1 on 2020-08-31: adjusted close moved 1.034x, unadjusted 0.258x (ok); AAPL 7-for-1 on 2014-06-09: adjusted close moved 1.016x, unadjusted 0.145x (ok); NVDA 10-for-1 on 2024-06-10: adjusted close moved 1.007x, unadjusted 0.101x (ok) |
| Delisted names present | pass | 12,392 of 17,893 companies with fundamentals are delisted; 14,747 delisted tickers have daily prices |
| Under 2% missing quarters | pass | 1.21% of quarters missing between each company's first and last quarter (7,576 of 628,419), domestic common stocks with at least 4 quarters |
| New filings within 5 days | pass | newest filing date in the data is 2026-11-25 (2 days before this run). A recent date means filings are arriving; the delay for each new filing shows up week to week. |

## Tables

- **Tickers:** 17,893 companies with fundamentals, 49 French industry groups (famaindustry). Rows by table: stocks 21,052, fundamentals 17,893, holdings_investor 13,357, insiders 12,286, funds 10,132.
- **Fundamentals:** 17,089 companies with as-first-reported quarterly rows (686,995 rows). Rows by dimension: ARQ 686,995, ART 693,741, ARY 187,053, MRQ 724,599, MRT 744,095, MRY 203,873.
- **Filing lag:** median 44 days from period end to filing, 90th percentile 89.
- **Daily prices:** 45,629,107 rows, 21,052 tickers, 1997-12-31 to 2026-11-25. Rows by decade: 1990s 4,048,246, 2000s 16,356,608, 2010s 13,914,847, 2020s 11,309,406.
- **8-K events:** 2,550,710 rows, 1993-11-08 to 2026-11-25. Most common codes: 91 (1,113,304), 81 (834,797), 34 (540,580), 22 (380,500), 71 (294,387), 52 (237,661). Code meanings are on Sharadar's events page.
- **Corporate actions:** 723,698 rows, 1997-12-31 to 2026-11-30. By type: dividend 562,993, listed 22,800, delisted 18,441, tickerchangeto 13,264, tickerchangefrom 13,264, split 13,232, initiated 8,406, acquisitionby 8,134.

## Fields named in the company factors doc

39 of 39 present in fundamentals. Full list in field_check.csv; every column of every table in fields.csv.

## Largest gaps in quarterly data

- CYRNQ: 57 quarters missing
- APLD: 49 quarters missing
- TEVA: 45 quarters missing
- BHC: 42 quarters missing
- AVDL: 39 quarters missing

## Owner-signal tables (optional)

- insiders: downloaded as 'insiders' (whole table), 248 MB in 2s
- holdings: downloaded as 'holdings' (whole table), 717 MB in 4s

## Not committed

- Raw tables stay on the runner and are not committed (size and licence).
