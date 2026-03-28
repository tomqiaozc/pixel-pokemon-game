// Sprint 9 QA-B: Fishing, Surfing & Move Tutor UI — Full Review
// Reviewer: qa-tester-2
// Date: 2026-03-28
// Task: #92
// Scope: Frontend PRs #84 (fishing/surfing), #86 (move tutor) + backend
// Backend tests: 1177 passed, 0 failed
//
// CRITICAL THEME: Move Tutor API wiring is completely broken — all 4 api.js
// functions call non-existent endpoints (/api/moves/* instead of /api/tutor/*).
// Fishing init runs before game session exists, making fishing permanently
// non-functional. The reel mini-game has zero challenge due to held-key input.

const Sprint9QAB = (() => {

    // =========================================================================
    // SECTION 1: CRITICAL — API WIRING & GAME-BREAKING BUGS
    // =========================================================================

    const CRITICAL_FINDINGS = [
        {
            id: 'S9-C01',
            severity: 'CRITICAL',
            module: 'api.js:646-647 / move_tutor.py:91',
            title: 'getTutorMoves() calls non-existent endpoint — wrong URL path',
            description: `api.js calls GET /api/moves/tutor/{mapId}. Backend route is
                GET /api/tutor/{tutor_id}. Path prefix is /api/moves/ instead of /api/tutor/,
                and parameter is mapId (e.g. "pallet_town") instead of tutor_id
                (e.g. "pallet_tutor"). Always 404s. Falls back to hardcoded local moves
                (Mega Punch, Mega Kick) that differ entirely from backend tutor catalog.`,
            impact: 'Move Tutor always shows stale local fallback moves. Backend tutor catalog unused.',
        },
        {
            id: 'S9-C02',
            severity: 'CRITICAL',
            module: 'api.js:650-656 / move_tutor.py',
            title: 'checkMoveCompatibility() calls non-existent endpoint',
            description: `api.js POSTs to /api/moves/compatibility with {game_id, pokemon_index,
                move_name}. No such route exists. Backend has GET /api/tm/compatible/{tm_number}/
                {pokemon_id} (different verb, different params). .catch() at movetutor.js:275
                silently proceeds to teach anyway, bypassing all compatibility validation.`,
            impact: 'Any Pokemon can learn any move regardless of type compatibility.',
        },
        {
            id: 'S9-C03',
            severity: 'CRITICAL',
            module: 'api.js:659-666 / move_tutor.py',
            title: 'teachMove() calls non-existent endpoint with wrong payload',
            description: `api.js POSTs to /api/moves/teach with {game_id, pokemon_index,
                move_name, replace_slot}. Backend has POST /api/tutor/teach expecting
                {game_id, pokemon_index, tutor_id, move_name, forget_move_index}. Wrong URL,
                missing tutor_id, wrong field name (replace_slot vs forget_move_index).
                .catch(() => {}) swallows error. Moves never persist to backend.`,
            impact: 'All tutor/TM moves are local-only. Lost on save/reload. No cost deduction.',
        },
        {
            id: 'S9-C04',
            severity: 'CRITICAL',
            module: 'fishing.js:411 / game.js:46',
            title: 'Fishing.init() runs before game session — equippedRod permanently null',
            description: `Fishing.init() is called at game.js line 46 during Game.init().
                At that point API.gameId is null (createGame not yet called). API.getInventory()
                returns null immediately. equippedRod is never set. No code path ever calls
                Fishing.setRod(). canFish() always returns false.`,
            impact: 'Fishing is completely non-functional. Players can never fish.',
        },
        {
            id: 'S9-C05',
            severity: 'CRITICAL',
            module: 'fishing.js:141,163 / input.js:44',
            title: 'Reel mini-game uses held-key check — zero challenge',
            description: `Input.isActionPressed() returns true every frame the key is held.
                In reeling state, reelProgress += REEL_GAIN (18) fires every frame. Holding Z
                fills bar from 25 to 100 in ~4 frames (66ms at 60fps). The "Mash Z!" mechanic
                is completely bypassed — holding the button catches every fish instantly.`,
            impact: 'Fishing mini-game has no gameplay challenge. Every catch trivially succeeds.',
        },
    ];


    // =========================================================================
    // SECTION 2: HIGH — DATA LOSS, INTEGRATION & RENDERING BUGS
    // =========================================================================

    const HIGH_FINDINGS = [
        {
            id: 'S9-H01',
            severity: 'HIGH',
            module: 'api.js:669-672 / move_tutor.py:78',
            title: 'getReminderMoves() wrong URL + response format mismatch',
            description: `api.js calls GET /api/moves/reminder/{gameId}/{pokemonIndex}.
                Backend route is GET /api/tutor/reminder/{game_id}/{pokemon_index}.
                Even if URL were correct, backend returns {forgotten_moves: [...]} but
                frontend expects flat array — Array.isArray({...}) is false.`,
            impact: 'Move Reminder feature completely non-functional.',
        },
        {
            id: 'S9-H02',
            severity: 'HIGH',
            module: 'fishing.js:193 / game.js:309-313',
            title: 'Fish encounter skips Pokedex markSeen, transition animation, stat timing',
            description: `Fish→battle path in game.js skips: (1) Pokedex.markSeen() call
                (encounters.js does this, fishing path does not), (2) encounter transition
                animation (flash + black bars), (3) fishCaught stat incremented on reel
                success BEFORE battle outcome, inflating count for escaped fish.`,
            impact: 'Fished Pokemon never appear as "seen" in Pokedex. Jarring battle entry.',
        },
        {
            id: 'S9-H03',
            severity: 'HIGH',
            module: 'fishing.js:203-237',
            title: 'buildFishEnemy() produces incomplete enemy data for battle.js',
            description: `When pendingFishData is present, backend moves are ignored (battle.js
                picks moves by type). When pendingFishData is null (fallback), returned object
                has no moves, stats, ability, or speciesId fields. Caught fallback fish get
                speciesId: 0, breaking evolution/EXP backend calls.`,
            impact: 'Fallback fish Pokemon have speciesId 0. Backend move pools wasted.',
        },
        {
            id: 'S9-H04',
            severity: 'HIGH',
            module: 'fishing.js:411-420',
            title: 'Rod selection picks first inventory match — no player rod choice',
            description: `init() iterates inventory and returns on first rod found. No sorting
                by quality. If Old Rod appears before Super Rod in inventory array, player is
                stuck with Old Rod. setRod() is exposed but never called from anywhere.
                No UI for rod selection exists.`,
            impact: 'Players cannot choose which rod to use.',
        },
        {
            id: 'S9-H05',
            severity: 'HIGH',
            module: 'movetutor.js:386 / openTM:114-121',
            title: 'TM not consumed — newMove.itemId is always undefined',
            description: `When source is 'tm', line 386 calls API.useItem(newMove.itemId, idx).
                But openTM() never copies itemId to the newMove object. API.useItem(undefined, idx)
                sends null item_id to backend. TMs are never consumed from inventory.`,
            impact: 'Players have infinite TM uses. Game balance broken.',
        },
        {
            id: 'S9-H06',
            severity: 'HIGH',
            module: 'movetutor.js:52 vs move_tutor_service.py:22',
            title: 'Frontend and backend HM_MOVES sets disagree',
            description: `Frontend: {Cut, Fly, Surf, Strength, Flash, Whirlpool, Waterfall, Dive}
                (8 moves). Backend: {Cut, Flash, Surf, Strength, Fly} (5 moves). Frontend
                blocks deletion of Whirlpool/Waterfall/Dive that backend would allow.`,
            impact: 'Inconsistent HM deletion rules between client and server.',
        },
        {
            id: 'S9-H07',
            severity: 'HIGH',
            module: 'movetutor.js:197-211, 340-390',
            title: 'Tutor move cost never deducted from player money',
            description: `startTeaching() never checks or deducts Game.player.money. Backend
                teach_move_via_tutor deducts cost, but API.teachMove() calls non-existent
                endpoint (S9-C03). Cost is displayed in UI but never charged anywhere.`,
            impact: 'All tutor moves are free. Listed prices are decorative.',
        },
        {
            id: 'S9-H08',
            severity: 'HIGH',
            module: 'game.js:8, 592-617',
            title: 'Surfing state persists through map transitions — movement breaks',
            description: `Fishing.isSurfing() is tracked as a module flag within overworld state.
                loadMap() never calls Fishing.cancelFishing() or resets surfing. If player
                surfs into a door/map exit, surfing persists into next map. On a map with
                no water, isSolidForMovement() with isSurf=true blocks all non-water solid
                tiles but allows walking through some walls.`,
            impact: 'Player can get stuck or clip through walls after surfing map transition.',
        },
        {
            id: 'S9-H09',
            severity: 'HIGH',
            module: 'playerstats.js:4-17',
            title: 'fishCaught and movesLearned stats not defined — increment produces NaN',
            description: `game.js:311 calls PlayerStats.increment('fishCaught') and
                movetutor.js:389 calls PlayerStats.increment('movesLearned'). Neither key
                exists in the initial stats object. Incrementing undefined produces NaN.
                Stats display as NaN, backend sync sends NaN values.`,
            impact: 'Fish caught and moves learned counters permanently broken (NaN).',
        },
        {
            id: 'S9-H10',
            severity: 'HIGH',
            module: 'move_tutor_service.py:362-385',
            title: 'TMs without item_id bypass inventory check — 8 TMs usable for free',
            description: `TM03-TM10 have item_id: None in TM_DEFINITIONS. use_tm() checks
                "if item_id is not None" before verifying inventory. TMs with null item_id
                skip inventory validation entirely. Psychic, Earthquake, Toxic, Fire Blast,
                Blizzard, Thunder, Rock Slide, Swift are all free and infinite.`,
            impact: 'Major game balance exploit. 8 powerful TMs usable without owning them.',
        },
    ];


    // =========================================================================
    // SECTION 3: MEDIUM — LOGIC & SYNC ISSUES
    // =========================================================================

    const MEDIUM_FINDINGS = [
        {
            id: 'S9-M01',
            severity: 'MEDIUM',
            module: 'fishing.js:95-99',
            title: 'API.fishEncounter() errors silently swallowed — no user feedback',
            description: `.catch(() => {}) on fishEncounter call. On maps without backend
                fishing tables (anything beyond pallet_town and route_2), 404 is silently
                ignored. pendingFishData stays null, fallback used with speciesId: 0.`,
            impact: 'No indication of backend failure. Fallback fish have broken speciesId.',
        },
        {
            id: 'S9-M02',
            severity: 'MEDIUM',
            module: 'fishing.js:95-98',
            title: 'API call race condition — response may arrive after fish is built',
            description: `fishEncounter() fires at cast start. If backend takes >2100ms
                (cast+min bobber wait), pendingFishData is still null at catch time.
                Cancelling fishing while API is in-flight leaves stale data for next attempt.`,
            impact: 'Slow connections use wrong fish data. Cancel→recast may use stale data.',
        },
        {
            id: 'S9-M03',
            severity: 'MEDIUM',
            module: 'fishing.js:353-355',
            title: 'Surf check uses p.type === "Water" — misses multi-type backend data',
            description: `party.some(p => p.type === 'Water') checks single string type.
                Backend-synced Pokemon have types array (["Water", "Poison"]). Also, any
                Water-type enables surfing regardless of level or knowing Surf move.`,
            impact: 'Surf availability inconsistent with backend data and game design.',
        },
        {
            id: 'S9-M04',
            severity: 'MEDIUM',
            module: 'movetutor.js:282-294',
            title: 'No duplicate move check — Pokemon can learn same move twice',
            description: `proceedToLearn() checks move count and empty slots but never checks
                if Pokemon already knows the move. Backend _teach_move_to_pokemon checks
                duplicates, but API call fails (S9-C03). Player can teach Flamethrower
                to a Pokemon that already has Flamethrower.`,
            impact: 'Wasted move slots with duplicate moves.',
        },
        {
            id: 'S9-M05',
            severity: 'MEDIUM',
            module: 'movetutor.js:openReminder',
            title: 'Move Reminder exported but never wired to any trigger',
            description: `openReminder(npcName) is exported but never called from game.js,
                npc.js, or menu.js. No NPC type check for 'reminder' in game.js (only 'tutor'
                at line 371). Entire Move Reminder flow is unreachable.`,
            impact: 'Move Reminder feature completely inaccessible to players.',
        },
        {
            id: 'S9-M06',
            severity: 'MEDIUM',
            module: 'movetutor.js:754,796',
            title: 'drawTutorNpc never caches sprite — regenerates canvas every frame',
            description: `Line 754 checks Sprites.cache but line 796 returns without storing
                the generated canvas back into cache. Every frame creates a new canvas element
                for tutor NPCs.`,
            impact: 'Performance degradation and GC pressure on maps with tutor NPCs.',
        },
        {
            id: 'S9-M07',
            severity: 'MEDIUM',
            module: 'movetutor.js:74-83 vs backend',
            title: 'Tutor move data shape mismatch — even with correct URL would break',
            description: `Frontend maps m.name, m.type, m.power, m.pp, m.max_pp. Backend
                get_tutor_info returns {move_name, cost, compatible_types} — no type, power,
                or pp fields. Even after fixing URL (S9-C01), moves display with undefined names.`,
            impact: 'Fixing S9-C01 alone is insufficient; response mapping also needs fixing.',
        },
        {
            id: 'S9-M08',
            severity: 'MEDIUM',
            module: 'encounters.js:256',
            title: 'Surf encounters use fabricated area_id — always local fallback',
            description: `Calls API.checkEncounter(currentMap + '_surfing'). Unless backend
                has encounter tables with _surfing suffix, returns null. No dedicated
                /api/encounter/surf endpoint exists. All surf encounters are local-only.`,
            impact: 'Surfing encounters bypass backend. No IVs, abilities, or gender on surf Pokemon.',
        },
        {
            id: 'S9-M09',
            severity: 'MEDIUM',
            module: 'fishing.js:159-162',
            title: 'Reel decay is non-functional — rate too low relative to gain',
            description: `Decay of 12 * (dt/1000) ≈ 0.19 points per tick vs gain of 18 per
                frame. Decay timer resets only after 100ms accumulation. Combined with
                S9-C05 (held-key), decay has zero practical effect.`,
            impact: 'Even without held-key bug, reel challenge is negligible.',
        },
        {
            id: 'S9-M10',
            severity: 'MEDIUM',
            module: 'game.js:370-375',
            title: 'Tutor NPC type check is exact string match — case/naming fragile',
            description: `game.js checks npc.type === 'tutor'. If backend NPC data uses
                'move_tutor' or 'Tutor', the check fails silently and falls through to
                generic dialogue. No error message to player.`,
            impact: 'Backend NPC type inconsistency silently breaks Move Tutor access.',
        },
    ];


    // =========================================================================
    // SECTION 4: LOW — POLISH & MINOR ISSUES
    // =========================================================================

    const LOW_FINDINGS = [
        {
            id: 'S9-L01',
            severity: 'LOW',
            module: 'fishing.js:130 / game.js:301',
            title: 'Escape during fishing cancels fishing AND opens pause menu',
            description: `Input.isDown('Escape') checked both in fishing.js (cancel) and
                game.js (pause menu). Same keypress fires both on consecutive frames.`,
        },
        {
            id: 'S9-L02',
            severity: 'LOW',
            module: 'fishing.js:325-339',
            title: 'globalAlpha set during fish result may leak if state changes mid-frame',
            description: `ctx.globalAlpha = alpha set at line 325, reset at 339.
                No ctx.save()/ctx.restore() pattern. State change mid-render could
                leave alpha partially transparent.`,
        },
        {
            id: 'S9-L03',
            severity: 'LOW',
            module: 'fishing.js:218-236',
            title: 'Super Rod fallback gives Gyarados 25% chance — too common for rare Pokemon',
            description: `All entries in fallback pool have equal weight. Gyarados has
                1/4 chance on Super Rod vs near-zero in original games.`,
        },
        {
            id: 'S9-L04',
            severity: 'LOW',
            module: 'fishing.js:329,338',
            title: 'Fish result overlay uses hardcoded font size — no scale factor',
            description: `renderFishResult uses 18px hardcoded instead of scaling with
                canvas scale factor like renderFishing does.`,
        },
        {
            id: 'S9-L05',
            severity: 'LOW',
            module: 'movetutor.js:155-160',
            title: 'close() does not reset all state — stale newMove can leak to next open',
            description: `close() resets active, phase, availableMoves, compatibleParty but
                not newMove, source, tutorNpcName, or resultMessage. Stale values could
                briefly flash on next open.`,
        },
        {
            id: 'S9-L06',
            severity: 'LOW',
            module: 'movetutor.js:48-49',
            title: 'tutorMovesCache and tmInventory declared but never used',
            description: `Both variables suggest planned caching that was never implemented.
                Dead code.`,
        },
        {
            id: 'S9-L07',
            severity: 'LOW',
            module: 'encounter_tables.json',
            title: 'Only 2 areas have fishing tables — most water tiles have no backend data',
            description: `Fishing tables exist only for pallet_town and route_2.
                All other maps return 404 and fall back to local data.`,
        },
    ];


    // =========================================================================
    // API WIRING AUDIT
    // =========================================================================

    const API_AUDIT = {
        fishing: {
            fishEncounter: 'WIRED — called on cast start',
            getInventory: 'WIRED but BROKEN — called before gameId exists (S9-C04)',
            checkEncounter_surf: 'PARTIAL — uses fabricated area_id suffix (S9-M08)',
        },
        moveTutor: {
            getTutorMoves: 'BROKEN — wrong URL path /api/moves/tutor/* (S9-C01)',
            checkMoveCompatibility: 'BROKEN — non-existent endpoint (S9-C02)',
            teachMove: 'BROKEN — wrong URL + wrong payload (S9-C03)',
            getReminderMoves: 'BROKEN — wrong URL + response format mismatch (S9-H01)',
            useItem_tm: 'BROKEN — newMove.itemId is undefined (S9-H05)',
        },
    };


    // =========================================================================
    // SUMMARY
    // =========================================================================

    const ALL_FINDINGS = [
        ...CRITICAL_FINDINGS,
        ...HIGH_FINDINGS,
        ...MEDIUM_FINDINGS,
        ...LOW_FINDINGS,
    ];

    const SUMMARY = {
        sprint: 9,
        qa_type: 'QA-B (Fishing, Surfing & Move Tutor UI)',
        backend_tests: '1177 passed, 0 failed',
        total_findings: ALL_FINDINGS.length,
        by_severity: {
            CRITICAL: ALL_FINDINGS.filter(f => f.severity === 'CRITICAL').length,
            HIGH: ALL_FINDINGS.filter(f => f.severity === 'HIGH').length,
            MEDIUM: ALL_FINDINGS.filter(f => f.severity === 'MEDIUM').length,
            LOW: ALL_FINDINGS.filter(f => f.severity === 'LOW').length,
        },
        top_issues: [
            'S9-C01-C03: ALL 4 Move Tutor api.js functions call non-existent endpoints (CRITICAL)',
            'S9-C04: Fishing.init() runs before game session — fishing permanently broken (CRITICAL)',
            'S9-C05: Reel mini-game has zero challenge — held-key bypasses mashing (CRITICAL)',
            'S9-H01: Move Reminder wrong URL + response format mismatch (HIGH)',
            'S9-H02: Fish encounters skip Pokedex, transition, stat timing (HIGH)',
            'S9-H05: TM not consumed — itemId always undefined (HIGH)',
            'S9-H08: Surfing state persists through map transitions (HIGH)',
            'S9-H09: fishCaught/movesLearned stats produce NaN (HIGH)',
            'S9-H10: 8 TMs usable without owning them — backend item_id null bypass (HIGH)',
        ],
        verdict: `Sprint 9 introduces fishing and move tutor systems with solid backend
            implementations (1177 tests passing). However, the frontend-backend integration
            is severely broken.

            FISHING: The fishing module has good visual polish (cast animation, bobber bounce,
            reel progress bar) but is completely non-functional because init() runs before a
            game session exists (S9-C04). Even if that is fixed, the reel QTE has zero challenge
            (S9-C05), fish encounters skip Pokedex registration (S9-H02), and fallback fish
            have speciesId: 0 (S9-H03).

            MOVE TUTOR: All 4 api.js functions use wrong URL paths (/api/moves/* instead of
            /api/tutor/*). Every backend call silently 404s and falls back to local data.
            Moves are never persisted, cost is never charged, compatibility is never checked,
            TMs are never consumed. The Move Reminder feature is coded but unreachable
            (no trigger wired). This is the same frontend integration gap pattern flagged
            in Sprints 4, 5, 6, and 8.

            SURFING: Entry/exit mechanics are mostly correct but surfing state persists
            through map transitions (S9-H08), surf encounters are local-only (S9-M08),
            and the type check uses string comparison that misses multi-type Pokemon (S9-M03).

            Priority: Fix S9-C04 first (fishing init timing), then S9-C01-C03 (move tutor
            URL paths). The fishing QTE balance (S9-C05) and TM inventory bypass (S9-H10)
            are also high-priority gameplay issues.`,
    };

    console.log(`Sprint 9 QA-B: ${ALL_FINDINGS.length} findings`);
    console.log(`  CRITICAL: ${SUMMARY.by_severity.CRITICAL}`);
    console.log(`  HIGH:     ${SUMMARY.by_severity.HIGH}`);
    console.log(`  MEDIUM:   ${SUMMARY.by_severity.MEDIUM}`);
    console.log(`  LOW:      ${SUMMARY.by_severity.LOW}`);

    return {
        CRITICAL_FINDINGS,
        HIGH_FINDINGS,
        MEDIUM_FINDINGS,
        LOW_FINDINGS,
        API_AUDIT,
        SUMMARY,
    };
})();
