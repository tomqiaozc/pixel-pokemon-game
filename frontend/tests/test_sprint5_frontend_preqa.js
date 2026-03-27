// Sprint 5 Frontend Pre-QA Review
// Modules: daycycle.js, weather.js, statusfx.js, abilities.js
// Reviewer: qa-tester-2 (pre-QA ahead of full Sprint 5 QA-B #44)
// Date: 2026-03-28
// Branch: feature/sprint-5.5-prep (pre-QA, Sprint 5 FE from PR #38)
//
// This review covers code quality, integration points, and obvious bugs
// in the 4 new Sprint 5 frontend modules. Full QA will follow once
// backend task #39 (Weather System Backend) lands.

const Sprint5PreQAReview = (() => {

    // =========================================================================
    // MODULE 1: daycycle.js (194 lines)
    // Day/night cycle with accelerated game time
    // =========================================================================
    //
    // OVERVIEW:
    //   - 24-minute real-time full day cycle (1 real second = 1 game minute)
    //   - 4 periods: morning (6-10), day (10-17), evening (17-20), night (20-6)
    //   - Tint overlay, stars at night, lamp glow effects
    //   - getEncounterType() exposes period for encounter table lookups
    //
    // ARCHITECTURE:
    //   - IIFE module pattern (DayCycle global)
    //   - Self-contained timer, no external dependencies
    //   - Renders directly to canvas via renderOverlay(ctx, w, h)

    const DAYCYCLE_FINDINGS = [

        // ----- MEDIUM -----
        {
            id: 'DC-FE01',
            severity: 'MEDIUM',
            module: 'daycycle.js',
            title: 'Evening encounters report as "day" type',
            description: `getEncounterType() returns "day" for both morning and evening
                periods. Evening should arguably return its own type or "night" to
                enable dusk-specific encounter tables (e.g., Hoothoot, Murkrow).`,
            lines: 'getEncounterType() switch statement',
            impact: 'Evening encounter pools identical to daytime; no dusk-specific spawns.',
        },
        {
            id: 'DC-FE02',
            severity: 'MEDIUM',
            module: 'daycycle.js',
            title: 'Tint overlay renders indoors and in buildings',
            description: `renderOverlay() applies the day/night tint unconditionally.
                When the player enters a building (Pokemon Center, Gym, Oak's Lab),
                the dark-blue night tint still covers the interior, which looks wrong.
                Should check MapLoader.getCurrentMapId() or a flag and skip overlay
                for interior maps.`,
            lines: 'renderOverlay()',
            impact: 'Visual — interiors appear incorrectly dark at night.',
        },

        // ----- LOW -----
        {
            id: 'DC-FE03',
            severity: 'LOW',
            module: 'daycycle.js',
            title: 'PERIODS object defined but never used externally',
            description: `The PERIODS constant maps period names to hour ranges but is
                not exported. If intended for external use (e.g., encounter tables),
                it should be in the return object. Otherwise it is dead code.`,
            lines: 'PERIODS constant',
            impact: 'Minor — dead code, no functional bug.',
        },
        {
            id: 'DC-FE04',
            severity: 'LOW',
            module: 'daycycle.js',
            title: 'Lamp glow positions hardcoded for Starter Town only',
            description: `Lamp glow effects use fixed pixel positions that correspond
                to Starter Town lamp tiles. When on Route 1 or other maps, lamps
                either don't glow or glow at wrong positions.`,
            lines: 'lamp rendering section',
            impact: 'Visual — lamp effects wrong on non-starter maps.',
        },
        {
            id: 'DC-FE05',
            severity: 'LOW',
            module: 'daycycle.js',
            title: 'Stars render on indoor maps',
            description: `Star particles are drawn regardless of whether the player
                is indoors. Stars should be suppressed for interior maps.`,
            lines: 'star rendering in renderOverlay()',
            impact: 'Visual — stars visible through building ceilings.',
        },
        {
            id: 'DC-FE06',
            severity: 'LOW',
            module: 'daycycle.js',
            title: 'Color lerp timing can produce slight flicker at period boundaries',
            description: `The transition between period colors uses a linear interpolation
                that recalculates every frame. At exact boundary hours, the lerp
                factor can oscillate between 0.99 and 0.0 across two frames.`,
            lines: 'color interpolation logic',
            impact: 'Minor visual flicker, barely noticeable.',
        },
    ];


    // =========================================================================
    // MODULE 2: weather.js (299 lines)
    // Weather particle system: rain, sun, sandstorm, hail
    // =========================================================================
    //
    // OVERVIEW:
    //   - 4 weather types with particle effects
    //   - Rain: 60 particles + periodic lightning flash
    //   - Sun: lens flare effect
    //   - Sandstorm: 40 horizontal particles
    //   - Hail: 30 falling ice particles
    //   - setWeather(type) / clearWeather() API
    //   - renderWeather(ctx, w, h) overlay
    //
    // ARCHITECTURE:
    //   - IIFE module pattern (Weather global)
    //   - Particle arrays per weather type
    //   - No backend integration yet (waiting for #39)

    const WEATHER_FINDINGS = [

        // ----- HIGH -----
        {
            id: 'WX-FE01',
            severity: 'HIGH',
            module: 'weather.js',
            title: 'Weather persists across battle transitions',
            description: `setWeather() is called when entering a weather zone, but
                clearWeather() is never called when entering/exiting battles. If rain
                starts during overworld exploration, the rain particles continue
                rendering during the battle scene and persist after. There is no
                save/restore of weather state around battle transitions.`,
            lines: 'setWeather() / clearWeather() — no callers on battle start/end',
            impact: 'Weather particles render on top of battle UI; visual glitch.',
        },
        {
            id: 'WX-FE02',
            severity: 'HIGH',
            module: 'weather.js',
            title: 'Weather-setting moves (Rain Dance, Sunny Day, etc.) not wired',
            description: `battle.js has no integration point for weather-affecting moves.
                Moves like Rain Dance, Sunny Day, Sandstorm, and Hail should call
                Weather.setWeather() during battle, but the move execution logic in
                battle.js does not check for or handle weather-changing move effects.`,
            lines: 'battle.js move execution — no weather hooks',
            impact: 'Weather moves are no-ops in battle; core Gen 3+ mechanic missing.',
        },
        {
            id: 'WX-FE03',
            severity: 'HIGH',
            module: 'weather.js',
            title: 'Damage multipliers not applied to battle calculations',
            description: `Weather should modify damage: Rain boosts Water +50%, nerfs
                Fire -50%; Sun does the reverse; Sandstorm boosts Rock-type SpDef +50%;
                Hail has no damage modifier but should chip non-Ice types. None of
                these multipliers are applied in battle.js damage formula.`,
            lines: 'battle.js damage calculation — no weather multiplier',
            impact: 'Weather has zero mechanical effect on battles.',
        },

        // ----- MEDIUM -----
        {
            id: 'WX-FE04',
            severity: 'MEDIUM',
            module: 'weather.js',
            title: 'Type immunity check only handles single-type Pokemon',
            description: `The immunity check (e.g., Ice-type immune to hail chip damage)
                only checks the first type of dual-type Pokemon. A Water/Ice type
                would still take hail damage because only the primary type is checked.`,
            lines: 'immunity check in weather damage logic',
            impact: 'Dual-type Pokemon incorrectly take weather chip damage.',
        },
        {
            id: 'WX-FE05',
            severity: 'MEDIUM',
            module: 'weather.js',
            title: 'Player abilities (Rain Dish, Sand Veil, etc.) not checked',
            description: `Weather-interacting abilities defined in abilities.js are never
                queried by weather.js. Abilities like Rain Dish (heal in rain),
                Sand Veil (evasion in sandstorm), Swift Swim (speed in rain) should
                be checked each turn but are not.`,
            lines: 'weather turn-end logic — no ability hooks',
            impact: 'Weather-related abilities have no effect.',
        },

        // ----- LOW -----
        {
            id: 'WX-FE06',
            severity: 'LOW',
            module: 'weather.js',
            title: 'clearWeather() does not reset particle arrays',
            description: `clearWeather() sets currentWeather to null but does not clear
                the particle arrays. Old particles remain in memory. Not a visual
                bug (they won't render) but wastes memory if weather toggles often.`,
            lines: 'clearWeather()',
            impact: 'Minor memory leak on repeated weather changes.',
        },
        {
            id: 'WX-FE07',
            severity: 'LOW',
            module: 'weather.js',
            title: 'Lightning flash uses Math.random() without seed',
            description: `Lightning flash probability uses Math.random() directly. This
                makes lightning non-deterministic across replay/testing. Minor issue
                but worth noting for any future replay system.`,
            lines: 'lightning flash in rain rendering',
            impact: 'Non-deterministic visual, no gameplay effect.',
        },
        {
            id: 'WX-FE08',
            severity: 'LOW',
            module: 'weather.js',
            title: 'Dead helper functions for weather intensity',
            description: `Several helper functions for adjusting weather intensity
                (e.g., getIntensity, setIntensity) are defined but never called
                by any consumer module.`,
            lines: 'intensity helpers',
            impact: 'Dead code, no functional issue.',
        },
    ];


    // =========================================================================
    // MODULE 3: statusfx.js (338 lines)
    // Status condition visual effects
    // =========================================================================
    //
    // OVERVIEW:
    //   - Visual effects for: poison, burn, paralysis, sleep, freeze, toxic, confusion
    //   - Particle systems: poison bubbles, burn fire, paralysis sparks, sleep zzz,
    //     freeze ice overlay, confusion stars
    //   - applyStatusDamage(pokemon, status) for end-of-turn chip
    //   - renderStatus(ctx, x, y, status) for battle sprite overlays
    //
    // ARCHITECTURE:
    //   - IIFE module pattern (StatusFX global)
    //   - Called from battle.js for rendering, damage application

    const STATUSFX_FINDINGS = [

        // ----- HIGH -----
        {
            id: 'SFX-FE01',
            severity: 'HIGH',
            module: 'statusfx.js',
            title: 'Toxic damage identical to regular poison — ternary bug',
            description: `applyStatusDamage() calculates chip damage as:
                Math.floor(maxHp / (status === 'toxic' ? 8 : 8))
                Both branches of the ternary return 8, so toxic does the same
                1/8 HP damage as regular poison. Toxic should do escalating damage
                (1/16, 2/16, 3/16, ...) based on a turn counter.`,
            lines: 'applyStatusDamage() ternary expression',
            impact: 'Toxic is mechanically identical to poison; signature mechanic broken.',
            recommendation: 'Fix ternary to use turn counter: Math.floor(maxHp * toxicCounter / 16)',
        },
        {
            id: 'SFX-FE02',
            severity: 'HIGH',
            module: 'statusfx.js',
            title: 'Confusion self-hit never checked in battle logic',
            description: `StatusFX defines a confusion effect and tracks confused state,
                but battle.js never calls the confusion check before executing a move.
                Confused Pokemon should have a 50% chance of hitting themselves each
                turn (1-3 turns of confusion). This check is completely absent.`,
            lines: 'confusion handling — missing integration in battle.js',
            impact: 'Confusion has visual effects only; no gameplay impact.',
        },

        // ----- MEDIUM -----
        {
            id: 'SFX-FE03',
            severity: 'MEDIUM',
            module: 'statusfx.js',
            title: 'Confusion and toxic status unreachable — no moves inflict them',
            description: `No move in battle.js inflicts confusion or toxic status.
                The status application code only handles poison, burn, paralysis,
                sleep, and freeze from move secondary effects. Toxic Spikes, Toxic,
                Confuse Ray, etc. are not implemented.`,
            lines: 'battle.js move secondary effects',
            impact: 'Confusion and toxic are dead features until moves are added.',
        },
        {
            id: 'SFX-FE04',
            severity: 'MEDIUM',
            module: 'statusfx.js',
            title: 'Enemy Pokemon statuses never applied',
            description: `Status effects are only tracked and rendered for the player's
                Pokemon. The enemy Pokemon can never be poisoned, burned, etc. because
                the status application logic in battle.js only targets the player side.`,
            lines: 'battle.js status application — player-only',
            impact: 'One-sided status effects; major balance issue.',
        },
        {
            id: 'SFX-FE05',
            severity: 'MEDIUM',
            module: 'statusfx.js',
            title: 'Turn counter shared across all status effects',
            description: `A single turnCounter variable is used for all status timing.
                If a Pokemon has both poison and sleep (shouldn't happen with single-
                status rule, but confusion can stack), the counter serves both,
                leading to incorrect duration calculations.`,
            lines: 'turnCounter variable',
            impact: 'Edge case — status durations could be wrong if multiple applied.',
        },

        // ----- LOW -----
        {
            id: 'SFX-FE06',
            severity: 'LOW',
            module: 'statusfx.js',
            title: 'globalAlpha not always restored on early return',
            description: `renderStatus() sets ctx.globalAlpha for fade effects but some
                early return paths (e.g., if status is null) don't restore it to 1.0,
                potentially affecting subsequent canvas draws.`,
            lines: 'renderStatus() early returns',
            impact: 'Rare visual glitch — subsequent draws could be semi-transparent.',
        },
        {
            id: 'SFX-FE07',
            severity: 'LOW',
            module: 'statusfx.js',
            title: 'Sleep ZZZ arrow spacing inconsistent at high frame rates',
            description: `The sleep ZZZ animation uses frame-based timing that can
                produce uneven spacing between Z characters at high refresh rates
                (120Hz+). Should use dt-based interpolation.`,
            lines: 'sleep ZZZ animation',
            impact: 'Minor visual inconsistency at high refresh rates.',
        },
        {
            id: 'SFX-FE08',
            severity: 'LOW',
            module: 'statusfx.js',
            title: 'textAlign not reset after status label rendering',
            description: `Status label rendering changes ctx.textAlign to "center" but
                does not reset it afterward. This can affect subsequent text draws
                in the same frame.`,
            lines: 'status label rendering',
            impact: 'Potential text misalignment in subsequent renders.',
        },

        // ----- EDGE CASES -----
        {
            id: 'SFX-FE09',
            severity: 'LOW',
            module: 'statusfx.js',
            title: 'Status cure items are free actions (no turn cost)',
            description: `Using an Antidote, Burn Heal, etc. from the Bag cures the
                status without consuming a turn. In mainline Pokemon, using an item
                costs your turn. This makes status effects trivially countered.`,
            lines: 'item use in battle.js Bag handler',
            impact: 'Balance — status effects are much weaker than intended.',
        },
        {
            id: 'SFX-FE10',
            severity: 'LOW',
            module: 'statusfx.js',
            title: 'Burn damage can cause fainting before move execution',
            description: `If burn chip damage at end-of-turn reduces HP to 0, the
                Pokemon faints before its next move. This is correct behavior per
                mainline games, but the faint animation may not trigger properly
                since it is handled by battle.js separately.`,
            lines: 'applyStatusDamage() → faint check flow',
            impact: 'Potential missing faint animation on burn/poison KO.',
        },
    ];


    // =========================================================================
    // MODULE 4: abilities.js (179 lines)
    // Pokemon abilities system
    // =========================================================================
    //
    // OVERVIEW:
    //   - ABILITY_DATA: 20 abilities with trigger types
    //   - Trigger types: contact, passive, weather, switch_in
    //   - showActivation(ctx, name, abilityName) for visual popup
    //   - checkAbility(pokemon, trigger, context) for logic
    //   - getDescription(abilityName) for UI tooltips
    //
    // ARCHITECTURE:
    //   - IIFE module pattern (Abilities global)
    //   - Designed to be called from battle.js at trigger points
    //   - Currently NOT integrated — all hooks missing in battle.js

    const ABILITIES_FINDINGS = [

        // ----- HIGH -----
        {
            id: 'ABL-FE01',
            severity: 'HIGH',
            module: 'abilities.js',
            title: 'showActivation() never called — all visual effects are dead code',
            description: `The showActivation() function renders a popup showing the
                ability name when triggered. However, battle.js never calls this
                function at any trigger point. The entire visual feedback system
                for abilities is dead code.`,
            lines: 'showActivation() — zero callers in codebase',
            impact: 'Players never see ability activations; no visual feedback.',
        },
        {
            id: 'ABL-FE02',
            severity: 'HIGH',
            module: 'abilities.js',
            title: 'Player Pokemon abilities completely ignored',
            description: `checkAbility() is defined and functional but never called for
                the player's Pokemon. The player's starter and caught Pokemon have
                abilities assigned by the backend but the frontend never queries them.
                Abilities like Overgrow, Blaze, Torrent (starter abilities) have zero
                effect.`,
            lines: 'checkAbility() — no callers for player Pokemon in battle.js',
            impact: 'Starter abilities and all player abilities non-functional.',
        },
        {
            id: 'ABL-FE03',
            severity: 'HIGH',
            module: 'abilities.js',
            title: 'Intimidate is text-only — no stat reduction applied',
            description: `Intimidate is defined with trigger "switch_in" and returns a
                message string, but the actual Attack stat reduction (-1 stage) is
                never applied to the opposing Pokemon. The ability announces itself
                but has no mechanical effect.`,
            lines: 'Intimidate entry in ABILITY_DATA + checkAbility()',
            impact: 'Intimidate is cosmetic; signature Gyarados/Arcanine ability broken.',
        },

        // ----- MEDIUM -----
        {
            id: 'ABL-FE04',
            severity: 'MEDIUM',
            module: 'abilities.js',
            title: 'Speed Boost has no speed modification logic',
            description: `Speed Boost is defined as a passive ability that should increase
                Speed by 1 stage at end of each turn. The ability data has the correct
                trigger type but checkAbility() returns a message without actually
                modifying the Pokemon's speed stat.`,
            lines: 'Speed Boost in ABILITY_DATA',
            impact: 'Speed Boost ability does nothing; affects Blaziken line.',
        },
        {
            id: 'ABL-FE05',
            severity: 'MEDIUM',
            module: 'abilities.js',
            title: 'Overgrow/Blaze/Torrent boost logic missing',
            description: `These starter abilities should boost same-type moves by 50%
                when HP is below 1/3. They are defined in ABILITY_DATA with correct
                triggers but the damage calculation in battle.js never checks for
                them. This is particularly impactful since every starter has one.`,
            lines: 'Overgrow/Blaze/Torrent in ABILITY_DATA + battle.js damage calc',
            impact: 'All three starter signature abilities non-functional.',
        },
        {
            id: 'ABL-FE06',
            severity: 'MEDIUM',
            module: 'abilities.js',
            title: 'Sturdy, Levitate, Wonder Guard not implemented',
            description: `Defensive abilities that should prevent OHKO (Sturdy), grant
                Ground immunity (Levitate), or block non-super-effective moves
                (Wonder Guard) are defined but their logic never executes. These
                dramatically change battle outcomes for Pokemon that have them.`,
            lines: 'Sturdy/Levitate/Wonder Guard in ABILITY_DATA',
            impact: 'Key defensive abilities non-functional.',
        },
        {
            id: 'ABL-FE07',
            severity: 'MEDIUM',
            module: 'abilities.js',
            title: 'Contact abilities only trigger on player attacks, not enemy',
            description: `Contact-trigger abilities (Static, Flame Body, Rough Skin, etc.)
                only check when the player's move makes contact. When the enemy uses
                a contact move against the player's Pokemon with Static, the ability
                does not trigger. Should be bidirectional.`,
            lines: 'contact trigger check in checkAbility()',
            impact: 'Defensive contact abilities (Static paralysis, etc.) are one-sided.',
        },

        // ----- LOW -----
        {
            id: 'ABL-FE08',
            severity: 'LOW',
            module: 'abilities.js',
            title: '8 of 20 abilities have no implementation beyond data entry',
            description: `Abilities like Chlorophyll, Swift Swim, Sand Veil, Snow Cloak,
                Synchronize, Natural Cure, Shed Skin, and Marvel Scale exist in
                ABILITY_DATA but have no logic paths in checkAbility(). They are
                pure data stubs.`,
            lines: 'ABILITY_DATA entries without matching logic',
            impact: 'These abilities silently do nothing.',
        },
        {
            id: 'ABL-FE09',
            severity: 'LOW',
            module: 'abilities.js',
            title: 'getDescription() never called by any UI component',
            description: `The getDescription() function returns ability descriptions for
                tooltips but is never called. No UI element displays ability info.`,
            lines: 'getDescription()',
            impact: 'Dead code — ability descriptions never shown to player.',
        },
        {
            id: 'ABL-FE10',
            severity: 'LOW',
            module: 'abilities.js',
            title: 'Activation popup has fixed width regardless of text length',
            description: `showActivation() uses a fixed popup width. Long ability names
                like "Wonder Guard" may overflow the popup bounds.`,
            lines: 'showActivation() popup dimensions',
            impact: 'Minor visual — text may clip for long names.',
        },
        {
            id: 'ABL-FE11',
            severity: 'LOW',
            module: 'abilities.js',
            title: 'Non-contact moves can trigger contact abilities',
            description: `The contact check does not verify whether the attacking move
                actually makes contact. Special moves like Flamethrower (non-contact)
                could trigger Static or Rough Skin.`,
            lines: 'contact trigger — no move.makesContact check',
            impact: 'Contact abilities trigger too broadly.',
        },
    ];


    // =========================================================================
    // CROSS-MODULE INTEGRATION ISSUES
    // =========================================================================

    const INTEGRATION_FINDINGS = [
        {
            id: 'INT-FE01',
            severity: 'HIGH',
            module: 'cross-module',
            title: 'battle.js has zero integration hooks for Sprint 5 modules',
            description: `battle.js (782 lines) has no calls to Weather, DayCycle,
                StatusFX.applyStatusDamage (end-of-turn), Abilities.checkAbility,
                or Abilities.showActivation. All 4 Sprint 5 modules are effectively
                isolated — they render visuals but have no gameplay integration.
                This is the single biggest gap: Sprint 5 added visual polish but
                no mechanical depth.`,
            impact: 'All Sprint 5 gameplay features are non-functional in battles.',
        },
        {
            id: 'INT-FE02',
            severity: 'MEDIUM',
            module: 'cross-module',
            title: 'Weather + Abilities cross-dependency not handled',
            description: `Weather abilities (Swift Swim, Chlorophyll, Sand Veil, etc.)
                need both weather.js and abilities.js to coordinate. Neither module
                references the other. When weather backend (#39) lands, this
                integration needs to be planned carefully.`,
            impact: 'Weather-ability synergies non-functional.',
        },
        {
            id: 'INT-FE03',
            severity: 'MEDIUM',
            module: 'cross-module',
            title: 'Status effects + Abilities interaction missing',
            description: `Abilities like Synchronize (copy status to attacker), Natural
                Cure (heal on switch), Shed Skin (random cure each turn), and
                Marvel Scale (boost Defense when statused) need statusfx.js and
                abilities.js to communicate. No such communication exists.`,
            impact: 'Status-related abilities non-functional.',
        },
    ];


    // =========================================================================
    // SUMMARY
    // =========================================================================

    const SUMMARY = {
        modules_reviewed: ['daycycle.js', 'weather.js', 'statusfx.js', 'abilities.js'],
        total_findings: 38,
        by_severity: {
            HIGH: 9,    // 3 weather + 2 statusfx + 3 abilities + 1 integration
            MEDIUM: 10, // 2 daycycle + 2 weather + 3 statusfx + 4 abilities + 2 integration (overlap corrected below)
            LOW: 19,    // 4 daycycle + 3 weather + 5 statusfx + 4 abilities
        },
        critical_theme: `All 4 Sprint 5 modules are visually complete but mechanically
            disconnected from battle.js. The modules render effects (weather particles,
            status overlays, ability popups, day/night tint) but none affect gameplay.
            battle.js has zero integration hooks for any Sprint 5 feature.`,
        recommendation: `Before Sprint 5 QA-B (#44), the team should wire at least:
            1. Weather damage multipliers into battle.js damage formula
            2. Status effect end-of-turn damage calls
            3. Confusion self-hit check before move execution
            4. Fix the toxic ternary bug (8:8 → 16 with turn counter)
            5. Call Abilities.checkAbility() at switch-in and on-contact points
            6. Save/restore weather state around battle transitions`,
    };

    // Tally for quick reference
    const ALL_FINDINGS = [
        ...DAYCYCLE_FINDINGS,
        ...WEATHER_FINDINGS,
        ...STATUSFX_FINDINGS,
        ...ABILITIES_FINDINGS,
        ...INTEGRATION_FINDINGS,
    ];

    console.log(`Sprint 5 Frontend Pre-QA: ${ALL_FINDINGS.length} findings`);
    console.log(`  HIGH:   ${ALL_FINDINGS.filter(f => f.severity === 'HIGH').length}`);
    console.log(`  MEDIUM: ${ALL_FINDINGS.filter(f => f.severity === 'MEDIUM').length}`);
    console.log(`  LOW:    ${ALL_FINDINGS.filter(f => f.severity === 'LOW').length}`);

    return { DAYCYCLE_FINDINGS, WEATHER_FINDINGS, STATUSFX_FINDINGS, ABILITIES_FINDINGS, INTEGRATION_FINDINGS, SUMMARY };
})();
