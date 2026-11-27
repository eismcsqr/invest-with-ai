# Event data check report

Run: 2026-11-27. Written by `scripts/build_event_data.py`. Event types: `docs/event-types.md`; sources: `docs/event-sources.md`; write-up: `docs/event-data.md`.

## Events by type

| Type | Level | Main | Cross-check | Unmapped | First | Last |
|---|---|---|---|---|---|---|
| Geopolitical shocks | market | 145 | 0 | 0 | 1987-04-28 | 2026-11-18 |
| Trade and tariff actions | market | 0 | 38 | 0 | 2016-03-07 | 2026-11-02 |
| Elections and policy shocks | market | 219 | 0 | 0 | 1987-10-31 | 2026-11-03 |
| Energy and commodity supply shocks | market | 123 | 0 | 0 | 1988-10-24 | 2026-11-23 |
| Major regulatory actions | | 0 | 0 | 0 | | |
| Guidance changes | | 0 | 0 | 0 | | |
| Mergers and acquisitions | | 0 | 0 | 0 | | |
| Leadership changes | | 0 | 0 | 0 | | |
| Capital structure breaks | | 0 | 0 | 0 | | |
| Accounting and legal trouble | | 0 | 0 | 0 | | |
| Distress and restructuring | | 0 | 0 | 0 | | |
| Activist stakes | | 0 | 0 | 0 | | |

## Checks

| Check | Status | Detail |
|---|---|---|
| Source: Federal Register: tariff actions | fail | RuntimeError: www.federalregister.gov: HTTP 400 |
| Source: Federal Register: significant final rules | fail | RuntimeError: www.federalregister.gov: HTTP 400 |
| Dates: market-wide events | pass | 525 events; 0 dated after today; 0 public after day 0; 0 with day 0 before the event date; 0 with no trading day within 5 days (no returns) |
| Dates: regulatory events | pass | 0 events; 0 dated after today; 0 public after day 0; 0 with day 0 before the event date; 0 with no trading day within 5 days (no returns) |
| Spot check: known events present | fail | Russia invades Ukraine (2022-02-24): not found; oil price war crash (2020-03-09): found; oil jump (2008-09-22): found; 2016 election (2016-11-08): found; reciprocal tariffs (2025-04-02): not found; steel and aluminum tariffs (Section 232) (2018-03-08): not found |
| Spot check: energy on the Mar 9, 2020 oil crash | pass | energy minus market -11.9% that day |
| EDGAR search pulled | pass | 4665 query-months fetched, 0 from cache, 0 missing, in 1,348s |
| Dates: company events | pass | 0 events; 0 dated after today; 0 public after day 0; 0 with day 0 before the event date; 0 with no trading day within 5 days (no returns) |
| No look-ahead: Geopolitical risk spikes | pass | 138 events up to 2025-11-27 with all data, 138 with data cut at 2025-11-27; identical |
| No look-ahead: Policy uncertainty spikes | pass | 200 events up to 2025-11-27 with all data, 200 with data cut at 2025-11-27; identical |
| No look-ahead: Oil price moves | pass | 111 events up to 2025-11-27 with all data, 111 with data cut at 2025-11-27; identical |
| No look-ahead: off-cycle guidance | pass | 3,000 companies' off-cycle 2.02 days up to 2025-11-27 (6,791 events) rerun with later filings deleted: 0 companies differ |
| No look-ahead: dividend breaks | pass | 3,000 payers' breaks up to 2025-11-27 (1,081 events) rerun with later payments and prices deleted: 0 payers differ |
| Count: Geopolitical shocks (risk index spike) | pass | 145 episodes (write-up: 135 with whole-sample top-5% days; this rule uses only earlier days) |
| Count: Elections and policy shocks (policy uncertainty spike) | pass | 202 episodes (write-up: 131 with whole-sample top-5% days; this rule uses only earlier days) |
| Count: elections | pass | 8 presidential and 9 midterm since 1994 (write-up: 8 and 9, before the Nov 3, 2026 midterm) |
| Count: Energy and commodity supply shocks | pass | 123 big one-day oil moves since 1988 |
| Count: Trade and tariff actions | fail | 0 days with tariff actions (main) |
| Count: EDGAR SC 13D | pass | about 1,483 documents a quarter (write-up: about 1,586) |
| Count: EDGAR SC TO-T | pass | about 143 documents a quarter (write-up: about 200) |

## Event days against ordinary days (sector level, day 0)

Mean absolute group-minus-market move on event days, against every day since 1994, French's 12 groups. A ratio above 1 means event days move groups more than usual.

| Type | Events | Event days (%) | All days (%) | Ratio |
|---|---|---|---|---|
| Geopolitical shocks | 145 | 0.606 | 0.563 | 1.08 |
| Trade and tariff actions | 0 |  | 0.563 |  |
| Elections and policy shocks | 219 | 0.620 | 0.563 | 1.10 |
| Energy and commodity supply shocks | 123 | 0.859 | 0.563 | 1.53 |
| Major regulatory actions | 0 |  | 0.563 |  |

## Gaps

- Federal Register: tariff actions: source failed this run (RuntimeError).
- Federal Register: significant final rules: source failed this run (RuntimeError).
- Sector moves wait for French's data, which ends 2026-09-30: Geopolitical shocks 3, Trade and tariff actions 1, Elections and policy shocks 2, Energy and commodity supply shocks 4 events have no full set of windows yet.
- Company filings not tied to a stock: any officer or director change (8-K 5.02): not a common stock in Sharadar's ticker list 237,661, 13D stake (Sharadar code 35, inferred): not a common stock in Sharadar's ticker list 155,890, Reg FD disclosure away from results, mostly presentations (8-K 7.01): not a common stock in Sharadar's ticker list 148,363, late quarterly report notice (NT 10-Q): no listed company 69,214, acquisition or sale completed, either side (8-K 2.01): not a common stock in Sharadar's ticker list 67,098, leadership: no listed company 54,882, 13D stake of 5% or more: no listed company 46,886, late annual report notice (NT 10-K): no listed company 39,846, new share offering: no listed company 37,577, tender offer (Sharadar code 37, inferred): not a common stock in Sharadar's ticker list 34,867, delisting or listing-rule notice (8-K 3.01): not a common stock in Sharadar's ticker list 25,130, results release away from the regular schedule (8-K 2.02): not a common stock in Sharadar's ticker list 19,650
- Filing times: Sharadar and EDGAR search give filing dates only, so the main company window is days 0 and 1, which covers filings after the 4 PM close.
- Merger announcements are picked out by the deal filing that follows them: the 8-K was public that day, but choosing it uses a later filing (flagged later_filing).
- OPEC meeting dates are not in v1 (agreed Nov 27); energy shocks are big oil moves.
- SEC enforcement actions are not in v1 (names only, no company numbers).

## Notes

- Geopolitical risk index: 1985-01-01 to 2026-11-23, column GPRD.
