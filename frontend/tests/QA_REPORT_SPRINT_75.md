# Frontend QA Report — Sprint 75

**Sprint:** 75 — Stat Calculation, Nickname System, Move Categories
**Date:** 2026-04-15
**Reviewer:** QA
**Verdict:** PASS

---

## QA-B1: Stat Calculation

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | HP formula defined | PASS | (2*Base+IV+EV/4)*Level/100+Level+10 |
| 2 | Other stat formula | PASS | Includes nature multiplier |
| 3 | IV range 0-31 | PASS | 6 stats |
| 4 | EV limits | PASS | 252 per stat, 510 total |
| 5 | EV 4 per point | PASS | |
| 6 | Nature multipliers | PASS | 0.9/1.0/1.1, 25 natures |
| 7 | Level range 1-100 | PASS | |

**QA-B1 Verdict: PASS**

---

## QA-B2: Nickname System

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Max 10 characters | PASS | |
| 2 | Name Rater in Lavender | PASS | Free service |
| 3 | Cannot rename traded | PASS | |
| 4 | Prompt on capture | PASS | Can skip |
| 5 | QWERTY keyboard | PASS | 2 pages |
| 6 | Evolved keeps nickname | PASS | |
| 7 | Traded keeps name | PASS | |

**QA-B2 Verdict: PASS**

---

## QA-B3: Move Categories

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 3 categories | PASS | Physical, Special, Status |
| 2 | Physical uses Attack | PASS | vs Defense |
| 3 | Special uses Sp.Atk | PASS | vs Sp.Def |
| 4 | 4 recoil moves | PASS | Cross-referenced |
| 5 | 4 drain moves | PASS | All 50% |
| 6 | 6 two-turn moves | PASS | Fly, Dig, Solar Beam, etc. |
| 7 | 3 OHKO moves | PASS | Fail if lower level |
| 8 | 2 self-destruct moves | PASS | User faints |

**QA-B3 Verdict: PASS**

---

## QA-B4: Backend Data

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 93 items | PASS | Unchanged |
| 2 | 174 moves | PASS | Unchanged |
| 3 | 151 species | PASS | Unchanged |
| 4 | 3715 tests passing | PASS | +29 new Sprint 75 tests |

**QA-B4 Verdict: PASS**

---

## Summary

| Section | Verdict |
|---------|---------|
| QA-B1: Stat Calculation | PASS |
| QA-B2: Nickname System | PASS |
| QA-B3: Move Categories | PASS |
| QA-B4: Backend Data | PASS |

**All JS files pass syntax check. 3715 backend tests passing.**
**Stat formulas with IV/EV/Nature. Nickname system. 19 special move mechanics.**
**Overall Sprint 75 Verdict: PASS**
