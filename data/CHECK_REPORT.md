# Macro data check report

Run date: 2026-11-25

**11 datasets pulled. 0 stale or empty. 3 with gaps over 7 days to review.**

Missing counts the dates in the source file with no value (FRED lists market holidays this way). Gaps list stretches longer than a week between values in daily data, usually market closures.

| Dataset | Source | First | Latest | Rows | Missing | Gaps > 7 days | Status |
|---|---|---|---|---|---|---|---|
| DGS2 | FRED | 1976-06-01 | 2026-11-24 | 13171 | 554 | 0 | ok |
| T5YIE | FRED | 2003-01-02 | 2026-11-25 | 6235 | 256 | 0 | ok |
| T10YIE | FRED | 2003-01-02 | 2026-11-25 | 6235 | 256 | 0 | ok |
| DTWEXBGS | FRED | 2006-01-02 | 2026-11-20 | 5450 | 214 | 0 | ok |
| DTWEXB | FRED | 1995-01-04 | 2019-12-31 | 6520 | 192 | 0 | discontinued (expected) |
| industry12_daily_vw | Ken French | 1926-07-01 | 2026-09-30 | 26338 | 0 | 1 | ok |
| industry12_daily_ew | Ken French | 1926-07-01 | 2026-09-30 | 26338 | 0 | 1 | ok |
| industry12_monthly_vw | Ken French | 1926-07 | 2026-09 | 1203 | 0 | 0 | ok |
| industry12_monthly_ew | Ken French | 1926-07 | 2026-09 | 1203 | 0 | 0 | ok |
| ff_factors_daily | Ken French | 1926-07-01 | 2026-09-30 | 26338 | 0 | 1 | ok |
| ff_factors_monthly | Ken French | 1926-07 | 2026-09 | 1203 | 0 | 0 | ok |

## Gaps to review

- **industry12_daily_vw:** 1933-03-03 to 1933-03-15
- **industry12_daily_ew:** 1933-03-03 to 1933-03-15
- **ff_factors_daily:** 1933-03-03 to 1933-03-15
