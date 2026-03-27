// achievements.js — Achievement tracking & popup notifications

const Achievements = (() => {
    // Achievement definitions
    const ACHIEVEMENTS = [
        { id: 'first_catch',     name: 'First Catch!',        desc: 'Catch your first wild Pokemon',     check: s => s.pokemonCaught >= 1 },
        { id: 'catch_10',        name: 'Pokemon Collector',   desc: 'Catch 10 Pokemon',                  check: s => s.pokemonCaught >= 10 },
        { id: 'catch_50',        name: 'Pokemon Master',      desc: 'Catch 50 Pokemon',                  check: s => s.pokemonCaught >= 50 },
        { id: 'first_win',       name: 'First Victory',       desc: 'Win your first battle',             check: s => s.battlesWon >= 1 },
        { id: 'win_10',          name: 'Battle Veteran',      desc: 'Win 10 battles',                    check: s => s.battlesWon >= 10 },
        { id: 'win_50',          name: 'Battle Legend',        desc: 'Win 50 battles',                    check: s => s.battlesWon >= 50 },
        { id: 'badge_1',         name: 'Badge Collector',     desc: 'Earn your first gym badge',         check: s => s.badges >= 1 },
        { id: 'badge_4',         name: 'Halfway There',       desc: 'Earn 4 gym badges',                 check: s => s.badges >= 4 },
        { id: 'badge_8',         name: 'Pokemon Champion',    desc: 'Earn all 8 gym badges',             check: s => s.badges >= 8 },
        { id: 'trainer_1',       name: 'Rival Defeated',      desc: 'Defeat your first trainer',         check: s => s.trainersDefeated >= 1 },
        { id: 'trainer_10',      name: 'Trainer Crusher',     desc: 'Defeat 10 trainers',                check: s => s.trainersDefeated >= 10 },
        { id: 'evolve_1',        name: 'Evolution!',          desc: 'Evolve a Pokemon for the first time', check: s => s.pokemonEvolved >= 1 },
        { id: 'steps_1000',      name: 'Adventurer',          desc: 'Walk 1,000 steps',                  check: s => s.steps >= 1000 },
        { id: 'steps_10000',     name: 'World Traveler',      desc: 'Walk 10,000 steps',                 check: s => s.steps >= 10000 },
        { id: 'pokedex_50',      name: 'Pokedex: 50%',        desc: 'See 50% of all Pokemon',            check: s => s.pokemonSeen >= 75 },
    ];

    // Earned achievement IDs
    const earned = new Set();

    // Popup queue
    const popupQueue = [];
    let currentPopup = null;
    let popupTimer = 0;
    const POPUP_DURATION = 3000;
    const POPUP_SLIDE = 300;

    function checkAchievements() {
        const stats = typeof PlayerStats !== 'undefined' ? PlayerStats.getStats() : {};
        const badges = typeof BadgeCase !== 'undefined' ? BadgeCase.getBadgeCount() : 0;

        const checkData = { ...stats, badges };

        for (const ach of ACHIEVEMENTS) {
            if (earned.has(ach.id)) continue;
            if (ach.check(checkData)) {
                earned.add(ach.id);
                popupQueue.push(ach);
            }
        }
    }

    function update(dt) {
        // Process popup queue
        if (currentPopup) {
            popupTimer += dt;
            if (popupTimer >= POPUP_DURATION) {
                currentPopup = null;
                popupTimer = 0;
            }
        } else if (popupQueue.length > 0) {
            currentPopup = popupQueue.shift();
            popupTimer = 0;
        }
    }

    function renderPopup(ctx, canvasW, canvasH) {
        if (!currentPopup) return;

        // Slide in from top
        let slideY;
        if (popupTimer < POPUP_SLIDE) {
            slideY = -60 + (60 * (popupTimer / POPUP_SLIDE));
        } else if (popupTimer > POPUP_DURATION - POPUP_SLIDE) {
            const fadeOut = (popupTimer - (POPUP_DURATION - POPUP_SLIDE)) / POPUP_SLIDE;
            slideY = -60 * fadeOut;
        } else {
            slideY = 0;
        }

        const popW = 300;
        const popH = 50;
        const px = (canvasW - popW) / 2;
        const py = 8 + slideY;

        // Background
        ctx.fillStyle = 'rgba(20, 40, 20, 0.92)';
        ctx.fillRect(px, py, popW, popH);
        ctx.strokeStyle = '#f8d830';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, popW, popH);

        // Star icon
        ctx.fillStyle = '#f8d830';
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'left';
        ctx.fillText('*', px + 10, py + 28);

        // Achievement name
        ctx.fillStyle = '#f8d830';
        ctx.font = 'bold 13px monospace';
        ctx.fillText(currentPopup.name, px + 30, py + 20);

        // Description
        ctx.fillStyle = '#a0c0a0';
        ctx.font = '10px monospace';
        ctx.fillText(currentPopup.desc, px + 30, py + 38);

        // "Achievement Unlocked" label
        ctx.fillStyle = '#809080';
        ctx.font = '8px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('Achievement!', px + popW - 8, py + 14);

        ctx.textAlign = 'left';
    }

    // Render achievement list (for Trainer Card back or separate screen)
    function renderList(ctx, cx, cy, w, h) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
        ctx.fillRect(cx, cy, w, h);
        ctx.strokeStyle = '#f8d830';
        ctx.lineWidth = 2;
        ctx.strokeRect(cx, cy, w, h);

        ctx.fillStyle = '#f8d830';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Achievements', cx + w / 2, cy + 20);

        const lineH = 22;
        const startY = cy + 34;

        for (let i = 0; i < ACHIEVEMENTS.length; i++) {
            const ach = ACHIEVEMENTS[i];
            const y = startY + i * lineH;
            if (y + lineH > cy + h - 10) break;

            const isEarned = earned.has(ach.id);

            // Checkbox
            ctx.fillStyle = isEarned ? '#48c048' : '#404040';
            ctx.fillRect(cx + 10, y, 14, 14);
            if (isEarned) {
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 10px monospace';
                ctx.textAlign = 'center';
                ctx.fillText('V', cx + 17, y + 12);
            }

            // Name
            ctx.fillStyle = isEarned ? '#c0e0c0' : '#606060';
            ctx.font = '11px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(ach.name, cx + 30, y + 12);

            // Description
            ctx.fillStyle = isEarned ? '#809080' : '#404040';
            ctx.font = '9px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(ach.desc, cx + w - 10, y + 12);
        }

        // Count
        ctx.fillStyle = '#809080';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${earned.size} / ${ACHIEVEMENTS.length}`, cx + w / 2, cy + h - 10);

        ctx.textAlign = 'left';
    }

    function getEarnedCount() { return earned.size; }
    function getTotalCount() { return ACHIEVEMENTS.length; }
    function isEarned(id) { return earned.has(id); }

    return {
        checkAchievements, update, renderPopup, renderList,
        getEarnedCount, getTotalCount, isEarned,
    };
})();
