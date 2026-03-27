/**
 * Sprint 4 QA-B: Routes, Towns & Integration Playthrough
 * QA Tester: qa-tester-2
 * Task: #43
 *
 * Reviews Sprint 4 frontend features:
 *   - Multiple routes & towns (map system, transitions, buildings)
 *   - Gym battles & badge system UI
 *   - Trainer encounters on routes
 *   - Integration playthrough: Pallet Town -> Pewter City -> Beat Brock
 *
 * Files reviewed:
 *   - game.js, map.js, maploader.js, routes.js, renderer.js
 *   - gym.js, badges.js, trainer.js, trainerencounter.js
 *   - encounters.js, npc.js, ledges.js, signs.js
 *   - pokecenter.js, menu.js, battle.js
 *   - index.html (script loading order)
 */


// ============================================================
// MAP SYSTEM & TRANSITIONS
// ============================================================

/**
 * TEST: MAP-FE01 - MapLoader.setCurrentMap missing export
 * STATUS: BUG (CRITICAL)
 *
 * game.js line 292 calls MapLoader.setCurrentMap(mapId) inside loadMap().
 * However, maploader.js does NOT export setCurrentMap. The export list
 * (lines 209-220) includes: registerMap, getCurrentMap, getCurrentMapId,
 * getMapName, checkExits, checkDoors, transitionTo, update,
 * renderTransition, isTransitioning.
 *
 * currentMapId IS updated internally during transitionTo() (line 144),
 * but loadMap() is also called directly at game.js line 112 after
 * starter selection (loadMap('pallet_town')), which would crash.
 *
 * This means:
 *   - TypeError on first map load after starter selection
 *   - Game crashes before the overworld even renders
 *   - ALL map transitions via loadMap() are broken
 *
 * BUG SEVERITY: CRITICAL — game is unplayable past starter selection.
 *
 * FIX: Add setCurrentMap to maploader.js exports, or change loadMap()
 *   to use MapLoader.transitionTo() instead.
 */

/**
 * TEST: MAP-FE02 - Map registration and data
 * STATUS: PASS
 *
 * routes.js registerAll() registers 5 maps with MapLoader:
 *   - pallet_town (30x25)
 *   - route_1 (20x40)
 *   - viridian_city (30x25)
 *   - route_2 (20x35)
 *   - pewter_city (30x25)
 *
 * Each map has: data (tile array), width, height, exits, doors, trainers.
 * All maps built procedurally with correct tile types.
 */

/**
 * TEST: MAP-FE03 - Map transition fade effect
 * STATUS: PASS (assuming MAP-FE01 is fixed)
 *
 * MapLoader.transitionTo() (line 132-149):
 *   - Sets transitioning=true, starts fadeAlpha at 0
 *   - Phase 1: Fade out (alpha 0->1)
 *   - Phase 2: Swap map (set currentMapId, load data)
 *   - Phase 3: Fade in (alpha 1->0)
 *   - Returns {transitioning, loaded, spawnX, spawnY, spawnDir}
 *
 * game.js updateOverworld() checks transResult and repositions player.
 * Encounters.reset() called on map change to clear cooldowns.
 */

/**
 * TEST: MAP-FE04 - Map name popup
 * STATUS: PASS
 *
 * MapLoader.renderTransition() displays map name in a dark bar at
 * top center of screen. Fades in, holds, fades out. Triggered on
 * every map transition. Uses getMapName() which returns display_name.
 */

/**
 * TEST: MAP-FE05 - Map exits (edge transitions)
 * STATUS: PASS
 *
 * MapLoader.checkExits(x, y) checks if player is at a map edge
 * exit tile. Supports both tile-specific exits and full-edge exits.
 *
 * Verified connections:
 *   Pallet Town north -> Route 1 (spawn at 10, 39)
 *   Route 1 south -> Pallet Town (spawn at 15, 0)
 *   Route 1 north -> Viridian City (spawn at 15, 24)
 *   Viridian City south -> Route 1 (spawn at 10, 0)
 *   Viridian City north -> Route 2 (spawn at 10, 34)
 *   Route 2 south -> Viridian City (spawn at 15, 0)
 *   Route 2 north -> Pewter City (spawn at 15, 24)
 *   Pewter City south -> Route 2 (spawn at 10, 0)
 *
 * All bidirectional. Spawn positions within map bounds.
 */

/**
 * TEST: MAP-FE06 - Building doors
 * STATUS: PASS with issues
 *
 * MapLoader.checkDoors(x, y) checks if player is on a DOOR tile.
 * game.js handles doors with special-case branching:
 *   - targetMap contains 'pokecenter' -> enterPokeCenter()
 *   - targetMap is 'pewter_gym' or 'viridian_gym' -> Gym.enter()
 *   - all other doors -> MapLoader.transitionTo()
 *
 * Issues:
 *   a. Pallet Town door at (5,6) points to 'pokecenter' but this
 *      is the Player's House, not a Pokemon Center (routes.js line 351).
 *   b. 'oak_lab' door at (12,16) references a map that is never
 *      registered with MapLoader. Entering would crash/softlock.
 *
 * See MAP-FE10 and MAP-FE11 for details.
 */

/**
 * TEST: MAP-FE07 - starter_town default mapId mismatch
 * STATUS: BUG (LOW)
 *
 * maploader.js line 8: currentMapId initialized to 'starter_town'.
 * No map named 'starter_town' is ever registered. If anything queries
 * MapLoader.getCurrentMapId() before the first map load (during starter
 * selection), it returns a non-existent map ID.
 *
 * BUG SEVERITY: Low — unlikely to cause issues since getCurrentMap()
 *   returns null for unknown IDs and callers check for null.
 */

/**
 * TEST: MAP-FE08 - Legacy buildStarterMap runs unnecessarily
 * STATUS: NOTE (code quality)
 *
 * map.js line 28: buildStarterMap() executes during module init,
 * creating a 30x25 map that is immediately overwritten by loadMap().
 * Wasted work at startup.
 */


// ============================================================
// NPC SYSTEM
// ============================================================

/**
 * TEST: NPC-FE01 - NPCs not map-specific
 * STATUS: BUG (HIGH)
 *
 * NPC.init() (npc.js lines 41-73) hardcodes 5 NPCs: Prof. Oak,
 * Nurse Joy, Shopkeeper, Youngster, Girl. Called once in Game.init().
 *
 * When player transitions to Route 1, Viridian City, or any other
 * map, these same 5 NPCs remain active at their original coordinates.
 * They render at wrong positions, block movement on wrong tiles, and
 * are interactable even on different maps.
 *
 * NPCs should be loaded per-map. MapLoader accepts an 'npcs' config
 * but nothing reads it to update the NPC module.
 *
 * BUG SEVERITY: HIGH — NPCs from Pallet Town appear on all maps.
 *   Viridian City, Pewter City, and routes have NO town NPCs of
 *   their own despite the backend maps.json defining them.
 */

/**
 * TEST: NPC-FE02 - NPC direction permanently changed after interaction
 * STATUS: BUG (LOW)
 *
 * npc.js line 203: NPC faces player on interaction. originalDir is
 * stored (line 84) but never used to reset. After talking to an NPC,
 * they face the player's direction forever.
 *
 * BUG SEVERITY: Low — cosmetic issue, NPCs don't face their
 *   original direction after dialogue ends.
 */


// ============================================================
// TRAINER ENCOUNTER SYSTEM
// ============================================================

/**
 * TEST: TRN-FE01 - Trainer line-of-sight detection
 * STATUS: PASS
 *
 * TrainerEncounter.checkLineOfSight() (lines 39-96):
 *   - Checks non-defeated trainers on current map
 *   - Validates player is within directional sight range
 *   - Checks no solid tiles block the line
 *   - Triggers encounter sequence: "!" -> walk -> dialogue -> battle
 *
 * Works correctly for cardinal directions.
 */

/**
 * TEST: TRN-FE02 - Trainer encounter sequence
 * STATUS: PASS
 *
 * Phases: idle -> exclamation (600ms) -> walk toward player -> dialogue -> battle
 * Smooth animation with trainer walking tile-by-tile.
 * Player movement locked during encounter.
 */

/**
 * TEST: TRN-FE03 - Trainers loaded per map
 * STATUS: PASS
 *
 * game.js line 296-298: loadMap() loads trainers from map config
 * via TrainerEncounter.loadTrainers(mapId, map.trainers).
 *
 * Route trainers defined in routes.js:
 *   Route 1: Youngster Joey (Rattata lv4), Lass Crissy (Pidgey lv5)
 *   Route 2: Bug Catcher Doug (Caterpie lv6 + Weedle lv6), Lass Robin (Oddish lv7)
 */

/**
 * TEST: TRN-FE04 - Trainer marked defeated BEFORE battle
 * STATUS: BUG (MEDIUM)
 *
 * game.js lines 138-139:
 *   startBattle(trainerResult.trainer.pokemon[0]);
 *   TrainerEncounter.defeatTrainer(MapLoader.getCurrentMapId(), trainerResult.trainer.name);
 *
 * defeatTrainer() is called immediately after startBattle(), BEFORE
 * the battle resolves. The trainer is marked defeated regardless of
 * whether the player wins or loses.
 *
 * BUG SEVERITY: Medium — player can lose to a trainer and never
 *   be challenged again. Should only mark defeated on player victory.
 */

/**
 * TEST: TRN-FE05 - Only first Pokemon used in trainer battles
 * STATUS: BUG (MEDIUM)
 *
 * game.js line 138: startBattle(trainerResult.trainer.pokemon[0])
 * Only sends pokemon[0] to battle. Bug Catcher Doug has 2 Pokemon
 * (Caterpie + Weedle) but only Caterpie is fought.
 *
 * Same issue in gym trainer battles (game.js line 89).
 *
 * BUG SEVERITY: Medium — multi-Pokemon trainer teams are defined
 *   but only the first Pokemon is used. Battles are shorter than
 *   intended and trainer difficulty is reduced.
 */

/**
 * TEST: TRN-FE06 - Defeated trainers persist only in session
 * STATUS: NOTE
 *
 * defeatedTrainers Set (trainerencounter.js line 8) is in-memory only.
 * Lost on page refresh. No save/load integration.
 * Acceptable for current scope but needs persistence later.
 */

/**
 * TEST: TRN-FE07 - Trainer sight blocked by NPCs
 * STATUS: BUG (LOW)
 *
 * checkLineOfSight() checks GameMap.isSolid() along the sight line
 * but does NOT check NPC.isSolid(). A trainer can "see through" an
 * NPC standing in the line of sight.
 *
 * BUG SEVERITY: Low — NPCs rarely stand between trainer and player
 *   path in current map layouts.
 */


// ============================================================
// GYM SYSTEM
// ============================================================

/**
 * TEST: GYM-FE01 - Pewter Gym (Brock) layout
 * STATUS: PASS
 *
 * gym.js buildPewterGym() creates a 13x15 tile map with:
 *   - Rock-themed colors (brown floor, stone walls)
 *   - Leader platform at top
 *   - Statues flanking the entrance
 *   - Puzzle/barrier tiles creating a path
 *   - 1 gym trainer: Camper Liam (Geodude lv7)
 *   - Brock at position (6, 2)
 *   - Door at bottom center
 *
 * Well-structured interior layout.
 */

/**
 * TEST: GYM-FE02 - Viridian Gym (Giovanni) layout
 * STATUS: PASS
 *
 * gym.js buildViridianGym() creates a 15x17 tile map with:
 *   - Ground-themed colors (darker tones)
 *   - More complex maze-like barrier layout
 *   - 2 gym trainers: Cooltrainer Samuel (Sandslash lv40),
 *     Cooltrainer Yuji (Dugtrio lv38)
 *   - Giovanni at position (7, 2)
 *   - Door at bottom center
 */

/**
 * TEST: GYM-FE03 - Gym leader battles
 * STATUS: PASS with notes
 *
 * Player walks to leader, presses action key. game.js lines 78-86:
 *   - Brock (Rock type) fights with Onix (lv14, 35 HP)
 *   - Giovanni (Ground type) fights with Rhydon (lv50, 105 HP)
 *
 * NOTE: Leader Pokemon are hardcoded in game.js via ternary on type
 *   string, not in gym.js. Fragile coupling — adding a third gym
 *   requires editing game.js.
 *
 * NOTE: Leaders only have 1 Pokemon each. Brock should canonically
 *   have Geodude + Onix. Giovanni should have a full team.
 */

/**
 * TEST: GYM-FE04 - Badge award flow is DISCONNECTED
 * STATUS: BUG (HIGH)
 *
 * The full intended flow:
 *   1. Player beats gym leader -> TrainerBattle shows victory dialogue
 *   2. TrainerBattle awards badge -> BadgeCase.earnBadge(index)
 *   3. Badge ceremony animation plays
 *
 * What actually happens:
 *   1. Player beats gym leader -> game.js calls startBattle() directly
 *      (line 86), which goes to Battle.start(), NOT TrainerBattle
 *   2. Battle ends -> updateBattle() syncs HP and returns to 'overworld'
 *      (line 371), but state was 'gym', not 'overworld' -> state mismatch
 *   3. No victory dialogue, no reward money, no badge earned
 *   4. BadgeCase.earnBadge() is NEVER called anywhere in the codebase
 *
 * The TrainerBattle module (trainer.js) has full VS intro animation,
 * victory dialogue, reward money, and badge ceremony rendering, but
 * game.js bypasses it entirely.
 *
 * BUG SEVERITY: HIGH — badges are never earned. The badge case UI
 *   exists but all 8 badges remain permanently unearned. The entire
 *   badge progression system is non-functional.
 *
 * FIX: game.js gym leader battle flow should use TrainerBattle module
 *   instead of calling startBattle() directly.
 */

/**
 * TEST: GYM-FE05 - Viridian Gym not locked
 * STATUS: BUG (MEDIUM)
 *
 * routes.js line 220 comments "Gym (top area -- locked until 7 badges)"
 * but no badge count check exists. Player can enter Viridian Gym
 * immediately and fight Giovanni at any time.
 *
 * game.js line 267-275 handles gym doors but has no lock check.
 *
 * BUG SEVERITY: Medium — player can fight Giovanni (lv50 Rhydon)
 *   at the start of the game. Should require 7 badges per comment.
 */

/**
 * TEST: GYM-FE06 - Gym trainers can be re-challenged
 * STATUS: BUG (LOW)
 *
 * Unlike overworld trainers (TrainerEncounter.defeatTrainer()),
 * gym trainers in gym.js have no defeated state tracking. Player
 * can battle the same gym trainer every time they enter the gym.
 *
 * BUG SEVERITY: Low — minor inconsistency, gym trainers should
 *   only fight once per visit.
 */

/**
 * TEST: GYM-FE07 - Gym leader re-challengeable
 * STATUS: BUG (LOW)
 *
 * No check for whether the player already earned the gym's badge.
 * Player can fight Brock/Giovanni repeatedly. Since badges are
 * never actually earned (GYM-FE04), this is moot, but would be
 * a problem once badges work.
 */

/**
 * TEST: GYM-FE08 - Badge case UI
 * STATUS: PASS (as standalone UI)
 *
 * badges.js implements a full badge case overlay:
 *   - 4x2 grid displaying all 8 Kanto badges
 *   - Gold/silver styling for earned vs grayed for unearned
 *   - Shine animation on earned badges
 *   - Badge name, gym name, leader name display
 *   - Navigation and selection
 *
 * The UI works correctly — it just has no way to earn badges.
 */

/**
 * TEST: GYM-FE09 - Badge case inaccessible from game
 * STATUS: BUG (MEDIUM)
 *
 * BadgeCase.open() is exported but never called from game.js or
 * PauseMenu. The badge case cannot be opened during gameplay.
 *
 * BUG SEVERITY: Medium — badge case exists but is inaccessible.
 *   Should be accessible from the pause menu.
 */


// ============================================================
// BATTLE SYSTEM (Sprint 4 integration)
// ============================================================

/**
 * TEST: BAT-FE01 - No type effectiveness in damage
 * STATUS: BUG (MEDIUM)
 *
 * battle.js calculateDamage() (line 362) uses only power and level.
 * No type matchup system (STAB, super effective, not very effective,
 * immunity). Every move deals neutral damage regardless of types.
 *
 * This means:
 *   - Water Gun vs Onix does normal damage (should be 4x effective)
 *   - Tackle vs Ghost would hit (should be immune)
 *   - Fighting a Rock-type gym leader has no strategic depth
 *
 * BUG SEVERITY: Medium — type matchups are core to Pokemon gameplay.
 */

/**
 * TEST: BAT-FE02 - Enemy always uses Tackle/Scratch
 * STATUS: BUG (MEDIUM)
 *
 * battle.js lines 320-324: Enemy move selection is hardcoded to
 * randomly pick "Tackle" or "Scratch" (both Normal, power 40).
 *
 * Brock's Onix uses Tackle/Scratch instead of Rock Throw/Bind.
 * Giovanni's Rhydon uses Tackle/Scratch instead of Earthquake/Horn Drill.
 *
 * BUG SEVERITY: Medium — gym leaders and trainers feel generic.
 *   Enemy Pokemon should use their own typed moves.
 */

/**
 * TEST: BAT-FE03 - No EXP gain after battle victory
 * STATUS: BUG (MEDIUM)
 *
 * game.js updateBattle() (lines 362-374): On battle completion,
 * only syncs HP back to party. No EXP awarded, no level-up check,
 * no evolution trigger. The EXP bar in battle UI is decorative.
 *
 * Backend has full EXP/level-up system (evolution_service.py) but
 * frontend doesn't call it after battles.
 *
 * BUG SEVERITY: Medium — player Pokemon never gains EXP or levels
 *   up during normal gameplay.
 */

/**
 * TEST: BAT-FE04 - No attack/defense stats in damage formula
 * STATUS: BUG (LOW)
 *
 * battle.js calculateDamage() uses only power and level, ignoring
 * attack/defense stats entirely. An Onix with 160 Defense takes the
 * same damage as a Caterpie with 35 Defense.
 *
 * BUG SEVERITY: Low — simplification, but undermines stat-based
 *   Pokemon gameplay.
 */


// ============================================================
// ENCOUNTER SYSTEM (Route integration)
// ============================================================

/**
 * TEST: ENC-FE01 - Same encounter pool on all maps
 * STATUS: BUG (MEDIUM)
 *
 * encounters.js has a single WILD_POKEMON array (lines 25-31):
 * Pidgey, Rattata, Caterpie, Weedle, Oddish — all at level 3 +/- 2.
 *
 * Route 1 and Route 2 have identical encounters. Pallet Town's tall
 * grass also has the same Pokemon. No route differentiation.
 *
 * Backend has encounter tables defined for route_1 and route_2
 * (Task #48 completed) but frontend doesn't use them.
 *
 * BUG SEVERITY: Medium — undermines exploration progression.
 */

/**
 * TEST: ENC-FE02 - Encounter rate and cooldown
 * STATUS: PASS
 *
 * 10% per tile step in tall grass. 3-second cooldown between
 * encounters. rate() called only on tile change. Reasonable pacing.
 */

/**
 * TEST: ENC-FE03 - Pokedex marked on encounter
 * STATUS: PASS
 *
 * encounters.js line 135-136: Pokedex.markSeen() called when
 * encounter triggers with the species entry. Working correctly.
 *
 * (This was previously flagged as missing in Sprint 3 QA but has
 * been fixed.)
 */

/**
 * TEST: ENC-FE04 - STEP_THRESHOLD unused
 * STATUS: NOTE (dead code)
 *
 * encounters.js line 6: STEP_THRESHOLD = 8 declared but never used.
 * Line 9: stepAccumulator also unused. Encounter works on tile change
 * detection instead.
 */


// ============================================================
// LEDGE SYSTEM
// ============================================================

/**
 * TEST: LED-FE01 - Ledge system is dead code
 * STATUS: BUG (MEDIUM)
 *
 * ledges.js is fully implemented: parabolic jump arc, dust particles,
 * one-way south jumping, collision checks.
 *
 * But NO map in routes.js registers ledge data. Route 1 places ROCK
 * tiles with comment "Ledges (rocks player can jump down from)" but
 * they're just regular solid ROCK tiles, not configured as ledges.
 *
 * Ledges.isLedge() always returns false. tryJump() never triggers.
 *
 * BUG SEVERITY: Medium — feature built but not wired up. Ledges
 *   were likely intended for Route 1 and Route 2.
 */


// ============================================================
// SIGNS SYSTEM
// ============================================================

/**
 * TEST: SGN-FE01 - Signs present and readable
 * STATUS: PASS (assuming rendering works)
 *
 * signs.js defines per-map signs with positions and text.
 * renderer.js renders sign posts at correct positions.
 * Interaction checks player facing direction.
 *
 * Signs provide flavor text and directions ("Route 1 - Pallet Town
 * to Viridian City", "Pewter City - Home of the Rock Gym", etc.)
 */


// ============================================================
// POKEMON CENTER (multi-town integration)
// ============================================================

/**
 * TEST: PC-FE01 - Pokemon Center works across towns
 * STATUS: PASS with note
 *
 * pokecenter.js is a singleton — same 15x12 layout, same Nurse Joy
 * healing flow, same tiles for all Pokemon Centers.
 *
 * NOTE: No city differentiation. The banner always says "Pokemon Center"
 *   regardless of whether you're in Viridian or Pewter. Interior is
 *   identical. This is acceptable — the original games had similar
 *   Pokemon Center interiors.
 */

/**
 * TEST: PC-FE02 - Pallet Town "Player House" opens Pokemon Center
 * STATUS: BUG (MEDIUM)
 *
 * routes.js line 351: Door at Pallet Town (5,6) has targetMap: 'pokecenter'.
 * This coordinate is the Player's House, not a Pokemon Center building.
 * Pallet Town doesn't have a Pokemon Center.
 *
 * Entering the player's house shows the Pokemon Center interior with
 * Nurse Joy, which is incorrect.
 *
 * BUG SEVERITY: Medium — player's house should be a different interior
 *   (Mom, bed, TV, etc.) or at least not a Pokemon Center.
 */


// ============================================================
// MISSING MAP: OAK'S LAB
// ============================================================

/**
 * TEST: MAP-FE10 - Oak's Lab door references unregistered map
 * STATUS: BUG (HIGH)
 *
 * routes.js line 352: Pallet Town door at (12,16) targets 'oak_lab'.
 * But registerAll() never registers a map named 'oak_lab'.
 *
 * If the player steps on this door:
 *   - MapLoader.transitionTo('oak_lab') starts transition
 *   - currentMapId set to 'oak_lab'
 *   - getCurrentMap() returns null
 *   - loadMap() returns early at line 294 (game.js)
 *   - Player is stuck with no map data, effectively softlocked
 *
 * BUG SEVERITY: HIGH — stepping on Oak's Lab door softlocks the game.
 *   The door tile exists and is walkable, so the player will naturally
 *   walk into it.
 */


// ============================================================
// CAMERA & RENDERING
// ============================================================

/**
 * TEST: RND-FE01 - Camera on different map sizes
 * STATUS: PASS with note
 *
 * renderer.js camera clamp: max(0, min(camX, mapW*TILE - viewportW))
 *
 * All Sprint 4 maps are larger than the viewport (minimum 20x25 vs
 * viewport 15x11), so clamping works correctly.
 *
 * NOTE: If a map smaller than 15x11 tiles were ever added, the camera
 *   would pin to top-left corner. Not an issue with current maps.
 */

/**
 * TEST: RND-FE02 - Rendering pipeline
 * STATUS: PASS
 *
 * Draw order: tiles -> NPCs -> signs -> trainers -> player -> dust ->
 *   encounter overlay -> map transition overlay
 *
 * Correct z-ordering. Overdraw buffer of 1 tile on edges prevents
 * gaps during scrolling.
 */


// ============================================================
// SCRIPT LOADING ORDER
// ============================================================

/**
 * TEST: SCR-FE01 - index.html script order
 * STATUS: PASS
 *
 * New Sprint 4 scripts properly ordered:
 *   - maploader.js before routes.js (routes registers with MapLoader)
 *   - routes.js before game.js (game loads maps from Routes)
 *   - signs.js before renderer.js (renderer draws signs)
 *   - trainerencounter.js before game.js (game checks trainer encounters)
 *   - ledges.js before game.js (game checks ledge jumps)
 *   - gym.js before game.js (game enters gyms)
 *   - badges.js and trainer.js loaded (even if currently unused)
 *
 * All dependency chains satisfied.
 */


// ============================================================
// INTEGRATION PLAYTHROUGH
// ============================================================

/**
 * TEST: PLAY-01 - Start in Pallet Town
 * STATUS: BLOCKED by MAP-FE01
 *
 * After starter selection, game.js calls loadMap('pallet_town')
 * which calls MapLoader.setCurrentMap() -> CRASH (TypeError).
 *
 * The entire playthrough is blocked by the missing setCurrentMap
 * export. All subsequent playthrough tests assume this is fixed.
 */

/**
 * TEST: PLAY-02 - Walk around Pallet Town
 * STATUS: CONDITIONAL PASS (assuming MAP-FE01 fixed)
 *
 * 30x25 map with grass, paths, houses, pond.
 * Player spawns at center. Movement works with collision.
 * 5 NPCs present from NPC.init() with dialogue.
 *
 * Issues: Player House door opens Pokemon Center (PC-FE02).
 *   Oak's Lab door softlocks (MAP-FE10).
 */

/**
 * TEST: PLAY-03 - Route 1: Pallet Town -> Viridian City
 * STATUS: CONDITIONAL PASS
 *
 * North exit transitions to Route 1. Map name popup shows.
 * Two trainers on route (Joey, Crissy) with line-of-sight.
 * Tall grass encounters work (same pool as everywhere).
 *
 * Issues: 5 Pallet Town NPCs still visible (NPC-FE01).
 *   Trainers defeated before battle resolves (TRN-FE04).
 *   Only first Pokemon fought (TRN-FE05).
 */

/**
 * TEST: PLAY-04 - Viridian City
 * STATUS: CONDITIONAL PASS
 *
 * Arrive from Route 1 south. Map name popup shows.
 * Pokemon Center door works -> enters Pokemon Center interior.
 * Healing flow works (Nurse Joy dialogue, animation).
 *
 * Issues: No Viridian City NPCs (NPC-FE01, only Pallet NPCs).
 *   Viridian Gym accessible despite needing 7 badges (GYM-FE05).
 */

/**
 * TEST: PLAY-05 - Route 2: Viridian City -> Pewter City
 * STATUS: CONDITIONAL PASS
 *
 * North exit transitions to Route 2. Slightly harder trainers
 * (Doug, Robin). Same encounter pool as Route 1.
 * Ledges should be present but aren't (LED-FE01).
 */

/**
 * TEST: PLAY-06 - Pewter City and Brock
 * STATUS: CONDITIONAL PASS
 *
 * Arrive from Route 2 south. Pewter Pokemon Center works.
 * Pewter Gym door opens gym interior. Gym trainer Camper Liam
 * challenges (Geodude lv7). Brock challenges (Onix lv14).
 *
 * Issues:
 *   - No badge earned after beating Brock (GYM-FE04)
 *   - No EXP gained from any battles (BAT-FE03)
 *   - No type effectiveness (BAT-FE01)
 *   - Brock's Onix uses Tackle/Scratch (BAT-FE02)
 *   - Can re-fight Brock immediately (GYM-FE07)
 */

/**
 * TEST: PLAY-07 - Save/load preserves map position
 * STATUS: PARTIAL
 *
 * Save menu calls backend POST /api/game/{id}/save.
 * Backend saves player position including map_id, x, y.
 * However, frontend position is client-side only — the save
 * captures the backend's last-known position, which may diverge
 * from where the player actually is on screen.
 *
 * Defeated trainers are NOT saved (session-only Set).
 */


// ============================================================
// BUG SUMMARY
// ============================================================

/**
 * Sprint 4 QA-B: Routes, Towns & Integration Playthrough
 *
 * CRITICAL (game-breaking):
 *   1. [MAP-FE01] MapLoader.setCurrentMap() called but not exported.
 *      Game crashes after starter selection. ALL map loading broken.
 *
 * HIGH (major feature gaps):
 *   2. [GYM-FE04] Badge award flow completely disconnected. game.js
 *      bypasses TrainerBattle module, calls Battle.start() directly.
 *      Badges never earned, no victory dialogue, no reward money.
 *      TrainerBattle module is dead code in practice.
 *
 *   3. [NPC-FE01] NPCs hardcoded for Pallet Town only, persist on
 *      all maps. Other towns have no NPCs. Wrong NPCs render on
 *      wrong maps.
 *
 *   4. [MAP-FE10] Oak's Lab door targets unregistered 'oak_lab' map.
 *      Stepping on door softlocks the game.
 *
 * MEDIUM (significant issues):
 *   5. [TRN-FE04] Trainer marked defeated before battle resolves.
 *      Losing to trainer still marks them defeated.
 *
 *   6. [TRN-FE05] Only first Pokemon used in multi-Pokemon trainer
 *      battles. Teams truncated to 1 Pokemon.
 *
 *   7. [BAT-FE01] No type effectiveness in damage calculation.
 *      All moves deal neutral damage regardless of types.
 *
 *   8. [BAT-FE02] Enemy always uses Tackle/Scratch. Gym leaders
 *      and trainers don't use their typed moves.
 *
 *   9. [BAT-FE03] No EXP gain after battle victory. Player Pokemon
 *      never levels up during gameplay.
 *
 *  10. [ENC-FE01] Same encounter pool on all routes. No route
 *      differentiation despite backend having encounter tables.
 *
 *  11. [LED-FE01] Ledge system implemented but not wired up.
 *      No map registers ledge data.
 *
 *  12. [GYM-FE05] Viridian Gym not locked — player can fight
 *      Giovanni immediately despite "7 badges required" intent.
 *
 *  13. [GYM-FE09] Badge case inaccessible from pause menu.
 *
 *  14. [PC-FE02] Pallet Town Player's House opens Pokemon Center
 *      instead of house interior.
 *
 * LOW (minor issues):
 *  15. [MAP-FE07] Default currentMapId is 'starter_town' (non-existent).
 *  16. [NPC-FE02] NPCs don't reset facing direction after interaction.
 *  17. [TRN-FE07] Trainer sight not blocked by NPCs.
 *  18. [BAT-FE04] No attack/defense stats in damage formula.
 *  19. [GYM-FE06] Gym trainers can be re-challenged infinitely.
 *  20. [GYM-FE07] Gym leader re-challengeable (no badge check).
 *
 * CODE QUALITY:
 *  21. [MAP-FE08] Legacy buildStarterMap() runs unnecessarily.
 *  22. [ENC-FE04] STEP_THRESHOLD and stepAccumulator unused.
 *  23. Duplicate buildHouse() in map.js and routes.js.
 *  24. Gym leader Pokemon hardcoded in game.js, not gym.js.
 *
 * PREVIOUSLY FIXED (verified):
 *  25. [#63] Caught Pokemon now added to party/PC + Pokedex updated.
 *  26. [#62] Negative quantity exploit fixed with Field(gt=0).
 *  27. [ENC-FE03] Pokedex.markSeen() now called on encounters.
 *
 * OVERALL VERDICT: Sprint 4 has built a solid multi-map engine
 *   (MapLoader, routes, signs, trainer encounters, gyms, badge UI)
 *   but several critical integration gaps prevent the intended
 *   gameplay experience:
 *
 *   The CRITICAL setCurrentMap bug must be fixed first — the game
 *   literally cannot load maps without it. After that, the HIGH
 *   issues (badge flow disconnection, NPC persistence, Oak's Lab
 *   softlock) need attention before the Sprint 4 features can be
 *   considered functional.
 *
 *   The battle system needs type effectiveness, proper enemy moves,
 *   and EXP gain to make gym battles meaningful. The encounter
 *   system needs route-specific tables.
 *
 *   RECOMMENDATION: Fix MAP-FE01 and MAP-FE10 immediately (crashes).
 *   Then wire GYM-FE04 (badges) and NPC-FE01 (per-map NPCs) as
 *   highest priority. Battle improvements (BAT-FE01/02/03) can be
 *   phased in.
 */
