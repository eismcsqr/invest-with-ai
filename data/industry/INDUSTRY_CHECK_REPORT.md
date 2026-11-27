# Industry data check report

Run date: 2026-11-27

**5 datasets pulled. 1 failed, stale or empty. 0 skipped for a missing key.**

Series counts columns (industries, categories or indexes). Missing counts blank cells inside a series's own history. Stale means the newest value is older than expected (75 days for monthly data, 200 for quarterly).

| Dataset | Source | Series | First | Latest | Periods | Missing | Status |
|---|---|---|---|---|---|---|---|
| gross_output | BEA |  |  |  |  |  | FAILED |
| m3 | Census | 378 | 1992-01 | 2026-09 | 417 | 0 | ok |
| concentration_2017 | Census | 1935 | 2017 | 2017 | 9974 | 0 | ok |
| concentration_2022 | Census | 1866 | 2022 | 2022 | 9625 | 0 | ok |
| ppi_industry | BLS | 916 | 1985-01 | 2026-10 | 502 | 0 | ok |
| capacity_utilization | Fed G.17 via FRED | 58 | 1948-01 | 2026-10 | 946 | 0 | ok |

## Notes and checks

- **gross_output:** Earlier file kept. BEA table list: BEA said: This UserId is not active. Please activate it and try again.
- **m3:** 87 M3 categories; millions of dollars. Category codes are Census M3 codes; mapping to NAICS and French groups comes next. 2 series with no value in the last 400 days (likely discontinued).
- **concentration_2017:** 1935 of 1935 NAICS industries have an HHI; the rest give only the largest firms' share of revenue (or are withheld).
- **concentration_2022:** 1866 of 1866 NAICS industries have an HHI; the rest give only the largest firms' share of revenue (or are withheld).
- **ppi_industry:** Series list from FRED's PPI listing. Not seasonally adjusted (BLS publishes industry indexes unadjusted). 250 ids FRED lists were not found at BLS: PCU211111211111, PCU211112211112, PCU212111212111, PCU212112212112, PCU212113212113. 3 series a period or more behind the latest (often normal right after a release): PCU332114332114, PCU332313332313, PCU332813332813. 9 series with no value in the last 400 days (likely discontinued).
- **capacity_utilization:** Percent of capacity, seasonally adjusted. 1 series a period or more behind the latest (often normal right after a release): CAPUTLN325211S. 2 series with no value in the last 400 days (likely discontinued).

## Known gaps

- Services capacity: no free measure; G.17 covers manufacturing, mining and utilities only.
- Competition from company revenue shares needs Sharadar (paid, not bought).
- Regulation (QuantGov RegData, Federal Register) and technology (PatentsView) are not in this pull yet.
- Government data uses NAICS; matching it to French's 12 and 49 groups needs a crosswalk, not built yet.
