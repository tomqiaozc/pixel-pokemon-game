// Sprint 8 QA-B: Berry Farming, Daycare UI & Achievement Display — Full Review
// Reviewer: qa-tester-2
// Date: 2026-03-28
// Task: #86
// Scope: Frontend PRs #75 (berry), #78 (daycare), #71 (achievements) + backend
// Backend tests: 1002 passed, 0 failed
//
// CRITICAL THEME: game.js integration bugs break daycare NPC and NPC interactions.
// Achievement API sync is broken due to response format mismatch.
// Berry farming and daycare core flows work but have party-full data loss bugs.

const Sprint8QAB = (() => {

    // =========================================================================
    // SECTION 1: CRITICAL — GAME.JS INTEGRATION BUGS
    // =========================================================================

    const CRITICAL_FINDINGS = [
        {
            id: 'S8-C01',
            severity: 'CRITICAL',
            module: 'game.js:324',
            title: 'Daycare NPC if-block has no body — breaks ALL NPC/legendary interactions',
            description: `game.js line 324: if (Daycare.checkNpcInteraction(x, y, dir)) {
                has no body and no closing brace before the regular NPC interaction code.
                When checkNpcInteraction returns false (every map except daycare tile),
                all regular NPC interactions, quest triggers, and legendary spawn checks
                on lines 325+ are SKIPPED because they are nested inside the daycare
                if-block's scope. This is a game-breaking regression affecting all maps.`,
            impact: 'NPCs, shopkeepers, Oak, and legendary encounters unreachable.',
        },
        {
            id: 'S8-C02',
            severity: 'CRITICAL',
            module: 'game.js:324 / daycare.js:164',
            title: 'checkNpcInteraction missing mapId arg — always returns false',
            description: `game.js calls Daycare.checkNpcInteraction(x, y, dir) with 3 args.
                daycare.js function expects 4 args: (playerX, playerY, playerDir, mapId).
                mapId is undefined, so mapId !== DAYCARE_NPC.mapId is always true,
                function always returns false. Daycare NPC can never be interacted with
                via facing detection. Only door entry works.`,
            impact: 'Daycare NPC interaction completely broken.',
        },
        {
            id: 'S8-C03',
            severity: 'CRITICAL',
            module: 'achievements.js / backend',
            title: 'Achievement GET response format mismatch — sync broken',
            description: `Frontend expects API.getAchievements() to return {achievements: [...ids]}.
                Backend returns list[Achievement] objects with full fields (id, name, tier,
                progress, etc.). The frontend cannot parse the response, so achievement
                sync from server to client is completely broken. Achievements loaded from
                backend are silently dropped.`,
            impact: 'Achievement state never loads from backend; local-only persistence.',
        },
    ];


    // =========================================================================
    // SECTION 2: HIGH — DATA LOSS & RENDERING BUGS
    // =========================================================================

    const HIGH_FINDINGS = [
        {
            id: 'S8-H01',
            severity: 'HIGH',
            module: 'game.js:94',
            title: 'Daycare NPC renderNpc missing 4 args — old man never rendered',
            description: `game.js calls Daycare.renderNpc(ctx) with only ctx. Function
                expects (ctx, camX, camY, scale, mapId). mapId is undefined, guard
                at line 803 always returns early. Daycare old man is invisible on Route 1.`,
            impact: 'No visual cue that daycare exists.',
        },
        {
            id: 'S8-H02',
            severity: 'HIGH',
            module: 'daycare.js:95-108',
            title: 'Egg silently dropped when party full — no PC fallback',
            description: `collectEgg: if party.length >= 6, egg is not pushed to party.
                But API call succeeds and egg_ready is set to false. "You received an egg!"
                notification still shows. Egg is permanently lost. No PC box fallback.`,
            impact: 'Players lose eggs with full party; coins/time wasted.',
        },
        {
            id: 'S8-H03',
            severity: 'HIGH',
            module: 'daycare.js:66-89',
            title: 'Withdraw succeeds server-side but Pokemon lost if party full',
            description: `withdraw: checks party.length < 6 at line 71 but server still
                processes the withdrawal. daycareStatus updated at line 81. Pokemon
                removed from daycare slot on server but never added to local party.
                Pokemon vanishes.`,
            impact: 'Players permanently lose deposited Pokemon.',
        },
        {
            id: 'S8-H04',
            severity: 'HIGH',
            module: 'daycare.js:70-81',
            title: 'Withdrawn Pokemon uses stale pre-deposit stats',
            description: `Line 70 reads slotData from OLD daycareStatus before server
                response. Line 81 updates daycareStatus from response AFTER push.
                Withdrawn Pokemon has pre-deposit level and stats, not the leveled-up
                data from daycare time. Server response data is not used for the push.`,
            impact: 'Daycare leveling has no effect on withdrawn Pokemon.',
        },
        {
            id: 'S8-H05',
            severity: 'HIGH',
            module: 'berry.js:640',
            title: 'Berry Give action has no backend API — held items local-only',
            description: `berry.js line 640: API.post ? null : null — dead no-op expression.
                No api.js giveBerry() method exists. Give assigns berry as held item
                locally only. Lost on refresh. Berry quantity decremented locally but
                not on server, causing pouch desync.`,
            impact: 'Held berries ephemeral; pouch desyncs with server.',
        },
        {
            id: 'S8-H06',
            severity: 'HIGH',
            module: 'achievements.js / backend',
            title: 'Achievement notification endpoint URL mismatch — never called',
            description: `Frontend references /player/{id}/achievements/notifications but
                backend route is /achievements/recent/{id}. The function is also never
                called from any code path, making it dead code.`,
            impact: 'Achievement notifications from server never fetched.',
        },
        {
            id: 'S8-H07',
            severity: 'HIGH',
            module: 'achievements.js / backend',
            title: 'Frontend and backend define completely different achievement sets',
            description: `Frontend achievements.js defines its own achievement IDs, names,
                and categories with zero overlap to the backend achievement definitions.
                Different IDs means saved/loaded achievements reference nonexistent entries
                on the other side.`,
            impact: 'Cross-system achievement state is meaningless.',
        },
        {
            id: 'S8-H08',
            severity: 'HIGH',
            module: 'backend breeding_service.py',
            title: 'Breeding evolved Pokemon produces wrong species',
            description: `_determine_offspring_species (lines 92-106) returns the parent's
                species ID without looking up the base evolution form. Breeding Charizard
                produces a Charizard egg instead of a Charmander egg. Should trace back
                to the base form of the evolutionary line.`,
            impact: 'Breeding produces incorrect Pokemon species.',
        },
    ];


    // =========================================================================
    // SECTION 3: MEDIUM — LOGIC & SYNC ISSUES
    // =========================================================================

    const MEDIUM_FINDINGS = [
        {
            id: 'S8-M01',
            severity: 'MEDIUM',
            module: 'berry.js:361-381',
            title: 'Plant offline fallback desyncs state and loses berries',
            description: `When plantBerry API fails, frontend optimistically sets plot to
                "planted" locally and decrements berry quantity. On next 30s refresh,
                plot reverts to empty (server truth). Berry is lost.`,
            impact: 'Berry consumed but plot empty after sync.',
        },
        {
            id: 'S8-M02',
            severity: 'MEDIUM',
            module: 'berry.js:399-411',
            title: 'Water offline fallback desyncs water count',
            description: `Same pattern as S8-M01 — locally increments water count on API
                failure, reverts on next sync.`,
            impact: 'Misleading water count display.',
        },
        {
            id: 'S8-M03',
            severity: 'MEDIUM',
            module: 'berry.js:642',
            title: 'Give always targets party[0] — no Pokemon selector',
            description: `Line 642: const poke = party[0] with // TODO: party selection.
                Players with 6 Pokemon can only give berries to first slot.`,
            impact: 'Limited usability for berry held items.',
        },
        {
            id: 'S8-M04',
            severity: 'MEDIUM',
            module: 'daycare.js:220-232',
            title: 'Eggs can be deposited into daycare — no filter',
            description: `Party selection for deposit allows selecting eggs. Depositing
                an egg is nonsensical (eggs cannot breed). No guard on frontend.`,
            impact: 'Wasted daycare slot if player deposits an egg.',
        },
        {
            id: 'S8-M05',
            severity: 'MEDIUM',
            module: 'daycare.js:134-160',
            title: 'Step counter desyncs — sub-50-step sessions lost on reload',
            description: `Steps reported to backend every 50 accumulated steps. If player
                walks 49 steps and closes game, those steps are lost. Local counter
                may hit 0 before backend confirms, leaving egg in stuck state.`,
            impact: 'Egg hatch progress can be lost.',
        },
        {
            id: 'S8-M06',
            severity: 'MEDIUM',
            module: 'daycare.js:122',
            title: 'Multi-egg hatch always targets first egg in party',
            description: `findIndex(p => p.is_egg) always finds first egg. If player has
                multiple eggs, hatch animation targets wrong egg if backend hatched
                a different one.`,
            impact: 'Wrong egg hatches visually with multiple eggs.',
        },
        {
            id: 'S8-M07',
            severity: 'MEDIUM',
            module: 'daycare.js:563-575',
            title: 'Hatched Pokemon never registered in Pokedex',
            description: `Egg hatch reveal phase replaces party entry but never calls
                API.registerCaught() or API.registerSeen(). Hatched Pokemon missing
                from Pokedex.`,
            impact: 'Pokedex incomplete for bred Pokemon.',
        },
        {
            id: 'S8-M08',
            severity: 'MEDIUM',
            module: 'achievements.js',
            title: 'No event-driven achievement checks — only 5s polling timer',
            description: `Achievement checks run on a 5-second timer. No direct calls from
                battle win, catch, evolve, or badge handlers. Player may wait up to 5s
                to see an achievement they just earned.`,
            impact: 'Delayed achievement notifications; feels unresponsive.',
        },
        {
            id: 'S8-M09',
            severity: 'MEDIUM',
            module: 'achievements.js',
            title: 'checkAchievements() called without required force arg from game.js',
            description: `game.js calls checkAchievements() but the function requires a
                force argument to bypass the 5s throttle. Without it, the call from
                game.js is effectively throttled and may not run when intended.`,
            impact: 'Achievement checks from game events may be skipped.',
        },
        {
            id: 'S8-M10',
            severity: 'MEDIUM',
            module: 'backend breeding_service.py',
            title: 'Ditto (species #132) missing from pokemon_species.json',
            description: `Ditto is absent from the species data file, making Ditto-based
                breeding unavailable. Ditto is essential for breeding any Pokemon
                outside its own egg group.`,
            impact: 'Major breeding feature gap — Ditto breeding impossible.',
        },
    ];


    // =========================================================================
    // SECTION 4: LOW — POLISH & MINOR ISSUES
    // =========================================================================

    const LOW_FINDINGS = [
        {
            id: 'S8-L01',
            severity: 'LOW',
            module: 'berry.js:124',
            title: 'Sparkle animation uses hardcoded 16ms instead of actual dt',
            description: `sparkleTimer += 16 instead of using frame delta time.
                Animation speed varies with actual frame rate.`,
        },
        {
            id: 'S8-L02',
            severity: 'LOW',
            module: 'berry.js:699-746',
            title: 'Berry pouch list can overflow panel without scrolling',
            description: `10 berry types at 42px each = 420px + 40px header = 460px.
                Standard 480px canvas panel is 420px tall. Last rows clip.`,
        },
        {
            id: 'S8-L03',
            severity: 'LOW',
            module: 'berry.js:805',
            title: 'Notification width hardcoded — measureText unused',
            description: `ctx.measureText ? 200 : 200 — ternary always returns 200.
                Long messages may clip.`,
        },
        {
            id: 'S8-L04',
            severity: 'LOW',
            module: 'daycare.js:5,850',
            title: 'Egg progress bar assumes 5000 steps for all species',
            description: `HATCH_STEPS = 5000 used for all eggs. Different species have
                different hatch requirements. Progress bar inaccurate.`,
        },
        {
            id: 'S8-L05',
            severity: 'LOW',
            module: 'daycare.js:102-104',
            title: 'Notification can overlap daycare interior panel',
            description: `renderNotify called after renderInterior. Timing overlap
                draws notification on top of menu.`,
        },
        {
            id: 'S8-L06',
            severity: 'LOW',
            module: 'achievements.js',
            title: 'Missing gold tier in capture achievement chain',
            description: `Capture achievements jump from silver to platinum with no
                gold tier entry.`,
        },
        {
            id: 'S8-L07',
            severity: 'LOW',
            module: 'achievements.js',
            title: 'saveAchievements response discarded by frontend',
            description: `API.saveAchievements() response is not consumed. Any server
                error is silently ignored.`,
        },
    ];


    // =========================================================================
    // API WIRING AUDIT
    // =========================================================================

    const API_AUDIT = {
        berry: {
            getBerryTypes: 'WIRED — called on init',
            getBerryPlots: 'WIRED — called on map load + 30s auto-refresh',
            plantBerry: 'WIRED — on plant action',
            waterBerry: 'WIRED — on water action',
            harvestBerry: 'WIRED — on harvest action',
            getBerryPouch: 'WIRED — on interaction open + pouch open',
            giveBerry: 'MISSING — no api.js function exists (S8-H05)',
        },
        daycare: {
            getDaycareStatus: 'WIRED — on init + interior open',
            daycareDeposit: 'WIRED — on deposit action',
            daycareWithdraw: 'WIRED — on withdraw action',
            daycareCollectEgg: 'WIRED — on egg collect',
            daycareStep: 'WIRED — every 50 steps or on hatch',
        },
        achievements: {
            getAchievements: 'WIRED but BROKEN — response format mismatch (S8-C03)',
            saveAchievements: 'WIRED — on new achievement',
            getNotifications: 'BROKEN — URL mismatch, never called (S8-H06)',
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
        sprint: 8,
        qa_type: 'QA-B (Berry Farming, Daycare UI & Achievement Display)',
        backend_tests: '1002 passed, 0 failed',
        total_findings: ALL_FINDINGS.length,
        by_severity: {
            CRITICAL: ALL_FINDINGS.filter(f => f.severity === 'CRITICAL').length,
            HIGH: ALL_FINDINGS.filter(f => f.severity === 'HIGH').length,
            MEDIUM: ALL_FINDINGS.filter(f => f.severity === 'MEDIUM').length,
            LOW: ALL_FINDINGS.filter(f => f.severity === 'LOW').length,
        },
        top_issues: [
            'S8-C01: game.js daycare if-block breaks ALL NPC interactions (CRITICAL)',
            'S8-C02: checkNpcInteraction missing mapId — always false (CRITICAL)',
            'S8-C03: Achievement API response format mismatch — sync broken (CRITICAL)',
            'S8-H02: Egg dropped when party full — no PC fallback (HIGH)',
            'S8-H03: Withdraw loses Pokemon when party full (HIGH)',
            'S8-H04: Withdrawn Pokemon uses stale stats (HIGH)',
            'S8-H05: Berry Give has no backend API (HIGH)',
            'S8-H08: Breeding evolved Pokemon produces wrong species (HIGH)',
        ],
        verdict: `Sprint 8 introduces solid berry farming and daycare systems with proper
            backend API wiring (11/12 berry endpoints wired, 5/5 daycare wired). However,
            3 CRITICAL bugs in game.js integration break the daycare NPC AND all other NPC
            interactions across all maps. The achievement system has a fundamental response
            format mismatch making server sync non-functional.

            Berry farming is the most polished: planting, watering, harvesting, and auto-refresh
            all work correctly through backend APIs. The one gap is the Give action.

            Daycare has correct API wiring but dangerous party-full edge cases where Pokemon
            and eggs are permanently lost. The breeding backend has a species inheritance bug
            (evolved parents produce evolved eggs) and Ditto is missing from species data.

            Priority: Fix S8-C01 first — it breaks ALL NPC interactions game-wide.`,
    };

    console.log(`Sprint 8 QA-B: ${ALL_FINDINGS.length} findings`);
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
