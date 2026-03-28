// daycare.js — Daycare & breeding UI: deposit/withdraw, egg collection, hatch animation

const Daycare = (() => {
    const TILE = Sprites.TILE;
    const HATCH_STEPS = 5000; // matches backend DEFAULT_HATCH_STEPS

    // Daycare NPC location on Route 1 (outside the building)
    const DAYCARE_NPC = { mapId: 'route_1', x: 15, y: 23 };

    // State
    let daycareStatus = null; // { slot_1, slot_2, egg_ready, compatible, compatibility_message }
    let eggSteps = 0;         // local step counter sent to backend periodically
    let stepBuffer = 0;       // accumulate steps before sending to backend

    // Daycare interior screen state
    let interiorActive = false;
    let interiorPhase = 'main'; // main, deposit, withdraw, status, egg_collect
    let menuIndex = 0;
    let partyIndex = 0;
    let actionCooldown = 0;

    // Egg hatch animation state
    let hatchActive = false;
    let hatchPhase = 'dark';  // dark, rock, crack1, crack2, crack3, flash, reveal, done
    let hatchTimer = 0;
    let hatchPokemon = null;  // { name, types, level, ... }
    let hatchSparkles = [];
    let hatchEggIndex = -1;   // index in party

    // Phase timings (ms)
    const PHASE_DARK = 1000;
    const PHASE_ROCK = 2000;
    const PHASE_CRACK = 800;
    const PHASE_FLASH = 500;
    const PHASE_REVEAL = 2500;

    // Notification
    let notifyText = '';
    let notifyTimer = 0;

    // --- API wiring ---

    function loadStatus() {
        API.getDaycareStatus().then(data => {
            if (data) daycareStatus = data;
        }).catch(() => {});
    }

    function deposit(pokemonIndex) {
        API.daycareDeposit(pokemonIndex).then(data => {
            if (data && !data.detail) {
                daycareStatus = data;
                // Remove from party locally
                if (Game.player.party && pokemonIndex < Game.player.party.length) {
                    Game.player.party.splice(pokemonIndex, 1);
                }
                showNotify('Pokemon deposited at daycare!');
            } else {
                showNotify(data && data.detail ? data.detail : 'Cannot deposit');
            }
        }).catch(() => {
            showNotify('Deposit failed (offline)');
        });
    }

    function withdraw(slot) {
        API.daycareWithdraw(slot).then(data => {
            if (data && !data.detail) {
                // Add Pokemon back to party
                const slotData = slot === 1 ? daycareStatus.slot_1 : daycareStatus.slot_2;
                if (slotData && Game.player.party && Game.player.party.length < 6) {
                    Game.player.party.push({
                        name: slotData.name,
                        type: slotData.types ? slotData.types[0] : 'Normal',
                        level: slotData.level,
                        hp: slotData.stats ? slotData.stats.hp : 20,
                        maxHp: slotData.stats ? slotData.stats.hp : 20,
                        speciesId: slotData.species_id || 0,
                    });
                }
                daycareStatus = data;
                showNotify('Pokemon withdrawn!');
            } else {
                showNotify(data && data.detail ? data.detail : 'Cannot withdraw');
            }
        }).catch(() => {
            showNotify('Withdraw failed (offline)');
        });
    }

    function collectEgg() {
        API.daycareCollectEgg().then(data => {
            if (data && data.success && data.egg) {
                const eggPokemon = {
                    name: 'Egg',
                    type: data.egg.types ? data.egg.types[0] : 'Normal',
                    level: 1,
                    hp: 10,
                    maxHp: 10,
                    is_egg: true,
                    hatch_counter: data.egg.hatch_counter || HATCH_STEPS,
                    species_id: data.egg.id,
                    egg_data: data.egg,
                };
                // Add egg to party if room, else send to PC
                if (Game.player.party && Game.player.party.length < 6) {
                    Game.player.party.push(eggPokemon);
                    showNotify('You received an egg!');
                } else {
                    // Party full — store in local PC box (syncs on save)
                    if (!Game.player.pcBox) Game.player.pcBox = [];
                    Game.player.pcBox.push(eggPokemon);
                    showNotify('Party full! Egg sent to PC.');
                }
                if (daycareStatus) daycareStatus.egg_ready = false;
            } else {
                showNotify(data && data.detail ? data.detail : 'No egg available');
            }
        }).catch(() => {
            showNotify('Egg collection failed (offline)');
        });
    }

    function sendSteps(steps) {
        API.daycareStep(steps).then(data => {
            if (data && data.hatched && data.pokemon) {
                // Find egg in party and trigger hatch
                const eggIdx = Game.player.party.findIndex(p => p.is_egg);
                if (eggIdx >= 0) {
                    hatchEggIndex = eggIdx;
                    hatchPokemon = data.pokemon;
                    startHatchAnimation();
                }
            }
        }).catch(() => {});
    }

    // --- Step counting (called from game.js on movement) ---

    function onStep() {
        stepBuffer++;

        // Decrement local egg counters
        if (Game.player.party) {
            for (const poke of Game.player.party) {
                if (poke.is_egg && poke.hatch_counter > 0) {
                    poke.hatch_counter--;
                    if (poke.hatch_counter <= 0 && !hatchActive) {
                        // Local hatch trigger (backend will confirm via step API)
                        const eggIdx = Game.player.party.indexOf(poke);
                        hatchEggIndex = eggIdx;
                        // Send steps to backend to get the hatched pokemon data
                        sendSteps(stepBuffer);
                        stepBuffer = 0;
                        return;
                    }
                }
            }
        }

        // Send accumulated steps to backend every 50 steps
        if (stepBuffer >= 50) {
            sendSteps(stepBuffer);
            stepBuffer = 0;
        }
    }

    // --- Daycare NPC detection ---

    function checkNpcInteraction(playerX, playerY, playerDir, mapId) {
        if (mapId !== DAYCARE_NPC.mapId) return false;

        const tileX = Math.floor((playerX + TILE / 2) / TILE);
        const tileY = Math.floor((playerY + TILE / 2) / TILE);
        const facingX = tileX + (playerDir === 3 ? 1 : playerDir === 2 ? -1 : 0);
        const facingY = tileY + (playerDir === 0 ? 1 : playerDir === 1 ? -1 : 0);

        return facingX === DAYCARE_NPC.x && facingY === DAYCARE_NPC.y;
    }

    function openInterior() {
        interiorActive = true;
        interiorPhase = 'main';
        menuIndex = 0;
        partyIndex = 0;
        actionCooldown = 250;
        loadStatus();
    }

    function closeInterior() {
        interiorActive = false;
        interiorPhase = 'main';
    }

    function isInteriorActive() { return interiorActive; }

    // --- Interior update ---

    function updateInterior(dt) {
        if (!interiorActive) return;
        actionCooldown = Math.max(0, actionCooldown - dt);

        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (interiorPhase === 'main') {
            const items = getMainMenu();
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) menuIndex = Math.max(0, menuIndex - 1);
                if (mov.dy > 0) menuIndex = Math.min(items.length - 1, menuIndex + 1);
                actionCooldown = 150;
            }
            if (action) {
                actionCooldown = 200;
                const sel = items[menuIndex];
                if (sel === 'Deposit Pokemon') { interiorPhase = 'deposit'; partyIndex = 0; }
                else if (sel === 'Withdraw Slot 1') { withdraw(1); closeInterior(); }
                else if (sel === 'Withdraw Slot 2') { withdraw(2); closeInterior(); }
                else if (sel === 'Collect Egg') { collectEgg(); closeInterior(); }
                else if (sel === 'Check Status') { interiorPhase = 'status'; }
                else if (sel === 'Leave') { closeInterior(); }
            }
            if (back) { closeInterior(); actionCooldown = 200; }

        } else if (interiorPhase === 'deposit') {
            const party = Game.player.party || [];
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) partyIndex = Math.max(0, partyIndex - 1);
                if (mov.dy > 0) partyIndex = Math.min(party.length - 1, partyIndex + 1);
                actionCooldown = 150;
            }
            if (action && party.length > 1) {
                actionCooldown = 200;
                deposit(partyIndex);
                closeInterior();
            }
            if (back) { interiorPhase = 'main'; menuIndex = 0; actionCooldown = 200; }

        } else if (interiorPhase === 'status') {
            if (action || back) { interiorPhase = 'main'; menuIndex = 0; actionCooldown = 200; }
        }
    }

    function getMainMenu() {
        const items = [];
        const s = daycareStatus;
        const slotsUsed = (s && s.slot_1 ? 1 : 0) + (s && s.slot_2 ? 1 : 0);

        if (slotsUsed < 2) items.push('Deposit Pokemon');
        if (s && s.slot_1) items.push('Withdraw Slot 1');
        if (s && s.slot_2) items.push('Withdraw Slot 2');
        if (s && s.egg_ready) items.push('Collect Egg');
        items.push('Check Status');
        items.push('Leave');
        return items;
    }

    // --- Interior rendering ---

    function renderInterior(ctx, canvasW, canvasH) {
        if (!interiorActive) return;

        // Dim overlay
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        if (interiorPhase === 'main') {
            renderMainMenu(ctx, canvasW, canvasH);
        } else if (interiorPhase === 'deposit') {
            renderDeposit(ctx, canvasW, canvasH);
        } else if (interiorPhase === 'status') {
            renderStatus(ctx, canvasW, canvasH);
        }
    }

    function renderMainMenu(ctx, canvasW, canvasH) {
        const items = getMainMenu();
        const boxW = 200;
        const boxH = items.length * 28 + 50;
        const bx = (canvasW - boxW) / 2;
        const by = (canvasH - boxH) / 2;

        // NPC portrait area
        ctx.fillStyle = '#f0e8d0';
        ctx.fillRect(bx, by, boxW, boxH);
        ctx.strokeStyle = '#806040';
        ctx.lineWidth = 3;
        ctx.strokeRect(bx, by, boxW, boxH);

        // Title
        ctx.fillStyle = '#604020';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Daycare', bx + boxW / 2, by + 20);

        // Compatibility message
        if (daycareStatus && daycareStatus.compatibility_message) {
            ctx.font = '9px monospace';
            ctx.fillStyle = '#806040';
            ctx.fillText(daycareStatus.compatibility_message, bx + boxW / 2, by + 36);
        }

        // Menu items
        ctx.font = '13px monospace';
        for (let i = 0; i < items.length; i++) {
            const iy = by + 44 + i * 28;
            if (i === menuIndex) {
                ctx.fillStyle = '#c08040';
                ctx.fillRect(bx + 6, iy - 2, boxW - 12, 24);
                ctx.fillStyle = '#ffffff';
            } else {
                ctx.fillStyle = '#604020';
            }
            ctx.textAlign = 'left';
            ctx.fillText(items[i], bx + 26, iy + 14);
            if (i === menuIndex) ctx.fillText('\u25B6', bx + 10, iy + 14);
        }
        ctx.textAlign = 'left';
    }

    function renderDeposit(ctx, canvasW, canvasH) {
        const party = Game.player.party || [];
        const panelW = canvasW - 60;
        const panelH = Math.min(canvasH - 60, party.length * 40 + 60);
        const px = 30;
        const py = (canvasH - panelH) / 2;

        ctx.fillStyle = '#f0e8d0';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#806040';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, panelW, panelH);

        ctx.fillStyle = '#604020';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Choose Pokemon to Deposit', px + panelW / 2, py + 22);

        if (party.length <= 1) {
            ctx.font = '12px monospace';
            ctx.fillStyle = '#a08060';
            ctx.fillText("Can't deposit your last Pokemon!", px + panelW / 2, py + 50);
        }

        const TYPE_COLORS = {
            Grass: '#78c850', Fire: '#f08030', Water: '#6890f0',
            Normal: '#a8a878', Bug: '#a8b820', Flying: '#a890f0',
            Poison: '#a040a0', Electric: '#f8d030', Psychic: '#f85888',
            Ice: '#98d8d8', Rock: '#b8a038', Ground: '#e0c068',
        };

        for (let i = 0; i < party.length; i++) {
            const poke = party[i];
            const iy = py + 34 + i * 40;
            const iw = panelW - 20;
            const ix = px + 10;

            ctx.fillStyle = i === partyIndex ? 'rgba(192, 128, 64, 0.3)' : 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(ix, iy, iw, 36);
            if (i === partyIndex) {
                ctx.strokeStyle = '#c08040';
                ctx.lineWidth = 1;
                ctx.strokeRect(ix, iy, iw, 36);
            }

            // Type color icon
            ctx.fillStyle = TYPE_COLORS[poke.type] || '#a0a0a0';
            ctx.fillRect(ix + 4, iy + 4, 28, 28);
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(poke.is_egg ? '?' : poke.name[0], ix + 18, iy + 24);

            // Name and level
            ctx.fillStyle = '#604020';
            ctx.font = 'bold 13px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(poke.name, ix + 40, iy + 16);
            ctx.font = '11px monospace';
            ctx.fillText(`Lv${poke.level}`, ix + 40, iy + 30);

            // HP bar
            if (!poke.is_egg) {
                const barX = ix + iw - 110;
                const barW = 80;
                const hpRatio = poke.hp / poke.maxHp;
                ctx.fillStyle = '#303030';
                ctx.fillRect(barX, iy + 10, barW, 8);
                ctx.fillStyle = hpRatio < 0.2 ? '#e04038' : hpRatio < 0.5 ? '#f8c830' : '#48c048';
                ctx.fillRect(barX + 1, iy + 11, (barW - 2) * hpRatio, 6);
                ctx.fillStyle = '#806040';
                ctx.font = '9px monospace';
                ctx.textAlign = 'right';
                ctx.fillText(`${poke.hp}/${poke.maxHp}`, barX + barW, iy + 30);
            }
        }

        ctx.fillStyle = '#a08060';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('Z: Deposit | B/Esc: Back', px + panelW - 10, py + panelH - 8);
        ctx.textAlign = 'left';
    }

    function renderStatus(ctx, canvasW, canvasH) {
        const s = daycareStatus;
        const boxW = canvasW - 80;
        const boxH = 200;
        const bx = 40;
        const by = (canvasH - boxH) / 2;

        ctx.fillStyle = '#f0e8d0';
        ctx.fillRect(bx, by, boxW, boxH);
        ctx.strokeStyle = '#806040';
        ctx.lineWidth = 2;
        ctx.strokeRect(bx, by, boxW, boxH);

        ctx.fillStyle = '#604020';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Daycare Status', bx + boxW / 2, by + 24);

        // Slot 1
        const s1y = by + 40;
        ctx.font = 'bold 13px monospace';
        ctx.textAlign = 'left';
        ctx.fillText('Slot 1:', bx + 15, s1y + 14);
        if (s && s.slot_1) {
            ctx.font = '12px monospace';
            ctx.fillText(`${s.slot_1.name} Lv${s.slot_1.level}`, bx + 80, s1y + 14);
            ctx.fillStyle = '#a08060';
            ctx.fillText(`+${s.slot_1.steps_gained || 0} steps`, bx + 80, s1y + 30);
            ctx.fillStyle = '#604020';
        } else {
            ctx.font = '12px monospace';
            ctx.fillStyle = '#a08060';
            ctx.fillText('Empty', bx + 80, s1y + 14);
            ctx.fillStyle = '#604020';
        }

        // Slot 2
        const s2y = by + 80;
        ctx.font = 'bold 13px monospace';
        ctx.fillText('Slot 2:', bx + 15, s2y + 14);
        if (s && s.slot_2) {
            ctx.font = '12px monospace';
            ctx.fillText(`${s.slot_2.name} Lv${s.slot_2.level}`, bx + 80, s2y + 14);
            ctx.fillStyle = '#a08060';
            ctx.fillText(`+${s.slot_2.steps_gained || 0} steps`, bx + 80, s2y + 30);
            ctx.fillStyle = '#604020';
        } else {
            ctx.font = '12px monospace';
            ctx.fillStyle = '#a08060';
            ctx.fillText('Empty', bx + 80, s2y + 14);
            ctx.fillStyle = '#604020';
        }

        // Compatibility
        const cy = by + 130;
        ctx.font = 'bold 13px monospace';
        ctx.fillText('Compatibility:', bx + 15, cy + 14);
        if (s && s.slot_1 && s.slot_2) {
            // Draw hearts based on compatibility
            const heartX = bx + 130;
            if (s.compatible) {
                ctx.fillStyle = '#e04060';
                for (let i = 0; i < 3; i++) {
                    drawHeart(ctx, heartX + i * 20, cy + 4, 8);
                }
                ctx.fillStyle = '#604020';
                ctx.font = '11px monospace';
                ctx.fillText('Compatible!', bx + 200, cy + 14);
            } else {
                ctx.fillStyle = '#808080';
                drawHeart(ctx, heartX, cy + 4, 8);
                ctx.fillStyle = '#604020';
                ctx.font = '11px monospace';
                ctx.fillText('Incompatible', bx + 160, cy + 14);
            }
        } else {
            ctx.font = '11px monospace';
            ctx.fillStyle = '#a08060';
            ctx.fillText('Need 2 Pokemon', bx + 130, cy + 14);
        }

        // Compatibility message
        if (s && s.compatibility_message) {
            ctx.font = '10px monospace';
            ctx.fillStyle = '#806040';
            ctx.textAlign = 'center';
            ctx.fillText(`"${s.compatibility_message}"`, bx + boxW / 2, cy + 34);
        }

        // Egg ready indicator
        if (s && s.egg_ready) {
            ctx.fillStyle = '#e0a020';
            ctx.font = 'bold 12px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('An egg has been found!', bx + boxW / 2, by + boxH - 20);
        }

        // Back hint
        ctx.fillStyle = '#a08060';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('Press any key to close', bx + boxW - 10, by + boxH - 8);
        ctx.textAlign = 'left';
    }

    function drawHeart(ctx, x, y, size) {
        const s = size;
        ctx.beginPath();
        ctx.moveTo(x, y + s * 0.3);
        ctx.bezierCurveTo(x, y, x + s * 0.5, y, x + s * 0.5, y + s * 0.3);
        ctx.bezierCurveTo(x + s * 0.5, y, x + s, y, x + s, y + s * 0.3);
        ctx.bezierCurveTo(x + s, y + s * 0.6, x + s * 0.5, y + s * 0.9, x + s * 0.5, y + s);
        ctx.bezierCurveTo(x + s * 0.5, y + s * 0.9, x, y + s * 0.6, x, y + s * 0.3);
        ctx.fill();
    }

    // --- Egg Hatch Animation ---

    function startHatchAnimation() {
        hatchActive = true;
        hatchPhase = 'dark';
        hatchTimer = 0;
        hatchSparkles = [];
    }

    function isHatching() { return hatchActive; }

    function updateHatch(dt) {
        if (!hatchActive) return;
        hatchTimer += dt;
        actionCooldown = Math.max(0, actionCooldown - dt);

        // Update sparkles
        for (const sp of hatchSparkles) {
            sp.age += dt;
            sp.x += sp.vx * dt * 0.05;
            sp.y += sp.vy * dt * 0.05;
        }
        hatchSparkles = hatchSparkles.filter(s => s.age < s.life);

        // Phase transitions
        if (hatchPhase === 'dark' && hatchTimer > PHASE_DARK) {
            hatchPhase = 'rock';
            hatchTimer = 0;
        } else if (hatchPhase === 'rock' && hatchTimer > PHASE_ROCK) {
            hatchPhase = 'crack1';
            hatchTimer = 0;
        } else if (hatchPhase === 'crack1' && hatchTimer > PHASE_CRACK) {
            hatchPhase = 'crack2';
            hatchTimer = 0;
        } else if (hatchPhase === 'crack2' && hatchTimer > PHASE_CRACK) {
            hatchPhase = 'crack3';
            hatchTimer = 0;
        } else if (hatchPhase === 'crack3' && hatchTimer > PHASE_CRACK) {
            hatchPhase = 'flash';
            hatchTimer = 0;
            // Burst of sparkles
            for (let i = 0; i < 25; i++) {
                hatchSparkles.push(makeSparkle());
            }
        } else if (hatchPhase === 'flash' && hatchTimer > PHASE_FLASH) {
            hatchPhase = 'reveal';
            hatchTimer = 0;
            // Replace egg in party with hatched pokemon
            if (hatchPokemon && hatchEggIndex >= 0 && Game.player.party) {
                const p = hatchPokemon;
                Game.player.party[hatchEggIndex] = {
                    name: p.name,
                    type: p.types ? p.types[0] : 'Normal',
                    level: p.level || 1,
                    hp: p.current_hp || p.stats?.hp || 20,
                    maxHp: p.max_hp || p.stats?.hp || 20,
                    speciesId: p.id || 0,
                    is_egg: false,
                };
            }
        } else if (hatchPhase === 'reveal') {
            if (Math.random() < 0.05) hatchSparkles.push(makeSparkle());
            if (hatchTimer > PHASE_REVEAL || (Input.isActionPressed() && actionCooldown <= 0 && hatchTimer > 500)) {
                hatchPhase = 'done';
                hatchTimer = 0;
                actionCooldown = 300;
            }
        } else if (hatchPhase === 'done') {
            if (hatchTimer > 500 || (Input.isActionPressed() && actionCooldown <= 0)) {
                hatchActive = false;
                hatchPokemon = null;
                hatchEggIndex = -1;
            }
        }
    }

    function makeSparkle() {
        return {
            x: (Math.random() - 0.5) * 120,
            y: (Math.random() - 0.5) * 100,
            vx: (Math.random() - 0.5) * 3,
            vy: -Math.random() * 2 - 0.5,
            size: 2 + Math.random() * 5,
            age: 0,
            life: 800 + Math.random() * 600,
            color: Math.random() > 0.5 ? '#f8f8f8' : '#f8d830',
        };
    }

    function renderHatch(ctx, canvasW, canvasH) {
        if (!hatchActive) return;

        const cx = canvasW / 2;
        const cy = canvasH * 0.4;

        // Dark background
        ctx.fillStyle = '#080818';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Stars
        for (let i = 0; i < 40; i++) {
            const sx = ((37 * (i + 1) * 7) % canvasW);
            const sy = ((37 * (i + 1) * 13) % (canvasH * 0.7));
            const blink = Math.sin(Date.now() * 0.002 + i) * 0.3 + 0.7;
            ctx.fillStyle = `rgba(255, 255, 255, ${blink * 0.5})`;
            ctx.fillRect(sx, sy, 2, 2);
        }

        // Draw egg with animation phase
        if (hatchPhase === 'dark' || hatchPhase === 'rock' || hatchPhase === 'crack1' || hatchPhase === 'crack2' || hatchPhase === 'crack3') {
            // Rocking motion during rock phase
            let rockAngle = 0;
            if (hatchPhase === 'rock') {
                rockAngle = Math.sin(hatchTimer * 0.008) * 0.15;
            } else if (hatchPhase !== 'dark') {
                rockAngle = Math.sin(hatchTimer * 0.012) * 0.2;
            }

            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(rockAngle);
            drawEgg(ctx, 0, 0, 50);

            // Crack lines
            if (hatchPhase === 'crack1' || hatchPhase === 'crack2' || hatchPhase === 'crack3') {
                ctx.strokeStyle = '#604020';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(-5, -15);
                ctx.lineTo(3, -5);
                ctx.lineTo(-2, 5);
                ctx.stroke();
            }
            if (hatchPhase === 'crack2' || hatchPhase === 'crack3') {
                ctx.beginPath();
                ctx.moveTo(8, -20);
                ctx.lineTo(12, -8);
                ctx.lineTo(6, 2);
                ctx.lineTo(10, 10);
                ctx.stroke();
            }
            if (hatchPhase === 'crack3') {
                ctx.beginPath();
                ctx.moveTo(-10, -5);
                ctx.lineTo(-15, 5);
                ctx.lineTo(-8, 15);
                ctx.stroke();
                // Bright glow through cracks
                ctx.fillStyle = 'rgba(255, 255, 200, 0.5)';
                ctx.fillRect(-4, -14, 6, 8);
                ctx.fillRect(7, -18, 6, 10);
            }
            ctx.restore();

        } else if (hatchPhase === 'flash') {
            // White flash
            const flashAlpha = 1 - hatchTimer / PHASE_FLASH;
            ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);

        } else if (hatchPhase === 'reveal' || hatchPhase === 'done') {
            // Show hatched Pokemon
            if (hatchPokemon) {
                drawHatchedPokemon(ctx, cx, cy, hatchPokemon);
            }
        }

        // Sparkles
        for (const sp of hatchSparkles) {
            const alpha = 1 - sp.age / sp.life;
            ctx.globalAlpha = alpha;
            ctx.fillStyle = sp.color;
            const sx = cx + sp.x;
            const sy = cy + sp.y;
            ctx.beginPath();
            ctx.moveTo(sx, sy - sp.size);
            ctx.lineTo(sx + sp.size * 0.6, sy);
            ctx.lineTo(sx, sy + sp.size);
            ctx.lineTo(sx - sp.size * 0.6, sy);
            ctx.closePath();
            ctx.fill();
        }
        ctx.globalAlpha = 1;

        // Text box
        ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
        ctx.fillRect(20, canvasH - 70, canvasW - 40, 55);
        ctx.strokeStyle = '#f8f8f8';
        ctx.lineWidth = 2;
        ctx.strokeRect(20, canvasH - 70, canvasW - 40, 55);

        ctx.fillStyle = '#f8f8f8';
        ctx.font = '15px monospace';
        ctx.textAlign = 'center';

        if (hatchPhase === 'dark') {
            ctx.fillText('Oh?', canvasW / 2, canvasH - 40);
        } else if (hatchPhase === 'rock') {
            ctx.fillText('Your egg is moving!', canvasW / 2, canvasH - 40);
        } else if (hatchPhase === 'crack1' || hatchPhase === 'crack2') {
            ctx.fillText('It\'s about to hatch!', canvasW / 2, canvasH - 40);
        } else if (hatchPhase === 'crack3') {
            ctx.fillText('...!', canvasW / 2, canvasH - 40);
        } else if (hatchPhase === 'flash') {
            ctx.fillText('!!!', canvasW / 2, canvasH - 40);
        } else if (hatchPhase === 'reveal' || hatchPhase === 'done') {
            const name = hatchPokemon ? hatchPokemon.name : 'a Pokemon';
            ctx.fillText(`Your egg hatched into ${name}!`, canvasW / 2, canvasH - 40);
        }
        ctx.textAlign = 'left';
    }

    function drawEgg(ctx, cx, cy, size) {
        const hw = size * 0.4;
        const hh = size * 0.55;

        // Egg body (oval)
        ctx.fillStyle = '#f0e8d0';
        ctx.beginPath();
        ctx.ellipse(cx, cy, hw, hh, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#c0b088';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Pattern (zig-zag band)
        ctx.fillStyle = '#80c050';
        ctx.beginPath();
        const bandY = cy - hh * 0.15;
        for (let i = -4; i <= 4; i++) {
            const x = cx + (i / 4) * hw;
            const y = bandY + (i % 2 === 0 ? -4 : 4);
            if (i === -4) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        for (let i = 4; i >= -4; i--) {
            const x = cx + (i / 4) * hw;
            const y = bandY + (i % 2 === 0 ? 4 : 12);
            ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fill();

        // Egg highlight
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.beginPath();
        ctx.ellipse(cx - hw * 0.3, cy - hh * 0.4, hw * 0.2, hh * 0.25, -0.3, 0, Math.PI * 2);
        ctx.fill();
    }

    function drawHatchedPokemon(ctx, cx, cy, pokemon) {
        const TYPE_COLORS = {
            normal: '#a8a878', fire: '#f08030', water: '#6890f0', grass: '#78c850',
            electric: '#f8d030', ice: '#98d8d8', fighting: '#c03028', poison: '#a040a0',
            ground: '#e0c068', flying: '#a890f0', psychic: '#f85888', bug: '#a8b820',
            rock: '#b8a038', ghost: '#705898', dragon: '#7038f8', dark: '#705848',
            steel: '#b8b8d0', fairy: '#ee99ac',
        };
        const pType = pokemon.types ? pokemon.types[0] : 'normal';
        const color = TYPE_COLORS[pType.toLowerCase()] || '#a0a0a0';

        // Body
        const size = 70;
        const half = size / 2;
        ctx.fillStyle = color;
        ctx.fillRect(cx - half * 0.6, cy - half * 0.6, size * 0.6, size * 0.7);
        ctx.fillRect(cx - half * 0.4, cy - half * 0.8, size * 0.4, size * 0.3);

        // Eyes
        ctx.fillStyle = '#202020';
        ctx.fillRect(cx - half * 0.3, cy - half * 0.4, 4, 4);
        ctx.fillRect(cx + half * 0.1, cy - half * 0.4, 4, 4);

        // Name
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(pokemon.name, cx, cy + half + 20);
        ctx.font = '12px monospace';
        ctx.fillStyle = '#c0c0c0';
        ctx.fillText(`Lv${pokemon.level || 1}`, cx, cy + half + 36);
        ctx.textAlign = 'left';
    }

    // --- Daycare NPC sprite (rendered on overworld) ---

    function renderNpc(ctx, camX, camY, scale, mapId) {
        if (mapId !== DAYCARE_NPC.mapId) return;

        const screenX = (DAYCARE_NPC.x * TILE - camX) * scale;
        const screenY = (DAYCARE_NPC.y * TILE - camY) * scale;
        const s = scale;

        // Old man with hat
        // Hat
        ctx.fillStyle = '#a07030';
        ctx.fillRect(screenX + 3 * s, screenY, 10 * s, 3 * s);
        ctx.fillRect(screenX + 5 * s, screenY - s, 6 * s, 2 * s);
        // Face
        ctx.fillStyle = '#f8c098';
        ctx.fillRect(screenX + 4 * s, screenY + 3 * s, 8 * s, 5 * s);
        // Eyes
        ctx.fillStyle = '#202020';
        ctx.fillRect(screenX + 5 * s, screenY + 5 * s, 2 * s, 2 * s);
        ctx.fillRect(screenX + 9 * s, screenY + 5 * s, 2 * s, 2 * s);
        // Overalls
        ctx.fillStyle = '#4060a0';
        ctx.fillRect(screenX + 3 * s, screenY + 8 * s, 10 * s, 5 * s);
        // Shirt
        ctx.fillStyle = '#e0e0e0';
        ctx.fillRect(screenX + 5 * s, screenY + 8 * s, 6 * s, 2 * s);
        // Legs
        ctx.fillStyle = '#604020';
        ctx.fillRect(screenX + 4 * s, screenY + 13 * s, 3 * s, 3 * s);
        ctx.fillRect(screenX + 9 * s, screenY + 13 * s, 3 * s, 3 * s);

        // Egg ready indicator
        if (daycareStatus && daycareStatus.egg_ready) {
            // Exclamation mark above head
            const exY = screenY - 8 * s;
            ctx.fillStyle = '#e0a020';
            ctx.font = `bold ${12 * s}px monospace`;
            ctx.textAlign = 'center';
            ctx.fillText('!', screenX + 8 * s, exY);
            ctx.textAlign = 'left';
        }
    }

    // --- Egg rendering in party (for menu.js party screen) ---

    function isEgg(pokemon) {
        return pokemon && pokemon.is_egg === true;
    }

    function getEggProgress(pokemon) {
        if (!pokemon || !pokemon.is_egg) return 1;
        const total = HATCH_STEPS;
        const remaining = pokemon.hatch_counter || 0;
        return Math.max(0, Math.min(1, 1 - remaining / total));
    }

    function getEggSummary(pokemon) {
        if (!pokemon || !pokemon.is_egg) return '';
        const progress = getEggProgress(pokemon);
        if (progress > 0.9) return 'It will hatch soon!';
        if (progress > 0.5) return 'It moves occasionally.';
        if (progress > 0.2) return 'It appears to move sometimes.';
        return 'What will hatch from this egg?';
    }

    // --- Notification ---

    function showNotify(text) {
        notifyText = text;
        notifyTimer = 2000;
    }

    function updateNotify(dt) {
        if (notifyTimer > 0) notifyTimer = Math.max(0, notifyTimer - dt);
    }

    function renderNotify(ctx, canvasW, canvasH) {
        if (notifyTimer <= 0 || !notifyText) return;
        const alpha = Math.min(1, notifyTimer / 500);
        ctx.globalAlpha = alpha;
        const boxW = 220;
        const boxH = 30;
        const bx = (canvasW - boxW) / 2;
        const by = canvasH - 60;
        ctx.fillStyle = '#604020';
        ctx.fillRect(bx, by, boxW, boxH);
        ctx.strokeStyle = '#c08040';
        ctx.lineWidth = 2;
        ctx.strokeRect(bx, by, boxW, boxH);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(notifyText, canvasW / 2, by + 20);
        ctx.textAlign = 'left';
        ctx.globalAlpha = 1;
    }

    return {
        loadStatus,
        onStep,
        checkNpcInteraction,
        openInterior,
        closeInterior,
        isInteriorActive,
        updateInterior,
        renderInterior,
        isHatching,
        updateHatch,
        renderHatch,
        renderNpc,
        isEgg,
        getEggProgress,
        getEggSummary,
        updateNotify,
        renderNotify,
        DAYCARE_NPC,
    };
})();
