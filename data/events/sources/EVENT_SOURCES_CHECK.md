# Event sources check report

Run: 2026-11-27. One row per candidate source for the 12 agreed event types (docs/event-types.md). Written by scripts/check_event_sources.py.

| Event type | Source | Status | First | Last | Events | Cost | Note |
|---|---|---|---|---|---|---|---|
| Geopolitical shocks | Geopolitical risk index, daily (matteoiacoviello.com) | partial | 1985-01-01 | 2026-11-23 | 15 | free | column GPRD; 15 spike episodes (top 1% of days, 10-day gap); 3 of 5 known events in the top 5% of days; last value 4 days old |
| check_tpu | Trade policy uncertainty index, daily | fail |  |  |  | free | RuntimeError: no daily TPU series found in the linked files |
| Elections and policy shocks | Economic policy uncertainty index, daily (FRED USEPUINDXD) | pass | 1985-01-01 | 2026-11-26 | 42 | free | column USEPUINDXD; 42 spike episodes (top 1% of days, 10-day gap); 2 of 3 known events in the top 5% of days; last value 1 days old |
| Elections and policy shocks | US federal election days (fixed by law: first Tuesday after the first Monday in November) | pass | 1990-11-06 | 2026-11-03 | 8 presidential, 9 midterm since 1994 | free | computed; matches 5 known dates |
| Energy and commodity supply shocks | WTI oil price, daily (FRED DCOILWTICO) | pass | 1986-01-02 | 2026-11-24 |  | free | last value 3 days old |
| Energy and commodity supply shocks | OPEC announcement dates and oil supply surprises (Kaenzig 2021) | fail |  |  |  | free | author's site: dkaenzig.github.io: HTTP 404 |
| Major regulatory actions | Federal Register API: final rules marked significant, by agency | pass | 1995 | 2026 | 9521 | free | significant flag present from 1995; median 294 a year |
| Trade and tariff actions | Federal Register API: USTR documents and presidential proclamations mentioning tariffs | pass | 1994 | 2026 | 1398 | free | 274 proclamations, 1124 USTR documents |
| Guidance changes | Sharadar 8-K events table (items 2.02, 7.01) | partial |  |  | 0 | already paid (Sharadar bundle) | 0 item filings since Aug 2004; codes not found: 2.02, 7.01 |
| Mergers and acquisitions | Sharadar 8-K events table (items 1.01, 2.01) | partial |  |  | 0 | already paid (Sharadar bundle) | 0 item filings since Aug 2004; codes not found: 1.01, 2.01 |
| Leadership changes | Sharadar 8-K events table (items 5.02) | partial |  |  | 0 | already paid (Sharadar bundle) | 0 item filings since Aug 2004; codes not found: 5.02 |
| Capital structure breaks | Sharadar 8-K events table (items 8.01, 3.02) | partial |  |  | 0 | already paid (Sharadar bundle) | 0 item filings since Aug 2004; codes not found: 8.01, 3.02 |
| Accounting and legal trouble | Sharadar 8-K events table (items 4.01, 4.02, 3.01) | partial |  |  | 0 | already paid (Sharadar bundle) | 0 item filings since Aug 2004; codes not found: 4.01, 4.02, 3.01 |
| Distress and restructuring | Sharadar 8-K events table (items 1.03, 2.04, 2.05) | partial |  |  | 0 | already paid (Sharadar bundle) | 0 item filings since Aug 2004; codes not found: 1.03, 2.04, 2.05 |
| Capital structure breaks | Sharadar corporate actions: dividend history | pass | 1997-12-31 | 2026-11-25 | 27027 | already paid (Sharadar bundle) | 13,843 payers; 27,027 candidate cuts of 25% or more (rough: specials and splits not yet removed); 5,836 payers with no dividend in the last 200 days |
| Mergers and acquisitions | Sharadar corporate actions: acquisitions and mergers | pass | 1998-01-07 | 2026-11-20 | 24804 | already paid (Sharadar bundle) | completion dates with the other party: acquisitionalternativecommon 1, acquisitionalternativewarrant 1, acquisitionbesteffortcashcad 3, acquisitionbesteffortcashusd 8, acquisitionbesteffortcommon 6, acquisitionbesteffortnote 1, acquisitionbesteffortpreferred 1, acquisitionbesteffortpreferred2 1, acquisitionbesteffortright 2, acquisitionby 8,134, acquisitioncash 5,349, acquisitioncashcad 20, acquisitioncasheur 2, acquisitioncashgbp 1, acquisitioncashhkd 1, acquisitioncashsgd 1, acquisitioncashusd 5, acquisitioncommon 15, acquisitiondefaultcasheur 1, acquisitiondistributioncashusd 2, acquisitiondistributionstock 7, acquisitiondividendusd 1, acquisitionelectcash 152, acquisitionelectcashusd 2, acquisitionelectcommon 2, acquisitionelectstock 147, acquisitionestimatedcashusd 1, acquisitionestimatedcommon 6, acquisitionestimatedpackagecommon 2, acquisitionestimatedpackagepreferred 1, acquisitionof 8,134, acquisitionpreferred 5, acquisitionqualificationcashcad 1, acquisitionqualificationdefaultstock 1, acquisitionqualificationstock 1, acquisitionspecial 1, acquisitionstock 2,508, acquisitionterminalcashusd 1, acquisitionwarrant 4, mergerfrom 136, mergerto 136 |
| Company events (all 8-K types) | Cross-check: Sharadar item codes vs SEC filing index, 8 companies since 2015 | fail | 2015-01-01 | 2026-11-27 | 0 | free | 0% of SEC's (date, item) pairs found in Sharadar; Sharadar has 964 pairs; SEC gives the acceptance time for 610 8-Ks (needed for the after-4 PM rule) |
| Activist stakes | SEC EDGAR filing index: SC 13D, SCHEDULE 13D | partial |  |  | about 0 a quarter | free | 0 sample quarters read |
| Mergers and acquisitions | SEC EDGAR filing index: SC TO-T, SC 14D9 | partial |  |  | about 0 a quarter | free | 0 sample quarters read |
| Mergers and acquisitions | SEC EDGAR filing index: DEFM14A, PREM14A | partial |  |  | about 0 a quarter | free | 0 sample quarters read |
| Capital structure breaks | SEC EDGAR filing index: 424B4, 424B5, S-3 | partial |  |  | about 0 a quarter | free | 0 sample quarters read |
| Accounting and legal trouble | SEC EDGAR filing index: NT 10-K, NT 10-Q | partial |  |  | about 0 a quarter | free | 0 sample quarters read |
| Leadership changes | SEC EDGAR full-text search: 8-Ks naming the CEO or CFO with 'resign' | pass | 2001-01-01 | 2026-11-27 | 4,574 CEO hits in 2015 | free | 2015: CEO 4,574 hits (83 of 100 sampled tagged item 5.02), CFO 3,806 hits; 2001: 1,371 CEO hits (search covers 2001 on) |

## Notes

- **gpr:** File: data_gpr_daily_recent.xls (sheet Sheet1).
- **tpu:** Files linked on the TPU page: tpu_web_latest.xlsx, firm_tpu.csv
- **tpu:** tpu_web_latest.xlsx: sheets ReadMe (37 rows), Series_description (5 rows), TPU_MONTHLY (803 rows), TPU_QUARTERLY (267 rows), TPU_DAILY (4346 rows); no daily date/TPU column found
- **tpu:** firm_tpu.csv: sheets csv (119954 rows); no daily date/TPU column found
- **fr:** Agencies with the most significant final rules: Health and Human Services Department (1323), Environmental Protection Agency (845), Transportation Department (839), Agriculture Department (817), Labor Department (626), Centers for Medicare & Medicaid Services (596), Defense Department (546), Commerce Department (496), Interior Department (490), Treasury Department (397), Homeland Security Department (386), Housing and Urban Development Department (378)
- **sharadar:** Events table columns: ticker, date, eventcodes
- **sharadar:** Actions table columns: date, action, ticker, name, value, contraticker, contraname

## Sharadar 8-K codes (all, by rows)

- 91: 1,113,304 rows, 15,284 tickers, 1994-01-04 to 2026-11-25
- 81: 834,797 rows, 17,529 tickers, 1994-01-04 to 2026-11-25
- 34: 540,580 rows, 16,874 tickers, 1994-01-04 to 2026-11-25
- 22: 380,500 rows, 10,089 tickers, 2004-08-23 to 2026-11-25
- 71: 294,387 rows, 11,351 tickers, 1996-10-09 to 2026-11-25
- 52: 237,661 rows, 11,165 tickers, 1994-12-05 to 2026-11-25
- 11: 210,002 rows, 11,313 tickers, 2004-08-23 to 2026-11-25
- 35: 155,890 rows, 13,864 tickers, 1993-11-08 to 2026-11-25
- 57: 78,772 rows, 8,661 tickers, 2010-03-01 to 2026-11-25
- 21: 67,098 rows, 11,700 tickers, 1994-01-04 to 2026-11-25
- 23: 63,968 rows, 8,282 tickers, 2004-08-24 to 2026-11-25
- 53: 46,153 rows, 10,286 tickers, 1994-01-11 to 2026-11-25
- 32: 38,458 rows, 7,228 tickers, 2004-08-23 to 2026-11-25
- 37: 34,867 rows, 3,904 tickers, 2000-01-24 to 2026-11-25
- 31: 25,130 rows, 7,709 tickers, 2004-08-24 to 2026-11-25
- 12: 20,115 rows, 7,085 tickers, 2004-08-23 to 2026-11-25
- 33: 17,193 rows, 7,147 tickers, 2004-08-23 to 2026-09-02
- 51: 11,664 rows, 6,817 tickers, 1994-01-04 to 2026-11-25
- 41: 10,698 rows, 4,988 tickers, 2004-08-23 to 2026-11-25
- 25: 7,564 rows, 2,950 tickers, 2004-08-24 to 2026-11-17
- 40: 6,806 rows, 3,558 tickers, 1994-01-13 to 2004-08-20
- 42: 5,015 rows, 3,167 tickers, 2004-08-24 to 2026-11-25
- 24: 3,236 rows, 1,843 tickers, 2004-08-26 to 2026-11-24
- 13: 3,130 rows, 1,716 tickers, 1994-01-05 to 2026-11-25
- 26: 3,126 rows, 1,691 tickers, 2004-08-25 to 2026-11-18
- 55: 2,324 rows, 1,762 tickers, 2003-07-30 to 2026-11-25
- 54: 1,459 rows, 827 tickers, 2003-07-28 to 2026-11-10
- 58: 1,224 rows, 778 tickers, 2011-12-19 to 2026-10-23
- 56: 784 rows, 695 tickers, 2005-11-10 to 2026-11-25
- 14: 244 rows, 70 tickers, 2011-10-17 to 2026-10-30
- 65: 11 rows, 11 tickers, 2006-08-04 to 2013-04-30
- 63: 11 rows, 10 tickers, 2005-07-01 to 2011-11-17
- 62: 7 rows, 6 tickers, 2008-04-03 to 2017-01-11
- 15: 5 rows, 5 tickers, 2003-08-07 to 2004-08-18
- 64: 3 rows, 3 tickers, 2008-06-20 to 2013-09-12
