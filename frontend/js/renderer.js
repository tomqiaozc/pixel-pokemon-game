// renderer.js — Canvas rendering system with camera

const Renderer = (() => {
    const TILE = Sprites.TILE;
    const SCALE = 3; // Each pixel is 3x3 on screen
    const VIEWPORT_TILES_X = 15; // Tiles visible horizontally
    const VIEWPORT_TILES_Y = 11; // Tiles visible vertically

    let canvas, ctx;
    let canvasW, canvasH;

    // Camera position in world pixels (top-left of viewport)
    let camX = 0;
    let camY = 0;

    // Water animation frame counter
    let waterFrame = 0;
    let waterTimer = 0;

    function init() {
        canvas = document.getElementById('game-canvas');
        ctx = canvas.getContext('2d');

        canvasW = VIEWPORT_TILES_X * TILE * SCALE;
        canvasH = VIEWPORT_TILES_Y * TILE * SCALE;

        canvas.width = canvasW;
        canvas.height = canvasH;

        ctx.imageSmoothingEnabled = false;
    }

    // Center camera on a world-pixel position
    function centerCamera(worldX, worldY) {
        const halfW = (VIEWPORT_TILES_X * TILE) / 2;
        const halfH = (VIEWPORT_TILES_Y * TILE) / 2;

        camX = worldX - halfW;
        camY = worldY - halfH;

        // Clamp to map bounds
        const maxX = GameMap.MAP_W * TILE - VIEWPORT_TILES_X * TILE;
        const maxY = GameMap.MAP_H * TILE - VIEWPORT_TILES_Y * TILE;
        camX = Math.max(0, Math.min(camX, maxX));
        camY = Math.max(0, Math.min(camY, maxY));
    }

    function render(player, dt) {
        // Update water animation
        waterTimer += dt;
        if (waterTimer > 500) {
            waterFrame++;
            waterTimer = 0;
        }

        ctx.clearRect(0, 0, canvasW, canvasH);

        // Determine which tiles are visible
        const startTileX = Math.floor(camX / TILE);
        const startTileY = Math.floor(camY / TILE);
        const offsetX = -(camX % TILE);
        const offsetY = -(camY % TILE);

        // Draw tiles
        for (let ty = -1; ty <= VIEWPORT_TILES_Y + 1; ty++) {
            for (let tx = -1; tx <= VIEWPORT_TILES_X + 1; tx++) {
                const mapX = startTileX + tx;
                const mapY = startTileY + ty;
                const tile = GameMap.getTile(mapX, mapY);
                const sprite = getTileSprite(tile);
                if (sprite) {
                    const screenX = (offsetX + tx * TILE) * SCALE;
                    const screenY = (offsetY + ty * TILE) * SCALE;
                    ctx.drawImage(sprite, screenX, screenY, TILE * SCALE, TILE * SCALE);
                }
            }
        }

        // Draw NPCs
        NPC.render(ctx, camX, camY, SCALE);

        // Draw sign posts
        const mapId = MapLoader.getCurrentMapId();
        const signs = Signs.getSignsForMap(mapId);
        for (const sign of signs) {
            const signScreenX = (sign.x * TILE - camX) * SCALE;
            const signScreenY = (sign.y * TILE - camY) * SCALE;
            drawSignPost(ctx, signScreenX, signScreenY, SCALE);
        }

        // Draw trainer NPCs
        TrainerEncounter.render(ctx, camX, camY, SCALE);

        // Draw player (with ledge arc height offset)
        const arcHeight = Ledges.getArcHeight();
        const playerScreenX = (player.x - camX) * SCALE;
        const playerScreenY = (player.y - camY - arcHeight) * SCALE;
        const playerSprite = Sprites.drawPlayer(player.dir, player.animFrame);
        ctx.drawImage(playerSprite, playerScreenX, playerScreenY, TILE * SCALE, TILE * SCALE);

        // Draw ledge dust particles
        Ledges.renderDust(ctx, camX, camY, SCALE);

        // Draw encounter overlay effects (grass rustles, exclamation, transitions)
        Encounters.renderOverlay(ctx, camX, camY, SCALE, canvasW, canvasH);

        // Draw day/night tint overlay (rendered BEFORE weather so particles show on top)
        const currentMapId = MapLoader.getCurrentMapId();
        const mapConfig = MapLoader.getCurrentMap();
        if (!mapConfig || !mapConfig.isIndoor) {
            DayCycle.renderOverlay(ctx, canvasW, canvasH, performance.now());
        }

        // Draw overworld weather particles (rain, hail, sand) — AFTER tint so they're visible at night
        Weather.renderOverworld(ctx, canvasW, canvasH);

        // Draw lamp glow at night (after tint, after weather)
        if (!mapConfig || !mapConfig.isIndoor) {
            DayCycle.renderLamps(ctx, camX, camY, SCALE, currentMapId);
        }

        // Draw map transition overlay (fade + map name popup)
        MapLoader.renderTransition(ctx, canvasW, canvasH);
    }

    function drawSignPost(ctx, x, y, scale) {
        const s = scale;
        // Wooden post
        ctx.fillStyle = '#806030';
        ctx.fillRect(x + 6 * s, y + 6 * s, 4 * s, 10 * s);
        // Sign board
        ctx.fillStyle = '#a08040';
        ctx.fillRect(x + 2 * s, y + 2 * s, 12 * s, 8 * s);
        // Border
        ctx.strokeStyle = '#604020';
        ctx.lineWidth = s;
        ctx.strokeRect(x + 2 * s, y + 2 * s, 12 * s, 8 * s);
    }

    function getTileSprite(type) {
        switch (type) {
            case GameMap.T.GRASS:      return Sprites.drawGrass();
            case GameMap.T.TALL_GRASS: return Sprites.drawTallGrass();
            case GameMap.T.DIRT:       return Sprites.drawDirt();
            case GameMap.T.WATER:      return Sprites.drawWater(waterFrame);
            case GameMap.T.TREE:       return Sprites.drawTree();
            case GameMap.T.ROCK:       return Sprites.drawRock();
            case GameMap.T.FLOWER:     return Sprites.drawFlower();
            case GameMap.T.HOUSE_WALL: return Sprites.drawHouseWall();
            case GameMap.T.HOUSE_ROOF: return Sprites.drawHouseRoof();
            case GameMap.T.DOOR:       return Sprites.drawDoor();
            default:                   return Sprites.drawGrass();
        }
    }

    return { init, centerCamera, render, SCALE, TILE, getCamX: () => camX, getCamY: () => camY };
})();
