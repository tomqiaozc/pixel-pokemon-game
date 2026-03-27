// menu.js — Pause menu, inventory, and party management

const PauseMenu = (() => {
    let active = false;
    let menuIndex = 0;
    let subScreen = null; // null, 'party', 'bag', 'pokedex', 'save'
    let actionCooldown = 0;
    let slideProgress = 0;

    // Inventory data (mock, will be synced with backend)
    const inventory = {
        potions: [
            { id: 'potion', name: 'Potion', qty: 3, desc: 'Restores 20 HP.', category: 'potions', color: '#d048d0' },
            { id: 'super-potion', name: 'Super Potion', qty: 1, desc: 'Restores 50 HP.', category: 'potions', color: '#d048d0' },
        ],
        pokeballs: [
            { id: 'pokeball', name: 'Poke Ball', qty: 5, desc: 'Catches wild Pokemon.', category: 'pokeballs', color: '#e04040' },
        ],
        battle: [
            { id: 'antidote', name: 'Antidote', qty: 2, desc: 'Cures poison.', category: 'battle', color: '#48a048' },
        ],
        key: [],
    };

    // Party data (mock)
    const party = [
        // Will be populated from game state
    ];

    // Bag screen state
    let bagTab = 0; // 0=potions, 1=pokeballs, 2=battle, 3=key
    let bagIndex = 0;
    let bagAction = -1; // -1=none, 0=Use, 1=Give, 2=Toss, 3=Cancel

    // Party screen state
    let partyIndex = 0;

    const MENU_ITEMS = ['Pokemon', 'Bag', 'Pokedex', 'Badges', 'Save', 'Close'];
    const BAG_TABS = ['Potions', 'Balls', 'Battle', 'Key Items'];
    const BAG_TAB_KEYS = ['potions', 'pokeballs', 'battle', 'key'];

    function open() {
        active = true;
        menuIndex = 0;
        subScreen = null;
        actionCooldown = 250;
        slideProgress = 0;

        // Sync party from game state
        syncParty();
    }

    function close() {
        active = false;
        subScreen = null;
    }

    function isActive() { return active; }

    function syncParty() {
        party.length = 0;
        if (Game.player.party && Game.player.party.length > 0) {
            for (const poke of Game.player.party) {
                party.push({
                    name: poke.name,
                    level: poke.level,
                    hp: poke.hp,
                    maxHp: poke.maxHp,
                    type: poke.type,
                    typeColor: poke.typeColor,
                });
            }
        } else if (Game.player.starter) {
            // Fallback for backwards compatibility
            party.push({
                name: Game.player.starter.name,
                level: 5,
                hp: 20,
                maxHp: 20,
                type: Game.player.starter.type,
                typeColor: Game.player.starter.typeColor,
            });
        }
    }

    function update(dt) {
        if (!active) return;
        actionCooldown = Math.max(0, actionCooldown - dt);
        slideProgress = Math.min(1, slideProgress + dt * 0.006);

        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (subScreen === null) {
            // Main pause menu
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) { menuIndex = Math.max(0, menuIndex - 1); actionCooldown = 150; }
                if (mov.dy > 0) { menuIndex = Math.min(MENU_ITEMS.length - 1, menuIndex + 1); actionCooldown = 150; }
            }
            if (action) {
                actionCooldown = 200;
                if (menuIndex === 0) { subScreen = 'party'; partyIndex = 0; }
                else if (menuIndex === 1) { subScreen = 'bag'; bagTab = 0; bagIndex = 0; bagAction = -1; }
                else if (menuIndex === 2) { subScreen = 'pokedex'; Pokedex.open(); }
                else if (menuIndex === 3) { subScreen = 'badges'; BadgeCase.open(); }
                else if (menuIndex === 4) { /* Save - placeholder */ }
                else if (menuIndex === 5) { close(); }
            }
            if (back) { close(); actionCooldown = 200; }
        } else if (subScreen === 'party') {
            updateParty(dt, mov, action, back);
        } else if (subScreen === 'bag') {
            updateBag(dt, mov, action, back);
        } else if (subScreen === 'pokedex') {
            Pokedex.update(dt);
            if (!Pokedex.isActive()) { subScreen = null; }
        } else if (subScreen === 'badges') {
            BadgeCase.update(dt);
            if (!BadgeCase.isActive()) { subScreen = null; }
        }
    }

    function updateParty(dt, mov, action, back) {
        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { partyIndex = Math.max(0, partyIndex - 1); actionCooldown = 150; }
            if (mov.dy > 0) { partyIndex = Math.min(Math.max(0, party.length - 1), partyIndex + 1); actionCooldown = 150; }
        }
        if (back) { subScreen = null; actionCooldown = 200; }
    }

    function updateBag(dt, mov, action, back) {
        const items = inventory[BAG_TAB_KEYS[bagTab]] || [];

        if (bagAction >= 0) {
            // Action submenu
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) { bagAction = Math.max(0, bagAction - 1); actionCooldown = 150; }
                if (mov.dy > 0) { bagAction = Math.min(3, bagAction + 1); actionCooldown = 150; }
            }
            if (action) {
                actionCooldown = 200;
                if (bagAction === 0) { /* Use item - placeholder */ }
                else if (bagAction === 2 && items[bagIndex]) {
                    // Toss item
                    items[bagIndex].qty--;
                    if (items[bagIndex].qty <= 0) items.splice(bagIndex, 1);
                    if (bagIndex >= items.length) bagIndex = Math.max(0, items.length - 1);
                }
                bagAction = -1;
            }
            if (back) { bagAction = -1; actionCooldown = 200; }
            return;
        }

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { bagIndex = Math.max(0, bagIndex - 1); actionCooldown = 150; }
            if (mov.dy > 0) { bagIndex = Math.min(Math.max(0, items.length - 1), bagIndex + 1); actionCooldown = 150; }
            if (mov.dx < 0) { bagTab = Math.max(0, bagTab - 1); bagIndex = 0; actionCooldown = 200; }
            if (mov.dx > 0) { bagTab = Math.min(BAG_TABS.length - 1, bagTab + 1); bagIndex = 0; actionCooldown = 200; }
        }
        if (action && items.length > 0) { bagAction = 0; actionCooldown = 200; }
        if (back) { subScreen = null; actionCooldown = 200; }
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        // Dim overlay
        ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        if (subScreen === null) {
            renderMainMenu(ctx, canvasW, canvasH);
        } else if (subScreen === 'party') {
            renderParty(ctx, canvasW, canvasH);
        } else if (subScreen === 'bag') {
            renderBag(ctx, canvasW, canvasH);
        } else if (subScreen === 'pokedex') {
            Pokedex.render(ctx, canvasW, canvasH);
        } else if (subScreen === 'badges') {
            BadgeCase.render(ctx, canvasW, canvasH);
        }
    }

    function renderMainMenu(ctx, canvasW, canvasH) {
        const menuW = 160;
        const menuH = MENU_ITEMS.length * 32 + 16;
        const mx = canvasW - menuW - 10;
        const my = 10;

        // Menu background
        ctx.fillStyle = '#f8f8f0';
        ctx.fillRect(mx, my, menuW, menuH);
        ctx.strokeStyle = '#404040';
        ctx.lineWidth = 3;
        ctx.strokeRect(mx, my, menuW, menuH);

        // Menu items
        ctx.font = 'bold 16px monospace';
        for (let i = 0; i < MENU_ITEMS.length; i++) {
            const iy = my + 12 + i * 32;
            if (i === menuIndex) {
                ctx.fillStyle = '#4080c0';
                ctx.fillRect(mx + 4, iy - 4, menuW - 8, 28);
                ctx.fillStyle = '#ffffff';
            } else {
                ctx.fillStyle = '#404040';
            }
            ctx.textAlign = 'left';
            ctx.fillText(MENU_ITEMS[i], mx + 30, iy + 14);

            if (i === menuIndex) {
                ctx.fillText('\u25B6', mx + 10, iy + 14);
            }
        }
    }

    function renderParty(ctx, canvasW, canvasH) {
        const panelW = canvasW - 40;
        const panelH = canvasH - 40;
        const px = 20;
        const py = 20;

        // Background
        ctx.fillStyle = '#303850';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#f8f8f8';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, panelW, panelH);

        // Title
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Pokemon Party', px + panelW / 2, py + 25);

        if (party.length === 0) {
            ctx.font = '14px monospace';
            ctx.fillStyle = '#a0a0a0';
            ctx.fillText('No Pokemon in party', px + panelW / 2, py + panelH / 2);
        }

        // Party slots (up to 6)
        for (let i = 0; i < Math.max(party.length, 1); i++) {
            const slotY = py + 40 + i * 55;
            const slotW = panelW - 20;
            const slotH = 48;
            const slotX = px + 10;

            // Slot background
            ctx.fillStyle = i === partyIndex ? 'rgba(80, 130, 200, 0.6)' : 'rgba(255, 255, 255, 0.1)';
            ctx.fillRect(slotX, slotY, slotW, slotH);
            ctx.strokeStyle = i === partyIndex ? '#80c0f8' : '#606060';
            ctx.lineWidth = 1;
            ctx.strokeRect(slotX, slotY, slotW, slotH);

            if (i < party.length) {
                const poke = party[i];

                // Pokemon name
                ctx.fillStyle = '#f8f8f8';
                ctx.font = 'bold 14px monospace';
                ctx.textAlign = 'left';
                ctx.fillText(poke.name, slotX + 50, slotY + 18);

                // Level
                ctx.font = '12px monospace';
                ctx.fillText(`Lv${poke.level}`, slotX + 50, slotY + 36);

                // Type badge
                const TYPE_COLORS = {
                    Grass: '#78c850', Fire: '#f08030', Water: '#6890f0',
                    Normal: '#a8a878', Bug: '#a8b820', Flying: '#a890f0',
                    Poison: '#a040a0', Electric: '#f8d030',
                };
                ctx.fillStyle = TYPE_COLORS[poke.type] || '#a0a0a0';
                ctx.fillRect(slotX + 130, slotY + 26, 50, 16);
                ctx.fillStyle = '#ffffff';
                ctx.font = '10px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(poke.type, slotX + 155, slotY + 38);

                // HP bar
                const barX = slotX + slotW - 160;
                const barW = 120;
                const barY = slotY + 12;
                const hpRatio = poke.hp / poke.maxHp;

                ctx.fillStyle = '#303030';
                ctx.fillRect(barX, barY, barW, 10);
                let hpColor = '#48c048';
                if (hpRatio < 0.5) hpColor = '#f8c830';
                if (hpRatio < 0.2) hpColor = '#e04038';
                ctx.fillStyle = hpColor;
                ctx.fillRect(barX + 1, barY + 1, (barW - 2) * hpRatio, 8);

                ctx.fillStyle = '#c0c0c0';
                ctx.font = '10px monospace';
                ctx.textAlign = 'right';
                ctx.fillText(`${poke.hp}/${poke.maxHp}`, barX + barW, barY + 28);

                // Simple sprite indicator
                ctx.fillStyle = TYPE_COLORS[poke.type] || '#a0a0a0';
                ctx.fillRect(slotX + 8, slotY + 8, 32, 32);
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 16px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(poke.name[0], slotX + 24, slotY + 30);
            }
        }

        // Back hint
        ctx.fillStyle = '#808080';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('B / Esc: Back', px + panelW - 10, py + panelH - 8);
        ctx.textAlign = 'left';
    }

    function renderBag(ctx, canvasW, canvasH) {
        const panelW = canvasW - 40;
        const panelH = canvasH - 40;
        const px = 20;
        const py = 20;

        // Background
        ctx.fillStyle = '#383820';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#f8f8f8';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, panelW, panelH);

        // Tabs
        const tabW = panelW / BAG_TABS.length;
        for (let i = 0; i < BAG_TABS.length; i++) {
            const tx = px + i * tabW;
            ctx.fillStyle = i === bagTab ? '#606040' : '#484830';
            ctx.fillRect(tx, py, tabW, 28);
            ctx.strokeStyle = '#808060';
            ctx.lineWidth = 1;
            ctx.strokeRect(tx, py, tabW, 28);

            ctx.fillStyle = i === bagTab ? '#f8f8d0' : '#a0a080';
            ctx.font = i === bagTab ? 'bold 12px monospace' : '11px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(BAG_TABS[i], tx + tabW / 2, py + 18);
        }

        // Items list
        const items = inventory[BAG_TAB_KEYS[bagTab]] || [];
        const listY = py + 34;

        if (items.length === 0) {
            ctx.fillStyle = '#808060';
            ctx.font = '14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('No items', px + panelW / 2, listY + 40);
        }

        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            const iy = listY + i * 42;
            const iw = panelW - 20;
            const ih = 38;
            const ix = px + 10;

            // Item row
            ctx.fillStyle = i === bagIndex ? 'rgba(120, 120, 80, 0.6)' : 'rgba(255, 255, 255, 0.05)';
            ctx.fillRect(ix, iy, iw, ih);
            if (i === bagIndex) {
                ctx.strokeStyle = '#c0c080';
                ctx.lineWidth = 1;
                ctx.strokeRect(ix, iy, iw, ih);
            }

            // Item icon (colored square)
            ctx.fillStyle = item.color || '#a0a0a0';
            ctx.fillRect(ix + 6, iy + 6, 26, 26);
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(item.name[0], ix + 19, iy + 24);

            // Item name and qty
            ctx.fillStyle = '#f8f8d0';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(item.name, ix + 40, iy + 18);

            ctx.fillStyle = '#c0c0a0';
            ctx.font = '11px monospace';
            ctx.fillText(item.desc, ix + 40, iy + 32);

            // Quantity
            ctx.fillStyle = '#f8f8d0';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(`x${item.qty}`, ix + iw - 10, iy + 24);
        }

        // Action submenu
        if (bagAction >= 0 && items.length > 0) {
            const actions = ['Use', 'Give', 'Toss', 'Cancel'];
            const amx = canvasW - 140;
            const amy = canvasH / 2 - 60;
            const amw = 100;
            const amh = actions.length * 28 + 12;

            ctx.fillStyle = '#f8f8f0';
            ctx.fillRect(amx, amy, amw, amh);
            ctx.strokeStyle = '#404040';
            ctx.lineWidth = 2;
            ctx.strokeRect(amx, amy, amw, amh);

            ctx.font = '14px monospace';
            for (let i = 0; i < actions.length; i++) {
                const ay = amy + 10 + i * 28;
                ctx.fillStyle = i === bagAction ? '#4080c0' : '#f8f8f0';
                if (i === bagAction) ctx.fillRect(amx + 4, ay - 2, amw - 8, 24);
                ctx.fillStyle = i === bagAction ? '#ffffff' : '#404040';
                ctx.textAlign = 'left';
                ctx.fillText(actions[i], amx + 24, ay + 14);
                if (i === bagAction) ctx.fillText('\u25B6', amx + 8, ay + 14);
            }
        }

        // Back hint
        ctx.fillStyle = '#808060';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('\u2190\u2192 Tabs | B/Esc: Back', px + panelW - 10, py + panelH - 8);
        ctx.textAlign = 'left';
    }

    return { open, close, isActive, update, render, inventory, party };
})();
