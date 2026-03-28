// achievements.js — Achievement tracking, medal tiers, progress bars & popup notifications
// Consumes backend achievement definitions (35 achievements, 8 categories)

const Achievements = (() => {
    // Medal tier thresholds — achievements with progressive tiers
    const MEDAL_TIERS = {
        bronze:   { color: '#cd7f32', label: 'Bronze',   icon: 'B' },
        silver:   { color: '#c0c0c0', label: 'Silver',   icon: 'S' },
        gold:     { color: '#ffd700', label: 'Gold',     icon: 'G' },
        platinum: { color: '#e5e4e2', label: 'Platinum', icon: 'P' },
    };

    // Achievement categories — matches backend's 8 categories
    const CATEGORIES = {
        collection: { name: 'Collection', color: '#6890f0' },
        battle:     { name: 'Battle',     color: '#e04040' },
        gym:        { name: 'Gym',        color: '#a040a0' },
        evolution:  { name: 'Evolution',  color: '#f8d030' },
        story:      { name: 'Story',      color: '#40a040' },
        minigame:   { name: 'Minigame',   color: '#f09030' },
        economy:    { name: 'Economy',    color: '#c0a040' },
        farming:    { name: 'Farming',    color: '#78c850' },
    };

    // Dynamic achievement list — loaded from backend, replaces old hardcoded list
    // Each entry: { id, name, description, category, tier, completed, progress, target }
    let ACHIEVEMENTS = [];

    // State
    const earned = new Set();
    const popupQueue = [];
    let currentPopup = null;
    let popupTimer = 0;
    const POPUP_DURATION = 3500;
    const POPUP_SLIDE = 300;
    let checkTimer = 0;
    const CHECK_INTERVAL = 5000;
    let notifyTimer = 0;
    const NOTIFY_INTERVAL = 8000;

    // Achievement list screen state
    let listOpen = false;
    let listCursor = 0;
    let listScroll = 0;
    let listCategory = null; // null = all, or category key

    function loadEarned() {
        // Load local cache first for instant display
        try {
            const saved = localStorage.getItem('pokemon_achievements');
            if (saved) {
                const ids = JSON.parse(saved);
                for (const id of ids) earned.add(id);
            }
        } catch { /* ignore */ }

        // Fetch full achievement list from backend (raw array of Achievement objects)
        API.getAchievements().then(data => {
            if (data && Array.isArray(data)) {
                ACHIEVEMENTS = data.map(a => ({
                    id: a.id,
                    name: a.name,
                    desc: a.description || a.desc || '',
                    category: a.category || 'collection',
                    tier: a.tier || 'bronze',
                    completed: a.completed || false,
                    progress: a.progress || 0,
                    target: a.target || 1,
                }));
                // Mark completed ones as earned
                for (const a of data) {
                    if (a.completed) earned.add(a.id);
                }
                persistLocal();
            }
        }).catch(() => {});
    }

    function persistLocal() {
        try {
            localStorage.setItem('pokemon_achievements', JSON.stringify([...earned]));
        } catch { /* ignore */ }
    }

    function saveToBackend() {
        API.saveAchievements([...earned]).then(data => {
            if (data && Array.isArray(data.newly_earned)) {
                for (const ach of data.newly_earned) {
                    if (!earned.has(ach.id)) {
                        earned.add(ach.id);
                        popupQueue.push({
                            id: ach.id,
                            name: ach.name,
                            desc: ach.description || ach.desc || '',
                            category: ach.category || 'collection',
                            tier: ach.tier || 'bronze',
                        });
                    }
                }
                // Update ACHIEVEMENTS with fresh data
                if (Array.isArray(data.all_achievements)) {
                    ACHIEVEMENTS = data.all_achievements.map(a => ({
                        id: a.id,
                        name: a.name,
                        desc: a.description || a.desc || '',
                        category: a.category || 'collection',
                        tier: a.tier || 'bronze',
                        completed: a.completed || false,
                        progress: a.progress || 0,
                        target: a.target || 1,
                    }));
                }
                persistLocal();
            }
        }).catch(() => {});
    }

    function checkAchievements() {
        // Trigger server-side achievement check — backend evaluates all conditions
        API.saveAchievements([...earned]).then(data => {
            if (data && Array.isArray(data.newly_earned)) {
                for (const ach of data.newly_earned) {
                    if (!earned.has(ach.id)) {
                        earned.add(ach.id);
                        popupQueue.push({
                            id: ach.id,
                            name: ach.name,
                            desc: ach.description || ach.desc || '',
                            category: ach.category || 'collection',
                            tier: ach.tier || 'bronze',
                        });
                    }
                }
                if (Array.isArray(data.all_achievements)) {
                    ACHIEVEMENTS = data.all_achievements.map(a => ({
                        id: a.id,
                        name: a.name,
                        desc: a.description || a.desc || '',
                        category: a.category || 'collection',
                        tier: a.tier || 'bronze',
                        completed: a.completed || false,
                        progress: a.progress || 0,
                        target: a.target || 1,
                    }));
                }
                persistLocal();
            }
        }).catch(() => {});
    }

    function pollNotifications() {
        API.getAchievementNotifications().then(data => {
            if (data && Array.isArray(data)) {
                for (const notif of data) {
                    if (!earned.has(notif.achievement_id)) {
                        earned.add(notif.achievement_id);
                        popupQueue.push({
                            id: notif.achievement_id,
                            name: notif.achievement_name,
                            desc: notif.description || '',
                            category: notif.category || 'collection',
                            tier: notif.tier || 'bronze',
                        });
                        persistLocal();
                    }
                }
            }
        }).catch(() => {});
    }

    function update(dt) {
        checkTimer += dt;
        if (checkTimer >= CHECK_INTERVAL) {
            checkTimer = 0;
            checkAchievements();
        }

        notifyTimer += dt;
        if (notifyTimer >= NOTIFY_INTERVAL) {
            notifyTimer = 0;
            pollNotifications();
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
        // Refresh from backend when opening
        API.getAchievements().then(data => {
            if (data && Array.isArray(data)) {
                ACHIEVEMENTS = data.map(a => ({
                    id: a.id,
                    name: a.name,
                    desc: a.description || a.desc || '',
                    category: a.category || 'collection',
                    tier: a.tier || 'bronze',
                    completed: a.completed || false,
                    progress: a.progress || 0,
                    target: a.target || 1,
                }));
                for (const a of data) {
                    if (a.completed) earned.add(a.id);
                }
                persistLocal();
            }
        }).catch(() => {});
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

        for (let i = 0; i < maxVisible && (i + listScroll) < filtered.length; i++) {
            const ach = filtered[i + listScroll];
            const y = listY + i * itemH;
            const isEarned = earned.has(ach.id) || ach.completed;
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

            // Progress bar (uses backend-provided progress/target)
            const progCurrent = ach.progress || 0;
            const progTarget = ach.target || 1;
            const progRatio = progCurrent / progTarget;
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
            ctx.fillText(isEarned ? 'Complete!' : `${progCurrent}/${progTarget}`, cx + w - 12, y + 38);

            // Tier label
            if (ach.tier && MEDAL_TIERS[ach.tier]) {
                ctx.fillStyle = isEarned ? MEDAL_TIERS[ach.tier].color : '#404858';
                ctx.font = '8px monospace';
                ctx.textAlign = 'right';
                ctx.fillText(MEDAL_TIERS[ach.tier].label, cx + w - 12, y + 16);
            }
        }

        // Count at bottom
        const earnedInFilter = filtered.filter(a => earned.has(a.id) || a.completed).length;
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
            if ((earned.has(ach.id) || ach.completed) && ach.tier && MEDAL_TIERS[ach.tier]) {
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
