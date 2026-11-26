# Invest with AI

This repository holds the code for the Invest with AI framework, which helps assess whether a stock is investable across four pillars: macro, industry, company and events.

## Macro data pull

`.github/workflows/macro-data.yml` runs `scripts/fetch_macro_data.py` every Saturday, on demand from the Actions tab, and whenever the script or series list changes. It commits the results to `data/`.

- **FRED series:** listed in `config/fred_series.csv`, one file each in `data/fred/`. Needs the `FRED_API_KEY` repository secret. Monthly levels (CPI, PCE, retail sales) are the current revised values; original release versions (ALFRED) are not pulled yet.
- **Sector returns:** Kenneth French's 12 industry portfolios, daily and monthly, value- and equal-weighted, in `data/french/` (percent returns).
- **Market return:** Fama-French factors in `data/french/ff_factors_*.csv`. Market return = `mkt_rf + rf`.
- **Check report:** `data/CHECK_REPORT.md` lists each dataset's date range, missing values, long gaps and whether it is stale.

To add a FRED series, add a row to `config/fred_series.csv`.

## Rates test

`scripts/rates_test.py` measures how each of French's 12 sectors moves against the market when the 2-year yield moves on Fed decision days, and compares the result with the Macro Exposure Scorecard v0's rates scores. It runs from the data already in `data/` and writes `results/rates_test/`. Write-up: `docs/rates-test.md`.

It uses `data/events/fomc_decisions.csv` once the event calendar is merged, and the provisional list in `config/fomc_dates_provisional.csv` until then.
