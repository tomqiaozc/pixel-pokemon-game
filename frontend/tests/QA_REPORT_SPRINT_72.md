# Frontend QA Report — Sprint 72

**Sprint:** 72 — TM/HM List, Kanto Region, PP Table
**Date:** 2026-04-15
**Reviewer:** QA
**Verdict:** PASS

---

## QA-B1: TM/HM List

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 50 TMs | PASS | TM01-TM50 |
| 2 | 5 HMs | PASS | Cut, Fly, Surf, Strength, Flash |
| 3 | TMs have fields | PASS | number, move, location, source |
| 4 | Sequential TM numbers | PASS | 1-50 |
| 5 | Sequential HM numbers | PASS | 1-5 |
| 6 | All moves in moves.json | PASS | Cross-referenced |
| 7 | HMs not deletable | PASS | |
| 8 | TMs single-use | PASS | Consumed on use |
| 9 | HMs infinite use | PASS | |
| 10 | Total fields match | PASS | |

**QA-B1 Verdict: PASS**

---

## QA-B2: Kanto Region

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 11 cities/towns | PASS | Pallet through Indigo Plateau |
| 2 | 25 routes | PASS | Route 1-25 |
| 3 | 13 dungeons | PASS | Forests, caves, buildings |
| 4 | Cities have fields | PASS | name, map_id, gym, pokecenter |
| 5 | 8 gym cities | PASS | |
| 6 | Routes have connections | PASS | 2 per route |
| 7 | Dungeons have floors | PASS | All >= 1 |
| 8 | Pallet Town no gym | PASS | |
| 9 | Region name Kanto | PASS | |
| 10 | Total fields match | PASS | |

**QA-B2 Verdict: PASS**

---

## QA-B3: PP Table

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 8 PP tiers | PASS | 5 through 40 |
| 2 | PP Up config | PASS | 3 max, 20% each, 60% total |
| 3 | 5 restore items | PASS | Ether through Leppa Berry |
| 4 | Struggle move | PASS | 50 power, 25% recoil, null PP |
| 5 | Struggle at zero PP | PASS | |
| 6 | Pokecenter restores PP | PASS | |
| 7 | Max PP calculation | PASS | base * 1.6 |
| 8 | Total tiers match | PASS | |

**QA-B3 Verdict: PASS**

---

## QA-B4: Backend Data

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 93 items | PASS | Unchanged |
| 2 | 174 moves | PASS | Unchanged |
| 3 | 151 species | PASS | Unchanged |
| 4 | 3627 tests passing | PASS | +32 new Sprint 72 tests |

**QA-B4 Verdict: PASS**

---

## Summary

| Section | Verdict |
|---------|---------|
| QA-B1: TM/HM List | PASS |
| QA-B2: Kanto Region | PASS |
| QA-B3: PP Table | PASS |
| QA-B4: Backend Data | PASS |

**All JS files pass syntax check. 3627 backend tests passing.**
**50 TMs + 5 HMs. 11 cities, 25 routes, 13 dungeons. 8 PP tiers.**
**Overall Sprint 72 Verdict: PASS**
