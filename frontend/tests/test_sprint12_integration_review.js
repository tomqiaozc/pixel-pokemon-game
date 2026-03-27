/**
 * Sprint 1-2 Integration Review: End-to-End Feature Verification
 * QA Tester: qa-tester-2
 * Scope: All features from Sprint 1 (core game loop) and Sprint 2 (battle/encounter)
 *
 * This review checks that Sprint 1-2 features work together end-to-end,
 * verifying integration points between frontend modules and frontend-backend
 * communication.
 */


// ============================================================
// GAME INITIALIZATION & STATE MACHINE
// ============================================================

/**
 * TEST: INT-GS01 - Game state machine transitions
 * STATUS: PASS
 *
 * game.js manages states: starter -> overworld -> battle -> evolution -> pokecenter
 *
 * Verified transitions:
 *   - Game starts in 'starter' state (line 10)
 *   - After starter selection, transitions to 'overworld' (line 51)
 *   - Encounter triggers transition to 'battle' (encounters.js -> game.startBattle)
 *   - Battle end transitions back to 'overworld' (game.js line 105)
 *   - Evolution triggers transition to 'evolution' (game.js line 130)
 *   - Pokemon Center door tile triggers 'pokecenter' (game.js line 180)
 *   - All transitions use proper state assignment, no invalid states possible
 */

/**
 * TEST: INT-GS02 - Game loop timing
 * STATUS: PASS
 *
 * game.js uses requestAnimationFrame with delta time:
 *   - lastTime tracked, dt = (now - lastTime) / 1000 (line 20)
 *   - dt passed to all update functions
 *   - Each state's update/render functions called per frame
 *   - No fixed timestep issues — animation speed is framerate-independent
 */

/**
 * TEST: INT-GS03 - Script loading order in index.html
 * STATUS: PASS with note
 *
 * Load order: sprites -> input -> map -> dialogue -> npc -> renderer ->
 *   starter -> battle -> encounters -> pokedex -> evolution -> pokecenter ->
 *   menu -> game
 *
 * Dependencies satisfied:
 *   - sprites loads before renderer (renderer uses Sprites) -> CORRECT
 *   - input loads before game (game reads Input) -> CORRECT
 *   - map loads before renderer (renderer uses Map) -> CORRECT
 *   - dialogue loads before npc/starter/pokecenter (all use Dialogue) -> CORRECT
 *   - npc loads before game (game calls NPC.update) -> CORRECT
 *   - battle loads before encounters (encounters triggers battle) -> CORRECT
 *   - game loads last (orchestrates everything) -> CORRECT
 *
 * NOTE: All modules use IIFE pattern with window assignments. No module
 *   bundler or import system. This means load order is critical and fragile —
 *   adding a new module requires manually inserting it in the right position
 *   in index.html. Works fine at current scale (14 scripts).
 */


// ============================================================
// STARTER SELECTION -> OVERWORLD TRANSITION
// ============================================================

/**
 * TEST: INT-SS01 - Starter selection creates game via backend
 * STATUS: PASS
 *
 * starter.js line ~380: After player confirms starter choice:
 *   1. POST /api/game/new -> creates game, gets game_id
 *   2. POST /api/game/{game_id}/choose-starter with pokemon_id
 *   3. Stores game_id in window.gameState.gameId
 *   4. Calls game.startOverworld() to transition state
 *
 * Backend game_service.py creates in-memory game dict with player,
 * party, position (default: pallet_town), inventory.
 *
 * Integration verified: frontend sends correct payload, backend creates
 * correct game state, game_id propagated for future API calls.
 */

/**
 * TEST: INT-SS02 - Starter Pokemon data consistency
 * STATUS: PASS with note
 *
 * Frontend starter.js defines 3 starters with sprites and display data.
 * Backend game route choose-starter creates a Pokemon entry in player's party.
 *
 * Frontend stores: { id, name, level, hp, maxHp } in window.gameState.party[0]
 * Backend stores: full Pokemon dict with stats, moves, types, etc.
 *
 * NOTE: Frontend party data is a simplified subset of backend data.
 *   After starter selection, frontend has minimal Pokemon data. The
 *   battle system uses its own Pokemon objects (battle.js lines 30-50)
 *   that are constructed from the party data. Stats like attack/defense
 *   are NOT synced from backend — battle uses simplified damage formula.
 *   This is acceptable for Sprint 1-2 scope but will cause issues when
 *   backend stat calculations matter (e.g., EVs, IVs, nature modifiers).
 */


// ============================================================
// OVERWORLD MOVEMENT & RENDERING
// ============================================================

/**
 * TEST: INT-OW01 - Player movement and input integration
 * STATUS: PASS
 *
 * Input flow:
 *   1. input.js captures keydown/keyup events -> keys object
 *   2. game.js update() reads Input.keys for arrow/WASD
 *   3. Movement applies with cooldown (moveTimer, line ~65)
 *   4. Player position updated in gameState.player.x/y
 *   5. renderer.js reads player position each frame for camera
 *
 * Grid-based movement: 1 tile per input with cooldown timer.
 * Cooldown prevents continuous rapid movement while key held.
 */

/**
 * TEST: INT-OW02 - Collision detection
 * STATUS: PASS
 *
 * map.js provides isWalkable(x, y) checking tile types.
 * Non-walkable tiles: WATER, TREE, WALL, HOUSE (building exteriors)
 * Walkable tiles: GRASS, PATH, TALL_GRASS, DOOR
 *
 * game.js checks isWalkable before applying movement.
 * NPC collision also checked via npc.js isOccupied(x, y).
 *
 * Both systems work together — player cannot walk through walls or NPCs.
 */

/**
 * TEST: INT-OW03 - Camera and viewport
 * STATUS: PASS
 *
 * renderer.js:
 *   - SCALE = 3 (16px tiles rendered at 48px)
 *   - VIEWPORT = 15x11 tiles visible
 *   - Camera centers on player, clamped to map bounds
 *   - Renders visible tile range only (performance optimization)
 *   - Player always rendered at screen center (or offset at map edges)
 *
 * Integration: renderer reads Map.tiles for terrain, NPC.npcs for
 *   NPC sprites, and gameState.player for player position. All data
 *   sources consistent.
 */

/**
 * TEST: INT-OW04 - Tile rendering consistency
 * STATUS: PASS
 *
 * sprites.js defines pixel art for all tile types used in map.js.
 * Every tile type in Map.TILES has a corresponding sprite function.
 * renderer.js calls Sprites.drawTile() which dispatches to correct sprite.
 *
 * No missing sprites for any map tile type.
 */


// ============================================================
// NPC SYSTEM
// ============================================================

/**
 * TEST: INT-NPC01 - NPC interaction flow
 * STATUS: PASS
 *
 * Full flow:
 *   1. Player faces NPC and presses action key (Z/Space/Enter)
 *   2. game.js checks NPC.getInteractTarget(player.x, player.y, facing)
 *   3. npc.js returns NPC if adjacent and player facing them
 *   4. game.js calls Dialogue.start(npc.dialogue)
 *   5. dialogue.js displays typewriter text, waits for action key
 *   6. On dialogue end, control returns to overworld
 *
 * Integration points all verified. Facing check uses direction
 * offsets correctly (up: y-1, down: y+1, left: x-1, right: x+1).
 */

/**
 * TEST: INT-NPC02 - NPC positions and map layout
 * STATUS: PASS
 *
 * npc.js defines 5 hardcoded NPCs with x,y positions.
 * All NPC positions are on walkable tiles in map.js layout.
 * No NPCs overlap with each other or with non-walkable tiles.
 *
 * NOTE: These NPCs are frontend-only (hardcoded in npc.js).
 *   Backend maps.json also defines NPCs with positions. Currently
 *   no connection between the two — frontend ignores backend NPC data.
 *   This is expected for Sprint 1-2 but will need reconciliation
 *   when Sprint 4 map system frontend integration happens.
 */


// ============================================================
// ENCOUNTER SYSTEM
// ============================================================

/**
 * TEST: INT-ENC01 - Encounter trigger flow
 * STATUS: PASS
 *
 * Full flow:
 *   1. Player moves onto TALL_GRASS tile (map.js tile type check)
 *   2. encounters.js checkEncounter() called
 *   3. 10% chance per step (Math.random() < 0.1)
 *   4. Random Pokemon selected from WILD_POKEMON pool
 *   5. Random level calculated (base level +/- 2)
 *   6. game.startBattle(wildPokemon) called
 *   7. game.js transitions state to 'battle'
 *
 * Integration: map tile type -> encounter check -> battle start
 *   all connected properly.
 */

/**
 * TEST: INT-ENC02 - Wild Pokemon pool
 * STATUS: PASS with note
 *
 * encounters.js WILD_POKEMON: Pidgey, Rattata, Caterpie, Weedle, Oddish
 * All at base level 3 with level variance of 2 (levels 1-5).
 *
 * NOTE: This is a single flat pool — no route differentiation.
 *   Backend maps.json defines encounter_zones with encounter_table_ids
 *   ("route_1", "route_2") but frontend doesn't use them. Every
 *   tall grass patch has the same Pokemon pool.
 *   -> Flagged in Sprint 4 pre-QA as MAP-D09 (medium severity)
 */

/**
 * TEST: INT-ENC03 - Encounter rate feels reasonable
 * STATUS: PASS
 *
 * 10% per step is standard for Pokemon games. With grid movement
 * and cooldown timer, player takes ~3-4 steps per second when
 * holding a direction key. Average ~2.5 seconds between encounters
 * in tall grass — slightly aggressive but within acceptable range.
 */


// ============================================================
// BATTLE SYSTEM
// ============================================================

/**
 * TEST: INT-BAT01 - Battle initialization from encounter
 * STATUS: PASS
 *
 * game.startBattle(wildPokemon):
 *   1. Sets state to 'battle'
 *   2. battle.js init() receives wild Pokemon data
 *   3. Player's party[0] used as active Pokemon
 *   4. Battle UI rendered: HP bars, Pokemon sprites, menu
 *
 * Pokemon data flows correctly from encounter -> game -> battle.
 */

/**
 * TEST: INT-BAT02 - Battle state machine
 * STATUS: PASS
 *
 * Battle states: intro -> menu -> fight_select -> animating -> text -> result
 *
 * Flow:
 *   - intro: Slide-in animation, "Wild X appeared!" text
 *   - menu: Fight / Bag / Pokemon / Run options
 *   - fight_select: Choose from 4 moves
 *   - animating: Attack animation plays
 *   - text: Damage/effectiveness text shown
 *   - result: Win/lose/run outcome -> back to overworld
 *
 * All state transitions verified. No dead-end states.
 */

/**
 * TEST: INT-BAT03 - Damage calculation
 * STATUS: PASS with note
 *
 * battle.js uses simplified damage formula:
 *   damage = (attackerLevel * 2 / 5 + 2) * movePower * atk/def / 50 + 2
 *   with type effectiveness multiplier and random factor (0.85-1.0)
 *
 * NOTE: This is a frontend-only calculation. Backend has its own
 *   battle service (not reviewed in Sprint 1-2 scope). Currently
 *   battles are entirely client-side — no backend API calls during
 *   battle. This means:
 *   - Battle outcomes not validated server-side
 *   - EXP gains calculated client-side
 *   - HP changes not synced to backend during battle
 *   - Theoretically exploitable (client can manipulate battle state)
 *   Acceptable for single-player offline play but would need
 *   server authority for any multiplayer or anti-cheat.
 */

/**
 * TEST: INT-BAT04 - Run from battle
 * STATUS: PASS
 *
 * Selecting "Run" from battle menu:
 *   - 100% success rate (no speed comparison)
 *   - Displays "Got away safely!" text
 *   - Transitions back to overworld
 *   - Player position preserved (same tile as before battle)
 *
 * Clean transition, no state leaks.
 */

/**
 * TEST: INT-BAT05 - Battle victory flow
 * STATUS: PASS with notes
 *
 * When wild Pokemon HP reaches 0:
 *   1. "Wild X fainted!" text displayed
 *   2. EXP calculated and awarded to player's Pokemon
 *   3. Level up checked and applied if threshold met
 *   4. "X gained Y EXP!" / "X grew to level Z!" text
 *   5. Return to overworld state
 *
 * NOTE 1: EXP is calculated client-side. Backend has a separate
 *   EXP formula in evolution_service.py (level^3 threshold).
 *   Frontend formula may differ — not verified for consistency.
 *
 * NOTE 2: After battle victory, player's Pokemon HP is NOT healed.
 *   Damage persists in gameState.party[0].hp. This is correct
 *   Pokemon behavior but means player needs healing (Pokemon Center
 *   or items) between battles.
 *
 * NOTE 3: Pokedex is NOT updated on battle victory. markCaught()
 *   is never called even though the function exists in pokedex.js.
 *   -> Already flagged in Sprint 3 QA-B report (INT-04, medium)
 */

/**
 * TEST: INT-BAT06 - Bag and Pokemon menu options
 * STATUS: KNOWN LIMITATION
 *
 * battle.js line 218: "Bag" and "Pokemon" options in battle menu
 * are not implemented. Selecting them shows "Not implemented yet" text.
 *
 * This means:
 *   - Cannot use items during battle (potions, pokeballs)
 *   - Cannot switch Pokemon during battle
 *   - Cannot catch wild Pokemon from battle UI
 *
 * Backend has full item use and catch mechanics (items_service.py)
 * but frontend battle UI doesn't call them.
 *
 * This is the single biggest integration gap from Sprint 1-2.
 * Severity: HIGH for gameplay, expected for Sprint 1-2 scope.
 */

/**
 * TEST: INT-BAT07 - Player defeat (party wipe)
 * STATUS: PASS with note
 *
 * When player's Pokemon HP reaches 0:
 *   1. "X fainted!" text displayed
 *   2. If party has other Pokemon with HP > 0, could switch (NOT IMPLEMENTED)
 *   3. With single Pokemon (Sprint 1-2 typical), battle ends
 *   4. "You blacked out!" text, returns to overworld
 *
 * NOTE: No penalty for losing — player returns to same position.
 *   Standard Pokemon behavior would return player to last Pokemon
 *   Center and deduct money. Not implemented (acceptable for Sprint 1-2).
 */


// ============================================================
// DIALOGUE SYSTEM
// ============================================================

/**
 * TEST: INT-DLG01 - Dialogue integration across modules
 * STATUS: PASS
 *
 * Dialogue.start() is called from:
 *   - npc.js: NPC interaction text
 *   - starter.js: Professor Oak's dialogue
 *   - pokecenter.js: Nurse Joy healing dialogue
 *   - battle.js: Battle text messages
 *   - encounters.js: "Wild X appeared!" text
 *
 * All callers use the same API correctly. Typewriter effect works
 * consistently. Action key advances/completes text in all contexts.
 */

/**
 * TEST: INT-DLG02 - Choice dialogue
 * STATUS: PASS
 *
 * Dialogue.startChoice() used for:
 *   - Starter selection confirmation ("Choose X?")
 *   - Nurse Joy healing ("Shall I heal your Pokemon?")
 *
 * Yes/No selection with up/down navigation. Callback receives
 * boolean result. Both callers handle yes/no correctly.
 */


// ============================================================
// MENU SYSTEM (Sprint 2)
// ============================================================

/**
 * TEST: INT-MNU01 - Pause menu access
 * STATUS: PASS
 *
 * Escape key in overworld opens pause menu (menu.js).
 * Menu options: Pokemon, Bag, Pokedex, Save, Close
 *
 * Input correctly captured — Escape only works in overworld state,
 * not during battle or other states.
 */

/**
 * TEST: INT-MNU02 - Pokemon submenu
 * STATUS: PASS with note
 *
 * Shows party Pokemon with name, level, HP bar.
 * Data read from window.gameState.party array.
 *
 * NOTE: menu.js syncParty() always sets HP to 20/20 (hardcoded).
 *   This means the Pokemon submenu always shows full HP regardless
 *   of actual battle damage. This is a display bug.
 *   -> Already flagged in Sprint 3 QA-B report (INT-05, medium)
 */

/**
 * TEST: INT-MNU03 - Bag submenu
 * STATUS: PASS with note
 *
 * Shows items organized in categories: potions, pokeballs, battle, key items.
 * Uses hardcoded mock data, NOT synced with backend inventory.
 *
 * Backend has full inventory system (items_service.py, player model
 * has inventory list). Frontend bag display is entirely mock.
 *   -> Already flagged in Sprint 3 QA-B (INT-06, low)
 */

/**
 * TEST: INT-MNU04 - Pokedex submenu
 * STATUS: PASS
 *
 * Opens pokedex.js UI from menu. Pokedex correctly shows
 * seen/caught/unseen status for all 20 entries.
 * Navigation and detail view work from menu context.
 * Back button returns to menu, not directly to overworld.
 */

/**
 * TEST: INT-MNU05 - Save function
 * STATUS: PASS
 *
 * Save option calls backend POST /api/game/{game_id}/save.
 * Backend game_service.py save_game() stores current state.
 * Load available via GET /api/game/{game_id}.
 *
 * Integration works: frontend sends game_id, backend persists.
 * NOTE: Backend storage is in-memory only — save lost on server restart.
 */


// ============================================================
// EVOLUTION SYSTEM (Sprint 2)
// ============================================================

/**
 * TEST: INT-EVO01 - Evolution trigger after level up
 * STATUS: PASS
 *
 * After battle victory with level up:
 *   1. battle.js checks if evolution is available
 *   2. If yes, game.startEvolution(pokemon, evolvedForm) called
 *   3. game.js transitions to 'evolution' state
 *   4. evolution.js plays animation sequence
 *   5. On completion, pokemon data updated in gameState.party
 *   6. Returns to overworld
 *
 * Full chain verified: battle -> level up -> evolution check -> animation -> update
 */

/**
 * TEST: INT-EVO02 - Evolution cancellation
 * STATUS: PASS
 *
 * During glow/morph phases, pressing B cancels evolution.
 * Pokemon stays unevolved, returns to overworld.
 * No data corruption — party data unchanged on cancel.
 */

/**
 * TEST: INT-EVO03 - Evolution data consistency
 * STATUS: PASS with note
 *
 * Frontend evolution check uses hardcoded evolution table in starter.js.
 * Backend evolution_service.py has its own evolution data with level thresholds.
 *
 * NOTE: Frontend and backend evolution data are independent.
 *   Frontend checks: Bulbasaur->Ivysaur@16, Charmander->Charmeleon@16, etc.
 *   Backend checks: similar thresholds but from Pokemon data files.
 *   Potential for desync if one is updated without the other.
 */


// ============================================================
// CROSS-CUTTING INTEGRATION ISSUES
// ============================================================

/**
 * TEST: INT-XC01 - Frontend-backend data synchronization
 * STATUS: ISSUE - Multiple sync gaps
 *
 * The frontend and backend maintain largely independent state:
 *
 * SYNCED:
 *   - Game creation (POST /api/game/new) -> game_id shared
 *   - Starter selection (POST /api/game/{id}/choose-starter)
 *   - Save/Load (POST/GET /api/game/{id}/save)
 *
 * NOT SYNCED:
 *   a. Battle outcomes — calculated client-side, not reported to backend
 *   b. EXP and level ups — client-side only
 *   c. HP changes — client-side only (except Pokemon Center heal is visual-only)
 *   d. Inventory — frontend uses mock data, backend has real inventory
 *   e. Pokedex — frontend tracks seen/caught locally, backend has pokedex API
 *   f. Player position — frontend tracks locally, backend has position in game state
 *   g. NPC data — frontend hardcoded, backend has NPC data in maps.json
 *
 * This is the fundamental architectural gap. The game works as a
 * single-player client-side experience that uses the backend only
 * for initial setup and save/load. All gameplay logic runs client-side.
 *
 * SEVERITY: Expected for Sprint 1-2 iterative development, but becomes
 *   critical as features like items, catching, gym battles require
 *   backend validation.
 */

/**
 * TEST: INT-XC02 - Error handling for API failures
 * STATUS: ISSUE - Minimal error handling
 *
 * Frontend API calls (starter.js, menu.js save):
 *   - Use fetch() with .then()/.catch()
 *   - Catch blocks typically console.log the error
 *   - No user-visible error messages
 *   - No retry logic
 *   - Game continues in potentially inconsistent state
 *
 * If backend is down:
 *   - Starter selection fails silently
 *   - Save fails silently
 *   - Game otherwise works (client-side logic doesn't need backend)
 *
 * SEVERITY: Low — game is playable offline after initial setup fails,
 *   but user gets no feedback about failures.
 */

/**
 * TEST: INT-XC03 - Canvas rendering performance
 * STATUS: PASS
 *
 * Rendering pipeline:
 *   1. Clear canvas
 *   2. Render visible tiles (15x11 viewport = 165 tiles max)
 *   3. Render NPCs in viewport
 *   4. Render player
 *   5. Render UI overlays (HP bars, text, menus)
 *
 * All sprites are programmatic (Canvas API draw calls, no image loading).
 * No sprite caching observed — sprites redrawn each frame.
 * At 165 tiles * ~10-20 draw calls per tile = ~2000-3000 draw calls/frame.
 *
 * Performance is fine at current scale. Could become an issue with
 * larger maps (Sprint 4 maps up to 25x25 = 625 tiles) or more complex
 * sprites. Canvas sprite caching (drawImage from offscreen canvas)
 * would help if needed.
 */

/**
 * TEST: INT-XC04 - Game state persistence across state transitions
 * STATUS: PASS
 *
 * window.gameState object survives all state transitions:
 *   - Overworld -> Battle: party data preserved, position preserved
 *   - Battle -> Overworld: HP changes persisted, EXP updated
 *   - Overworld -> Pokemon Center: position preserved for return
 *   - Any state -> Menu: game paused, state frozen
 *
 * No state leaks or data loss across transitions.
 */

/**
 * TEST: INT-XC05 - Input handling across states
 * STATUS: PASS
 *
 * Input routing:
 *   - Overworld: arrows move, Z interacts, Escape opens menu
 *   - Battle: arrows navigate menu, Z selects, B goes back
 *   - Dialogue: Z advances text, arrows for choices
 *   - Menu: arrows navigate, Z selects, Escape closes
 *   - Evolution: B cancels during specific phases
 *   - Pokemon Center: arrows move, Z interacts
 *
 * Each state handles its own input. No input conflicts between states.
 * game.js routes update() to correct state handler.
 */


// ============================================================
// BUG SUMMARY
// ============================================================

/**
 * Sprint 1-2 Integration Review Findings:
 *
 * PASS (working correctly):
 *   - Game state machine with proper transitions
 *   - Script loading order satisfies all dependencies
 *   - Starter selection -> backend game creation -> overworld
 *   - Player movement with collision detection
 *   - Camera and viewport rendering
 *   - NPC interaction with dialogue
 *   - Encounter triggering from tall grass
 *   - Battle system (fight and run)
 *   - Evolution animation with cancellation
 *   - Dialogue typewriter effect and choices
 *   - Pause menu navigation
 *   - Save/load via backend API
 *   - Canvas rendering performance
 *   - Game state persistence across transitions
 *   - Input handling isolation between states
 *
 * HIGH (major gameplay impact):
 *   1. [INT-BAT06] Battle Bag/Pokemon menu not implemented.
 *      Cannot use items or switch Pokemon during battle.
 *      Cannot catch wild Pokemon. Backend has these features
 *      but frontend doesn't connect to them.
 *
 * MEDIUM (notable gaps):
 *   2. [INT-XC01] Frontend-backend state sync — 7 categories
 *      of data not synced between client and server. Game
 *      effectively runs client-side after initial setup.
 *
 *   3. [INT-BAT05] Pokedex not updated on encounters or catches.
 *      markSeen()/markCaught() exist but never called.
 *      (Also flagged in Sprint 3 QA-B as INT-04)
 *
 *   4. [INT-MNU02] Menu Pokemon screen shows hardcoded 20/20 HP.
 *      (Also flagged in Sprint 3 QA-B as INT-05)
 *
 *   5. [INT-SS02] Frontend Pokemon data is simplified subset of
 *      backend data. Stats diverge over time as client-side
 *      calculations accumulate without backend validation.
 *
 *   6. [INT-EVO03] Evolution data maintained independently in
 *      frontend and backend. Potential for desync.
 *
 * LOW (minor issues):
 *   7. [INT-XC02] API errors handled silently — user gets no
 *      feedback when save fails or backend is unreachable.
 *
 *   8. [INT-NPC02] NPCs hardcoded in frontend, separate from
 *      backend map NPC data. Will need reconciliation in Sprint 4.
 *
 *   9. [INT-ENC02] Single encounter pool — no route differentiation.
 *      All tall grass has same Pokemon. Backend map data defines
 *      route-specific encounter tables but frontend doesn't use them.
 *
 * ARCHITECTURAL NOTE:
 *   The game is architecturally split between a fully functional
 *   client-side game engine and a backend that is largely unused
 *   during gameplay. The backend provides game creation, starter
 *   selection, and save/load, but all combat, movement, encounters,
 *   and progression happen client-side without server validation.
 *
 *   This architecture is fine for Sprint 1-2's scope (single-player
 *   prototype) but creates increasing technical debt as more features
 *   land on both sides. Sprint 4's map system integration will be the
 *   first major test of backend-frontend unification.
 *
 * OVERALL: Sprint 1-2 features work well together as a client-side
 *   game. The core loop (explore -> encounter -> battle -> level up ->
 *   evolve) is functional and enjoyable. Main risk is the growing gap
 *   between frontend and backend state, which will compound as new
 *   sprints add features to both sides.
 */
