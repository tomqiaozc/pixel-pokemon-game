# Sprint 11 Frontend QA Report

**Date:** 2026-04-14
**Reviewer:** Frontend QA Tester (Agent)
**Checklist Used:** `frontend/tests/QA_CHECKLIST_SPRINT_11.md`

---

## Overall Verdict: CONDITIONAL PASS

Sprint 11 delivers 4 features (Route 4, Cerulean City, Cerulean Gym, 12 new Pokemon sprites). Sprites, signs, state machine integration, and error handling all pass. However, **1 critical bug** (Misty gym leader battle uses wrong Pokemon) and **1 medium bug** (2 inaccessible buildings) must be fixed before release.

---

## Feature Reviews

### F4: Pokemon Sprites — PASS

**File:** `sprites.js` (lines ~820-975)

- 12 new species sprite functions added: `drawSpecies23` through `drawSpecies64`
- All use `createCanvas(TILE, TILE)` for correct 16x16 bounds
- All sprites cached via existing cache mechanism
- All 12 exported in the module's return block (lines 976-1006)
- No pixel coordinates exceed 0-15 range (within TILE bounds)
- Naming convention consistent: `drawSpeciesXX()` using species ID number

**Checklist items:** All PASS. No issues found.

---

### F1: Route 4 — PASS

**File:** `routes.js` (lines 330-407 build, 497-515 trainers, 600-616 registration)

- Map dimensions: 30x20 tiles — correct
- Terrain: winding dirt path, 2 tall grass zones, 2 ledge rows, water puddle — all present
- Exit west → `mt_moon_entrance`, exit east → `cerulean_city` — correct connectivity
- 3 trainers registered: Hiker Marcos (8,5), Lass Dana (20,9), Youngster Timmy (14,15)
- Ledges registered in map config
- Sign at (15,9): "Mt. Moon - Cerulean City" — PASS

| Check | Result |
|-------|--------|
| Map builds without error | PASS |
| Exits connect correctly | PASS |
| Trainers have valid teams | PASS |
| Tall grass zones placed | PASS |
| Ledges registered | PASS |
| Sign text correct | PASS |

**Minor note (LOW):** Trainer names/positions differ slightly from plan (cosmetic, gameplay-adjusted). No functional impact.

---

### F2: Cerulean City — CONDITIONAL PASS

**File:** `routes.js` (lines 410-473 build, 618-644 registration), `npc.js`, `signs.js`

- Map dimensions: 25x25 tiles — correct
- 4 buildings rendered: Pokemon Center, Poke Mart, Gym, Bike Shop — all present in layout
- Surfable water pond at y=17-22, x=16-23 — correct
- 5 NPCs defined: Nurse Joy, Shopkeeper, Fisher, Bike Fan, Swimmer — all use valid NPC types
- Sign at (12,10): "A Mysterious, Blue Aura Surrounds It" — PASS

| Check | Result | Notes |
|-------|--------|-------|
| Map builds without error | PASS | |
| All 4 buildings rendered | PASS | |
| Pokemon Center door | PASS | (5,7) → pokecenter |
| Cerulean Gym door | PASS | (20,7) → cerulean_gym |
| Poke Mart door | **FAIL** | Not in doors array |
| Bike Shop door | **FAIL** | Not in doors array |
| NPCs present & typed | PASS | |
| Sign text correct | PASS | |
| Water pond placed | PASS | |

#### BUG — MEDIUM: Missing building doors

**Location:** `routes.js:627-629`

The Cerulean City registration only has 2 doors:
```javascript
doors: [
    { x: 5, y: 7, targetMap: 'pokecenter', spawnX: 7, spawnY: 9 },
    { x: 20, y: 7, targetMap: 'cerulean_gym', spawnX: 7, spawnY: 15 },
],
```

**Missing:**
- Poke Mart door at approximately (14, 7) — building is rendered but player cannot enter
- Bike Shop door at approximately (5, 19) — building is rendered but player cannot enter

**Impact:** Two buildings are visible but inaccessible. The Shopkeeper NPC references the Poke Mart, and the Bike Fan NPC references the Bike Shop, creating a misleading experience.

**Fix:** Add door entries for Poke Mart and Bike Shop. Poke Mart can target `'pokemart'` or a generic interior; Bike Shop can target `'bike_shop'` or show a dialogue.

---

### F3: Cerulean Gym — CONDITIONAL PASS

**File:** `gym.js` (lines 51-68 definition, 183-230 build), `game.js` (lines 587-591 door handler, 198-205 leader battle)

- Gym definition: Misty, Water type, Cascade Badge (index 1), 12x12 interior — correct
- `buildCeruleanGym()`: water pool (PUZZLE tiles) at center, barriers, walkways — correct
- Water theme colors in `drawGymTile()`: floor `#c0d8e8`, wall `#4070a0` — correct
- Leader sprite: Misty-specific orange hair (`#e06030`) — correct
- Door handler in `game.js:587-591`: dispatches to `Gym.enter('cerulean')` — correct
- Cascade Badge in `badges.js`: index 1, name "Cascade Badge", leader "Misty" — correct

| Check | Result | Notes |
|-------|--------|-------|
| Gym definition correct | PASS | |
| Interior layout builds | PASS | |
| Water theme renders | PASS | |
| Door handler works | PASS | |
| Badge definition correct | PASS | |
| Leader battle Pokemon | **FAIL** | Critical bug — see below |
| Gym trainers | LOW | Diana has 1 Pokemon instead of 2 |

#### BUG — CRITICAL: Misty battles with Rhydon L50

**Location:** `game.js:198-205`

```javascript
const leaderPokemon = {
    name: result.leader.type === 'Rock' ? 'Onix' : 'Rhydon',
    level: result.leader.type === 'Rock' ? 14 : 50,
    hp: result.leader.type === 'Rock' ? 35 : 105,
    maxHp: result.leader.type === 'Rock' ? 35 : 105,
    type: result.leader.type,
};
```

The leader Pokemon construction only has a ternary for Rock type (Brock). **Any non-Rock gym leader defaults to Rhydon L50 with 105 HP.** This means:

- **Misty (Water)** → Rhydon L50 (should be Starmie ~L21)
- Giovanni (Ground) → Rhydon L50 (coincidentally reasonable but unintentional)

**Impact:** Game-breaking for Cerulean Gym. A level 50 Rhydon is unbeatable at the expected player level (~15-20). Additionally, Rhydon is Rock/Ground type, not Water — thematically wrong for Misty.

**Fix:** Extend the ternary to a lookup or chain:
```javascript
// Suggested fix pattern:
const leaderTeams = {
    Rock:  { name: 'Onix',    level: 14, hp: 35  },
    Water: { name: 'Starmie', level: 21, hp: 50  },
    // ... future gym types
};
const team = leaderTeams[result.leader.type] || { name: 'Rhydon', level: 50, hp: 105 };
```

#### BUG — LOW: Gym trainer Diana has 1 Pokemon instead of 2

**Location:** `gym.js` cerulean gym trainers definition

Diana has only Goldeen L16. Plan specified 2 Pokemon (Horsea L16, Shellder L16). Luis correctly has 2 Pokemon (Horsea L16, Shellder L17). Minor gameplay impact — gym is slightly easier than intended.

---

## Cross-Cutting Checks

| Check | Result | Notes |
|-------|--------|-------|
| Silent `.catch(() => {})` patterns | PASS | Zero matches across all frontend JS |
| `BASE_URL` consistency | PASS | No new API references added |
| Game state machine | PASS | No new states added; `cerulean_gym` door handler correctly uses existing `'gym'` state |
| Pewter Gym regression | PASS | `game.js` Rock-type ternary branch unchanged; Brock still gets Onix L14 |
| `index.html` script tags | PASS | No new files to include — all changes in existing modules |
| Module IIFE pattern | PASS | No new modules; existing patterns maintained |

### INFO: Missing SPECIES_IDS entries

**Location:** `game.js:750-761`

The `SPECIES_IDS` lookup map does not include most Sprint 11 species:
- Missing: Ekans (23), Nidoran-F (29), Nidoran-M (32), Jigglypuff (39), Abra (63), Kadabra (64)
- Present: Oddish (43)

**Impact:** EXP calculation for battles against these species will use fallback ID 19 (Rattata), giving slightly incorrect EXP yields. Low gameplay impact but technically incorrect.

---

## Summary of Findings

| # | Severity | Component | Description |
|---|----------|-----------|-------------|
| 1 | **CRITICAL** | `game.js:198-205` | Misty gym leader battle uses Rhydon L50 instead of Water-type Pokemon |
| 2 | **MEDIUM** | `routes.js:627-629` | Cerulean City missing Poke Mart and Bike Shop door entries |
| 3 | LOW | `gym.js` cerulean trainers | Diana has 1 Pokemon instead of planned 2 |
| 4 | INFO | `game.js:750-761` | `SPECIES_IDS` missing 6 Sprint 11 species |

**Recommendation:** Fix #1 (CRITICAL) and #2 (MEDIUM) before merging. Items #3 and #4 can be deferred to Sprint 12.

---

*Report generated by Frontend QA Tester agent using QA_CHECKLIST_SPRINT_11.md*
