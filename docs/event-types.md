# Events pillar: event types

**Agreed November 27, 2026** (Kshitij took all three calls in section 6 as recommended). It follows the other pillars' pattern: boundary first, then the list, with data and a test for each.

## 1. Boundary

**An event is dated, one-off news that changes a stock's outlook beyond what the other pillars' regular readings already capture.** Most events are unscheduled, so the whole event is the surprise. For the few scheduled ones (elections, OPEC meetings), the surprise is the outcome against what was expected, read from the market's reaction, as in macro.

What stays where it is:

- **Scheduled macro news stays in macro:** Fed decisions and CPI, PCE and retail sales releases (the event calendar on main).
- **Scheduled results stay in company:** the results-day move beyond the industry is the earnings surprise factor.
- **Slow, recurring flows stay in company:** insider trades (owner signals) and the regular level of buybacks and dividends (capital use). Events only take the breaks: a dividend cut, suspension or first dividend, a new share offering.

**Events have no channels of their own.** Each one reaches the stock through a factor and channel the other pillars already have (a tariff through macro's costs channel, a new rule through industry's regulation factor, a CEO exit through company valuation). The event method (tracker task "Event method") maps each event onto those factors; this list only says which ones each type acts through.

Events come at three levels, each tested against a different baseline:

| Level | Hits | Measured as |
|---|---|---|
| Market-wide | Every stock, by how exposed its sector is | Sector return minus the market on event days (Kenneth French's 12 and 49 groups) |
| Industry | One group | The group's return minus the market |
| Company | One firm | The stock's return minus its French industry group, on the event day and the next (filings after 4 PM count to the next trading day), plus a 20-day drift check |

The macro guardrails carry over: about 30 events before a measured score counts, several time periods with sign-flip flags, ranges not exact numbers, event days compared with ordinary days.

## 2. Market-wide events

| Event type | What it is | Why it moves stocks | Acts through | Candidate free data | Test |
|---|---|---|---|---|---|
| **Geopolitical shocks** | Wars, attacks, sudden escalations | Raise oil and input costs, hit risk appetite, move the dollar | Macro: costs, valuation, currency | Caldara and Iacoviello geopolitical risk index (daily, from 1985) | Sector moves vs. the market on the index's spike days |
| **Trade and tariff actions** | New or removed tariffs, trade deals, export bans | Change input costs and overseas sales for exposed sectors | Macro: costs, revenue, currency | Trade policy uncertainty index (same authors); tariff notices in the Federal Register | Sector moves on spike days and on dated tariff announcements (2018 to 2019, 2025) |
| **Elections and policy shocks** | National election results, sudden policy turns | Shift the expected path of taxes, spending and regulation by sector | Macro: rates and valuation; industry: regulation | Election dates (fixed); economic policy uncertainty index (daily, on FRED as USEPUINDXD) | Sector moves on election days and policy-uncertainty spike days. Only about eight presidential elections since 1994, so elections alone stay low confidence |
| **Energy and commodity supply shocks** | OPEC decisions, pipeline or refinery outages, harvest failures | Move energy and input prices faster than demand can adjust | Macro: inflation, costs; industry: coping with shocks | OPEC meeting dates; daily oil price on FRED (DCOILWTICO); published oil supply news shock series | Sector moves on OPEC days, split by whether oil rose or fell |

## 3. Industry events

| Event type | What it is | Why it moves stocks | Acts through | Candidate free data | Test |
|---|---|---|---|---|---|
| **Major regulatory actions** | Final major rules, court rulings or enforcement waves that hit one industry | Change costs, allowed prices or who can compete | Industry: regulation, competitive position | Federal Register API (rules by agency, from 1994, no key); QuantGov RegData already chosen for the regulation factor | Affected group vs. the market on the days major rules from its agencies are published |

## 4. Company events

Each has an official SEC filing. Two routes to the dates:

- **Sharadar's 8-K events table** (in the weekly company data pull since Nov 27): 2.5 million rows from November 1993, one row per company, date and 8-K item code. Its corporate actions table adds dividends, listings, delistings and acquisitions. Confirm the code meanings on Sharadar's events page before mapping them; 8-K item numbers in their current form start in August 2004, so earlier rows use the older items.
- **SEC EDGAR, free:** the cross-check, the exact filing time (filings after 4 PM count to the next trading day), and the filings that aren't 8-Ks: tender offers, 13D stakes, offerings and late filing notices.

| Event type | What it is | Why it moves the stock | Acts through | Official record | Test |
|---|---|---|---|---|---|
| **Guidance changes** | Outlook raised or cut away from the results day (pre-announcements) | Resets expected earnings outside the scheduled surprise | Company: earnings surprise, growth | 8-K items 2.02 and 7.01 filed away from results dates | Move beyond the industry, split by raised vs. cut (direction read from the move, since text needs parsing) |
| **Mergers and acquisitions** | Agreed deals, tender offers, completed takeovers | Targets jump to the offer price; buyers often fall on overpaying or new debt | Company: valuation, balance sheet, growth | 8-K 1.01 and 2.01; tender offer filings (SC TO); merger proxies (DEFM14A) | Targets and buyers measured separately |
| **Leadership changes** | CEO or CFO leaves or is appointed | Signals trouble or a new strategy; abrupt exits hit hardest | Company: valuation, competitive position | 8-K item 5.02 | Planned vs. abrupt (effective at once) measured separately |
| **Capital structure breaks** | New share offerings; dividend cuts, suspensions or first dividends | Dilution or a signal about future cash | Company: capital use, financing, valuation | Offering filings (S-3, 424B); 8-K 8.01 and dividend history | Each break type measured on its own |
| **Accounting and legal trouble** | Restatements, auditor changes, late filings, delisting notices, SEC actions | Trust in the numbers drops, financing costs rise | Company: valuation, financing | 8-K 4.02, 4.01, 3.01; late filing notices (NT 10-K, NT 10-Q); SEC litigation releases | Move beyond the industry plus 20-day drift, where research finds the largest falls |
| **Distress and restructuring** | Bankruptcy, debt defaults, layoffs and plant closures | Equity can be wiped out; restructuring can also be read as a fix | Company: balance sheet, financing | 8-K 1.03, 2.04, 2.05 | Each item measured on its own |
| **Activist stakes** | An investor files to say it owns 5% or more and intends to push for change | Markets expect changes in strategy, payouts or a sale | Company: valuation, capital use | Schedule 13D filings | Move beyond the industry around the filing, plus drift |

## 5. Parked for later, and why

| Event type | Why it waits |
|---|---|
| **Analyst rating and target changes** | Paid data (Financial Modeling Prep), parked with analyst estimates on Nov 25 |
| **Index additions and removals** | No clean free history from the index providers; the effect has also shrunk since the 2000s |
| **Product approvals and recalls** | Free records (openFDA, NHTSA recalls) name products and sponsors, not tickers, so each needs matching to a company. Worth it for healthcare in v2 |
| **Crises and disasters** (pandemics, financial crises, natural disasters) | Too few to measure; shown as narrative with low confidence |
| **Labor strikes** | Free BLS list of large work stoppages exists, but events are few per industry |
| **News-only events and rumors** | No official record, so they'd be tagged opinion or narrative. They wait until the fact-tagging layer is built |

Insider trades and the regular level of buybacks and dividends aren't event types: they stay in company (section 1).

## 6. Decisions (Nov 27)

1. **Boundary:** events are one-off news at three levels (market, industry, company). Scheduled macro releases stay in macro; scheduled results and recurring flows stay in company. Not taken: events as company-only, which would leave geopolitics and tariffs to macro, which has no factor for them.
2. **v1 list:** the 12 types in sections 2 to 4: four market-wide, one industry, seven company. Each has a dated official record and enough history for about 30 events. The rest wait (section 5).
3. **Official records only in v1:** every v1 event comes from an official record (a filing, a government register, a published index), so each is tagged as fact with a source and date. News and rumors wait for the fact-tagging layer.

## 7. What can be tested when

- **Now, on data already in the repo:** the four market-wide types and regulatory actions run on Kenneth French's group returns, once the index and register files are pulled (a GitHub job reaches those sites; this workspace can't).
- **Company types, now:** the company data pull (merged Nov 27, pull request 14) brings Sharadar's daily prices from 1997, delisted companies included, and its 8-K events and corporate actions tables. That is enough to test the seven company types against each stock's French industry group; EDGAR adds the filings outside 8-Ks.

Sources named here were not opened from this workspace (it can't reach them); the event data task confirms each one.
