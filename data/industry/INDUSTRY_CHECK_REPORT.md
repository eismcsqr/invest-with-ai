# Industry data check report

Run date: 2026-11-27

**9 datasets pulled. 0 failed, stale or empty. 0 skipped for a missing key.**

Series counts columns (industries, categories or indexes). Missing counts blank cells inside a series's own history. Stale means the newest value is older than expected (75 days for monthly data, 200 for quarterly).

| Dataset | Source | Series | First | Latest | Periods | Missing | Status |
|---|---|---|---|---|---|---|---|
| gross_output_nominal | BEA | 99 | 2005-01 | 2026-04 | 86 | 0 | ok |
| gross_output_price_index | BEA | 99 | 2005-01 | 2026-04 | 86 | 0 | ok |
| gross_output_quantity_index | BEA | 99 | 2005-01 | 2026-04 | 86 | 0 | ok |
| gross_output_real | BEA | 100 | 2005-01 | 2026-04 | 86 | 0 | ok |
| m3 | Census | 378 | 1992-01 | 2026-09 | 417 | 0 | ok |
| concentration_2017 | Census | 1935 | 2017 | 2017 | 9974 | 115 | ok |
| concentration_2022 | Census | 1866 | 2022 | 2022 | 9625 | 40 | ok |
| ppi_industry | BLS | 916 | 1985-01 | 2026-10 | 502 | 0 | ok |
| capacity_utilization | Fed G.17 via FRED | 58 | 1948-01 | 2026-10 | 946 | 0 | ok |

## Notes and checks

- **gross_output_nominal:** Table 15: Gross Output by Industry (A) (Q).
- **gross_output_price_index:** Table 18: Chain-Type Price Indexes for Gross Output by Industry (A) (Q).
- **gross_output_quantity_index:** Table 16: Chain-Type Quantity Indexes for Gross Output by Industry (A) (Q).
- **gross_output_real:** Table 208: Real Gross Output by Industry (A) (Q).
- **m3:** 87 M3 categories; millions of dollars. Category codes are Census M3 codes; mapping to NAICS and French groups comes next. 2 series with no value in the last 400 days (likely discontinued).
- **concentration_2017:** 1919 of 1935 NAICS industries give the largest firms' share of revenue; 1505 also have an HHI (Census publishes it for the 50 largest firms, mostly in manufacturing). Missing counts withheld shares.
- **concentration_2022:** 1865 of 1866 NAICS industries give the largest firms' share of revenue; 1461 also have an HHI (Census publishes it for the 50 largest firms, mostly in manufacturing). Missing counts withheld shares.
- **ppi_industry:** Series list from FRED's PPI listing. Not seasonally adjusted (BLS publishes industry indexes unadjusted). 250 ids FRED lists were not found at BLS: PCU211111211111, PCU211112211112, PCU212111212111, PCU212112212112, PCU212113212113. 3 series a period or more behind the latest (often normal right after a release): PCU332114332114, PCU332313332313, PCU332813332813. 9 series with no value in the last 400 days (likely discontinued).
- **capacity_utilization:** Percent of capacity, seasonally adjusted. 1 series a period or more behind the latest (often normal right after a release): CAPUTLN325211S. 2 series with no value in the last 400 days (likely discontinued).

## Known gaps

- Services capacity: no free measure; G.17 covers manufacturing, mining and utilities only.
- Competition from company revenue shares needs Sharadar (paid, not bought).
- Regulation (QuantGov RegData, Federal Register) and technology (PatentsView) are not in this pull yet.
- Government data uses NAICS; matching it to French's 12 and 49 groups needs a crosswalk, not built yet.
