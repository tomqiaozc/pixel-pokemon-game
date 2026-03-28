// trading.js — Pokemon Trading System UI (Sprint 6)

const Trading = (() => {
    let active = false;
    // Phases: connect, code_entry, waiting, selecting, partner_wait, preview, confirming, partner_confirm, animating, done
    let phase = 'connect';
    let actionCooldown = 0;
    let selectedIndex = 0;
    let partnerSelectedIndex = -1;
    let tradeAnimation = 0;
    let confirmed = false;
    let partnerConfirmed = false;
    let waitTimer = 0;
    let codeDigits = [0, 0, 0, 0, 0, 0, 0, 0];
    let codeIndex = 0;
    let connectOption = 0; // 0=Quick Match, 1=Trade Code, 2=Cancel

    // Fallback partner data (used when backend is unavailable)
    const MOCK_PARTNERS = [
        { name: 'BLUE', id: 'TR-4829' },
        { name: 'LANCE', id: 'TR-7712' },
        { name: 'MISTY', id: 'TR-2205' },
    ];
    let partnerTrainer = null;
    let partnerParty = [];

    // Backend session state
    let sessionId = null;
    let pollTimer = 0;
    const POLL_INTERVAL = 2000;
    let useMock = false; // falls back to mock if backend unavailable

    // Type colors for display
    const TYPE_COLORS = {
        Grass: '#78c850', Fire: '#f08030', Water: '#6890f0',
        Normal: '#a8a878', Bug: '#a8b820', Flying: '#a890f0',
        Poison: '#a040a0', Electric: '#f8d030', Ground: '#e0c068',
        Rock: '#b8a038', Ice: '#98d8d8', Dragon: '#7038f8',
        Psychic: '#f85888', Ghost: '#705898', Dark: '#705848',
        Steel: '#b8b8d0', Fighting: '#c03028', Fairy: '#ee99ac',
    };

    function open() {
        active = true;
        phase = 'connect';
        actionCooldown = 250;
        selectedIndex = 0;
        partnerSelectedIndex = -1;
        partnerTrainer = null;
        partnerParty = [];
        tradeAnimation = 0;
        confirmed = false;
        partnerConfirmed = false;
        waitTimer = 0;
        codeDigits = [0, 0, 0, 0, 0, 0, 0, 0];
        codeIndex = 0;
        connectOption = 0;
        sessionId = null;
        pollTimer = 0;
        useMock = false;
    }

    function close() {
        active = false;
        phase = 'connect';
    }

    function isActive() { return active; }

    // Generate mock partner party based on partner name
    function generatePartnerParty(partnerName) {
        const parties = {
            'BLUE': [
                { name: 'Pidgeot', level: 38, type: 'Flying', hp: 98, maxHp: 98 },
                { name: 'Alakazam', level: 40, type: 'Psychic', hp: 88, maxHp: 88 },
                { name: 'Rhydon', level: 37, type: 'Ground', hp: 105, maxHp: 105 },
                { name: 'Gyarados', level: 39, type: 'Water', hp: 110, maxHp: 110 },
                { name: 'Arcanine', level: 41, type: 'Fire', hp: 108, maxHp: 108 },
            ],
            'LANCE': [
                { name: 'Dragonite', level: 50, type: 'Dragon', hp: 140, maxHp: 140 },
                { name: 'Aerodactyl', level: 45, type: 'Rock', hp: 95, maxHp: 95 },
                { name: 'Charizard', level: 47, type: 'Fire', hp: 115, maxHp: 115 },
            ],
            'MISTY': [
                { name: 'Starmie', level: 35, type: 'Water', hp: 85, maxHp: 85 },
                { name: 'Golduck', level: 33, type: 'Water', hp: 92, maxHp: 92 },
                { name: 'Lapras', level: 36, type: 'Water', hp: 130, maxHp: 130 },
                { name: 'Vaporeon', level: 34, type: 'Water', hp: 125, maxHp: 125 },
            ],
        };
        return parties[partnerName] || [
            { name: 'Rattata', level: 10, type: 'Normal', hp: 30, maxHp: 30 },
        ];
    }

    function getPlayerParty() {
        return Game.player.party || [];
    }

    function canTrade(partyIndex) {
        const party = getPlayerParty();
        // Can't trade last Pokemon
        if (party.length <= 1) return { ok: false, reason: 'Cannot trade your last Pokemon!' };
        return { ok: true };
    }

    function update(dt) {
        if (!active) return;
        actionCooldown = Math.max(0, actionCooldown - dt);

        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (phase === 'connect') {
            updateConnect(dt, mov, action, back);
        } else if (phase === 'code_entry') {
            updateCodeEntry(dt, mov, action, back);
        } else if (phase === 'waiting') {
            updateWaiting(dt, action, back);
        } else if (phase === 'selecting') {
            updateSelecting(dt, mov, action, back);
        } else if (phase === 'partner_wait') {
            updatePartnerWait(dt, action, back);
        } else if (phase === 'preview') {
            updatePreview(dt, mov, action, back);
        } else if (phase === 'confirming') {
            updateConfirming(dt, mov, action, back);
        } else if (phase === 'partner_confirm') {
            updatePartnerConfirm(dt, action, back);
        } else if (phase === 'animating') {
            updateAnimation(dt);
        } else if (phase === 'done') {
            if (action || back) { close(); actionCooldown = 200; }
        }
    }

    function updateConnect(dt, mov, action, back) {
        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { connectOption = Math.max(0, connectOption - 1); actionCooldown = 150; }
            if (mov.dy > 0) { connectOption = Math.min(2, connectOption + 1); actionCooldown = 150; }
        }
        if (action) {
            actionCooldown = 200;
            if (connectOption === 0) {
                // Quick match — create trade session via backend
                phase = 'waiting';
                waitTimer = 0;
                API.tradeCreate().then(data => {
                    if (data && data.session) {
                        sessionId = data.session.id;
                    } else {
                        useMock = true;
                    }
                });
            } else if (connectOption === 1) {
                // Trade code
                phase = 'code_entry';
                codeDigits = [0, 0, 0, 0, 0, 0, 0, 0];
                codeIndex = 0;
            } else {
                close();
            }
        }
        if (back) { close(); actionCooldown = 200; }
    }

    function updateCodeEntry(dt, mov, action, back) {
        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) {
                codeDigits[codeIndex] = (codeDigits[codeIndex] + 1) % 10;
                actionCooldown = 120;
            }
            if (mov.dy > 0) {
                codeDigits[codeIndex] = (codeDigits[codeIndex] + 9) % 10;
                actionCooldown = 120;
            }
            if (mov.dx > 0) {
                codeIndex = Math.min(7, codeIndex + 1);
                actionCooldown = 120;
            }
            if (mov.dx < 0) {
                codeIndex = Math.max(0, codeIndex - 1);
                actionCooldown = 120;
            }
        }
        if (action) {
            // Submit code — join trade session via backend
            const code = codeDigits.join('');
            phase = 'waiting';
            waitTimer = 0;
            actionCooldown = 200;
            API.tradeJoin(code).then(data => {
                if (data && data.session) {
                    sessionId = data.session.id;
                    if (data.player1_team) {
                        partnerTrainer = { name: 'Partner', id: data.session.player1_id || 'TR-????' };
                        partnerParty = (data.player1_team || []).map(p => ({
                            name: p.name, level: p.level || 10,
                            type: (p.types && p.types[0]) || p.type || 'Normal',
                            hp: p.current_hp || p.hp || 50, maxHp: (p.stats && p.stats.hp) || p.max_hp || p.maxHp || 50,
                        }));
                    }
                } else {
                    useMock = true;
                }
            });
        }
        if (back) { phase = 'connect'; actionCooldown = 200; }
    }

    function updateWaiting(dt, action, back) {
        waitTimer += dt;
        pollTimer += dt;

        if (sessionId && !useMock && pollTimer >= POLL_INTERVAL) {
            pollTimer = 0;
            API.tradeStatus(sessionId).then(data => {
                if (data && data.session && data.session.player2_id) {
                    // Partner found
                    partnerTrainer = { name: 'Partner', id: data.session.player2_id };
                    partnerParty = (data.player2_team || []).map(p => ({
                        name: p.name, level: p.level || 10,
                        type: (p.types && p.types[0]) || p.type || 'Normal',
                        hp: p.current_hp || p.hp || 50, maxHp: p.max_hp || p.maxHp || 50,
                    }));
                    if (partnerParty.length === 0) {
                        partnerParty = generatePartnerParty('BLUE');
                    }
                    phase = 'selecting';
                    selectedIndex = 0;
                    partnerSelectedIndex = -1;
                    actionCooldown = 300;
                }
            });
        }

        // Mock fallback after timeout
        if ((useMock || !sessionId) && waitTimer > 3000) {
            const idx = Math.floor(Math.random() * MOCK_PARTNERS.length);
            partnerTrainer = MOCK_PARTNERS[idx];
            partnerParty = generatePartnerParty(partnerTrainer.name);
            phase = 'selecting';
            selectedIndex = 0;
            partnerSelectedIndex = -1;
            actionCooldown = 300;
        }
        if (back) {
            if (sessionId) API.tradeDelete(sessionId);
            phase = 'connect';
            sessionId = null;
            actionCooldown = 200;
        }
    }

    function updateSelecting(dt, mov, action, back) {
        const party = getPlayerParty();
        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { selectedIndex = Math.max(0, selectedIndex - 1); actionCooldown = 150; }
            if (mov.dy > 0) { selectedIndex = Math.min(Math.max(0, party.length - 1), selectedIndex + 1); actionCooldown = 150; }
        }
        if (action && party.length > 0) {
            const check = canTrade(selectedIndex);
            if (!check.ok) {
                actionCooldown = 500;
            } else {
                // Offer pokemon via backend
                if (sessionId && !useMock) {
                    API.tradeOffer(sessionId, selectedIndex);
                }
                phase = 'partner_wait';
                waitTimer = 0;
                pollTimer = 0;
                actionCooldown = 200;
            }
        }
        if (back) {
            if (sessionId) API.tradeCancel(sessionId);
            phase = 'connect';
            partnerTrainer = null;
            partnerParty = [];
            sessionId = null;
            actionCooldown = 200;
        }
    }

    function updatePartnerWait(dt, action, back) {
        waitTimer += dt;
        pollTimer += dt;

        // Poll backend for partner's offer
        if (sessionId && !useMock && pollTimer >= POLL_INTERVAL) {
            pollTimer = 0;
            API.tradeStatus(sessionId).then(data => {
                if (data && data.session) {
                    const s = data.session;
                    // Check if partner has offered
                    const partnerOffer = s.player2_offer || s.player1_offer;
                    if (partnerOffer && partnerOffer.pokemon_index !== undefined) {
                        partnerSelectedIndex = partnerOffer.pokemon_index;
                        if (partnerSelectedIndex >= partnerParty.length) {
                            partnerSelectedIndex = 0;
                        }
                        phase = 'preview';
                        actionCooldown = 300;
                    }
                }
            });
        }

        // Mock fallback
        if ((useMock || !sessionId) && waitTimer > 2000) {
            partnerSelectedIndex = Math.floor(Math.random() * partnerParty.length);
            phase = 'preview';
            actionCooldown = 300;
        }
        if (back) {
            phase = 'selecting';
            actionCooldown = 200;
        }
    }

    function updatePreview(dt, mov, action, back) {
        if (action) {
            phase = 'confirming';
            confirmed = false;
            partnerConfirmed = false;
            actionCooldown = 200;
        }
        if (back) {
            phase = 'selecting';
            partnerSelectedIndex = -1;
            actionCooldown = 200;
        }
    }

    function updateConfirming(dt, mov, action, back) {
        if (action) {
            confirmed = true;
            // Confirm trade via backend
            if (sessionId && !useMock) {
                API.tradeConfirm(sessionId);
            }
            phase = 'partner_confirm';
            waitTimer = 0;
            pollTimer = 0;
            actionCooldown = 200;
        }
        if (back) {
            phase = 'preview';
            actionCooldown = 200;
        }
    }

    function updatePartnerConfirm(dt, action, back) {
        waitTimer += dt;
        pollTimer += dt;

        // Poll backend for partner confirmation
        if (sessionId && !useMock && pollTimer >= POLL_INTERVAL) {
            pollTimer = 0;
            API.tradeStatus(sessionId).then(data => {
                if (data && data.session) {
                    const s = data.session;
                    if (s.status === 'completed' || (s.player1_confirmed && s.player2_confirmed)) {
                        partnerConfirmed = true;
                        phase = 'animating';
                        tradeAnimation = 0;
                        actionCooldown = 200;
                    }
                }
            });
        }

        // Mock fallback
        if ((useMock || !sessionId) && waitTimer > 1500) {
            partnerConfirmed = true;
            phase = 'animating';
            tradeAnimation = 0;
            actionCooldown = 200;
        }
        if (back) {
            confirmed = false;
            if (sessionId && !useMock) API.tradeCancel(sessionId);
            phase = 'preview';
            actionCooldown = 200;
        }
    }

    function updateAnimation(dt) {
        tradeAnimation += dt;
        if (tradeAnimation > 4000) {
            // Execute the trade
            executeTrade();
            phase = 'done';
            actionCooldown = 300;
        }
    }

    function executeTrade() {
        const party = getPlayerParty();
        if (selectedIndex >= 0 && selectedIndex < party.length && partnerSelectedIndex >= 0) {
            const receivedPokemon = { ...partnerParty[partnerSelectedIndex] };
            receivedPokemon.originalTrainer = partnerTrainer.name;
            receivedPokemon.tradedPokemon = true;
            // EXP boost flag for traded Pokemon (1.5x)
            receivedPokemon.expBoost = 1.5;
            receivedPokemon.exp = 0;
            receivedPokemon.maxExp = 100;

            // Remove traded Pokemon, add received
            party.splice(selectedIndex, 1, receivedPokemon);

            // Track stats
            if (typeof PlayerStats !== 'undefined') {
                PlayerStats.increment('pokemonCaught');
            }
        }
    }

    // ---- Render Functions ----

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        // Full-screen background
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Title bar
        ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
        ctx.fillRect(0, 0, canvasW, 36);
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Trade Center', canvasW / 2, 24);

        if (partnerTrainer) {
            ctx.fillStyle = '#a0a0b0';
            ctx.font = '10px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(`Connected: ${partnerTrainer.name} (${partnerTrainer.id})`, canvasW - 10, 24);
        }

        if (phase === 'connect') {
            renderConnect(ctx, canvasW, canvasH);
        } else if (phase === 'code_entry') {
            renderCodeEntry(ctx, canvasW, canvasH);
        } else if (phase === 'waiting') {
            renderWaiting(ctx, canvasW, canvasH);
        } else if (phase === 'selecting') {
            renderTradeRoom(ctx, canvasW, canvasH);
        } else if (phase === 'partner_wait') {
            renderTradeRoom(ctx, canvasW, canvasH);
            renderWaitingOverlay(ctx, canvasW, canvasH, 'Waiting for partner to select...');
        } else if (phase === 'preview') {
            renderPreview(ctx, canvasW, canvasH);
        } else if (phase === 'confirming') {
            renderPreview(ctx, canvasW, canvasH);
            renderConfirmPrompt(ctx, canvasW, canvasH);
        } else if (phase === 'partner_confirm') {
            renderPreview(ctx, canvasW, canvasH);
            renderWaitingOverlay(ctx, canvasW, canvasH, 'Waiting for partner...');
        } else if (phase === 'animating') {
            renderAnimation(ctx, canvasW, canvasH);
        } else if (phase === 'done') {
            renderDone(ctx, canvasW, canvasH);
        }

        ctx.textAlign = 'left';
    }

    function renderConnect(ctx, canvasW, canvasH) {
        const centerY = canvasH / 2 - 40;
        const options = ['Quick Match', 'Trade Code', 'Cancel'];
        const descs = [
            'Find a random trade partner',
            'Enter an 8-digit code to match',
            'Return to the game',
        ];

        // Pokeball decoration
        drawPokeballIcon(ctx, canvasW / 2, centerY - 50, 20);

        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Connect to another trainer?', canvasW / 2, centerY - 20);

        for (let i = 0; i < options.length; i++) {
            const y = centerY + 20 + i * 48;
            const isSelected = i === connectOption;

            ctx.fillStyle = isSelected ? 'rgba(80, 80, 160, 0.5)' : 'rgba(255, 255, 255, 0.05)';
            ctx.fillRect(canvasW / 2 - 120, y - 8, 240, 40);
            if (isSelected) {
                ctx.strokeStyle = '#8080c0';
                ctx.lineWidth = 1;
                ctx.strokeRect(canvasW / 2 - 120, y - 8, 240, 40);
            }

            ctx.fillStyle = isSelected ? '#f8f8f8' : '#808090';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(options[i], canvasW / 2, y + 10);

            ctx.fillStyle = '#606070';
            ctx.font = '10px monospace';
            ctx.fillText(descs[i], canvasW / 2, y + 24);
        }

        renderControlHint(ctx, canvasW, canvasH, 'Z: Select | B: Back');
    }

    function renderCodeEntry(ctx, canvasW, canvasH) {
        const centerY = canvasH / 2 - 20;

        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Enter Trade Code', canvasW / 2, centerY - 30);

        ctx.fillStyle = '#606070';
        ctx.font = '10px monospace';
        ctx.fillText('Share this code with your trade partner', canvasW / 2, centerY - 12);

        // Code digit boxes
        const digitW = 28;
        const totalW = digitW * 8 + 7 * 6 + 10; // 8 digits + gaps + dash gap
        const startX = (canvasW - totalW) / 2;

        for (let i = 0; i < 8; i++) {
            const gap = i < 4 ? 0 : 10; // dash gap between 4th and 5th
            const x = startX + i * (digitW + 6) + gap;
            const y = centerY;

            const isCurrent = i === codeIndex;
            ctx.fillStyle = isCurrent ? 'rgba(80, 80, 200, 0.5)' : 'rgba(255, 255, 255, 0.1)';
            ctx.fillRect(x, y, digitW, 36);
            ctx.strokeStyle = isCurrent ? '#a0a0f0' : '#404060';
            ctx.lineWidth = isCurrent ? 2 : 1;
            ctx.strokeRect(x, y, digitW, 36);

            ctx.fillStyle = isCurrent ? '#f8f8f8' : '#a0a0b0';
            ctx.font = 'bold 18px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(`${codeDigits[i]}`, x + digitW / 2, y + 25);

            // Up/down arrows for current digit
            if (isCurrent) {
                ctx.fillStyle = '#8080c0';
                ctx.font = '10px monospace';
                ctx.fillText('\u25B2', x + digitW / 2, y - 4);
                ctx.fillText('\u25BC', x + digitW / 2, y + 48);
            }
        }

        // Dash between 4th and 5th digit
        const dashX = startX + 4 * (digitW + 6) - 2;
        ctx.fillStyle = '#606070';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('-', dashX, centerY + 24);

        renderControlHint(ctx, canvasW, canvasH, 'U/D: Digit | L/R: Move | Z: Connect | B: Back');
    }

    function renderWaiting(ctx, canvasW, canvasH) {
        const dots = '.'.repeat(Math.floor(waitTimer / 500) % 4);

        // Spinning Pokeball
        const angle = waitTimer * 0.004;
        const cx = canvasW / 2;
        const cy = canvasH / 2 - 20;
        const r = 18;

        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(angle);

        // Top half (red)
        ctx.fillStyle = '#e04040';
        ctx.beginPath();
        ctx.arc(0, 0, r, Math.PI, 0);
        ctx.fill();

        // Bottom half (white)
        ctx.fillStyle = '#f0f0f0';
        ctx.beginPath();
        ctx.arc(0, 0, r, 0, Math.PI);
        ctx.fill();

        // Center line
        ctx.strokeStyle = '#303030';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(-r, 0);
        ctx.lineTo(r, 0);
        ctx.stroke();

        // Center button
        ctx.fillStyle = '#f0f0f0';
        ctx.beginPath();
        ctx.arc(0, 0, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#303030';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.restore();

        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Searching for trade partner${dots}`, canvasW / 2, canvasH / 2 + 30);

        const elapsed = Math.floor(waitTimer / 1000);
        ctx.fillStyle = '#606070';
        ctx.font = '10px monospace';
        ctx.fillText(`Time: ${elapsed}s`, canvasW / 2, canvasH / 2 + 50);

        renderControlHint(ctx, canvasW, canvasH, 'B: Cancel');
    }

    function renderTradeRoom(ctx, canvasW, canvasH) {
        const party = getPlayerParty();
        const halfW = (canvasW - 20) / 2;
        const listY = 44;
        const listH = canvasH - 80;

        // Player's side (left)
        ctx.fillStyle = 'rgba(40, 40, 80, 0.4)';
        ctx.fillRect(5, listY, halfW, listH);
        ctx.strokeStyle = '#4040a0';
        ctx.lineWidth = 1;
        ctx.strokeRect(5, listY, halfW, listH);

        ctx.fillStyle = '#8080c0';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Your Pokemon', 5 + halfW / 2, listY + 16);

        renderPartyList(ctx, party, 5, listY + 22, halfW, selectedIndex, true);

        // Partner's side (right)
        const rightX = canvasW / 2 + 5;
        ctx.fillStyle = 'rgba(80, 40, 40, 0.4)';
        ctx.fillRect(rightX, listY, halfW, listH);
        ctx.strokeStyle = '#a04040';
        ctx.lineWidth = 1;
        ctx.strokeRect(rightX, listY, halfW, listH);

        ctx.fillStyle = '#c08080';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(partnerTrainer ? `${partnerTrainer.name}'s Pokemon` : 'Partner', rightX + halfW / 2, listY + 16);

        renderPartyList(ctx, partnerParty, rightX, listY + 22, halfW, -1, false);

        // Trade restriction warning
        if (party.length <= 1) {
            ctx.fillStyle = 'rgba(200, 40, 40, 0.8)';
            ctx.fillRect(canvasW / 2 - 130, canvasH - 56, 260, 20);
            ctx.fillStyle = '#f8f8f8';
            ctx.font = 'bold 10px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('Cannot trade your last Pokemon!', canvasW / 2, canvasH - 42);
        }

        renderControlHint(ctx, canvasW, canvasH, 'U/D: Select | Z: Offer | B: Disconnect');
    }

    function renderPartyList(ctx, party, x, y, w, selected, showCursor) {
        const slotH = 36;
        const padding = 4;

        for (let i = 0; i < Math.max(party.length, 1); i++) {
            const sy = y + i * (slotH + 2);
            const isSelected = showCursor && i === selected;

            if (i >= party.length) break;
            const poke = party[i];

            // Slot background
            ctx.fillStyle = isSelected ? 'rgba(80, 80, 180, 0.5)' : 'rgba(255, 255, 255, 0.05)';
            ctx.fillRect(x + padding, sy, w - padding * 2, slotH);
            if (isSelected) {
                ctx.strokeStyle = '#8080e0';
                ctx.lineWidth = 1;
                ctx.strokeRect(x + padding, sy, w - padding * 2, slotH);
            }

            // Type color indicator
            const typeColor = TYPE_COLORS[poke.type] || '#a0a0a0';
            ctx.fillStyle = typeColor;
            ctx.fillRect(x + padding + 4, sy + 6, 24, 24);
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(poke.name[0], x + padding + 16, sy + 23);

            // Name and level
            ctx.fillStyle = isSelected ? '#f8f8f8' : '#c0c0d0';
            ctx.font = '12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(poke.name, x + padding + 34, sy + 16);

            ctx.fillStyle = '#808090';
            ctx.font = '10px monospace';
            ctx.fillText(`Lv${poke.level}`, x + padding + 34, sy + 30);

            // Type badge
            ctx.fillStyle = typeColor;
            ctx.fillRect(x + w - padding - 52, sy + 14, 44, 14);
            ctx.fillStyle = '#ffffff';
            ctx.font = '9px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(poke.type, x + w - padding - 30, sy + 24);

            // Cursor arrow
            if (isSelected && showCursor) {
                ctx.fillStyle = '#f8d030';
                ctx.font = 'bold 12px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('\u25B6', x + padding - 2, sy + 22);
            }
        }

        if (party.length === 0) {
            ctx.fillStyle = '#606070';
            ctx.font = '11px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('No Pokemon', x + w / 2, y + 40);
        }
    }

    function renderPreview(ctx, canvasW, canvasH) {
        const party = getPlayerParty();
        const playerPoke = party[selectedIndex];
        const partnerPoke = partnerParty[partnerSelectedIndex];
        if (!playerPoke || !partnerPoke) return;

        const panelW = canvasW - 30;
        const panelH = canvasH - 60;
        const px = 15;
        const py = 42;

        // Panel background
        ctx.fillStyle = 'rgba(20, 20, 40, 0.95)';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#f8d030';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, panelW, panelH);

        // Title
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Trade Preview', px + panelW / 2, py + 20);

        const halfW = (panelW - 40) / 2;
        const cardY = py + 32;
        const cardH = panelH - 80;

        // Your Pokemon card (left)
        renderPokemonCard(ctx, playerPoke, px + 10, cardY, halfW, cardH, '#4040a0', 'Your Pokemon');

        // Trade arrows in center
        const arrowX = px + panelW / 2;
        const arrowY = cardY + cardH / 2;
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';

        const bounce = Math.sin(Date.now() * 0.004) * 4;
        ctx.fillText('\u2194', arrowX, arrowY + bounce);

        // Partner Pokemon card (right)
        renderPokemonCard(ctx, partnerPoke, px + panelW - halfW - 10, cardY, halfW, cardH, '#a04040', `${partnerTrainer.name}'s Pokemon`);

        // Traded Pokemon EXP boost note
        ctx.fillStyle = '#48c048';
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Traded Pokemon gain 1.5x EXP!', px + panelW / 2, py + panelH - 28);

        renderControlHint(ctx, canvasW, canvasH, 'Z: Accept Trade | B: Go Back');
    }

    function renderPokemonCard(ctx, poke, x, y, w, h, borderColor, label) {
        // Card background
        ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.fillRect(x, y, w, h);
        ctx.strokeStyle = borderColor;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, w, h);

        // Label
        ctx.fillStyle = borderColor;
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(label, x + w / 2, y + 12);

        // Pokemon sprite (type-colored square)
        const typeColor = TYPE_COLORS[poke.type] || '#a0a0a0';
        const spriteSize = Math.min(36, w - 20);
        ctx.fillStyle = typeColor;
        ctx.fillRect(x + (w - spriteSize) / 2, y + 18, spriteSize, spriteSize);
        ctx.fillStyle = '#ffffff';
        ctx.font = `bold ${Math.floor(spriteSize * 0.5)}px monospace`;
        ctx.textAlign = 'center';
        ctx.fillText(poke.name.substring(0, 3), x + w / 2, y + 18 + spriteSize * 0.65);

        // Name
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(poke.name, x + w / 2, y + 62);

        // Stats
        const statsY = y + 76;
        const statsX = x + 8;
        ctx.font = '10px monospace';
        ctx.textAlign = 'left';

        ctx.fillStyle = '#a0a0b0';
        ctx.fillText(`Level: `, statsX, statsY);
        ctx.fillStyle = '#f8f8f8';
        ctx.fillText(`${poke.level}`, statsX + 50, statsY);

        ctx.fillStyle = '#a0a0b0';
        ctx.fillText(`Type:  `, statsX, statsY + 14);
        ctx.fillStyle = typeColor;
        ctx.fillText(`${poke.type}`, statsX + 50, statsY + 14);

        ctx.fillStyle = '#a0a0b0';
        ctx.fillText(`HP:    `, statsX, statsY + 28);
        ctx.fillStyle = '#f8f8f8';
        ctx.fillText(`${poke.hp}/${poke.maxHp}`, statsX + 50, statsY + 28);

        // HP bar
        const barX = statsX;
        const barY = statsY + 34;
        const barW = w - 16;
        const hpRatio = poke.hp / poke.maxHp;
        ctx.fillStyle = '#303030';
        ctx.fillRect(barX, barY, barW, 6);
        ctx.fillStyle = hpRatio > 0.5 ? '#48c048' : hpRatio > 0.2 ? '#f8c830' : '#e04038';
        ctx.fillRect(barX, barY, barW * hpRatio, 6);

        // OT tag if traded
        if (poke.originalTrainer) {
            ctx.fillStyle = '#808090';
            ctx.font = '9px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`OT: ${poke.originalTrainer}`, statsX, barY + 16);
        }
    }

    function renderConfirmPrompt(ctx, canvasW, canvasH) {
        const party = getPlayerParty();
        const playerPoke = party[selectedIndex];
        const partnerPoke = partnerParty[partnerSelectedIndex];
        if (!playerPoke || !partnerPoke) return;

        // Overlay
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        const boxW = 280;
        const boxH = 70;
        const bx = (canvasW - boxW) / 2;
        const by = (canvasH - boxH) / 2;

        ctx.fillStyle = 'rgba(20, 20, 60, 0.95)';
        ctx.fillRect(bx, by, boxW, boxH);
        ctx.strokeStyle = '#f8d030';
        ctx.lineWidth = 2;
        ctx.strokeRect(bx, by, boxW, boxH);

        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 13px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Trade ${playerPoke.name}`, canvasW / 2, by + 22);
        ctx.fillText(`for ${partnerPoke.name}?`, canvasW / 2, by + 40);

        ctx.fillStyle = '#a0a0b0';
        ctx.font = '10px monospace';
        ctx.fillText('Z: Confirm | B: Cancel', canvasW / 2, by + 58);
    }

    function renderWaitingOverlay(ctx, canvasW, canvasH, text) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        const dots = '.'.repeat(Math.floor(waitTimer / 500) % 4);
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${text}${dots}`, canvasW / 2, canvasH / 2);

        ctx.fillStyle = '#808090';
        ctx.font = '10px monospace';
        ctx.fillText('B: Cancel', canvasW / 2, canvasH / 2 + 24);
    }

    function renderAnimation(ctx, canvasW, canvasH) {
        const progress = Math.min(1, tradeAnimation / 4000);
        const party = getPlayerParty();
        const playerPoke = party[selectedIndex];
        const partnerPoke = partnerParty[partnerSelectedIndex];

        // Dark background with stars
        ctx.fillStyle = '#0a0a1a';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Stars
        for (let i = 0; i < 20; i++) {
            const sx = (i * 37 + tradeAnimation * 0.02 * (i % 3 + 1)) % canvasW;
            const sy = (i * 23 + i * i * 7) % canvasH;
            ctx.fillStyle = `rgba(255, 255, 255, ${0.3 + Math.sin(tradeAnimation * 0.003 + i) * 0.3})`;
            ctx.fillRect(sx, sy, 2, 2);
        }

        const cx = canvasW / 2;
        const cy = canvasH / 2;

        if (progress < 0.3) {
            // Phase 1: Pokeballs rise from sides
            const p = progress / 0.3;
            const leftX = 60;
            const rightX = canvasW - 60;
            const riseY = canvasH - 60 - p * (canvasH / 2 - 60);

            drawPokeball(ctx, leftX, riseY, 14);
            drawPokeball(ctx, rightX, riseY, 14);

            // Labels
            if (playerPoke) {
                ctx.fillStyle = '#8080c0';
                ctx.font = '11px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(playerPoke.name, leftX, riseY + 24);
            }
            if (partnerPoke) {
                ctx.fillStyle = '#c08080';
                ctx.font = '11px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(partnerPoke.name, rightX, riseY + 24);
            }
        } else if (progress < 0.7) {
            // Phase 2: Pokeballs travel in arc, cross in middle
            const p = (progress - 0.3) / 0.4;
            const leftStartX = 60;
            const rightStartX = canvasW - 60;

            // Arc path
            const leftX = leftStartX + (rightStartX - leftStartX) * p;
            const rightX = rightStartX - (rightStartX - leftStartX) * p;
            const arcY = cy - Math.sin(p * Math.PI) * 80;

            drawPokeball(ctx, leftX, arcY, 14);
            drawPokeball(ctx, rightX, arcY, 14);

            // Sparkle trail
            for (let i = 0; i < 5; i++) {
                const trailP = Math.max(0, p - i * 0.04);
                const tlx = leftStartX + (rightStartX - leftStartX) * trailP;
                const trx = rightStartX - (rightStartX - leftStartX) * trailP;
                const tay = cy - Math.sin(trailP * Math.PI) * 80;
                const alpha = 0.4 - i * 0.08;
                ctx.fillStyle = `rgba(248, 208, 48, ${alpha})`;
                ctx.fillRect(tlx - 2, tay - 2, 4, 4);
                ctx.fillRect(trx - 2, tay - 2, 4, 4);
            }
        } else if (progress < 0.85) {
            // Phase 3: Flash/sparkle at landing positions
            const p = (progress - 0.7) / 0.15;
            const flashAlpha = Math.sin(p * Math.PI * 4) * 0.5 + 0.5;

            ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha * 0.6})`;
            ctx.fillRect(0, 0, canvasW, canvasH);

            // Sparkles
            for (let i = 0; i < 8; i++) {
                const angle = (i / 8) * Math.PI * 2 + tradeAnimation * 0.005;
                const dist = 20 + p * 30;
                const sx = cx + Math.cos(angle) * dist;
                const sy = cy + Math.sin(angle) * dist;
                ctx.fillStyle = '#f8d030';
                ctx.fillRect(sx - 2, sy - 2, 4, 4);
            }
        } else {
            // Phase 4: Reveal new Pokemon
            const p = (progress - 0.85) / 0.15;

            if (partnerPoke) {
                const typeColor = TYPE_COLORS[partnerPoke.type] || '#a0a0a0';
                const size = 40 * p;
                ctx.fillStyle = typeColor;
                ctx.globalAlpha = p;
                ctx.fillRect(cx - size / 2, cy - size / 2 - 20, size, size);
                ctx.fillStyle = '#ffffff';
                ctx.font = `bold ${Math.floor(size * 0.4)}px monospace`;
                ctx.textAlign = 'center';
                ctx.fillText(partnerPoke.name.substring(0, 3), cx, cy - 20 + size * 0.15);
                ctx.globalAlpha = 1;

                ctx.fillStyle = '#f8f8f8';
                ctx.font = 'bold 14px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(partnerPoke.name, cx, cy + 30);
                ctx.fillStyle = '#a0a0b0';
                ctx.font = '11px monospace';
                ctx.fillText(`Lv${partnerPoke.level}`, cx, cy + 46);
            }
        }

        // Progress text
        const messages = ['Initiating trade...', 'Exchanging Pokemon...', 'Almost done...', 'Trade complete!'];
        const msgIdx = Math.min(messages.length - 1, Math.floor(progress * messages.length));
        ctx.fillStyle = '#c0c0d0';
        ctx.font = '12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(messages[msgIdx], cx, canvasH - 30);
    }

    function renderDone(ctx, canvasW, canvasH) {
        const party = getPlayerParty();
        const receivedPoke = party[selectedIndex]; // Now the traded-in Pokemon
        const partnerPoke = partnerParty[partnerSelectedIndex];

        ctx.fillStyle = '#0a0a1a';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Celebration
        ctx.fillStyle = '#48c048';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Trade Complete!', canvasW / 2, canvasH / 2 - 50);

        if (receivedPoke) {
            const typeColor = TYPE_COLORS[receivedPoke.type] || '#a0a0a0';
            ctx.fillStyle = typeColor;
            ctx.fillRect(canvasW / 2 - 20, canvasH / 2 - 35, 40, 40);
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 16px monospace';
            ctx.fillText(receivedPoke.name.substring(0, 3), canvasW / 2, canvasH / 2 - 8);

            ctx.fillStyle = '#f8f8f8';
            ctx.font = 'bold 14px monospace';
            ctx.fillText(`${receivedPoke.name} joined your team!`, canvasW / 2, canvasH / 2 + 24);

            if (receivedPoke.originalTrainer) {
                ctx.fillStyle = '#808090';
                ctx.font = '10px monospace';
                ctx.fillText(`OT: ${receivedPoke.originalTrainer}`, canvasW / 2, canvasH / 2 + 42);
            }

            ctx.fillStyle = '#48c048';
            ctx.font = '10px monospace';
            ctx.fillText('This Pokemon gains 1.5x EXP!', canvasW / 2, canvasH / 2 + 58);
        }

        ctx.fillStyle = '#606070';
        ctx.font = '10px monospace';
        ctx.fillText('Press any key to exit', canvasW / 2, canvasH / 2 + 80);
    }

    function drawPokeball(ctx, x, y, r) {
        // Top half (red)
        ctx.fillStyle = '#e04040';
        ctx.beginPath();
        ctx.arc(x, y, r, Math.PI, 0);
        ctx.fill();

        // Bottom half (white)
        ctx.fillStyle = '#f0f0f0';
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI);
        ctx.fill();

        // Center line
        ctx.strokeStyle = '#303030';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x - r, y);
        ctx.lineTo(x + r, y);
        ctx.stroke();

        // Center button
        ctx.fillStyle = '#f0f0f0';
        ctx.beginPath();
        ctx.arc(x, y, r * 0.25, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#303030';
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }

    function drawPokeballIcon(ctx, x, y, r) {
        drawPokeball(ctx, x, y, r);
    }

    function renderControlHint(ctx, canvasW, canvasH, text) {
        ctx.fillStyle = '#404050';
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(text, canvasW / 2, canvasH - 8);
    }

    return { open, close, isActive, update, render };
})();
