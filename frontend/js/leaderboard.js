// leaderboard.js — Leaderboard & Player Stats / Trainer Card UI

const Leaderboard = (() => {
    let active = false;
    let tab = 0; // 0=Top Trainers, 1=Battle Record, 2=Pokedex, 3=Speedrun
    let scrollIndex = 0;
    let actionCooldown = 0;

    const TAB_NAMES = ['Top Trainers', 'Battles', 'Pokedex', 'Speedrun'];

    // Mock leaderboard data per category (will be replaced by backend API)
    const MOCK_DATA = {
        trainers: [
            { rank: 1, name: 'RED', score: '8 Badges', detail: '12:34:00' },
            { rank: 2, name: 'BLUE', score: '8 Badges', detail: '14:20:00' },
            { rank: 3, name: 'LANCE', score: '8 Badges', detail: '16:05:00' },
            { rank: 4, name: 'CYNTHIA', score: '7 Badges', detail: '18:10:00' },
            { rank: 5, name: 'STEVEN', score: '7 Badges', detail: '19:30:00' },
            { rank: 6, name: 'MISTY', score: '6 Badges', detail: '20:00:00' },
            { rank: 7, name: 'BROCK', score: '5 Badges', detail: '22:15:00' },
            { rank: 8, name: 'GARY', score: '4 Badges', detail: '24:10:00' },
            { rank: 9, name: 'LEAF', score: '3 Badges', detail: '25:00:00' },
            { rank: 10, name: 'GOLD', score: '2 Badges', detail: '26:30:00' },
        ],
        battles: [
            { rank: 1, name: 'RED', score: '95.2%', detail: '40W 2L' },
            { rank: 2, name: 'BLUE', score: '88.0%', detail: '22W 3L' },
            { rank: 3, name: 'LANCE', score: '85.7%', detail: '18W 3L' },
            { rank: 4, name: 'CYNTHIA', score: '82.0%', detail: '41W 9L' },
            { rank: 5, name: 'STEVEN', score: '80.0%', detail: '16W 4L' },
            { rank: 6, name: 'MISTY', score: '75.0%', detail: '12W 4L' },
            { rank: 7, name: 'BROCK', score: '72.5%', detail: '29W 11L' },
            { rank: 8, name: 'GARY', score: '70.0%', detail: '7W 3L' },
            { rank: 9, name: 'LEAF', score: '66.7%', detail: '10W 5L' },
            { rank: 10, name: 'GOLD', score: '60.0%', detail: '6W 4L' },
        ],
        pokedex: [
            { rank: 1, name: 'RED', score: '100%', detail: '151 caught' },
            { rank: 2, name: 'BLUE', score: '93.4%', detail: '141 caught' },
            { rank: 3, name: 'LANCE', score: '86.1%', detail: '130 caught' },
            { rank: 4, name: 'CYNTHIA', score: '78.1%', detail: '118 caught' },
            { rank: 5, name: 'STEVEN', score: '69.5%', detail: '105 caught' },
            { rank: 6, name: 'MISTY', score: '60.3%', detail: '91 caught' },
            { rank: 7, name: 'BROCK', score: '52.3%', detail: '79 caught' },
            { rank: 8, name: 'GARY', score: '46.4%', detail: '70 caught' },
            { rank: 9, name: 'LEAF', score: '39.7%', detail: '60 caught' },
            { rank: 10, name: 'GOLD', score: '33.1%', detail: '50 caught' },
        ],
        speedrun: [
            { rank: 1, name: 'RED', score: '2:34:12', detail: '8 gyms' },
            { rank: 2, name: 'BLUE', score: '2:58:40', detail: '8 gyms' },
            { rank: 3, name: 'LANCE', score: '3:15:20', detail: '8 gyms' },
            { rank: 4, name: 'CYNTHIA', score: '3:45:10', detail: '7 gyms' },
            { rank: 5, name: 'STEVEN', score: '4:02:30', detail: '7 gyms' },
            { rank: 6, name: 'MISTY', score: '4:30:00', detail: '6 gyms' },
            { rank: 7, name: 'BROCK', score: '5:10:15', detail: '5 gyms' },
            { rank: 8, name: 'GARY', score: '5:45:00', detail: '4 gyms' },
            { rank: 9, name: 'LEAF', score: '6:20:30', detail: '3 gyms' },
            { rank: 10, name: 'GOLD', score: '7:00:00', detail: '2 gyms' },
        ],
    };

    const CATEGORY_KEYS = ['trainers', 'battles', 'pokedex', 'speedrun'];
    const COLUMN_HEADERS = [
        { col1: 'Badges', col2: 'Time' },
        { col1: 'Win Rate', col2: 'Record' },
        { col1: 'Completion', col2: 'Caught' },
        { col1: 'Time', col2: 'Gyms' },
    ];

    function open() {
        active = true;
        tab = 0;
        scrollIndex = 0;
        actionCooldown = 250;
    }

    function close() {
        active = false;
    }

    function isActive() { return active; }

    function update(dt) {
        if (!active) return;
        actionCooldown = Math.max(0, actionCooldown - dt);

        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (mov && actionCooldown <= 0) {
            if (mov.dx > 0) { tab = Math.min(TAB_NAMES.length - 1, tab + 1); scrollIndex = 0; actionCooldown = 200; }
            if (mov.dx < 0) { tab = Math.max(0, tab - 1); scrollIndex = 0; actionCooldown = 200; }
            if (mov.dy < 0) { scrollIndex = Math.max(0, scrollIndex - 1); actionCooldown = 150; }
            if (mov.dy > 0) {
                const data = MOCK_DATA[CATEGORY_KEYS[tab]];
                scrollIndex = Math.min(Math.max(0, data.length - 6), scrollIndex + 1);
                actionCooldown = 150;
            }
        }

        if (back) { close(); actionCooldown = 200; }
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        const panelW = canvasW - 20;
        const panelH = canvasH - 20;
        const px = 10;
        const py = 10;

        // Background
        ctx.fillStyle = '#1a2a1a';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#48c048';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, panelW, panelH);

        // Title
        ctx.fillStyle = '#48c048';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Leaderboard', px + panelW / 2, py + 20);

        // Category tabs
        const tabW = panelW / TAB_NAMES.length;
        for (let i = 0; i < TAB_NAMES.length; i++) {
            const tx = px + i * tabW;
            ctx.fillStyle = i === tab ? '#2a4a2a' : '#1a2a1a';
            ctx.fillRect(tx, py + 28, tabW, 20);
            ctx.strokeStyle = '#387038';
            ctx.lineWidth = 1;
            ctx.strokeRect(tx, py + 28, tabW, 20);
            ctx.fillStyle = i === tab ? '#90e090' : '#507050';
            ctx.font = i === tab ? 'bold 10px monospace' : '9px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(TAB_NAMES[i], tx + tabW / 2, py + 42);
        }

        const contentY = py + 54;
        const headers = COLUMN_HEADERS[tab];
        const data = MOCK_DATA[CATEGORY_KEYS[tab]];

        // Column headers
        ctx.fillStyle = '#387038';
        ctx.fillRect(px + 4, contentY, panelW - 8, 18);
        ctx.fillStyle = '#90e090';
        ctx.font = 'bold 9px monospace';
        ctx.textAlign = 'left';
        ctx.fillText('#', px + 10, contentY + 13);
        ctx.fillText('Name', px + 36, contentY + 13);
        ctx.fillText(headers.col1, px + 130, contentY + 13);
        ctx.textAlign = 'right';
        ctx.fillText(headers.col2, px + panelW - 10, contentY + 13);

        // Entries (visible window)
        const visible = data.slice(scrollIndex, scrollIndex + 6);
        for (let i = 0; i < visible.length; i++) {
            const entry = visible[i];
            const y = contentY + 20 + i * 24;

            // Row background
            const isPlayer = entry.name === 'PLAYER';
            ctx.fillStyle = isPlayer ? 'rgba(72, 192, 72, 0.15)' : (i % 2 === 0 ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.05)');
            ctx.fillRect(px + 4, y, panelW - 8, 22);

            // Rank with medal colors
            const rankColors = { 1: '#f8d030', 2: '#c0c0c0', 3: '#c08030' };
            ctx.fillStyle = rankColors[entry.rank] || '#70a070';
            ctx.font = 'bold 11px monospace';
            ctx.textAlign = 'left';
            // Trophy icon for top 3
            if (entry.rank <= 3) {
                const trophies = { 1: 'G', 2: 'S', 3: 'B' };
                ctx.fillText(trophies[entry.rank], px + 10, y + 16);
            }
            ctx.fillText(`${entry.rank}`, px + 22, y + 16);

            // Name
            ctx.fillStyle = isPlayer ? '#48c048' : '#c0d0c0';
            ctx.font = '11px monospace';
            ctx.fillText(entry.name, px + 36, y + 16);

            // Score
            ctx.fillStyle = '#a0c0a0';
            ctx.fillText(entry.score, px + 130, y + 16);

            // Detail
            ctx.textAlign = 'right';
            ctx.fillStyle = '#809080';
            ctx.font = '10px monospace';
            ctx.fillText(entry.detail, px + panelW - 10, y + 16);
        }

        // Player rank (if not visible)
        const playerRank = getPlayerRank(tab);
        ctx.fillStyle = '#48c048';
        ctx.font = '10px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`Your Rank: #${playerRank}`, px + 10, py + panelH - 24);

        // Scroll indicator
        if (data.length > 6) {
            ctx.fillStyle = '#507050';
            ctx.font = '9px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(`${scrollIndex + 1}-${Math.min(scrollIndex + 6, data.length)} of ${data.length}`, px + panelW / 2, py + panelH - 24);
        }

        // Controls hint
        ctx.fillStyle = '#507050';
        ctx.font = '9px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('L/R: Category | U/D: Scroll | B: Back', px + panelW - 6, py + panelH - 8);
        ctx.textAlign = 'left';
    }

    function getPlayerRank(category) {
        // Compute player's rank based on live game stats
        const badges = typeof BadgeCase !== 'undefined' ? BadgeCase.getBadgeCount() : 0;
        const stats = typeof PlayerStats !== 'undefined' ? PlayerStats.getStats() : {};
        const wins = stats.battlesWon || 0;
        const losses = stats.battlesLost || 0;
        const caught = stats.pokemonCaught || 0;
        const total = typeof Pokedex !== 'undefined' ? Pokedex.entries.length : 151;

        // Simple rank estimation based on mock data comparison
        if (category === 0) return Math.max(1, 11 - badges);
        if (category === 1) {
            const rate = wins + losses > 0 ? wins / (wins + losses) : 0;
            if (rate >= 0.9) return 1;
            if (rate >= 0.8) return 3;
            if (rate >= 0.7) return 5;
            return Math.max(6, 11 - wins);
        }
        if (category === 2) {
            const pct = caught / total;
            if (pct >= 0.9) return 1;
            if (pct >= 0.7) return 3;
            if (pct >= 0.5) return 5;
            return Math.max(6, 11 - Math.floor(caught / 10));
        }
        return 10; // Speedrun default
    }

    return { open, close, isActive, update, render };
})();
