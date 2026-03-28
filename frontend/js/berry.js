// berry.js — Berry farming UI: overworld plots, planting, watering, harvesting, pouch

const Berry = (() => {
    const TILE = Sprites.TILE;

    // Berry color definitions for pixel art rendering (matches backend berry_service BERRY_DEFS)
    const BERRY_COLORS = {
        1:  { name: 'Oran',   primary: '#4488dd', accent: '#2266aa' },
        2:  { name: 'Sitrus',  primary: '#ddcc44', accent: '#bbaa22' },
        3:  { name: 'Leppa',  primary: '#dd4444', accent: '#aa2222' },
        4:  { name: 'Cheri',  primary: '#ee3333', accent: '#cc1111' },
        5:  { name: 'Chesto', primary: '#5555cc', accent: '#3333aa' },
        6:  { name: 'Pecha',  primary: '#ee88bb', accent: '#cc6699' },
        7:  { name: 'Rawst',  primary: '#44bb66', accent: '#229944' },
        8:  { name: 'Aspear', primary: '#88ccee', accent: '#66aacc' },
        9:  { name: 'Lum',    primary: '#33cc33', accent: '#22aa22' },
        10: { name: 'Razz',   primary: '#cc3388', accent: '#aa1166' },
    };

    // Growth stage names (matches backend)
    const STAGES = ['empty', 'planted', 'sprouted', 'growing', 'flowering', 'ready'];

    // Plot definitions — matches backend PLOT_DEFS
    const PLOT_DEFS = {
        pallet_town:   [{ id: 'pallet_1', x: 8, y: 3 }, { id: 'pallet_2', x: 9, y: 3 }],
        route_1:       [{ id: 'route1_1', x: 5, y: 10 }, { id: 'route1_2', x: 6, y: 10 }, { id: 'route1_3', x: 7, y: 10 }],
        viridian_city: [{ id: 'viridian_1', x: 12, y: 5 }, { id: 'viridian_2', x: 13, y: 5 }],
    };

    // State
    let plots = {};           // plotId -> { plot_id, map_id, x, y, growth_stage, planted_berry, berry_name, water_count, time_remaining_seconds, yield_estimate }
    let pouch = {};           // berryId -> { berry_id, name, quantity }
    let berryTypes = [];      // Array of { id, name, description, growth_time_minutes, effect_type, rarity }
    let berryTypesLoaded = false;

    // Interaction UI state
    let interactionActive = false;
    let interactionPlotId = null;
    let interactionMenu = 0;  // 0=Plant, 1=Water, 2=Harvest, 3=Cancel
    let actionCooldown = 0;

    // Planting UI state
    let plantingActive = false;
    let plantingPlotId = null;
    let plantingIndex = 0;
    let plantingList = [];    // filtered pouch berries with qty > 0

    // Berry pouch UI state (opened from pause menu)
    let pouchActive = false;
    let pouchIndex = 0;
    let pouchList = [];
    let pouchAction = -1;     // -1=none, 0=Give, 1=Info, 2=Cancel
    let pouchTargetIndex = 0; // party pokemon index for Give

    // Sparkle effect for ready plots
    let sparkleTimer = 0;
    let sparkleFrame = 0;

    // Notification
    let notifyText = '';
    let notifyTimer = 0;

    // --- Init / Data Loading ---

    function init() {
        loadBerryTypes();
    }

    function loadBerryTypes() {
        API.getBerryTypes().then(data => {
            if (data && Array.isArray(data)) {
                berryTypes = data;
                berryTypesLoaded = true;
            }
        }).catch(() => {});
    }

    function loadPlotsForMap(mapId) {
        API.getBerryPlots(mapId).then(data => {
            if (data && Array.isArray(data)) {
                for (const p of data) {
                    plots[p.plot_id] = p;
                }
            }
        }).catch(() => {
            // Offline fallback: populate empty local plots
            const defs = PLOT_DEFS[mapId];
            if (defs) {
                for (const d of defs) {
                    if (!plots[d.id]) {
                        plots[d.id] = {
                            plot_id: d.id, map_id: mapId, x: d.x, y: d.y,
                            growth_stage: 'empty', planted_berry: null, berry_name: null,
                            water_count: 0, time_remaining_seconds: 0, yield_estimate: 0,
                        };
                    }
                }
            }
        });
    }

    function loadPouch() {
        API.getBerryPouch().then(data => {
            if (data && data.berries) {
                pouch = {};
                for (const [id, info] of Object.entries(data.berries)) {
                    pouch[id] = { berry_id: Number(id), name: info.name || getBerryName(Number(id)), quantity: info.quantity || 0 };
                }
            }
        }).catch(() => {});
    }

    function getBerryName(berryId) {
        const c = BERRY_COLORS[berryId];
        return c ? c.name + ' Berry' : 'Berry';
    }

    // --- Overworld Rendering ---

    function renderPlots(ctx, camX, camY, scale, mapId) {
        const defs = PLOT_DEFS[mapId];
        if (!defs) return;

        sparkleTimer += 16; // approx dt
        if (sparkleTimer > 300) {
            sparkleFrame = (sparkleFrame + 1) % 4;
            sparkleTimer = 0;
        }

        for (const def of defs) {
            const plot = plots[def.id];
            const screenX = (def.x * TILE - camX) * scale;
            const screenY = (def.y * TILE - camY) * scale;
            const s = scale;

            // Draw soil patch (always visible)
            drawSoilPatch(ctx, screenX, screenY, s);

            if (plot && plot.growth_stage && plot.growth_stage !== 'empty') {
                const berryId = plot.planted_berry;
                const color = BERRY_COLORS[berryId] || { primary: '#888888', accent: '#666666' };
                drawGrowthStage(ctx, screenX, screenY, s, plot.growth_stage, color);

                // Sparkle when ready
                if (plot.growth_stage === 'ready') {
                    drawSparkle(ctx, screenX, screenY, s);
                }
            }
        }
    }

    function drawSoilPatch(ctx, x, y, s) {
        // Dark brown tilled soil
        ctx.fillStyle = '#6b4226';
        ctx.fillRect(x + 2 * s, y + 10 * s, 12 * s, 6 * s);
        // Soil lines
        ctx.fillStyle = '#553318';
        ctx.fillRect(x + 3 * s, y + 12 * s, 10 * s, 1 * s);
        ctx.fillRect(x + 3 * s, y + 14 * s, 10 * s, 1 * s);
        // Mound
        ctx.fillStyle = '#7b5236';
        ctx.fillRect(x + 4 * s, y + 9 * s, 8 * s, 2 * s);
    }

    function drawGrowthStage(ctx, x, y, s, stage, color) {
        if (stage === 'planted') {
            // Small seed dot
            ctx.fillStyle = color.accent;
            ctx.fillRect(x + 7 * s, y + 9 * s, 2 * s, 2 * s);
        } else if (stage === 'sprouted') {
            // Small green sprout
            ctx.fillStyle = '#48a848';
            ctx.fillRect(x + 7 * s, y + 7 * s, 2 * s, 4 * s);
            // Tiny leaf
            ctx.fillRect(x + 9 * s, y + 7 * s, 2 * s, 2 * s);
        } else if (stage === 'growing') {
            // Taller stem with leaves
            ctx.fillStyle = '#48a848';
            ctx.fillRect(x + 7 * s, y + 4 * s, 2 * s, 7 * s);
            // Leaves
            ctx.fillRect(x + 5 * s, y + 5 * s, 2 * s, 2 * s);
            ctx.fillRect(x + 9 * s, y + 6 * s, 2 * s, 2 * s);
        } else if (stage === 'flowering') {
            // Full plant with berry color bud
            ctx.fillStyle = '#48a848';
            ctx.fillRect(x + 7 * s, y + 3 * s, 2 * s, 8 * s);
            ctx.fillRect(x + 4 * s, y + 4 * s, 3 * s, 2 * s);
            ctx.fillRect(x + 9 * s, y + 5 * s, 3 * s, 2 * s);
            // Berry bud on top
            ctx.fillStyle = color.primary;
            ctx.fillRect(x + 6 * s, y + 1 * s, 4 * s, 3 * s);
        } else if (stage === 'ready') {
            // Full plant with visible berry
            ctx.fillStyle = '#48a848';
            ctx.fillRect(x + 7 * s, y + 3 * s, 2 * s, 8 * s);
            ctx.fillRect(x + 4 * s, y + 4 * s, 3 * s, 2 * s);
            ctx.fillRect(x + 9 * s, y + 5 * s, 3 * s, 2 * s);
            // Big ripe berry
            ctx.fillStyle = color.primary;
            ctx.fillRect(x + 5 * s, y, 6 * s, 4 * s);
            // Berry highlight
            ctx.fillStyle = color.accent;
            ctx.fillRect(x + 6 * s, y + s, 2 * s, s);
        }
    }

    function drawSparkle(ctx, x, y, s) {
        const offsets = [
            [3, 0], [11, 1], [2, 3], [13, 2],
        ];
        const o = offsets[sparkleFrame];
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(x + o[0] * s, y + o[1] * s, s, s);
        // Cross sparkle
        ctx.fillRect(x + o[0] * s - s, y + o[1] * s, 3 * s, s);
        ctx.fillRect(x + o[0] * s, y + o[1] * s - s, s, 3 * s);
    }

    // --- Interaction Detection ---

    function checkInteraction(playerX, playerY, playerDir) {
        const tileX = Math.floor((playerX + TILE / 2) / TILE);
        const tileY = Math.floor((playerY + TILE / 2) / TILE);

        // Calculate facing tile
        const facingX = tileX + (playerDir === 3 ? 1 : playerDir === 2 ? -1 : 0);
        const facingY = tileY + (playerDir === 0 ? 1 : playerDir === 1 ? -1 : 0);

        const mapId = MapLoader.getCurrentMapId();
        const defs = PLOT_DEFS[mapId];
        if (!defs) return null;

        for (const def of defs) {
            if (facingX === def.x && facingY === def.y) {
                return def;
            }
        }
        return null;
    }

    function openInteraction(plotDef) {
        interactionActive = true;
        interactionPlotId = plotDef.id;
        interactionMenu = 0;
        actionCooldown = 200;
        // Refresh plot data
        loadPlotsForMap(plotDef.map_id || MapLoader.getCurrentMapId());
        loadPouch();
    }

    function closeInteraction() {
        interactionActive = false;
        interactionPlotId = null;
        plantingActive = false;
        plantingPlotId = null;
    }

    function isInteracting() { return interactionActive || plantingActive; }

    // --- Interaction Update ---

    function updateInteraction(dt) {
        actionCooldown = Math.max(0, actionCooldown - dt);

        if (plantingActive) {
            updatePlanting(dt);
            return;
        }

        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        const plot = plots[interactionPlotId];
        const stage = plot ? plot.growth_stage : 'empty';

        // Build menu items based on plot state
        const menuItems = getMenuItems(stage);

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) interactionMenu = Math.max(0, interactionMenu - 1);
            if (mov.dy > 0) interactionMenu = Math.min(menuItems.length - 1, interactionMenu + 1);
            actionCooldown = 150;
        }

        if (action) {
            actionCooldown = 200;
            const selected = menuItems[interactionMenu];
            if (selected === 'Plant') {
                openPlanting();
            } else if (selected === 'Water') {
                doWater();
            } else if (selected === 'Harvest') {
                doHarvest();
            } else if (selected === 'Info') {
                showPlotInfo();
            } else if (selected === 'Cancel') {
                closeInteraction();
            }
        }

        if (back) {
            closeInteraction();
            actionCooldown = 200;
        }
    }

    function getMenuItems(stage) {
        if (stage === 'empty' || !stage) return ['Plant', 'Cancel'];
        if (stage === 'ready') return ['Harvest', 'Info', 'Cancel'];
        // planted/sprouted/growing/flowering — can water (up to 3)
        const plot = plots[interactionPlotId];
        const items = [];
        if (plot && plot.water_count < 3) items.push('Water');
        items.push('Info', 'Cancel');
        return items;
    }

    // --- Actions ---

    function openPlanting() {
        plantingList = [];
        for (const [id, info] of Object.entries(pouch)) {
            if (info.quantity > 0) {
                plantingList.push(info);
            }
        }
        if (plantingList.length === 0) {
            showNotify('No berries to plant!');
            return;
        }
        plantingActive = true;
        plantingPlotId = interactionPlotId;
        plantingIndex = 0;
        actionCooldown = 200;
    }

    function updatePlanting(dt) {
        actionCooldown = Math.max(0, actionCooldown - dt);
        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) plantingIndex = Math.max(0, plantingIndex - 1);
            if (mov.dy > 0) plantingIndex = Math.min(plantingList.length - 1, plantingIndex + 1);
            actionCooldown = 150;
        }

        if (action && plantingList.length > 0) {
            actionCooldown = 200;
            const berry = plantingList[plantingIndex];
            API.plantBerry(plantingPlotId, berry.berry_id).then(data => {
                if (data && data.plot_id) {
                    plots[data.plot_id] = data;
                    berry.quantity--;
                    showNotify(`Planted ${berry.name}!`);
                } else if (data && data.detail) {
                    showNotify(data.detail);
                } else {
                    // Local fallback
                    plots[plantingPlotId] = {
                        ...plots[plantingPlotId],
                        growth_stage: 'planted',
                        planted_berry: berry.berry_id,
                        berry_name: berry.name,
                        water_count: 0,
                    };
                    berry.quantity--;
                    showNotify(`Planted ${berry.name}!`);
                }
            }).catch(() => {
                plots[plantingPlotId] = {
                    ...plots[plantingPlotId],
                    growth_stage: 'planted',
                    planted_berry: berry.berry_id,
                    berry_name: berry.name,
                    water_count: 0,
                };
                berry.quantity--;
                showNotify(`Planted ${berry.name}! (offline)`);
            });
            plantingActive = false;
            closeInteraction();
        }

        if (back) {
            plantingActive = false;
            actionCooldown = 200;
        }
    }

    function doWater() {
        API.waterBerry(interactionPlotId).then(data => {
            if (data && data.plot_id) {
                plots[data.plot_id] = data;
                showNotify(`Watered! (${data.water_count}/3)`);
            } else {
                // Local fallback
                const plot = plots[interactionPlotId];
                if (plot) {
                    plot.water_count = Math.min(3, (plot.water_count || 0) + 1);
                    showNotify(`Watered! (${plot.water_count}/3)`);
                }
            }
        }).catch(() => {
            const plot = plots[interactionPlotId];
            if (plot) {
                plot.water_count = Math.min(3, (plot.water_count || 0) + 1);
                showNotify(`Watered! (${plot.water_count}/3) (offline)`);
            }
        });
        closeInteraction();
    }

    function doHarvest() {
        API.harvestBerry(interactionPlotId).then(data => {
            if (data && data.success) {
                // Update plot to empty
                const plot = plots[interactionPlotId];
                if (plot) {
                    plot.growth_stage = 'empty';
                    plot.planted_berry = null;
                    plot.berry_name = null;
                    plot.water_count = 0;
                }
                // Update pouch
                const berryId = data.berry_id;
                if (berryId) {
                    if (!pouch[berryId]) {
                        pouch[berryId] = { berry_id: berryId, name: data.berry_name || getBerryName(berryId), quantity: 0 };
                    }
                    pouch[berryId].quantity += data.quantity || 1;
                }
                showNotify(`Harvested ${data.quantity || 1}x ${data.berry_name || 'Berry'}!`);
            } else {
                showNotify(data && data.message ? data.message : 'Cannot harvest yet');
            }
        }).catch(() => {
            showNotify('Harvest failed (offline)');
        });
        closeInteraction();
    }

    function showPlotInfo() {
        const plot = plots[interactionPlotId];
        if (!plot) return;
        const stage = plot.growth_stage || 'empty';
        const name = plot.berry_name || 'Nothing';
        const water = plot.water_count || 0;
        const remaining = plot.time_remaining_seconds || 0;
        let timeStr = 'Ready!';
        if (remaining > 0) {
            const mins = Math.ceil(remaining / 60);
            timeStr = `~${mins} min left`;
        }
        if (stage === 'empty') {
            Dialogue.start('Berry Plot', ['This plot is empty.', 'Plant a berry to start growing!']);
        } else if (stage === 'ready') {
            Dialogue.start('Berry Plot', [`${name} is ready to harvest!`]);
        } else {
            Dialogue.start('Berry Plot', [
                `${name} — Stage: ${stage}`,
                `Water: ${water}/3 | ${timeStr}`,
            ]);
        }
        closeInteraction();
    }

    // --- Interaction Rendering ---

    function renderInteraction(ctx, canvasW, canvasH) {
        if (plantingActive) {
            renderPlanting(ctx, canvasW, canvasH);
            return;
        }

        if (!interactionActive) return;

        const plot = plots[interactionPlotId];
        const stage = plot ? plot.growth_stage : 'empty';
        const menuItems = getMenuItems(stage);

        // Menu box
        const boxW = 120;
        const boxH = menuItems.length * 28 + 16;
        const bx = canvasW - boxW - 20;
        const by = canvasH / 2 - boxH / 2;

        ctx.fillStyle = '#f8f8f0';
        ctx.fillRect(bx, by, boxW, boxH);
        ctx.strokeStyle = '#404040';
        ctx.lineWidth = 3;
        ctx.strokeRect(bx, by, boxW, boxH);

        // Title
        ctx.fillStyle = '#2e7d32';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Berry Plot', bx + boxW / 2, by - 4);

        // Menu items
        ctx.font = '14px monospace';
        for (let i = 0; i < menuItems.length; i++) {
            const iy = by + 10 + i * 28;
            if (i === interactionMenu) {
                ctx.fillStyle = '#4caf50';
                ctx.fillRect(bx + 4, iy - 2, boxW - 8, 24);
                ctx.fillStyle = '#ffffff';
            } else {
                ctx.fillStyle = '#404040';
            }
            ctx.textAlign = 'left';
            ctx.fillText(menuItems[i], bx + 24, iy + 14);
            if (i === interactionMenu) {
                ctx.fillText('\u25B6', bx + 8, iy + 14);
            }
        }
        ctx.textAlign = 'left';
    }

    function renderPlanting(ctx, canvasW, canvasH) {
        // Berry selection panel
        const panelW = canvasW - 60;
        const panelH = Math.min(canvasH - 60, plantingList.length * 36 + 60);
        const px = 30;
        const py = (canvasH - panelH) / 2;

        // Background
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        ctx.fillStyle = '#2e4a2e';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#6aaa6a';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, panelW, panelH);

        // Title
        ctx.fillStyle = '#c8f8c8';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Choose a Berry to Plant', px + panelW / 2, py + 22);

        // Berry list
        for (let i = 0; i < plantingList.length; i++) {
            const berry = plantingList[i];
            const iy = py + 36 + i * 36;
            const iw = panelW - 20;
            const ih = 32;
            const ix = px + 10;

            // Row background
            ctx.fillStyle = i === plantingIndex ? 'rgba(100, 180, 100, 0.5)' : 'rgba(255, 255, 255, 0.05)';
            ctx.fillRect(ix, iy, iw, ih);
            if (i === plantingIndex) {
                ctx.strokeStyle = '#88dd88';
                ctx.lineWidth = 1;
                ctx.strokeRect(ix, iy, iw, ih);
            }

            // Berry color icon
            const bc = BERRY_COLORS[berry.berry_id] || { primary: '#888', accent: '#666' };
            ctx.fillStyle = bc.primary;
            ctx.fillRect(ix + 4, iy + 4, 24, 24);
            ctx.fillStyle = bc.accent;
            ctx.fillRect(ix + 6, iy + 6, 8, 8);

            // Name
            ctx.fillStyle = '#f0f0e0';
            ctx.font = 'bold 13px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(berry.name, ix + 36, iy + 20);

            // Quantity
            ctx.fillStyle = '#a0d0a0';
            ctx.font = '12px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(`x${berry.quantity}`, ix + iw - 8, iy + 20);
        }

        // Hint
        ctx.fillStyle = '#809880';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('Z: Plant | B/Esc: Back', px + panelW - 10, py + panelH - 8);
        ctx.textAlign = 'left';
    }

    // --- Berry Pouch Screen (pause menu sub-screen) ---

    function openPouch() {
        pouchActive = true;
        pouchIndex = 0;
        pouchAction = -1;
        pouchTargetIndex = 0;
        actionCooldown = 200;
        loadPouch();
        refreshPouchList();
    }

    function closePouch() {
        pouchActive = false;
        pouchAction = -1;
    }

    function isPouchActive() { return pouchActive; }

    function refreshPouchList() {
        pouchList = [];
        for (const [id, info] of Object.entries(pouch)) {
            if (info.quantity > 0) {
                pouchList.push(info);
            }
        }
    }

    function updatePouch(dt) {
        actionCooldown = Math.max(0, actionCooldown - dt);
        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        refreshPouchList();

        if (pouchAction >= 0) {
            // Action submenu
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) pouchAction = Math.max(0, pouchAction - 1);
                if (mov.dy > 0) pouchAction = Math.min(2, pouchAction + 1);
                actionCooldown = 150;
            }
            if (action) {
                actionCooldown = 200;
                if (pouchAction === 0 && pouchList[pouchIndex]) {
                    // Give berry to Pokemon as held item
                    const berry = pouchList[pouchIndex];
                    const party = Game.player.party;
                    if (party && party.length > 0) {
                        const poke = party[pouchTargetIndex] || party[0];
                        poke.heldItem = { id: berry.berry_id, name: berry.name };
                        berry.quantity--;
                        if (berry.quantity <= 0) {
                            pouchList.splice(pouchIndex, 1);
                            if (pouchIndex >= pouchList.length) pouchIndex = Math.max(0, pouchList.length - 1);
                        }
                        showNotify(`${poke.name} is holding ${berry.name}!`);
                    } else {
                        showNotify('No Pokemon in party!');
                    }
                } else if (pouchAction === 1 && pouchList[pouchIndex]) {
                    // Info
                    const berry = pouchList[pouchIndex];
                    const btype = berryTypes.find(t => t.id === berry.berry_id);
                    const desc = btype ? btype.description : 'A berry.';
                    Dialogue.start(berry.name, [desc]);
                }
                pouchAction = -1;
            }
            if (back) { pouchAction = -1; actionCooldown = 200; }
            return;
        }

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) pouchIndex = Math.max(0, pouchIndex - 1);
            if (mov.dy > 0) pouchIndex = Math.min(Math.max(0, pouchList.length - 1), pouchIndex + 1);
            actionCooldown = 150;
        }
        if (action && pouchList.length > 0) { pouchAction = 0; actionCooldown = 200; }
        if (back) { closePouch(); actionCooldown = 200; }
    }

    function renderPouch(ctx, canvasW, canvasH) {
        if (!pouchActive) return;

        const panelW = canvasW - 40;
        const panelH = canvasH - 40;
        const px = 20;
        const py = 20;

        // Background
        ctx.fillStyle = '#2e4a2e';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#6aaa6a';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, panelW, panelH);

        // Title
        ctx.fillStyle = '#c8f8c8';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Berry Pouch', px + panelW / 2, py + 25);

        if (pouchList.length === 0) {
            ctx.font = '14px monospace';
            ctx.fillStyle = '#809880';
            ctx.fillText('No berries', px + panelW / 2, py + panelH / 2);
        }

        // Berry list
        for (let i = 0; i < pouchList.length; i++) {
            const berry = pouchList[i];
            const iy = py + 40 + i * 42;
            const iw = panelW - 20;
            const ih = 38;
            const ix = px + 10;

            // Row
            ctx.fillStyle = i === pouchIndex ? 'rgba(100, 180, 100, 0.5)' : 'rgba(255, 255, 255, 0.05)';
            ctx.fillRect(ix, iy, iw, ih);
            if (i === pouchIndex) {
                ctx.strokeStyle = '#88dd88';
                ctx.lineWidth = 1;
                ctx.strokeRect(ix, iy, iw, ih);
            }

            // Berry icon
            const bc = BERRY_COLORS[berry.berry_id] || { primary: '#888', accent: '#666' };
            ctx.fillStyle = bc.primary;
            ctx.fillRect(ix + 6, iy + 6, 26, 26);
            ctx.fillStyle = bc.accent;
            ctx.fillRect(ix + 8, iy + 8, 10, 10);
            // Highlight
            ctx.fillStyle = '#ffffff';
            ctx.globalAlpha = 0.3;
            ctx.fillRect(ix + 9, iy + 9, 4, 4);
            ctx.globalAlpha = 1.0;

            // Name
            ctx.fillStyle = '#f0f0e0';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(berry.name, ix + 40, iy + 18);

            // Effect description
            const btype = berryTypes.find(t => t.id === berry.berry_id);
            if (btype) {
                ctx.fillStyle = '#809880';
                ctx.font = '10px monospace';
                ctx.fillText(btype.description || '', ix + 40, iy + 32);
            }

            // Quantity
            ctx.fillStyle = '#a0d0a0';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(`x${berry.quantity}`, ix + iw - 10, iy + 24);
        }

        // Action submenu
        if (pouchAction >= 0 && pouchList.length > 0) {
            const actions = ['Give', 'Info', 'Cancel'];
            const amx = canvasW - 130;
            const amy = canvasH / 2 - 50;
            const amw = 90;
            const amh = actions.length * 28 + 12;

            ctx.fillStyle = '#f8f8f0';
            ctx.fillRect(amx, amy, amw, amh);
            ctx.strokeStyle = '#404040';
            ctx.lineWidth = 2;
            ctx.strokeRect(amx, amy, amw, amh);

            ctx.font = '14px monospace';
            for (let i = 0; i < actions.length; i++) {
                const ay = amy + 10 + i * 28;
                if (i === pouchAction) {
                    ctx.fillStyle = '#4caf50';
                    ctx.fillRect(amx + 4, ay - 2, amw - 8, 24);
                    ctx.fillStyle = '#ffffff';
                } else {
                    ctx.fillStyle = '#404040';
                }
                ctx.textAlign = 'left';
                ctx.fillText(actions[i], amx + 24, ay + 14);
                if (i === pouchAction) ctx.fillText('\u25B6', amx + 8, ay + 14);
            }
        }

        // Back hint
        ctx.fillStyle = '#809880';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('B / Esc: Back', px + panelW - 10, py + panelH - 8);
        ctx.textAlign = 'left';
    }

    // --- Notification ---

    function showNotify(text) {
        notifyText = text;
        notifyTimer = 2000;
    }

    function updateNotify(dt) {
        if (notifyTimer > 0) {
            notifyTimer = Math.max(0, notifyTimer - dt);
        }
    }

    function renderNotify(ctx, canvasW, canvasH) {
        if (notifyTimer <= 0 || !notifyText) return;

        const alpha = Math.min(1, notifyTimer / 500);
        ctx.globalAlpha = alpha;

        const textW = ctx.measureText ? 200 : 200;
        const boxW = textW + 30;
        const boxH = 30;
        const bx = (canvasW - boxW) / 2;
        const by = canvasH - 60;

        ctx.fillStyle = '#2e7d32';
        ctx.fillRect(bx, by, boxW, boxH);
        ctx.strokeStyle = '#66bb6a';
        ctx.lineWidth = 2;
        ctx.strokeRect(bx, by, boxW, boxH);

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(notifyText, canvasW / 2, by + 20);
        ctx.textAlign = 'left';

        ctx.globalAlpha = 1.0;
    }

    // --- Main update (called from game loop) ---

    function update(dt) {
        updateNotify(dt);

        // Periodically refresh growth stages (every 30 seconds)
        if (typeof Berry._refreshTimer === 'undefined') Berry._refreshTimer = 0;
        Berry._refreshTimer += dt;
        if (Berry._refreshTimer > 30000) {
            Berry._refreshTimer = 0;
            const mapId = MapLoader.getCurrentMapId();
            if (PLOT_DEFS[mapId]) {
                loadPlotsForMap(mapId);
            }
        }
    }

    return {
        init,
        loadPlotsForMap,
        loadPouch,
        renderPlots,
        checkInteraction,
        openInteraction,
        closeInteraction,
        isInteracting,
        updateInteraction,
        renderInteraction,
        openPouch,
        closePouch,
        isPouchActive,
        updatePouch,
        renderPouch,
        update,
        renderNotify,
        PLOT_DEFS,
    };
})();
