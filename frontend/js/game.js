// game.js — Main game loop and player logic

const Game = (() => {
    const TILE = Sprites.TILE;
    const MOVE_SPEED = 1.5; // pixels per frame
    const ANIM_INTERVAL = 150; // ms between walk frames

    // Player state
    const player = {
        x: 14 * TILE,   // Starting position (on the dirt path)
        y: 10 * TILE,
        dir: 0,          // 0=down, 1=up, 2=left, 3=right
        animFrame: 0,    // 0=stand, 1=walk1, 2=walk2
        animTimer: 0,
        moving: false,
    };

    let lastTime = 0;

    function init() {
        Input.init();
        Renderer.init();
        Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
        lastTime = performance.now();
        requestAnimationFrame(loop);
    }

    function loop(timestamp) {
        const dt = timestamp - lastTime;
        lastTime = timestamp;

        update(dt);
        Renderer.render(player, dt);

        requestAnimationFrame(loop);
    }

    function update(dt) {
        const movement = Input.getMovement();

        if (movement) {
            player.moving = true;
            player.dir = movement.dir;

            // Calculate new position
            let newX = player.x + movement.dx * MOVE_SPEED;
            let newY = player.y + movement.dy * MOVE_SPEED;

            // Collision detection — check corners of player bounding box
            // Player hitbox is slightly smaller than full tile for smoother movement
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

                if (GameMap.isSolid(tileX, tileTop) || GameMap.isSolid(tileX, tileBottom)) {
                    newX = player.x; // Block horizontal
                }
            }

            // Check vertical movement
            if (movement.dy !== 0) {
                const checkY = movement.dy > 0 ? bottom : top;
                const tileLeft  = Math.floor((newX + margin) / TILE);
                const tileRight = Math.floor((newX + TILE - margin - 1) / TILE);
                const tileY     = Math.floor(checkY / TILE);

                if (GameMap.isSolid(tileLeft, tileY) || GameMap.isSolid(tileRight, tileY)) {
                    newY = player.y; // Block vertical
                }
            }

            player.x = newX;
            player.y = newY;

            // Walk animation
            player.animTimer += dt;
            if (player.animTimer >= ANIM_INTERVAL) {
                player.animFrame = (player.animFrame % 2) + 1; // cycle 1 -> 2 -> 1
                player.animTimer = 0;
            }
        } else {
            player.moving = false;
            player.animFrame = 0;
            player.animTimer = 0;
        }

        // Center camera on player
        Renderer.centerCamera(player.x + TILE / 2, player.y + TILE / 2);
    }

    // Start the game when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return { player };
})();
