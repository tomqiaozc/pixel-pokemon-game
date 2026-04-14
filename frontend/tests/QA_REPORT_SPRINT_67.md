# Frontend QA Report — Sprint 67

**Sprint:** 67 — PC Item Storage, Vending Machine, Pickup Ability
**Date:** 2026-04-14
**Reviewer:** QA
**Verdict:** PASS

---

## QA-B1: PC Item Storage

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 50 unique items max | PASS | 999 per item |
| 2 | 3 operations | PASS | Deposit, withdraw, toss |
| 3 | Operations have fields | PASS | id, name |
| 4 | Cannot store key items | PASS | |
| 5 | Toss confirm required | PASS | |
| 6 | Initial Potion | PASS | 1 Potion at start |
| 7 | 7 dialogue entries | PASS | |

**QA-B1 Verdict: PASS**

---

## QA-B2: Vending Machine

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Celadon rooftop | PASS | |
| 2 | 3 drinks | PASS | Fresh Water, Soda Pop, Lemonade |
| 3 | Drinks have fields | PASS | item, price, heal_amount |
| 4 | Price progression | PASS | 200, 300, 350 |
| 5 | Heal progression | PASS | 50, 60, 80 |
| 6 | 3 guard trades | PASS | Drinks for TMs, one-time |
| 7 | Unlimited stock | PASS | |

**QA-B2 Verdict: PASS**

---

## QA-B3: Pickup Ability

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | After battle trigger | PASS | 10% chance |
| 2 | Requires no held item | PASS | |
| 3 | 19 item entries | PASS | Level-weighted table |
| 4 | Items have fields | PASS | item, level range, weight |
| 5 | Level ranges valid | PASS | min <= max |
| 6 | All weights positive | PASS | |
| 7 | Rare Candy high level | PASS | Level 31+ |
| 8 | Nugget all levels | PASS | 1-100 |

**QA-B3 Verdict: PASS**

---

## QA-B4: Backend Data

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | 93 items | PASS | Unchanged |
| 2 | 174 moves | PASS | Unchanged |
| 3 | 151 species | PASS | Unchanged |
| 4 | 3482 tests passing | PASS | +27 new Sprint 67 tests |

**QA-B4 Verdict: PASS**

---

## Summary

| Section | Verdict |
|---------|---------|
| QA-B1: PC Item Storage | PASS |
| QA-B2: Vending Machine | PASS |
| QA-B3: Pickup Ability | PASS |
| QA-B4: Backend Data | PASS |

**All JS files pass syntax check. 3482 backend tests passing.**
**PC storage (50 items). 3 vending drinks with guard trades. 19-item pickup table.**
**Overall Sprint 67 Verdict: PASS**
