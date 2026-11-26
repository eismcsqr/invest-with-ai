# Company pillar: factors

**Agreed November 26, 2026** (Kshitij locked it in with all the picks in section 8). Drafted November 25 and revised the same night. It follows the industry pillar's pattern: boundary, factors, channels, data, scoring.

## 1. Boundary

**Company is whatever still moves a stock once the market, macro and its industry are taken out:** the company's own results, financial choices and how they compare with what was expected.

- Shared drivers stay upstream as the shock. Rates, oil and the sector's demand cycle belong to macro and industry. Company scores how this firm's **exposure** to those shocks differs from its sector's (more debt, more overseas sales, a different cost mix). This is the "fundamental exposure" layer the macro spec held back for the company pillar.
- One-off news (a CEO exit, a merger, a lawsuit, a product recall) goes to the events pillar. Company covers the ongoing state of the business and its scheduled results.
- Peers are the company's Kenneth French industry group (Sharadar's Fama industry field maps each ticker to it). Agreed: French's detailed groups (about 49) for company comparisons, the 12 broad groups for the industry pillar (section 8).

## 2. Factors

Six factors, plus one exposure layer that adjusts the other pillars.

| Factor | What it captures | Channels it reaches the stock through |
|---|---|---|
| **Growth** | Revenue and earnings growth against industry peers, and whether it is speeding up or slowing | Revenue, competitive position, valuation |
| **Profitability** | Margins and return on capital against peers, and how steady they are | Costs, competitive position, valuation |
| **Balance sheet** | Debt load, interest cover, cash, debt coming due | Financing, valuation |
| **Capital use** | Free cash flow and what is done with it: buybacks or dilution, dividends, reinvestment, share-based pay | Financing, valuation |
| **Earnings surprise** | How results land against what the market expected, read from the stock's move on results days beyond its industry's move. Analyst consensus is a later upgrade (section 5) | Valuation (re-rating), plus whatever the results reveal about revenue and costs |
| **Owner signals** | Insider buying and selling, and changes in institutional ownership | Valuation |

**Exposure profile (not a factor):** international revenue share, debt that reprices soon, cost mix. It does not move the stock by itself. It scales this company's macro and industry scores up or down from its sector's (for example, a homebuilder with twice the sector's short-term debt gets a bigger rates hit). Currency reaches company only through this layer.

Dropped from the starting ideas: **management** (no clean data; owner signals and capital use are the measurable part of it) and **product launches** (one-off news, so events).

## 3. Data: Sharadar and EDGAR fields

Field names below follow Sharadar's published fundamentals schema. I couldn't open Sharadar's own documentation from here (blocked from this workspace), so I confirmed the names on a third-party page that mirrors the schema. Confirm against Sharadar's docs when the subscription is set up. EDGAR names are standard US-GAAP tags, available through its free company facts API (no key; 10 requests a second; a contact in the request header).

**Point in time:** use the as-reported quarterly dimension (ARQ) and date each number by when it was filed, not by its period end. That is the "no peeking ahead" data check.

| Factor | Sharadar fields | EDGAR tags (cross-check) | Derived measures | Gaps |
|---|---|---|---|---|
| Growth | revenue, netinc, epsdil | Revenues or RevenueFromContractWithCustomerExcludingAssessedTax, NetIncomeLoss, EarningsPerShareDiluted | Year-on-year growth, change in growth, rank within industry | None |
| Profitability | grossmargin, gp, opinc, ebitda, invcap, roe | GrossProfit, OperatingIncomeLoss | Operating margin, return on invested capital (calculated ourselves), margin stability over 3 years | Sharadar's own ROIC isn't documented, so we calculate it |
| Balance sheet | debt, debtc, debtnc, cashneq, equity, ebit, intexp, workingcapital | LongTermDebt, InterestExpense, LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths | Net debt to EBITDA, interest cover, share of debt due within a year | Fixed vs floating debt is in note text, not reliably tagged |
| Capital use | ncfo, fcf, capex, depamor, ncfcommon, ncfdiv, dps, shareswa, sbcomp, marketcap | PaymentsForRepurchaseOfCommonStock, ShareBasedCompensation | Free cash flow yield, net buyback yield, share count change, capex vs depreciation, share-based pay as a share of revenue | None |
| Earnings surprise | Daily prices (Sharadar's price dataset, from 1998); results-day dates from Sharadar's 8-K events dataset (from 1993) | Filing dates from the submissions API (8-K "results of operations" filings and 10-Q/10-K) | Stock's return on results days, after its industry's return (French) | Analyst estimates aren't in Sharadar or EDGAR; parked as a later upgrade (section 5) |
| Owner signals | Sharadar insiders dataset (from 2005) and institutional dataset (from 2013) | Form 4 and 13F filings (raw, needs parsing) | Net insider buying over 6 months, change in institutional ownership | Field names unconfirmed; these datasets may cost extra beyond Fundamentals |
| Exposure profile | revenueusd vs revenue (only shows reporting currency, not where sales are) | Geographic and segment revenue are dimensional facts, which the simple APIs leave out; they need the full XBRL in each filing | International revenue share, short-term debt share, cost of revenue vs operating costs | Weakest part: international revenue needs filing-level parsing |

**Finance companies** (French's "Money" group: banks, insurers, brokers) don't fit these measures. Revenue, margins and debt mean different things for a bank. They get their own version: section 6.

Sources checked Nov 25: SEC EDGAR API documentation (sec.gov) and its webmaster FAQ; QuantRocket's Sharadar overview (dataset list and start years); a third-party page mirroring Sharadar's fundamentals field list.

## 4. Scoring: what carries over from industry

Carries over as is:
- **Mechanism:** −3 to +3 per factor per channel, same scale, six channels.
- **Measured check** over several periods with sign-flip flags.
- **Confidence:** high when mechanism and data agree over enough history.
- **Score = reading × exposure, shown as a range.**

What changes:
1. **Reading is mainly against peers, not own history.** Industry read each sector against its own past. A company is read first by where it ranks in its industry (top fifth = tailwind), with its own trend second.
2. **Exposure comes from the industry.** How much a factor matters (the "exposure") is measured per industry group, since leverage matters more for utilities than for software. The company's reading is then multiplied by its industry's exposure.
3. **Measured check uses the residual.** The stock's return after market, macro and industry are removed, tested against the factor readings across all companies at once.
4. **Dated by filing, with delisted companies kept**, so the check isn't flattered by look-ahead or by only seeing survivors.
5. **New output:** the exposure profile, which adjusts macro and industry scores per company.

## 5. Analyst estimates: a good-to-have for later

**Decided Nov 25 (Kshitij):** analyst estimates are a good-to-have, parked for later. No key test for now.

**Earnings surprise for v1:** the stock's return on results days after its industry's move (Kenneth French), using results dates from EDGAR and Sharadar. This follows the macro decision to use the market's reaction as the measure of surprise: free, never revised. Tradeoff: it measures surprise indirectly, and can't tell a beat that was already priced in from no news.

**The later upgrade:** expert surprise = (actual EPS − analyst consensus just before the report) ÷ share price, ranked within the industry, with the results-day move kept as a check. Revenue surprise after that; the cheap sources mostly give EPS only. Rating and price-target changes ("expert views") could become a seventh factor at the same time, if the source's history is deep enough.

**Sources checked Nov 25, for when we come back to it** (read on their own pages; both sites are blocked from this workspace, so nothing was tested yet):

| Source | What it gives | Cost | Limits found | Not stated on their pages |
|---|---|---|---|---|
| Alpha Vantage, earnings history | Quarterly and annual EPS with the analyst estimate and the surprise in dollars and percent (per a third-party guide; Alpha Vantage's own page for it didn't load in full) | Free key | 25 requests a day free, which is about 120 days for 3,000 companies; premium from $49.99/month removes the daily cap. Free key is for personal, non-commercial use | How far back, whether delisted companies are covered, where the estimates come from, whether the estimate is the final pre-report consensus |
| Financial Modeling Prep | Analyst estimates, earnings surprises (date, estimated and actual EPS), price target consensus, historical grades (upgrades and downgrades), historical ratings | Personal plans: Starter $19/month billed yearly ($29 monthly), Premium $49/month yearly ($69 monthly), Ultimate $99/month yearly ($139 monthly). Free plan is limited to about 87 large stocks | Starter: US only, 5 years of history, estimates annual only, too short for backtests. Premium: US, UK and Canada, 30+ years. Bulk earnings surprises only on Ultimate | Which plan carries the per-company earnings surprise endpoint (it's marked legacy), history depth for targets and grades, whether firm-level records are given, delisted coverage |
| Zacks via Intrinio | 20+ years of EPS surprises with counts of estimates above and below actual | Enterprise plan only, price by sales call; Intrinio's own example is $950/month plus $150/month per year of history | — | Revision history, coverage |
| I/B/E/S (LSEG) | The research standard: every estimate as it changed | Institutional, through WRDS (a university or corporate subscription) | Not open to individuals | — |

**Expert views as a separate signal (rating and target changes):** worth it later, not in v1. Research on analysts finds that changes in estimates and ratings move stocks more than the level of the consensus, but measuring that needs the history of how views shifted. The cheap sources mostly keep the last consensus, not its path, and FMP's history depth for grades and targets isn't stated. Add it as a seventh factor only if a test shows FMP's grade and target history goes back far enough and includes delisted companies.

**When we come back to it:** test before paying. Get free keys from Alpha Vantage and Financial Modeling Prep, save them as repository secrets, and run a 10-company test as a GitHub job (GitHub's runners reach both sites; this workspace can't). The test checks history depth, delisted names, and whether the estimates match each other. Then:
- If Alpha Vantage has 15+ years and delisted names: use it for expert surprise, free, and accept the slow first load (or one month of premium).
- If not: Financial Modeling Prep Premium (about $49/month billed yearly), which also opens the expert views signal.
- Zacks or I/B/E/S only if the product needs estimate revision history; not for research now.

## 6. Financials version: banks and insurers (added Nov 25)

**Decided Nov 25 (Kshitij):** include banks and insurers in v1, not later.

Same six factors and channels, same scoring. What changes is the measures inside four of them, because a bank's debt is mostly customer deposits (its raw material, not a risk sign), lending is the business itself, and an insurer earns from pricing risk and investing premiums.

| Factor | Banks | Insurers |
|---|---|---|
| Growth | Carries over, measured on loans, deposits and net interest income instead of revenue | Carries over, measured on premiums earned and book value per share |
| Profitability | Net interest margin, return on equity, efficiency ratio (costs ÷ revenue) | Combined ratio (claims plus expenses ÷ premiums; under 100% means underwriting makes money), return on equity, investment yield |
| Balance sheet → **Capital and credit** | Capital ratios (core tier 1, leverage), loan losses (net charge-offs and provisions ÷ loans), reserves against bad loans, loans ÷ deposits, share of deposits above the insured limit | Debt ÷ equity, reserve changes (whether past claims estimates were too low), riskiness of the investment portfolio |
| Capital use | Payouts (dividends plus buybacks) against capital headroom, not free cash flow | Payouts against book value growth, not free cash flow |
| Earnings surprise | Carries over unchanged | Carries over unchanged |
| Owner signals | Carries over unchanged | Carries over unchanged |
| Exposure profile | Rate sensitivity: how net interest income moves with rates (disclosed in filings as a table, mostly untagged) | Duration of the investment portfolio (in notes, mostly untagged) |

**Valuation baseline for financials:** price to tangible book value and price to earnings, not EV/EBITDA, which means little for a lender.

**Other financials** (asset managers, brokers, exchanges, payment companies) have ordinary accounts and use the standard version. REITs, which French also files under "Money", use the standard version for now; their usual cash measure (funds from operations) is a later refinement.

### Sources for financials

| Need | Source | Free? | Notes |
|---|---|---|---|
| Prices, payouts, share counts, book value, deposits | Sharadar (pb, equity, intangibles, ncfdiv, ncfcommon, deposits, investments) | Paid (already chosen) | Sharadar has no fields for loans, net interest income, loan losses, capital ratios, premiums or claims. Its "revenue" for a bank is net interest income after loan-loss provisions, which mixes two factors |
| Bank income, loan losses, capital ratios (holding company level) | EDGAR XBRL from 10-Q and 10-K: US-GAAP tags for net interest income, provision for loan losses, charge-offs, and regulatory capital ratios | Free, no key | Already keyed to tickers via EDGAR's company IDs. Tag coverage for capital ratios varies by bank; confirm on a sample of filings |
| Bank holding company regulatory data | Federal Reserve FR Y-9C, from the FFIEC's quarterly bulk download (caret-delimited text, history back to 1986 via the Chicago Fed archive and FFIEC) | Free; no registration mentioned | Most complete and consistent source for capital and loan quality. Keyed by the Fed's own ID (RSSD), not tickers, so it needs a crosswalk to tickers. The download page is a web form; whether a script can pull it needs a test |
| Bank-level detail (deposits, uninsured share) | FDIC BankFind API (call report data for insured banks) | Free, no key | Covers the bank subsidiaries, not the listed holding company; variable list and history depth weren't readable from its docs page |
| Insurer underwriting results | EDGAR XBRL: premiums earned, claims and benefits incurred, underwriting expenses | Free | Combined ratio calculated ourselves. Regulators' statutory filings (including insurers' capital adequacy) are sold by the NAIC, so insurer capital stays a gap |

**Reach:** none of these sites can be reached from this workspace (sec.gov, the FFIEC, the Fed and the FDIC were all refused on Nov 25). A GitHub job can reach them, as the FRED test did. None needs a key.

Sources read Nov 25: FFIEC financial data download page; Chicago Fed bank holding company data page; FDIC BankFind API documentation page; the third-party page that mirrors Sharadar's field list.

## 7. Industry-specific measures (added Nov 26)

**Asked Nov 26 (Kshitij):** use measures that fit each industry rather than one shared set stretched across all of them.

**How it works:** the six factors stay as the frame in every industry, so the pillar reads the same way everywhere. Inside each factor, an industry gets the measures that actually drive its stocks, added to or replacing the generic ones. Every measure is scored as a rank within the company's peers (top fifth = tailwind), so a retailer's same-store sales and a utility's rate base growth both become comparable readings even though the raw numbers aren't.

### Common core (every company, every industry)

These stay identical everywhere, so any two companies can be compared directly:

| Factor | Core measure | Source |
|---|---|---|
| Growth | Revenue growth (net revenue for banks) | Sharadar, EDGAR |
| Profitability | Return on equity | Sharadar |
| Capital use | Total payout (dividends plus buybacks) and change in share count | Sharadar |
| Earnings surprise | Results-day move beyond the industry's move | Prices plus EDGAR filing dates |
| Owner signals | Net insider buying, change in institutional ownership | Sharadar |
| Valuation baseline | Price to earnings against peers | Sharadar |

Balance sheet has no core measure, because leverage means opposite things for a bank and a software company.

### Measures by industry group (Kenneth French's 12)

Source key: **S** = Sharadar field, **X** = EDGAR structured data (XBRL tag, entity-wide, so in the free API), **O** = another free structured source, **T** = only in filing text or company reports (custom extraction, or a gap for now).

| Group | Factor it sits in | Industry-specific measures | Source |
|---|---|---|---|
| **Consumer nondurables** (food, drinks, household goods, apparel, tobacco) | Growth | Price vs. volume behind sales growth | T |
| | Profitability | Gross margin and its trend; advertising spend ÷ revenue | S; X |
| | Balance sheet | Inventory turns | S |
| **Consumer durables** (cars, appliances, furniture) | Growth | Units delivered; order backlog | T; X (remaining performance obligations, where reported) |
| | Profitability | Gross margin; warranty costs ÷ revenue | S; X |
| | Balance sheet | Inventory days; health of the in-house lending arm (car makers) | S; T |
| **Manufacturing** (machinery, aerospace, autos parts, metals) | Growth | Backlog growth; orders vs. shipments (book-to-bill) | X (remaining performance obligations); T |
| | Profitability | Incremental margin (extra profit per extra dollar of sales) | S |
| | Capital use | Capex ÷ depreciation | S |
| | Balance sheet | Pension shortfall | X |
| **Energy** (oil, gas, coal) | Growth | Production volumes | T |
| | Profitability | Cost per barrel produced; oil price needed to break even | T (custom) |
| | Balance sheet | Proved reserves and reserve life | X (reserve disclosures, coverage to confirm) |
| | Capital use | Reinvestment rate (capex ÷ operating cash flow) | S |
| | Exposure profile | Measured sensitivity to the oil price; share of output hedged | Prices plus FRED oil price; T |
| **Chemicals** | Profitability | Spread between selling prices and feedstock costs (gross margin against BLS producer prices) | S plus BLS |
| | Growth | Price vs. volume | T |
| | Balance sheet | Environmental cleanup liabilities | X |
| **Business equipment** (software, computers, chips, electronics) | Growth | Remaining performance obligations (contracted future revenue) growth; deferred revenue growth | X; S |
| | Growth | Recurring revenue share; net revenue retention from existing customers | T |
| | Profitability | R&D ÷ revenue; gross margin | S |
| | Capital use | Share-based pay ÷ revenue (dilution) | S |
| | Balance sheet | Inventory days and book-to-bill (chips, hardware) | S; T |
| | Exposure profile | Customer concentration (share of revenue from the biggest customers) | Filing-level XBRL (dimensional), or T |
| **Telecom** | Growth | Subscriber net additions; revenue per user | T |
| | Profitability | Customer churn; EBITDA margin | T; S |
| | Capital use | Capex ÷ revenue | S |
| | Balance sheet | Net debt ÷ EBITDA | S |
| **Utilities** | Growth | Rate base growth (the regulated asset base that earns a return) | O (FERC Form 1, electric utilities; XBRL since 2021, older years in legacy files) |
| | Profitability | Earned vs. allowed return on equity (the gap is regulatory lag) | O plus T (allowed return comes from state rate cases) |
| | Balance sheet | Net debt ÷ EBITDA; interest cover | S |
| | Capital use | Dividend payout ratio | S |
| **Shops** (retail, wholesale, some services) | Growth | Same-store sales; store count growth; online share of sales | T |
| | Profitability | Gross margin; sales per square foot | S; T |
| | Balance sheet | Inventory turns; lease obligations | S; X |
| **Healthcare** | Growth | Late-stage pipeline (drugs in phase 3 or filed) | O (ClinicalTrials.gov, free) |
| | Growth | Patent and exclusivity expiry on current drugs (patent cliff) | O (FDA Orange Book data files, free) |
| | Profitability | R&D ÷ revenue; medical cost ratio for health insurers | S; T |
| | Balance sheet | Cash runway for unprofitable biotechs (cash ÷ yearly burn) | S |
| | Exposure profile | Revenue share of the biggest drug | Filing-level XBRL (dimensional), or T |
| **Money** (banks, insurers) | All | As in section 6 | X, O, S |
| **Other** (transport, mining, construction, business services, media, hotels) | All | Core plus generic measures for now. Too mixed for one set; sub-industry measures (airline load factor and cost per seat-mile, mining cost per ton) come later by detailed group | T |

### Main data gaps

1. **Operating numbers that live only in text:** same-store sales, subscribers and churn, production volumes, price vs. volume, recurring revenue, units delivered. Companies report them in earnings releases and filings, but not as tagged data. Getting them means reading each filing (Claude can extract them, but every number needs checking against the source, across 20+ years of filings).
2. **Breakdowns of revenue** (by customer, product, region): tagged in the full filings but left out of EDGAR's free API, so they need filing-level parsing.
3. **Utilities' allowed returns** come from state rate cases, which have no single free database.
4. **Insurers' regulatory capital** (statutory filings) is sold by the NAIC.
5. EDGAR tag coverage for several measures (reserves, remaining performance obligations, warranty and environmental liabilities) needs confirming on sample filings.

New free sources this adds: FDA Orange Book data files, ClinicalTrials.gov, FERC Form 1. All reachable from a GitHub job, none from this workspace (to confirm with the data pull).

## 8. Decisions (agreed Nov 26)

1. **Valuation: baseline or factor?** Agreed: baseline. Treat valuation (P/E, EV/EBITDA against peers; price to tangible book for financials) as "what's already priced in" that the other factors are read against, not a seventh factor. It matches "markets react to surprises, not levels" and avoids counting valuation twice, since it's already a channel. The alternative adds a value factor, which is well studied but slow-moving and drifts.
2. **Peers for company comparisons: detailed groups everywhere.** Agreed: compare each company with its French detailed group (about 49, e.g. banks, insurance, software, semiconductors, retail), while the industry pillar keeps the 12 broad groups. Industry-specific measures only make sense against like companies. The alternative keeps the 12 broad groups, which would rank a chipmaker's inventory against a software company's.
3. **Text-only measures: v1 or later?** Agreed: build v1 on structured data only (Sharadar, EDGAR tags, FERC, FDA, ClinicalTrials.gov), and add text extraction as a second phase, starting with the three most valuable: same-store sales, subscribers and churn, and production volumes. The alternative extracts them now, which gives fuller industry coverage but means checking thousands of extracted numbers before the first run.
4. **Bank data: EDGAR first or the Fed's FR Y-9C first?** Agreed: EDGAR first, Y-9C as a cross-check. EDGAR is free and already tied to tickers. Y-9C is more complete and consistent but needs a holding-company-to-ticker crosswalk built first.

Also agreed: earnings surprise read from the results-day move beyond the industry, with analyst consensus as a later upgrade (section 5); one-off company news in events; banks and insurers included in v1 (section 6).
