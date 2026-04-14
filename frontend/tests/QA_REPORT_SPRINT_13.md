# Frontend QA Report — Sprint 13

**Sprint:** 13 — Vermilion City, S.S. Anne, Lt. Surge
**Date:** 2026-04-14
**Reviewer:** QA
**Verdict:** PASS

---

## QA-B1: Vermilion City

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | buildVermilionCity() in routes.js | PASS | 30x25 tiles, tree border, cross roads, 7 buildings |
| 2 | Pokemon Center interior | PASS | buildVermilionPokemonCenter() 8x8, counter, Nurse Joy NPC |
| 3 | Pokemart interior | PASS | buildVermilionPokemart() 8x8, shelves, counter, Clerk NPC |
| 4 | Pokemon Fan Club interior | PASS | buildVermilionFanClub() 8x8, table/chairs, Chairman NPC with Bike Voucher dialogue |
| 5 | Vermilion Gym interior | PASS | buildVermilionGymInterior() 10x12, electric floor pattern, Lt. Surge at top |
| 6 | Vermilion Dock interior | PASS | buildVermilionDock() 12x8, water sides, gate, ship entry door |
| 7 | Diglett's Cave entrance | PASS | buildDiglettsCaveEntrance() 6x6, rock walls, ladder |
| 8 | North exit to Route 6 | PASS | `{ edge: 'north', targetMap: 'route_6' }` |
| 9 | East exit to Route 11 | PASS | `{ edge: 'east', targetMap: 'route_11' }` |
| 10 | 3 NPCs placed | PASS | Sailor, Vermilion Fan, Fisherman with dialogues |
| 11 | 4 lamps for day/night | PASS | lamps at (6,12), (16,12), (24,12), (8,22) |

**QA-B1 Verdict: PASS**

---

## QA-B2: S.S. Anne

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | S.S. Anne Deck (20x10) | PASS | buildSSAnneDeck() with railings, water bottom, exits to cabins & captain |
| 2 | S.S. Anne Cabins (20x12) | PASS | buildSSAnneCabins() with 3 cabin rooms, beds, hallway, doors |
| 3 | S.S. Anne Kitchen (10x8) | PASS | buildSSAnneKitchen() with counters/stoves, table, Chef NPC |
| 4 | Captain's Room (8x6) | PASS | buildSSAnneCaptainsRoom() with desk, bed, Captain NPC |
| 5 | Room-to-room connections | PASS | Dock→Deck→Cabins→Kitchen, Deck→Captain's Room |
| 6 | Captain NPC with HM dialogue | PASS | 4-line dialogue ending with "take this HM01 Cut" |
| 7 | 5 S.S. Anne trainers | PASS | ssAnneTrainers: Gentleman, Lass, Youngster, 2 Sailors |
| 8 | 2 passenger NPCs | PASS | In cabins with flavour dialogue |
| 9 | API endpoints wired | PASS | getSSAnneState, boardSSAnne, defeatSSAnneRival, helpCaptain, receiveHM |

**QA-B2 Verdict: PASS**

---

## QA-B3: Lt. Surge Gym & Trash Can Puzzle

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Gym interior with electric theme | PASS | 10x12, alternating flower tiles as electric pattern |
| 2 | Lt. Surge sprite | PASS | drawLtSurge() — green camo, blonde hair, military boots |
| 3 | Sailor sprite | PASS | drawSailor() — white uniform, blue collar, sailor hat |
| 4 | Captain sprite | PASS | drawCaptain() — white cap, gold buttons, grey beard |
| 5 | Trash can sprite | PASS | drawTrashCan() — grey body, darker lid, handle |
| 6 | Trash puzzle API wired | PASS | getTrashPuzzleState, checkTrashCan, resetTrashPuzzle in api.js |
| 7 | Lt. Surge NPC in gym | PASS | Positioned at (5,1), facing down, battle dialogue |

**QA-B3 Verdict: PASS**

---

## QA-B4: Route 11

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | buildRoute11() in routes.js | PASS | 30x20, tree borders, horizontal dirt path |
| 2 | 3 tall grass patches | PASS | Left (4-10, 3-7), right (15-24, 13-17), right upper (18-24, 4-7) |
| 3 | 3 trainers placed | PASS | route11Trainers: Youngster Dave, Gambler Stan, Bug Catcher Rod |
| 4 | West exit to Vermilion City | PASS | `{ edge: 'west', targetMap: 'vermilion_city' }` |
| 5 | Lamps for day/night | PASS | 2 lamps at (10,10) and (20,10) |
| 6 | Rocks and trees for decoration | PASS | 3 rocks, 3 trees, 2 flowers scattered |

**QA-B4 Verdict: PASS**

---

## QA-B5: Route Connectivity

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Route 6 → Vermilion (south exit) | PASS | Updated from door to `{ edge: 'south', targetMap: 'vermilion_city' }` |
| 2 | Vermilion → Route 6 (north exit) | PASS | `{ edge: 'north', targetMap: 'route_6' }` |
| 3 | Vermilion → Route 11 (east exit) | PASS | `{ edge: 'east', targetMap: 'route_11' }` |
| 4 | Vermilion → Dock → S.S. Anne chain | PASS | Door to dock, dock door to ss_anne_deck |

**QA-B5 Verdict: PASS**

---

## Summary

| Section | Verdict |
|---------|---------|
| QA-B1: Vermilion City | PASS |
| QA-B2: S.S. Anne | PASS |
| QA-B3: Lt. Surge Gym | PASS |
| QA-B4: Route 11 | PASS |
| QA-B5: Route Connectivity | PASS |

**All JS files pass syntax check (node --check).**
**Backend: 1600 tests passing.**
**Overall Sprint 13 Verdict: PASS**
