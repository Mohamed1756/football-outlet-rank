# Sources

Every dataset and paper this project leans on, in one place. Gate notes
(arrival.md, retention when built) cite claims; this file owns
provenance: where it came from, what licence, what we take from it, what
we don't. Football data is scarce and shifts — when a source is replaced
or a pool re-cut, update the row here, not the prose everywhere.

## Tracking & event data

| Source | Access | Licence | Gates using it | Take | Don't take |
|---|---|---|---|---|---|
| StatsBomb Open Data 360 (WC2022, Euro2020/2024, LaLiga 20/21, WWC2023) | github.com/statsbomb/open-data | Open | 3 (frozen calibration) | 173,440 frozen ground passes, full choice sets, outcomes | Velocities (none carried); seconds (standing starts inflate) |
| Metrica sample-data (Sample Game 1+2) | github.com/metrica-sports/sample-data | Open | 3 (mechanism tests), 4 (candidate) | 25 Hz velocities, ball track, measured peak speeds | Outcomes (two games, no labels); ends unnormalized across periods |
| SkillCorner Open Data (20 A-League 24/25 matches) | github.com/SkillCorner/opendata | MIT | 3 (broadcast replication), 4–5 (candidates) | 10 fps tracking, provider targeted receivers, possession outcomes | Precision (broadcast noise; trust gate catches spikes) |
| IDSSE (Bassek et al. 2025, 7 Bundesliga 22/23 matches) | Hugging Face `pysport/idsse-data` | CC-BY 4.0 | 3 (measured truth), 4–5 (candidates) | 25 fps TRACAB + ball, DFL events, measured receptions | Volume (1,160 measured; thin per player) |
| A-League 24/25 final table | aleagues.com.au (regular season) | Public facts, pinned | fingerprints | Cited positions/points/goals only — see `data/pooled/league_table.json` | Anything unbinned (nulls stay null until filled from source) |

Bassek et al. 2025: Scientific Data 12:195,
doi:10.1038/s41597-025-04505-y.

## Physics & biomechanics (concepts borrowed, values assumed)

Per-constant derivation notes live in
`src/physics/arrival_constants.py` — this table is the map, not the
derivation.

| Paper | Concept | Our assumption |
|---|---|---|
| Spearman et al. 2017 (Hudl SSAC, physics-based pass probabilities) | time-to-control (λ ~4.3/s); drag-model alternative (k = 0.0138) | 0.45 s first-touch latency + logistic; Coulomb won our rematch, not their k |
| Morin et al. 2016 + Samozino et al. 2021 (sprint F-v-P) | force-velocity profiling method | 3.5 m/s² burst, 8.5 m/s cap — team-sport values, not a measured cohort |
| FIFA Quality Programme for Football Turf, Test Manual I | ball-surface interaction regulated | Coulomb rolling friction, μ_roll ~ 0.25 |
| Lees & Nolan 1998 (Kicking Biomechanics in Soccer) | hip-pivot latencies | 0.15 s plant / 0.70 s full flip curve (`src/physics/biomechanics.py`) |

## Related work (independent convergence, not inputs)

- Carrasquilla et al. (Univ. del Rosario 2026, Int J Sports Sci
  Coaching): decision safety / OART over intended-target option sets on
  WC2022 360. Same question family, learned completion model vs our
  arrival cushion; low passer ICC (~0.03–0.04) corroborates the
  passer-trait null without confirming it.

## Adding a source (gate 4+ rule)

New dataset or paper → new row here with access, licence, gates, and the
take/don't-take split — in the same commit that first uses it. No
source cited in two places with two wordings; gate notes cite the claim,
this file cites the source.
