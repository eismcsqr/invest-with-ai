# Event data check report

Run: 2026-11-27. Written by `scripts/build_event_data.py`. Event types: `docs/event-types.md`; sources: `docs/event-sources.md`; write-up: `docs/event-data.md`.

## Events by type

| Type | Level | Main | Cross-check | Unmapped | First | Last |
|---|---|---|---|---|---|---|
| Geopolitical shocks | market | 155 | 0 | 0 | 1987-04-28 | 2026-11-18 |
| Trade and tariff actions | market | 344 | 38 | 0 | 1994-06-30 | 2026-11-10 |
| Elections and policy shocks | market | 237 | 0 | 0 | 1987-10-31 | 2026-11-03 |
| Energy and commodity supply shocks | market | 123 | 0 | 0 | 1988-10-24 | 2026-11-23 |
| Major regulatory actions | industry | 7,327 | 0 | 2,194 | 1995-01-06 | 2026-11-27 |
| Guidance changes | company | 19,650 | 148,363 | 0 | 2005-09-06 | 2026-11-25 |
| Mergers and acquisitions | company | 25,191 | 101,965 | 0 | 1994-01-04 | 2026-11-25 |
| Leadership changes | company | 45,024 | 237,661 | 0 | 1994-12-05 | 2026-11-27 |
| Capital structure breaks | company | 33,364 | 0 | 0 | 1998-11-04 | 2026-11-27 |
| Accounting and legal trouble | company | 70,867 | 0 | 0 | 1994-01-13 | 2026-11-25 |
| Distress and restructuring | company | 17,267 | 0 | 0 | 1994-01-05 | 2026-11-25 |
| Activist stakes | company | 22,660 | 155,890 | 0 | 1993-11-08 | 2026-11-27 |

## Checks

| Check | Status | Detail |
|---|---|---|
| Trade actions: documents read and kept | pass | 1,456 documents mention tariffs (274 proclamations, 58 executive orders, 1124 USTR); 403 kept as actions on 344 days (write-up: 274 proclamations and 1,124 USTR documents mention tariffs) |
| Regulation: every significant rule read | pass | 9,521 rules read; the API counts 9,521 (write-up: 9,521) |
| Regulation: rules tied to an industry group | pass | 7,327 of 9,521 (77%) map to a French group through config/regulation_agencies.csv |
| Dates: market-wide events | pass | 897 events; 0 dated after today; 0 public after day 0; 0 with day 0 before the event date; 0 with no trading day within 5 days (no returns) |
| Dates: regulatory events | pass | 9,521 events; 0 dated after today; 0 public after day 0; 0 with day 0 before the event date; 1 with no trading day within 5 days (no returns) |
| Spot check: known events present | pass | Russia invades Ukraine (2022-02-24): found; oil price war crash (2020-03-09): found; oil jump (2008-09-22): found; 2016 election (2016-11-08): found; reciprocal tariffs (2025-04-02): found; steel and aluminum tariffs (Section 232) (2018-03-08): found |
| Spot check: energy on the Mar 9, 2020 oil crash | pass | energy minus market -11.9% that day |
| EDGAR search pulled | pass | 60 query-months fetched, 4605 from cache, 0 missing, in 15s |
| Dates: company events | pass | 877,902 events; 0 dated after today; 0 public after day 0; 0 with day 0 before the event date; 49,780 with no trading day within 5 days (no returns) |
| No look-ahead: Geopolitical risk spikes | pass | 147 events up to 2025-11-27 with all data, 147 with data cut at 2025-11-27; identical |
| No look-ahead: Policy uncertainty spikes | pass | 218 events up to 2025-11-27 with all data, 218 with data cut at 2025-11-27; identical |
| No look-ahead: Oil price moves | pass | 111 events up to 2025-11-27 with all data, 111 with data cut at 2025-11-27; identical |
| No look-ahead: off-cycle guidance | pass | 3,000 companies' off-cycle 2.02 days up to 2025-11-27 (6,791 events) rerun with later filings deleted: 0 companies differ |
| No look-ahead: dividend breaks | pass | 3,000 payers' breaks up to 2025-11-27 (1,402 events) rerun with later payments and prices deleted: 0 payers differ |
| Count: Geopolitical shocks (risk index spike) | pass | 145 episodes (write-up: 135 with whole-sample top-5% days; this rule uses only earlier days) |
| Count: Elections and policy shocks (policy uncertainty spike) | pass | 202 episodes (write-up: 131 with whole-sample top-5% days; this rule uses only earlier days) |
| Count: elections | pass | 8 presidential and 9 midterm since 1994 (write-up: 8 and 9, before the Nov 3, 2026 midterm) |
| Count: Energy and commodity supply shocks | pass | 123 big one-day oil moves since 1988 |
| Count: Trade and tariff actions | pass | 344 days with tariff actions (main) |
| Count: Sharadar code 13 | pass | 3,130 rows now vs 3,130 in the Nov 27 source check |
| Count: Sharadar code 21 | pass | 67,098 rows now vs 67,098 in the Nov 27 source check |
| Count: Sharadar code 22 | pass | 380,500 rows now vs 380,500 in the Nov 27 source check |
| Count: Sharadar code 24 | pass | 3,236 rows now vs 3,236 in the Nov 27 source check |
| Count: Sharadar code 25 | pass | 7,564 rows now vs 7,564 in the Nov 27 source check |
| Count: Sharadar code 31 | pass | 25,130 rows now vs 25,130 in the Nov 27 source check |
| Count: Sharadar code 35 | pass | 155,890 rows now vs 155,890 in the Nov 27 source check |
| Count: Sharadar code 37 | pass | 34,867 rows now vs 34,867 in the Nov 27 source check |
| Count: Sharadar code 40 | pass | 6,806 rows now vs 6,806 in the Nov 27 source check |
| Count: Sharadar code 41 | pass | 10,698 rows now vs 10,698 in the Nov 27 source check |
| Count: Sharadar code 42 | pass | 5,015 rows now vs 5,015 in the Nov 27 source check |
| Count: Sharadar code 52 | pass | 237,661 rows now vs 237,661 in the Nov 27 source check |
| Count: Sharadar code 71 | pass | 294,387 rows now vs 294,387 in the Nov 27 source check |
| Count: dividend cut of 25% or more | pass | 2,013 (write-up: 3,137; differences come from the point-in-time rules and one row per company and day) |
| Count: dividend stopped (no payment for 200 days) | pass | 1,163 (write-up: 994; differences come from the point-in-time rules and one row per company and day) |
| Count: target: deal completed | pass | 7,517 (write-up: 8,270; differences come from the point-in-time rules and one row per company and day) |
| Count: delisted after bankruptcy or liquidation | pass | 3,337 (write-up: 3,337; differences come from the point-in-time rules and one row per company and day) |
| Count: delisted by the exchange or regulator | pass | 1,010 (write-up: 1,010; differences come from the point-in-time rules and one row per company and day) |
| Count: Guidance changes (main rows) | pass | 19,650 company events |
| Count: Mergers and acquisitions (main rows) | pass | 25,191 company events |
| Count: Leadership changes (main rows) | pass | 45,024 company events |
| Count: Capital structure breaks (main rows) | pass | 33,364 company events |
| Count: Accounting and legal trouble (main rows) | pass | 70,867 company events |
| Count: Distress and restructuring (main rows) | pass | 17,267 company events |
| Count: Activist stakes (main rows) | pass | 22,660 company events |
| Count: EDGAR SC 13D | pass | about 1,483 documents a quarter (write-up: about 1,586) |
| Count: EDGAR SC TO-T | pass | about 143 documents a quarter (write-up: about 200) |

## Event days against ordinary days (sector level, day 0)

Mean absolute group-minus-market move on event days, against every day since 1994, French's 12 groups. A ratio above 1 means event days move groups more than usual.

| Type | Events | Event days (%) | All days (%) | Ratio |
|---|---|---|---|---|
| Geopolitical shocks | 155 | 0.606 | 0.563 | 1.08 |
| Trade and tariff actions | 344 | 0.636 | 0.563 | 1.13 |
| Elections and policy shocks | 237 | 0.639 | 0.563 | 1.14 |
| Energy and commodity supply shocks | 123 | 0.859 | 0.563 | 1.53 |
| Major regulatory actions | 7327 | 0.595 | 0.563 | 1.06 |

## Company events: moves against peers

Stock minus its French group (equal-weighted peers). Abs d0 is the median absolute day-0 move beyond peers; the ordinary-day figure is the same over a sample of every stock-day. d01 is days 0 and 1; post20 is days 2 to 21 (drift). Per-company rows stay on the runner (licence).

| Type | Subtype | Role | Events | Companies | With returns | Median abs d0 (%) | Ordinary (%) | Ratio | Median d01 (%) | Median post20 (%) | Picked with a later filing |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Guidance changes | Reg FD disclosure away from results, mostly presentations (8-K 7.01) | cross-check | 148,363 | 7,709 | 146,550 | 1.328 | 1.254 | 1.06 | 0.007 | -0.533 | 0 |
| Guidance changes | results release away from the regular schedule (8-K 2.02) | main | 19,650 | 6,651 | 19,350 | 2.372 | 1.254 | 1.89 | -0.550 | -1.182 | 0 |
| Mergers and acquisitions | acquisition or sale completed, either side (8-K 2.01) | cross-check | 67,098 | 11,700 | 56,023 | 1.618 | 1.254 | 1.29 | -0.136 | -1.023 | 0 |
| Mergers and acquisitions | tender offer (Sharadar code 37, inferred) | cross-check | 34,867 | 3,904 | 32,368 | 1.227 | 1.254 | 0.98 | 0.076 | -0.684 | 0 |
| Mergers and acquisitions | buyer: deal announced (from the target's filing) | main | 2,100 | 1,223 | 1,945 | 1.276 | 1.254 | 1.02 | -0.405 | -0.466 | 2,100 |
| Mergers and acquisitions | buyer: deal completed | main | 5,181 | 2,619 | 4,692 | 1.195 | 1.254 | 0.95 | 0.095 | -0.487 | 0 |
| Mergers and acquisitions | target: deal announced (8-K 1.01 before the deal filing) | main | 4,577 | 4,329 | 4,561 | 3.542 | 1.254 | 2.82 | 3.027 | -0.239 | 4,577 |
| Mergers and acquisitions | target: deal completed | main | 7,517 | 7,482 | 15 | 0.920 | 1.254 | 0.73 | 2.377 | -4.576 | 0 |
| Mergers and acquisitions | target: merger proxy filed | main | 4,953 | 4,639 | 4,927 | 0.836 | 1.254 | 0.67 | -0.046 | -0.752 | 0 |
| Mergers and acquisitions | target: tender offer filed | main | 863 | 798 | 840 | 0.995 | 1.254 | 0.79 | 0.255 | -0.381 | 0 |
| Leadership changes | any officer or director change (8-K 5.02) | cross-check | 237,661 | 11,165 | 228,275 | 1.325 | 1.254 | 1.06 | -0.192 | -0.849 | 0 |
| Leadership changes | CEO exit (effective immediately) | main | 4,476 | 3,128 | 4,333 | 1.690 | 1.254 | 1.35 | -0.250 | -1.258 | 0 |
| Leadership changes | CEO exit (other wording) | main | 31,037 | 8,010 | 29,492 | 1.383 | 1.254 | 1.10 | -0.259 | -0.817 | 0 |
| Leadership changes | CFO exit (effective immediately) | main | 876 | 712 | 858 | 1.776 | 1.254 | 1.42 | -0.306 | -1.838 | 0 |
| Leadership changes | CFO exit (other wording) | main | 8,635 | 4,201 | 8,526 | 1.267 | 1.254 | 1.01 | -0.325 | -0.724 | 0 |
| Capital structure breaks | dividend cut of 25% or more | main | 2,013 | 1,463 | 1,995 | 1.335 | 1.254 | 1.06 | -0.129 | -1.146 | 0 |
| Capital structure breaks | dividend stopped (no payment for 200 days) | main | 1,163 | 1,068 | 1,153 | 1.705 | 1.254 | 1.36 | -0.365 | -1.292 | 0 |
| Capital structure breaks | first dividend | main | 1,631 | 1,631 | 1,614 | 1.278 | 1.254 | 1.02 | 0.450 | -0.792 | 0 |
| Capital structure breaks | new share offering | main | 4,054 | 2,485 | 4,036 | 2.890 | 1.254 | 2.30 | -0.773 | -1.801 | 0 |
| Capital structure breaks | new share offering | main | 24,503 | 3,880 | 24,445 | 1.943 | 1.254 | 1.55 | -1.125 | -1.296 | 0 |
| Accounting and legal trouble | auditor change (8-K 4.01) | main | 10,698 | 4,988 | 9,828 | 1.665 | 1.254 | 1.33 | -0.423 | -1.925 | 0 |
| Accounting and legal trouble | auditor change, pre-2004 item | main | 6,806 | 3,558 | 5,029 | 1.820 | 1.254 | 1.45 | -0.306 | -1.686 | 0 |
| Accounting and legal trouble | delisted by the exchange or regulator | main | 1,010 | 1,010 | 0 | 6.885 | 1.254 | 5.49 |  |  | 0 |
| Accounting and legal trouble | delisting or listing-rule notice (8-K 3.01) | main | 25,130 | 7,709 | 21,057 | 2.439 | 1.254 | 1.94 | -1.285 | -3.443 | 0 |
| Accounting and legal trouble | late annual report notice (NT 10-K) | main | 9,013 | 4,504 | 8,890 | 2.122 | 1.254 | 1.69 | -0.809 | -2.649 | 0 |
| Accounting and legal trouble | late quarterly report notice (NT 10-Q) | main | 13,195 | 4,740 | 13,028 | 1.887 | 1.254 | 1.50 | -0.532 | -3.480 | 0 |
| Accounting and legal trouble | restatement: past results no longer reliable (8-K 4.02) | main | 5,015 | 3,167 | 4,843 | 1.477 | 1.254 | 1.18 | -0.575 | -0.983 | 0 |
| Distress and restructuring | bankruptcy or receivership (8-K 1.03) | main | 3,130 | 1,716 | 1,541 | 6.605 | 1.254 | 5.27 | -4.072 | -5.994 | 0 |
| Distress and restructuring | debt default or acceleration trigger (8-K 2.04) | main | 3,236 | 1,843 | 2,836 | 2.252 | 1.254 | 1.80 | -1.295 | -2.728 | 0 |
| Distress and restructuring | delisted after bankruptcy or liquidation | main | 3,337 | 3,337 | 0 | 4.417 | 1.254 | 3.52 |  |  | 0 |
| Distress and restructuring | layoffs, closures or exit costs (8-K 2.05) | main | 7,564 | 2,950 | 7,445 | 1.836 | 1.254 | 1.46 | -0.563 | -1.092 | 0 |
| Activist stakes | 13D stake (Sharadar code 35, inferred) | cross-check | 155,890 | 13,864 | 134,894 | 1.581 | 1.254 | 1.26 | 0.020 | -1.197 | 0 |
| Activist stakes | 13D stake of 5% or more | main | 21,109 | 8,957 | 20,894 | 1.707 | 1.254 | 1.36 | 0.299 | -1.200 | 0 |
| Activist stakes | 13D stake of 5% or more | main | 1,551 | 1,220 | 1,498 | 2.128 | 1.254 | 1.70 | 0.152 | -2.294 | 0 |

## Gaps

- Regulation: agencies not mapped to an industry (rules kept, role unmapped): Personnel Management Office (201), Small Business Administration (164), Homeland Security Department (151), Social Security Administration (148), Occupational Safety and Health Administration (140), State Department (131), Farm Credit Administration (124), Employment and Training Administration (99), General Services Administration (90), Justice Department (79)
- Sector moves wait for French's data, which ends 2026-09-30: Geopolitical shocks 3, Trade and tariff actions 7, Elections and policy shocks 2, Energy and commodity supply shocks 4, Major regulatory actions 39 events have no full set of windows yet.
- Company filings not tied to a stock: late quarterly report notice (NT 10-Q): no listed company 56,015, late annual report notice (NT 10-K): no listed company 30,832, 13D stake of 5% or more: no listed company 18,781, leadership: no listed company 9,813, new share offering: under 60 days of trading before (IPO) 5,100, new share offering: no listed company 2,466, 13D stake of 5% or more: ambiguous 2,402, merger proxy: no listed company 1,980, target: tender offer filed: no listed company 912, target: tender offer filed: ambiguous 748, leadership: ambiguous 8, merger proxy: ambiguous 5
- Filing times: Sharadar and EDGAR search give filing dates only, so the main company window is days 0 and 1, which covers filings after the 4 PM close.
- Merger announcements are picked out by the deal filing that follows them: the 8-K was public that day, but choosing it uses a later filing (flagged later_filing).
- OPEC meeting dates are not in v1 (agreed Nov 27); energy shocks are big oil moves.
- SEC enforcement actions are not in v1 (names only, no company numbers).

## Notes

- Geopolitical risk index: 1985-01-01 to 2026-11-23, column GPRD.
- Trade actions are dated on the signing day for presidential documents (the White House releases the text that day) and the publication day for USTR notices.
