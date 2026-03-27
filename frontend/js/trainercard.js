// trainercard.js — Trainer Card UI (classic Pokemon-style)

const TrainerCard = (() => {
    let active = false;
    let actionCooldown = 0;
    let closeCooldown = 0;
    let flipTimer = 0;
    let showBack = false;

    function open() {
        active = true;
        actionCooldown = 250;
        closeCooldown = 400;
        flipTimer = 0;
        showBack = false;
    }

    function close() {
        active = false;
    }

    function isActive() { return active; }

    function update(dt) {
        if (!active) return;
        actionCooldown = Math.max(0, actionCooldown - dt);
        closeCooldown = Math.max(0, closeCooldown - dt);
        flipTimer += dt;

        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && closeCooldown <= 0;

        if (action) {
            showBack = !showBack;
            actionCooldown = 300;
        }
        if (back) { close(); closeCooldown = 200; }
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        // Dim overlay
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Card dimensions
        const cardW = Math.min(440, canvasW - 40);
        const cardH = Math.min(300, canvasH - 40);
        const cx = (canvasW - cardW) / 2;
        const cy = (canvasH - cardH) / 2;

        // Card background — gradient effect
        const badges = typeof BadgeCase !== 'undefined' ? BadgeCase.getBadgeCount() : 0;
        const cardColors = ['#3070a0', '#308060', '#a05030', '#906020', '#604080'];
        const cardColor = cardColors[Math.min(Math.floor(badges / 2), cardColors.length - 1)];

        ctx.fillStyle = cardColor;
        ctx.fillRect(cx, cy, cardW, cardH);

        // Border
        ctx.strokeStyle = '#f8d830';
        ctx.lineWidth = 3;
        ctx.strokeRect(cx, cy, cardW, cardH);

        // Inner border
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 1;
        ctx.strokeRect(cx + 4, cy + 4, cardW - 8, cardH - 8);

        if (!showBack) {
            renderFront(ctx, cx, cy, cardW, cardH);
        } else {
            renderBack(ctx, cx, cy, cardW, cardH);
        }

        // Flip hint
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Z: Flip Card | B: Close', canvasW / 2, cy + cardH + 14);
        ctx.textAlign = 'left';
    }

    function renderFront(ctx, cx, cy, cardW, cardH) {
        const stats = typeof PlayerStats !== 'undefined' ? PlayerStats.getStats() : {};
        const badges = typeof BadgeCase !== 'undefined' ? BadgeCase.getBadgeCount() : 0;

        // Title bar
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(cx + 8, cy + 8, cardW - 16, 24);
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'left';
        ctx.fillText('TRAINER CARD', cx + 14, cy + 24);

        // Stars for badge milestones (1 star per 2 badges)
        const stars = Math.floor(badges / 2);
        ctx.fillStyle = '#f8d830';
        ctx.font = '14px monospace';
        ctx.textAlign = 'right';
        let starStr = '';
        for (let i = 0; i < stars; i++) starStr += '*';
        ctx.fillText(starStr, cx + cardW - 14, cy + 24);

        // Trainer sprite area
        const spriteX = cx + 16;
        const spriteY = cy + 42;
        const spriteW = 64;
        const spriteH = 80;

        ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
        ctx.fillRect(spriteX, spriteY, spriteW, spriteH);

        // Simple pixel art trainer
        ctx.fillStyle = '#e04040'; // Hat
        ctx.fillRect(spriteX + 16, spriteY + 8, 32, 12);
        ctx.fillStyle = '#f8c0a0'; // Face
        ctx.fillRect(spriteX + 20, spriteY + 20, 24, 20);
        ctx.fillStyle = '#3060b0'; // Jacket
        ctx.fillRect(spriteX + 16, spriteY + 40, 32, 24);
        ctx.fillStyle = '#404040'; // Pants
        ctx.fillRect(spriteX + 18, spriteY + 64, 28, 14);

        // Info section
        const infoX = cx + 90;
        const infoY = cy + 44;
        const lineH = 22;

        ctx.font = '12px monospace';
        ctx.textAlign = 'left';

        // Name — read from Game.player
        ctx.fillStyle = '#e0e0e0';
        ctx.fillText('Name:', infoX, infoY);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 14px monospace';
        const playerName = (typeof Game !== 'undefined' && Game.player && Game.player.name) ? Game.player.name : 'RED';
        ctx.fillText(playerName, infoX + 60, infoY);

        // IDNo — read from API game ID
        ctx.font = '12px monospace';
        ctx.fillStyle = '#e0e0e0';
        ctx.fillText('IDNo:', infoX, infoY + lineH);
        ctx.fillStyle = '#ffffff';
        const playerId = (typeof API !== 'undefined' && API.getGameId()) ? String(API.getGameId()).padStart(5, '0') : '00001';
        ctx.fillText(playerId, infoX + 60, infoY + lineH);

        // Money
        ctx.fillStyle = '#e0e0e0';
        ctx.fillText('Money:', infoX, infoY + lineH * 2);
        ctx.fillStyle = '#f8d830';
        const money = stats.money || 3000;
        ctx.fillText(`$${money.toLocaleString()}`, infoX + 60, infoY + lineH * 2);

        // Pokedex
        ctx.fillStyle = '#e0e0e0';
        ctx.font = '12px monospace';
        ctx.fillText('Pokedex:', infoX, infoY + lineH * 3);
        const seen = stats.pokemonSeen || 0;
        const caught = stats.pokemonCaught || 0;
        ctx.fillStyle = '#ffffff';
        ctx.fillText(`${caught} caught / ${seen} seen`, infoX + 75, infoY + lineH * 3);

        // Play time
        ctx.fillStyle = '#e0e0e0';
        ctx.fillText('Time:', infoX, infoY + lineH * 4);
        ctx.fillStyle = '#ffffff';
        ctx.fillText(stats.playTime || '0:00', infoX + 60, infoY + lineH * 4);

        // Badge display — 8 badge slots in a row
        const badgeY = cy + cardH - 60;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(cx + 8, badgeY - 6, cardW - 16, 50);

        ctx.fillStyle = '#c0c0c0';
        ctx.font = '10px monospace';
        ctx.textAlign = 'left';
        ctx.fillText('Badges:', cx + 14, badgeY + 6);

        const badgeStartX = cx + 80;
        const badgeSpacing = (cardW - 100) / 8;
        for (let i = 0; i < 8; i++) {
            const bx = badgeStartX + i * badgeSpacing;
            const hasBadge = typeof BadgeCase !== 'undefined' && BadgeCase.hasBadge(i);

            if (hasBadge) {
                if (typeof TrainerBattle !== 'undefined' && TrainerBattle.drawBadge) {
                    TrainerBattle.drawBadge(ctx, bx + 12, badgeY + 22, 14, i, true);
                } else {
                    ctx.fillStyle = '#f8d830';
                    ctx.fillRect(bx + 4, badgeY + 12, 16, 16);
                }
            } else {
                ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
                ctx.fillRect(bx + 4, badgeY + 12, 16, 16);
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
                ctx.lineWidth = 1;
                ctx.strokeRect(bx + 4, badgeY + 12, 16, 16);
            }
        }

        ctx.textAlign = 'left';
    }

    function renderBack(ctx, cx, cy, cardW, cardH) {
        const stats = typeof PlayerStats !== 'undefined' ? PlayerStats.getStats() : {};

        // Title
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(cx + 8, cy + 8, cardW - 16, 24);
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('BATTLE RECORD', cx + cardW / 2, cy + 24);

        const startY = cy + 44;
        const labelX = cx + 20;
        const valX = cx + cardW - 20;

        const statLines = [
            { label: 'Battles Won', value: stats.battlesWon || 0 },
            { label: 'Battles Lost', value: stats.battlesLost || 0 },
            { label: 'Win Rate', value: ((stats.battlesWon || 0) + (stats.battlesLost || 0)) > 0
                ? Math.round(((stats.battlesWon || 0) / ((stats.battlesWon || 0) + (stats.battlesLost || 0))) * 100) + '%'
                : '0%' },
            { label: 'Trainers Defeated', value: stats.trainersDefeated || 0 },
            { label: 'Pokemon Caught', value: stats.pokemonCaught || 0 },
            { label: 'Pokemon Evolved', value: stats.pokemonEvolved || 0 },
            { label: 'Steps Walked', value: (stats.steps || 0).toLocaleString() },
            { label: 'Items Used', value: stats.itemsUsed || 0 },
        ];

        const fav = stats.favoritePokemon || 'None';

        // Compute line height to fit available card space
        const availH = cardH - 44 - 50;
        const lineH = Math.min(26, Math.floor(availH / (statLines.length + 1.5)));

        for (let i = 0; i < statLines.length; i++) {
            const y = startY + i * lineH;

            ctx.fillStyle = i % 2 === 0 ? 'rgba(0, 0, 0, 0.15)' : 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(cx + 8, y - 4, cardW - 16, lineH - 2);

            ctx.fillStyle = '#d0d0d0';
            ctx.font = '12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(statLines[i].label, labelX, y + 12);

            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 13px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(`${statLines[i].value}`, valX, y + 12);
        }

        // Favorite Pokemon section
        const favY = startY + statLines.length * lineH + 8;
        if (favY + 30 < cy + cardH - 10) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
            ctx.fillRect(cx + 8, favY, cardW - 16, 30);
            ctx.fillStyle = '#f8d830';
            ctx.font = 'bold 12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText('Favorite Pokemon:', labelX, favY + 20);
            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'right';
            ctx.fillText(fav, valX, favY + 20);
        }

        ctx.textAlign = 'left';
    }

    return { open, close, isActive, update, render };
})();
