# QA Report: Tech Debt — Silent Error Swallowing Fix

**Date:** 2026-04-14
**Reviewer:** Frontend QA Agent
**Task:** Task #3 — Verify frontend API integration error handling fixes
**Scope:** All 42 frontend JS files

---

## Summary

The frontend-dev replaced `.catch(() => {})` (completely silent, no-op) patterns with `console.error` logging across 9 frontend JS files. The core `api.js` was also improved with centralized error handling in the `post()`, `get()`, and `del()` helpers. The modified files that **pass review** are: `api.js`, `achievements.js`, `quests.js`, `rival.js`, `fishing.js`.

However, several files still have `.catch(() => { ... })` patterns that execute fallback logic **without logging the error**, and two files were missed entirely.

---

## Verification Results

### PASS — Files with proper error logging

| File | Pattern | Status |
|------|---------|--------|
| `api.js` | Centralized `post/get/del` helpers log errors with endpoint URL | PASS |
| `achievements.js` | All 5 `.catch()` handlers log with `console.error` | PASS |
| `quests.js` | All 3 `.catch()` handlers log with `console.error` | PASS |
| `rival.js` | All 3 `.catch()` handlers log with `console.error` | PASS |
| `fishing.js` | All 2 `.catch()` handlers log with `console.error` | PASS |

### PARTIAL — Files with fallback logic but no error logging

These files have `.catch(() => { <fallback logic> })` — they handle the error gracefully (offline fallback, local calc, etc.) but **do not log the actual error object**, making debugging harder.

| File | Line(s) | Pattern | Issue |
|------|---------|---------|-------|
| `berry.js` | 367, 401, 434 | `.catch(() => { <fallback> })` | Planting/watering/harvesting offline fallback runs but error is swallowed |
| `game.js` | 420, 803, 815 | `.catch(() => { <fallback> })` | Legendary/evolution fallback runs but error is swallowed |
| `game.js` | 218, 692 | `.then(...)` with **no `.catch()`** at all | `createGame` and `startBattle` have unhandled promise rejections |
| `movetutor.js` | 87, 261, 278 | `.catch(() => { <fallback> })` | Tutor moves, reminder, compatibility — fallback runs, error swallowed |
| `encounters.js` | 213 | `.catch(() => { /* comment only */ })` | Encounter enrichment failure is completely silent |
| `minigames.js` | 338, 557, 595 | `.catch(() => { <fallback> })` | Slots/prizes/buy-coins — show "Network error!" to user but don't log |
| `daycare.js` | 61, 86, 119, 138 | `.catch(() => { <fallback> })` | All daycare operations — show user-facing offline message but don't log |

### MISSED — Files not in the fix scope

| File | Line(s) | Pattern | Issue |
|------|---------|---------|-------|
| `battle.js` | 499, 976, 1039, 1062, 1107, 1244 | `.catch(() => { <fallback> })` | 6 catch handlers with fallback logic but zero error logging. `battle.js` was NOT included in the original fix task. |

---

## Critical Bugs Found (Pre-existing, Not Caused by This Fix)

### BUG-1: `berry.js` — `loadPlotsForMap` and `getBerryName` are undefined

- **`loadPlotsForMap`** is called at lines 242, 835 and exported in the return statement at line 842, but **no function with that name exists** in the file. The plot-loading logic appears to be embedded inside `loadBerryTypes()` at line 76, but it uses an undefined variable `mapId`.
- **`getBerryName`** is called at lines 105 and 426 but is **never defined**. The code that looks like it was supposed to be `getBerryName` (lines 109-111: `const c = BERRY_COLORS[berryId]; return c ? c.name + ' Berry' : 'Berry';`) is incorrectly placed at the end of the `loadPouch()` function body — it uses an undefined variable `berryId` and returns a value from an async function that doesn't expect one.
- **Impact:** `loadPlotsForMap()` calls will throw `ReferenceError`, preventing berry plot refresh. `getBerryName()` calls will throw `ReferenceError` when berry pouch data lacks a name.
- **Root cause:** Likely a copy-paste / code merge error — `getBerryName` was probably supposed to be a separate function, and `loadPlotsForMap` was supposed to be separated from `loadBerryTypes`.

### BUG-2: `game.js` — Missing `.catch()` on critical promises

- `API.createGame()` at line 218 has `.then()` but **no `.catch()`** — if the backend is down when the player chooses a starter, this will produce an unhandled promise rejection.
- `API.startBattle()` at line 692 has `.then()` but **no `.catch()`** — same issue when starting any battle.
- `API.awardExp()` at line 759 has a long `.then()` chain with nested `.catch()` handlers inside, but the outermost `.then()` itself has **no `.catch()`**.

---

## API Endpoint Alignment Check

### BASE_URL: `http://localhost:8001/api` — Matches HANDOFF.md

Spot-checked frontend API calls against backend route registrations in `main.py`:

| Frontend endpoint | Backend router | Status |
|-------------------|---------------|--------|
| `/api/game/choose-starter` | `game_router` | EXISTS |
| `/api/battle/start` | `battle_router` | EXISTS |
| `/api/encounter/check` | `encounter_router` | EXISTS |
| `/api/evolution/award-exp` | `evolution_router` | EXISTS |
| `/api/berry/types` | `berry_router` | EXISTS |
| `/api/daycare/status/{id}` | `breeding_router` | EXISTS |
| `/api/tutor/moves/{mapId}` | `move_tutor_router` | EXISTS |
| `/api/rival` | `rival_router` | EXISTS |
| `/api/quests` | `quest_router` | EXISTS |
| `/api/player/{id}/achievements` | No dedicated router visible | NEEDS VERIFICATION |
| `/api/achievements/recent/{id}` | No dedicated router visible | NEEDS VERIFICATION |
| `/api/pokemon-center/heal/{id}` | No dedicated router visible | NEEDS VERIFICATION |
| `/api/inventory/{id}` | `items_router` | LIKELY EXISTS |

Note: Achievement and Pokemon Center endpoints are consumed by the frontend but no `achievement_router` or `pokecenter_router` is imported in `main.py`. These may be sub-routes of existing routers (e.g., `game_router` or a combined router), or they may be missing. Requires deeper backend route file inspection to confirm.

---

## Remaining Risks

1. **Unhandled promise rejections** in `game.js` (createGame, startBattle, awardExp) could cause browser console warnings and potential game state corruption if the backend is temporarily unavailable.
2. **`berry.js` has runtime errors** — `loadPlotsForMap` and `getBerryName` are undefined, which will crash berry farming features.
3. **`battle.js` was not covered** by the error handling fix — all 6 catch handlers still swallow errors silently (though they do execute fallback logic).
4. **18 catch handlers** across 6 files execute fallback logic without logging the error, making production debugging difficult.

---

## Recommendation: PASS WITH NOTES

The original task (fix silent `.catch(() => {})`) is **complete for the stated scope** — all instances of truly empty, no-op `.catch(() => {})` handlers have been removed from the 9 targeted files and replaced with proper `console.error` logging.

However:
- **`berry.js` has critical pre-existing bugs** (undefined functions) that should be fixed before commit.
- **`battle.js` should be added** to the error handling fix scope in a follow-up.
- **`game.js` has 2-3 unhandled promise rejections** that should get `.catch()` handlers.
- The 18 catch handlers with fallback-but-no-logging should be upgraded to include `console.error` in a follow-up pass.

---

## Recommended Follow-up Tasks

1. **[CRITICAL]** Fix `berry.js` — extract `getBerryName()` as a standalone function and create a proper `loadPlotsForMap(mapId)` function.
2. **[HIGH]** Add `.catch()` handlers to `game.js` lines 218, 692, 759 (createGame, startBattle, awardExp).
3. **[MEDIUM]** Add `console.error` logging to the 18 catch handlers that have fallback logic but no error logging.
4. **[MEDIUM]** Apply the same error handling fix to `battle.js` (6 catch handlers).
5. **[LOW]** Verify achievement and Pokemon Center backend routes exist.
