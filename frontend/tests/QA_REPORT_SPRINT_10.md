# QA Report: Sprint 10 — Secret Areas, HM Puzzles, Cave System

**Date:** 2026-04-14
**Reviewer:** Frontend QA Agent
**Task:** Task #20 — Final Sprint 10 frontend QA review
**Scope:** 3 new modules (`secretareas.js`, `hmpuzzles.js`, `cave.js`), API integration (`api.js`), game loop integration (`game.js`, `renderer.js`, `sprites.js`, `map.js`, `maploader.js`), and `index.html` script loading

---

## Overall Verdict: PASS

All 3 new frontend modules are well-structured, properly integrated into the game loop, and follow existing codebase conventions. No critical bugs found in the new Sprint 10 code.

---

## 1. New Module Review

### 1.1 `secretareas.js` (217 lines) — PASS

| Check | Result |
|-------|--------|
| IIFE module pattern | PASS — standard `const SecretAreas = (() => { ... })()` |
| API calls with error logging | PASS — 3 API calls, all have `.catch(err => console.error(...))` |
| State management | PASS — `discovered` map of `mapId -> Set("x,y")`, clean design |
| Animation system | PASS — 3-phase discovery animation (sparkle burst, reveal flash, floating text), 2000ms duration |
| Public API exports | PASS — all necessary functions exported |
| Cross-module integration | PASS — calls `PlayerStats.increment('secretsFound')` and `Quests.setFlag()` |

**Note:** `renderShimmer()` function (line 190) is defined but has an empty body (returns immediately if `animActive`). Not a bug — appears to be a placeholder for future shimmer hints on undiscovered areas.

### 1.2 `hmpuzzles.js` (408 lines) — PASS

| Check | Result |
|-------|--------|
| IIFE module pattern | PASS |
| API calls with error logging | PASS — 5 API calls (`getHMObstacles`, `getHMObstacleState`, `useHM`, `pushBoulder`, `useHM` for Strength), all have `.catch(err => console.error(...))` |
| Obstacle collision | PASS — `isObstacleAt()` correctly handles both cuttable trees and pushable boulders, skips removed obstacles, checks boulder pushed positions |
| Cut animation | PASS — 3-frame animation (slash, shake, fade+leaf particles), 600ms |
| Boulder push | PASS — checks destination for solids/other obstacles before pushing, 300ms interpolated animation |
| Strength activation | PASS — per-map-session (resets on `onMapChange`), requires HM prompt confirmation |
| HM prompt system | PASS — uses `Dialogue.start()` for confirmation, clean prompt state management |
| State persistence | PASS — loads removed/pushed state from backend on map load |

### 1.3 `cave.js` (224 lines) — PASS

| Check | Result |
|-------|--------|
| IIFE module pattern | PASS |
| API calls with error logging | PASS — 3 API calls (`getCaveState`, `useFlash`, `caveTransition`), all have `.catch(err => console.error(...))` |
| Darkness rendering | PASS — uses `destination-out` compositing to punch radial gradient hole in dark overlay |
| Flash animation | PASS — 800ms ease-out cubic interpolation from radius 2 to 10 tiles, white flash + expanding ring effect |
| Cave state management | PASS — per-map state in `caveStates` object, `isDarkCave()` returns true only if dark AND not lit |
| Floor transitions | PASS — `transitionCaveFloor()` calls `MapLoader.transitionTo()`, sets up darkness for new floor |
| Ambient effects | PASS — subtle dust mote particles rendered in lit cave areas |

---

## 2. API Integration (`api.js`)

### 2.1 New Endpoints — PASS

All 14 new API methods verified in `api.js`:

| Module | Methods | BASE_URL | Export |
|--------|---------|----------|--------|
| Secret Areas (4) | `checkSecretArea`, `discoverSecretArea`, `getSecretProgress`, `listSecretAreas` | `localhost:8001` | PASS |
| Cave System (4) | `getCaveState`, `useFlash`, `caveTransition`, `getCaveMaps` | `localhost:8001` | PASS |
| HM Overworld (6) | `useHM`, `pushBoulder`, `getHMObstacles`, `getHMObstacleState`, `getSurfState`, `exitSurf` | `localhost:8001` | PASS |

All 14 methods are properly exported in the `api.js` return statement.

### 2.2 Minor Issue

**`checkSecretArea`** (api.js ~line 717) sends `game_id: gameId` in the request body but lacks the `if (!gameId) return null;` guard that other gameId-dependent methods have. If called before game creation, it will send `game_id: null` to the backend.

- **Severity:** LOW — `checkSecretArea` is only called from `SecretAreas.checkForSecretArea()` which is invoked during overworld movement, well after game creation.
- **Recommendation:** Add the guard for consistency.

---

## 3. Game Loop Integration (`game.js`)

### 3.1 State Machine — PASS

New states added to the game state machine (line 8):
```
starter, overworld, battle, evolution, pokecenter, gym, badge_award, minigame, cutscene, hatch, secret_discovery, hm_animation
```

| State | Update Loop | Render | Exit Condition |
|-------|-------------|--------|----------------|
| `secret_discovery` (line 160) | `SecretAreas.update(dt)` | `Renderer.render()` + `SecretAreas.renderDiscoveryAnimation()` | `!SecretAreas.isAnimating()` -> `overworld` |
| `hm_animation` (line 168) | `HMPuzzles.update(dt)` | `Renderer.render()` + `HMPuzzles.renderObstacles()` + `HMPuzzles.renderHMAnimation()` | `!HMPuzzles.isAnimating()` -> `overworld` |

Both new states properly re-center the camera on exit via `Renderer.centerCamera()`.

### 3.2 Overworld Integration — PASS

| Integration Point | Location | Status |
|-------------------|----------|--------|
| `SecretAreas.update(dt)` called in overworld | Line 82 | PASS |
| `Cave.update(dt)` called in overworld | Line 83 | PASS |
| `HMPuzzles.update(dt)` called in overworld | Line 84 | PASS |
| Secret area hidden entrance rendering | Line 87 | PASS |
| Secret area discovery animation rendering | Line 88 | PASS |
| HM animation overlay rendering | Line 136 | PASS |
| `SecretAreas.checkForSecretArea()` on player step | Line 544 | PASS — called on each walk animation step |
| `SecretAreas.loadDiscoveredAreas()` on init | Line 62 | PASS |
| `SecretAreas.loadDiscoveredAreas()` on map load | Line 641 | PASS |
| `HMPuzzles.tryUseHM()` on action key press | Line 466 | PASS |
| `HMPuzzles.onMapChange()` on map load | Line 649 | PASS |
| Cave enter/exit on map load | Lines 643-647 | PASS — checks `map.isDark` or `map.mapType === 'cave'` |

### 3.3 HM Interaction Placement — PASS

`HMPuzzles.tryUseHM()` is called at line 466, which is **outside and after** the NPC interaction block (lines 400-422). This is correct — HM obstacles should be checked after NPCs, signs, and legendary spawn interactions. The interaction priority order is:

1. Fishing/Surfing (lines 373-388)
2. Berry plots (lines 390-394)
3. Daycare NPC (lines 396-398)
4. Move Tutor / regular NPC (lines 400-422)
5. Legendary spawn (lines 424-458)
6. Signs (lines 460-464)
7. **HM obstacles (line 466)** — correct position

### 3.4 Pre-existing Issues (NOT Sprint 10 regressions)

- `API.awardExp()` at line 803 still lacks an outer `.catch()` handler — inner `.then()` chain (checkEvolution, evolve) has catches, but the outermost promise does not. (Reported in QA_REPORT_TECH_DEBT.md)
- `state = 'secret_discovery'` is never explicitly set anywhere in game.js. The `SecretAreas.renderDiscoveryAnimation()` is called directly in the overworld state (line 88), so the `secret_discovery` state block (lines 160-167) appears to be **dead code**. The animation plays within the overworld state, and the dedicated `secret_discovery` state is never entered. This is not a bug — the animation still works — but the state handler is unused.

---

## 4. Renderer Integration (`renderer.js`)

### 4.1 Render Order — PASS

Sprint 10 additions to the render pipeline (in order):

| Order | What | Line | Status |
|-------|------|------|--------|
| After NPCs | `SecretAreas.renderHiddenEntrance()` | 83 | PASS |
| After secret entrances | `HMPuzzles.renderObstacles()` | 86 | PASS |
| After day/night + weather | Cave darkness overlay | 139-144 | PASS |
| After darkness | Cave ambient particles | 147-149 | PASS |
| After ambient | Flash animation effect | 152-156 | PASS |

### 4.2 Cave Darkness Rendering — PASS

Darkness rendering is properly gated:
```javascript
if (mapConfig && mapConfig.isDark && Cave.isDarkCave(currentMapId))
```
This correctly requires: (1) map config exists, (2) map is marked `isDark`, (3) cave is still dark (not lit by Flash). The player center position is correctly computed and passed to `Cave.renderDarkness()`.

### 4.3 Flash Animation Rendering — PASS

Flash animation is gated by `Cave.isFlashAnimating()` and uses the same player center calculation. Renders after the darkness overlay, which is the correct z-order.

---

## 5. Sprite Definitions (`sprites.js`)

### 5.1 New Sprite Functions — PASS

| Function | Lines | Cached | Exported | Status |
|----------|-------|--------|----------|--------|
| `drawCuttableTree()` | 401-427 | Yes (`cache.cuttableTree`) | Yes | PASS |
| `drawPushableBoulder()` | 429-457 | Yes (`cache.pushableBoulder`) | Yes | PASS |

Both sprites:
- Render on a grass base (consistent with other terrain sprites)
- Use the standard `createCanvas(TILE, TILE)` pattern
- Are properly cached to avoid re-rendering
- Have visual indicators: cuttable tree has dashed yellow outline, boulder has yellow arrow hints

---

## 6. Collision System (`map.js`)

### 6.1 `isSolidForMovement()` — PASS

Sprint 10 additions to collision detection (lines 152-159):

```javascript
// Secret entrances are always passable
if (SecretAreas.isSecretEntrance(MapLoader.getCurrentMapId(), tileX, tileY)) {
    return false;
}
// HM obstacles (cuttable trees, pushable boulders) block movement
if (HMPuzzles.isObstacleAt(MapLoader.getCurrentMapId(), tileX, tileY)) {
    return true;
}
```

**Check order is correct:** secret entrance passability is checked **before** HM obstacle blocking. This prevents a scenario where an obstacle placed on a discovered secret entrance would block access.

---

## 7. Map Loader (`maploader.js`)

### 7.1 Cave Support — PASS

Map configuration includes Sprint 10 fields:
- `isDark` (line 41): `config.isDark || false` — cave darkness mechanics flag
- `mapType` (line 42): `config.mapType || 'overworld'` — supports `'overworld'`, `'cave'`, `'indoor'`

These fields are used by `game.js:loadMap()` (lines 643-647) to trigger `Cave.enterCave()`/`Cave.exitCave()` on map transitions.

`MapLoader.transitionTo()` is used by `Cave.transitionCaveFloor()` for multi-floor cave transitions — the existing transition system (fade-out/loading/fade-in) handles this correctly.

---

## 8. Script Loading (`index.html`)

### 8.1 New Script Tags — PASS

Three new script tags added (lines 51-53):
```html
<script src="js/secretareas.js"></script>
<script src="js/cave.js"></script>
<script src="js/hmpuzzles.js"></script>
```

**Load order verification:**

| Script | Dependencies | Loaded After Dependencies? |
|--------|-------------|---------------------------|
| `secretareas.js` | `Sprites`, `API`, `PlayerStats`, `Quests`, `Dialogue` | PASS — all loaded earlier |
| `cave.js` | `Sprites`, `API`, `MapLoader` | PASS — all loaded earlier |
| `hmpuzzles.js` | `Sprites`, `API`, `GameMap`, `MapLoader`, `Dialogue`, `PlayerStats` | PASS — all loaded earlier |

All 3 scripts are loaded **before** `api.js` and `game.js` (lines 54-55), which is correct since `api.js` exports the API functions they reference, and `game.js` calls their init/integration functions.

**Wait** — `secretareas.js`, `cave.js`, and `hmpuzzles.js` all call `API.*` methods, but they are loaded **before** `api.js` (line 54). This is safe because:
- The modules are IIFEs that only **define** functions referencing `API`
- The `API` calls happen at runtime (on user interaction / map load), not at module load time
- By the time any `API.*` function is called, `api.js` has already been loaded and executed

**PASS** — load order is correct.

---

## 9. Backend Route Registration

### 9.1 New Routers — PASS

All 3 new backend route modules are imported and registered in `backend/main.py`:

| Router | Import | Registered |
|--------|--------|------------|
| `secret_area_router` | Line 25: `from .routes.secret_area import router as secret_area_router` | Line 60: `app.include_router(secret_area_router)` |
| `hm_overworld_router` | Line 26: `from .routes.hm_overworld import router as hm_overworld_router` | Line 61: `app.include_router(hm_overworld_router)` |
| `cave_router` | Line 27: `from .routes.cave import router as cave_router` | Line 62: `app.include_router(cave_router)` |

---

## 10. Silent Error Handling Check

### 10.1 New Modules — PASS

Scanned all 3 new modules for `.catch(() => {})` (empty no-op catch) and `.catch(() =>` (without `{`). **Zero matches found.** All error handlers in the new modules use `console.error()` with descriptive messages.

### 10.2 Full Frontend Scan

Grep for `.catch(() => {` across all frontend JS files returned **zero matches**. The tech debt fix from Task #3 remains intact, and no new silent catch handlers were introduced.

---

## 11. Cross-Module Conflict Analysis

### 11.1 State Machine Conflicts — NONE

The 3 new systems operate independently:
- **SecretAreas**: triggered by player movement (step-based check), visual-only animation in overworld state
- **HMPuzzles**: triggered by action key press, blocks player during animation via `hm_animation` state
- **Cave**: persistent state per map, affects rendering layer only (darkness overlay)

No two systems compete for the same game state or input events.

### 11.2 Rendering Layer Conflicts — NONE

Render order in `renderer.js` is well-layered:
1. Base tiles
2. NPCs
3. Secret area entrances (world-space)
4. HM obstacles (world-space)
5. Player
6. Day/night tint
7. Weather
8. Cave darkness (screen-space overlay)
9. Cave ambient particles
10. Flash animation
11. Map transition fade

Each layer renders independently. Cave darkness correctly uses `destination-out` compositing which does not interfere with other layers.

### 11.3 Collision Conflicts — NONE

`isSolidForMovement()` checks are ordered: secret entrance passability -> HM obstacle blocking -> tile solidity. No circular dependencies or conflicting checks.

---

## 12. Issues Summary

### Sprint 10 Issues (New Code)

| ID | Severity | File | Description |
|----|----------|------|-------------|
| S10-01 | LOW | `api.js` | `checkSecretArea` lacks `if (!gameId) return null` guard (inconsistency, not a functional bug) |
| S10-02 | INFO | `game.js` | `secret_discovery` state (lines 160-167) is defined but never entered — dead code. The secret area animation plays within the `overworld` state instead. |
| S10-03 | INFO | `secretareas.js` | `renderShimmer()` function body is empty — placeholder for future feature |

### Pre-existing Issues (NOT Sprint 10)

| ID | Severity | File | Description |
|----|----------|------|-------------|
| PRE-01 | MEDIUM | `game.js:803` | `API.awardExp()` has no outer `.catch()` — unhandled promise rejection risk (reported in QA_REPORT_TECH_DEBT.md) |
| PRE-02 | CRITICAL | `berry.js` | `loadPlotsForMap` and `getBerryName` are undefined functions (reported in QA_REPORT_TECH_DEBT.md) |

---

## 13. Conclusion

**Verdict: PASS**

All 3 new Sprint 10 frontend modules are production-ready:
- Clean IIFE module pattern with proper encapsulation
- All API calls have proper `.catch(err => console.error(...))` error handlers
- Correctly integrated into the game loop, renderer, collision system, and map loader
- No silent error swallowing introduced
- Backend route handlers are registered for all new endpoints
- Script loading order is correct in `index.html`
- No cross-module conflicts between the 3 new systems
- Sprite functions are cached and exported properly

The only issues found are low-severity (missing gameId guard, dead state handler, empty placeholder function) — none warrant blocking the Sprint 10 release.
