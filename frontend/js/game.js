// game.js — Main game loop with state management

const Game = (() => {
    const TILE = Sprites.TILE;
    const MOVE_SPEED = 1.5; // pixels per frame
    const ANIM_INTERVAL = 150; // ms between walk frames

    // Game states: starter, overworld, battle, evolution, pokecenter, gym, badge_award
    let state = 'starter';
    let canvas, ctx;
    let pendingBadge = null;
    let previousState = null;

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
        Routes.registerAll();
        canvas = document.getElementById('game-canvas');
        ctx = canvas.getContext('2d');
        StarterSelect.reset();
        lastTime = performance.now();
        requestAnimationFrame(loop);
    }

    function loop(timestamp) {
        const dt = timestamp - lastTime;
        lastTime = timestamp;

        if (state === 'starter') {
            updateStarter(dt);
        } else if (state === 'overworld') {
            updateOverworld(dt);
            Renderer.render(player, dt);
            // Render dialogue overlay on top of overworld
            if (Dialogue.isActive()) {
                Dialogue.render(ctx, canvas.width, canvas.height);
            }
            // Render pause menu overlay
            if (PauseMenu.isActive()) {
                PauseMenu.render(ctx, canvas.width, canvas.height);
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
                const leaderPokemon = {
                    name: result.leader.type === 'Rock' ? 'Onix' : 'Rhydon',
                    level: result.leader.type === 'Rock' ? 14 : 50,
                    hp: result.leader.type === 'Rock' ? 35 : 105,
                    maxHp: result.leader.type === 'Rock' ? 35 : 105,
                    type: result.leader.type,
                };
                pendingBadge = result.badge;
                previousState = 'gym';
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
            }];
            state = 'overworld';
            loadMap('pallet_town');
            Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
        }
    }

    function updateOverworld(dt) {
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
            startBattle(trainerResult.trainer.pokemon[0], { canRun: false, battleType: 'trainer' });
            TrainerEncounter.defeatTrainer(MapLoader.getCurrentMapId(), trainerResult.trainer.name);
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

    // Load a map by id
    function loadMap(mapId) {
        MapLoader.setCurrentMap(mapId);
        const map = MapLoader.getCurrentMap();
        if (!map) return;
        GameMap.loadMapData(map.data, map.width, map.height);
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
    }

    function updateBattle(dt) {
        const result = Battle.update(dt);
        Battle.render();

        if (result.done) {
            // Sync HP back to party after battle
            if (player.party[0] && result.playerHp !== undefined) {
                player.party[0].hp = Math.max(0, result.playerHp);
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
                    });
                }
            }

            if (pendingBadge && result.result === 'win') {
                BadgeCase.earnBadge(pendingBadge.index);
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

    return { player, getState, setState, startBattle, startEvolution, enterPokeCenter };
})();
