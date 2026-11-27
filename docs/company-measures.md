# Company pillar: measures and peer ranks (v1 build)

**Built November 27, 2026.** This turns the Sharadar company data into the six factor measures in `docs/company-factors.md` and scores them as `docs/company-method.md` describes. Code: `scripts/company_measures.py`, run every Saturday right after the company data pull, in the same workflow. Checks: `data/company/measures/MEASURES_CHECK_REPORT.md`.

## What it does, start to finish

For the run date, using only filings dated on or before it and prices on or before it:

1. **Universe:** every common stock in Sharadar with a price in the week before the run date (secondary share classes, preferreds and warrants left out). Delisted companies stay in any run dated while they traded.
2. **Measures:** each company's measures, from the as-reported trailing twelve months (Sharadar's ART rows), dated by filing. A filing older than 200 days counts as missing.
3. **Peers:** the company's detailed French group (Sharadar's `famaindustry`). The smallest fifth of listed companies by market value is left out of peer sets; they are still ranked against their group, with low confidence.
4. **Percentiles:** each measure ranked within peers (ties share a rank). Measures with a trend are two thirds level, one third change over the past year, both ranked within peers.
5. **Fallback:** with fewer than 10 peers, core measures and the standard measures every group shares rank against the broad group (French's 12, from SIC codes); industry-specific measures have no reading.
6. **Factor reading:** the average of its measure percentiles, in five bands (+1, +0.5, 0, −0.5, −1). A factor needs at least half its measures.
7. **Company score:** 3 × Σ(exposure × reading) ÷ Σ(exposure), on −3 to +3, with a range (each factor at its weakest and strongest measure) and a confidence label. Factors with no data drop out of both sums.

## Measures by factor

**Core** measures apply to every company and fall back to the broad group. The rest apply to the standard version, or to the groups named.

| Factor | Measure | Better | Level and trend | Applies to |
|---|---|---|---|---|
| Growth | Revenue growth | higher | level | core |
| | Change in revenue growth (speeding up or slowing) | higher | level | all |
| | Earnings change ÷ market value a year ago | higher | level | standard |
| | Deferred revenue growth | higher | level | business equipment |
| | Deposit growth | higher | level | banks |
| | Tangible book per share growth | higher | level | banks, insurers |
| Profitability | Return on equity | higher | both | core |
| | Operating margin | higher | both | standard |
| | Return on invested capital (EBIT ÷ invested capital) | higher | both | standard |
| | Operating margin swings over 12 quarters | lower | level | standard |
| | Gross margin | higher | both | consumer nondurables, durables, business equipment, shops, chemicals |
| | Incremental margin | higher | level | manufacturing |
| | EBITDA margin | higher | both | telecom |
| | Return on assets | higher | both | banks |
| | Efficiency ratio (costs ÷ revenue) | lower | both | banks |
| Balance sheet (capital and credit for banks and insurers) | Net debt ÷ EBITDA | lower | both | standard |
| | Interest cover | higher | both | standard |
| | Share of debt due within a year | lower | level | standard |
| | Inventory turns | higher | both | consumer nondurables, durables, shops, business equipment |
| | Cash runway (years of cash burn) | higher | level | healthcare |
| | Tangible equity ÷ tangible assets | higher | both | banks, insurers |
| | Debt ÷ equity | lower | both | insurers |
| Capital use | Total payout yield (dividends plus buybacks ÷ market value) | higher | both | core |
| | Change in share count | lower | level | core |
| | Free cash flow yield | higher | both | standard |
| | Share-based pay ÷ revenue | lower | both | business equipment |
| Earnings surprise | Two-day move on the latest results day beyond the peer group's median move, ÷ normal daily volatility | higher | level | core |
| Owner signals | Net open-market insider buying over 6 months ÷ shares outstanding | higher | level | core |
| | Change in institutional ownership over the latest quarter ÷ shares outstanding | higher | level | core |

**Edge cases (method section 2):** negative equity makes return on equity missing and puts the company at the bottom on leverage; a company with no debt ranks top on interest cover and debt due soon; a company not burning cash ranks top on cash runway; a zero or negative denominator elsewhere is missing.

**Computed but not scored:** R&D ÷ revenue (business equipment, healthcare), capex ÷ depreciation (manufacturing), reinvestment rate (energy), capex ÷ revenue (telecom) and dividend payout ratio (utilities). The factors doc names them, but which way is better isn't settled: more R&D can be investment or waste, and a high payout ratio can be confidence or strain. They're kept in the per-company results; the measured check's proposed directions are in `docs/company-check.md`, waiting on a decision.

**Insider buying is ranked from zero out (changed Nov 27 after the first run).** Most companies have no open-market insider trades in six months, so their value is exactly zero. Ranked plainly, that tie sat around the 60th percentile and read +0.5, which made "nothing happened" look like a mild plus and tilted owner signals positive. Now zero reads 50 (neutral), net buyers rank among buyers from 50 to 100, and net sellers among sellers from 0 to 50.

**Owner signals need whole tables.** Insider trades and institutional holdings are pulled as whole tables (skipped with a note if a zip is over 6 GB). Insider buying is scored only when the insider table covers the full 6 months to the run date; institutional change only when there are two complete recent quarters (a quarter is complete when it holds at least half as many companies as the fullest quarter, and at least 1,000), counted 46 days after quarter end. Otherwise the measure is left out of that run and the check report says why.

**Valuation baseline** (shown, not scored): earnings yield, and price to tangible book for every company.

## How it differs from the method doc

- **48 groups, not 49.** Sharadar's `famaindustry` follows French's 48-group scheme (software sits inside business services).
- **Peer group's move for earnings surprise** comes from Sharadar prices (the median daily return of the group's peer set), not French's files, which run about two months behind.
- **Results days** are 8-K item 2.02 filings ("results of operations"); quarterly filing dates are the fallback for companies without one. A results day must be in the last 200 days; peers' moves from the past year count.
- **Standard measures fall back too.** The method names only core measures for the broad-group fallback; small groups (tobacco, coal, shipbuilding and a few others) would otherwise have no growth, profitability or balance sheet reading, so the standard measures every group shares fall back as well.
- **Industry-specific measures with fewer than 10 peers** get no reading for now. The method pools the group's last three years instead; that needs the historical runs that come with the measured check.
- **Share count change** is worked out from market value and split-adjusted price at each filing, so splits don't show as dilution.
- **Exposure profile** multipliers stay at 1 (filing-level data not parsed yet), as the method says.
- **Confidence:** check 3 (the measured check) comes from `data/company/check/factor_check.csv`, written by the monthly check (`docs/company-check.md`). A factor is High only when all three checks pass; the company takes the lowest confidence among the factors carrying most of its weight.

## Not built yet

- **EDGAR measures:** loan losses and capital ratios for banks, combined ratio for insurers, remaining performance obligations, pension shortfall, advertising, warranty and environmental liabilities. Banks' capital and credit factor rests on tangible equity alone until then.
- **Other free sources:** FERC Form 1 (utilities' rate base), FDA Orange Book and ClinicalTrials.gov (healthcare).
- **Text-only measures** (same-store sales, subscribers, production volumes): second phase, as agreed.

## Point in time

- Every fundamental comes from a row whose filing date is on or before the run date; every price from a trading day on or before it.
- The report counts any date after the run date among those used (should be 0).
- **Truncation test:** the whole calculation runs a year back twice, once with all data and once after deleting every row filed or priced after that date. Any company whose result differs fails the check.
- Companies that later left the market stay in the year-back run.

## What is committed

Only aggregate checks: the repository is public and the Sharadar personal licence doesn't allow redistributing its data. The full per-company file (every measure, percentile, reading, score, range and confidence) is written to `raw/company_results/` on the runner.

Run locally (with Sharadar tables in `raw/sharadar/`): `python scripts/company_measures.py [--asof YYYY-MM-DD]`.
