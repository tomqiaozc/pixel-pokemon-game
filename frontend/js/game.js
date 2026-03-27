// game.js — Main game loop with state management

const Game = (() => {
    const TILE = Sprites.TILE;
    const MOVE_SPEED = 1.5; // pixels per frame
    const ANIM_INTERVAL = 150; // ms between walk frames

    // Game states: starter, overworld, battle
    let state = 'starter';
    let canvas, ctx;

    // Player state
    const player = {
        x: 14 * TILE,   // Starting position (on the dirt path)
        y: 10 * TILE,
        dir: 0,          // 0=down, 1=up, 2=left, 3=right
        animFrame: 0,    // 0=stand, 1=walk1, 2=walk2
        animTimer: 0,
        moving: false,
        starter: null,   // Chosen starter Pokemon
    };

    let lastTime = 0;

    function init() {
        Input.init();
        Renderer.init();
        NPC.init();
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
        }

        requestAnimationFrame(loop);
    }

    function updateStarter(dt) {
        const result = StarterSelect.update(dt, canvas);
        StarterSelect.render(ctx, canvas.width, canvas.height);

        if (result.done) {
            player.starter = result.starter;
            state = 'overworld';
            Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
        }
    }

    function updateOverworld(dt) {
        // Update NPC animations
        NPC.update(dt);

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
            return; // Lock player movement during dialogue
        }

        // Check for NPC interaction (action key)
        if (Input.isActionPressed()) {
            const npc = NPC.checkInteraction(player.x, player.y, player.dir);
            if (npc) {
                Dialogue.start(npc.name, npc.dialogue);
                return;
            }
        }

        const movement = Input.getMovement();

        if (movement) {
            player.moving = true;
            player.dir = movement.dir;

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

        // Encounter check
        const encounter = Encounters.update(dt, player);
        if (encounter.startBattle) {
            startBattle(encounter.enemy);
        }
    }

    // Expose for other modules
    function getState() { return state; }
    function setState(s) { state = s; }

    function startBattle(enemyData) {
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

        const starterName = player.starter ? player.starter.name : 'Charmander';
        const starterType = player.starter ? player.starter.type : 'Fire';

        Battle.start({
            name: starterName,
            level: 5,
            hp: 20,
            maxHp: 20,
            exp: 0,
            maxExp: 100,
            type: starterType,
            moves: starterMoves[starterName] || starterMoves['Charmander'],
        }, enemyData);

        state = 'battle';
    }

    function updateBattle(dt) {
        const result = Battle.update(dt);
        Battle.render();

        if (result.done) {
            state = 'overworld';
            Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
        }
    }

    // Start the game when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return { player, getState, setState, startBattle };
})();
