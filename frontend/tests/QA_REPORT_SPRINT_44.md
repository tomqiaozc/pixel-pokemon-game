# Frontend QA Report — Sprint 44

**Sprint:** 44 — Move Priority, Berry Growth, Evolution Stone Locations
**Date:** 2026-04-14
**Reviewer:** QA
**Verdict:** PASS

---

## QA-B1: Move Priority

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 75 moves with priority | PASS | Dict keyed by move name |
| 2 | 8 priority brackets | PASS | -7 to +5 scale |
| 3 | Quick Attack priority 1 | PASS | Goes before normal moves |
| 4 | Normal moves at 0 | PASS | Tackle, Flamethrower, Surf, etc. |
| 5 | Negative priority (5+) | PASS | Whirlwind, Counter, etc. |
| 6 | Positive priority (3+) | PASS | Quick Attack, Extreme Speed, Protect |
| 7 | Speed tie rules | PASS | Random on ties |
| 8 | Gen 1 cross-reference | PASS | 60+ moves verified in moves.json |

**QA-B1 Verdict: PASS**

---

## QA-B2: Berry Growth

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 4 garden locations | PASS | Route 7, Route 11, Cerulean, Fuchsia |
| 2 | 22 total plots | PASS | Sum matches total_plots |
| 3 | 5 growth stages | PASS | Planted through Ready |
| 4 | 10 berries | PASS | Matches items.json berry count |
| 5 | Growth times positive | PASS | 3-12 hours |
| 6 | Stage duration consistent | PASS | growth_time / 5 |
| 7 | Watering mechanics | PASS | 3 max level, 50% dry penalty |
| 8 | 4 mulch types | PASS | growth, damp, stable, rich |
| 9 | Wilt after 24h | PASS | Ready berries wilt |
| 10 | Berry cross-reference | PASS | All match items.json |

**QA-B2 Verdict: PASS**

---

## QA-B3: Evolution Stone Locations

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 5 stones | PASS | Fire, Water, Thunder, Leaf, Moon |
| 2 | All have 2+ sources | PASS | Shop + field items |
| 3 | Valid source types | PASS | shop, field_item |
| 4 | Shop prices present | PASS | 2100 each at Celadon |
| 5 | Celadon sells 4 stones | PASS | Not Moon Stone |
| 6 | Moon Stone field-only | PASS | No shop source |
| 7 | Moon Stone in Mt. Moon | PASS | 2 locations |
| 8 | Hidden items (4+) | PASS | Across routes |

**QA-B3 Verdict: PASS**

---

## QA-B4: Backend Data

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 93 items | PASS | Unchanged |
| 2 | 174 moves | PASS | Unchanged |
| 3 | 151 species | PASS | Unchanged |
| 4 | 2740 tests passing | PASS | +38 new Sprint 44 tests |

**QA-B4 Verdict: PASS**

---

## Summary

| Section | Verdict |
|---------|---------|
| QA-B1: Move Priority | PASS |
| QA-B2: Berry Growth | PASS |
| QA-B3: Evolution Stone Locations | PASS |
| QA-B4: Backend Data | PASS |

**All JS files pass syntax check. 2740 backend tests passing.**
**75 move priorities. 10 berry growth profiles. 5 evolution stone location maps.**
**Overall Sprint 44 Verdict: PASS**
