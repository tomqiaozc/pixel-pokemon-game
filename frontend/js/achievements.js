// achievements.js — Achievement tracking, medal tiers, progress bars & popup notifications

const Achievements = (() => {
    // Medal tier thresholds — achievements with progressive tiers
    const MEDAL_TIERS = {
        bronze:   { color: '#cd7f32', label: 'Bronze',   icon: 'B' },
        silver:   { color: '#c0c0c0', label: 'Silver',   icon: 'S' },
        gold:     { color: '#ffd700', label: 'Gold',     icon: 'G' },
        platinum: { color: '#e5e4e2', label: 'Platinum', icon: 'P' },
    };

    // Achievement categories
    const CATEGORIES = {
        battle:    { name: 'Battle',    color: '#e04040' },
        capture:   { name: 'Capture',   color: '#e05040' },
        explore:   { name: 'Explore',   color: '#40a040' },
        collect:   { name: 'Collect',   color: '#6890f0' },
        training:  { name: 'Training',  color: '#f8d030' },
    };

    // Full achievement definitions with progress tracking
    const ACHIEVEMENTS = [
        // Battle achievements
        { id: 'first_win',       name: 'First Victory',       desc: 'Win your first battle',
          category: 'battle', tier: null, check: s => s.battlesWon >= 1, progress: s => Math.min(1, s.battlesWon), target: 1 },
        { id: 'win_10',          name: 'Battle Veteran',      desc: 'Win 10 battles',
          category: 'battle', tier: 'bronze', check: s => s.battlesWon >= 10, progress: s => Math.min(10, s.battlesWon), target: 10 },
        { id: 'win_50',          name: 'Battle Expert',       desc: 'Win 50 battles',
          category: 'battle', tier: 'silver', check: s => s.battlesWon >= 50, progress: s => Math.min(50, s.battlesWon), target: 50 },
        { id: 'win_100',         name: 'Battle Legend',        desc: 'Win 100 battles',
          category: 'battle', tier: 'gold', check: s => s.battlesWon >= 100, progress: s => Math.min(100, s.battlesWon), target: 100 },
        { id: 'win_500',         name: 'Battle God',           desc: 'Win 500 battles',
          category: 'battle', tier: 'platinum', check: s => s.battlesWon >= 500, progress: s => Math.min(500, s.battlesWon), target: 500 },
        { id: 'trainer_1',       name: 'Rival Defeated',       desc: 'Defeat your first trainer',
          category: 'battle', tier: null, check: s => s.trainersDefeated >= 1, progress: s => Math.min(1, s.trainersDefeated), target: 1 },
        { id: 'trainer_10',      name: 'Trainer Crusher',      desc: 'Defeat 10 trainers',
          category: 'battle', tier: 'bronze', check: s => s.trainersDefeated >= 10, progress: s => Math.min(10, s.trainersDefeated), target: 10 },

        // Capture achievements
        { id: 'first_catch',     name: 'First Catch!',         desc: 'Catch your first wild Pokemon',
          category: 'capture', tier: null, check: s => s.pokemonCaught >= 1, progress: s => Math.min(1, s.pokemonCaught), target: 1 },
        { id: 'catch_10',        name: 'Pokemon Collector',    desc: 'Catch 10 Pokemon',
          category: 'capture', tier: 'bronze', check: s => s.pokemonCaught >= 10, progress: s => Math.min(10, s.pokemonCaught), target: 10 },
        { id: 'catch_50',        name: 'Pokemon Hunter',       desc: 'Catch 50 Pokemon',
          category: 'capture', tier: 'silver', check: s => s.pokemonCaught >= 50, progress: s => Math.min(50, s.pokemonCaught), target: 50 },
        { id: 'catch_150',       name: 'Pokemon Master',       desc: 'Catch 150 Pokemon',
          category: 'capture', tier: 'platinum', check: s => s.pokemonCaught >= 150, progress: s => Math.min(150, s.pokemonCaught), target: 150 },

        // Explore achievements
        { id: 'steps_1000',      name: 'Adventurer',           desc: 'Walk 1,000 steps',
          category: 'explore', tier: 'bronze', check: s => s.steps >= 1000, progress: s => Math.min(1000, s.steps), target: 1000 },
        { id: 'steps_10000',     name: 'World Traveler',       desc: 'Walk 10,000 steps',
          category: 'explore', tier: 'silver', check: s => s.steps >= 10000, progress: s => Math.min(10000, s.steps), target: 10000 },
        { id: 'steps_50000',     name: 'Globe Trotter',        desc: 'Walk 50,000 steps',
          category: 'explore', tier: 'gold', check: s => s.steps >= 50000, progress: s => Math.min(50000, s.steps), target: 50000 },

        // Collect achievements
        { id: 'badge_1',         name: 'Badge Collector',      desc: 'Earn your first gym badge',
          category: 'collect', tier: null, check: s => s.badges >= 1, progress: s => Math.min(1, s.badges), target: 1 },
        { id: 'badge_4',         name: 'Halfway There',        desc: 'Earn 4 gym badges',
          category: 'collect', tier: 'silver', check: s => s.badges >= 4, progress: s => Math.min(4, s.badges), target: 4 },
        { id: 'badge_8',         name: 'Pokemon Champion',     desc: 'Earn all 8 gym badges',
          category: 'collect', tier: 'gold', check: s => s.badges >= 8, progress: s => Math.min(8, s.badges), target: 8 },
        { id: 'pokedex_50',      name: 'Pokedex: 50%',         desc: 'See 50% of all Pokemon',
          category: 'collect', tier: 'silver', check: s => s.pokemonSeen >= 75, progress: s => Math.min(75, s.pokemonSeen), target: 75 },

        // Training achievements
        { id: 'evolve_1',        name: 'Evolution!',           desc: 'Evolve a Pokemon for the first time',
          category: 'training', tier: null, check: s => s.pokemonEvolved >= 1, progress: s => Math.min(1, s.pokemonEvolved), target: 1 },
        { id: 'evolve_10',       name: 'Evolution Expert',     desc: 'Evolve 10 Pokemon',
          category: 'training', tier: 'silver', check: s => s.pokemonEvolved >= 10, progress: s => Math.min(10, s.pokemonEvolved), target: 10 },
        { id: 'legendary_catch', name: 'Legendary Hunter',     desc: 'Catch a legendary Pokemon',
          category: 'training', tier: 'gold', check: s => (s.legendariesCaught || 0) >= 1, progress: s => Math.min(1, s.legendariesCaught || 0), target: 1 },
    ];

    // State
    const earned = new Set();
    const popupQueue = [];
    let currentPopup = null;
    let popupTimer = 0;
    const POPUP_DURATION = 3500;
    const POPUP_SLIDE = 300;
    let dirty = false;
    let checkTimer = 0;
    const CHECK_INTERVAL = 5000;

    // Achievement list screen state
    let listOpen = false;
    let listCursor = 0;
    let listScroll = 0;
    let listCategory = null; // null = all, or category key

    function loadEarned() {
        try {
            const saved = localStorage.getItem('pokemon_achievements');
            if (saved) {
                const ids = JSON.parse(saved);
                for (const id of ids) earned.add(id);
            }
        } catch { /* ignore */ }

        API.getAchievements().then(data => {
            if (data && Array.isArray(data.achievements)) {
                for (const id of data.achievements) earned.add(id);
                persistLocal();
            }
        });
    }

    function persistLocal() {
        try {
            localStorage.setItem('pokemon_achievements', JSON.stringify([...earned]));
        } catch { /* ignore */ }
    }

    function saveToBackend() {
        if (!dirty) return;
        dirty = false;
        persistLocal();
        API.saveAchievements([...earned]);
    }

    function checkAchievements(force) {
        if (!force) return;
        const stats = typeof PlayerStats !== 'undefined' ? PlayerStats.getStats() : {};
        const badges = typeof BadgeCase !== 'undefined' ? BadgeCase.getBadgeCount() : 0;
        const checkData = { ...stats, badges };

        for (const ach of ACHIEVEMENTS) {
            if (earned.has(ach.id)) continue;
            if (ach.check(checkData)) {
                earned.add(ach.id);
                popupQueue.push(ach);
                dirty = true;
            }
        }

        if (dirty) saveToBackend();
    }

    function update(dt) {
        checkTimer += dt;
        if (checkTimer >= CHECK_INTERVAL) {
            checkTimer = 0;
            checkAchievements(true);
        }

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

    // ---- Medal pixel art rendering ----
    function drawMedal(ctx, x, y, size, tier) {
        if (!tier) {
            // No tier — simple star
            ctx.fillStyle = '#f8d030';
            drawStar(ctx, x, y, size * 0.4, size * 0.2, 5);
            return;
        }
        const medal = MEDAL_TIERS[tier];
        if (!medal) return;

        // Medal circle
        ctx.fillStyle = medal.color;
        ctx.beginPath();
        ctx.arc(x, y, size * 0.4, 0, Math.PI * 2);
        ctx.fill();

        // Inner ring
        ctx.strokeStyle = 'rgba(255,255,255,0.3)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(x, y, size * 0.3, 0, Math.PI * 2);
        ctx.stroke();

        // Ribbon bottom
        ctx.fillStyle = tier === 'platinum' ? '#8080c0' : tier === 'gold' ? '#c04040' : tier === 'silver' ? '#4060c0' : '#408040';
        ctx.fillRect(x - size * 0.2, y + size * 0.3, size * 0.15, size * 0.3);
        ctx.fillRect(x + size * 0.05, y + size * 0.3, size * 0.15, size * 0.3);

        // Tier letter
        ctx.fillStyle = '#ffffff';
        ctx.font = `bold ${Math.floor(size * 0.35)}px monospace`;
        ctx.textAlign = 'center';
        ctx.fillText(medal.icon, x, y + size * 0.12);
    }

    function drawStar(ctx, cx, cy, outerR, innerR, points) {
        ctx.beginPath();
        for (let i = 0; i < points * 2; i++) {
            const r = i % 2 === 0 ? outerR : innerR;
            const angle = (Math.PI * i / points) - Math.PI / 2;
            const x = cx + r * Math.cos(angle);
            const y = cy + r * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fill();
    }

    // ---- Popup notification ----
    function renderPopup(ctx, canvasW, canvasH) {
        if (!currentPopup) return;

        let slideY;
        if (popupTimer < POPUP_SLIDE) {
            slideY = -70 + (70 * (popupTimer / POPUP_SLIDE));
        } else if (popupTimer > POPUP_DURATION - POPUP_SLIDE) {
            const fadeOut = (popupTimer - (POPUP_DURATION - POPUP_SLIDE)) / POPUP_SLIDE;
            slideY = -70 * fadeOut;
        } else {
            slideY = 0;
        }

        const popW = Math.min(320, canvasW - 20);
        const popH = 58;
        const px = (canvasW - popW) / 2;
        const py = 8 + slideY;

        // Background with gradient feel
        ctx.fillStyle = 'rgba(20, 30, 50, 0.94)';
        ctx.fillRect(px, py, popW, popH);

        // Category color accent bar
        const cat = CATEGORIES[currentPopup.category];
        ctx.fillStyle = cat ? cat.color : '#f8d830';
        ctx.fillRect(px, py, 4, popH);

        // Border
        ctx.strokeStyle = '#f8d830';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, popW, popH);

        // Medal icon
        drawMedal(ctx, px + 26, py + popH / 2, 32, currentPopup.tier);

        // Achievement name
        ctx.fillStyle = '#f8d830';
        ctx.font = 'bold 13px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(currentPopup.name, px + 48, py + 22);

        // Description
        ctx.fillStyle = '#a0b8d0';
        ctx.font = '10px monospace';
        ctx.fillText(currentPopup.desc, px + 48, py + 38);

        // "Achievement Unlocked" label
        ctx.fillStyle = '#607090';
        ctx.font = '8px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('Achievement Unlocked!', px + popW - 8, py + 14);

        // Tier label
        if (currentPopup.tier && MEDAL_TIERS[currentPopup.tier]) {
            ctx.fillStyle = MEDAL_TIERS[currentPopup.tier].color;
            ctx.font = 'bold 8px monospace';
            ctx.fillText(MEDAL_TIERS[currentPopup.tier].label, px + popW - 8, py + popH - 8);
        }

        ctx.textAlign = 'left';
    }

    // ---- Achievement list screen ----
    function openList() {
        listOpen = true;
        listCursor = 0;
        listScroll = 0;
        listCategory = null;
    }

    function closeList() {
        listOpen = false;
    }

    function isListOpen() { return listOpen; }

    function getFilteredAchievements() {
        if (!listCategory) return ACHIEVEMENTS;
        return ACHIEVEMENTS.filter(a => a.category === listCategory);
    }

    function updateList(dt) {
        if (!listOpen) return;
        const action = Input.isActionPressed();
        const back = Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B');
        const mov = Input.getMovement();

        if (back) { closeList(); return; }

        const filtered = getFilteredAchievements();

        if (mov) {
            if (mov.dy < 0 && listCursor > 0) { listCursor--; }
            if (mov.dy > 0 && listCursor < filtered.length - 1) { listCursor++; }
            // Category tabs with left/right
            if (mov.dx !== 0) {
                const cats = [null, ...Object.keys(CATEGORIES)];
                let idx = cats.indexOf(listCategory);
                if (mov.dx > 0) idx = Math.min(cats.length - 1, idx + 1);
                if (mov.dx < 0) idx = Math.max(0, idx - 1);
                listCategory = cats[idx];
                listCursor = 0;
                listScroll = 0;
            }
        }
    }

    function renderList(ctx, cx, cy, w, h) {
        // Full-screen achievement list
        ctx.fillStyle = 'rgba(10, 15, 30, 0.95)';
        ctx.fillRect(cx, cy, w, h);
        ctx.strokeStyle = '#f8d830';
        ctx.lineWidth = 2;
        ctx.strokeRect(cx, cy, w, h);

        // Title
        ctx.fillStyle = '#f8d830';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('ACHIEVEMENTS', cx + w / 2, cy + 20);

        // Medal count summary
        const medalCounts = getMedalCounts();
        let mx = cx + w / 2 - 80;
        for (const tier of ['bronze', 'silver', 'gold', 'platinum']) {
            drawMedal(ctx, mx, cy + 38, 20, tier);
            ctx.fillStyle = '#d0d0d0';
            ctx.font = '10px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`${medalCounts[tier]}`, mx + 14, cy + 42);
            mx += 42;
        }

        // Category tabs
        const tabY = cy + 52;
        const cats = [{ key: null, name: 'All' }, ...Object.values(CATEGORIES).map((c, i) => ({ key: Object.keys(CATEGORIES)[i], ...c }))];
        const tabW = w / cats.length;
        for (let i = 0; i < cats.length; i++) {
            const tx = cx + i * tabW;
            const isActive = listCategory === cats[i].key;
            ctx.fillStyle = isActive ? 'rgba(248,216,48,0.2)' : 'rgba(255,255,255,0.05)';
            ctx.fillRect(tx, tabY, tabW, 18);
            ctx.fillStyle = isActive ? '#f8d830' : '#607080';
            ctx.font = isActive ? 'bold 9px monospace' : '9px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(cats[i].name, tx + tabW / 2, tabY + 13);
        }

        // Achievement list
        const filtered = getFilteredAchievements();
        const listY = tabY + 22;
        const itemH = 44;
        const maxVisible = Math.floor((h - (listY - cy) - 30) / itemH);

        // Scroll to keep cursor visible
        if (listCursor < listScroll) listScroll = listCursor;
        if (listCursor >= listScroll + maxVisible) listScroll = listCursor - maxVisible + 1;

        const stats = typeof PlayerStats !== 'undefined' ? PlayerStats.getStats() : {};
        const badges = typeof BadgeCase !== 'undefined' ? BadgeCase.getBadgeCount() : 0;
        const checkData = { ...stats, badges };

        for (let i = 0; i < maxVisible && (i + listScroll) < filtered.length; i++) {
            const ach = filtered[i + listScroll];
            const y = listY + i * itemH;
            const isEarned = earned.has(ach.id);
            const isCursor = (i + listScroll) === listCursor;

            // Row background
            if (isCursor) {
                ctx.fillStyle = 'rgba(80, 120, 200, 0.3)';
                ctx.fillRect(cx + 4, y, w - 8, itemH - 2);
                ctx.strokeStyle = '#6090c0';
                ctx.lineWidth = 1;
                ctx.strokeRect(cx + 4, y, w - 8, itemH - 2);
            } else if (isEarned) {
                ctx.fillStyle = 'rgba(72, 192, 72, 0.08)';
                ctx.fillRect(cx + 4, y, w - 8, itemH - 2);
            }

            // Medal icon
            if (isEarned) {
                drawMedal(ctx, cx + 22, y + 18, 24, ach.tier);
            } else {
                // Locked icon
                ctx.fillStyle = '#303040';
                ctx.beginPath();
                ctx.arc(cx + 22, y + 18, 10, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#505060';
                ctx.font = 'bold 10px monospace';
                ctx.textAlign = 'center';
                ctx.fillText('?', cx + 22, y + 22);
            }

            // Achievement name
            ctx.fillStyle = isEarned ? '#e0e8f0' : '#505868';
            ctx.font = 'bold 12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(ach.name, cx + 42, y + 16);

            // Description
            ctx.fillStyle = isEarned ? '#8098b0' : '#404858';
            ctx.font = '9px monospace';
            ctx.fillText(ach.desc, cx + 42, y + 28);

            // Progress bar
            const progCurrent = ach.progress(checkData);
            const progRatio = progCurrent / ach.target;
            const barX = cx + 42;
            const barY = y + 32;
            const barW = w - 100;
            const barH = 6;

            ctx.fillStyle = 'rgba(255,255,255,0.1)';
            ctx.fillRect(barX, barY, barW, barH);

            if (isEarned) {
                ctx.fillStyle = '#48c048';
                ctx.fillRect(barX, barY, barW, barH);
            } else {
                const cat = CATEGORIES[ach.category];
                ctx.fillStyle = (cat ? cat.color : '#4080c0') + '80';
                ctx.fillRect(barX, barY, barW * Math.min(1, progRatio), barH);
            }

            // Progress text
            ctx.fillStyle = isEarned ? '#48c048' : '#607080';
            ctx.font = '8px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(isEarned ? 'Complete!' : `${progCurrent}/${ach.target}`, cx + w - 12, y + 38);

            // Tier label
            if (ach.tier && MEDAL_TIERS[ach.tier]) {
                ctx.fillStyle = isEarned ? MEDAL_TIERS[ach.tier].color : '#404858';
                ctx.font = '8px monospace';
                ctx.textAlign = 'right';
                ctx.fillText(MEDAL_TIERS[ach.tier].label, cx + w - 12, y + 16);
            }
        }

        // Count at bottom
        const earnedInFilter = filtered.filter(a => earned.has(a.id)).length;
        ctx.fillStyle = '#607080';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${earnedInFilter} / ${filtered.length} completed`, cx + w / 2, cy + h - 12);

        // Controls hint
        ctx.fillStyle = '#404858';
        ctx.font = '9px monospace';
        ctx.fillText('\u2190\u2192 Category | \u2191\u2193 Scroll | Esc: Back', cx + w / 2, cy + h - 2);

        ctx.textAlign = 'left';
    }

    // ---- Medal counts for trainer card ----
    function getMedalCounts() {
        const counts = { bronze: 0, silver: 0, gold: 0, platinum: 0, total: 0 };
        for (const ach of ACHIEVEMENTS) {
            if (earned.has(ach.id) && ach.tier && MEDAL_TIERS[ach.tier]) {
                counts[ach.tier]++;
                counts.total++;
            }
        }
        return counts;
    }

    function getEarnedCount() { return earned.size; }
    function getTotalCount() { return ACHIEVEMENTS.length; }
    function isEarned(id) { return earned.has(id); }

    return {
        checkAchievements, update, renderPopup, renderList,
        getEarnedCount, getTotalCount, isEarned, loadEarned,
        openList, closeList, isListOpen, updateList,
        getMedalCounts, drawMedal, MEDAL_TIERS,
    };
})();
