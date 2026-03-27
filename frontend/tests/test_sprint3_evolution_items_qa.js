/**
 * Sprint 3 QA-A: Evolution & Items Review
 * QA Tester: qa-tester-2 (assisting qa-tester to clear QA gate)
 * Task: #22 — Sprint 3 QA-A: Review evolution & items
 *
 * Reviews:
 *   - Frontend: evolution.js, menu.js (bag/inventory)
 *   - Backend: evolution_service.py, evolution routes, item_service.py,
 *     item routes, item models
 *   - Cross-cutting: frontend-backend integration for both systems
 */


// ============================================================
// POKEMON EVOLUTION — FRONTEND (evolution.js)
// ============================================================

/**
 * TEST: EVO-F01 - Evolution animation phases
 * STATUS: PASS
 *
 * 6-phase animation sequence:
 *   Phase      | Duration | Visual
 *   -----------|----------|-----------------------------------
 *   start      | 2000ms   | Pre-evo form, "What? X is evolving!"
 *   glow       | 2500ms   | Pulsing white glow, sparkle particles
 *   morph      | 1500ms   | Cross-fade pre->post, 8 light rays
 *   flash      | 500ms    | White screen flash, fades out
 *   reveal     | 2000ms   | Evolved form, congratulations text
 *   done       | 500ms    | Fires onComplete callback
 *
 * Total animation: 9 seconds. Well-paced and visually engaging.
 */

/**
 * TEST: EVO-F02 - Evolution cancellation
 * STATUS: PASS
 *
 * B key during glow or morph phases cancels evolution (lines 48-54).
 * On cancel:
 *   - Jumps to reveal phase showing PRE-evolution form
 *   - Text: "[name] stopped evolving."
 *   - Callback fires with cancelled=true
 *   - Pokemon stays unevolved
 *
 * Cannot cancel during start, flash, reveal, or done phases.
 * This matches standard Pokemon behavior.
 */

/**
 * TEST: EVO-F03 - Reveal phase skip
 * STATUS: PASS
 *
 * During reveal phase, after 500ms delay, pressing action key
 * (Z/Space/Enter) skips remaining reveal time and advances to done.
 * Prevents player from being stuck watching the reveal animation.
 */

/**
 * TEST: EVO-F04 - Sparkle and light ray effects
 * STATUS: PASS
 *
 * Sparkle particles: random position, velocity, size, lifetime, color.
 * Spawned during glow phase. Light rays spawned during morph phase (8 rays).
 * Both use delta-time for smooth animation regardless of framerate.
 */

/**
 * TEST: EVO-F05 - drawEvoSprite null safety
 * STATUS: PASS with note
 *
 * drawEvoSprite() (line 258) has null check: `if (!pokemon) return`.
 * However, start() (line 26) does NOT validate that pre/post params
 * are non-null. If start() is called with null pokemon data, it will
 * crash on first render when accessing prePokemon.name.
 *
 * BUG SEVERITY: Low — unlikely in practice since game.js validates
 *   before calling, but no defensive check at the API boundary.
 */


// ============================================================
// POKEMON EVOLUTION — BACKEND (evolution_service.py, routes)
// ============================================================

/**
 * TEST: EVO-B01 - EXP calculation formula
 * STATUS: PASS
 *
 * EXP threshold: level^3 (medium-fast growth rate, line 24)
 *   Level 5 = 125 EXP, Level 10 = 1000 EXP, Level 16 = 4096 EXP
 *
 * EXP gained per battle (line 131):
 *   max(1, (defeated_species.base_exp * defeated_level) // 7)
 *
 * Integer division ensures minimum 1 EXP per battle.
 * Formula is a reasonable simplification of Gen I-IV formula.
 */

/**
 * TEST: EVO-B02 - Evolution trigger at correct levels
 * STATUS: PASS
 *
 * check_evolution() (line 41): current_level >= species.evolution.level
 * Uses >= comparison so level-skipping still triggers evolution.
 *
 * Evolution checked in award_exp() only when level-up occurs (line 155-157).
 * Multi-level-up case handled correctly: if Pokemon jumps from 14 to 18
 * and evolution is at 16, the >= check catches it.
 */

/**
 * TEST: EVO-B03 - Stats recalculation after evolution
 * STATUS: PASS with note
 *
 * evolve_pokemon() (lines 67-76): Recalculates all stats using new
 * species base stats via _calc_stat() with IV=15.
 *
 * NOTE: IVs are hardcoded to 15 for all Pokemon (mid-range approximation).
 *   Every Pokemon of the same species/level has identical stats.
 *   If IVs are added later, all existing Pokemon stats would change.
 *   -> Also flagged in Task #47 (Bug: base stats vs IV-calculated)
 */

/**
 * TEST: EVO-B04 - Move learning on level-up
 * STATUS: PASS
 *
 * get_pending_moves() (lines 92-107): Returns moves learnable at
 * exact current level that are not already known.
 *
 * award_exp() includes pending moves in response for frontend to
 * offer move-learning UI.
 */

/**
 * TEST: EVO-B05 - Move replacement (4-move limit)
 * STATUS: PASS
 *
 * /learn-move endpoint (routes lines 71-109):
 *   - < 4 moves: appends new move
 *   - 4 moves + forget_move_index: replaces specified move
 *   - 4 moves + no forget index: returns 400 error
 *
 * Correctly enforces the 4-move limit.
 */

/**
 * TEST: EVO-B06 - Evolution replaces entire moveset
 * STATUS: BUG (MEDIUM)
 *
 * evolve_pokemon() (line 78) calls _generate_moves_for_level()
 * which creates a fresh moveset for the evolved species at current level.
 * This DISCARDS any custom moves the player may have taught via TMs
 * or move tutors.
 *
 * The /evolve route (line 49) writes result.new_moves directly to
 * the Pokemon, completing the moveset replacement.
 *
 * Standard Pokemon behavior preserves the existing moveset on evolution
 * and only adds new moves learned at the evolution level.
 *
 * BUG SEVERITY: Medium — player loses custom move choices on evolution.
 */

/**
 * TEST: EVO-B07 - current_hp not updated on level-up
 * STATUS: BUG (MEDIUM)
 *
 * award_exp() (lines 170-178): When stats are recalculated on level-up,
 * max HP changes but current_hp is NOT updated. In standard Pokemon games,
 * current HP increases by the same delta as max HP on level-up.
 *
 * Example: Pokemon has 30/35 HP. Levels up, max HP becomes 40.
 *   Expected: 35/40 HP (current HP gains +5 delta)
 *   Actual: 30/40 HP (current HP unchanged)
 *
 * Similarly, /evolve endpoint updates stats but not current_hp.
 *
 * BUG SEVERITY: Medium — Pokemon appears damaged after leveling up
 *   or evolving, even though it should gain the HP difference.
 */

/**
 * TEST: EVO-B08 - No Pokedex update on evolution
 * STATUS: BUG (MEDIUM)
 *
 * The /evolve endpoint updates id, name, stats, and moves (lines 46-49)
 * but does NOT register the new evolved species in the Pokedex system.
 *
 * Backend has full Pokedex tracking (pokedex_service.py) but evolution
 * does not call mark_caught() or mark_seen() for the evolved form.
 *
 * BUG SEVERITY: Medium — evolved Pokemon not recorded in Pokedex.
 */

/**
 * TEST: EVO-B09 - award_exp redundant get_species calls
 * STATUS: NOTE (code quality)
 *
 * award_exp() lines 146 and 167 both call get_species(pokemon["id"])
 * within the same if-block. The result could be stored once.
 *
 * No functional impact, but wasteful.
 */


// ============================================================
// ITEMS & INVENTORY — FRONTEND (menu.js bag screen)
// ============================================================

/**
 * TEST: ITEM-F01 - Bag screen layout and navigation
 * STATUS: PASS
 *
 * Bag screen has 4 category tabs: Potions, Balls, Battle, Key Items
 * Tab switching with left/right arrows. Item selection with up/down.
 * Action submenu on Z/Space: Use, Give, Toss, Cancel.
 *
 * Navigation is smooth and intuitive.
 */

/**
 * TEST: ITEM-F02 - Frontend inventory is hardcoded mock data
 * STATUS: BUG (MEDIUM)
 *
 * menu.js lines 11-23: Inventory is a hardcoded object:
 *   - Potion x3, Super Potion x1, Poke Ball x5, Antidote x2
 *
 * Comment says "will be synced with backend" but no sync code exists.
 * Backend has full inventory API (GET /api/inventory/{game_id}) but
 * frontend never calls it.
 *
 * Player cannot see items bought from shops or received from gameplay.
 *
 * BUG SEVERITY: Medium — inventory display is entirely fake.
 *   Already flagged in Sprint 3 QA-B (INT-06) and Sprint 1-2
 *   integration review (INT-XC01).
 */

/**
 * TEST: ITEM-F03 - Use and Give actions are no-ops
 * STATUS: BUG (MEDIUM)
 *
 * menu.js line 128: "Use" action has placeholder comment, does nothing.
 * menu.js line 128: "Give" action also does nothing.
 * Both close the action submenu, giving the impression something happened.
 *
 * Player selects "Use Potion" -> menu closes -> nothing happens.
 *
 * BUG SEVERITY: Medium — core item functionality not implemented
 *   in frontend. Backend has full use_item() service but frontend
 *   doesn't call it.
 */

/**
 * TEST: ITEM-F04 - Toss action works
 * STATUS: PASS with note
 *
 * menu.js lines 129-134: Toss decrements quantity by 1, removes item
 * from array if quantity reaches 0, adjusts bagIndex.
 *
 * NOTE: Only tosses 1 at a time (no quantity prompt). Backend
 *   toss_item() supports arbitrary quantities.
 */

/**
 * TEST: ITEM-F05 - Party screen HP display
 * STATUS: BUG (MEDIUM)
 *
 * syncParty() (lines 60-73): Only reads Game.player.starter and
 * hardcodes level=5, hp=20, maxHp=20 for all Pokemon.
 *
 * After battles where Pokemon take damage, the party screen still
 * shows 20/20 HP. After level-ups, still shows level 5.
 *
 * BUG SEVERITY: Medium — party screen is misleading.
 *   Already flagged in Sprint 3 QA-B (INT-05).
 */


// ============================================================
// ITEMS & INVENTORY — BACKEND (item_service.py, routes, models)
// ============================================================

/**
 * TEST: ITEM-B01 - Item definitions and effects
 * STATUS: PASS
 *
 * 9 items defined in data/items.json:
 *   ID | Name           | Category    | Buy  | Sell | Effect
 *   ---|----------------|-------------|------|------|------------------
 *   1  | Potion         | potion      | 300  | 150  | heal_hp, 20
 *   2  | Super Potion   | potion      | 700  | 350  | heal_hp, 50
 *   3  | Antidote       | status_heal | 100  | 50   | cure poison
 *   4  | Paralyze Heal  | status_heal | 200  | 100  | cure paralysis
 *   5  | Full Heal      | status_heal | 600  | 300  | cure all
 *   6  | Revive         | potion      | 1500 | 750  | revive, 50% HP
 *   7  | Pokeball       | pokeball    | 200  | 100  | catch, 1.0x
 *   8  | Great Ball     | pokeball    | 600  | 300  | catch, 1.5x
 *   9  | Ultra Ball     | pokeball    | 1200 | 600  | catch, 2.0x
 *
 * All sell prices are exactly 50% of buy price (correct).
 * Item effects match standard Pokemon values.
 */

/**
 * TEST: ITEM-B02 - Potion healing amounts
 * STATUS: PASS
 *
 * use_item() handles "heal_hp" effect:
 *   - Potion: restores 20 HP, capped at max HP
 *   - Super Potion: restores 50 HP, capped at max HP
 *   - Cannot use on fainted Pokemon (current_hp == 0)
 *   - Cannot use on full HP Pokemon
 *   - Correctly decrements inventory quantity after use
 */

/**
 * TEST: ITEM-B03 - Status heal items
 * STATUS: PASS
 *
 * use_item() handles "cure_status" effect:
 *   - Antidote: cures "poison" status
 *   - Paralyze Heal: cures "paralysis" status
 *   - Full Heal: cures any status (status="all")
 *   - Returns error if Pokemon has no status condition
 */

/**
 * TEST: ITEM-B04 - Revive mechanics
 * STATUS: PASS
 *
 * use_item() handles "revive" effect:
 *   - Only works on fainted Pokemon (current_hp == 0)
 *   - Restores to floor(max_hp * amount) where amount=0.5
 *   - Correctly checks faint condition first
 */

/**
 * TEST: ITEM-B05 - Pokeball catch formula
 * STATUS: PASS
 *
 * attempt_catch() (lines 267-299):
 *   catch_value = ((3*maxHP - 2*currentHP) * catchRate * ballMod) / (3*maxHP)
 *   3 shake checks, each: random(0,255) < catch_value
 *   All 3 must pass for successful catch.
 *
 * Default catch rate: 45.
 * Ball modifiers: Pokeball 1.0x, Great Ball 1.5x, Ultra Ball 2.0x.
 *
 * Formula matches Gen I-III mechanics. Lower HP = higher catch chance.
 */

/**
 * TEST: ITEM-B06 - Caught Pokemon NOT added to team
 * STATUS: BUG (HIGH)
 *
 * /api/battle/catch endpoint (routes lines 87-130):
 *   On successful catch:
 *   - Battle marked as over (winner="player") ✓
 *   - Pokeball quantity decremented ✓
 *   - Caught Pokemon NEVER added to player's party or PC ✗
 *
 * The Pokemon effectively vanishes after being "caught."
 * Player loses a Pokeball and gains nothing.
 *
 * BUG SEVERITY: HIGH — core catch mechanic is broken. This is the
 *   most critical bug in the items system.
 */

/**
 * TEST: ITEM-B07 - Shop buy with insufficient funds
 * STATUS: PASS
 *
 * buy_item() (lines 181-224):
 *   - Validates item exists in shop
 *   - Checks money >= price * quantity
 *   - Returns error message if insufficient funds
 *   - Correctly deducts money on success
 *   - Adds/increments inventory entry
 */

/**
 * TEST: ITEM-B08 - Shop sell
 * STATUS: PASS
 *
 * sell_item() (lines 227-264):
 *   - Validates item exists and player has enough quantity
 *   - Decrements inventory quantity
 *   - Adds sell_price * quantity to player money
 *   - Starting money: 3000
 */

/**
 * TEST: ITEM-B09 - Shop stock not enforced
 * STATUS: BUG (LOW)
 *
 * ShopItem model has a `stock` field loaded from shops.json.
 * The field is exposed in API responses but buy_item() NEVER checks
 * or decrements stock. All shops currently have stock=-1 (unlimited).
 *
 * If finite stock is ever added to shop data, it would be silently
 * ignored.
 *
 * BUG SEVERITY: Low — all shops are unlimited, but the stock field
 *   is misleading dead data.
 */

/**
 * TEST: ITEM-B10 - Toss leaves zero-quantity ghost entries
 * STATUS: BUG (LOW)
 *
 * toss_item() (line 155): Clamps quantity to 0 but does NOT remove
 * the inventory entry. After tossing all of an item, a ghost entry
 * with quantity=0 remains in the inventory list.
 *
 * get_inventory() returns these zero-quantity entries to the client.
 *
 * BUG SEVERITY: Low — cosmetic issue, player sees "Potion x0" in
 *   inventory.
 */

/**
 * TEST: ITEM-B11 - No quantity validation on buy/sell/toss
 * STATUS: BUG (MEDIUM)
 *
 * BuyRequest, SellRequest, TossItemRequest all accept quantity: int
 * with no Field(gt=0) constraint in the Pydantic models.
 *
 * Exploits possible:
 *   - buy_item(quantity=0): deducts 0 money, adds 0 items (harmless)
 *   - buy_item(quantity=-1): money check passes (price * -1 < money),
 *     money INCREASES, inventory item quantity decreases
 *   - sell_item(quantity=-1): could allow negative inventory
 *
 * BUG SEVERITY: Medium — negative quantity exploit can generate
 *   infinite money.
 */

/**
 * TEST: ITEM-B12 - Dead code: _find_inventory_item
 * STATUS: NOTE (code quality)
 *
 * _find_inventory_item() (line 64) is defined but never called
 * anywhere in the codebase. It also has a confusing operator
 * precedence issue in its conditional.
 *
 * No functional impact. Should be removed or used.
 */

/**
 * TEST: ITEM-B13 - Unused math import
 * STATUS: NOTE (code quality)
 *
 * item_service.py line 5: `import math` is never used.
 */

/**
 * TEST: ITEM-B14 - Redundant inventory check in catch endpoint
 * STATUS: NOTE (code quality)
 *
 * /api/battle/catch (route line 102): Calls get_inventory(req.game_id)
 * but doesn't use the result. Then separately fetches the game and
 * manually iterates raw inventory. Wasted API call.
 */


// ============================================================
// CROSS-CUTTING INTEGRATION
// ============================================================

/**
 * TEST: INT-EI01 - Evolution + Items interaction
 * STATUS: NOTE
 *
 * No direct interaction between evolution and items systems.
 * Items like "Rare Candy" (instant level-up) or evolution stones
 * are not implemented. Current items are healing/catching only.
 * This is fine for Sprint 3 scope.
 */

/**
 * TEST: INT-EI02 - Battle catch -> inventory flow
 * STATUS: BUG (see ITEM-B06)
 *
 * Full catch flow:
 *   1. Player uses Pokeball from battle menu ← NOT IMPLEMENTED (battle Bag is no-op)
 *   2. POST /api/battle/catch with ball item_id
 *   3. Backend calculates catch success
 *   4. If caught, battle ends but Pokemon NOT added to team
 *   5. Frontend cannot trigger catch from battle UI anyway
 *
 * Double-blocked: frontend can't initiate + backend doesn't complete.
 */

/**
 * TEST: INT-EI03 - Evolution frontend-backend sync
 * STATUS: PASS with note
 *
 * Frontend evolution.js is purely animation — no evolution logic.
 * game.js calls backend to check evolution and trigger it.
 *
 * However, frontend evolution data in starter.js (hardcoded evolution
 * levels) may diverge from backend species data. Frontend does some
 * local evolution checking that could conflict with backend.
 */


// ============================================================
// BUG SUMMARY
// ============================================================

/**
 * Sprint 3 QA-A: Evolution & Items Findings
 *
 * HIGH SEVERITY:
 *   1. [ITEM-B06] Caught Pokemon not added to team — catch endpoint
 *      marks battle as won and decrements Pokeballs but never adds
 *      the caught Pokemon to party or PC. Pokemon vanishes.
 *
 * MEDIUM SEVERITY:
 *   2. [EVO-B06] Evolution replaces entire moveset — discards any
 *      custom/taught moves. Should preserve existing moves and only
 *      add new level-up moves.
 *
 *   3. [EVO-B07] current_hp not updated on level-up or evolution —
 *      Pokemon appears damaged after gaining levels even though max
 *      HP increased. Should gain the HP delta.
 *
 *   4. [EVO-B08] Evolved Pokemon not registered in Pokedex — backend
 *      Pokedex service exists but evolution doesn't call it.
 *
 *   5. [ITEM-F02] Frontend inventory is hardcoded mock data — bag
 *      screen shows fake items, ignoring backend inventory API.
 *
 *   6. [ITEM-F03] Use and Give item actions are no-ops — selecting
 *      these does nothing but closes the menu, misleading the player.
 *
 *   7. [ITEM-F05] Party screen HP hardcoded to 20/20 — doesn't
 *      reflect actual battle damage or level-ups.
 *
 *   8. [ITEM-B11] No quantity validation — negative quantities in
 *      buy/sell can exploit money system (infinite money glitch).
 *
 * LOW SEVERITY:
 *   9. [EVO-F05] evolution.js start() doesn't validate null params.
 *
 *  10. [ITEM-B09] Shop stock field loaded but never enforced.
 *
 *  11. [ITEM-B10] Toss leaves zero-quantity ghost entries in inventory.
 *
 * CODE QUALITY NOTES:
 *  12. [EVO-B09] Redundant get_species() calls in award_exp()
 *  13. [ITEM-B12] Dead code: _find_inventory_item() never called
 *  14. [ITEM-B13] Unused math import
 *  15. [ITEM-B14] Redundant inventory check in catch endpoint
 *
 * OVERALL VERDICT: Sprint 3 evolution system works well for the
 *   animation and basic level-up flow, but has gaps in HP handling
 *   and Pokedex integration. Items system backend is solid for
 *   healing/status/shop mechanics but catch flow is broken (Pokemon
 *   vanishes). Frontend item/bag UI is non-functional (mock data,
 *   no-op actions). The negative quantity exploit is a security concern.
 *
 * RECOMMENDATION: Fix ITEM-B06 (catch adding Pokemon) and ITEM-B11
 *   (quantity validation) as priority — these are functional bugs.
 *   The frontend integration gaps (ITEM-F02, ITEM-F03, ITEM-F05)
 *   are known tech debt tracked in Task #45.
 */
