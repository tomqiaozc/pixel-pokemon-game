// pvp.js — Multiplayer PvP Battle Lobby UI shell (Sprint 6 prep)

const PvP = (() => {
    let active = false;
    let phase = 'lobby'; // lobby, matchmaking, teamPreview, battle, results
    let actionCooldown = 0;
    let selectedIndex = 0;
    let matchTimer = 0;
    let opponentName = '';

    // Battle format options
    const FORMATS = [
        { id: 'singles', name: 'Singles (1v1)', desc: 'Classic single battle format' },
        { id: 'doubles', name: 'Doubles (2v2)', desc: 'Double battle with 2 Pokemon each' },
        { id: 'free', name: 'Free Battle', desc: 'No restrictions, any level' },
    ];

    function open() {
        active = true;
        phase = 'lobby';
        actionCooldown = 250;
        selectedIndex = 0;
        matchTimer = 0;
        opponentName = '';
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
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) { selectedIndex = Math.max(0, selectedIndex - 1); actionCooldown = 150; }
                if (mov.dy > 0) { selectedIndex = Math.min(FORMATS.length - 1, selectedIndex + 1); actionCooldown = 150; }
            }
            if (action) {
                phase = 'matchmaking';
                matchTimer = 0;
                actionCooldown = 200;
            }
            if (back) { close(); actionCooldown = 200; }
        } else if (phase === 'matchmaking') {
            matchTimer += dt;
            if (back) { phase = 'lobby'; actionCooldown = 200; }
        } else if (phase === 'teamPreview') {
            if (action) { phase = 'lobby'; actionCooldown = 200; } // placeholder
            if (back) { phase = 'lobby'; actionCooldown = 200; }
        } else if (phase === 'results') {
            if (action || back) { close(); actionCooldown = 200; }
        }
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        // Background
        ctx.fillStyle = '#1a1028';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Title
        ctx.fillStyle = '#e04040';
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('PvP Battle Arena', canvasW / 2, 30);

        if (phase === 'lobby') {
            renderLobby(ctx, canvasW, canvasH);
        } else if (phase === 'matchmaking') {
            renderMatchmaking(ctx, canvasW, canvasH);
        } else if (phase === 'teamPreview') {
            renderTeamPreview(ctx, canvasW, canvasH);
        } else if (phase === 'results') {
            renderResults(ctx, canvasW, canvasH);
        }

        ctx.textAlign = 'left';
    }

    function renderLobby(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Choose Battle Format:', canvasW / 2, 55);

        for (let i = 0; i < FORMATS.length; i++) {
            const fmt = FORMATS[i];
            const y = 70 + i * 50;
            const isSelected = i === selectedIndex;

            ctx.fillStyle = isSelected ? 'rgba(160, 50, 50, 0.5)' : 'rgba(255, 255, 255, 0.05)';
            ctx.fillRect(30, y, canvasW - 60, 44);
            if (isSelected) {
                ctx.strokeStyle = '#e06060';
                ctx.lineWidth = 1;
                ctx.strokeRect(30, y, canvasW - 60, 44);
            }

            ctx.fillStyle = isSelected ? '#f8f8f8' : '#a0a0b0';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(fmt.name, 46, y + 20);

            ctx.fillStyle = '#808090';
            ctx.font = '11px monospace';
            ctx.fillText(fmt.desc, 46, y + 36);
        }

        // Stats panel
        const statsY = 70 + FORMATS.length * 50 + 10;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.fillRect(30, statsY, canvasW - 60, 50);
        ctx.fillStyle = '#808090';
        ctx.font = '11px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('W: 0  L: 0  Rating: 1000', canvasW / 2, statsY + 22);
        ctx.fillText('Online Players: --', canvasW / 2, statsY + 40);

        ctx.fillStyle = '#606070';
        ctx.font = '10px monospace';
        ctx.fillText('Z: Find Match | B: Exit', canvasW / 2, canvasH - 20);
    }

    function renderMatchmaking(ctx, canvasW, canvasH) {
        const dots = '.'.repeat(Math.floor(matchTimer / 500) % 4);

        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Searching for opponent${dots}`, canvasW / 2, canvasH / 2 - 20);

        // Spinning indicator
        const angle = matchTimer * 0.005;
        ctx.strokeStyle = '#e04040';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(canvasW / 2, canvasH / 2 + 30, 15, angle, angle + Math.PI * 1.5);
        ctx.stroke();

        const elapsed = Math.floor(matchTimer / 1000);
        ctx.fillStyle = '#808090';
        ctx.font = '11px monospace';
        ctx.fillText(`Time: ${elapsed}s`, canvasW / 2, canvasH / 2 + 65);
        ctx.fillText('B: Cancel', canvasW / 2, canvasH / 2 + 85);
    }

    function renderTeamPreview(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Team Preview', canvasW / 2, canvasH / 2 - 30);
        ctx.fillStyle = '#808090';
        ctx.font = '12px monospace';
        ctx.fillText('(Coming soon)', canvasW / 2, canvasH / 2);
    }

    function renderResults(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Battle Results', canvasW / 2, canvasH / 2 - 20);
        ctx.fillStyle = '#a0a0b0';
        ctx.font = '12px monospace';
        ctx.fillText('Press any key to exit', canvasW / 2, canvasH / 2 + 20);
    }

    return { open, close, isActive, update, render, FORMATS };
})();
