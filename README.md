# Invest with AI

This repository holds the code for the Invest with AI framework, which helps assess whether a stock is investable across four pillars: macro, industry, company and events.

## Macro data pull

`.github/workflows/macro-data.yml` runs `scripts/fetch_macro_data.py` every Saturday, on demand from the Actions tab, and whenever the script or series list changes. It commits the results to `data/`.

- **FRED series:** listed in `config/fred_series.csv`, one file each in `data/fred/`. Needs the `FRED_API_KEY` repository secret. Monthly levels (CPI, PCE, retail sales) are the current revised values; original release versions (ALFRED) are not pulled yet.
- **Sector returns:** Kenneth French's 12 industry portfolios, daily and monthly, value- and equal-weighted, and his 49 industry portfolios, daily, value- and equal-weighted, from 1990 on, in `data/french/` (percent returns).
- **Market return:** Fama-French factors in `data/french/ff_factors_*.csv`. Market return = `mkt_rf + rf`.
- **Check report:** `data/CHECK_REPORT.md` lists each dataset's date range, missing values, long gaps and whether it is stale.

To add a FRED series, add a row to `config/fred_series.csv`.

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
