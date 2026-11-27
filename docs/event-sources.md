# Events pillar: a source for each event type

**Draft, November 27, 2026** (tracker task "Event sources"). For each of the 12 event types agreed on Nov 27 (`docs/event-types.md`), this names the source, how much history it has, what it costs and what's still missing. Every source here was opened and checked by `scripts/check_event_sources.py`, run on GitHub on Nov 27; the full results are in `data/events/sources/` (summary: `EVENT_SOURCES_CHECK.md`).

All 12 types have a working source that is free or already paid for (Sharadar). One type, energy supply shocks, is missing its best record (OPEC meeting dates) and has a fallback; that's the one call in section 4.

## 1. The table

"Events" is how many dated events the source gives, the number the test needs at least 30 of.

| Event type | Source | History | Events | Cost | Gaps |
|---|---|---|---|---|---|
| **Geopolitical shocks** | Caldara and Iacoviello geopolitical risk index, daily | 1985 to Nov 23, 2026; updated Mondays | 135 spike episodes (top 5% of days, 10 days apart); 15 in the top 1% | Free | 3 of 5 known events land in the top 5% of days (Iraq 2003, Ukraine 2022, Israel 2023 yes; 9/11 at the 87th percentile, Crimea at the 59th) |
| **Trade and tariff actions** | Federal Register API: presidential proclamations and US Trade Representative documents that mention tariffs | 1994 to now | 274 proclamations, 1,124 USTR documents | Free | "Mentions tariffs" is broad: the event data task keeps actual actions (new or removed tariffs, Section 232 and 301 decisions) and drops routine notices |
| | Trade policy uncertainty index, daily (same authors) | 2015 to Nov 23, 2026 | 17 spike episodes (top 5%) | Free | Daily only from 2015, and only 1 of 4 known tariff days lands in its top 5% (April 2025 does; the 2018 and 2019 announcements don't), so a cross-check, not the main record |
| **Elections and policy shocks** | US federal election days, fixed by law | 1994 to 2026 | 8 presidential, 9 midterm | Free | Elections alone stay low confidence (too few) |
| | Economic policy uncertainty index, daily (FRED `USEPUINDXD`) | 1985 to Nov 26, 2026 | 131 spike episodes (top 5%) | Free | Built from newspaper counts, so it is a published index rather than a decision record |
| **Energy and commodity supply shocks** | WTI oil price, daily (FRED `DCOILWTICO`) | 1986 to Nov 24, 2026 | Big one-day oil moves (to be set in the event method) | Free | Big moves mix supply news with demand news. OPEC meeting dates would separate them but aren't reachable yet (section 4) |
| **Major regulatory actions** | Federal Register API: final rules marked significant, by agency | 1995 to now | 9,521 rules, about 300 a year | Free | Agencies need mapping to industry groups (health and EPA rules are the most common). "Significant" is wider than "major"; the method can keep the largest |
| **Guidance changes** | Sharadar 8-K events: items 2.02 (results) and 7.01 (Reg FD) | 2.02 from Aug 2004 | 647,000 item filings | Already paid | Off-cycle ones are found by dropping filings near the 10-Q or 10-K date (from Sharadar fundamentals); raised vs. cut comes from the move, not the text |
| **Mergers and acquisitions** | Sharadar 8-K events: items 1.01 and 2.01; a code that matches tender offer filings | 1994 to now | 238,000 item filings | Already paid | Item 1.01 covers every material contract, not just deals; tender offers and merger proxies narrow it |
| | Sharadar corporate actions: completed takeovers, target side | 1998 to now | 8,270 | Already paid | Completion dates, not announcements; buyer is often private (no ticker) |
| | SEC EDGAR: tender offers (SC TO-T, SC 14D9) and merger proxies (DEFM14A, PREM14A) | 2001 to now | About 200 and 87 a quarter | Free | Announcement day is the 8-K before these; the event data task links them |
| **Leadership changes** | Sharadar 8-K events: item 5.02 | 1994 to now | 237,000 | Already paid | 5.02 also covers directors and pay, so it's too broad alone |
| | SEC EDGAR full-text search: 8-Ks naming the CEO or CFO with "resign" | 2001 to now | 4,574 CEO hits in 2015 alone; 83 of 100 sampled are item 5.02 | Free | Planned vs. abrupt still needs a read of the filing's wording |
| **Capital structure breaks** | Sharadar corporate actions: dividend history | 1998 to now | 3,137 cuts of 25% or more by steady payers, 994 stops | Already paid | First dividends need a rule too (not counted yet) |
| | SEC EDGAR: offering prospectuses (424B4, 424B5) and shelf filings (S-3) | 2001 to now | About 1,155 a quarter | Free | 424B5 covers debt as well as shares; the event data task keeps share offerings |
| **Accounting and legal trouble** | Sharadar 8-K events: items 4.01 (auditor change), 4.02 (restatement), 3.01 (delisting notice) | Aug 2004 to now | 40,800 | Already paid | |
| | SEC EDGAR: late filing notices (NT 10-K, NT 10-Q) | 2001 to now | About 824 a quarter | Free | |
| | Sharadar corporate actions: regulatory delistings | 1998 to now | 1,010 | Already paid | |
| **Distress and restructuring** | Sharadar 8-K events: items 1.03 (bankruptcy), 2.04 (default triggers), 2.05 (layoffs and closures) | 1994 to now | 12,500 | Already paid | Plus 3,337 bankruptcy delistings in corporate actions |
| **Activist stakes** | SEC EDGAR: Schedule 13D filings | 2001 to now | About 1,586 a quarter | Free | 13D also covers non-activist holders (founders, parent companies); the method filters by filer and stated purpose. The form was renamed "SCHEDULE 13D" in Dec 2024, so both names are needed |
| | Sharadar 8-K events: a code that matches 13D filings | 1993 to now | 155,900 | Already paid | Code meaning inferred, not confirmed (section 2) |

## 2. What the checks found

- **Sharadar's events table matches SEC.** For 8 large companies since 2015, 98% of the 8-K items SEC lists (687 of 704) are in Sharadar on the same filing date. Sharadar's code is the item number without its dot (5.02 is 52). Its dates are filing dates; SEC's filing index adds the exact acceptance time, which the after-4 PM rule needs, so the event data task takes the time from SEC.
- **Sharadar's events table holds more than 8-Ks.** Three codes aren't 8-K items. Going by what the same companies filed with SEC on those days, code 34 lines up with passive 5% stakes (13G), code 35 with activist stakes (13D) and code 37 with tender offers. That's inferred, not confirmed: Sharadar's own code list wasn't reachable from the check.
- **Old 8-K items are folded in.** 8-Ks before August 2004 used different item numbers; Sharadar maps the old ones onto the new codes (bankruptcy, acquisitions and leadership go back to 1994, with an old-style auditor code to 2004). Items that only exist since 2004 (2.02, 4.02, 1.01) start then.
- **13D targets can be tied to a stock.** In 503 of 511 sampled 13D filings, SEC's search lists both the filer's and the target company's SEC numbers, so the target can be matched to a ticker without opening the filing.
- **SEC's complete filing index needs a contact.** SEC's quarterly index files (every filing since 1993) refuse a client that doesn't give a name and email. SEC's full-text search and company pages work without one, and cover 2001 on, which is enough for v1. Adding a `SEC_USER_AGENT` secret later opens the index files (section 4).
- **OPEC's site and Kaenzig's data aren't reachable.** OPEC's website refused the check (HTTP 403). Kaenzig's dated list of OPEC announcements, the standard research record, sits on openICPSR behind a free sign-in.

## 3. What's left out

- **SEC enforcement actions** (part of accounting and legal trouble). SEC's litigation releases name companies in text, with no SEC number or ticker, so each would need matching by hand. Left out of v1; restatements, auditor changes, late filings and delisting notices cover the type.
- **Daily trade policy uncertainty before 2015.** The index's daily version starts in 2015; the Federal Register gives the dated tariff actions back to 1994 instead.

## 4. Calls to make

1. **Energy supply shocks: start with big oil price moves, add OPEC dates later.** Recommended. Use days with the largest one-day moves in the WTI price (free, from 1986) as v1 event days, tagged as price moves, not decisions. OPEC meeting dates would split supply news from demand news, but the two routes need you: create a free openICPSR account and download Kaenzig's file, or have the dates typed in from OPEC press releases you open yourself. The alternative waits on that before the energy type can run.
2. **SEC contact: not needed now.** Full-text search covers 2001 on. If the event study later wants 1994 to 2000 for filings outside 8-Ks, add a repository secret `SEC_USER_AGENT` holding a name and email, which SEC asks automated clients to give.

## 5. Re-running the check

`.github/workflows/event-sources.yml` runs the check on demand from the Actions tab, and whenever the script or workflow changes. It needs the `SHARADAR_API_KEY` and `FRED_API_KEY` secrets (both already set) and installs two Excel readers (`xlrd`, `openpyxl`) on the GitHub runner. Sharadar's raw tables stay on the runner; only counts are committed.
