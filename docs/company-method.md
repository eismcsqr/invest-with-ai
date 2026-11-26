# Company pillar: scoring method

**Agreed November 26, 2026** (Kshitij agreed the four picks in section 12). Builds on the agreed factors in `docs/company-factors.md` and follows the industry method (tracker, Industry method): mechanism on the −3 to +3 scale, a current reading, a measured check, a confidence rule, and score = reading × exposure, shown as a range.

## 1. The steps, start to finish

For each company, on each date, using only numbers filed by that date:

1. **Measure:** compute each measure the company's group uses (common core plus its industry-specific measures, from the factors doc).
2. **Rank against peers:** turn each measure into a percentile (0 to 100) within the company's detailed industry group.
3. **Factor percentile:** average the measure percentiles inside each factor.
4. **Reading:** turn the factor percentile into a reading from −1 to +1 (five bands).
5. **Factor score:** reading × the group's exposure to that factor (0 to 3), so each factor lands on −3 to +3.
6. **Company score:** the exposure-weighted average of the six readings, scaled to −3 to +3, with a range and a confidence label.

## 2. Ranking against peers

**Percentile ranks, not standardized scores.** Each measure is ranked within the peer group on that date. Direction is set per measure (higher revenue growth is better; higher debt to EBITDA is worse).

Why ranks:
- **Outliers don't matter.** A company with 400% growth after a tiny base ranks top, same as one with 40%. Standardized scores would let it swamp the factor.
- **Different units compare.** A retailer's inventory turns and a utility's interest cover both become "where it sits among its peers".
- **Matches "top fifth = tailwind"** in the industry method.

Cost: ranks drop magnitude (just ahead and far ahead look alike inside a band). The product shows the raw number and the peer median beside the reading, so magnitude stays visible.

**Level and trend.** Each measure is ranked twice: its level, and its change over the past year (also ranked within peers). The measure's percentile is two thirds level, one third change. This is the factors doc's "rank first, own trend second". Growth's own "speeding up or slowing" measure already is a trend, so it gets level only.

**Numbers that break a ratio:**
- Negative equity: return on equity is "not meaningful" (treated as missing); the balance sheet gets the bottom rank on leverage.
- Negative earnings: price to earnings is replaced by earnings yield (earnings ÷ price), which ranks cleanly through zero.
- Zero or negative denominators elsewhere: not meaningful, treated as missing.

## 3. Who counts as a peer

- **Peer group:** the company's French detailed group (about 49), as agreed.
- **Size floor:** the smallest fifth of all listed companies by market value on that date is left out of peer sets. Tiny companies have extreme ratios that would push everyone else's ranks around. They are still scored (ranked against the peer set), with low confidence.
- **Minimum peers:** a measure needs at least 10 peers with data on that date.
  - Core measures (revenue growth, return on equity, payout, earnings surprise, owner signals, price to earnings) fall back to the broad 12 group when the detailed group is too small.
  - Industry-specific measures pool the group's last three years of peer readings instead, since a broad group would mix unlike companies.
  - Either fallback caps that factor's confidence at Medium.
- **Financials** rank within their own detailed groups (banks, insurance), using the financials measures from the factors doc.

## 4. Turning a percentile into a reading

Five bands, on the same −1 to +1 reading the industry method uses:

| Peer percentile | Reading |
|---|---|
| Top fifth (80 to 100) | +1 (tailwind) |
| 60 to 80 | +0.5 |
| Middle fifth (40 to 60) | 0 (neutral) |
| 20 to 40 | −0.5 |
| Bottom fifth (0 to 20) | −1 (headwind) |

The industry method uses three bands (top fifth, middle, bottom fifth) because a sector against its own history moves slowly. Peer ranks spread companies out much more, and three bands would put 60% of companies at exactly zero. Five bands keep the industry's extremes and fill the middle.

## 5. Factor details

| Factor | How the reading is built |
|---|---|
| Growth | Average of growth measure percentiles (core: revenue growth; plus the group's own). Includes the change in growth rate as its own measure |
| Profitability | Core return on equity plus the group's margin and return measures; margin stability over 3 years counts as one measure |
| Balance sheet (Capital and credit for banks and insurers) | Group measures only (no core). Lower leverage and more cover rank higher |
| Capital use | Core: total payout and change in share count (fewer shares ranks higher); plus free cash flow yield and the group's own measures |
| Earnings surprise | The stock's return over the two days around its latest results (the results day and the day after, since many report after the close), minus its industry's return, divided by the stock's normal daily volatility. Ranked against peers' latest results-day moves over the past year. It holds until the next results day |
| Owner signals | Net open-market insider buying over 6 months as a share of shares outstanding, and the quarter's change in institutional ownership. Each ranked within peers, averaged |

**Valuation stays the baseline:** price to earnings (or earnings yield) against peers is shown next to the score as "how much is already priced in", and is not added to it.

## 6. Missing and stale data

- A measure with no filing in the last 200 days is treated as missing.
- A factor needs at least half its measures, and at least one, to get a reading. Otherwise its reading is "no data" (counted as 0) and the gap is shown.
- Missing data is never filled with an estimate. It only lowers confidence.

## 7. Exposure and factor weights

**Exposure** says how much each factor drives stocks in a group, from 0 to 3. As in the industry method, it is the mechanism: each factor's exposure is the sum of its channel scores (for example, balance sheet for utilities: financing 2, valuation 1, so 3), capped at 3. The channel split is kept so the product can say why.

**Default: equal weights (2 for every factor), adjusted only where a group's mechanism is clear:**

| Group | Raised to 3 | Lowered to 1 |
|---|---|---|
| Utilities | Balance sheet | Growth |
| Telecom | Balance sheet | |
| Money (banks, insurers) | Capital and credit | |
| Energy | Balance sheet, capital use | |
| Business equipment | Growth | Balance sheet |
| Healthcare | Growth | |
| Consumer nondurables | Profitability | |
| Shops | Profitability | |
| Others (durables, manufacturing, chemicals, other) | none | none |

Earnings surprise and owner signals stay at 2 everywhere.

**Later:** once Sharadar is in, the measured check (section 9) estimates each factor's real exposure per detailed group, and those numbers replace the defaults where the evidence is solid, using the same rule as the macro score review: change only when it passes the false-discovery check and holds across periods.

**Company score** = 3 × Σ(exposure × reading) ÷ Σ(exposure). So it stays on −3 to +3, and a factor with no data drops out of both sums.

## 8. Range and confidence

**Range:** the score recomputed with each factor at its weakest measure's reading (low end) and at its strongest measure's (high end). When a company's measures disagree, the range is wide. That is what the user sees, never a single exact number.

**Confidence**, per factor and for the company, from three checks, as in the macro rule (high with all three, medium with two, low otherwise):

1. **Data:** the factor has at least two thirds of its measures, fresh.
2. **Peers:** at least 20 peers in the detailed group, no fallback.
3. **Measured check:** the factor's reading has predicted this group's residual returns with the same sign across periods.

The company's confidence is the confidence of the factors carrying most of its exposure. Until company data is in, check 3 can't pass, so nothing goes above Medium (as in the macro score review).

## 9. Measured check

Same design as the industry method, with the residual from the factors doc: each month, the stock's return after the market, its macro exposures and its industry are taken out. Then, across all companies at once:

- Sort companies by each factor's reading and compare residual returns over the next quarter (top fifth vs bottom fifth), per detailed group where there are enough companies.
- Several periods (before 2008, 2008 to 2019, 2020 on) with sign-flip flags.
- Point in time: readings use only numbers filed by that date; delisted companies stay in.
- Out of sample: fit on earlier years, test on later.

## 10. How company sits with macro and industry

- **Layered, so nothing counts twice.** Macro is measured relative to the market, industry after macro, company after industry. Each pillar explains what the one before it left over, so the three scores can be shown side by side and added.
- **Same scale.** All three land on −3 to +3 with a range and a confidence label.
- **Exposure profile adjusts the other two.** A company's macro and industry channel scores are its sector's, multiplied by how its exposure compares with the sector's (for example, international revenue share ÷ the sector's average scales the currency channel; short-term debt share ÷ the sector's scales the financing channel). Multipliers are capped between 0.5 and 2 so one odd number can't flip a sign or blow up a score. Until filing-level data is parsed, the multiplier is 1.
- **How much each pillar counts** in one stock view is the Pillar combination task. This method only commits to the layering and the shared scale.

## 11. What can't be tested until company data is in

- Whether ranks beat standardized scores at predicting residual returns.
- The real factor exposures per group (the defaults are judgment).
- The two-thirds level, one-third trend split.
- The size floor and the 10-peer minimum.
- The earnings surprise window (two days) and whether to scale by volatility.
- Whether owner signals add anything (and whether Sharadar's insider and institutional datasets cost extra).
- The exposure profile multipliers.

## 12. Decisions (agreed Nov 26)

1. **Ranking:** percentile ranks within peers, not standardized scores. Ranks ignore outliers and compare unlike measures; magnitude stays visible through the raw number and peer median shown beside the reading.
2. **Reading bands:** five bands (section 4), not the industry method's three, which would put 60% of companies at zero.
3. **Factor weights:** equal (2 per factor), with the group adjustments in section 7, replaced by measured exposures once company data is in. The alternative, an evidence tilt now (profitability and earnings surprise heaviest), was not taken because it rests on published research rather than our data.
4. **Peers:** the smallest fifth of listed companies by market value is left out of peer sets, with a 10-peer minimum and the fallbacks in section 3.
