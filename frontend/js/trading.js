// trading.js — Pokemon Trading System UI shell (Sprint 6 prep)

const Trading = (() => {
    let active = false;
    let phase = 'lobby'; // lobby, selecting, confirming, animating, done
    let actionCooldown = 0;
    let selectedIndex = 0;
    let partnerPokemon = null;
    let tradeAnimation = 0;

    function open() {
        active = true;
        phase = 'lobby';
        actionCooldown = 250;
        selectedIndex = 0;
        partnerPokemon = null;
        tradeAnimation = 0;
    }

    function close() {
        active = false;
        phase = 'lobby';
    }

    function isActive() { return active; }

    function update(dt) {
        if (!active) return;
        actionCooldown = Math.max(0, actionCooldown - dt);

        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (phase === 'lobby') {
            if (back) { close(); actionCooldown = 200; }
            if (action) {
                phase = 'selecting';
                selectedIndex = 0;
                actionCooldown = 200;
            }
        } else if (phase === 'selecting') {
            const partyLen = Game.player.party ? Game.player.party.length : 0;
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) { selectedIndex = Math.max(0, selectedIndex - 1); actionCooldown = 150; }
                if (mov.dy > 0) { selectedIndex = Math.min(Math.max(0, partyLen - 1), selectedIndex + 1); actionCooldown = 150; }
            }
            if (action && partyLen > 0) {
                phase = 'confirming';
                actionCooldown = 200;
            }
            if (back) { phase = 'lobby'; actionCooldown = 200; }
        } else if (phase === 'confirming') {
            if (action) {
                phase = 'animating';
                tradeAnimation = 0;
                actionCooldown = 200;
            }
            if (back) { phase = 'selecting'; actionCooldown = 200; }
        } else if (phase === 'animating') {
            tradeAnimation += dt;
            if (tradeAnimation > 3000) {
                phase = 'done';
                actionCooldown = 200;
            }
        } else if (phase === 'done') {
            if (action || back) { close(); actionCooldown = 200; }
        }
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        // Background
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Title
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Pokemon Trade Center', canvasW / 2, 30);

        if (phase === 'lobby') {
            renderLobby(ctx, canvasW, canvasH);
        } else if (phase === 'selecting') {
            renderSelecting(ctx, canvasW, canvasH);
        } else if (phase === 'confirming') {
            renderConfirming(ctx, canvasW, canvasH);
        } else if (phase === 'animating') {
            renderAnimation(ctx, canvasW, canvasH);
        } else if (phase === 'done') {
            ctx.fillStyle = '#48c048';
            ctx.font = 'bold 18px monospace';
            ctx.fillText('Trade Complete!', canvasW / 2, canvasH / 2);
            ctx.fillStyle = '#a0a0b0';
            ctx.font = '12px monospace';
            ctx.fillText('Press any key to exit', canvasW / 2, canvasH / 2 + 30);
        }

        ctx.textAlign = 'left';
    }

    function renderLobby(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#a0a0b0';
        ctx.font = '14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Searching for trade partners...', canvasW / 2, canvasH / 2 - 20);

        // Placeholder: show "no partners found" with option to enter local trade
        ctx.fillStyle = '#606070';
        ctx.font = '11px monospace';
        ctx.fillText('(Local trade mode — press Z to select a Pokemon)', canvasW / 2, canvasH / 2 + 10);
        ctx.fillText('Press B/Esc to exit', canvasW / 2, canvasH / 2 + 30);
    }

    function renderSelecting(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Select a Pokemon to trade:', canvasW / 2, 55);

        const party = Game.player.party || [];
        for (let i = 0; i < party.length; i++) {
            const poke = party[i];
            const y = 70 + i * 36;
            const isSelected = i === selectedIndex;

            ctx.fillStyle = isSelected ? 'rgba(80, 80, 160, 0.6)' : 'rgba(255, 255, 255, 0.05)';
            ctx.fillRect(40, y, canvasW - 80, 32);
            if (isSelected) {
                ctx.strokeStyle = '#8080c0';
                ctx.lineWidth = 1;
                ctx.strokeRect(40, y, canvasW - 80, 32);
            }

            ctx.fillStyle = isSelected ? '#f8f8f8' : '#a0a0b0';
            ctx.font = '13px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`${poke.name}  Lv${poke.level}`, 56, y + 22);
        }

        ctx.fillStyle = '#606070';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Z: Select | B: Back', canvasW / 2, canvasH - 20);
    }

    function renderConfirming(ctx, canvasW, canvasH) {
        const party = Game.player.party || [];
        const poke = party[selectedIndex];
        if (!poke) return;

        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Trade ${poke.name}?`, canvasW / 2, canvasH / 2 - 20);

        ctx.fillStyle = '#a0a0b0';
        ctx.font = '12px monospace';
        ctx.fillText('Z: Confirm | B: Cancel', canvasW / 2, canvasH / 2 + 20);
    }

    function renderAnimation(ctx, canvasW, canvasH) {
        const progress = Math.min(1, tradeAnimation / 3000);

        // Pokeball moving animation
        const ballX = canvasW / 2;
        const ballY = canvasH / 2 + Math.sin(progress * Math.PI * 4) * 30;
        const scale = 1 + Math.sin(progress * Math.PI * 2) * 0.3;

        ctx.fillStyle = '#e04040';
        ctx.beginPath();
        ctx.arc(ballX, ballY, 15 * scale, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(ballX, ballY + 5, 10 * scale, 0, Math.PI);
        ctx.fill();

        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Trading...', canvasW / 2, canvasH / 2 + 60);
    }

    return { open, close, isActive, update, render };
})();
