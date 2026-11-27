# Events pillar: event data

**Built November 27, 2026** (tracker task "Event data"). `scripts/build_event_data.py` pulls each of the 12 event types agreed on Nov 27 (`docs/event-types.md`) from the source checked for it (`docs/event-sources.md`), writes one clean event table per level and lines every event up with sector and stock returns around it. `.github/workflows/event-data.yml` runs it every Saturday at 10 AM Pacific, after the company pull. Results of the latest run: `data/events/pull/EVENT_DATA_CHECK.md`.

## 1. What each type is built from

| Type | Level | Record | Rule |
|---|---|---|---|
| Geopolitical shocks | Market | Geopolitical risk index, daily | Index above the 95th percentile of all earlier days (two years of history first); a new episode needs 10 quiet days. Inside a running episode, a day above the 99th percentile and 25% above the episode's last recorded day is kept as an escalation (so Russia's invasion of Ukraine, weeks into an elevated stretch, gets its own day) |
| Trade and tariff actions | Market | Federal Register: presidential proclamations and executive orders, and USTR notices, that mention tariffs | Kept when the title is an actual action (Section 232 and 301 actions, new or changed duties, trade agreements); routine notices (comment requests, hearings, product exclusions, GSP reviews) dropped. One event per day. The trade policy uncertainty index's spikes are kept as a cross-check |
| Elections and policy shocks | Market | Election days (by law) and the policy uncertainty index, daily | Every presidential and midterm election since 1994; index spikes and escalations as for geopolitical risk |
| Energy and commodity supply shocks | Market | WTI oil price, daily | One-day moves bigger than 97.5% of earlier moves, split into jumps and drops (agreed Nov 27: oil moves now, OPEC dates later). The event method can tighten the cut-off from the percentile on each row |
| Major regulatory actions | Industry | Federal Register: final rules marked significant | Each rule tied to French groups through its agency (`config/regulation_agencies.csv`, 12 and 49 groups). Rules from agencies with no single industry (tax, labor, wildlife) are kept but marked unmapped |
| Guidance changes | Company | Sharadar 8-K item 2.02 | A results filing that doesn't fit the company's own schedule: no earlier 2.02 about one, two, three or four quarters before (within 10 days). Needs a year of earlier filings. Item 7.01 filed away from results is kept as a cross-check (mostly presentations) |
| Mergers and acquisitions | Company | SEC tender offers (SC TO-T) and merger proxies (PREM14A, DEFM14A); Sharadar completed deals; 8-K 1.01 | Targets and buyers separately: announcement, tender offer, proxy, completion |
| Leadership changes | Company | 8-Ks tagged item 5.02 that name the CEO or CFO with "resign" or "retire" (SEC full-text search) | Split into "effective immediately" wording (abrupt) and other wording (planned). All 5.02 filings kept as a cross-check |
| Capital structure breaks | Company | Sharadar dividend history; SEC 424B4 and 424B5 share offerings | Dividend cuts of 25% or more by steady payers, stops (200 days with no payment), first dividends; share offerings by companies already trading at least 60 days (424B5s kept only when they say "we are offering … shares of our common stock", which drops debt) |
| Accounting and legal trouble | Company | 8-K 4.01, 4.02, 3.01; SEC NT 10-K and NT 10-Q; Sharadar regulatory delistings | One subtype each |
| Distress and restructuring | Company | 8-K 1.03, 2.04, 2.05; Sharadar bankruptcy delistings | One subtype each |
| Activist stakes | Company | SEC Schedule 13D (both form names) | Tied to the target when exactly one of the filing's SEC numbers is a listed stock. Sharadar's code 35 is kept as a cross-check |

Each row has a role: **main** (the record the event method tests), **cross-check** (a second view of the same type) or **unmapped** (a rule with no industry).

## 2. Returns around each event

Day 0 is the first trading day on or after the event date. Windows: days -20 to -1, day -1, day 0, days 0 and 1, and days 2 to 21 (drift).

- **Market-wide events:** every French group's return minus the market (Fama-French market return), for the 12 and 49 groups, plus the market's own return. French's daily data runs about two months behind, so the latest events wait for the next update (the check report counts them).
- **Industry events:** the affected groups' returns minus the market.
- **Company events:** the stock's return (Sharadar, adjusted for splits and dividends), its peers' return (equal-weighted average of its French group in Sharadar, daily moves capped at -50% and +100%, stocks under $1 left out) and the all-stock market, and the stock minus its peers. Filing dates carry no time, so days 0 and 1 is the main window: it covers filings after the 4 PM close.

## 3. No look-ahead

- Every event is dated when its record became public: the index day, the election day, the oil price day, the signing day of a presidential document (the White House releases it that day), the Federal Register publication day, the SEC filing day.
- Spike and big-move days are chosen against earlier days only. Off-cycle guidance, dividend cuts, stops and first dividends use only earlier filings, payments and prices.
- The truncation test reruns each of those rules on data cut a year back and checks the events before the cut are the same.
- **One known exception:** merger announcements are picked out by the deal filing that follows them (the earliest 8-K 1.01 in the 90 days before the target's tender offer, board response or proxy). The 8-K was public on its day, but choosing it uses a later filing. These rows are flagged `later_filing`, and buyers' announcements inherit the flag. The event method should treat them as a known selection limit.

## 4. Files

Committed to `data/events/pull/` (public sources only):

| File | What |
|---|---|
| `market_events.csv` | Every market-wide event: id, type, subtype, role, date, day 0, public from, source, record reference, detail |
| `regulatory_events.csv` | Every significant final rule, with its 12-group and 49-group mapping |
| `sector_moves_12.csv`, `sector_moves_49.csv` | Group minus market per event and window, in percent (market rows give the market's own return) |
| `company_event_summary.csv` | Company events by type and subtype: events, companies, dates, how many have returns, median moves beyond peers against ordinary days |
| `counts_by_year.csv` | Events per type, role and year, all levels |
| `checks.csv`, `EVENT_DATA_CHECK.md` | The checks and the report |

On the runner only (`raw/event_results/company_events.csv`): every company event with its stock, peer, market and stock-minus-peer returns. Sharadar's personal licence doesn't allow sharing its data and the repository is public, as with the company measures.

## 5. Checks

- **Counts against the source write-up:** index spikes, elections, oil moves, tariff days, every significant rule the Federal Register counts, Sharadar's code counts against the Nov 27 check, dividend breaks and deal and delisting counts, SEC form volumes per quarter, and at least 30 main events per company type.
- **Dates:** nothing after today, nothing public after day 0, day 0 never before the event date, events with no trading day near them counted.
- **No look-ahead:** the truncation tests above.
- **Spot checks:** Russia's invasion of Ukraine, the March 2020 oil crash (and energy's fall against the market that day), the 2016 election, the 2018 steel tariffs and the April 2025 tariffs.
- **Event days against ordinary days:** how much more groups and stocks move on event days than on any day, per type. A sanity check, not the test: that's the event method's job.
- **Gaps:** unmapped agencies, filings not tied to a stock, events waiting for French's data, SEC search months not fetched.

## 6. Limits

- **Filing times:** dates only, so the company window is two days.
- **Index revisions:** the risk indexes are rebuilt from newspaper counts and can shift slightly; the run uses the current vintage.
- **13D filers:** 13D also covers founders and parent companies; filtering by filer and purpose is the event method's call. Filings where both sides are listed are left out.
- **OPEC meeting dates** and **SEC enforcement actions** are not in v1 (`docs/event-sources.md`).
- **SEC search** covers 2001 on. Company types from Sharadar's 8-K table go back to 1994 (to Aug 2004 for items created then).
