// movetutor.js — Move Tutor NPC, TM/HM usage, and move replacement UI
// Provides: tutor interaction overlay, TM/HM learn flow, move replacement screen

const MoveTutor = (() => {
    const TILE = Sprites.TILE;

    // ---- Type colors for move display ----
    const TYPE_COLORS = {
        Normal: '#a8a878', Fire: '#f08030', Water: '#6890f0', Grass: '#78c850',
        Electric: '#f8d030', Ice: '#98d8d8', Fighting: '#c03028', Poison: '#a040a0',
        Ground: '#e0c068', Flying: '#a890f0', Psychic: '#f85888', Bug: '#a8b820',
        Rock: '#b8a038', Ghost: '#705898', Dragon: '#7038f8', Dark: '#705848',
        Steel: '#b8b8d0', Fairy: '#ee99ac',
    };

    // ---- State ----
    let active = false;
    let phase = 'select_move'; // select_move, select_pokemon, confirm, replace, teaching, done
    let actionCooldown = 0;

    // Move list from tutor/TM/HM
    let availableMoves = []; // [{ name, type, power, pp, maxPp, cost, isHM }]
    let moveIndex = 0;

    // Pokemon selection
    let partyIndex = 0;
    let compatibleParty = []; // indices into Game.player.party that can learn

    // Move replacement
    let replaceIndex = 0; // 0-3 for existing moves, 4 = cancel
    let newMove = null;   // the move being learned

    // Source: 'tutor', 'tm', 'hm'
    let source = 'tutor';
    let tutorNpcName = '';

    // Teaching animation
    let teachTimer = 0;
    let teachPokemonName = '';
    let teachMoveName = '';
    let teachSparkles = [];

    // Result message
    let resultMessage = '';
    let resultTimer = 0;

    // Backend data cache
    let tutorMovesCache = {};  // mapId -> moves array
    let tmInventory = [];       // [{ id, name, type, power, pp, isHM }]

    // ---- HM moves (non-deletable) ----
    const HM_MOVES = new Set(['Cut', 'Fly', 'Surf', 'Strength', 'Flash']);

    function isHMMove(moveName) {
        return HM_MOVES.has(moveName);
    }

    // ==================== TUTOR NPC ====================

    function openTutor(npcName, mapId) {
        active = true;
        source = 'tutor';
        phase = 'select_move';
        tutorNpcName = npcName;
        moveIndex = 0;
        partyIndex = 0;
        replaceIndex = 0;
        actionCooldown = 300;
        availableMoves = [];

        // Fetch tutor moves from backend
        API.getTutorMoves(mapId).then(data => {
            if (data && Array.isArray(data)) {
                availableMoves = data.map(m => ({
                    name: m.name,
                    type: m.type || 'Normal',
                    power: m.power || 0,
                    pp: m.pp || 10,
                    maxPp: m.max_pp || m.pp || 10,
                    cost: m.cost || 0,
                    isHM: false,
                }));
            }
            if (availableMoves.length === 0) {
                availableMoves = getLocalTutorMoves();
            }
        }).catch(() => {
            availableMoves = getLocalTutorMoves();
        });
    }

    function getLocalTutorMoves() {
        return [
            { name: 'Mega Punch', type: 'Normal', power: 80, pp: 20, maxPp: 20, cost: 3000, isHM: false },
            { name: 'Mega Kick', type: 'Normal', power: 120, pp: 5, maxPp: 5, cost: 5000, isHM: false },
            { name: 'Thunder Wave', type: 'Electric', power: 0, pp: 20, maxPp: 20, cost: 2000, isHM: false },
            { name: 'Seismic Toss', type: 'Fighting', power: 0, pp: 20, maxPp: 20, cost: 4000, isHM: false },
            { name: 'Softboiled', type: 'Normal', power: 0, pp: 10, maxPp: 10, cost: 5000, isHM: false },
            { name: 'Dream Eater', type: 'Psychic', power: 100, pp: 15, maxPp: 15, cost: 4000, isHM: false },
        ];
    }

    // ==================== TM/HM USAGE ====================

    function openTM(tmItem) {
        active = true;
        source = tmItem.isHM ? 'hm' : 'tm';
        phase = 'select_pokemon';
        moveIndex = 0;
        partyIndex = 0;
        replaceIndex = 0;
        actionCooldown = 300;

        newMove = {
            name: tmItem.moveName || tmItem.name,
            type: tmItem.moveType || tmItem.type || 'Normal',
            power: tmItem.movePower || tmItem.power || 0,
            pp: tmItem.movePP || tmItem.pp || 10,
            maxPp: tmItem.moveMaxPP || tmItem.maxPp || tmItem.pp || 10,
            isHM: !!tmItem.isHM,
            itemId: tmItem.id || tmItem.item_id || null,
        };

        // All party Pokemon shown; compatibility check on selection
        compatibleParty = [];
        const party = Game.player.party;
        for (let i = 0; i < party.length; i++) {
            if (!party[i].is_egg) compatibleParty.push(i);
        }
    }

    // ==================== MOVE REMINDER ====================

    function openReminder(npcName) {
        active = true;
        source = 'reminder';
        phase = 'select_pokemon';
        tutorNpcName = npcName;
        moveIndex = 0;
        partyIndex = 0;
        replaceIndex = 0;
        actionCooldown = 300;
        availableMoves = [];
        compatibleParty = [];

        const party = Game.player.party;
        for (let i = 0; i < party.length; i++) {
            if (!party[i].is_egg) compatibleParty.push(i);
        }
    }

    // ==================== UPDATE ====================

    function isActive() { return active; }

    function close() {
        active = false;
        phase = 'select_move';
        availableMoves = [];
        compatibleParty = [];
    }

    function update(dt) {
        if (!active) return;
        actionCooldown = Math.max(0, actionCooldown - dt);

        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (phase === 'select_move') {
            updateSelectMove(mov, action, back);
        } else if (phase === 'select_pokemon') {
            updateSelectPokemon(mov, action, back);
        } else if (phase === 'confirm') {
            updateConfirm(action, back);
        } else if (phase === 'replace') {
            updateReplace(mov, action, back);
        } else if (phase === 'teaching') {
            updateTeaching(dt, action);
        } else if (phase === 'done') {
            resultTimer += dt;
            if (resultTimer > 2000 || action) {
                close();
            }
        }
    }

    function updateSelectMove(mov, action, back) {
        if (back) { close(); return; }
        if (availableMoves.length === 0) return;

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { moveIndex = Math.max(0, moveIndex - 1); actionCooldown = 120; }
            if (mov.dy > 0) { moveIndex = Math.min(availableMoves.length - 1, moveIndex + 1); actionCooldown = 120; }
        }

        if (action) {
            actionCooldown = 200;
            newMove = availableMoves[moveIndex];

            // Go to Pokemon selection
            compatibleParty = [];
            const party = Game.player.party;
            for (let i = 0; i < party.length; i++) {
                if (!party[i].is_egg) compatibleParty.push(i);
            }
            if (compatibleParty.length > 0) {
                partyIndex = 0;
                phase = 'select_pokemon';
            }
        }
    }

    function updateSelectPokemon(mov, action, back) {
        if (back) {
            if (source === 'tutor') { phase = 'select_move'; }
            else { close(); }
            actionCooldown = 200;
            return;
        }

        if (compatibleParty.length === 0) return;

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { partyIndex = Math.max(0, partyIndex - 1); actionCooldown = 120; }
            if (mov.dy > 0) { partyIndex = Math.min(compatibleParty.length - 1, partyIndex + 1); actionCooldown = 120; }
        }

        if (action) {
            actionCooldown = 200;
            const pokemonIdx = compatibleParty[partyIndex];
            const pokemon = Game.player.party[pokemonIdx];

            // For reminder source, load forgotten moves for this Pokemon
            if (source === 'reminder') {
                API.getReminderMoves(pokemonIdx).then(data => {
                    const moveList = data && data.forgotten_moves ? data.forgotten_moves
                                   : (data && Array.isArray(data) ? data : []);
                    if (moveList.length > 0) {
                        availableMoves = moveList.map(m => ({
                            name: m.name,
                            type: m.type || 'Normal',
                            power: m.power || 0,
                            pp: m.pp || 10,
                            maxPp: m.max_pp || m.pp || 10,
                            cost: 0,
                            isHM: false,
                        }));
                    } else {
                        availableMoves = [];
                    }
                    if (availableMoves.length > 0) {
                        moveIndex = 0;
                        phase = 'select_move';
                    } else {
                        resultMessage = `${pokemon.name} has no moves to remember!`;
                        resultTimer = 0;
                        phase = 'done';
                    }
                }).catch(() => {
                    resultMessage = `${pokemon.name} has no moves to remember!`;
                    resultTimer = 0;
                    phase = 'done';
                });
                return;
            }

            // Check compatibility with backend
            API.checkMoveCompatibility(pokemonIdx, newMove.name).then(data => {
                if (data && data.compatible === false) {
                    resultMessage = `${pokemon.name} can't learn ${newMove.name}!`;
                    resultTimer = 0;
                    phase = 'done';
                } else {
                    proceedToLearn(pokemonIdx);
                }
            }).catch(() => {
                // Backend unavailable — proceed anyway (local)
                proceedToLearn(pokemonIdx);
            });
        }
    }

    function proceedToLearn(pokemonIdx) {
        const pokemon = Game.player.party[pokemonIdx];
        const moves = pokemon.moves || [];

        if (moves.length < 4 || moves.some(m => m.name === '---')) {
            // Has an empty slot — learn directly
            startTeaching(pokemonIdx);
        } else {
            // 4 moves — need replacement
            replaceIndex = 0;
            phase = 'replace';
        }
    }

    function updateConfirm(action, back) {
        if (back) { phase = 'select_pokemon'; actionCooldown = 200; return; }
        if (action) {
            actionCooldown = 200;
            const pokemonIdx = compatibleParty[partyIndex];
            startTeaching(pokemonIdx);
        }
    }

    function updateReplace(mov, action, back) {
        if (back) { phase = 'select_pokemon'; actionCooldown = 200; return; }

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { replaceIndex = Math.max(0, replaceIndex - 1); actionCooldown = 120; }
            if (mov.dy > 0) { replaceIndex = Math.min(4, replaceIndex + 1); actionCooldown = 120; }
        }

        if (action) {
            actionCooldown = 200;
            if (replaceIndex === 4) {
                // Cancel — don't learn
                resultMessage = `${Game.player.party[compatibleParty[partyIndex]].name} did not learn ${newMove.name}.`;
                resultTimer = 0;
                phase = 'done';
                return;
            }

            const pokemonIdx = compatibleParty[partyIndex];
            const pokemon = Game.player.party[pokemonIdx];
            const oldMove = pokemon.moves[replaceIndex];

            // HM moves can't be deleted
            if (isHMMove(oldMove.name)) {
                resultMessage = `HM moves can't be forgotten!`;
                resultTimer = 0;
                // Stay in replace phase
                return;
            }

            // Replace the move
            startTeaching(pokemonIdx, replaceIndex);
        }
    }

    function startTeaching(pokemonIdx, replaceSlot) {
        const pokemon = Game.player.party[pokemonIdx];
        teachPokemonName = pokemon.name;
        teachMoveName = newMove.name;
        teachTimer = 0;
        teachSparkles = [];
        phase = 'teaching';

        // Charge tutor move cost
        if (source === 'tutor' && newMove.cost > 0) {
            const currentMoney = PlayerStats.get('money') || 0;
            PlayerStats.set('money', Math.max(0, currentMoney - newMove.cost));
        }

        // Apply the move locally
        if (!pokemon.moves) pokemon.moves = [];

        if (replaceSlot !== undefined && replaceSlot >= 0) {
            pokemon.moves[replaceSlot] = {
                name: newMove.name,
                type: newMove.type,
                power: newMove.power,
                pp: newMove.pp,
                maxPp: newMove.maxPp,
            };
        } else {
            // Find empty slot or append
            const emptyIdx = pokemon.moves.findIndex(m => m.name === '---');
            if (emptyIdx >= 0) {
                pokemon.moves[emptyIdx] = {
                    name: newMove.name,
                    type: newMove.type,
                    power: newMove.power,
                    pp: newMove.pp,
                    maxPp: newMove.maxPp,
                };
            } else if (pokemon.moves.length < 4) {
                pokemon.moves.push({
                    name: newMove.name,
                    type: newMove.type,
                    power: newMove.power,
                    pp: newMove.pp,
                    maxPp: newMove.maxPp,
                });
            }
        }

        // Notify backend (fire-and-forget)
        API.teachMove(pokemonIdx, newMove.name, replaceSlot).catch(() => {});

        // Consume TM if source is 'tm' (HMs are reusable)
        if (source === 'tm') {
            API.useItem(newMove.itemId, pokemonIdx).catch(() => {});
        }

        PlayerStats.increment('movesLearned');
    }

    function updateTeaching(dt, action) {
        teachTimer += dt;

        // Spawn sparkles
        if (teachTimer % 80 < dt) {
            teachSparkles.push({
                x: 0.3 + Math.random() * 0.4,
                y: 0.3 + Math.random() * 0.3,
                age: 0,
                vx: (Math.random() - 0.5) * 0.001,
                vy: -Math.random() * 0.001,
            });
        }
        for (const s of teachSparkles) {
            s.age += dt;
            s.x += s.vx * dt;
            s.y += s.vy * dt;
        }
        teachSparkles = teachSparkles.filter(s => s.age < 600);

        if (teachTimer > 1800 || (teachTimer > 800 && action)) {
            resultMessage = `${teachPokemonName} learned ${teachMoveName}!`;
            resultTimer = 0;
            phase = 'done';
            Achievements.checkAchievements();
        }
    }

    // ==================== RENDER ====================

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        // Dark overlay
        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        if (phase === 'select_move') {
            renderSelectMove(ctx, canvasW, canvasH);
        } else if (phase === 'select_pokemon') {
            renderSelectPokemon(ctx, canvasW, canvasH);
        } else if (phase === 'replace') {
            renderReplace(ctx, canvasW, canvasH);
        } else if (phase === 'teaching') {
            renderTeaching(ctx, canvasW, canvasH);
        } else if (phase === 'done') {
            renderResult(ctx, canvasW, canvasH);
        }
    }

    function renderSelectMove(ctx, canvasW, canvasH) {
        // Title
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        const title = source === 'reminder' ? 'MOVE REMINDER' : 'MOVE TUTOR';
        ctx.fillText(title, canvasW / 2, 30);

        if (source === 'tutor') {
            ctx.fillStyle = '#a0a0a0';
            ctx.font = '11px monospace';
            ctx.fillText(tutorNpcName, canvasW / 2, 46);
        }

        if (availableMoves.length === 0) {
            ctx.fillStyle = '#c0c0c0';
            ctx.font = '12px monospace';
            ctx.fillText('Loading moves...', canvasW / 2, canvasH / 2);
            ctx.textAlign = 'left';
            return;
        }

        // Move list
        const listY = 58;
        const itemH = 32;
        const maxVisible = Math.min(availableMoves.length, 6);
        const scrollOffset = Math.max(0, moveIndex - 4);

        for (let i = 0; i < maxVisible; i++) {
            const mi = i + scrollOffset;
            if (mi >= availableMoves.length) break;
            const move = availableMoves[mi];
            const y = listY + i * itemH;

            // Highlight
            if (mi === moveIndex) {
                ctx.fillStyle = 'rgba(248,216,48,0.15)';
                ctx.fillRect(20, y - 2, canvasW - 40, itemH - 2);
                ctx.strokeStyle = '#f8d030';
                ctx.lineWidth = 1;
                ctx.strokeRect(20, y - 2, canvasW - 40, itemH - 2);
            }

            // Type color bar
            const typeColor = TYPE_COLORS[move.type] || '#a8a878';
            ctx.fillStyle = typeColor;
            ctx.fillRect(24, y + 2, 4, itemH - 6);

            // Move name
            ctx.fillStyle = '#f8f8f8';
            ctx.font = '12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(move.name, 34, y + 14);

            // Type
            ctx.fillStyle = typeColor;
            ctx.font = '10px monospace';
            ctx.fillText(move.type, 34, y + 24);

            // Power / PP
            ctx.fillStyle = '#c0c0c0';
            ctx.textAlign = 'right';
            ctx.font = '10px monospace';
            const pwrText = move.power > 0 ? `PWR:${move.power}` : 'Status';
            ctx.fillText(`${pwrText}  PP:${move.pp}`, canvasW - 30, y + 14);

            // Cost
            if (move.cost > 0) {
                ctx.fillStyle = '#f8d030';
                ctx.fillText(`$${move.cost}`, canvasW - 30, y + 24);
            }
        }

        // Controls
        ctx.fillStyle = '#606060';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Z: Select | Esc: Back', canvasW / 2, canvasH - 12);
        ctx.textAlign = 'left';
    }

    function renderSelectPokemon(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('SELECT POKEMON', canvasW / 2, 30);

        if (newMove) {
            ctx.fillStyle = '#c0c0c0';
            ctx.font = '11px monospace';
            ctx.fillText(`Teaching: ${newMove.name} (${newMove.type})`, canvasW / 2, 46);
        }

        const party = Game.player.party;
        const listY = 60;
        const itemH = 34;

        for (let i = 0; i < compatibleParty.length; i++) {
            const pi = compatibleParty[i];
            const pokemon = party[pi];
            const y = listY + i * itemH;

            // Highlight
            if (i === partyIndex) {
                ctx.fillStyle = 'rgba(248,216,48,0.15)';
                ctx.fillRect(20, y - 2, canvasW - 40, itemH - 2);
                ctx.strokeStyle = '#f8d030';
                ctx.lineWidth = 1;
                ctx.strokeRect(20, y - 2, canvasW - 40, itemH - 2);
            }

            // Pokemon name and level
            ctx.fillStyle = '#f8f8f8';
            ctx.font = '12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(pokemon.name, 30, y + 14);

            ctx.fillStyle = '#a0a0a0';
            ctx.font = '10px monospace';
            ctx.fillText(`Lv.${pokemon.level}  ${pokemon.type}`, 30, y + 26);

            // HP bar
            ctx.fillStyle = '#c0c0c0';
            ctx.textAlign = 'right';
            ctx.fillText(`${pokemon.hp}/${pokemon.maxHp}`, canvasW - 30, y + 14);

            // Move count
            const moveCount = pokemon.moves ? pokemon.moves.filter(m => m.name !== '---').length : 0;
            ctx.fillText(`${moveCount}/4 moves`, canvasW - 30, y + 26);
        }

        ctx.fillStyle = '#606060';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Z: Select | Esc: Back', canvasW / 2, canvasH - 12);
        ctx.textAlign = 'left';
    }

    function renderReplace(ctx, canvasW, canvasH) {
        const pokemonIdx = compatibleParty[partyIndex];
        const pokemon = Game.player.party[pokemonIdx];

        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${pokemon.name} wants to learn ${newMove.name}!`, canvasW / 2, 28);

        ctx.fillStyle = '#e04040';
        ctx.font = '11px monospace';
        ctx.fillText('But it already knows 4 moves. Delete a move to make room?', canvasW / 2, 44);

        // Existing moves (0-3) + Cancel (4)
        const listY = 60;
        const itemH = 38;
        const moves = pokemon.moves || [];

        for (let i = 0; i < 4; i++) {
            const move = moves[i] || { name: '---', type: 'Normal', power: 0, pp: 0, maxPp: 0 };
            const y = listY + i * itemH;

            // Highlight
            if (i === replaceIndex) {
                ctx.fillStyle = 'rgba(224,64,56,0.15)';
                ctx.fillRect(20, y - 2, canvasW - 40, itemH - 4);
                ctx.strokeStyle = '#e04040';
                ctx.lineWidth = 1;
                ctx.strokeRect(20, y - 2, canvasW - 40, itemH - 4);
            }

            // Type color
            const typeColor = TYPE_COLORS[move.type] || '#a8a878';
            ctx.fillStyle = typeColor;
            ctx.fillRect(24, y + 2, 4, itemH - 8);

            // Move name
            ctx.fillStyle = isHMMove(move.name) ? '#e04040' : '#f8f8f8';
            ctx.font = '12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(move.name + (isHMMove(move.name) ? ' [HM]' : ''), 34, y + 14);

            // Stats
            ctx.fillStyle = '#c0c0c0';
            ctx.font = '10px monospace';
            const pwrText = move.power > 0 ? `PWR:${move.power}` : 'Status';
            ctx.fillText(`${move.type}  ${pwrText}  PP:${move.pp}/${move.maxPp}`, 34, y + 26);
        }

        // Cancel option
        const cancelY = listY + 4 * itemH;
        if (replaceIndex === 4) {
            ctx.fillStyle = 'rgba(128,128,128,0.2)';
            ctx.fillRect(20, cancelY - 2, canvasW - 40, 24);
            ctx.strokeStyle = '#808080';
            ctx.lineWidth = 1;
            ctx.strokeRect(20, cancelY - 2, canvasW - 40, 24);
        }
        ctx.fillStyle = '#a0a0a0';
        ctx.font = '12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText("Don't learn this move", canvasW / 2, cancelY + 12);

        // New move preview (bottom)
        const previewY = cancelY + 34;
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 11px monospace';
        ctx.fillText('New Move:', canvasW / 2, previewY);
        const nc = TYPE_COLORS[newMove.type] || '#a8a878';
        ctx.fillStyle = nc;
        ctx.font = '12px monospace';
        const npwr = newMove.power > 0 ? `PWR:${newMove.power}` : 'Status';
        ctx.fillText(`${newMove.name}  ${newMove.type}  ${npwr}  PP:${newMove.pp}`, canvasW / 2, previewY + 16);

        ctx.fillStyle = '#606060';
        ctx.font = '10px monospace';
        ctx.fillText('Z: Forget move | Esc: Back', canvasW / 2, canvasH - 12);
        ctx.textAlign = 'left';
    }

    function renderTeaching(ctx, canvasW, canvasH) {
        const cx = canvasW / 2;
        const cy = canvasH / 2 - 20;

        // Pokemon name
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(teachPokemonName, cx, cy - 40);

        // Glow effect
        const glowRadius = 30 + Math.sin(teachTimer * 0.006) * 8;
        const typeColor = newMove ? (TYPE_COLORS[newMove.type] || '#a8a878') : '#f8d030';
        const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, glowRadius);
        gradient.addColorStop(0, typeColor);
        gradient.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(cx, cy, glowRadius, 0, Math.PI * 2);
        ctx.fill();

        // Sparkles
        for (const s of teachSparkles) {
            const alpha = 1 - s.age / 600;
            ctx.globalAlpha = alpha;
            ctx.fillStyle = '#f8f8f8';
            ctx.fillRect(s.x * canvasW - 2, s.y * canvasH - 2, 4, 4);
            ctx.fillStyle = typeColor;
            ctx.fillRect(s.x * canvasW - 1, s.y * canvasH - 1, 2, 2);
        }
        ctx.globalAlpha = 1;

        // Move name appearing
        const progress = Math.min(1, teachTimer / 800);
        ctx.globalAlpha = progress;
        ctx.fillStyle = typeColor;
        ctx.font = 'bold 20px monospace';
        ctx.fillText(teachMoveName, cx, cy + 30);
        ctx.globalAlpha = 1;

        // Learning text
        if (teachTimer > 600) {
            ctx.fillStyle = '#f8f8f8';
            ctx.font = '12px monospace';
            ctx.fillText(`${teachPokemonName} is learning ${teachMoveName}...`, cx, cy + 60);
        }
        ctx.textAlign = 'left';
    }

    function renderResult(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(resultMessage, canvasW / 2, canvasH / 2);

        ctx.fillStyle = '#808080';
        ctx.font = '10px monospace';
        ctx.fillText('Press Z to continue', canvasW / 2, canvasH / 2 + 30);
        ctx.textAlign = 'left';
    }

    // ==================== TM/HM DISC SPRITES ====================

    function drawTMDisc(ctx, x, y, size, type, isHM) {
        const color = TYPE_COLORS[type] || '#a8a878';
        const s = size;

        // Disc body
        ctx.fillStyle = isHM ? '#d4a020' : color;
        ctx.beginPath();
        ctx.arc(x, y, s / 2, 0, Math.PI * 2);
        ctx.fill();

        // Inner ring
        ctx.strokeStyle = isHM ? '#f8d830' : '#f8f8f8';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(x, y, s / 2 - 3, 0, Math.PI * 2);
        ctx.stroke();

        // Label
        ctx.fillStyle = '#202020';
        ctx.font = `bold ${Math.floor(s * 0.35)}px monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(isHM ? 'HM' : 'TM', x, y);
        ctx.textBaseline = 'alphabetic';
        ctx.textAlign = 'left';
    }

    // ==================== TUTOR NPC SPRITE ====================

    function drawTutorNpc(dir, frame) {
        const key = `tutor_${dir}_${frame}`;
        if (Sprites.cache && Sprites.cache[key]) return Sprites.cache[key];

        // Use base player drawing with custom colors
        const c = document.createElement('canvas');
        c.width = TILE;
        c.height = TILE;
        const sctx = c.getContext('2d');
        const px = (ctx, x, y, color) => { ctx.fillStyle = color; ctx.fillRect(x, y, 1, 1); };

        const isUp = dir === 1;
        const isLeft = dir === 2;
        const isRight = dir === 3;

        // Hair (white — old master)
        for (let x = 5; x <= 10; x++) px(sctx, x, 1, '#e0e0e0');
        for (let x = 4; x <= 11; x++) px(sctx, x, 2, '#e0e0e0');
        for (let x = 4; x <= 11; x++) px(sctx, x, 3, '#e0e0e0');

        // Face
        for (let x = 4; x <= 11; x++) px(sctx, x, 4, '#f8b878');
        for (let x = 4; x <= 11; x++) px(sctx, x, 5, '#f8b878');
        for (let x = 4; x <= 11; x++) px(sctx, x, 6, '#f8b878');

        // Eyes
        if (!isUp) {
            if (isLeft) px(sctx, 5, 5, '#202020');
            else if (isRight) px(sctx, 10, 5, '#202020');
            else { px(sctx, 6, 5, '#202020'); px(sctx, 9, 5, '#202020'); }
        }

        // Robe (purple — tutor)
        for (let y = 7; y <= 13; y++) {
            for (let x = 4; x <= 11; x++) px(sctx, x, y, '#6040a0');
        }

        // Belt
        for (let x = 4; x <= 11; x++) px(sctx, x, 10, '#f8d030');

        // Shoes
        for (let x = 5; x <= 7; x++) px(sctx, x, 14, '#402820');
        for (let x = 8; x <= 10; x++) px(sctx, x, 14, '#402820');

        return c;
    }

    return {
        isActive, close, update, render,
        openTutor, openTM, openReminder,
        isHMMove, drawTMDisc, drawTutorNpc,
        TYPE_COLORS,
    };
})();
