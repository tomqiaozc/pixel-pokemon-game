// ledges.js — One-way ledge jump system

const Ledges = (() => {
    const TILE = Sprites.TILE;

    let jumping = false;
    let jumpTimer = 0;
    let jumpStartX = 0;
    let jumpStartY = 0;
    let jumpEndX = 0;
    let jumpEndY = 0;
    let jumpDir = 0;

    const JUMP_DURATION = 300; // ms
    const JUMP_HEIGHT = 8; // pixels of arc height

    // Dust particles on landing
    let dustParticles = [];

    // Check if a tile is a ledge (uses ROCK tiles placed in routes as ledges)
    // Ledges are one-way: player can jump down (south) but not climb up
    function isLedge(tileX, tileY) {
        // Check map data for ledge tiles
        // In routes.js, ledges are placed as ROCK tiles in horizontal rows
        // We treat horizontal rows of rocks on routes as ledges
        const map = MapLoader.getCurrentMap();
        if (!map) return false;

        // Check if there's a registered ledge at this position
        if (map.ledges) {
            for (const ledge of map.ledges) {
                if (tileX >= ledge.x1 && tileX <= ledge.x2 && tileY === ledge.y) {
                    return true;
                }
            }
        }
        return false;
    }

    // Try to jump over a ledge
    // Returns true if jump started, false if blocked
    function tryJump(playerX, playerY, dir) {
        if (jumping) return false;
        // Only allow jumping down (south, dir=0)
        if (dir !== 0) return false;

        const tileX = Math.floor((playerX + TILE / 2) / TILE);
        const tileY = Math.floor((playerY + TILE / 2) / TILE);
        const belowTileY = tileY + 1;

        if (!isLedge(tileX, belowTileY)) return false;

        // Check landing tile (2 tiles below = 1 past the ledge)
        const landTileY = tileY + 2;
        if (GameMap.isSolid(tileX, landTileY)) return false;

        // Start jump
        jumping = true;
        jumpTimer = 0;
        jumpDir = dir;
        jumpStartX = playerX;
        jumpStartY = playerY;
        jumpEndX = playerX;
        jumpEndY = playerY + TILE * 2; // Jump 2 tiles down

        return true;
    }

    function update(dt) {
        // Update dust particles
        for (const p of dustParticles) {
            p.age += dt;
            p.x += p.vx * dt * 0.06;
            p.y += p.vy * dt * 0.06;
            p.vy += 0.001 * dt;
        }
        dustParticles = dustParticles.filter(p => p.age < p.life);

        if (!jumping) return { jumping: false };

        jumpTimer += dt;
        const progress = Math.min(1, jumpTimer / JUMP_DURATION);

        // Linear interpolation for X/Y
        const currentX = jumpStartX + (jumpEndX - jumpStartX) * progress;
        const currentY = jumpStartY + (jumpEndY - jumpStartY) * progress;

        // Parabolic arc for visual height offset
        const arcHeight = -JUMP_HEIGHT * 4 * progress * (progress - 1);

        if (progress >= 1) {
            jumping = false;
            // Spawn landing dust
            spawnDust(jumpEndX + TILE / 2, jumpEndY + TILE);
            return {
                jumping: false,
                landed: true,
                x: jumpEndX,
                y: jumpEndY,
            };
        }

        return {
            jumping: true,
            x: currentX,
            y: currentY,
            arcHeight,
        };
    }

    function spawnDust(cx, cy) {
        for (let i = 0; i < 6; i++) {
            dustParticles.push({
                x: cx + (Math.random() - 0.5) * 16,
                y: cy + Math.random() * 4,
                vx: (Math.random() - 0.5) * 1.5,
                vy: -Math.random() * 0.8,
                size: 2 + Math.random() * 3,
                life: 300 + Math.random() * 200,
                age: 0,
            });
        }
    }

    function renderDust(ctx, camX, camY, scale) {
        for (const p of dustParticles) {
            const alpha = 1 - p.age / p.life;
            ctx.globalAlpha = alpha * 0.6;
            ctx.fillStyle = '#c0b090';
            const screenX = (p.x - camX) * scale;
            const screenY = (p.y - camY) * scale;
            ctx.fillRect(screenX, screenY, p.size * scale, p.size * scale);
        }
        ctx.globalAlpha = 1;
    }

    function isJumping() { return jumping; }

    function getArcHeight() {
        if (!jumping) return 0;
        const progress = Math.min(1, jumpTimer / JUMP_DURATION);
        return -JUMP_HEIGHT * 4 * progress * (progress - 1);
    }

    return { isLedge, tryJump, update, renderDust, isJumping, getArcHeight };
})();
