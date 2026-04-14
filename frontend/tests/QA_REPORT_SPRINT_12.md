# Frontend QA Report — Sprint 12

**Sprint:** 12 — Nugget Bridge, Bill's House, Team Rocket, Routes 5/6
**Date:** 2026-04-14
**Reviewer:** Frontend QA Agent (re-review)
**Verdict:** CONDITIONAL PASS

---

## QA-B1: Nugget Bridge

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | nuggetbridge.js exists with IIFE | PASS | `const NuggetBridge = (() => { ... })();` with loadState, getState, onTrainerDefeated, tryAwardNugget, isBridgeClear, renderBridgeProgress, renderNuggetReceived |
| 2 | 3 Nugget Bridge API endpoints wired | PASS | `getNuggetBridgeState` (api.js:779), `defeatBridgeTrainer` (api.js:784), `awardNugget` (api.js:792) — all exported |
| 3 | Proper error logging (no `.catch(() => {})`) | PASS | No empty catch patterns. api.js helpers use `console.error()` |
| 4 | Route 24 with water on both sides | PASS | `buildRoute24()`: 10x40, fills T.WATER first, 4-tile dirt bridge deck in center (x=3-6), rock railings at x=2 and x=7 |
| 5 | 6 trainers defined (5 bridge + Rocket Grunt) | PASS | `nuggetBridgeTrainers`: Bug Catcher Ethan, Lass Ali, Youngster Calvin, Lass Shannon, Hiker Josh, Rocket Grunt (with recruitment dialogue) |
| 6 | Nugget award rendering | PASS | `renderNuggetReceived()` draws gold overlay with "Got a Nugget!" |
| 7 | Cerulean City north exit to route_24 | PASS | `{ edge: 'north', targetMap: 'route_24', spawnX: 5, spawnY: 38, spawnDir: 1 }` |

**QA-B1 Verdict: PASS**

---

## QA-B2: Bill's Event

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | billevent.js exists with IIFE | PASS | `const BillEvent = (() => { ... })();` with state machine: pokemon -> transforming -> human -> ticket_given |
| 2 | 4 Bill event API endpoints wired | PASS | `getBillState` (api.js:801), `billTransform` (api.js:806), `billComplete` (api.js:811), `billTicket` (api.js:816) — all exported |
| 3 | Bill's House interior (8x8) | PASS | `buildBillsHouse()`: W=8, H=8, walls, door at bottom center, bookshelves (1,1-3), PC machine (1,5-6), table (4,2-3) |
| 4 | Route 25 (30x20) with Bill's House door | PASS | `buildRoute25()`: W=30, H=20. Bill's House at (25,3) via buildHouse. Door: `{ x: 27, y: 7, targetMap: 'bills_house', spawnX: 4, spawnY: 6 }` |
| 5 | Bill NPC dialogue for all states | PASS | `getBillDialogue()` covers: pokemon (help me!), transforming (wait!), human (thank you + ticket), ticket_given (thanks again), default (...) |
| 6 | S.S. Ticket rendering | PASS | `renderTicketReceived()` draws blue overlay (#60b0e8) with "Got an S.S. Ticket!" |

**QA-B2 Verdict: PASS**

---

## QA-B3: Routes 5/6 & Underground

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Route 5 (20x25) | PASS | `buildRoute5()`: W=20, H=25. Tree borders, central dirt path, tall grass patches, Underground entrance building at y=20-23 |
| 2 | Underground Path (4x30 stone corridor) | PASS | `buildUndergroundPath()`: W=4, H=30. T.DIRT floor, T.ROCK walls on sides, doors at top (y=0) and bottom (y=29) |
| 3 | Route 6 (20x25) with 2 trainers | PASS | `buildRoute6()`: W=20, H=25. `route6Trainers`: Bug Catcher Elijah (Butterfree L16), Youngster Dave (Rattata L15 + Spearow L15) |
| 4 | Map transitions: Cerulean -> Route 5 -> Underground -> Route 6 | PASS | Full chain: cerulean south -> route_5 (exit). route_5 door (10,23) -> underground_path (1,1). underground doors (1/2,0) -> route_5. underground doors (1/2,29) -> route_6 (10,2). route_6 door (10,3) -> underground_path (1,28) |
| 5 | Gate guard NPC or dialogue | **FAIL** | Gate guard sprite exists in sprites.js (`drawGateGuard`) but NO gate guard NPC is placed anywhere. Route 6 gate building door references `vermilion_gate` map which does NOT exist. See Bug #1 |
| 6 | Cerulean City south exit to route_5 | PASS | `{ edge: 'south', targetMap: 'route_5', spawnX: 10, spawnY: 1, spawnDir: 0 }` |

**QA-B3 Verdict: CONDITIONAL PASS** (Bug #1)

---

## QA-B4: Team Rocket & Cerulean Event

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Rocket Grunt sprite (black outfit, white R) | PASS | `drawRocketGrunt()`: Black outfit (#202020), white R on chest (#f0f0f0), black cap, gray pants (#404040) |
| 2 | Gate Guard sprite | PASS | `drawGateGuard()`: Blue uniform (#3050c0), gold badge (#d0a838), blue cap |
| 3 | Cerulean burgled house interior (8x8) | PASS | `buildCeruleanBurgledHouse()`: W=8, H=8, walls, door at (4,7), bookshelf, table |
| 4 | House owner NPC with robbery dialogue | PASS | NPC at (2,4): "Someone broke in and stole my TM!", "I think it was a Team Rocket member...", "They ran off toward Route 5!" |
| 5 | Burgled house door in Cerulean City | PASS | `{ x: 20, y: 19, targetMap: 'cerulean_burgled_house', spawnX: 4, spawnY: 6 }` |

**QA-B4 Verdict: PASS**

---

## Code Quality

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | No `.catch(() => {})` patterns | PASS | Confirmed via grep — zero matches in nuggetbridge.js, billevent.js, api.js |
| 2 | All API methods exported | PASS | 8 new methods in api.js return block: getNuggetBridgeState, defeatBridgeTrainer, awardNugget, getBillState, billTransform, billComplete, billTicket, giveItem |
| 3 | IIFE pattern consistent | PASS | Both nuggetbridge.js and billevent.js use `const X = (() => { ... })();` |
| 4 | Script tags in index.html | PASS | nuggetbridge.js (L54) and billevent.js (L55) included before api.js (L56) |

**Code Quality Verdict: PASS**

---

## Bugs Found

### Bug #1: Missing `vermilion_gate` map — Route 6 gate door leads to non-existent map
**Severity:** Medium
**Location:** routes.js:1114
**Description:** Route 6 has a door at `{ x: 10, y: 24, targetMap: 'vermilion_gate' }` but no `vermilion_gate` map is registered in `registerAll()`. Additionally, no gate guard NPC is placed in any map despite the `drawGateGuard()` sprite being defined.

**Impact:** If a player walks into the Route 6 gate building door, the MapLoader will attempt to load `vermilion_gate` which doesn't exist. This will likely cause a runtime error or blank screen.

**Recommendation:** Either:
- (a) Define a simple `vermilion_gate` interior map (e.g. 8x6 corridor) with a gate guard NPC using the existing sprite, OR
- (b) If Vermilion City is Sprint 13 scope, remove the door reference or make it a blocked door with a "This way is closed" sign until the gate map is ready

---

## Summary

27/28 checklist items pass. One item is a conditional pass due to a missing map reference.

Sprint 12 frontend is well-implemented:
- NuggetBridge module with state tracking, trainer progression, nugget award
- BillEvent module with full 4-state machine and S.S. Ticket
- Routes 24, 25, 5, 6 and Underground Path properly defined with transitions
- Bill's House (8x8) with NPC and dialogue
- Cerulean burgled house (8x8) with robbery NPC
- Rocket Grunt and Gate Guard sprites (16x16 pixel art)
- 8 new API methods wired and exported
- Both new script tags in index.html

**Overall Verdict: CONDITIONAL PASS** — Fix Bug #1 (`vermilion_gate` missing map) before merging.
