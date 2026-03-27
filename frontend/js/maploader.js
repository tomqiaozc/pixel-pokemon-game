// maploader.js — Multi-map rendering system with transitions

const MapLoader = (() => {
    const TILE = Sprites.TILE;

    // All registered maps
    const maps = {};
    let currentMapId = 'starter_town';
    let previousMapId = null;

    // Transition state
    let transitioning = false;
    let transitionPhase = 'none'; // none, fade_out, loading, fade_in
    let transitionAlpha = 0;
    let transitionTarget = null; // { mapId, spawnX, spawnY, spawnDir }

    // Map name popup
    let mapNameTimer = 0;
    let mapNameText = '';
    let mapNameAlpha = 0;

    const TRANSITION_SPEED = 0.004;
    const MAP_NAME_DURATION = 2500;
    const MAP_NAME_FADE = 500;

    // Register a map definition
    function registerMap(id, config) {
        maps[id] = {
            id,
            name: config.name || id,
            width: config.width,
            height: config.height,
            data: config.data,
            exits: config.exits || [],    // { x, y, targetMap, spawnX, spawnY, spawnDir }
            doors: config.doors || [],    // { x, y, targetMap, spawnX, spawnY, spawnDir }
            npcs: config.npcs || [],
            trainers: config.trainers || [],
            tileTypes: config.tileTypes || null, // custom tile types for this map
        };
    }

    // Get current map data
    function getCurrentMap() {
        return maps[currentMapId] || null;
    }

    function getCurrentMapId() {
        return currentMapId;
    }

    function getMapName() {
        const map = maps[currentMapId];
        return map ? map.name : '';
    }

    // Check if player is at an exit point
    function checkExits(playerX, playerY) {
        const map = maps[currentMapId];
        if (!map || transitioning) return null;

        const tileX = Math.floor((playerX + TILE / 2) / TILE);
        const tileY = Math.floor((playerY + TILE / 2) / TILE);

        // Check edge exits
        for (const exit of map.exits) {
            if (tileX === exit.x && tileY === exit.y) {
                return exit;
            }
        }

        // Check if at map edge (auto-transition for routes)
        if (tileX <= 0 || tileX >= map.width - 1 || tileY <= 0 || tileY >= map.height - 1) {
            for (const exit of map.exits) {
                // Match exit direction
                if (exit.edge === 'north' && tileY <= 0) return exit;
                if (exit.edge === 'south' && tileY >= map.height - 1) return exit;
                if (exit.edge === 'east' && tileX >= map.width - 1) return exit;
                if (exit.edge === 'west' && tileX <= 0) return exit;
            }
        }

        return null;
    }

    // Check door tiles
    function checkDoors(playerX, playerY) {
        const map = maps[currentMapId];
        if (!map || transitioning) return null;

        const tileX = Math.floor((playerX + TILE / 2) / TILE);
        const tileY = Math.floor((playerY + TILE / 2) / TILE);

        for (const door of map.doors) {
            if (tileX === door.x && tileY === door.y) {
                return door;
            }
        }
        return null;
    }

    // Start transition to a new map
    function transitionTo(targetMapId, spawnX, spawnY, spawnDir) {
        if (transitioning) return;
        transitioning = true;
        transitionPhase = 'fade_out';
        transitionAlpha = 0;
        transitionTarget = {
            mapId: targetMapId,
            spawnX: spawnX * TILE,
            spawnY: spawnY * TILE,
            spawnDir: spawnDir || 0,
        };
    }

    // Update transition animation
    function update(dt) {
        // Update map name popup
        if (mapNameTimer > 0) {
            mapNameTimer -= dt;
            if (mapNameTimer > MAP_NAME_DURATION - MAP_NAME_FADE) {
                // Fading in
                mapNameAlpha = Math.min(1, (MAP_NAME_DURATION - mapNameTimer) / MAP_NAME_FADE);
            } else if (mapNameTimer < MAP_NAME_FADE) {
                // Fading out
                mapNameAlpha = Math.max(0, mapNameTimer / MAP_NAME_FADE);
            } else {
                mapNameAlpha = 1;
            }
        } else {
            mapNameAlpha = 0;
        }

        if (!transitioning) return { transitioning: false };

        if (transitionPhase === 'fade_out') {
            transitionAlpha += TRANSITION_SPEED * dt;
            if (transitionAlpha >= 1) {
                transitionAlpha = 1;
                transitionPhase = 'loading';
            }
        } else if (transitionPhase === 'loading') {
            // Switch map
            previousMapId = currentMapId;
            currentMapId = transitionTarget.mapId;
            transitionPhase = 'fade_in';

            // Show map name popup
            const map = maps[currentMapId];
            if (map) {
                mapNameText = map.name;
                mapNameTimer = MAP_NAME_DURATION;
            }

            // Return spawn position for game.js to reposition player
            return {
                transitioning: true,
                loaded: true,
                spawnX: transitionTarget.spawnX,
                spawnY: transitionTarget.spawnY,
                spawnDir: transitionTarget.spawnDir,
            };
        } else if (transitionPhase === 'fade_in') {
            transitionAlpha -= TRANSITION_SPEED * dt;
            if (transitionAlpha <= 0) {
                transitionAlpha = 0;
                transitionPhase = 'none';
                transitioning = false;
            }
        }

        return { transitioning: true };
    }

    // Render transition overlay
    function renderTransition(ctx, canvasW, canvasH) {
        // Map name popup
        if (mapNameAlpha > 0) {
            const popupW = Math.max(140, mapNameText.length * 11 + 40);
            const popupH = 30;
            const popupX = (canvasW - popupW) / 2;
            const popupY = 12;

            ctx.globalAlpha = mapNameAlpha * 0.85;
            ctx.fillStyle = '#202020';
            ctx.fillRect(popupX, popupY, popupW, popupH);
            ctx.strokeStyle = '#f8f8f8';
            ctx.lineWidth = 2;
            ctx.strokeRect(popupX, popupY, popupW, popupH);

            ctx.fillStyle = '#f8f8f8';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(mapNameText, canvasW / 2, popupY + 20);
            ctx.textAlign = 'left';
            ctx.globalAlpha = 1;
        }

        // Fade overlay
        if (transitionAlpha > 0) {
            ctx.fillStyle = `rgba(0, 0, 0, ${transitionAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }
    }

    function setCurrentMap(mapId) {
        currentMapId = mapId;
    }

    function isTransitioning() {
        return transitioning;
    }

    return {
        registerMap,
        getCurrentMap,
        getCurrentMapId,
        setCurrentMap,
        getMapName,
        checkExits,
        checkDoors,
        transitionTo,
        update,
        renderTransition,
        isTransitioning,
    };
})();
