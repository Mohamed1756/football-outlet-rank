# Pooled evidence (reproducible from loaders, no tracking data needed)

Each file backs a numbered claim in `arrival.md`. Regenerate with the
named loader + function; raw tracking (90 MB/match) is not vendored.

| File | n | Backs |
|---|---|---|
| `frozen_five_leagues.pkl` | 173,440 (dict by league) | fig1 five curves, ~100x gradient |
| `skillcorner_frozen_live.pkl` | 14,814 ×2 (frozen, live) | fig1 sixth line; live≈frozen shape |
| `skillcorner_targeted_frozen_live.pkl` | 14,822 ×2, targeted receivers | Confirms sixth line (d1 0.244 both); supersedes heuristic version |
| `skillcorner_team_margins.pkl` | ~13,000, keyed (match, side) | fig3 team fingerprints (join match.json for names) |
| `idsse_ball_flights.pkl` | 2,246 (t, dist) segments | Coulomb wins short-window fit (RMSE 0.035 m) |
| `idsse_reception_speeds.pkl` | 1,128 (dist, v0, t_true) | Drag rematch grid (Coulomb-22 wins) |
| `idsse_rematch_656.pkl` | 656 × (dist, v0, t_true) | Same grid, post-cleaning subset |
| `idsse_measured_all_1160.pkl` | 1,160 (margin, outcome) | Full measured pool (canonical; d1 0.40 → d10 0.01) |
| `idsse_measured_live.pkl` | 673 (margin, outcome) | First-3-matches cut cited in earlier drafts |
| `idsse_pooled7.pkl` | 631 (margin, outcome) | Same, alternate cut; kept for audit |
| `value_choice_by_passer.pkl` | 124 passers | Value-added null (corr ≈ 0.01) |

Superseded cuts are marked, not deleted: early notes cite their numbers.
