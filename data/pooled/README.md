# Pooled evidence: what the files are and what regenerates them

Two tiers. Tracking-derived pools (SkillCorner, IDSSE) regenerate from
the loaders in `src/io/` plus the repo test fixtures' hand slices —
raw tracking (90 MB/match) is not vendored. **360-derived pools do
not regenerate from this repo: no StatsBomb 360 loader exists here.**
They are frozen reference inputs from the calibration analysis, kept
auditable by the counts and edge values printed below. The scoring
rule that bins everything (WC2022 edges) is the literal
`DECILE_EDGES_S` in `src/models/pressing/calibration.py`.

| File | n | Backs |
|---|---|---|
| `frozen_five_leagues.pkl` | 173,440 dicts by league (margin, rank, complete) | fig1 five curves, ~100x gradient. **Frozen 360 input: no loader in repo.** Counts: wc2022 41,561; euro2020 33,761; laliga 28,694; euro2024 34,617; wwc2023 32,807 |
| `skillcorner_frozen_live.pkl` | 14,814 ×2 (margin, outcome) | fig1 sixth line, first (heuristic) cut. Superseded by the targeted pool below |
| `skillcorner_targeted_frozen_live.pkl` | 14,822 ×2, targeted receivers | **Canonical broadcast pool.** Pooled-decile d1 0.245 frozen / 0.221 live (same shape, noisier tight top); supersedes heuristic version |
| `skillcorner_team_margins.pkl` | 14,822 live-presser margins keyed (match, side) → 13 clubs after the match_teams.json join (fig3/table n=13,122 is the plotted labeled-pass subset — recount before reusing) | fig3 team fingerprints (join match.json for names) |
| `idsse_ball_flights.pkl` | 2,246 (t, dist) segments | Coulomb wins short-window fit (RMSE 0.035 m) |
| `idsse_reception_speeds.pkl` | 1,128 (dist, v0, t_true) | Drag rematch grid (Coulomb-22 wins) |
| `idsse_rematch_656.pkl` | ndarray (656, 3) of (dist, v0, t_true) — not a list of tuples like its siblings | Same grid, post-cleaning subset |
| `idsse_measured_all_1160.pkl` | 1,160 (margin, outcome) | Full measured pool (canonical; pooled-decile d1 0.40 → d10 0.01) |
| `idsse_measured_live.pkl` | 673 (margin, outcome) | First-3-matches cut cited in earlier drafts |
| `idsse_pooled7.pkl` | 631 (margin, outcome) | Same, alternate cut; kept for audit |
| `value_choice_by_passer.pkl` | 124 passers: name → [n, rank0_choices, value_choices, completions, total_outlets] (51 with n≥5 drive the null: rank-0 choice 0.00–0.25, completion 0.60–1.00, value/completion corr 0.02) | Value-added null |
| `league_table.json` | 13 clubs; only cited figures pinned (positions, 53 pts, 49/55/32 goals), rest null | table-vs-fingerprints points/goals |

Superseded cuts are marked, not deleted: early notes cite their numbers.

## Figure provenance

No script in this repo generates the figures: they are frozen binaries.
`fig1_decile_curves.png` plots the frozen-edge table `reproduce.py`
prints for the five 360 curves; its broadcast sixth line is the
superseded heuristic cut (`skillcorner_frozen_live.pkl`, n=14,814,
frozen-edge d1 1946/8642 = 0.225), kept as published — the canonical
targeted cut (n=14,822, d1 1948/8645 = 0.225) agrees to 1e-4 there,
so the plotted line stands. `fig3`, `fig5`, `fig6`, `fig7` are
hand-built SVGs/PNGs from the commits named in git history (`cef4edf`
started fig1 as a tracked SVG; `4b7aeef` rendered the PNG; `f843448`
added fig7). Uneditable without the source data + a plotting script:
to change a figure, rebuild it from the pool it cites and bank the
script in `scripts/` in the same task. Until then, captions describe
what is plotted, not what a rerun would plot.
## Binning rule, stated once

Headline gradient figures (arrival.md, fig1) use **pooled deciles**:
each pool is split into its own tenths, so d1 always holds that pool's
tightest 10%. Cross-pool comparison on common ground uses **frozen
WC2022 edges** (`DECILE_EDGES_S`): the same absolute margin, whatever
share of each pool falls in it. `scripts/reproduce.py` prints the
frozen-edge table (portable seconds); the headlines print the pooled
table (portable shape). Both binnings, both labeled — never one
presented as the other.
