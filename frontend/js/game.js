// game.js — Main game loop with state management

const Game = (() => {
    const TILE = Sprites.TILE;
    const MOVE_SPEED = 1.5; // pixels per frame
    const ANIM_INTERVAL = 150; // ms between walk frames

    // Game states: starter, overworld, battle, evolution, pokecenter, gym, badge_award, minigame, cutscene
    let state = 'starter';
    let canvas, ctx;
    let pendingBadge = null;
    let previousState = null;
    let pendingDefeatedTrainer = null;

    // Player state
    const player = {
        x: 14 * TILE,   // Starting position (on the dirt path)
        y: 10 * TILE,
        dir: 0,          // 0=down, 1=up, 2=left, 3=right
        animFrame: 0,    // 0=stand, 1=walk1, 2=walk2
        animTimer: 0,
        moving: false,
        starter: null,   // Chosen starter Pokemon
        party: [],       // Array of Pokemon with current stats (hp, level, etc.)
    };

    let lastTime = 0;

    function init() {
        Input.init();
        Renderer.init();
        NPC.init();
        Quests.init();
        Routes.registerAll();
        PlayerStats.load();
        Achievements.loadEarned();
        canvas = document.getElementById('game-canvas');
        ctx = canvas.getContext('2d');
        StarterSelect.reset();
        lastTime = performance.now();

        // Try loading a saved game from backend
        tryLoadGame();

        requestAnimationFrame(loop);
    }

    function tryLoadGame() {
        // Check if there's a saved game session to restore
        API.getGameState().then(data => {
            if (data && data.player && data.player.team && data.player.team.length > 0) {
                // Restore player state from save
                const p = data.player;
                player.party = p.team.map(poke => ({
                    name: poke.name,
                    type: poke.types ? poke.types[0] : 'Normal',
                    level: poke.level || 5,
                    hp: poke.current_hp || poke.stats.hp,
                    maxHp: poke.stats ? poke.stats.hp : 20,
                    exp: 0,
                    maxExp: 100,
                    attack: poke.stats ? poke.stats.attack : 10,
                    defense: poke.stats ? poke.stats.defense : 10,
                    spAttack: poke.stats ? poke.stats.sp_attack : 10,
                    spDefense: poke.stats ? poke.stats.sp_defense : 10,
                    speed: poke.stats ? poke.stats.speed : 10,
                    speciesId: poke.id || 0,
                    moves: (poke.moves || []).map(m => ({
                        name: m.name, type: m.type, power: m.power || 0,
                        pp: m.pp || 35, maxPp: m.pp || 35,
                    })),
                }));
                player.starter = { name: player.party[0].name, type: player.party[0].type };
                player.money = p.money || 3000;
                if (p.position) {
                    player.x = (p.position.x || 14) * TILE;
                    player.y = (p.position.y || 10) * TILE;
                    player.dir = p.position.facing === 'up' ? 1 : p.position.facing === 'left' ? 2 : p.position.facing === 'right' ? 3 : 0;
                }
                const mapId = (p.position && p.position.map_id) || 'pallet_town';
                state = 'overworld';
                loadMap(mapId);
                Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
            }
        }).catch(() => {
            // No saved game — stay on starter select screen
        });
    }

    function loop(timestamp) {
        const dt = timestamp - lastTime;
        lastTime = timestamp;

        // Track play time and check achievements
        PlayerStats.updatePlayTime(dt);
        Achievements.update(dt);
        Achievements.checkAchievements();

        if (state === 'starter') {
            updateStarter(dt);
        } else if (state === 'overworld') {
            updateOverworld(dt);
            Renderer.render(player, dt);
            // Render dialogue overlay on top of overworld
            if (Dialogue.isActive()) {
                Dialogue.render(ctx, canvas.width, canvas.height);
            }
            // Render quest HUD
            Quests.updateHUD(dt);
            Quests.renderHUD(ctx, canvas.width, canvas.height);
            // Render quest journal overlay
            if (Quests.isJournalOpen()) {
                Quests.renderJournal(ctx, canvas.width, canvas.height);
            }
            // Render pause menu overlay
            if (PauseMenu.isActive()) {
                PauseMenu.render(ctx, canvas.width, canvas.height);
            }
            // Render achievement popup (on top of everything)
            Achievements.renderPopup(ctx, canvas.width, canvas.height);
        } else if (state === 'cutscene') {
            updateCutscene(dt);
            Renderer.render(player, dt);
            Cutscene.renderOverlay(ctx, canvas.width, canvas.height);
            if (Dialogue.isActive()) {
                Dialogue.render(ctx, canvas.width, canvas.height);
            }
        } else if (state === 'minigame') {
            MiniGames.update(dt);
            MiniGames.render(ctx, canvas.width, canvas.height);
            if (!MiniGames.isActive()) {
                state = 'overworld';
                Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
            }
        } else if (state === 'battle') {
            updateBattle(dt);
        } else if (state === 'evolution') {
            Evolution.update(dt);
            Evolution.render(ctx, canvas.width, canvas.height);
            if (!Evolution.isActive()) {
                state = 'overworld';
                Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
            }
        } else if (state === 'pokecenter') {
            const result = PokeCenter.update(dt);
            PokeCenter.render(ctx, canvas.width, canvas.height);
            if (result.exited) {
                state = 'overworld';
                Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
            }
        } else if (state === 'gym') {
            const result = Gym.update(dt);
            Gym.render(ctx, canvas.width, canvas.height);
            if (result.exited) {
                state = 'overworld';
                Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
            }
            if (result.battleLeader) {
                // Use backend team data if available, fallback to hardcoded
                const leaderTeam = result.leader.team;
                const leaderPokemon = leaderTeam && leaderTeam.length > 0
                    ? leaderTeam[0]
                    : {
                        name: result.leader.type === 'Rock' ? 'Onix' : 'Rhydon',
                        level: result.leader.type === 'Rock' ? 14 : 50,
                        hp: result.leader.type === 'Rock' ? 35 : 105,
                        maxHp: result.leader.type === 'Rock' ? 35 : 105,
                        type: result.leader.type,
                    };
                pendingBadge = result.badge;
                previousState = 'gym';
                // Notify backend of gym challenge
                const gymId = Gym.getActiveGym() && Gym.getActiveGym().gymId;
                if (gymId) API.challengeGym(gymId).catch(() => {});
                startBattle(leaderPokemon, { canRun: false, battleType: 'trainer' });
            }
            if (result.battleTrainer) {
                previousState = 'gym';
                startBattle(result.trainer.pokemon[0], { canRun: false, battleType: 'trainer' });
            }
        } else if (state === 'badge_award') {
            updateBadgeAward(dt);
        }

        requestAnimationFrame(loop);
    }

    function updateStarter(dt) {
        const result = StarterSelect.update(dt, canvas);
        StarterSelect.render(ctx, canvas.width, canvas.height);

        if (result.done) {
            player.starter = result.starter;
            player.party = [{
                name: result.starter.name,
                type: result.starter.type,
                level: 5,
                hp: 20,
                maxHp: 20,
                exp: 0,
                maxExp: 100,
                attack: 10, defense: 10, spAttack: 10, spDefense: 10, speed: 10,
                speciesId: 0,
            }];
            state = 'overworld';
            loadMap('pallet_town');
            Quests.onStarterChosen();
            Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);

            // Create backend game session and apply IV-calculated stats
            API.createGame('Red', result.starter.name).then(data => {
                if (data && data.player && data.player.team && data.player.team[0]) {
                    const s = data.player.team[0];
                    const lead = player.party[0];
                    if (s.stats) {
                        lead.maxHp = s.stats.hp || lead.maxHp;
                        lead.hp = s.current_hp || s.stats.hp || lead.hp;
                        lead.attack = s.stats.attack || lead.attack;
                        lead.defense = s.stats.defense || lead.defense;
                        lead.spAttack = s.stats.sp_attack || lead.spAttack;
                        lead.spDefense = s.stats.sp_defense || lead.spDefense;
                        lead.speed = s.stats.speed || lead.speed;
                    }
                    if (s.id) lead.speciesId = s.id;
                    if (s.moves && s.moves.length) {
                        lead.moves = s.moves.map(m => ({
                            name: m.name, type: m.type, power: m.power || 0,
                            pp: m.pp || 35, maxPp: m.pp || 35,
                        }));
                    }
                }
            });
        }
    }

    function updateOverworld(dt) {
        // Update day/night cycle
        DayCycle.update(dt);

        // Update weather particles
        Weather.update(dt);

        // Update overworld weather triggers (random weather per map)
        Weather.updateOverworld(dt, MapLoader.getCurrentMapId());

        // Update map transitions
        const transResult = MapLoader.update(dt);
        if (transResult.transitioning) {
            if (transResult.loaded) {
                loadMap(MapLoader.getCurrentMapId());
                player.x = transResult.spawnX;
                player.y = transResult.spawnY;
                player.dir = transResult.spawnDir || 0;
                Encounters.reset();
            }
            return;
        }

        // Update NPC animations
        NPC.update(dt);

        // Update trainer encounter sequence
        const trainerResult = TrainerEncounter.update(dt);
        if (trainerResult.encountering) return;
        if (trainerResult.startBattle) {
            pendingDefeatedTrainer = { mapId: MapLoader.getCurrentMapId(), name: trainerResult.trainer.name };
            startBattle(trainerResult.trainer.pokemon[0], { canRun: false, battleType: 'trainer' });
            return;
        }

        // Update ledge jumps
        const ledgeResult = Ledges.update(dt);
        if (ledgeResult.jumping) {
            player.x = ledgeResult.x;
            player.y = ledgeResult.y;
            Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
            return;
        }
        if (ledgeResult.landed) {
            player.x = ledgeResult.x;
            player.y = ledgeResult.y;
        }

        // Handle quest journal
        if (Quests.isJournalOpen()) {
            Quests.updateJournal(dt);
            return;
        }

        // Open quest journal with Q
        if (Input.isDown('q') || Input.isDown('Q')) {
            Quests.openJournal();
            return;
        }

        // Handle pause menu
        if (PauseMenu.isActive()) {
            PauseMenu.update(dt);
            return;
        }

        // Open pause menu with Escape
        if (Input.isDown('Escape')) {
            PauseMenu.open();
            return;
        }

        // Update dialogue if active
        if (Dialogue.isActive()) {
            Dialogue.update(dt);
            return;
        }

        // Check for NPC/sign interaction (action key)
        if (Input.isActionPressed()) {
            const npc = NPC.checkInteraction(player.x, player.y, player.dir);
            if (npc) {
                // Shopkeeper NPC opens shop interface
                if (npc.type === 'shopkeeper') {
                    openShopForNpc(npc);
                    return;
                }
                Dialogue.start(npc.name, npc.dialogue);
                return;
            }
            const sign = Signs.checkInteraction(player.x, player.y, player.dir);
            if (sign) {
                Dialogue.start('Sign', sign.text);
                return;
            }
        }

        const movement = Input.getMovement();

        if (movement) {
            player.moving = true;
            player.dir = movement.dir;

            // Try ledge jump before normal movement
            if (Ledges.tryJump(player.x, player.y, movement.dir)) return;

            // Calculate new position
            let newX = player.x + movement.dx * MOVE_SPEED;
            let newY = player.y + movement.dy * MOVE_SPEED;

            // Collision detection — check corners of player bounding box
            const margin = 3;
            const left   = newX + margin;
            const right  = newX + TILE - margin - 1;
            const top    = newY + margin;
            const bottom = newY + TILE - 1;

            // Check horizontal movement
            if (movement.dx !== 0) {
                const checkX = movement.dx > 0 ? right : left;
                const tileTop    = Math.floor((player.y + margin) / TILE);
                const tileBottom = Math.floor((player.y + TILE - 1) / TILE);
                const tileX      = Math.floor(checkX / TILE);

                if (GameMap.isSolid(tileX, tileTop) || GameMap.isSolid(tileX, tileBottom) ||
                    NPC.isSolid(tileX, tileTop) || NPC.isSolid(tileX, tileBottom)) {
                    newX = player.x;
                }
            }

            // Check vertical movement
            if (movement.dy !== 0) {
                const checkY = movement.dy > 0 ? bottom : top;
                const tileLeft  = Math.floor((newX + margin) / TILE);
                const tileRight = Math.floor((newX + TILE - margin - 1) / TILE);
                const tileY     = Math.floor(checkY / TILE);

                if (GameMap.isSolid(tileLeft, tileY) || GameMap.isSolid(tileRight, tileY) ||
                    NPC.isSolid(tileLeft, tileY) || NPC.isSolid(tileRight, tileY)) {
                    newY = player.y;
                }
            }

            player.x = newX;
            player.y = newY;

            // Walk animation
            player.animTimer += dt;
            if (player.animTimer >= ANIM_INTERVAL) {
                player.animFrame = (player.animFrame % 2) + 1;
                player.animTimer = 0;
                PlayerStats.increment('steps');
            }
        } else {
            player.moving = false;
            player.animFrame = 0;
            player.animTimer = 0;
        }

        // Center camera on player
        Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);

        // Check map exits
        const exit = MapLoader.checkExits(player.x, player.y);
        if (exit) {
            MapLoader.transitionTo(exit.targetMap, exit.spawnX, exit.spawnY, exit.spawnDir);
            return;
        }

        // Check doors
        const door = MapLoader.checkDoors(player.x, player.y);
        if (door) {
            if (door.targetMap === 'pokecenter') {
                enterPokeCenter();
                return;
            }
            if (door.targetMap === 'pewter_gym') {
                Gym.enter('pewter');
                state = 'gym';
                return;
            }
            if (door.targetMap === 'viridian_gym') {
                if (BadgeCase.getBadgeCount() < 7) {
                    Dialogue.start('Sign', ['This gym is locked. You need at least 7 badges to enter.']);
                    return;
                }
                Gym.enter('viridian');
                state = 'gym';
                return;
            }
            MapLoader.transitionTo(door.targetMap, door.spawnX, door.spawnY, door.spawnDir);
            return;
        }

        // Trainer line-of-sight check
        TrainerEncounter.checkLineOfSight(player.x, player.y);

        // Encounter check
        const encounter = Encounters.update(dt, player);
        if (encounter.startBattle) {
            startBattle(encounter.enemy);
        }
    }

    function updateCutscene(dt) {
        if (!Cutscene.isActive()) {
            state = 'overworld';
            return;
        }
        const result = Cutscene.update(dt);
        if (result && result.startBattle) {
            startBattle(result.enemy, result.options);
        }
        if (Dialogue.isActive()) {
            Dialogue.update(dt);
        }
    }

    function startCutscene(steps) {
        Cutscene.start(steps);
        state = 'cutscene';
    }

    function startMiniGame(gameType) {
        if (gameType === 'slots') MiniGames.startSlots();
        else if (gameType === 'memory') MiniGames.startMemory();
        else if (gameType === 'quiz') MiniGames.startQuiz();
        state = 'minigame';
    }

    // Load a map by id
    function loadMap(mapId) {
        MapLoader.setCurrentMap(mapId);
        const map = MapLoader.getCurrentMap();
        if (!map) return;
        GameMap.loadMapData(map.data, map.width, map.height);
        NPC.loadForMap(mapId);
        Quests.onMapEnter(mapId);
        Weather.onMapChange(mapId);
        if (map.trainers) {
            TrainerEncounter.loadTrainers(mapId, map.trainers);
        }
    }

    // Expose for other modules
    function getState() { return state; }
    function setState(s) { state = s; }

    function startEvolution(prePokemon, postPokemon) {
        Evolution.start(prePokemon, postPokemon, (wasCancelled) => {
            if (!wasCancelled) {
                // Update player's starter if it evolved
                if (player.starter && player.starter.name === prePokemon.name) {
                    player.starter = { ...player.starter, name: postPokemon.name, type: postPokemon.type };
                }
            }
        });
        state = 'evolution';
    }

    function enterPokeCenter() {
        PokeCenter.enter();
        state = 'pokecenter';
    }

    function startBattle(enemyData, options) {
        const starterMoves = {
            'Bulbasaur':  [
                { name: 'Tackle', type: 'Normal', power: 40, pp: 35, maxPp: 35 },
                { name: 'Vine Whip', type: 'Grass', power: 45, pp: 25, maxPp: 25 },
                { name: 'Growl', type: 'Normal', power: 0, pp: 40, maxPp: 40 },
                { name: 'Leech Seed', type: 'Grass', power: 0, pp: 10, maxPp: 10 },
            ],
            'Charmander': [
                { name: 'Scratch', type: 'Normal', power: 40, pp: 35, maxPp: 35 },
                { name: 'Ember', type: 'Fire', power: 40, pp: 25, maxPp: 25 },
                { name: 'Growl', type: 'Normal', power: 0, pp: 40, maxPp: 40 },
                { name: 'Smokescreen', type: 'Normal', power: 0, pp: 20, maxPp: 20 },
            ],
            'Squirtle':   [
                { name: 'Tackle', type: 'Normal', power: 40, pp: 35, maxPp: 35 },
                { name: 'Water Gun', type: 'Water', power: 40, pp: 25, maxPp: 25 },
                { name: 'Tail Whip', type: 'Normal', power: 0, pp: 30, maxPp: 30 },
                { name: 'Withdraw', type: 'Water', power: 0, pp: 40, maxPp: 40 },
            ],
        };

        const lead = player.party[0];
        const starterName = lead ? lead.name : 'Charmander';
        const starterType = lead ? lead.type : 'Fire';

        Battle.start({
            name: starterName,
            level: lead ? lead.level : 5,
            hp: lead ? lead.hp : 20,
            maxHp: lead ? lead.maxHp : 20,
            exp: lead ? lead.exp : 0,
            maxExp: lead ? lead.maxExp : 100,
            type: starterType,
            moves: starterMoves[starterName] || starterMoves['Charmander'],
        }, enemyData, options);

        state = 'battle';

        // Start backend battle session and pass battleId to Battle module
        API.startBattle(enemyData).then(data => {
            if (data && data.battle && data.battle.id) {
                Battle.setBattleId(data.battle.id);
            }
        });
    }

    // Shop interaction for shopkeeper NPCs
    let shopItems = [];
    let shopIndex = 0;
    let shopActive = false;
    let shopId = 'viridian'; // default shop

    function openShopForNpc(npc) {
        shopId = npc.shopId || 'viridian';
        Dialogue.startChoice(npc.name,
            'Welcome! What would you like to do?',
            [
                { text: 'Buy', value: 'buy' },
                { text: 'Sell', value: 'sell' },
                { text: 'Cancel', value: 'cancel' },
            ],
            (choice) => {
                if (choice === 'buy') {
                    API.getShop(shopId).then(data => {
                        if (data && data.items && data.items.length > 0) {
                            shopItems = data.items;
                            shopIndex = 0;
                            showShopBuyMenu(npc);
                        } else {
                            Dialogue.start(npc.name, ['Sorry, we are out of stock!']);
                        }
                    }).catch(() => {
                        Dialogue.start(npc.name, ['Sorry, the shop system is unavailable.']);
                    });
                } else if (choice === 'sell') {
                    Dialogue.start(npc.name, ['Sorry, I can\'t buy items from you right now.']);
                } else {
                    Dialogue.start(npc.name, ['Come back anytime!']);
                }
            }
        );
    }

    function showShopBuyMenu(npc) {
        const itemNames = shopItems.map(si => ({
            text: `${si.name || si.item_name} - $${si.price}`,
            value: si.item_id || si.id,
        }));
        itemNames.push({ text: 'Cancel', value: 'cancel' });
        Dialogue.startChoice(npc.name,
            `You have $${player.money || 3000}. What would you like to buy?`,
            itemNames,
            (itemId) => {
                if (itemId === 'cancel') {
                    Dialogue.start(npc.name, ['Come back anytime!']);
                    return;
                }
                API.buyItem(shopId, itemId, 1).then(result => {
                    if (result && result.success) {
                        player.money = result.money !== undefined ? result.money : (player.money || 3000) - 200;
                        Dialogue.start(npc.name, [result.message || 'Thank you for your purchase!']);
                        // Refresh inventory
                        if (typeof PauseMenu !== 'undefined') PauseMenu.inventory;
                    } else {
                        Dialogue.start(npc.name, [result?.message || 'You can\'t afford that!']);
                    }
                }).catch(() => {
                    Dialogue.start(npc.name, ['Transaction failed. Try again later.']);
                });
            }
        );
    }

    // Species ID mapping for EXP award calls
    const SPECIES_IDS = {
        'Bulbasaur': 1, 'Ivysaur': 2, 'Venusaur': 3,
        'Charmander': 4, 'Charmeleon': 5, 'Charizard': 6,
        'Squirtle': 7, 'Wartortle': 8, 'Blastoise': 9,
        'Caterpie': 10, 'Metapod': 11, 'Butterfree': 12,
        'Weedle': 13, 'Kakuna': 14, 'Beedrill': 15,
        'Pidgey': 16, 'Pidgeotto': 17, 'Pidgeot': 18,
        'Rattata': 19, 'Raticate': 20,
        'Oddish': 43, 'Geodude': 74, 'Onix': 95, 'Rhydon': 112,
        'Sandslash': 28, 'Dugtrio': 51,
    };

    function updateBattle(dt) {
        const result = Battle.update(dt);
        Battle.render();

        if (result.done) {
            // Sync HP back to party after battle
            if (player.party[0] && result.playerHp !== undefined) {
                player.party[0].hp = Math.max(0, result.playerHp);
            }

            // Track battle stats
            if (result.result === 'win') {
                PlayerStats.increment('battlesWon');
                if (player.party[0]) PlayerStats.recordBattlePokemon(player.party[0].name);
            } else if (result.result === 'lose') {
                PlayerStats.increment('battlesLost');
            } else if (result.result === 'catch') {
                PlayerStats.increment('battlesWon');
                PlayerStats.increment('pokemonCaught');
                if (result.enemyPokemon) PlayerStats.increment('pokemonSeen');
            }

            // Award EXP after battle victory (fire-and-forget with local fallback)
            if (result.result === 'win' && result.enemyPokemon && player.party[0]) {
                const defeatedName = result.enemyPokemon.name;
                const defeatedLevel = result.enemyPokemon.level;
                const speciesId = SPECIES_IDS[defeatedName] || 19;

                // Local EXP calculation as fallback
                const expGained = Math.floor((defeatedLevel * 50) / 7) + 10;
                player.party[0].exp = (player.party[0].exp || 0) + expGained;

                // Check for level up
                if (player.party[0].exp >= player.party[0].maxExp) {
                    player.party[0].level++;
                    player.party[0].exp -= player.party[0].maxExp;
                    player.party[0].maxExp = Math.floor(player.party[0].maxExp * 1.2);
                    const hpGain = 2 + Math.floor(Math.random() * 3);
                    player.party[0].maxHp += hpGain;
                    player.party[0].hp = Math.min(player.party[0].hp + hpGain, player.party[0].maxHp);
                }

                // Backend EXP award (async, updates server-side state)
                API.awardExp(0, speciesId, defeatedLevel).then(expResult => {
                    if (expResult && expResult.leveled_up && player.party[0]) {
                        player.party[0].level = expResult.new_level;
                        if (expResult.new_stats) {
                            const ns = expResult.new_stats;
                            player.party[0].maxHp = ns.hp || player.party[0].maxHp;
                            player.party[0].attack = ns.attack || ns.atk || player.party[0].attack;
                            player.party[0].defense = ns.defense || ns.def || player.party[0].defense;
                            player.party[0].spAttack = ns.sp_attack || ns.spAttack || player.party[0].spAttack;
                            player.party[0].spDefense = ns.sp_defense || ns.spDefense || player.party[0].spDefense;
                            player.party[0].speed = ns.speed || ns.spd || player.party[0].speed;
                        }
                    }
                    if (expResult && expResult.can_evolve && player.party[0]) {
                        // Use backend evolution check instead of hardcoded evoMap
                        const specId = player.party[0].speciesId || SPECIES_IDS[player.party[0].name] || 0;
                        API.checkEvolution(specId, player.party[0].level).then(evoData => {
                            if (evoData && evoData.evolves_to) {
                                const prePokemon = { name: player.party[0].name, type: player.party[0].type };
                                const postPokemon = {
                                    name: evoData.evolves_to.name || evoData.evolves_to,
                                    type: evoData.evolves_to.types ? evoData.evolves_to.types[0] : player.party[0].type,
                                };
                                // Tell backend to apply evolution
                                API.evolve(0).then(evolveResult => {
                                    if (evolveResult && evolveResult.new_name) {
                                        player.party[0].name = evolveResult.new_name;
                                        if (evolveResult.new_types && evolveResult.new_types[0]) {
                                            player.party[0].type = evolveResult.new_types[0];
                                        }
                                        if (evolveResult.new_stats) {
                                            const ns = evolveResult.new_stats;
                                            player.party[0].maxHp = ns.hp || player.party[0].maxHp;
                                            player.party[0].attack = ns.attack || player.party[0].attack;
                                            player.party[0].defense = ns.defense || player.party[0].defense;
                                            player.party[0].spAttack = ns.sp_attack || player.party[0].spAttack;
                                            player.party[0].spDefense = ns.sp_defense || player.party[0].spDefense;
                                            player.party[0].speed = ns.speed || player.party[0].speed;
                                        }
                                        if (evolveResult.new_species_id) {
                                            player.party[0].speciesId = evolveResult.new_species_id;
                                        }
                                    }
                                    startEvolution(prePokemon, postPokemon);
                                }).catch(() => {
                                    startEvolution(prePokemon, postPokemon);
                                });
                            } else {
                                // Fallback: try local evoMap
                                const localEvoMap = { Bulbasaur: 'Ivysaur', Charmander: 'Charmeleon', Squirtle: 'Wartortle' };
                                const evoName = localEvoMap[player.party[0].name];
                                if (evoName) {
                                    const prePokemon = { name: player.party[0].name, type: player.party[0].type };
                                    startEvolution(prePokemon, { name: evoName, type: player.party[0].type });
                                }
                            }
                        }).catch(() => {
                            // Fallback: try local evoMap
                            const localEvoMap = { Bulbasaur: 'Ivysaur', Charmander: 'Charmeleon', Squirtle: 'Wartortle' };
                            const evoName = localEvoMap[player.party[0].name];
                            if (evoName) {
                                const prePokemon = { name: player.party[0].name, type: player.party[0].type };
                                startEvolution(prePokemon, { name: evoName, type: player.party[0].type });
                            }
                        });
                    }
                });
            }

            // Add caught Pokemon to party
            if (result.result === 'catch' && result.enemyPokemon) {
                const caught = result.enemyPokemon;
                if (player.party.length < 6) {
                    player.party.push({
                        name: caught.name,
                        type: caught.type,
                        level: caught.level,
                        hp: caught.hp,
                        maxHp: caught.maxHp,
                        exp: 0,
                        maxExp: 100,
                        attack: caught.attack || 10, defense: caught.defense || 10,
                        spAttack: caught.spAttack || 10, spDefense: caught.spDefense || 10,
                        speed: caught.speed || 10,
                        speciesId: caught.speciesId || 0,
                    });
                }
                // Register caught in pokedex (syncs to backend)
                const dexEntry = Pokedex.entries.find(e => e.name === caught.name);
                if (dexEntry) Pokedex.markCaught(dexEntry.id);
            }

            // Mark route trainer as defeated only after winning
            if (result.result === 'win' && pendingDefeatedTrainer) {
                TrainerEncounter.defeatTrainer(pendingDefeatedTrainer.mapId, pendingDefeatedTrainer.name);
                PlayerStats.increment('trainersDefeated');
            }
            pendingDefeatedTrainer = null;

            if (pendingBadge && result.result === 'win') {
                BadgeCase.earnBadge(pendingBadge.index);
                Quests.onBadgeEarned(pendingBadge.index);
                badgeAwardTimer = 0;
                badgeAwardBadge = pendingBadge;
                pendingBadge = null;
                previousState = null;
                state = 'badge_award';
                return;
            }

            if (previousState === 'gym') {
                previousState = null;
                pendingBadge = null;
                state = 'gym';
            } else {
                state = 'overworld';
                Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
            }
        }
    }

    let badgeAwardTimer = 0;
    let badgeAwardBadge = null;

    function updateBadgeAward(dt) {
        badgeAwardTimer += dt;

        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const progress = Math.min(1, badgeAwardTimer / 500);
        ctx.globalAlpha = progress;

        ctx.fillStyle = '#f8d830';
        ctx.font = 'bold 22px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Badge Earned!', canvas.width / 2, canvas.height / 2 - 60);

        if (badgeAwardBadge) {
            const badgeSize = 40 + Math.sin(badgeAwardTimer * 0.003) * 4;
            TrainerBattle.drawBadge(ctx, canvas.width / 2, canvas.height / 2 + 10, badgeSize, badgeAwardBadge.index, true);

            ctx.fillStyle = '#f8f8f8';
            ctx.font = 'bold 16px monospace';
            ctx.fillText(badgeAwardBadge.name, canvas.width / 2, canvas.height / 2 + 70);

            const shineAlpha = Math.sin(badgeAwardTimer * 0.005) * 0.3 + 0.3;
            ctx.globalAlpha = shineAlpha;
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(canvas.width / 2 - 15, canvas.height / 2 - 5, 6, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.globalAlpha = 1;

        if (badgeAwardTimer > 1500) {
            ctx.fillStyle = '#a0a0a0';
            ctx.font = '12px monospace';
            ctx.fillText('Press any key to continue', canvas.width / 2, canvas.height / 2 + 110);
        }

        ctx.textAlign = 'left';

        if (badgeAwardTimer > 1500 && (Input.isActionPressed() || Input.isDown('Escape'))) {
            badgeAwardBadge = null;
            state = 'gym';
        }
    }

    // Start the game when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return { player, getState, setState, startBattle, startEvolution, enterPokeCenter, startCutscene, startMiniGame };
})();
