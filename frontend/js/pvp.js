// pvp.js — Multiplayer PvP Battle System UI (Sprint 6)

const PvP = (() => {
    let active = false;
    // Phases: lobby, code_entry, matchmaking, team_preview, battle, turn_wait, animating, results
    let phase = 'lobby';
    let actionCooldown = 0;
    let selectedIndex = 0;
    let matchTimer = 0;
    let turnTimer = 0;
    let previewTimer = 0;
    let animTimer = 0;

    // Connection
    let connectOption = 0; // 0=Quick Match, 1=Battle Code, 2=Cancel
    let codeDigits = [0, 0, 0, 0, 0, 0, 0, 0];
    let codeIndex = 0;

    // Battle format
    const FORMATS = [
        { id: 'singles', name: 'Singles (1v1)', desc: 'Classic single battle format' },
        { id: 'doubles', name: 'Doubles (2v2)', desc: 'Double battle with 2 Pokemon each' },
        { id: 'free', name: 'Free Battle', desc: 'No restrictions, any level' },
    ];
    let formatIndex = 0;
    let lobbyScreen = 'format'; // 'format' or 'connect'

    // Opponent data
    let opponent = null;
    let opponentParty = [];

    // Battle state
    let playerLead = 0; // index in party for lead Pokemon
    let playerReady = false;
    let opponentReady = false;
    let turnNumber = 0;
    let moveChoice = 0;
    let battleMenuMode = 'main'; // 'main' or 'fight'
    let playerPokemon = null;
    let enemyPokemon = null;
    let battleLog = [];
    let logIndex = 0;
    let charIdx = 0;
    let textTimer = 0;
    let battleResult = null; // 'win', 'lose', 'draw', 'disconnect'
    let rematchOption = 0; // 0=Rematch, 1=Exit
    let disconnectTimer = 0;
    let playerAction = null; // selected action for current turn

    // HP animation
    let playerHpDisplay = 0;
    let enemyHpDisplay = 0;
    let playerShake = 0;
    let enemyShake = 0;

    // PvP stats (loaded from PlayerStats when available)
    let pvpWins = 0;
    let pvpLosses = 0;
    let pvpRating = 1000;

    // Backend session state
    let sessionId = null;
    let pollTimer = 0;
    const POLL_INTERVAL = 2000;
    let useMock = false;

    // Type colors
    const TYPE_COLORS = {
        Grass: '#78c850', Fire: '#f08030', Water: '#6890f0',
        Normal: '#a8a878', Bug: '#a8b820', Flying: '#a890f0',
        Poison: '#a040a0', Electric: '#f8d030', Ground: '#e0c068',
        Rock: '#b8a038', Ice: '#98d8d8', Dragon: '#7038f8',
        Psychic: '#f85888', Ghost: '#705898', Dark: '#705848',
        Steel: '#b8b8d0', Fighting: '#c03028', Fairy: '#ee99ac',
    };

    const TURN_TIME_LIMIT = 60000; // 60 seconds per turn
    const PREVIEW_TIME_LIMIT = 30000; // 30 seconds team preview
    const DISCONNECT_TIMEOUT = 30000; // 30 seconds disconnect forfeit

    // Mock opponents
    const MOCK_OPPONENTS = [
        { name: 'BLUE', id: 'TR-4829', rating: 1200 },
        { name: 'LANCE', id: 'TR-7712', rating: 1450 },
        { name: 'CYNTHIA', id: 'TR-3391', rating: 1380 },
        { name: 'STEVEN', id: 'TR-5504', rating: 1290 },
    ];

    function generateOpponentParty(name) {
        const parties = {
            'BLUE': [
                { name: 'Pidgeot', level: 38, type: 'Flying', hp: 98, maxHp: 98, moves: [
                    { name: 'Wing Attack', type: 'Flying', power: 60 },
                    { name: 'Quick Attack', type: 'Normal', power: 40 },
                    { name: 'Sand Attack', type: 'Ground', power: 0 },
                    { name: 'Gust', type: 'Flying', power: 40 },
                ]},
                { name: 'Alakazam', level: 40, type: 'Psychic', hp: 88, maxHp: 88, moves: [
                    { name: 'Psychic', type: 'Psychic', power: 90 },
                    { name: 'Shadow Ball', type: 'Ghost', power: 80 },
                    { name: 'Recover', type: 'Normal', power: 0 },
                    { name: 'Thunder Punch', type: 'Electric', power: 75 },
                ]},
                { name: 'Rhydon', level: 37, type: 'Ground', hp: 105, maxHp: 105, moves: [
                    { name: 'Earthquake', type: 'Ground', power: 100 },
                    { name: 'Rock Slide', type: 'Rock', power: 75 },
                    { name: 'Horn Drill', type: 'Normal', power: 0 },
                    { name: 'Stomp', type: 'Normal', power: 65 },
                ]},
                { name: 'Gyarados', level: 39, type: 'Water', hp: 110, maxHp: 110, moves: [
                    { name: 'Hydro Pump', type: 'Water', power: 110 },
                    { name: 'Dragon Rage', type: 'Dragon', power: 40 },
                    { name: 'Bite', type: 'Dark', power: 60 },
                    { name: 'Thrash', type: 'Normal', power: 120 },
                ]},
                { name: 'Arcanine', level: 41, type: 'Fire', hp: 108, maxHp: 108, moves: [
                    { name: 'Flamethrower', type: 'Fire', power: 90 },
                    { name: 'Extreme Speed', type: 'Normal', power: 80 },
                    { name: 'Crunch', type: 'Dark', power: 80 },
                    { name: 'Fire Blast', type: 'Fire', power: 110 },
                ]},
                { name: 'Exeggutor', level: 36, type: 'Grass', hp: 95, maxHp: 95, moves: [
                    { name: 'Solar Beam', type: 'Grass', power: 120 },
                    { name: 'Psychic', type: 'Psychic', power: 90 },
                    { name: 'Sleep Powder', type: 'Grass', power: 0 },
                    { name: 'Egg Bomb', type: 'Normal', power: 100 },
                ]},
            ],
            'LANCE': [
                { name: 'Dragonite', level: 50, type: 'Dragon', hp: 140, maxHp: 140, moves: [
                    { name: 'Outrage', type: 'Dragon', power: 120 },
                    { name: 'Hyper Beam', type: 'Normal', power: 150 },
                    { name: 'Thunder', type: 'Electric', power: 110 },
                    { name: 'Fire Blast', type: 'Fire', power: 110 },
                ]},
                { name: 'Aerodactyl', level: 45, type: 'Rock', hp: 95, maxHp: 95, moves: [
                    { name: 'Rock Slide', type: 'Rock', power: 75 },
                    { name: 'Wing Attack', type: 'Flying', power: 60 },
                    { name: 'Earthquake', type: 'Ground', power: 100 },
                    { name: 'Hyper Beam', type: 'Normal', power: 150 },
                ]},
                { name: 'Charizard', level: 47, type: 'Fire', hp: 115, maxHp: 115, moves: [
                    { name: 'Flamethrower', type: 'Fire', power: 90 },
                    { name: 'Slash', type: 'Normal', power: 70 },
                    { name: 'Dragon Rage', type: 'Dragon', power: 40 },
                    { name: 'Fire Spin', type: 'Fire', power: 35 },
                ]},
            ],
            'CYNTHIA': [
                { name: 'Garchomp', level: 48, type: 'Dragon', hp: 130, maxHp: 130, moves: [
                    { name: 'Earthquake', type: 'Ground', power: 100 },
                    { name: 'Dragon Rush', type: 'Dragon', power: 100 },
                    { name: 'Crunch', type: 'Dark', power: 80 },
                    { name: 'Stone Edge', type: 'Rock', power: 100 },
                ]},
                { name: 'Lucario', level: 44, type: 'Fighting', hp: 92, maxHp: 92, moves: [
                    { name: 'Aura Sphere', type: 'Fighting', power: 80 },
                    { name: 'Flash Cannon', type: 'Steel', power: 80 },
                    { name: 'Shadow Ball', type: 'Ghost', power: 80 },
                    { name: 'Extreme Speed', type: 'Normal', power: 80 },
                ]},
                { name: 'Milotic', level: 46, type: 'Water', hp: 120, maxHp: 120, moves: [
                    { name: 'Surf', type: 'Water', power: 90 },
                    { name: 'Ice Beam', type: 'Ice', power: 90 },
                    { name: 'Recover', type: 'Normal', power: 0 },
                    { name: 'Mirror Coat', type: 'Psychic', power: 0 },
                ]},
                { name: 'Togekiss', level: 43, type: 'Flying', hp: 100, maxHp: 100, moves: [
                    { name: 'Air Slash', type: 'Flying', power: 75 },
                    { name: 'Aura Sphere', type: 'Fighting', power: 80 },
                    { name: 'Shadow Ball', type: 'Ghost', power: 80 },
                    { name: 'Thunder Wave', type: 'Electric', power: 0 },
                ]},
            ],
            'STEVEN': [
                { name: 'Metagross', level: 46, type: 'Steel', hp: 110, maxHp: 110, moves: [
                    { name: 'Meteor Mash', type: 'Steel', power: 90 },
                    { name: 'Earthquake', type: 'Ground', power: 100 },
                    { name: 'Psychic', type: 'Psychic', power: 90 },
                    { name: 'Hyper Beam', type: 'Normal', power: 150 },
                ]},
                { name: 'Aggron', level: 44, type: 'Steel', hp: 105, maxHp: 105, moves: [
                    { name: 'Iron Tail', type: 'Steel', power: 100 },
                    { name: 'Earthquake', type: 'Ground', power: 100 },
                    { name: 'Thunder', type: 'Electric', power: 110 },
                    { name: 'Dragon Claw', type: 'Dragon', power: 80 },
                ]},
                { name: 'Skarmory', level: 42, type: 'Steel', hp: 90, maxHp: 90, moves: [
                    { name: 'Steel Wing', type: 'Steel', power: 70 },
                    { name: 'Aerial Ace', type: 'Flying', power: 60 },
                    { name: 'Spikes', type: 'Ground', power: 0 },
                    { name: 'Toxic', type: 'Poison', power: 0 },
                ]},
            ],
        };
        return parties[name] || parties['BLUE'].slice(0, 3);
    }

    function getPlayerParty() {
        return Game.player.party || [];
    }

    function open() {
        active = true;
        phase = 'lobby';
        lobbyScreen = 'format';
        formatIndex = 0;
        connectOption = 0;
        actionCooldown = 250;
        selectedIndex = 0;
        matchTimer = 0;
        opponent = null;
        opponentParty = [];
        playerLead = 0;
        playerReady = false;
        opponentReady = false;
        battleResult = null;
        turnNumber = 0;
        battleLog = [];
        playerAction = null;
        codeDigits = [0, 0, 0, 0, 0, 0, 0, 0];
        codeIndex = 0;
        sessionId = null;
        pollTimer = 0;
        useMock = false;

        // Load PvP stats from PlayerStats if available
        if (typeof PlayerStats !== 'undefined') {
            const stats = PlayerStats.getStats();
            pvpWins = stats.pvpWins || 0;
            pvpLosses = stats.pvpLosses || 0;
        }
    }

    function close() {
        // Clean up backend session if active
        if (sessionId && !useMock) {
            API.pvpForfeit(sessionId);
            sessionId = null;
        }
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

        if (phase === 'lobby') updateLobby(dt, mov, action, back);
        else if (phase === 'code_entry') updateCodeEntry(dt, mov, action, back);
        else if (phase === 'matchmaking') updateMatchmaking(dt, action, back);
        else if (phase === 'team_preview') updateTeamPreview(dt, mov, action, back);
        else if (phase === 'battle') updateBattle(dt, mov, action, back);
        else if (phase === 'turn_wait') updateTurnWait(dt, action, back);
        else if (phase === 'animating') updateAnimating(dt, action);
        else if (phase === 'results') updateResults(dt, mov, action, back);
    }

    function updateLobby(dt, mov, action, back) {
        if (lobbyScreen === 'format') {
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) { formatIndex = Math.max(0, formatIndex - 1); actionCooldown = 150; }
                if (mov.dy > 0) { formatIndex = Math.min(FORMATS.length - 1, formatIndex + 1); actionCooldown = 150; }
            }
            if (action) {
                lobbyScreen = 'connect';
                connectOption = 0;
                actionCooldown = 200;
            }
            if (back) { close(); actionCooldown = 200; }
        } else {
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) { connectOption = Math.max(0, connectOption - 1); actionCooldown = 150; }
                if (mov.dy > 0) { connectOption = Math.min(2, connectOption + 1); actionCooldown = 150; }
            }
            if (action) {
                actionCooldown = 200;
                if (connectOption === 0) {
                    phase = 'matchmaking';
                    matchTimer = 0;
                    pollTimer = 0;
                    // Create PvP session via backend
                    API.pvpCreate().then(data => {
                        if (data && data.session) {
                            sessionId = data.session.id;
                        } else {
                            useMock = true;
                        }
                    });
                } else if (connectOption === 1) {
                    phase = 'code_entry';
                    codeDigits = [0, 0, 0, 0, 0, 0, 0, 0];
                    codeIndex = 0;
                } else {
                    lobbyScreen = 'format';
                }
            }
            if (back) { lobbyScreen = 'format'; actionCooldown = 200; }
        }
    }

    function updateCodeEntry(dt, mov, action, back) {
        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { codeDigits[codeIndex] = (codeDigits[codeIndex] + 1) % 10; actionCooldown = 120; }
            if (mov.dy > 0) { codeDigits[codeIndex] = (codeDigits[codeIndex] + 9) % 10; actionCooldown = 120; }
            if (mov.dx > 0) { codeIndex = Math.min(7, codeIndex + 1); actionCooldown = 120; }
            if (mov.dx < 0) { codeIndex = Math.max(0, codeIndex - 1); actionCooldown = 120; }
        }
        if (action) {
            const code = codeDigits.join('');
            phase = 'matchmaking';
            matchTimer = 0;
            pollTimer = 0;
            actionCooldown = 200;
            // Join PvP session via backend
            API.pvpJoin(code).then(data => {
                if (data && data.session) {
                    sessionId = data.session.id;
                } else {
                    useMock = true;
                }
            });
        }
        if (back) { phase = 'lobby'; lobbyScreen = 'connect'; actionCooldown = 200; }
    }

    function updateMatchmaking(dt, action, back) {
        matchTimer += dt;
        pollTimer += dt;

        // Poll backend for opponent joining
        if (sessionId && !useMock && pollTimer >= POLL_INTERVAL) {
            pollTimer = 0;
            API.pvpState(sessionId).then(data => {
                if (data && data.session && data.session.player2_id) {
                    opponent = { name: 'Opponent', id: data.session.player2_id, rating: '???' };
                    // Use backend pokemon data if available
                    if (data.player2_pokemon) {
                        opponentParty = [data.player2_pokemon].map(p => ({
                            name: p.name, level: p.level || 30,
                            type: (p.types && p.types[0]) || 'Normal',
                            hp: p.current_hp || p.hp || 80, maxHp: (p.stats && p.stats.hp) || p.max_hp || p.maxHp || 80,
                            moves: p.moves || [],
                        }));
                    } else {
                        opponentParty = generateOpponentParty('BLUE');
                    }
                    phase = 'team_preview';
                    previewTimer = 0;
                    playerLead = 0;
                    selectedIndex = 0;
                    playerReady = false;
                    opponentReady = false;
                    actionCooldown = 300;
                }
            });
        }

        // Mock fallback
        if ((useMock || !sessionId) && matchTimer > 3000) {
            const idx = Math.floor(Math.random() * MOCK_OPPONENTS.length);
            opponent = MOCK_OPPONENTS[idx];
            opponentParty = generateOpponentParty(opponent.name);
            phase = 'team_preview';
            previewTimer = 0;
            playerLead = 0;
            selectedIndex = 0;
            playerReady = false;
            opponentReady = false;
            actionCooldown = 300;
        }
        if (back) {
            if (sessionId) { API.pvpForfeit(sessionId); sessionId = null; }
            phase = 'lobby'; lobbyScreen = 'connect'; actionCooldown = 200;
        }
    }

    function updateTeamPreview(dt, mov, action, back) {
        previewTimer += dt;

        const party = getPlayerParty();
        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { selectedIndex = Math.max(0, selectedIndex - 1); actionCooldown = 150; }
            if (mov.dy > 0) { selectedIndex = Math.min(Math.max(0, party.length - 1), selectedIndex + 1); actionCooldown = 150; }
        }

        // Z to set lead / ready up
        if (action) {
            if (!playerReady) {
                playerLead = selectedIndex;
                playerReady = true;
                actionCooldown = 200;
                // Notify backend
                if (sessionId && !useMock) {
                    API.pvpReady(sessionId, playerLead).then(data => {
                        if (data && data.battle_started) {
                            opponentReady = true;
                        }
                    });
                }
            }
        }

        // Poll backend for opponent ready
        if (sessionId && !useMock && playerReady && !opponentReady) {
            pollTimer += dt;
            if (pollTimer >= POLL_INTERVAL) {
                pollTimer = 0;
                API.pvpState(sessionId).then(data => {
                    if (data && data.session) {
                        if (data.session.player1_ready && data.session.player2_ready) {
                            opponentReady = true;
                        }
                    }
                });
            }
        }

        // Mock fallback for opponent ready
        if ((useMock || !sessionId) && previewTimer > 2000 && !opponentReady) {
            opponentReady = true;
        }

        // Start battle when both ready or timer expires
        if ((playerReady && opponentReady) || previewTimer >= PREVIEW_TIME_LIMIT) {
            startPvPBattle();
        }

        if (back && !playerReady) {
            // Disconnect
            phase = 'lobby';
            lobbyScreen = 'format';
            opponent = null;
            actionCooldown = 200;
        }
    }

    function startPvPBattle() {
        const party = getPlayerParty();
        const lead = party[playerLead] || party[0];
        if (!lead) return;

        playerPokemon = {
            name: lead.name,
            level: lead.level,
            hp: lead.hp,
            maxHp: lead.maxHp,
            type: lead.type,
            moves: lead.moves || [
                { name: 'Tackle', type: 'Normal', power: 40 },
                { name: 'Growl', type: 'Normal', power: 0 },
            ],
        };

        const enemyLead = opponentParty[0];
        enemyPokemon = {
            name: enemyLead.name,
            level: enemyLead.level,
            hp: enemyLead.hp,
            maxHp: enemyLead.maxHp,
            type: enemyLead.type,
            moves: enemyLead.moves || [],
        };

        playerHpDisplay = playerPokemon.hp;
        enemyHpDisplay = enemyPokemon.hp;
        playerShake = 0;
        enemyShake = 0;
        turnNumber = 1;
        moveChoice = 0;
        battleMenuMode = 'main';
        battleLog = [`PvP Battle! ${opponent.name} sent out ${enemyPokemon.name}!`];
        logIndex = 0;
        charIdx = 0;
        textTimer = 0;
        playerAction = null;
        phase = 'battle';
        actionCooldown = 500;
    }

    function updateBattle(dt, mov, action, back) {
        // HP animation
        playerHpDisplay = lerp(playerHpDisplay, playerPokemon.hp, dt * 0.005);
        enemyHpDisplay = lerp(enemyHpDisplay, enemyPokemon.hp, dt * 0.005);
        if (playerShake > 0) playerShake = Math.max(0, playerShake - dt);
        if (enemyShake > 0) enemyShake = Math.max(0, enemyShake - dt);

        // Text log display
        if (logIndex < battleLog.length) {
            textTimer += dt;
            const currentText = battleLog[logIndex];
            charIdx = Math.min(currentText.length, Math.floor(textTimer / 25));

            if (action && charIdx >= currentText.length) {
                logIndex++;
                charIdx = 0;
                textTimer = 0;
                actionCooldown = 150;
            } else if (action && charIdx < currentText.length) {
                charIdx = currentText.length;
                actionCooldown = 150;
            }
            return;
        }

        // Turn timer
        turnTimer += dt;

        if (battleMenuMode === 'main') {
            if (mov && actionCooldown <= 0) {
                // 2x2 grid: 0=Fight, 1=Pokemon, 2=Forfeit (no Run, no Bag catch)
                if (mov.dy < 0 || mov.dy > 0) {
                    moveChoice = moveChoice >= 2 ? moveChoice - 2 : moveChoice + 2;
                    moveChoice = Math.min(2, Math.max(0, moveChoice));
                    actionCooldown = 150;
                }
                if (mov.dx !== 0) {
                    moveChoice = moveChoice % 2 === 0 ? Math.min(2, moveChoice + 1) : moveChoice - 1;
                    actionCooldown = 150;
                }
            }
            if (action) {
                actionCooldown = 200;
                if (moveChoice === 0) {
                    battleMenuMode = 'fight';
                    moveChoice = 0;
                } else if (moveChoice === 1) {
                    // Pokemon switch — not implemented in mock
                    battleLog.push('Cannot switch Pokemon in this battle!');
                    logIndex = battleLog.length - 1;
                    charIdx = 0;
                    textTimer = 0;
                } else if (moveChoice === 2) {
                    // Forfeit
                    if (sessionId && !useMock) {
                        API.pvpForfeit(sessionId);
                    }
                    battleResult = 'lose';
                    pvpLosses++;
                    pvpRating = Math.max(800, pvpRating - 20);
                    if (typeof PlayerStats !== 'undefined') {
                        PlayerStats.increment('battlesLost');
                        PlayerStats.increment('pvpLosses');
                    }
                    battleLog.push('You forfeited the battle!');
                    battleLog.push(`${opponent.name} wins!`);
                    logIndex = battleLog.length - 2;
                    charIdx = 0;
                    textTimer = 0;
                    phase = 'animating';
                    animTimer = 0;
                }
            }
        } else if (battleMenuMode === 'fight') {
            const moves = playerPokemon.moves || [];
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0 || mov.dy > 0) {
                    moveChoice = moveChoice >= 2 ? moveChoice - 2 : moveChoice + 2;
                    moveChoice = Math.min(moves.length - 1, Math.max(0, moveChoice));
                    actionCooldown = 150;
                }
                if (mov.dx !== 0) {
                    moveChoice = moveChoice % 2 === 0 ? Math.min(moves.length - 1, moveChoice + 1) : moveChoice - 1;
                    moveChoice = Math.max(0, moveChoice);
                    actionCooldown = 150;
                }
            }
            if (action && moves.length > 0) {
                playerAction = { type: 'move', moveIndex: moveChoice };
                phase = 'turn_wait';
                turnTimer = 0;
                actionCooldown = 200;
            }
            if (back) {
                battleMenuMode = 'main';
                moveChoice = 0;
                actionCooldown = 200;
            }
        }

        // Auto-forfeit if turn timer expires
        if (turnTimer >= TURN_TIME_LIMIT) {
            playerAction = { type: 'move', moveIndex: 0 };
            phase = 'turn_wait';
            turnTimer = 0;
        }
    }

    function updateTurnWait(dt, action, back) {
        turnTimer += dt;
        pollTimer += dt;

        // Send action to backend and poll for resolution
        if (sessionId && !useMock && pollTimer >= POLL_INTERVAL) {
            pollTimer = 0;
            const moveIdx = playerAction ? playerAction.moveIndex : 0;
            API.pvpAction(sessionId, 'fight', moveIdx).then(data => {
                if (data && data.turn_number) {
                    // Turn resolved by backend — apply results
                    applyBackendTurnResult(data);
                } else if (data && !data.waiting) {
                    // Fallback to local resolution
                    resolveTurn();
                }
                // If data.waiting, keep polling
            });
        }

        // Mock fallback
        if ((useMock || !sessionId) && turnTimer > 1500) {
            resolveTurn();
        }
    }

    function applyBackendTurnResult(data) {
        battleLog = [];
        if (data.events) {
            for (const evt of data.events) {
                battleLog.push(`${evt.attacker || '???'} used ${evt.move || 'a move'}!`);
                if (evt.damage > 0) {
                    battleLog.push(`It dealt ${evt.damage} damage!`);
                }
                if (evt.target_fainted) {
                    battleLog.push(`${evt.attacker === playerPokemon.name ? enemyPokemon.name : playerPokemon.name} fainted!`);
                }
            }
        }

        // Update HP from backend
        if (data.player1_pokemon) {
            playerPokemon.hp = data.player1_pokemon.current_hp || data.player1_pokemon.hp || playerPokemon.hp;
        }
        if (data.player2_pokemon) {
            enemyPokemon.hp = data.player2_pokemon.current_hp || data.player2_pokemon.hp || enemyPokemon.hp;
        }

        if (data.battle_over) {
            if (data.winner === API.getGameId() || data.winner === 'player1') {
                battleResult = 'win';
                pvpWins++;
                pvpRating += 25;
                if (typeof PlayerStats !== 'undefined') {
                    PlayerStats.increment('battlesWon');
                    PlayerStats.increment('pvpWins');
                }
            } else {
                battleResult = 'lose';
                pvpLosses++;
                pvpRating = Math.max(800, pvpRating - 20);
                if (typeof PlayerStats !== 'undefined') {
                    PlayerStats.increment('battlesLost');
                    PlayerStats.increment('pvpLosses');
                }
            }
            phase = 'animating';
            animTimer = 0;
        } else {
            turnNumber = data.turn_number || turnNumber + 1;
            phase = 'battle';
            battleMenuMode = 'main';
            moveChoice = 0;
            playerAction = null;
            turnTimer = 0;
            actionCooldown = 300;
        }

        logIndex = 0;
        charIdx = 0;
        textTimer = 0;
    }

    function resolveTurn() {
        const playerMove = playerPokemon.moves[playerAction.moveIndex] || playerPokemon.moves[0];
        const enemyMoveIdx = Math.floor(Math.random() * enemyPokemon.moves.length);
        const enemyMove = enemyPokemon.moves[enemyMoveIdx];

        battleLog = [];

        // Player attacks
        if (playerMove.power > 0) {
            const dmg = calculateDamage(playerPokemon.level, playerMove.power, enemyPokemon.level);
            enemyPokemon.hp = Math.max(0, enemyPokemon.hp - dmg);
            battleLog.push(`${playerPokemon.name} used ${playerMove.name}!`);
            battleLog.push(`${enemyPokemon.name} took ${dmg} damage!`);
            enemyShake = 300;
        } else {
            battleLog.push(`${playerPokemon.name} used ${playerMove.name}!`);
            battleLog.push(`But nothing happened...`);
        }

        // Check enemy faint
        if (enemyPokemon.hp <= 0) {
            battleLog.push(`${enemyPokemon.name} fainted!`);
            battleResult = 'win';
            pvpWins++;
            pvpRating += 25;
            if (typeof PlayerStats !== 'undefined') {
                PlayerStats.increment('battlesWon');
                PlayerStats.increment('pvpWins');
            }
            logIndex = 0;
            charIdx = 0;
            textTimer = 0;
            phase = 'animating';
            animTimer = 0;
            return;
        }

        // Enemy attacks
        if (enemyMove && enemyMove.power > 0) {
            const dmg = calculateDamage(enemyPokemon.level, enemyMove.power, playerPokemon.level);
            playerPokemon.hp = Math.max(0, playerPokemon.hp - dmg);
            battleLog.push(`${enemyPokemon.name} used ${enemyMove.name}!`);
            battleLog.push(`${playerPokemon.name} took ${dmg} damage!`);
            playerShake = 300;
        } else if (enemyMove) {
            battleLog.push(`${enemyPokemon.name} used ${enemyMove.name}!`);
        }

        // Check player faint
        if (playerPokemon.hp <= 0) {
            battleLog.push(`${playerPokemon.name} fainted!`);
            battleResult = 'lose';
            pvpLosses++;
            pvpRating = Math.max(800, pvpRating - 20);
            if (typeof PlayerStats !== 'undefined') {
                PlayerStats.increment('battlesLost');
                PlayerStats.increment('pvpLosses');
            }
            logIndex = 0;
            charIdx = 0;
            textTimer = 0;
            phase = 'animating';
            animTimer = 0;
            return;
        }

        turnNumber++;
        logIndex = 0;
        charIdx = 0;
        textTimer = 0;
        battleMenuMode = 'main';
        moveChoice = 0;
        playerAction = null;
        turnTimer = 0;
        phase = 'battle';
        actionCooldown = 300;
    }

    function calculateDamage(attackerLevel, movePower, defenderLevel) {
        const baseDmg = Math.floor(((2 * attackerLevel / 5 + 2) * movePower * 1.0) / 50 + 2);
        const variance = 0.85 + Math.random() * 0.15;
        return Math.max(1, Math.floor(baseDmg * variance));
    }

    function updateAnimating(dt, action) {
        animTimer += dt;

        // Continue showing battle log
        if (logIndex < battleLog.length) {
            textTimer += dt;
            const currentText = battleLog[logIndex];
            charIdx = Math.min(currentText.length, Math.floor(textTimer / 25));

            if (action && charIdx >= currentText.length) {
                logIndex++;
                charIdx = 0;
                textTimer = 0;
                actionCooldown = 150;
            } else if (action && charIdx < currentText.length) {
                charIdx = currentText.length;
                actionCooldown = 150;
            }
        }

        // HP animation
        playerHpDisplay = lerp(playerHpDisplay, playerPokemon.hp, dt * 0.005);
        enemyHpDisplay = lerp(enemyHpDisplay, enemyPokemon.hp, dt * 0.005);

        // After all text shown, go to results
        if (logIndex >= battleLog.length && animTimer > 1000) {
            phase = 'results';
            rematchOption = 0;
            actionCooldown = 300;
        }
    }

    function updateResults(dt, mov, action, back) {
        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0 || mov.dy > 0) {
                rematchOption = 1 - rematchOption;
                actionCooldown = 150;
            }
        }
        if (action) {
            actionCooldown = 200;
            if (rematchOption === 0) {
                // Rematch — go back to team preview with same opponent
                phase = 'team_preview';
                previewTimer = 0;
                playerReady = false;
                opponentReady = false;
                selectedIndex = 0;
                battleResult = null;
                // Reset opponent Pokemon HP
                opponentParty = generateOpponentParty(opponent.name);
            } else {
                close();
            }
        }
        if (back) { close(); actionCooldown = 200; }
    }

    function lerp(a, b, t) {
        return a + (b - a) * Math.min(1, t);
    }

    // ---- Render ----

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        // Background
        ctx.fillStyle = '#1a1028';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Title bar
        ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
        ctx.fillRect(0, 0, canvasW, 36);
        ctx.fillStyle = '#e04040';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('PvP Battle Arena', canvasW / 2, 24);

        if (opponent && phase !== 'lobby' && phase !== 'code_entry' && phase !== 'matchmaking') {
            ctx.fillStyle = '#a0a0b0';
            ctx.font = '10px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(`vs ${opponent.name} (${opponent.rating})`, canvasW - 10, 24);
        }

        if (phase === 'lobby') renderLobby(ctx, canvasW, canvasH);
        else if (phase === 'code_entry') renderCodeEntry(ctx, canvasW, canvasH);
        else if (phase === 'matchmaking') renderMatchmaking(ctx, canvasW, canvasH);
        else if (phase === 'team_preview') renderTeamPreview(ctx, canvasW, canvasH);
        else if (phase === 'battle' || phase === 'turn_wait') renderBattle(ctx, canvasW, canvasH);
        else if (phase === 'animating') renderBattle(ctx, canvasW, canvasH);
        else if (phase === 'results') renderResults(ctx, canvasW, canvasH);

        ctx.textAlign = 'left';
    }

    function renderLobby(ctx, canvasW, canvasH) {
        if (lobbyScreen === 'format') {
            ctx.fillStyle = '#c0c0d0';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('Choose Battle Format:', canvasW / 2, 55);

            for (let i = 0; i < FORMATS.length; i++) {
                const fmt = FORMATS[i];
                const y = 70 + i * 50;
                const isSelected = i === formatIndex;

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
            ctx.fillText(`W: ${pvpWins}  L: ${pvpLosses}  Rating: ${pvpRating}`, canvasW / 2, statsY + 22);
            ctx.fillText('Online Players: --', canvasW / 2, statsY + 40);

            renderHint(ctx, canvasW, canvasH, 'Z: Select Format | B: Exit');
        } else {
            // Connect screen
            const options = ['Quick Match', 'Battle Code', 'Back'];
            const descs = ['Find a random opponent', 'Enter code to match', 'Return to format select'];

            ctx.fillStyle = '#c0c0d0';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(`${FORMATS[formatIndex].name} — Find Opponent`, canvasW / 2, 55);

            for (let i = 0; i < options.length; i++) {
                const y = 80 + i * 48;
                const isSelected = i === connectOption;

                ctx.fillStyle = isSelected ? 'rgba(160, 50, 50, 0.5)' : 'rgba(255, 255, 255, 0.05)';
                ctx.fillRect(canvasW / 2 - 120, y, 240, 40);
                if (isSelected) {
                    ctx.strokeStyle = '#e06060';
                    ctx.lineWidth = 1;
                    ctx.strokeRect(canvasW / 2 - 120, y, 240, 40);
                }

                ctx.fillStyle = isSelected ? '#f8f8f8' : '#808090';
                ctx.font = 'bold 13px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(options[i], canvasW / 2, y + 18);
                ctx.fillStyle = '#606070';
                ctx.font = '10px monospace';
                ctx.fillText(descs[i], canvasW / 2, y + 32);
            }

            renderHint(ctx, canvasW, canvasH, 'Z: Select | B: Back');
        }
    }

    function renderCodeEntry(ctx, canvasW, canvasH) {
        const centerY = canvasH / 2 - 20;

        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Enter Battle Code', canvasW / 2, centerY - 30);
        ctx.fillStyle = '#606070';
        ctx.font = '10px monospace';
        ctx.fillText('Share this code with your opponent', canvasW / 2, centerY - 12);

        const digitW = 28;
        const totalW = digitW * 8 + 7 * 6 + 10;
        const startX = (canvasW - totalW) / 2;

        for (let i = 0; i < 8; i++) {
            const gap = i < 4 ? 0 : 10;
            const x = startX + i * (digitW + 6) + gap;
            const y = centerY;
            const isCurrent = i === codeIndex;

            ctx.fillStyle = isCurrent ? 'rgba(160, 50, 50, 0.5)' : 'rgba(255, 255, 255, 0.1)';
            ctx.fillRect(x, y, digitW, 36);
            ctx.strokeStyle = isCurrent ? '#e08080' : '#404060';
            ctx.lineWidth = isCurrent ? 2 : 1;
            ctx.strokeRect(x, y, digitW, 36);

            ctx.fillStyle = isCurrent ? '#f8f8f8' : '#a0a0b0';
            ctx.font = 'bold 18px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(`${codeDigits[i]}`, x + digitW / 2, y + 25);

            if (isCurrent) {
                ctx.fillStyle = '#e06060';
                ctx.font = '10px monospace';
                ctx.fillText('\u25B2', x + digitW / 2, y - 4);
                ctx.fillText('\u25BC', x + digitW / 2, y + 48);
            }
        }

        // Dash
        const dashX = startX + 4 * (digitW + 6) - 2;
        ctx.fillStyle = '#606070';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('-', dashX, centerY + 24);

        renderHint(ctx, canvasW, canvasH, 'U/D: Digit | L/R: Move | Z: Search | B: Back');
    }

    function renderMatchmaking(ctx, canvasW, canvasH) {
        const dots = '.'.repeat(Math.floor(matchTimer / 500) % 4);

        // Crossed swords icon
        const cx = canvasW / 2;
        const cy = canvasH / 2 - 30;

        // Spinning indicator
        const angle = matchTimer * 0.005;
        ctx.strokeStyle = '#e04040';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(cx, cy, 18, angle, angle + Math.PI * 1.5);
        ctx.stroke();

        ctx.fillStyle = '#c0c0d0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Searching for opponent${dots}`, cx, cy + 40);

        ctx.fillStyle = '#808090';
        ctx.font = '11px monospace';
        ctx.fillText(`Format: ${FORMATS[formatIndex].name}`, cx, cy + 60);

        const elapsed = Math.floor(matchTimer / 1000);
        ctx.fillStyle = '#606070';
        ctx.font = '10px monospace';
        ctx.fillText(`Time: ${elapsed}s`, cx, cy + 80);

        renderHint(ctx, canvasW, canvasH, 'B: Cancel');
    }

    function renderTeamPreview(ctx, canvasW, canvasH) {
        const party = getPlayerParty();
        const halfW = (canvasW - 20) / 2;
        const listY = 44;

        // Timer bar
        const timeLeft = Math.max(0, PREVIEW_TIME_LIMIT - previewTimer);
        const timeRatio = timeLeft / PREVIEW_TIME_LIMIT;
        ctx.fillStyle = '#303030';
        ctx.fillRect(10, 38, canvasW - 20, 4);
        ctx.fillStyle = timeRatio > 0.3 ? '#48c048' : '#e04040';
        ctx.fillRect(10, 38, (canvasW - 20) * timeRatio, 4);

        ctx.fillStyle = '#808090';
        ctx.font = '9px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`${Math.ceil(timeLeft / 1000)}s`, canvasW - 12, 36);

        // Your team (left)
        ctx.fillStyle = 'rgba(40, 40, 80, 0.4)';
        ctx.fillRect(5, listY + 8, halfW, canvasH - listY - 50);
        ctx.strokeStyle = '#4040a0';
        ctx.lineWidth = 1;
        ctx.strokeRect(5, listY + 8, halfW, canvasH - listY - 50);

        ctx.fillStyle = '#8080c0';
        ctx.font = 'bold 11px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Your Team', 5 + halfW / 2, listY + 22);

        for (let i = 0; i < party.length; i++) {
            const poke = party[i];
            const y = listY + 28 + i * 30;
            const isSelected = i === selectedIndex;
            const isLead = i === playerLead && playerReady;

            ctx.fillStyle = isSelected ? 'rgba(80, 80, 180, 0.4)' : 'rgba(255, 255, 255, 0.03)';
            ctx.fillRect(9, y, halfW - 8, 26);
            if (isSelected) {
                ctx.strokeStyle = '#6060c0';
                ctx.lineWidth = 1;
                ctx.strokeRect(9, y, halfW - 8, 26);
            }

            // Lead marker
            if (isLead) {
                ctx.fillStyle = '#f8d030';
                ctx.font = 'bold 10px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('LEAD', 12, y + 17);
            }

            const typeColor = TYPE_COLORS[poke.type] || '#a0a0a0';
            ctx.fillStyle = typeColor;
            ctx.fillRect(isLead ? 42 : 12, y + 4, 18, 18);
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 10px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(poke.name[0], (isLead ? 42 : 12) + 9, y + 17);

            ctx.fillStyle = '#c0c0d0';
            ctx.font = '11px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`${poke.name} Lv${poke.level}`, (isLead ? 64 : 34), y + 17);
        }

        // Opponent team (right) — species + level only
        const rightX = canvasW / 2 + 5;
        ctx.fillStyle = 'rgba(80, 40, 40, 0.4)';
        ctx.fillRect(rightX, listY + 8, halfW, canvasH - listY - 50);
        ctx.strokeStyle = '#a04040';
        ctx.lineWidth = 1;
        ctx.strokeRect(rightX, listY + 8, halfW, canvasH - listY - 50);

        ctx.fillStyle = '#c08080';
        ctx.font = 'bold 11px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${opponent.name}'s Team`, rightX + halfW / 2, listY + 22);

        for (let i = 0; i < opponentParty.length; i++) {
            const poke = opponentParty[i];
            const y = listY + 28 + i * 30;
            const typeColor = TYPE_COLORS[poke.type] || '#a0a0a0';

            ctx.fillStyle = 'rgba(255, 255, 255, 0.03)';
            ctx.fillRect(rightX + 4, y, halfW - 8, 26);

            ctx.fillStyle = typeColor;
            ctx.fillRect(rightX + 8, y + 4, 18, 18);
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 10px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(poke.name[0], rightX + 17, y + 17);

            ctx.fillStyle = '#c0c0d0';
            ctx.font = '11px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`${poke.name} Lv${poke.level}`, rightX + 30, y + 17);
        }

        // Ready status
        const statusY = canvasH - 38;
        ctx.fillStyle = playerReady ? '#48c048' : '#808090';
        ctx.font = 'bold 11px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(playerReady ? 'READY!' : 'Select lead, press Z', 10, statusY);

        ctx.fillStyle = opponentReady ? '#48c048' : '#808090';
        ctx.textAlign = 'right';
        ctx.fillText(opponentReady ? 'READY!' : 'Waiting...', canvasW - 10, statusY);

        renderHint(ctx, canvasW, canvasH, playerReady ? 'Waiting for opponent...' : 'U/D: Select Lead | Z: Ready | B: Disconnect');
    }

    function renderBattle(ctx, canvasW, canvasH) {
        // Battle scene background
        ctx.fillStyle = '#2a2a3a';
        ctx.fillRect(0, 36, canvasW, canvasH - 36);

        // Ground
        ctx.fillStyle = '#3a3a2a';
        ctx.fillRect(0, canvasH * 0.55, canvasW, canvasH * 0.45 - 90);

        // Turn indicator
        ctx.fillStyle = '#606070';
        ctx.font = '9px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`Turn ${turnNumber}`, 10, 48);

        // Turn timer (only during battle phase)
        if (phase === 'battle') {
            const timeLeft = Math.max(0, TURN_TIME_LIMIT - turnTimer);
            const timerSecs = Math.ceil(timeLeft / 1000);
            ctx.fillStyle = timerSecs <= 10 ? '#e04040' : '#808090';
            ctx.textAlign = 'right';
            ctx.fillText(`${timerSecs}s`, canvasW - 10, 48);
        }

        // Enemy Pokemon (top right area)
        if (enemyPokemon) {
            const ex = canvasW * 0.65;
            const ey = canvasH * 0.18;
            const shakeX = enemyShake > 0 ? Math.sin(enemyShake * 0.05) * 4 : 0;

            // Pokemon sprite (type-colored)
            const typeColor = TYPE_COLORS[enemyPokemon.type] || '#a0a0a0';
            ctx.fillStyle = typeColor;
            ctx.fillRect(ex + shakeX - 20, ey - 20, 40, 40);
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 16px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(enemyPokemon.name.substring(0, 3), ex + shakeX, ey + 5);

            // Enemy info box (top left)
            renderInfoBox(ctx, 10, 54, canvasW * 0.45, enemyPokemon, enemyHpDisplay, false);
        }

        // Player Pokemon (bottom left area)
        if (playerPokemon) {
            const px = canvasW * 0.25;
            const py = canvasH * 0.5;
            const shakeX = playerShake > 0 ? Math.sin(playerShake * 0.05) * 4 : 0;

            const typeColor = TYPE_COLORS[playerPokemon.type] || '#a0a0a0';
            ctx.fillStyle = typeColor;
            ctx.fillRect(px + shakeX - 24, py - 24, 48, 48);
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 20px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(playerPokemon.name.substring(0, 3), px + shakeX, py + 6);

            // Player info box (right side)
            renderInfoBox(ctx, canvasW * 0.5, canvasH * 0.38, canvasW * 0.48, playerPokemon, playerHpDisplay, true);
        }

        // Text box / Menu area (bottom)
        const boxY = canvasH - 90;
        ctx.fillStyle = 'rgba(16, 16, 32, 0.92)';
        ctx.fillRect(5, boxY, canvasW - 10, 85);
        ctx.strokeStyle = '#a0a0a0';
        ctx.lineWidth = 2;
        ctx.strokeRect(5, boxY, canvasW - 10, 85);

        // Show battle log text
        if (logIndex < battleLog.length) {
            const currentText = battleLog[logIndex];
            const displayText = currentText.substring(0, charIdx);
            ctx.fillStyle = '#f8f8f8';
            ctx.font = '13px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(displayText, 16, boxY + 24);

            if (charIdx >= currentText.length) {
                if (Math.floor(Date.now() / 400) % 2 === 0) {
                    ctx.fillText('\u25BC', canvasW - 30, boxY + 70);
                }
            }
        } else if (phase === 'turn_wait') {
            // Waiting for opponent
            const dots = '.'.repeat(Math.floor(turnTimer / 500) % 4);
            ctx.fillStyle = '#a0a0b0';
            ctx.font = 'bold 13px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(`Waiting for opponent${dots}`, canvasW / 2, boxY + 40);
        } else if (phase === 'battle') {
            // Battle menu
            if (battleMenuMode === 'main') {
                const menuItems = ['Fight', 'Pokemon', 'Forfeit'];
                for (let i = 0; i < menuItems.length; i++) {
                    const mx = 16 + (i % 2) * (canvasW / 2 - 20);
                    const my = boxY + 14 + Math.floor(i / 2) * 30;
                    const isSelected = i === moveChoice;

                    if (isSelected) {
                        ctx.fillStyle = '#e04040';
                        ctx.fillRect(mx - 4, my - 4, canvasW / 2 - 24, 26);
                    }
                    ctx.fillStyle = isSelected ? '#f8f8f8' : '#808090';
                    ctx.font = 'bold 14px monospace';
                    ctx.textAlign = 'left';
                    if (isSelected) ctx.fillText('\u25B6', mx, my + 12);
                    ctx.fillText(menuItems[i], mx + 16, my + 12);
                }
            } else if (battleMenuMode === 'fight') {
                const moves = playerPokemon.moves || [];
                for (let i = 0; i < moves.length; i++) {
                    const mx = 16 + (i % 2) * (canvasW / 2 - 20);
                    const my = boxY + 14 + Math.floor(i / 2) * 30;
                    const isSelected = i === moveChoice;
                    const move = moves[i];
                    const moveColor = TYPE_COLORS[move.type] || '#a0a0a0';

                    if (isSelected) {
                        ctx.fillStyle = moveColor;
                        ctx.globalAlpha = 0.4;
                        ctx.fillRect(mx - 4, my - 4, canvasW / 2 - 24, 26);
                        ctx.globalAlpha = 1;
                    }
                    ctx.fillStyle = isSelected ? '#f8f8f8' : '#808090';
                    ctx.font = '12px monospace';
                    ctx.textAlign = 'left';
                    if (isSelected) ctx.fillText('\u25B6', mx, my + 12);
                    ctx.fillText(move.name, mx + 16, my + 12);

                    // Move type indicator
                    ctx.fillStyle = moveColor;
                    ctx.fillRect(mx + canvasW / 2 - 70, my + 2, 36, 14);
                    ctx.fillStyle = '#fff';
                    ctx.font = '8px monospace';
                    ctx.textAlign = 'center';
                    ctx.fillText(move.type, mx + canvasW / 2 - 52, my + 12);
                }

                ctx.fillStyle = '#606070';
                ctx.font = '9px monospace';
                ctx.textAlign = 'right';
                ctx.fillText('B: Back', canvasW - 16, boxY + 78);
            }
        }
    }

    function renderInfoBox(ctx, x, y, w, pokemon, hpDisplay, isPlayer) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(x, y, w, 44);
        ctx.strokeStyle = '#606060';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, w, 44);

        // Name and level
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(pokemon.name, x + 6, y + 14);

        ctx.fillStyle = '#a0a0a0';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`Lv${pokemon.level}`, x + w - 6, y + 14);

        // HP bar
        const barX = x + 6;
        const barY = y + 20;
        const barW = w - 12;
        const hpRatio = Math.max(0, hpDisplay / pokemon.maxHp);

        ctx.fillStyle = '#303030';
        ctx.fillRect(barX, barY, barW, 8);
        ctx.fillStyle = hpRatio > 0.5 ? '#48c048' : hpRatio > 0.2 ? '#f8c830' : '#e04038';
        ctx.fillRect(barX + 1, barY + 1, (barW - 2) * hpRatio, 6);

        // HP text
        if (isPlayer) {
            ctx.fillStyle = '#c0c0c0';
            ctx.font = '9px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(`${Math.ceil(hpDisplay)}/${pokemon.maxHp}`, x + w - 6, y + 40);
        }
    }

    function renderResults(ctx, canvasW, canvasH) {
        // Dark overlay
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        const cx = canvasW / 2;
        const cy = canvasH / 2 - 40;

        // Result text
        if (battleResult === 'win') {
            ctx.fillStyle = '#f8d030';
            ctx.font = 'bold 22px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('VICTORY!', cx, cy);

            ctx.fillStyle = '#48c048';
            ctx.font = '12px monospace';
            ctx.fillText(`You defeated ${opponent.name}!`, cx, cy + 24);
            ctx.fillText(`Rating: ${pvpRating} (+25)`, cx, cy + 42);
        } else if (battleResult === 'lose') {
            ctx.fillStyle = '#e04040';
            ctx.font = 'bold 22px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('DEFEAT', cx, cy);

            ctx.fillStyle = '#a0a0b0';
            ctx.font = '12px monospace';
            ctx.fillText(`${opponent.name} wins!`, cx, cy + 24);
            ctx.fillText(`Rating: ${pvpRating} (-20)`, cx, cy + 42);
        } else if (battleResult === 'disconnect') {
            ctx.fillStyle = '#f8d030';
            ctx.font = 'bold 18px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('Opponent Disconnected', cx, cy);
            ctx.fillStyle = '#48c048';
            ctx.font = '12px monospace';
            ctx.fillText('You win by default!', cx, cy + 24);
        }

        // Battle record
        ctx.fillStyle = '#808090';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Record: ${pvpWins}W - ${pvpLosses}L`, cx, cy + 66);

        // Good game
        ctx.fillStyle = '#a0a0b0';
        ctx.font = 'bold 12px monospace';
        ctx.fillText('Good game!', cx, cy + 88);

        // Options
        const options = ['Rematch', 'Exit'];
        for (let i = 0; i < options.length; i++) {
            const oy = cy + 106 + i * 28;
            const isSelected = i === rematchOption;

            if (isSelected) {
                ctx.fillStyle = 'rgba(160, 50, 50, 0.5)';
                ctx.fillRect(cx - 60, oy - 8, 120, 24);
                ctx.strokeStyle = '#e06060';
                ctx.lineWidth = 1;
                ctx.strokeRect(cx - 60, oy - 8, 120, 24);
            }

            ctx.fillStyle = isSelected ? '#f8f8f8' : '#606070';
            ctx.font = 'bold 13px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(options[i], cx, oy + 8);
        }
    }

    function renderHint(ctx, canvasW, canvasH, text) {
        ctx.fillStyle = '#404050';
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(text, canvasW / 2, canvasH - 6);
    }

    return { open, close, isActive, update, render, FORMATS };
})();
