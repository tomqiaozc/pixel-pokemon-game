// badges.js — Badge case UI

const BadgeCase = (() => {
    let active = false;
    let actionCooldown = 0;
    let selectedIndex = 0;
    let shineTimer = 0;

    // Badge data — 8 badges from Kanto gyms
    const badges = [
        { name: 'Boulder Badge', gym: 'Pewter City Gym', leader: 'Brock', type: 'Rock', earned: false },
        { name: 'Cascade Badge', gym: 'Cerulean City Gym', leader: 'Misty', type: 'Water', earned: false },
        { name: 'Thunder Badge', gym: 'Vermilion City Gym', leader: 'Lt. Surge', type: 'Electric', earned: false },
        { name: 'Rainbow Badge', gym: 'Celadon City Gym', leader: 'Erika', type: 'Grass', earned: false },
        { name: 'Soul Badge', gym: 'Fuchsia City Gym', leader: 'Koga', type: 'Poison', earned: false },
        { name: 'Marsh Badge', gym: 'Saffron City Gym', leader: 'Sabrina', type: 'Psychic', earned: false },
        { name: 'Volcano Badge', gym: 'Cinnabar Island Gym', leader: 'Blaine', type: 'Fire', earned: false },
        { name: 'Earth Badge', gym: 'Viridian City Gym', leader: 'Giovanni', type: 'Ground', earned: false },
    ];

    function open() {
        active = true;
        selectedIndex = 0;
        actionCooldown = 250;
        shineTimer = 0;

        // Sync badges from backend
        API.getBadges().then(data => {
            if (data && data.badges) {
                for (const badge of data.badges) {
                    const idx = typeof badge === 'number' ? badge : badge.index;
                    if (idx >= 0 && idx < badges.length) {
                        badges[idx].earned = true;
                    }
                }
            }
        });
    }

    function close() {
        active = false;
    }

    function isActive() { return active; }

    function earnBadge(index) {
        if (index >= 0 && index < badges.length) {
            badges[index].earned = true;
            // Sync badge award with backend
            API.awardBadge(index);
        }
    }

    function getBadgeCount() {
        return badges.filter(b => b.earned).length;
    }

    function hasBadge(index) {
        return badges[index] && badges[index].earned;
    }

    function update(dt) {
        if (!active) return;

        actionCooldown = Math.max(0, actionCooldown - dt);
        shineTimer += dt;

        const mov = Input.getMovement();
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;

        if (mov && actionCooldown <= 0) {
            // Navigate 4x2 grid
            if (mov.dx > 0 && selectedIndex % 4 < 3) { selectedIndex++; actionCooldown = 150; }
            if (mov.dx < 0 && selectedIndex % 4 > 0) { selectedIndex--; actionCooldown = 150; }
            if (mov.dy > 0 && selectedIndex < 4) { selectedIndex += 4; actionCooldown = 150; }
            if (mov.dy < 0 && selectedIndex >= 4) { selectedIndex -= 4; actionCooldown = 150; }
        }

        if (back) {
            close();
            actionCooldown = 200;
        }
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        // Dark overlay
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Badge case panel
        const panelW = 480;
        const panelH = 340;
        const px = (canvasW - panelW) / 2;
        const py = (canvasH - panelH) / 2;

        // Case background
        ctx.fillStyle = '#8b0000';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#d4a520';
        ctx.lineWidth = 4;
        ctx.strokeRect(px, py, panelW, panelH);

        // Inner felt
        ctx.fillStyle = '#2a1a1a';
        ctx.fillRect(px + 12, py + 40, panelW - 24, panelH - 52);
        ctx.strokeStyle = '#4a2a2a';
        ctx.lineWidth = 2;
        ctx.strokeRect(px + 12, py + 40, panelW - 24, panelH - 52);

        // Title
        ctx.fillStyle = '#d4a520';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Badge Case', canvasW / 2, py + 28);

        // Badge count
        const count = getBadgeCount();
        ctx.fillStyle = '#c0a080';
        ctx.font = '12px monospace';
        ctx.fillText(`${count} / 8 Badges`, canvasW / 2, py + panelH - 12);

        // Draw 8 badges in 4x2 grid
        const gridStartX = px + 35;
        const gridStartY = py + 60;
        const cellW = 110;
        const cellH = 120;

        for (let i = 0; i < 8; i++) {
            const col = i % 4;
            const row = Math.floor(i / 4);
            const cx = gridStartX + col * cellW + cellW / 2;
            const cy = gridStartY + row * cellH + 40;

            const badge = badges[i];
            const isSelected = i === selectedIndex;

            // Selection highlight
            if (isSelected) {
                ctx.strokeStyle = '#f8d830';
                ctx.lineWidth = 2;
                ctx.strokeRect(
                    gridStartX + col * cellW + 5,
                    gridStartY + row * cellH + 5,
                    cellW - 10,
                    cellH - 10
                );
            }

            // Draw badge using TrainerBattle.drawBadge
            const badgeSize = badge.earned ? 28 : 22;
            TrainerBattle.drawBadge(ctx, cx, cy, badgeSize, i, badge.earned);

            // Shine animation for earned badges
            if (badge.earned) {
                const shineOffset = Math.sin(shineTimer * 0.002 + i * 0.8) * 0.3 + 0.7;
                ctx.globalAlpha = shineOffset * 0.4;
                ctx.fillStyle = '#ffffff';
                ctx.beginPath();
                ctx.arc(cx - badgeSize * 0.3, cy - badgeSize * 0.3, 4, 0, Math.PI * 2);
                ctx.fill();
                ctx.globalAlpha = 1;
            }

            // Badge name below
            ctx.fillStyle = badge.earned ? '#f8f8f8' : '#606060';
            ctx.font = badge.earned ? 'bold 9px monospace' : '9px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(badge.earned ? badge.name : '???', cx, cy + badgeSize + 14);
        }

        // Selected badge info at bottom
        const selected = badges[selectedIndex];
        if (selected.earned) {
            ctx.fillStyle = '#c0a080';
            ctx.font = '11px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(`${selected.gym} — Leader: ${selected.leader}`, canvasW / 2, py + panelH - 28);
        }

        // Controls
        ctx.fillStyle = '#806040';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('B / Esc: Back', px + panelW - 16, py + 28);

        ctx.textAlign = 'left';
    }

    return { open, close, isActive, update, render, earnBadge, getBadgeCount, hasBadge, badges };
})();
