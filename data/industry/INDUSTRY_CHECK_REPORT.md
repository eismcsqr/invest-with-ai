# Industry data check report

Run date: 2026-11-27

**1 datasets pulled. 0 failed, stale or empty. 5 skipped for a missing key.**

Series counts columns (industries, categories or indexes). Missing counts blank cells inside a series's own history. Stale means the newest value is older than expected (75 days for monthly data, 200 for quarterly).

| Dataset | Source | Series | First | Latest | Periods | Missing | Status |
|---|---|---|---|---|---|---|---|
| gross_output | BEA |  |  |  |  |  | skipped |
| m3 | Census |  |  |  |  |  | skipped |
| concentration_2017 | Census |  |  |  |  |  | skipped |
| concentration_2022 | Census |  |  |  |  |  | skipped |
| ppi_industry | BLS |  |  |  |  |  | skipped |
| capacity_utilization | Fed G.17 via FRED | 56 | 1948-01 | 2026-10 | 946 | 0 | ok |

## Notes and checks

- **gross_output:** Skipped: BEA_API_KEY not set.
- **m3:** Skipped: CENSUS_API_KEY not set.
- **concentration_2017:** Skipped: CENSUS_API_KEY not set.
- **concentration_2022:** Skipped: CENSUS_API_KEY not set.
- **ppi_industry:** Skipped: BLS_API_KEY not set.
- **capacity_utilization:** Percent of capacity, seasonally adjusted. 5 values outside 0 to 110: CAPUTLG3361T3S 1950-06=111.3630, CAPUTLG3361T3S 1950-07=110.6527, CAPUTLG3361T3S 1950-08=113.4966, CAPUTLG3361T3S 1950-10=111.1052, CAPUTLN325211S 1973-02=110.3539. 1 series a period or more behind the latest (often normal right after a release): CAPUTLN325211S. 2 series with no value in the last 400 days (likely discontinued).

## Known gaps

- Services capacity: no free measure; G.17 covers manufacturing, mining and utilities only.
- Competition from company revenue shares needs Sharadar (paid, not bought).
- Regulation (QuantGov RegData, Federal Register) and technology (PatentsView) are not in this pull yet.
- Government data uses NAICS; matching it to French's 12 and 49 groups needs a crosswalk, not built yet.
