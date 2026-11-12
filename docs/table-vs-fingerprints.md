# What the table doesn't care about

Rank predicts whether a pass arrives. It does not predict points.
Across 13 A-League teams (SkillCorner, n=13,122): points vs base
incompletion correlates −0.26; points vs median cushion −0.23.
Neither is worth naming.

The table tells you why, team by team:

- **Auckland won the league playing on the edge.** 53 points with the
  riskiest choices in the sample (0.42 s median cushion). Risk didn't
  cost them — it produced 49 goals.
- **Brisbane finished 12th playing the safest balls in the league**
  (0.83 s). Caution bought nothing: safe balls arrived and died
  (32 scored).
- **The bottom two chose "safe" and still finished there** (Brisbane
  0.83, Perth 0.80) — safe choices plus bad finishing is relegation
  form, not solidity. Wellington (11th, 0.62) chose mid-range and
  still went down with them: safety wasn't the differentiator.
- **City is the exception that proves the split matters:** 2nd place
  with safe choices *and* good finishing (0.110 base). Western United
  finished 3rd with the *worst* base rate (0.200) — and outscored
  their own sloppiness (55 goals, most in the top four).

The missing link is specific, not generic: it's not "possession" or
"xG" in the abstract — it's **receipt-to-shot**, what happens after
the ball arrives. Brisbane's safe balls arrive and die; Auckland's
risky balls arrive and become goals. This instrument stops at arrival
by design (`arrival.md`: the unplayed ball is unobserved; retention
covers only the first touch). Everything past receipt belongs to a
different instrument — one that starts where this one ends.
