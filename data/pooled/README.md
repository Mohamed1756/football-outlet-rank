# Pooled evidence (reproducible from loaders, no tracking data needed)

Two pickle files. Each entry is `(margin_s, incomplete)` with `incomplete`
in {0, 1}. Margins recompute exactly with the pinned code; labels come
from the source datasets.

- `skillcorner_frozen_live.pkl`: `(frozen, live)` tuple, 14,814 entries
  each. 20 A-League matches (SkillCorner Open Data, MIT), targeted
  receivers, 10 fps broadcast tracking. Frozen = 22 m/s Coulomb, static
  pressers. Live = same + gated-velocity presser advance. Built by
  `src/io/skillcorner.py::load_passes` + `arrival_margin`.
- `idsse_measured_live.pkl`: 673 entries. 7 Bundesliga 22/23 matches
  (IDSSE, Bassek et al. 2025, CC-BY 4.0). Measured reception points and
  release-to-reception times; `arrival_margin(measured=...)` with live
  pressers. Built by `src/io/idsse.py::load_passes`.

Raw tracking (90 MB/match) is not vendored; rerun the loaders against
the sources cited in README Sources to regenerate.
