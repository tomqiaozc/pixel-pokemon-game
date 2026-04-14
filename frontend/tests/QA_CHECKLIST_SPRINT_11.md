# QA Checklist: Sprint 11 — Route 4, Cerulean City, Misty's Gym & Pokemon Sprites

**Date Created:** 2026-04-14
**Reviewer:** Frontend QA Agent
**Sprint Plan:** `SPRINT_11_PLAN.md`
**Status:** PRE-REVIEW (checklists prepared ahead of implementation)

---

## How to Use This Document

Each feature section below contains:
1. **Files to Review** — which files to read for this feature
2. **Verification Checklist** — specific items to verify in the code
3. **Integration Checks** — API wiring, error handling, state machine

Mark each item `[x]` when verified during the actual review. Add findings inline.

---

## F1: Route 4 (`routes.js`, `map.js`)

### Files to Review

| File | What to Check |
|------|---------------|
| `frontend/js/routes.js` | Route 4 tile layout registered, `renderRoute4()` function exists |
| `frontend/js/map.js` | Collision data for Route 4 tiles |
| `frontend/js/maploader.js` | Route 4 map config (width: 30, height: 20, connections) |
| `frontend/js/game.js` | `loadMap('route_4')` path works, no new game states added |
| `frontend/js/api.js` | Map transition API calls work for Route 4 |

### Verification Checklist

#### Map Layout & Rendering
- [ ] `routes.js` contains Route 4 tile layout definition
- [ ] Route 4 registered in `Routes.registerAll()` or equivalent registration system
- [ ] Map dimensions match backend: **30 tiles wide x 20 tiles tall**
- [ ] Dirt path connects west (Mt. Moon exit) to east (Cerulean City entrance)
- [ ] Border tiles (trees/rocks) prevent walking off-map

#### Map Transitions
- [ ] **West exit** → `mt_moon_entrance` at entry coordinates `(24, 15)` per plan
- [ ] **East exit** → `cerulean_city` at entry coordinates `(0, 12)` per plan
- [ ] Transitions use existing `MapLoader.transitionTo()` — no custom transition code
- [ ] `MapLoader` config for `route_4` includes correct `connections` array
- [ ] Reverse: `mt_moon_entrance` has east connection to `route_4` at `(0, 10)`

#### Grass Encounter Zones
- [ ] Tall grass patches at correct coordinates matching backend:
  - Zone 1: x=5, y=5, width=8, height=6
  - Zone 2: x=18, y=10, width=6, height=5
- [ ] Tall grass tiles use existing `T.TALL_GRASS` tile type (not a new type)
- [ ] `Encounters.update()` triggers correctly in these zones (no new encounter code needed)

#### Trainers
- [ ] 3 trainers positioned at correct tile coordinates:
  - `lass_crissy` at (8, 10) facing right, sight range 3
  - `youngster_timmy` at (18, 8) facing down, sight range 4
  - `hiker_marcos` at (24, 14) facing left, sight range 3
- [ ] Trainer sprites render (may use existing trainer class sprites)
- [ ] Trainer sight lines trigger battles via existing `TrainerEncounter` system
- [ ] Defeated trainers persist across map re-entries

#### Ledges (if applicable)
- [ ] If ledge tiles exist: south-facing ledges for shortcut back
- [ ] Ledge jump uses existing `Ledges.tryJump()` system
- [ ] Cannot climb ledges northward (one-way)

#### Collision
- [ ] `isSolidForMovement()` returns correct values for all Route 4 tile types
- [ ] Player cannot walk through trees, rocks, or off-map boundaries
- [ ] Water tiles (if any) are solid unless surfing

### Integration Checks
- [ ] All API calls have `.catch(err => console.error(...))` — no silent catches
- [ ] No `.catch(() => {})` patterns
- [ ] No new game states added to game.js for Route 4 (uses existing `overworld`)
- [ ] Camera follows player correctly on the 30x20 map (test at map edges)

---

## F2: Cerulean City (`routes.js`, `npc.js`, `signs.js`, `sprites.js`)

### Files to Review

| File | What to Check |
|------|---------------|
| `frontend/js/routes.js` | Cerulean City tile layout, building placement |
| `frontend/js/map.js` | Collision data, door tiles |
| `frontend/js/maploader.js` | Cerulean City + 4 interior map configs |
| `frontend/js/npc.js` | 5 new NPC registrations, positions, dialogue triggers |
| `frontend/js/signs.js` | Cerulean City entrance sign |
| `frontend/js/sprites.js` | Any new building sprites (water-themed gym, etc.) |
| `frontend/js/game.js` | Door interactions for 4 Cerulean buildings |
| `frontend/js/api.js` | NPC dialogue API calls |

### Verification Checklist

#### Map Layout & Rendering
- [ ] `routes.js` contains Cerulean City tile layout definition
- [ ] Map dimensions match backend: **25 tiles wide x 25 tiles tall**
- [ ] City has 4 buildings at correct positions:
  - Pokemon Center: (3, 8), 5x4
  - Poke Mart: (10, 3), 4x4
  - Cerulean Gym: (15, 3), 6x5
  - Bike Shop: (3, 3), 4x4
- [ ] Building roof sprites render correctly (gym should have water/blue theme)
- [ ] Paths connect all buildings and city entrances
- [ ] Trees/borders prevent leaving map except via designated exits

#### Building Doors
- [ ] Pokemon Center door at (5, 12) → transitions to `cerulean_pokemon_center`
- [ ] Poke Mart door at (12, 7) → transitions to `cerulean_pokemart`
- [ ] Cerulean Gym door at (17, 8) → transitions to `cerulean_gym`
- [ ] Bike Shop door at (5, 7) → transitions to `bike_shop`
- [ ] All door interactions use existing `MapLoader.checkDoors()` system
- [ ] Exiting each interior returns player to correct overworld position outside the door

#### Interior Maps
- [ ] `cerulean_pokemon_center` map config exists in MapLoader (10x8, interior type)
- [ ] `cerulean_pokemart` map config exists (8x8, interior type)
- [ ] `cerulean_gym` map config exists (12x12, gym type)
- [ ] `bike_shop` map config exists (8x6, interior type)
- [ ] Each interior has correct tile layout with counter, NPCs, walls

#### Pokemon Center
- [ ] Entering Pokemon Center triggers `PokeCenter.enter()` or equivalent
- [ ] Nurse Joy NPC at (5, 2) triggers healing dialogue
- [ ] Healing flow works (same as existing Pokemon Center behavior)
- [ ] Exit returns to Cerulean City overworld

#### Poke Mart
- [ ] Shop clerk NPC at (4, 2) triggers shop interface
- [ ] Cerulean Poke Mart has correct inventory (per `shops.json`)
- [ ] Buy/sell flow works (if implemented)

#### NPCs
- [ ] 5 NPCs registered with correct positions:
  - `cerulean_townsfolk_1` at (8, 12) facing down
  - `cerulean_townsfolk_2` at (15, 8) facing left
  - `cerulean_townsfolk_3` at (20, 15) facing up
  - `bike_shop_owner` at (5, 5) facing down
  - `cerulean_officer` at (12, 20) facing right
- [ ] Each NPC triggers dialogue on action key interaction
- [ ] NPC collision prevents walking through them (`NPC.isSolid()`)
- [ ] Dialogue text matches backend data (or has reasonable fallback)
- [ ] Bike Shop owner mentions Bike Voucher / 1,000,000 price

#### Signs
- [ ] City sign exists near entrance (west side, where player enters from Route 4)
- [ ] Sign text: "Welcome to Cerulean City" or similar
- [ ] Sign interaction uses existing `Signs.checkInteraction()` system

#### Surfable Water
- [ ] Water zone in southeast corner (around x=18, y=18, 5x5 per plan)
- [ ] Water tiles are solid for walking, surfable if Sprint 10 Surf system is wired
- [ ] Encounter table `cerulean_city_surfing` triggers while surfing (if applicable)

### Integration Checks
- [ ] All API calls have `.catch(err => console.error(...))` — no silent catches
- [ ] No new game states for Cerulean City (uses existing `overworld`, `pokecenter`)
- [ ] NPC dialogue loads from backend with proper error handling
- [ ] No 404 endpoints in API calls

---

## F3: Cerulean Gym (`gym.js`, `sprites.js`, `badges.js`)

### Files to Review

| File | What to Check |
|------|---------------|
| `frontend/js/gym.js` | Cerulean Gym layout, battle flow, Misty entry |
| `frontend/js/sprites.js` | Misty sprite, gym trainer sprites, water pool tiles |
| `frontend/js/badges.js` | Cascade Badge sprite (`drawCascadeBadge()`) |
| `frontend/js/game.js` | Gym state handler works for `cerulean_gym` (should use existing gym state) |
| `frontend/js/api.js` | Gym challenge, battle, badge award API calls |

### Verification Checklist

#### Gym Interior
- [ ] `gym.js` has Cerulean Gym layout rendering (water-themed)
- [ ] Gym enter function accepts `'cerulean'` parameter: `Gym.enter('cerulean')`
- [ ] Water pool tiles render in center of gym
- [ ] Walkways around edges for player movement
- [ ] Misty positioned at back of gym (check exact coordinates)
- [ ] Interior walls prevent leaving except through door

#### Gym Trainers
- [ ] 2 gym trainers positioned correctly:
  - `cerulean_gym_trainer_1` (Diana/Swimmer) at (4, 6) facing right, sight 3
  - `cerulean_gym_trainer_2` (Luis/Swimmer) at (8, 6) facing left, sight 3
- [ ] Trainers trigger battle when player walks into sight range
- [ ] Trainer battles use existing `TrainerEncounter` / gym trainer system
- [ ] Trainer teams match backend data:
  - Diana: Horsea L16, Shellder L16
  - Luis: Goldeen L17, Horsea L17

#### Misty Battle
- [ ] Path to Misty is blocked until both gym trainers are defeated
- [ ] Misty battle starts on interaction (action key near Misty)
- [ ] Misty's team matches backend `gyms.json`: **Staryu L18, Starmie L21**
- [ ] Battle uses existing gym leader battle flow (`canRun: false, battleType: 'trainer'`)
- [ ] `pendingBadge` set correctly for Cascade Badge before battle starts

#### Cascade Badge
- [ ] `badges.js` has `drawCascadeBadge()` or equivalent at badge index for Cerulean
- [ ] Badge sprite: teardrop shape, blue fill, light blue highlight (per plan)
- [ ] Badge awarded on victory via existing `BadgeCase.earnBadge()` flow
- [ ] Badge appears in badge display / trainer card
- [ ] `Quests.onBadgeEarned()` called with correct badge index

#### Post-Victory
- [ ] Post-battle dialogue displays (Misty congratulates, mentions TM11 Bubblebeam)
- [ ] Player returns to gym interior after badge award screen
- [ ] Misty does not trigger re-battle after defeat

#### State Machine
- [ ] Cerulean Gym uses existing `'gym'` game state — no new state added
- [ ] `game.js` gym door check: entering `cerulean_gym` door triggers `Gym.enter('cerulean')` and `state = 'gym'`
- [ ] Existing Pewter Gym flow is NOT broken (regression check)
- [ ] Badge award state transition works correctly (same as Pewter/Boulder Badge)

### Integration Checks
- [ ] All gym-related API calls have `.catch(err => console.error(...))` — no silent catches
- [ ] `API.startBattle()` called for gym trainer and Misty battles with `.catch()`
- [ ] Badge award API call has error handling
- [ ] No 404 endpoints during full gym run

---

## F4: Pokemon Sprites (`sprites.js`)

### Files to Review

| File | What to Check |
|------|---------------|
| `frontend/js/sprites.js` | 12 new sprite functions, caching, exports |

### Verification Checklist

#### Sprite Functions Exist
- [ ] `drawSpecies23()` or equivalent — Ekans (purple snake, coiled, yellow rattle)
- [ ] `drawSpecies24()` — Arbok (larger purple cobra, hood pattern)
- [ ] `drawSpecies29()` — Nidoran-F (small blue quadruped, spots, horn)
- [ ] `drawSpecies30()` — Nidorina (larger blue, spines, darker spots)
- [ ] `drawSpecies32()` — Nidoran-M (small purple quadruped, large ears, horn)
- [ ] `drawSpecies33()` — Nidorino (larger purple, bigger horn, spines)
- [ ] `drawSpecies39()` — Jigglypuff (round pink circle, tuft, big eyes)
- [ ] `drawSpecies40()` — Wigglytuff (taller pink, rabbit ears, big eyes)
- [ ] `drawSpecies43()` — Oddish (blue body, green leaves on top)
- [ ] `drawSpecies44()` — Gloom (larger blue, droopy flower, drool)
- [ ] `drawSpecies63()` — Abra (yellow, seated pose, fox-like)
- [ ] `drawSpecies64()` — Kadabra (yellow/brown, spoon, mustache)

**Note:** Function names may follow a different pattern (e.g., `drawEkans()`, `drawOddish()`). Verify against existing naming convention in sprites.js — current convention uses `drawPlayer()`, `drawGrass()`, `drawCuttableTree()` etc. (no species ID numbers). Check actual pattern used.

#### Sprite Quality
- [ ] Each sprite uses `createCanvas(TILE, TILE)` — stays within 16x16 bounds
- [ ] Each sprite is cached (e.g., `if (cache.ekans) return cache.ekans`)
- [ ] Each sprite is exported in the `return { ... }` block
- [ ] No sprite overflows beyond 16x16 tile dimensions (verify pixel coordinates)
- [ ] Colors are reasonable for each species (purple for Ekans/Nidoran-M, blue for Nidoran-F, pink for Jigglypuff, etc.)

#### Integration
- [ ] Sprites render in battle screen (verify battle.js can look up sprite by species name or ID)
- [ ] Sprites render in Pokedex (verify pokedex.js can look up sprite)
- [ ] Sprites render in party menu (if party display uses species sprites)
- [ ] No missing sprite causes a crash or blank render — verify fallback behavior

---

## Cross-Cutting Checks

### Error Handling Scan
- [ ] `grep -r '.catch(() => {' frontend/js/` returns **zero matches** (no new silent catches introduced)
- [ ] `grep -r '.catch(() =>' frontend/js/` — any matches must have `console.error()` inside the handler
- [ ] All new API calls in modified files use `.catch(err => console.error('descriptive message:', err))`
- [ ] No `.then()` chains without a `.catch()` at the end (especially in game.js)

### API Endpoint Alignment
- [ ] All new frontend API calls use `BASE_URL` = `http://localhost:8001/api`
- [ ] Map transition endpoints match backend router paths
- [ ] Gym challenge/battle endpoints match backend router paths
- [ ] NPC dialogue endpoints match backend router paths
- [ ] No hardcoded URLs outside of `api.js`

### game.js State Machine Coherence
- [ ] No new game states added for Sprint 11 features (Route 4 = overworld, Cerulean = overworld, Gym = existing gym state)
- [ ] `loadMap()` function handles `route_4` and `cerulean_city` correctly
- [ ] Gym door check in `updateOverworld()` handles `cerulean_gym` door
- [ ] Existing states (starter, overworld, battle, evolution, pokecenter, gym, badge_award, minigame, cutscene, hatch, secret_discovery, hm_animation) still function correctly
- [ ] No state transition can leave the game stuck (verify all exit conditions)

### index.html Script Tags
- [ ] No new script tags needed for Sprint 11 (all changes are to existing files)
- [ ] If any new JS files were added: verify they are included in correct load order
- [ ] `api.js` and `game.js` remain the last two scripts loaded

### Regression Check
- [ ] Pewter Gym (Brock) still works end-to-end after gym.js changes
- [ ] Boulder Badge still awards correctly
- [ ] Existing map transitions (Pallet → Route 1 → Viridian → Route 2 → Pewter → Route 3 → Mt. Moon) still work
- [ ] Sprint 10 features (Secret Areas, HM Puzzles, Cave System) still function
- [ ] No existing sprite functions broken by sprites.js additions

---

## Backend Route Verification

Before reviewing frontend code, verify these backend routes exist:

- [ ] `GET /api/map/route_4` — Route 4 map data
- [ ] `GET /api/map/cerulean_city` — Cerulean City map data
- [ ] `GET /api/map/cerulean_pokemon_center` — Interior map data
- [ ] `GET /api/map/cerulean_pokemart` — Interior map data
- [ ] `GET /api/map/cerulean_gym` — Gym map data
- [ ] `GET /api/map/bike_shop` — Interior map data
- [ ] `POST /api/map/transition` — Handles Route 4 transitions
- [ ] `GET /api/gym/cerulean_gym` — Cerulean gym data with Misty's team
- [ ] `POST /api/gym/challenge` — Challenge cerulean gym
- [ ] `POST /api/gym/award-badge` — Award Cascade Badge
- [ ] `GET /api/npc/{npc_id}` — Returns NPC data for all 6 new NPCs
- [ ] `GET /api/encounter/table/route_4` — Route 4 encounter table
- [ ] `GET /api/encounter/table/cerulean_city_surfing` — Surfing encounters

---

## Review Workflow

When each feature is completed by the frontend-dev:

1. **Read all files listed** in the feature's "Files to Review" table
2. **Walk through checklist** item by item, marking `[x]` or noting failures
3. **Run cross-cutting checks** against the modified files
4. **Write findings** inline in this document or in a separate `QA_REPORT_SPRINT_11.md`
5. **Report to team-lead** with verdict: PASS / PASS WITH NOTES / FAIL

**Review order should follow merge order:** F4 (sprites) → F1 (Route 4) → F2 (Cerulean) → F3 (Gym)
