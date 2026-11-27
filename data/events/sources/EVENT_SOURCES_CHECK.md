# Event sources check report

Run: 2026-11-27. One row per candidate source for the 12 agreed event types (docs/event-types.md). Written by scripts/check_event_sources.py.

| Event type | Source | Status | First | Last | Events | Cost | Note |
|---|---|---|---|---|---|---|---|
| Geopolitical shocks | Geopolitical risk index, daily (matteoiacoviello.com) | partial | 1985-01-01 | 2026-11-23 | 135 | free | column GPRD; 15 spike episodes in the top 1% of days, 135 in the top 5% (10-day gap); 3 of 5 known events in the top 5% of days; last value 4 days old |
| Trade and tariff actions | Trade policy uncertainty index, daily (matteoiacoviello.com) | partial | 2015-01-01 | 2026-11-23 | 17 | free | column TPUD_index; 8 spike episodes in the top 1% of days, 17 in the top 5% (10-day gap); 1 of 4 known events in the top 5% of days; last value 4 days old |
| Elections and policy shocks | Economic policy uncertainty index, daily (FRED USEPUINDXD) | pass | 1985-01-01 | 2026-11-26 | 131 | free | column USEPUINDXD; 42 spike episodes in the top 1% of days, 131 in the top 5% (10-day gap); 2 of 3 known events in the top 5% of days; last value 1 days old |
| Elections and policy shocks | US federal election days (fixed by law: first Tuesday after the first Monday in November) | pass | 1990-11-06 | 2026-11-03 | 8 presidential, 9 midterm since 1994 | free | computed; matches 5 known dates |
| Energy and commodity supply shocks | WTI oil price, daily (FRED DCOILWTICO) | pass | 1986-01-02 | 2026-11-24 |  | free | last value 3 days old |
| Energy and commodity supply shocks | OPEC website: meeting press releases | fail |  |  |  | free | www.opec.org: HTTP 403 |
| Major regulatory actions | Federal Register API: final rules marked significant, by agency | pass | 1995 | 2026 | 9521 | free | significant flag present from 1995; median 294 a year |
| Trade and tariff actions | Federal Register API: USTR documents and presidential proclamations mentioning tariffs | pass | 1994 | 2026 | 1398 | free | 274 proclamations, 1124 USTR documents |
| Guidance changes | Sharadar 8-K events table (items 2.02, 7.01) | pass | 1996-10-09 | 2026-11-25 | 647107 | already paid (Sharadar bundle) | 647,107 item filings since Aug 2004 |
| Mergers and acquisitions | Sharadar 8-K events table (items 1.01, 2.01) | pass | 1994-01-04 | 2026-11-25 | 238124 | already paid (Sharadar bundle) | 238,124 item filings since Aug 2004 |
| Leadership changes | Sharadar 8-K events table (items 5.02) | pass | 1994-12-05 | 2026-11-25 | 236988 | already paid (Sharadar bundle) | 236,988 item filings since Aug 2004 |
| Capital structure breaks | Sharadar 8-K events table (items 8.01, 3.02) | pass | 1994-01-04 | 2026-11-25 | 735112 | already paid (Sharadar bundle) | 735,112 item filings since Aug 2004 |
| Accounting and legal trouble | Sharadar 8-K events table (items 4.01, 4.02, 3.01) | pass | 2004-08-23 | 2026-11-25 | 40843 | already paid (Sharadar bundle) | 40,843 item filings since Aug 2004 |
| Distress and restructuring | Sharadar 8-K events table (items 1.03, 2.04, 2.05) | pass | 1994-01-05 | 2026-11-25 | 12510 | already paid (Sharadar bundle) | 12,510 item filings since Aug 2004 |
| Capital structure breaks | Sharadar corporate actions: dividend history | pass | 1997-12-31 | 2026-11-25 | 4131 | already paid (Sharadar bundle) | 13,843 payers; 3,137 cuts of 25% or more by steady payers and 994 stops (200+ days without a payment), splits removed |
| Mergers and acquisitions | Sharadar corporate actions: completed acquisitions and mergers (target side) | pass | 1998-01-07 | 2026-11-20 | 8270 | already paid (Sharadar bundle) | acquisitionby 8,134 and mergerfrom 136, each with the other party's ticker; completion dates, not announcement dates |
| Distress and restructuring | Sharadar corporate actions: bankruptcy or liquidation delistings | pass | 1998-01-06 | 2026-11-20 | 3337 | already paid (Sharadar bundle) | the delisting end of a bankruptcy; the filing itself is 8-K item 1.03 |
| Accounting and legal trouble | Sharadar corporate actions: regulatory delistings | pass | 1997-12-31 | 2026-11-25 | 1010 | already paid (Sharadar bundle) | the delisting itself; the earlier exchange notice is 8-K item 3.01 |
| Company events (all 8-K types) | Cross-check: Sharadar item codes vs SEC filing index, 8 companies since 2015 | pass | 2015-01-01 | 2026-11-27 | 687 | free | 98% of SEC's (date, item) pairs found in Sharadar (687 on filing date, 405 on event date); Sharadar has 964 pairs; SEC gives the acceptance time for 610 8-Ks (needed for the after-4 PM rule) |
| Activist stakes | SEC EDGAR full-text search: SC 13D, SCHEDULE 13D | pass | 2001-01-01 | 2026-11-27 | about 1,586 a quarter | free | 10 sample quarters, 2001 on; complete index from 1993 needs SEC_USER_AGENT |
| Mergers and acquisitions | SEC EDGAR full-text search: SC TO-T, SC 14D9 | pass | 2001-01-01 | 2026-11-27 | about 200 a quarter | free | 10 sample quarters, 2001 on; complete index from 1993 needs SEC_USER_AGENT |
| Mergers and acquisitions | SEC EDGAR full-text search: DEFM14A, PREM14A | pass | 2001-01-01 | 2026-11-27 | about 87 a quarter | free | 10 sample quarters, 2001 on; complete index from 1993 needs SEC_USER_AGENT |
| Capital structure breaks | SEC EDGAR full-text search: 424B4, 424B5, S-3 | pass | 2001-01-01 | 2026-11-27 | about 1,155 a quarter | free | 10 sample quarters, 2001 on; complete index from 1993 needs SEC_USER_AGENT |
| Accounting and legal trouble | SEC EDGAR full-text search: NT 10-K, NT 10-Q | pass | 2001-01-01 | 2026-11-27 | about 824 a quarter | free | 10 sample quarters, 2001 on; complete index from 1993 needs SEC_USER_AGENT |
| Leadership changes | SEC EDGAR full-text search: 8-Ks naming the CEO or CFO with 'resign' | pass | 2001-01-01 | 2026-11-27 | 4,574 CEO hits in 2015 | free | 2015: CEO 4,574 hits (83 of 100 sampled tagged item 5.02), CFO 3,806 hits; 2001: 1,371 CEO hits (search covers 2001 on) |

## Notes

- **gpr:** File: data_gpr_daily_recent.xls (sheet Sheet1).
- **tpu:** Files linked on the TPU page: tpu_web_latest.xlsx, firm_tpu.csv
- **tpu:** TPU_DAILY first rows: DATE, NUMBER_ARTICLES, TPUD_ARTICLES, TPUD_index, TPUD_index_MA7, TPUD_index_MA30 / 2015-01-01 00:00:00, 690, 0, 0, None, None / 2015-01-02 00:00:00, 726, 1, 13.7741046831955, None, None / 2015-01-03 00:00:00, 746, 1, 13.4048257372654, None, None
- **tpu:** tpu_web_latest.xlsx: sheets ReadMe (37 rows), Series_description (5 rows), TPU_MONTHLY (803 rows), TPU_QUARTERLY (267 rows), TPU_DAILY (4346 rows); daily column TPUD_index in TPU_DAILY
- **tpu:** firm_tpu.csv: sheets csv (119954 rows); no daily date/TPU column found
- **fr:** Agencies with the most significant final rules: Health and Human Services Department (1323), Environmental Protection Agency (845), Transportation Department (839), Agriculture Department (817), Labor Department (626), Centers for Medicare & Medicaid Services (596), Defense Department (546), Commerce Department (496), Interior Department (490), Treasury Department (397), Homeland Security Department (386), Housing and Urban Development Department (378)
- **sharadar:** Events table columns: ticker, date, eventcodes
- **sharadar:** Actions table columns: date, action, ticker, name, value, contraticker, contraname
- **sharadar:** Sample acquisitionby rows (date, ticker, other party): 2026-11-19 UTZ (UTZ BRANDS INC) acquisitionby N/A (Intersnack Group GmbH & Co); 2026-11-18 SSTI (SOUNDTHINKING INC) acquisitionby N/A (Transom Capital Group LLC); 2026-11-18 LXFR (LUXFER HOLDINGS PLC) acquisitionby N/A (WYNNCHURCH CAPITAL PARTNERS LP)
- **sharadar:** Sharadar code 34 rows with no matching 8-K item: SC 13G/A 98, SCHEDULE 13G/A 46, 424B2 29, FWP 27, SCHEDULE 13G 22 (SEC forms that company filed that day)
- **sharadar:** Sharadar code 35 rows with no matching 8-K item: 4 18, SC 13D/A 17, SCHEDULE 13D/A 7, FWP 4, 424B2 4 (SEC forms that company filed that day)
- **sharadar:** Sharadar code 37 rows with no matching 8-K item: SC TO-T/A 19, SC TO-C 8, 8-K 8, 4 5, 425 5 (SEC forms that company filed that day)
- **sharadar:** Sharadar code 52 rows with no matching 8-K item: 8-K/A 7, 10-Q 2, (nothing filed that day) 2, 4 1, 3 1 (SEC forms that company filed that day)
- **sharadar:** Sharadar code 41 rows with no matching 8-K item: 10-K 1, 13F-HR 1, 4 1, CORRESP 1, POS AM 1 (SEC forms that company filed that day)
- **sharadar:** Sharadar code 57 rows with no matching 8-K item: 8-K/A 2, 4 1, 10-Q 1 (SEC forms that company filed that day)
- **sharadar:** Sharadar code 81 rows with no matching 8-K item: 424B2 1 (SEC forms that company filed that day)
- **edgar:** Ownership filings listed under the 8 companies' own SEC numbers: SCHEDULE 13G/A 129, SC 13G/A 116, SCHEDULE 13G 54, SC 13G 22, SC 13D/A 18, SCHEDULE 13D/A 15, SCHEDULE 13D 3, SC 13D 2
- **edgar:** Quarterly index files (complete list from 1993): www.sec.gov: HTTP 403. SEC wants a contact in the User-Agent; set the SEC_USER_AGENT secret to read them.
- **edgar:** Full-text search query word used for form counts: (none), none worked. Counts of 10,000 show as 10000+ (the search caps its totals there).
- **edgar:** 13D subject company: 503 of 511 sampled 13D hits list two or more SEC numbers (filer and subject), so the target can be tied to a stock without opening the filing.

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
