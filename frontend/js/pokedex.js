// pokedex.js — Pokedex UI screen

const Pokedex = (() => {
    let active = false;
    let listIndex = 0;
    let scrollOffset = 0;
    let actionCooldown = 0;
    let viewMode = 'list'; // list, detail

    const VISIBLE_ROWS = 8;

    // Pokedex entries (placeholder data)
    const entries = [
        { id: 1, name: 'Bulbasaur', type: 'Grass', type2: 'Poison', height: '0.7m', weight: '6.9kg', desc: 'A strange seed was planted on its back at birth. The plant sprouts and grows with this Pokemon.', color: '#68b868' },
        { id: 2, name: 'Ivysaur', type: 'Grass', type2: 'Poison', height: '1.0m', weight: '13.0kg', desc: 'When the bulb on its back grows large, it appears to lose the ability to stand on its hind legs.', color: '#68b868' },
        { id: 3, name: 'Venusaur', type: 'Grass', type2: 'Poison', height: '2.0m', weight: '100.0kg', desc: 'The plant blooms when it is absorbing solar energy. It stays on the move to seek sunlight.', color: '#68b868' },
        { id: 4, name: 'Charmander', type: 'Fire', height: '0.6m', weight: '8.5kg', desc: 'Obviously prefers hot places. When it rains, steam is said to spout from the tip of its tail.', color: '#e88040' },
        { id: 5, name: 'Charmeleon', type: 'Fire', height: '1.1m', weight: '19.0kg', desc: 'When it swings its burning tail, it elevates the temperature to unbearably high levels.', color: '#e88040' },
        { id: 6, name: 'Charizard', type: 'Fire', type2: 'Flying', height: '1.7m', weight: '90.5kg', desc: 'Spits fire that is hot enough to melt boulders. Known to cause forest fires unintentionally.', color: '#e88040' },
        { id: 7, name: 'Squirtle', type: 'Water', height: '0.5m', weight: '9.0kg', desc: 'After birth, its back swells and hardens into a shell. Powerfully sprays foam from its mouth.', color: '#58a8d8' },
        { id: 8, name: 'Wartortle', type: 'Water', height: '1.0m', weight: '22.5kg', desc: 'Often hides in water to stalk unwary prey. For swimming fast, it moves its ears to maintain balance.', color: '#58a8d8' },
        { id: 9, name: 'Blastoise', type: 'Water', height: '1.6m', weight: '85.5kg', desc: 'A brutal Pokemon with pressurized water jets on its shell. They are used for high-speed tackles.', color: '#58a8d8' },
        { id: 10, name: 'Caterpie', type: 'Bug', height: '0.3m', weight: '2.9kg', desc: 'Its short feet are tipped with suction pads that enable it to tirelessly climb slopes and walls.', color: '#68b838' },
        { id: 11, name: 'Metapod', type: 'Bug', height: '0.7m', weight: '9.9kg', desc: 'This Pokemon is vulnerable to attack while its shell is soft, exposing its weak and tender body.', color: '#68b838' },
        { id: 12, name: 'Butterfree', type: 'Bug', type2: 'Flying', height: '1.1m', weight: '32.0kg', desc: 'In battle, it flaps its wings at great speed to release highly toxic dust into the air.', color: '#68b838' },
        { id: 13, name: 'Weedle', type: 'Bug', type2: 'Poison', height: '0.3m', weight: '3.2kg', desc: 'Often found in forests, eating leaves. It has a sharp venomous stinger on top of its head.', color: '#b08830' },
        { id: 14, name: 'Kakuna', type: 'Bug', type2: 'Poison', height: '0.6m', weight: '10.0kg', desc: 'Almost incapable of moving, this Pokemon can only harden its shell to protect itself.', color: '#b08830' },
        { id: 15, name: 'Beedrill', type: 'Bug', type2: 'Poison', height: '1.0m', weight: '29.5kg', desc: 'Flies at high speed and attacks using its large venomous stingers on its forelegs and tail.', color: '#b08830' },
        { id: 16, name: 'Pidgey', type: 'Normal', type2: 'Flying', height: '0.3m', weight: '1.8kg', desc: 'A common sight in forests and woods. It flaps its wings at ground level to kick up blinding sand.', color: '#c0a870' },
        { id: 17, name: 'Pidgeotto', type: 'Normal', type2: 'Flying', height: '1.1m', weight: '30.0kg', desc: 'Very protective of its sprawling territorial area, this Pokemon will fiercely peck at any intruder.', color: '#c0a870' },
        { id: 18, name: 'Pidgeot', type: 'Normal', type2: 'Flying', height: '1.5m', weight: '39.5kg', desc: 'When hunting, it skims the surface of water at high speed to pick off unwary prey such as Magikarp.', color: '#c0a870' },
        { id: 19, name: 'Rattata', type: 'Normal', height: '0.3m', weight: '3.5kg', desc: 'Bites anything when it attacks. Small and very quick, it is a common sight in many places.', color: '#a060c0' },
        { id: 20, name: 'Raticate', type: 'Normal', height: '0.7m', weight: '18.5kg', desc: 'It uses its whiskers to maintain its balance. It apparently slows down if they are cut off.', color: '#a060c0' },
    ];

    // Seen/caught status (mock — will sync with backend)
    const status = {}; // id -> 'unseen' | 'seen' | 'caught'

    const TYPE_COLORS = {
        Normal: '#a8a878', Fire: '#f08030', Water: '#6890f0', Grass: '#78c850',
        Electric: '#f8d030', Ice: '#98d8d8', Fighting: '#c03028', Poison: '#a040a0',
        Ground: '#e0c068', Flying: '#a890f0', Psychic: '#f85888', Bug: '#a8b820',
        Rock: '#b8a038', Ghost: '#705898', Dragon: '#7038f8', Dark: '#705848',
        Steel: '#b8b8d0', Fairy: '#ee99ac',
    };

    function init() {
        // Set initial starter as caught, a few others as seen
        const starter = Game.player.starter;
        if (starter) {
            const entry = entries.find(e => e.name === starter.name);
            if (entry) status[entry.id] = 'caught';
        }
        // Mark some wild Pokemon as seen
        status[10] = status[10] || 'seen'; // Caterpie
        status[13] = status[13] || 'seen'; // Weedle
        status[16] = status[16] || 'seen'; // Pidgey
        status[19] = status[19] || 'seen'; // Rattata

        // Sync seen/caught status from backend
        API.getSpecies().then(data => {
            if (data && Array.isArray(data)) {
                for (const sp of data) {
                    const existing = entries.find(e => e.id === sp.id);
                    if (!existing && sp.id && sp.name) {
                        entries.push({
                            id: sp.id, name: sp.name,
                            type: sp.types ? sp.types[0] : 'Normal',
                            type2: sp.types && sp.types[1] ? sp.types[1] : undefined,
                            height: sp.height || '?', weight: sp.weight || '?',
                            desc: sp.description || '', color: TYPE_COLORS[sp.types ? sp.types[0] : 'Normal'] || '#a8a878',
                        });
                    }
                }
                entries.sort((a, b) => a.id - b.id);
            }
        }).catch(() => {});

        // Load pokedex seen/caught data from backend game state
        API.getGameState().then(data => {
            if (data && data.pokedex) {
                if (data.pokedex.seen) {
                    for (const id of data.pokedex.seen) {
                        if (!status[id] || status[id] === 'unseen') status[id] = 'seen';
                    }
                }
                if (data.pokedex.caught) {
                    for (const id of data.pokedex.caught) status[id] = 'caught';
                }
            }
        }).catch(() => {});
    }

    function open() {
        active = true;
        listIndex = 0;
        scrollOffset = 0;
        viewMode = 'list';
        actionCooldown = 250;
        init();
    }

    function close() {
        active = false;
    }

    function isActive() { return active; }

    function getStatus(id) {
        return status[id] || 'unseen';
    }

    function update(dt) {
        if (!active) return;
        actionCooldown = Math.max(0, actionCooldown - dt);

        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (viewMode === 'list') {
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) { listIndex = Math.max(0, listIndex - 1); actionCooldown = 120; }
                if (mov.dy > 0) { listIndex = Math.min(entries.length - 1, listIndex + 1); actionCooldown = 120; }
            }
            // Scroll
            if (listIndex < scrollOffset) scrollOffset = listIndex;
            if (listIndex >= scrollOffset + VISIBLE_ROWS) scrollOffset = listIndex - VISIBLE_ROWS + 1;

            if (action && getStatus(entries[listIndex].id) !== 'unseen') {
                viewMode = 'detail';
                actionCooldown = 200;
            }
            if (back) { close(); actionCooldown = 200; }
        } else if (viewMode === 'detail') {
            if (back || action) { viewMode = 'list'; actionCooldown = 200; }
        }
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        // Red Pokedex device frame
        ctx.fillStyle = '#c83030';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Inner border
        ctx.fillStyle = '#a02020';
        ctx.fillRect(8, 8, canvasW - 16, canvasH - 16);

        // Screen area
        ctx.fillStyle = '#e8e8d8';
        ctx.fillRect(14, 14, canvasW - 28, canvasH - 28);

        // Header
        ctx.fillStyle = '#c83030';
        ctx.fillRect(14, 14, canvasW - 28, 30);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('POKEDEX', canvasW / 2, 34);

        // Seen/Caught counter
        let seen = 0, caught = 0;
        for (const s of Object.values(status)) {
            if (s === 'seen' || s === 'caught') seen++;
            if (s === 'caught') caught++;
        }
        ctx.font = '10px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`Seen: ${seen}`, 24, 34);
        ctx.textAlign = 'right';
        ctx.fillText(`Caught: ${caught}`, canvasW - 24, 34);

        if (viewMode === 'list') {
            renderList(ctx, canvasW, canvasH);
        } else {
            renderDetail(ctx, canvasW, canvasH);
        }

        ctx.textAlign = 'left';
    }

    function renderList(ctx, canvasW, canvasH) {
        const listX = 20;
        const listY = 50;
        const rowH = 30;
        const listW = canvasW - 40;

        for (let i = 0; i < VISIBLE_ROWS && scrollOffset + i < entries.length; i++) {
            const entry = entries[scrollOffset + i];
            const idx = scrollOffset + i;
            const ry = listY + i * rowH;
            const st = getStatus(entry.id);

            // Row background
            ctx.fillStyle = idx === listIndex ? '#c8d8e8' : (i % 2 === 0 ? '#e8e8d8' : '#e0e0d0');
            ctx.fillRect(listX, ry, listW, rowH - 2);

            if (idx === listIndex) {
                ctx.strokeStyle = '#4080c0';
                ctx.lineWidth = 2;
                ctx.strokeRect(listX, ry, listW, rowH - 2);
            }

            // Number
            ctx.fillStyle = '#606060';
            ctx.font = '12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`#${String(entry.id).padStart(3, '0')}`, listX + 6, ry + 18);

            // Name or ???
            if (st === 'unseen') {
                ctx.fillStyle = '#a0a0a0';
                ctx.font = '13px monospace';
                ctx.fillText('???', listX + 50, ry + 18);
            } else {
                ctx.fillStyle = '#303030';
                ctx.font = 'bold 13px monospace';
                ctx.fillText(entry.name, listX + 50, ry + 18);

                // Type badge
                ctx.fillStyle = TYPE_COLORS[entry.type] || '#a0a0a0';
                ctx.fillRect(listX + listW - 100, ry + 5, 40, 16);
                ctx.fillStyle = '#ffffff';
                ctx.font = '9px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(entry.type, listX + listW - 80, ry + 17);

                if (entry.type2) {
                    ctx.fillStyle = TYPE_COLORS[entry.type2] || '#a0a0a0';
                    ctx.fillRect(listX + listW - 54, ry + 5, 40, 16);
                    ctx.fillStyle = '#ffffff';
                    ctx.fillText(entry.type2, listX + listW - 34, ry + 17);
                }

                // Pokeball icon for caught
                if (st === 'caught') {
                    ctx.fillStyle = '#e04040';
                    ctx.beginPath();
                    ctx.arc(listX + 40, ry + 14, 5, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.fillStyle = '#f0f0f0';
                    ctx.beginPath();
                    ctx.arc(listX + 40, ry + 14, 2, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
        }

        // Scroll indicators
        if (scrollOffset > 0) {
            ctx.fillStyle = '#606060';
            ctx.font = '12px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('\u25B2', canvasW / 2, listY - 2);
        }
        if (scrollOffset + VISIBLE_ROWS < entries.length) {
            ctx.fillStyle = '#606060';
            ctx.fillText('\u25BC', canvasW / 2, listY + VISIBLE_ROWS * rowH + 10);
        }

        // Footer
        ctx.fillStyle = '#808080';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Enter: Details | B/Esc: Close', canvasW / 2, canvasH - 20);
    }

    function renderDetail(ctx, canvasW, canvasH) {
        const entry = entries[listIndex];
        const st = getStatus(entry.id);

        // Detail background
        ctx.fillStyle = '#f0f0e8';
        ctx.fillRect(20, 48, canvasW - 40, canvasH - 70);

        // Number and name
        ctx.fillStyle = '#303030';
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`#${String(entry.id).padStart(3, '0')} ${entry.name}`, 30, 75);

        // Pokemon sprite area
        const spriteX = canvasW / 2;
        const spriteY = 140;
        const spriteSize = 80;

        ctx.fillStyle = '#d8d8c8';
        ctx.fillRect(spriteX - spriteSize / 2, spriteY - spriteSize / 2, spriteSize, spriteSize);
        ctx.strokeStyle = '#a0a090';
        ctx.lineWidth = 2;
        ctx.strokeRect(spriteX - spriteSize / 2, spriteY - spriteSize / 2, spriteSize, spriteSize);

        if (st === 'caught') {
            // Full color sprite (simplified)
            ctx.fillStyle = entry.color;
            ctx.fillRect(spriteX - 20, spriteY - 20, 40, 40);
            ctx.fillStyle = '#202020';
            ctx.fillRect(spriteX - 12, spriteY - 10, 4, 4);
            ctx.fillRect(spriteX + 8, spriteY - 10, 4, 4);
        } else {
            // Silhouette
            ctx.fillStyle = '#404040';
            ctx.fillRect(spriteX - 20, spriteY - 20, 40, 40);
        }

        // Type badges
        const badgeY = spriteY + spriteSize / 2 + 15;
        ctx.fillStyle = TYPE_COLORS[entry.type] || '#a0a0a0';
        const badge1X = entry.type2 ? spriteX - 50 : spriteX - 25;
        ctx.fillRect(badge1X, badgeY, 48, 20);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 11px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(entry.type, badge1X + 24, badgeY + 14);

        if (entry.type2) {
            ctx.fillStyle = TYPE_COLORS[entry.type2] || '#a0a0a0';
            ctx.fillRect(spriteX + 2, badgeY, 48, 20);
            ctx.fillStyle = '#ffffff';
            ctx.fillText(entry.type2, spriteX + 26, badgeY + 14);
        }

        // Stats
        const statsY = badgeY + 35;
        ctx.fillStyle = '#505050';
        ctx.font = '12px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`Height: ${entry.height}`, 40, statsY);
        ctx.fillText(`Weight: ${entry.weight}`, 40, statsY + 20);

        // Description
        ctx.fillStyle = '#303030';
        ctx.font = '12px monospace';
        const descY = statsY + 50;
        const maxW = canvasW - 80;

        // Word wrap description
        const words = entry.desc.split(' ');
        let line = '';
        let y = descY;
        for (const word of words) {
            const test = line + (line ? ' ' : '') + word;
            if (ctx.measureText(test).width > maxW) {
                ctx.fillText(line, 40, y);
                line = word;
                y += 16;
            } else {
                line = test;
            }
        }
        ctx.fillText(line, 40, y);

        // Footer
        ctx.fillStyle = '#808080';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('B/Esc: Back to list', canvasW / 2, canvasH - 20);
    }

    // Public API to mark Pokemon
    function markSeen(id) {
        if (!status[id]) {
            status[id] = 'seen';
            // Sync with backend
            API.registerSeen(id);
        }
    }
    function markCaught(id) {
        status[id] = 'caught';
        // Sync with backend
        API.registerCaught(id);
    }

    return { open, close, isActive, update, render, markSeen, markCaught, entries };
})();
