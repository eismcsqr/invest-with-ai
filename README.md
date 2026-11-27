# Invest with AI

This repository holds the code for the Invest with AI framework, which helps assess whether a stock is investable across four pillars: macro, industry, company and events.

## Macro data pull

`.github/workflows/macro-data.yml` runs `scripts/fetch_macro_data.py` every Saturday, on demand from the Actions tab, and whenever the script or series list changes. It commits the results to `data/`.

- **FRED series:** listed in `config/fred_series.csv`, one file each in `data/fred/`. Needs the `FRED_API_KEY` repository secret. Monthly levels (CPI, PCE, retail sales) are the current revised values; original release versions (ALFRED) are not pulled yet.
- **Sector returns:** Kenneth French's 12 industry portfolios, daily and monthly, value- and equal-weighted, and his 49 industry portfolios, daily, value- and equal-weighted, from 1990 on, in `data/french/` (percent returns).
- **Market return:** Fama-French factors in `data/french/ff_factors_*.csv`. Market return = `mkt_rf + rf`.
- **Check report:** `data/CHECK_REPORT.md` lists each dataset's date range, missing values, long gaps and whether it is stale.

To add a FRED series, add a row to `config/fred_series.csv`.

## Industry data pull

`.github/workflows/industry-data.yml` runs `scripts/fetch_industry_data.py` every Saturday an hour after the macro pull, on demand from the Actions tab, and whenever the script or workflow changes. It commits the results to `data/industry/`. These are the free sources agreed for the industry pillar on Nov 25.

Each source has its own repository secret. A source whose secret is missing is skipped with a warning and its earlier files are kept, so keys can be added one at a time.

| Factor | Source | Secret | Files |
|---|---|---|---|
| Demand cycle | BEA gross output by industry, quarterly (current dollars, real, and price index; tables found by name in BEA's table list) | `BEA_API_KEY` | `bea/gross_output_*.csv`, `bea/industries.csv`, `bea/tables.csv` |
| Demand cycle (manufacturing) | Census M3: new orders, shipments and unfilled orders by M3 category, monthly, from 1992, seasonally adjusted and not | `CENSUS_API_KEY` | `census/m3.csv`, `census/m3_columns.csv` |
| Competition (cross-check) | Census Economic Census concentration of largest firms, 2017 and 2022: HHI and the largest firms' share of revenue by NAICS industry | `CENSUS_API_KEY` | `census/concentration_<year>.csv` |
| Coping with shocks | BLS producer price indexes by NAICS industry, monthly, from 1985, not seasonally adjusted | `BLS_API_KEY` (and `FRED_API_KEY` for the series list) | `bls/ppi_industry.csv`, `bls/ppi_series.csv` |
| Capacity cycle | Fed G.17 capacity utilization by industry, monthly, seasonally adjusted, from FRED | `FRED_API_KEY` | `fed_g17/capacity_utilization.csv`, `fed_g17/series.csv` |

- **Layout:** time series files are wide: one `date` column and one column per industry, category or index. Quarterly BEA rows are dated to the quarter's first month (`2026-01` is Q1 2026).
- **PPI series list:** BLS's own list files block automated downloads, so the job takes the list of industry-level indexes from FRED's copy of the PPI (ids like `PCU325325`) and pulls each one from BLS (`PCU325---325---`). The list is saved, so later runs can reuse it if FRED is down.
- **Check report:** `data/industry/INDUSTRY_CHECK_REPORT.md` lists each dataset's series count, date range, missing values, stale or likely discontinued series, out-of-range values (capacity use outside 0 to 125, HHI outside 0 to 10,000) and which sources were skipped.
- **Not covered yet:** services capacity (no free measure), Sharadar revenue shares (paid), QuantGov RegData and the Federal Register (regulation) and PatentsView (technology). The NAICS-to-French-group crosswalk is in `config/industry_crosswalk.csv` (see Industry run).
- **Keyless check:** `python scripts/fetch_industry_data.py --smoke` reads three PPI indexes from BLS's keyless API and writes nothing.

## Company data pull

`.github/workflows/company-data.yml` runs `scripts/fetch_company_data.py` every Saturday an hour after the industry pull, on demand from the Actions tab, and whenever the script or workflow changes. It needs the `SHARADAR_API_KEY` repository secret (Sharadar personal bundle, bought Nov 27). It uses Sharadar's direct API (`api.sharadar.com/v1.0`), not Nasdaq Data Link.

- **Tables:** tickers, fundamentals, daily prices, 8-K events and corporate actions, each downloaded whole with the bulk route. Insider trades and institutional holdings come later, with the owner-signal measure.
- **What's committed:** only small files built from the tables, in `data/company/`: `fields.csv` (every column Sharadar sends), `field_check.csv` (the fields the company factors doc names), `coverage_by_group.csv` (companies per French industry group, delisted and domestic counts), `edgar_check.csv` (six companies' yearly revenue, net income and equity against their first SEC filing) and `COMPANY_CHECK_REPORT.md`. The raw tables stay on the runner: too big for the repository, and the personal licence doesn't allow redistributing them.
- **The six checks:** matches EDGAR within 1%, no number dated before its filing, splits handled, delisted names present, under 2% missing quarters (domestic common stocks), and the newest filing in the data within 5 days.
- **SEC contact:** SEC asks scripts to name a contact. If SEC refuses the generic one, add a `SEC_USER_AGENT` secret such as `Your Name you@example.com`; until then the EDGAR check is skipped with a note.

## Industry run

`scripts/industry_assessment.py` runs the industry pillar on French's 12 groups from the data already in the repo and writes `results/industry_run/` (write-up: `docs/industry-run.md`). Standard library only; about a minute.

- **Mapping:** `config/industry_crosswalk.csv` maps BEA industries, Fed capacity series, Census M3 categories and BLS producer price indexes to French's groups, following French's SIC definitions; BEA industries that span groups are split by rough output shares.
- **Exposure:** `config/industry_exposure_v0.csv`, a v0 judgment: each factor's channel scores (revenue, costs, financing, currency, valuation, competitive position) added up, capped at 3.
- **Readings:** demand (BEA real gross output), capacity (G.17, where it covers half the group) and coping with shocks (BEA output prices against all industries), each ranked against the group's last 20 years: top fifth = tailwind, bottom fifth = headwind. Competition, regulation and technology aren't scored yet.
- **Outputs:** `scores.csv` (score, range, confidence per group and factor), `readings.csv` (latest value, percentile, coverage), `checks.csv` and `pooled_checks.csv` (the measured check), `concentration.csv` (Census context), `measure_series.csv` (every measure's history).

## Event calendar

`scripts/build_event_calendar.py` runs right after the data pull in the same workflow and writes `data/events/`:

- **`fomc_decisions.csv`:** every Fed decision day since February 1994, when the FOMC began announcing its decisions. Scheduled meetings come from the Fed's FOMC calendars and historical pages; unscheduled actions are the conference calls, unscheduled meetings and notation votes that came with a target change (in the rates test) or a statement with no rate change (kept, but out of the rates test). The target before and after comes from FRED's `DFEDTAR` (to Dec 15, 2008) and `DFEDTARL`/`DFEDTARU` (since Dec 16, 2008).
- **`release_first_prints.csv`:** CPI, core CPI, PCE prices, core PCE prices, PCE spending and retail sales as first published, from ALFRED (FRED's archive of past data versions), with the prior month as known on release day, the first-print month-on-month change, and a data surprise.
- **`event_calendar.csv`:** one row per event day (Fed decisions plus CPI, personal income and outlays, and retail sales release dates from FRED's release calendar), with the market-reaction surprise and the scenario label.
- **`EVENTS_CHECK_REPORT.md`:** coverage, gaps, the cross-check against FRED's target rate, and spot checks against known decisions and prints.

### What each surprise measures

- **Market-reaction surprise (the macro spec's measure):** the change in the 2-year Treasury yield, in basis points, from the previous trading day's close to the event day's close, plus the same for 5- and 10-year breakeven inflation. Events on non-trading days (such as the Sunday, March 15, 2020 cut) count on the next trading day. Limits: daily closes include everything else that happened that day, Fed days include the morning before a 2 PM announcement, and `same_day_events` flags days with two events (such as CPI on a Fed day).
- **Scenario label (spec section 6):** yields up with stocks up is growth news; yields up with stocks down is tightening or inflation news; yields down with stocks down is weaker growth; yields down with stocks up is easing or cooling inflation. Moves under 1 basis point are "flat". It uses the Fama-French market return, which runs about two months behind.
- **Data surprise (a rough backup, not in the spec):** the first-print month-on-month change minus the average month-on-month change over the prior 12 months, both as known on release day. It has no analyst consensus behind it, so it counts predictable moves (like a known jump in gas prices) as surprises. Use it as a cross-check on the market measure, not instead of it.

## Rates test

`scripts/rates_test.py` measures how each of French's 12 sectors moves against the market when the 2-year yield moves on Fed decision days, and compares the result with the Macro Exposure Scorecard v0's rates scores. It runs from the data already in `data/` and writes `results/rates_test/`. Write-up: `docs/rates-test.md`. With `--groups 49` it runs on French's 49 detailed groups instead and writes `results/rates_test_49/` (write-up: `docs/rates-test-49.md`); `--groups all` runs both.

It uses the Fed decision days in `data/events/fomc_decisions.csv` (rows marked for the rates test), and falls back to the hand-entered list in `config/fomc_dates_provisional.csv` only if that file is missing.

## Score review

`config/macro_scorecard_v0_1.csv` is the v0 scorecard checked against the rates, inflation, spending and dollar tests: all 40 scores (10 company types × 4 factors) with their five channel scores, the v0 net, an evidence label, a confidence label and one line of evidence each. Write-up: `docs/score-review.md`. The original v0 scores stay in `config/v0_macro_scores.csv` and `config/v0_rates_scores.csv`, which the tests compare against.

`docs/company-method.md` is the company pillar's scoring method: how each of the six factors in `docs/company-factors.md` becomes a score against industry peers, the factor weights, the confidence rule and how company sits with macro and industry. Agreed Nov 26; not built yet (needs company data).

`docs/event-types.md` is the events pillar's list of event types: the boundary with the other pillars, the 12 types in v1 (four market-wide, one industry, seven company), what each acts through, its data and its test, and what is parked. Agreed Nov 27; not built yet.

## Event sources check

`.github/workflows/event-sources.yml` runs `scripts/check_event_sources.py` on demand and whenever the script or workflow changes. It opens the candidate source for each of the 12 event types (geopolitical risk and trade policy uncertainty indexes, FRED, the Federal Register API, Sharadar's events and corporate actions tables, SEC EDGAR) and commits counts and date ranges to `data/events/sources/` (summary: `EVENT_SOURCES_CHECK.md`). Write-up and the chosen source per type: `docs/event-sources.md`. Needs `SHARADAR_API_KEY` and `FRED_API_KEY`; `SEC_USER_AGENT` is optional and opens SEC's quarterly index files (from 1993).

## Event data pull

`.github/workflows/event-data.yml` runs `scripts/build_event_data.py` every Saturday at 10 AM Pacific (after the company pull), on demand from the Actions tab, and whenever the script, the agency map or the workflow changes. It pulls all 12 event types from their checked sources, writes one event table per level and lines each event up with returns around it. Write-up: `docs/event-data.md`.

- **Market-wide and industry events** (risk index spikes, tariff actions, elections, policy uncertainty spikes, big oil moves, significant final rules) are committed in `data/events/pull/` with each French group's move against the market (`sector_moves_12.csv`, `sector_moves_49.csv`). Rules are tied to industries through `config/regulation_agencies.csv`.
- **Company events** (guidance, mergers, leadership, capital structure, accounting, distress, activist stakes) come from Sharadar and SEC EDGAR. They and their stock-minus-peer returns stay on the runner (`raw/event_results/`, licence); only counts and medians are committed (`company_event_summary.csv`).
- **No look-ahead:** spike days, off-cycle guidance and dividend breaks use only earlier data, checked by rerunning on data cut a year back. Merger announcements are the one exception (flagged `later_filing`).
- **Secrets:** `SHARADAR_API_KEY`, `FRED_API_KEY`; `SEC_USER_AGENT` optional. SEC search results are cached between runs, so the first run takes longest.
- **Check report:** `data/events/pull/EVENT_DATA_CHECK.md`.
