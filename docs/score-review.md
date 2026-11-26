# Score review: v0 macro scorecard against the free tests

Reviewed on 2026-11-26. The revised scorecard is [`config/macro_scorecard_v0_1.csv`](../config/macro_scorecard_v0_1.csv): all 40 scores (10 company types × 4 factors) with their five channel scores, the v0 net, an evidence label, a confidence label and one line of evidence each.

## Headline

The free tests back v0's shape for rates, spending and the dollar, and change two scores. Retail stores turn out to be among the most rate-hurt groups, so the two mildest retail types move from 0 and −1 to −2. Inflation can't be checked at sector level with free data, so all ten inflation scores stay as judgment and are marked unverified.

With this review the macro pillar counts as checked at sector level for rates, spending and the dollar. Inflation, and anything at company level, still rests on judgment until company data (Sharadar) or consensus forecasts are in.

## The rule

- **Change a score** only where the evidence is solid: it passes the false-discovery check, or it holds in both the 12-sector and 49-group runs.
- **Keep a score the tests can't check**, mark it unverified, and cap its confidence at Medium.
- **Keep a score the tests don't support** when the evidence isn't solid, and lower its confidence instead.

## Score changes

| Company type | Factor | v0 → revised | Channels | Evidence |
|---|---|---|---|---|
| Discount retailer | Rates | 0 → −2 | Revenue +1 → −1 | Retail stores lag the market when the 2-year yield jumps on Fed days: −0.28 per +10 bp in the 49-group run, −0.21 for the broad retail sector, both pass the false-discovery check, and equal-weighted agrees (−0.22). v0's trade-down offset doesn't show up. |
| Grocery chain | Rates | −1 → −2 | Valuation 0 → −1 | Same retail result. v0 gave grocers no valuation hit while giving one to most other types. |

The tests can't split retail by store type, so which retail types v0 had too mild is judgment. Discount and grocery were the ones furthest from the group result. With the change, the four retail types average −2.75 instead of −2.0, closer to automakers (−4), which measure about as rate-hurt.

## Confidence changes, scores kept

| Company type | Factor | Score | Confidence v0 → revised | Why |
|---|---|---|---|---|
| Restaurant chain | Rates | −3 | Medium → Low | Restaurants and hotels (49) are no worse than the market (−0.07, range −0.24 to +0.10). Not solid enough to change the score. |
| Homebuilder | Rates | −5 | High → Medium | Construction (49) leans hurt (−0.25) in every period, but its range crosses zero and it includes contractors. |
| Automaker | Inflation | −2 | Medium → Low | Durables lean the other way on hot CPI prints (+0.13, range −0.03 to +0.32). |
| Homebuilder | Dollar | +1 | Low → Low, flagged | The "Other" group is hurt by a stronger dollar (−0.24 per +1%, High), but it also holds mining and services. The dollar test on detailed groups would settle it. |

Nine scores v0 rated High end up Medium: homebuilder rates (above), three inflation scores the tests can't check, and five where the test agrees only through a group that mixes in other businesses.

## Confirmed

- **Rates:** automakers (High), packaged foods no worse than the market (Medium, a no-difference result).
- **Spending:** automakers (High); homebuilders and airlines through the "Other" group (Medium, loose mapping); the three discretionary retail types fit the retail group (Medium).
- **Dollar:** packaged foods and luxury hurt by a strong dollar (High); discount, grocery and home improvement helped (Medium, group level); airlines hurt (Medium, loose mapping).

## Findings for businesses v0 doesn't cover

v0 has consumer types only, so these go to the industry pillar rather than into scores here:

- **Energy** beats the market when the 2-year yield jumps (+0.23, medium confidence) and is hit hardest by a stronger dollar (−0.76 per +1%, High).
- **Chemicals** are hurt by a stronger dollar (−0.51, High).
- **Healthcare and utilities** lag on strong spending days (High); utilities are also hurt by a stronger dollar.
- **Retail, rubber and plastics, and packaging** are the only three of 49 groups whose rate result passes the false-discovery check.

## Fix to the repo copy of v0

`config/v0_macro_scores.csv` lists the restaurant chain's inflation score as −6. The scorecard page's channels (revenue −1, costs −3, valuation −1) add to −5, and the page shows −5. The revised file uses −5. The test results compared against −6, which moves the retail group's v0 average from −1.4 to −1.6 and changes no verdict.

## Labels

- **Evidence:** confirmed (the mapped group's result matches), consistent (matches a group that mixes in other types), leans confirmed (right sign, range crosses zero), changed, not supported, contradicted but kept, unverified.
- **Confidence:** High when a test confirms it with a range that excludes zero and the group matches the type well; Medium for group-level agreement, a changed score, a no-difference result or an unverified score; Low when the test points the other way or doesn't support it.

## Limits

- **Sector level only.** French's groups mix businesses, so these checks test v0's ranking, not each company type. Company data would test types directly.
- **Relative to the market.** The tests show which groups do better or worse than the market, not whether they fall in absolute terms.
- **Free surprise measures.** The inflation and spending surprises are stand-ins for consensus forecasts, which weakens what they can show.
- **Inflation, spending and dollar ran on 12 sectors only.** A 49-group run of those tests would check the dollar flags and the retail split further.
