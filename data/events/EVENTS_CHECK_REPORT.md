# Event calendar check report

Run date: 2026-11-26

**271 Fed decision days for the rates test (1994-02-04 to 2026-10-28), 0 target changes without a decision day, 15 of 15 Fed spot checks and 5 of 5 first-print spot checks pass.**

## Fed decision days

Parsed 318 meetings, calls and notation votes from the Fed's FOMC pages (1994 onward; the FOMC began announcing decisions in February 1994).

| Type | Count | With a rate change | In the rates test |
|---|---|---|---|
| scheduled | 262 | 83 | yes |
| unscheduled rate change | 9 | 9 | yes |
| unscheduled statement | 8 | 0 | no |

Unscheduled rate changes:

- 1994-04-18: 3.50% to 3.75% (April 18 Conference Call - 1994)
- 1998-10-15: 5.25% to 5.00% (October 15 Conference Call - 1998)
- 2001-01-03: 6.50% to 6.00% (January 3 Conference Call - 2001)
- 2001-04-18: 5.00% to 4.50% (April 18 Conference Call - 2001)
- 2001-09-17: 3.50% to 3.00% (September 17 Conference Call - 2001)
- 2008-01-22: 4.25% to 3.50% (January 21 Conference Call - 2008)
- 2008-10-08: 2.00% to 1.50% (October 7 Conference Call - 2008)
- 2020-03-03: 1.50-1.75% to 1.00-1.25% (March 2 (unscheduled) Meeting - 2020)
- 2020-03-15: 1.00-1.25% to 0.00-0.25% (March 15 (unscheduled) Meeting - 2020)

Unscheduled statements with no rate change (kept, but left out of the rates test; dates are the call date unless the Fed page gives a release date):

- 2007-08-10: August 10 Conference Call - 2007 (date of the call; announcement may have come the next morning)
- 2007-08-16: August 16 Conference Call - 2007 (date of the call; announcement may have come the next morning)
- 2008-03-10: March 10 Conference Call - 2008 (date of the call; announcement may have come the next morning)
- 2010-05-09: May 9 Conference Call - 2010 (date of the call; announcement may have come the next morning)
- 2019-10-11: October 4 (unscheduled) - 2019 (released date from the Fed page)
- 2020-03-23: March 23 (notation vote) - 2020 (released date from the Fed page)
- 2020-08-27: August 27 (notation vote) - 2020 (date of the vote)
- 2025-08-22: August 22 (notation vote) 2025 (date of the vote)

**Schedule check:** the FOMC holds eight scheduled meetings a year. Years with a different count of scheduled decision days (1994 to 2026):

- 2020: 7 scheduled decision days (cancelled: March 17-18 (cancelled) Meeting - 2020)
- 2026: 7 scheduled decision days (not held yet: December 8-9* 2026)

Meetings on the Fed's pages with no statement, left out as not a decision day (statements follow every meeting since May 1999):

- September 15 Meeting - 2003

**Cross-check against FRED's target rate:** every change in DFEDTAR / DFEDTARU / DFEDTARL since February 1994 should fall on a decision day or the day after.

- All target changes matched a decision day.

**Spot checks** (target before and after, from the Fed's statements):

| Date | Expected | Pass |
|---|---|---|
| 1994-02-04 | 3.00% to 3.25% | pass |
| 2001-01-03 | 6.50% to 6.00% | pass |
| 2001-09-17 | 3.50% to 3.00% | pass |
| 2008-12-16 | 1.00% to 0.00-0.25% | pass |
| 2015-12-16 | 0.00-0.25% to 0.25-0.50% | pass |
| 2020-03-03 | 1.50-1.75% to 1.00-1.25% | pass |
| 2020-03-15 | 1.00-1.25% to 0.00-0.25% | pass |
| 2022-06-15 | 0.75-1.00% to 1.50-1.75% | pass |
| 2024-09-18 | 5.25-5.50% to 4.75-5.00% | pass |
| 2003-09-16 | 1.00% to 1.00% | pass |
| 2013-05-01 | 0.00-0.25% to 0.00-0.25% | pass |
| 2017-02-01 | 0.50-0.75% to 0.50-0.75% | pass |
| 2017-11-01 | 1.00-1.25% to 1.00-1.25% | pass |
| 2018-08-01 | 1.75-2.00% to 1.75-2.00% | pass |
| 2019-05-01 | 2.25-2.50% to 2.25-2.50% | pass |

## Data releases and first prints

| Release | Release dates on file | First prints from | First prints | Late first prints | Revision-only dates (no new month) | First-print dates missing from FRED's release calendar |
|---|---|---|---|---|---|---|
| Consumer price index | 625 (from 1976-06-22) | 1972-08-22 | 652 | 1 | 20 | 0 |
| Personal income and outlays (PCE) | 618 (from 1976-06-16) | 1979-12-18 | 316 | 7 | 16 | 0 |
| Advance retail sales | 633 (from 1976-06-10) | 2001-07-13 | 305 | 2 | 21 | 0 |

First prints count the headline series (CPI, PCE prices, retail sales); the start date is the earliest first print of any series in the release (PCE spending goes back to 1979). Revision-only dates are publications that added no new month, such as CPI's February seasonal-factor update or annual retail sales revisions; they are labelled and left out of the averages below. Release dates before the vintage coverage can't be checked this way.

Months with no first print (a skipped month in the vintage history):

- CPI: after 2025-09, next is 2025-11
- Core CPI: after 2025-09, next is 2025-11

Late first prints since 2010 (delayed releases, for example during government shutdowns):

- CPI 2025-10: released 2025-12-18, late (78 days after month start)
- Core CPI 2025-10: released 2025-12-18, late (78 days after month start)
- Core PCE prices 2018-12: released 2019-03-01, late (90 days after month start)
- Core PCE prices 2019-01: released 2019-03-29, late (87 days after month start)
- Core PCE prices 2019-02: released 2019-04-29, late (87 days after month start)
- Core PCE prices 2025-09: released 2025-12-05, late (95 days after month start)
- Core PCE prices 2025-10: released 2026-01-22, late (113 days after month start)
- Core PCE prices 2025-11: released 2026-01-22, late (82 days after month start)
- Core PCE prices 2025-12: released 2026-02-20, late (81 days after month start)
- PCE prices 2018-12: released 2019-03-01, late (90 days after month start)
- PCE prices 2019-01: released 2019-03-29, late (87 days after month start)
- PCE prices 2019-02: released 2019-04-29, late (87 days after month start)
- PCE prices 2025-09: released 2025-12-05, late (95 days after month start)
- PCE prices 2025-10: released 2026-01-22, late (113 days after month start)
- PCE prices 2025-11: released 2026-01-22, late (82 days after month start)
- PCE prices 2025-12: released 2026-02-20, late (81 days after month start)
- PCE spending 2018-12: released 2019-03-01, late (90 days after month start)
- PCE spending 2019-01: released 2019-03-29, late (87 days after month start)
- PCE spending 2019-02: released 2019-04-29, late (87 days after month start)
- PCE spending 2025-09: released 2025-12-05, late (95 days after month start)
- PCE spending 2025-10: released 2026-01-22, late (113 days after month start)
- PCE spending 2025-11: released 2026-01-22, late (82 days after month start)
- PCE spending 2025-12: released 2026-02-20, late (81 days after month start)
- Retail sales 2025-09: released 2025-11-25, late (85 days after month start)
- Retail sales 2025-10: released 2025-12-16, late (76 days after month start)

**Spot checks** (month-on-month change as first published, rounded to 0.1):

| Print | Released | Published | Computed | Pass |
|---|---|---|---|---|
| CPI 2022-05 | 2022-06-10 | +1.0% | +0.97% | pass |
| CPI 2022-08 | 2022-09-13 | +0.1% | +0.12% | pass |
| Core CPI 2022-08 | 2022-09-13 | +0.6% | +0.57% | pass |
| CPI 2023-10 | 2023-11-14 | +0.0% | +0.04% | pass |
| Retail sales 2020-04 | 2020-05-15 | -16.4% | -16.45% | pass |

## Market-reaction surprise (the spec's measure)

Change in the 2-year Treasury yield from the previous trading day's close to the event day's close. Ordinary days are trading days with none of these events, over the same years.

| Event | Days with a 2-year move | Average size on event days (bp) | Average size on ordinary days (bp) | Days sharing another event |
|---|---|---|---|---|
| Fed decision (rates test) | 271 | 5.3 | 3.6 | 36 |
| Consumer price index | 605 | 5.2 | 4.7 | 78 |
| Personal income and outlays (PCE) | 601 | 4.9 | 4.7 | 18 |
| Advance retail sales | 612 | 5.6 | 4.7 | 73 |

Event days without a 2-year move: 1 (latest: 2026-11-25 pce).
Stock-market returns come from Kenneth French's daily file, which runs about two months behind, so recent events have no scenario label yet.

Examples:

| Date | Event | Detail | 2-year change (bp) | Market return (%) | Scenario |
|---|---|---|---|---|---|
| 2008-12-16 | cpi | CPI 2008-11: -1.68% m/m; Core CPI 2008-11: +0.02% m/m | -10 | 5.15 | easing or cooling inflation |
| 2008-12-16 | fomc | Target 1.00% to 0.00-0.25% | -10 | 5.15 | easing or cooling inflation |
| 2022-06-15 | fomc | Target 0.75-1.00% to 1.50-1.75% | -25 | 1.55 | easing or cooling inflation |
| 2022-06-15 | retail_sales | Retail sales 2022-05: -0.27% m/m | -25 | 1.55 | easing or cooling inflation |
| 2022-09-13 | cpi | CPI 2022-08: +0.12% m/m; Core CPI 2022-08: +0.57% m/m | 17 | -4.28 | tightening or inflation news |
