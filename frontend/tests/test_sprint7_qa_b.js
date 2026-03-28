// Sprint 7 QA-B: Mini-Games, Coins & Prize Exchange — Full Review
// Reviewer: qa-tester-2
// Date: 2026-03-28
// Task: #77
// Scope: Frontend PR #68 (mini-game UI wiring) + Backend PR #65 (mini-game/coin/prize system)
// Modules: frontend/js/minigames.js, frontend/js/api.js,
//          backend services/minigame_service.py, routes/minigame.py, models/minigame.py
//
// Backend tests: 242 passed, 1 FAILED (stale achievement count assertion: expected 12, got 35)
//
// SERVER AUTHORITY VERDICT: Coin balance is server-authoritative. Slot results are
// server-generated. Quiz and memory completion go through backend. However, there are
// significant validation gaps that allow client-side exploitation.

const Sprint7QAB = (() => {

    // =========================================================================
    // SECTION 1: CRITICAL — BUY COINS API COMPLETELY BROKEN
    // =========================================================================

    const CRITICAL_FINDINGS = [
        {
            id: 'MG-C01',
            severity: 'CRITICAL',
            module: 'api.js / routes/minigame.py',
            title: 'Buy Coins API field name mismatch — all packages buy 50 coins',
            description: `api.js line 508 sends { game_id, money_amount: moneyAmount }.
                Backend BuyCoinsRequest model (routes/minigame.py line 24-26) expects
                { game_id, amount }. There is no "money_amount" field in the model.
                Pydantic silently ignores the unknown field and uses amount=1 (default).
                Result: regardless of which package the player picks ($1000/$2000/$5000),
                they always buy exactly 1 package (50 coins for $1000). The $2000/100-coin
                and $5000/250-coin packages are completely broken.`,
            impact: 'Players cannot buy $2000 or $5000 coin packages.',
            fix: 'api.js should send { game_id, amount: packageCount } or backend should accept money_amount.',
        },
    ];


    // =========================================================================
    // SECTION 2: HIGH — SECURITY & VALIDATION GAPS
    // =========================================================================

    const HIGH_FINDINGS = [
        {
            id: 'MG-H01',
            severity: 'HIGH',
            module: 'routes/minigame.py / models/minigame.py',
            title: 'Quiz answers leaked to client — correct_index in start response',
            description: `QuizQuestion model (models/minigame.py line 46-50) includes
                correct_index. Route line 106 returns session.model_dump() which
                serializes all correct answers. A player can open browser dev tools,
                read the correct_index for all 10 questions, and submit a perfect
                score every time. Frontend does not use correct_index for local grading
                but the data exposure is a trivial exploit.`,
            impact: 'Quiz can be cheated for guaranteed 50 coins per round.',
            fix: 'Exclude correct_index from the response: return only question text and options.',
        },
        {
            id: 'MG-H02',
            severity: 'HIGH',
            module: 'minigame_service.py',
            title: 'Memory game time not validated against server clock — fake instant completion',
            description: `Server records start_time = time.time() on session start (line 228)
                but on completion (line 252-263), validates client-provided time_seconds
                against max_time only — never compares against actual elapsed time.
                A client can start a session, immediately call /memory/complete with
                time_seconds=1 and pairs_matched=max to claim maximum reward (2x time
                bonus). The start_time is stored but never used.`,
            impact: 'Memory game can be farmed for max coins with zero gameplay.',
            fix: 'Validate: actual_elapsed = time.time() - start_time; reject if time_seconds < actual_elapsed * 0.8',
        },
        {
            id: 'MG-H03',
            severity: 'HIGH',
            module: 'minigames.js / minigame_service.py',
            title: 'Memory game pair count mismatch — easy/hard completions rejected',
            description: `Frontend generates: easy=8 pairs (4x4=16 cards), hard=12 pairs
                (6x4=24 cards). Backend expects: easy=6 pairs, hard=15 pairs.
                When frontend reports pairs_matched=8 for easy, server validation at
                line 271 (if pairs_matched > cfg["pairs"]) rejects it as invalid
                because 8 > 6. Similarly, hard completions with 12 pairs are rejected
                because 12 < 15 means incomplete, and 12 > 15 is false so it passes
                but rewards are reduced (12/15 = 80% of base).`,
            impact: 'Easy memory game always fails validation. Hard gives reduced rewards.',
            fix: 'Align pair counts: frontend should use backend values (6/10/15) or vice versa.',
        },
        {
            id: 'MG-H04',
            severity: 'HIGH',
            module: 'minigame_service.py',
            title: 'Prize Pokemon silently dropped when team is full — coins still deducted',
            description: `_add_prize_pokemon (line 545-547): if len(team) < 6, append;
                else silently skip. Coins are deducted at line 494 before the Pokemon
                is added. RedeemResult says success=True with message "Redeemed Porygon!"
                but the Pokemon is gone. No PC box fallback. No error to the player.`,
            impact: 'Players lose coins and receive nothing; no indication of failure.',
            fix: 'Check team size before deducting coins. Add PC box fallback or return error.',
        },
    ];


    // =========================================================================
    // SECTION 3: MEDIUM — GAMEPLAY & BALANCE ISSUES
    // =========================================================================

    const MEDIUM_FINDINGS = [
        {
            id: 'MG-M01',
            severity: 'MEDIUM',
            module: 'minigames.js / minigame_service.py',
            title: 'Quiz perfect bonus displayed but never awarded by server',
            description: `Frontend line 802 displays quizScore * 5 + (quizScore === quizTotal ? 50 : 0)
                showing a 50-coin bonus for perfect scores. Backend line 450 only awards
                score * 5 with no perfect bonus. Players see "75 coins!" but receive 50.`,
            impact: 'Misleading reward display; players think they earned more than they did.',
        },
        {
            id: 'MG-M02',
            severity: 'MEDIUM',
            module: 'minigames.js',
            title: 'Local quiz fallback awards coins client-side only',
            description: `Lines 194-200: If backend quiz start fails, falls back to local
                QUIZ_BANK with 5 questions. Lines 252-254: local fallback does
                coins += reward — client-side only, never persisted. Coins are phantom
                until next syncCoins() overwrites them.`,
            impact: 'Phantom coin balance when backend is unavailable.',
        },
        {
            id: 'MG-M03',
            severity: 'MEDIUM',
            module: 'minigame_service.py',
            title: 'No upper bound on coin purchase amount',
            description: `buy_coins accepts any amount >= 1 with no cap. A client can send
                amount=999999 to buy arbitrarily many coins in one request (as long as
                they have money). No coin wallet cap exists (original games cap at 9999).`,
            impact: 'Balance issue — no limit on coin hoarding.',
        },
        {
            id: 'MG-M04',
            severity: 'MEDIUM',
            module: 'minigame_service.py',
            title: 'No cooldown on memory game — farmable with no rate limit',
            description: `Slots have a 100/hour rate limit. Memory and quiz have none.
                Combined with MG-H02 (instant completion exploit), a bot could farm
                coins from memory game indefinitely.`,
            impact: 'Coin farming exploit via memory game.',
        },
        {
            id: 'MG-M05',
            severity: 'MEDIUM',
            module: 'minigame_service.py',
            title: 'Detached list bug in _add_prize_pokemon and _add_prize_item',
            description: `Lines 545, 556: player.get("team", []) and player.get("inventory", [])
                return new empty lists if key is missing. Appending to these detached
                lists does not modify the player dict. In practice, all players have
                these keys from creation, but a corrupted state could trigger silent
                data loss.`,
            impact: 'Latent bug — prizes could vanish in edge cases.',
        },
    ];


    // =========================================================================
    // SECTION 4: LOW — POLISH & MINOR ISSUES
    // =========================================================================

    const LOW_FINDINGS = [
        {
            id: 'MG-L01',
            severity: 'LOW',
            module: 'minigames.js',
            title: 'No payout table shown to player in slot machine UI',
            description: `Payout combinations and multipliers are server-side only.
                The slot machine UI shows reels and results but never displays what
                combinations pay what. Players have no way to know the odds.`,
            impact: 'UX — players gamble blind.',
        },
        {
            id: 'MG-L02',
            severity: 'LOW',
            module: 'minigames.js',
            title: 'Slot offline fallback creates local-only coin deduction',
            description: `Lines 335-341: On API failure, client deducts coins locally
                and shows a guaranteed loss. Stale until next syncCoins().`,
            impact: 'Temporary display mismatch.',
        },
        {
            id: 'MG-L03',
            severity: 'LOW',
            module: 'minigame_service.py',
            title: 'Double match does not recognize reel[0]==reel[2] pattern',
            description: `Line 201: Only checks reels[0]==reels[1] or reels[1]==reels[2].
                First+third match with different middle returns 0 payout. May be
                intentional (classic slot rules) but is undocumented.`,
            impact: 'Player expectation mismatch.',
        },
        {
            id: 'MG-L04',
            severity: 'LOW',
            module: 'minigame_service.py',
            title: 'Quiz sessions never expire — memory leak on abandoned sessions',
            description: `_quiz_sessions dict never cleaned up. Abandoned sessions persist
                in memory until server restart.`,
            impact: 'Minor memory leak over time.',
        },
        {
            id: 'MG-L05',
            severity: 'LOW',
            module: 'routes/minigame.py',
            title: 'All POST routes return same generic error for different failures',
            description: `Insufficient coins, invalid bet, rate limited, game not found
                all return the same HTTP 400 message. Client cannot distinguish error causes.`,
            impact: 'Debugging difficulty; poor error UX.',
        },
        {
            id: 'MG-L06',
            severity: 'LOW',
            module: 'minigame_service.py',
            title: 'No duplicate prize Pokemon protection',
            description: `A player can redeem the same prize Pokemon multiple times (e.g.,
                3 Porygons). Differs from original Game Corner one-per-save rule.`,
            impact: 'Design question — may be intentional.',
        },
        {
            id: 'MG-L07',
            severity: 'LOW',
            module: 'models/minigame.py',
            title: 'Duplicate MemoryCompleteRequest model and unused SlotSymbol model',
            description: `MemoryCompleteRequest defined in both models/minigame.py (line 31)
                and routes/minigame.py (line 67). SlotSymbol model (line 18) never used.`,
            impact: 'Dead code.',
        },
    ];


    // =========================================================================
    // SECTION 5: BACKEND TEST FAILURE
    // =========================================================================

    const TEST_FINDINGS = [
        {
            id: 'MG-T01',
            severity: 'MEDIUM',
            module: 'tests/test_leaderboard.py',
            title: 'Stale achievement count assertion — expected 12, got 35',
            description: `test_initial_achievements_all_incomplete (line 191) asserts
                len(achs) == 12. Sprint 7 added more achievements, bringing total to 35.
                Test needs updating. 242 tests pass, 1 fails.`,
            impact: 'CI red — stale test assertion.',
        },
    ];


    // =========================================================================
    // SECTION 6: SERVER AUTHORITY ASSESSMENT
    // =========================================================================

    const SERVER_AUTHORITY = {
        coin_balance: 'PASS — fetched from API.getCoins(), updated from result.coins_after',
        slot_machine: 'PASS — reels generated server-side, payout calculated server-side',
        memory_match: 'PARTIAL — completion validated but time is client-trusted (MG-H02)',
        quiz: 'PARTIAL — graded server-side but answers leaked in start response (MG-H01)',
        prize_exchange: 'PASS — coin deduction and delivery server-side',
        overall: `Server-authoritative for coins and slots. Memory and quiz have exploitable
            validation gaps that allow farming (instant memory completion, leaked quiz answers).`,
    };


    // =========================================================================
    // SUMMARY
    // =========================================================================

    const ALL_FINDINGS = [
        ...CRITICAL_FINDINGS,
        ...HIGH_FINDINGS,
        ...MEDIUM_FINDINGS,
        ...LOW_FINDINGS,
        ...TEST_FINDINGS,
    ];

    const SUMMARY = {
        sprint: 7,
        qa_type: 'QA-B (Mini-Games, Coins & Prize Exchange)',
        backend_tests: '242 passed, 1 failed (stale achievement count)',
        total_findings: ALL_FINDINGS.length,
        by_severity: {
            CRITICAL: ALL_FINDINGS.filter(f => f.severity === 'CRITICAL').length,
            HIGH: ALL_FINDINGS.filter(f => f.severity === 'HIGH').length,
            MEDIUM: ALL_FINDINGS.filter(f => f.severity === 'MEDIUM').length,
            LOW: ALL_FINDINGS.filter(f => f.severity === 'LOW').length,
        },
        top_issues: [
            'MG-C01: Buy Coins API field mismatch — $2000/$5000 packages broken (CRITICAL)',
            'MG-H01: Quiz answers leaked to client — trivial cheating (HIGH)',
            'MG-H02: Memory game time not server-validated — instant completion exploit (HIGH)',
            'MG-H03: Memory pair count mismatch — easy fails, hard reduced rewards (HIGH)',
            'MG-H04: Prize Pokemon dropped when team full — coins lost (HIGH)',
        ],
        server_authority_verdict: `Coins: PASS. Slots: PASS. Memory: PARTIAL (time exploit).
            Quiz: PARTIAL (answer leak). Prizes: PASS. Overall architecture is sound —
            the issues are validation gaps, not architectural.`,
        verdict: `The mini-game system has a solid server-authoritative architecture for
            coins and slot machine. However, 1 CRITICAL field name mismatch breaks the
            coin purchase flow, and 4 HIGH issues create exploitable gaps in quiz
            (answer leak), memory game (time faking), and prize exchange (team-full loss).
            The CRITICAL buy-coins bug should be a 1-line fix. The quiz answer leak and
            memory time validation are the most impactful security issues.`,
    };

    console.log(`Sprint 7 QA-B: ${ALL_FINDINGS.length} findings`);
    console.log(`  CRITICAL: ${SUMMARY.by_severity.CRITICAL}`);
    console.log(`  HIGH:     ${SUMMARY.by_severity.HIGH}`);
    console.log(`  MEDIUM:   ${SUMMARY.by_severity.MEDIUM}`);
    console.log(`  LOW:      ${SUMMARY.by_severity.LOW}`);

    return {
        CRITICAL_FINDINGS,
        HIGH_FINDINGS,
        MEDIUM_FINDINGS,
        LOW_FINDINGS,
        TEST_FINDINGS,
        SERVER_AUTHORITY,
        SUMMARY,
    };
})();
