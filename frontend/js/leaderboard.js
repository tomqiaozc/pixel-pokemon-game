// leaderboard.js — Leaderboard & Player Stats UI shell (Sprint 6 prep)

const Leaderboard = (() => {
    let active = false;
    let tab = 0; // 0=rankings, 1=my stats
    let scrollIndex = 0;
    let actionCooldown = 0;

    // Mock leaderboard data (will be replaced by backend API)
    const MOCK_RANKINGS = [
        { rank: 1, name: 'RED', badges: 8, pokemon: 151, rating: 2400 },
        { rank: 2, name: 'BLUE', badges: 8, pokemon: 142, rating: 2350 },
        { rank: 3, name: 'LANCE', badges: 8, pokemon: 130, rating: 2200 },
        { rank: 4, name: 'CYNTHIA', badges: 7, pokemon: 118, rating: 2100 },
        { rank: 5, name: 'STEVEN', badges: 7, pokemon: 105, rating: 2050 },
        { rank: 6, name: 'PLAYER', badges: 0, pokemon: 1, rating: 1000 },
    ];

    const STAT_CATEGORIES = [
        { label: 'Pokemon Caught', key: 'caught', value: 0 },
        { label: 'Pokemon Seen', key: 'seen', value: 0 },
        { label: 'Battles Won', key: 'wins', value: 0 },
        { label: 'Battles Lost', key: 'losses', value: 0 },
        { label: 'Trainers Defeated', key: 'trainers', value: 0 },
        { label: 'Badges Earned', key: 'badges', value: 0 },
        { label: 'Distance Walked', key: 'steps', value: 0 },
        { label: 'Play Time', key: 'playtime', value: '0:00' },
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
            if (mov.dx !== 0) {
                tab = tab === 0 ? 1 : 0;
                scrollIndex = 0;
                actionCooldown = 200;
            }
            if (mov.dy < 0) { scrollIndex = Math.max(0, scrollIndex - 1); actionCooldown = 150; }
            if (mov.dy > 0) {
                const maxScroll = tab === 0 ? Math.max(0, MOCK_RANKINGS.length - 5) : Math.max(0, STAT_CATEGORIES.length - 6);
                scrollIndex = Math.min(maxScroll, scrollIndex + 1);
                actionCooldown = 150;
            }
        }

        if (back) { close(); actionCooldown = 200; }
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        const panelW = canvasW - 30;
        const panelH = canvasH - 30;
        const px = 15;
        const py = 15;

        // Background
        ctx.fillStyle = '#1a2a1a';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#48c048';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, panelW, panelH);

        // Title
        ctx.fillStyle = '#48c048';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Leaderboard', px + panelW / 2, py + 22);

        // Tabs
        const tabs = ['Rankings', 'My Stats'];
        const tabW = panelW / 2;
        for (let i = 0; i < 2; i++) {
            const tx = px + i * tabW;
            ctx.fillStyle = i === tab ? '#2a4a2a' : '#1a2a1a';
            ctx.fillRect(tx, py + 30, tabW, 22);
            ctx.strokeStyle = '#387038';
            ctx.lineWidth = 1;
            ctx.strokeRect(tx, py + 30, tabW, 22);
            ctx.fillStyle = i === tab ? '#90e090' : '#507050';
            ctx.font = i === tab ? 'bold 12px monospace' : '11px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(tabs[i], tx + tabW / 2, py + 46);
        }

        const contentY = py + 58;

        if (tab === 0) {
            renderRankings(ctx, px, contentY, panelW, panelH - 68);
        } else {
            renderStats(ctx, px, contentY, panelW, panelH - 68);
        }

        // Back hint
        ctx.fillStyle = '#507050';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('B/Esc: Back', px + panelW - 10, py + panelH - 8);
        ctx.textAlign = 'left';
    }

    function renderRankings(ctx, px, startY, panelW, availH) {
        // Header row
        ctx.fillStyle = '#387038';
        ctx.fillRect(px + 6, startY, panelW - 12, 22);
        ctx.fillStyle = '#90e090';
        ctx.font = 'bold 10px monospace';
        ctx.textAlign = 'left';
        ctx.fillText('Rank', px + 12, startY + 15);
        ctx.fillText('Name', px + 52, startY + 15);
        ctx.fillText('Badges', px + 130, startY + 15);
        ctx.textAlign = 'right';
        ctx.fillText('Rating', px + panelW - 14, startY + 15);

        // Entries
        const visible = MOCK_RANKINGS.slice(scrollIndex, scrollIndex + 5);
        for (let i = 0; i < visible.length; i++) {
            const entry = visible[i];
            const y = startY + 26 + i * 28;

            ctx.fillStyle = entry.name === 'PLAYER' ? 'rgba(72, 192, 72, 0.15)' : 'rgba(255, 255, 255, 0.03)';
            ctx.fillRect(px + 6, y, panelW - 12, 26);

            // Rank medal colors
            const rankColors = { 1: '#f8d030', 2: '#c0c0c0', 3: '#c08030' };
            ctx.fillStyle = rankColors[entry.rank] || '#70a070';
            ctx.font = 'bold 12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`#${entry.rank}`, px + 12, y + 18);

            ctx.fillStyle = entry.name === 'PLAYER' ? '#48c048' : '#c0d0c0';
            ctx.font = '12px monospace';
            ctx.fillText(entry.name, px + 52, y + 18);

            ctx.fillStyle = '#a0b0a0';
            ctx.fillText(`${entry.badges}`, px + 145, y + 18);

            ctx.textAlign = 'right';
            ctx.fillStyle = '#c0d0c0';
            ctx.fillText(`${entry.rating}`, px + panelW - 14, y + 18);
        }

        ctx.textAlign = 'left';
    }

    function renderStats(ctx, px, startY, panelW, availH) {
        const visible = STAT_CATEGORIES.slice(scrollIndex, scrollIndex + 6);
        for (let i = 0; i < visible.length; i++) {
            const stat = visible[i];
            const y = startY + i * 32;

            ctx.fillStyle = i % 2 === 0 ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.1)';
            ctx.fillRect(px + 6, y, panelW - 12, 30);

            ctx.fillStyle = '#90c090';
            ctx.font = '12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(stat.label, px + 14, y + 20);

            ctx.fillStyle = '#c0e0c0';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(`${stat.value}`, px + panelW - 14, y + 20);
        }

        ctx.textAlign = 'left';
    }

    return { open, close, isActive, update, render };
})();
