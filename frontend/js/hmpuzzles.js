// hmpuzzles.js — HM overworld puzzle module (Cut, Strength, Flash obstacles)

const HMPuzzles = (() => {
    const TILE = Sprites.TILE;

    // Obstacle state per map: mapId -> array of obstacles
    let obstacles = {};
    // Removed obstacle tracking: mapId -> Set of obstacle ids
    let removedObstacles = {};
    // Boulder positions (may differ from original after pushing)
    let boulderPositions = {}; // obstacleId -> { x, y }
    // Strength activated flag (per map session)
    let strengthActive = false;

    // HM animation state
    let animActive = false;
    let animType = ''; // 'cut', 'strength', 'boulder_push'
    let animTimer = 0;
    let animX = 0;
    let animY = 0;
    let animObstacleId = '';
    let animDirection = '';
    const CUT_ANIM_DURATION = 600;    // ms
    const PUSH_ANIM_DURATION = 300;   // ms

    // HM prompt state
    let promptActive = false;
    let promptHmMove = '';
    let promptObstacle = null;
    let promptPokemonIndex = -1;

    // --- API Wiring ---

    function loadObstacles(mapId) {
        API.getHMObstacles(mapId).then(data => {
            if (data && Array.isArray(data)) {
                obstacles[mapId] = data;
            }
        }).catch(err => console.error('Failed to load HM obstacles:', err));

        // Load removed/pushed state for this game
        API.getHMObstacleState(mapId).then(data => {
            if (data) {
                if (data.removed && Array.isArray(data.removed)) {
                    if (!removedObstacles[mapId]) removedObstacles[mapId] = new Set();
                    for (const id of data.removed) {
                        removedObstacles[mapId].add(id);
                    }
                }
                if (data.boulders && typeof data.boulders === 'object') {
                    for (const [id, pos] of Object.entries(data.boulders)) {
                        boulderPositions[id] = { x: pos.x, y: pos.y };
                    }
                }
            }
        }).catch(err => console.error('Failed to load HM obstacle state:', err));
    }

    // --- Obstacle Queries ---

    function getObstaclesForMap(mapId) {
        return obstacles[mapId] || [];
    }

    function isObstacleAt(mapId, tileX, tileY) {
        const mapObstacles = obstacles[mapId];
        if (!mapObstacles) return false;

        for (const obs of mapObstacles) {
            // Skip removed obstacles
            if (removedObstacles[mapId] && removedObstacles[mapId].has(obs.id)) continue;

            if (obs.obstacle_type === 'pushable_boulder') {
                // Check pushed position
                const pos = boulderPositions[obs.id] || { x: obs.x, y: obs.y };
                if (pos.x === tileX && pos.y === tileY) return true;
            } else if (obs.obstacle_type === 'cuttable_tree') {
                if (obs.x === tileX && obs.y === tileY) return true;
            }
            // surf_zone obstacles don't block — they define water areas
        }
        return false;
    }

    function getObstacleAtFacing(mapId, playerX, playerY, dir) {
        const tileX = Math.floor((playerX + TILE / 2) / TILE);
        const tileY = Math.floor((playerY + TILE / 2) / TILE);

        // Calculate the tile the player is facing
        let facingX = tileX;
        let facingY = tileY;
        if (dir === 0) facingY += 1;      // down
        else if (dir === 1) facingY -= 1; // up
        else if (dir === 2) facingX -= 1; // left
        else if (dir === 3) facingX += 1; // right

        const mapObstacles = obstacles[mapId];
        if (!mapObstacles) return null;

        for (const obs of mapObstacles) {
            if (removedObstacles[mapId] && removedObstacles[mapId].has(obs.id)) continue;

            if (obs.obstacle_type === 'pushable_boulder') {
                const pos = boulderPositions[obs.id] || { x: obs.x, y: obs.y };
                if (pos.x === facingX && pos.y === facingY) return obs;
            } else if (obs.obstacle_type === 'cuttable_tree') {
                if (obs.x === facingX && obs.y === facingY) return obs;
            }
        }
        return null;
    }

    // --- HM Use ---

    function tryUseHM(mapId, playerX, playerY, dir) {
        const obstacle = getObstacleAtFacing(mapId, playerX, playerY, dir);
        if (!obstacle) return false;

        if (obstacle.obstacle_type === 'cuttable_tree') {
            showHMPrompt('Cut', obstacle);
            return true;
        }
        if (obstacle.obstacle_type === 'pushable_boulder') {
            if (strengthActive) {
                // Push boulder directly
                pushBoulder(mapId, obstacle, dir);
                return true;
            }
            showHMPrompt('Strength', obstacle);
            return true;
        }
        return false;
    }

    function showHMPrompt(hmMove, obstacle) {
        promptActive = true;
        promptHmMove = hmMove;
        promptObstacle = obstacle;
        // Find first party Pokemon that could know the HM (simplified — index 0)
        promptPokemonIndex = 0;

        const obstacleLabel = obstacle.obstacle_type === 'cuttable_tree' ? 'this tree' : 'this boulder';
        Dialogue.start('HM', [`Use ${hmMove} on ${obstacleLabel}?`, 'Press action key to confirm.']);
    }

    function confirmHMUse(mapId) {
        if (!promptActive) return;
        promptActive = false;

        if (promptHmMove === 'Cut') {
            useCut(mapId, promptObstacle);
        } else if (promptHmMove === 'Strength') {
            useStrength(mapId, promptObstacle);
        }
    }

    function cancelHMPrompt() {
        promptActive = false;
        promptHmMove = '';
        promptObstacle = null;
    }

    function isPromptActive() {
        return promptActive;
    }

    // --- Cut ---

    function useCut(mapId, obstacle) {
        API.useHM('Cut', mapId, obstacle.x, obstacle.y, 0).then(data => {
            if (data && data.success) {
                // Mark tree as removed
                if (!removedObstacles[mapId]) removedObstacles[mapId] = new Set();
                removedObstacles[mapId].add(obstacle.id);
                PlayerStats.increment('treesCut');
            }
        }).catch(err => console.error('Failed to use Cut:', err));

        // Start animation immediately for responsiveness
        startCutAnimation(obstacle.x, obstacle.y, obstacle.id);
    }

    function startCutAnimation(tileX, tileY, obstacleId) {
        animActive = true;
        animType = 'cut';
        animTimer = 0;
        animX = tileX;
        animY = tileY;
        animObstacleId = obstacleId;
    }

    // --- Strength ---

    function useStrength(mapId, obstacle) {
        API.useHM('Strength', mapId, obstacle.x, obstacle.y, 0).then(data => {
            if (data && data.success) {
                strengthActive = true;
            }
        }).catch(err => console.error('Failed to use Strength:', err));

        // Activate locally for responsiveness
        strengthActive = true;
        Dialogue.start('', ['Strength activated! You can now push boulders.']);
    }

    function pushBoulder(mapId, obstacle, dir) {
        const pos = boulderPositions[obstacle.id] || { x: obstacle.x, y: obstacle.y };
        let newX = pos.x;
        let newY = pos.y;
        let dirStr = '';

        if (dir === 0) { newY += 1; dirStr = 'down'; }
        else if (dir === 1) { newY -= 1; dirStr = 'up'; }
        else if (dir === 2) { newX -= 1; dirStr = 'left'; }
        else if (dir === 3) { newX += 1; dirStr = 'right'; }

        // Check if destination is solid
        if (GameMap.isSolid(newX, newY) || isObstacleAt(mapId, newX, newY)) {
            return; // Can't push into wall or another obstacle
        }

        API.pushBoulder(obstacle.id, dirStr).then(data => {
            if (data && data.success) {
                boulderPositions[obstacle.id] = { x: data.new_x, y: data.new_y };
            }
        }).catch(err => console.error('Failed to push boulder:', err));

        // Animate locally for responsiveness
        startPushAnimation(pos.x, pos.y, obstacle.id, dirStr);
        boulderPositions[obstacle.id] = { x: newX, y: newY };
    }

    function startPushAnimation(tileX, tileY, obstacleId, direction) {
        animActive = true;
        animType = 'boulder_push';
        animTimer = 0;
        animX = tileX;
        animY = tileY;
        animObstacleId = obstacleId;
        animDirection = direction;
    }

    // --- Animation ---

    function update(dt) {
        if (animActive) {
            animTimer += dt;
            const duration = animType === 'cut' ? CUT_ANIM_DURATION : PUSH_ANIM_DURATION;
            if (animTimer >= duration) {
                // Cut animation end: mark obstacle removed locally
                if (animType === 'cut') {
                    const mapId = MapLoader.getCurrentMapId();
                    if (!removedObstacles[mapId]) removedObstacles[mapId] = new Set();
                    removedObstacles[mapId].add(animObstacleId);
                }
                animActive = false;
            }
        }
    }

    function isAnimating() {
        return animActive;
    }

    // --- Rendering ---

    function renderObstacles(ctx, camX, camY, scale, mapId) {
        const mapObstacles = obstacles[mapId];
        if (!mapObstacles) return;

        for (const obs of mapObstacles) {
            if (removedObstacles[mapId] && removedObstacles[mapId].has(obs.id)) continue;

            if (obs.obstacle_type === 'cuttable_tree') {
                // During cut animation, show shaking/disappearing tree
                if (animActive && animType === 'cut' && animObstacleId === obs.id) {
                    renderCutAnimation(ctx, camX, camY, scale);
                    continue;
                }
                const sprite = Sprites.drawCuttableTree();
                const screenX = (obs.x * TILE - camX) * scale;
                const screenY = (obs.y * TILE - camY) * scale;
                ctx.drawImage(sprite, screenX, screenY, TILE * scale, TILE * scale);
            } else if (obs.obstacle_type === 'pushable_boulder') {
                const pos = boulderPositions[obs.id] || { x: obs.x, y: obs.y };

                // During push animation, interpolate position
                if (animActive && animType === 'boulder_push' && animObstacleId === obs.id) {
                    renderPushAnimation(ctx, camX, camY, scale, pos);
                    continue;
                }
                const sprite = Sprites.drawPushableBoulder();
                const screenX = (pos.x * TILE - camX) * scale;
                const screenY = (pos.y * TILE - camY) * scale;
                ctx.drawImage(sprite, screenX, screenY, TILE * scale, TILE * scale);
            }
        }
    }

    function renderCutAnimation(ctx, camX, camY, scale) {
        const progress = Math.min(1, animTimer / CUT_ANIM_DURATION);
        const screenX = (animX * TILE - camX) * scale;
        const screenY = (animY * TILE - camY) * scale;
        const s = scale;

        if (progress < 0.33) {
            // Frame 1: Slash effect across the tree
            const sprite = Sprites.drawCuttableTree();
            ctx.drawImage(sprite, screenX, screenY, TILE * s, TILE * s);
            // Slash line
            const slashProgress = progress / 0.33;
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2 * s;
            ctx.beginPath();
            ctx.moveTo(screenX + 2 * s, screenY + 4 * s);
            ctx.lineTo(screenX + 2 * s + slashProgress * 12 * s, screenY + 4 * s + slashProgress * 8 * s);
            ctx.stroke();
        } else if (progress < 0.66) {
            // Frame 2: Tree shakes
            const shakeOffset = Math.sin((progress - 0.33) * 60) * 2 * s;
            const sprite = Sprites.drawCuttableTree();
            ctx.drawImage(sprite, screenX + shakeOffset, screenY, TILE * s, TILE * s);
        } else {
            // Frame 3: Tree fades and disappears
            const fadeProgress = (progress - 0.66) / 0.34;
            ctx.globalAlpha = 1 - fadeProgress;
            const sprite = Sprites.drawCuttableTree();
            ctx.drawImage(sprite, screenX, screenY - fadeProgress * 4 * s, TILE * s, TILE * s);
            ctx.globalAlpha = 1;

            // Leaf particles
            const leafCount = 6;
            for (let i = 0; i < leafCount; i++) {
                const lx = screenX + TILE * s / 2 + Math.sin(i * 1.3 + progress * 10) * fadeProgress * 20 * s;
                const ly = screenY + fadeProgress * (10 + i * 5) * s;
                const leafAlpha = Math.max(0, 1 - fadeProgress * 1.5);
                ctx.fillStyle = `rgba(72, 160, 72, ${leafAlpha})`;
                ctx.fillRect(lx, ly, 2 * s, 2 * s);
            }
        }
    }

    function renderPushAnimation(ctx, camX, camY, scale, targetPos) {
        const progress = Math.min(1, animTimer / PUSH_ANIM_DURATION);
        // Interpolate from old position to new position
        const dx = animDirection === 'right' ? 1 : animDirection === 'left' ? -1 : 0;
        const dy = animDirection === 'down' ? 1 : animDirection === 'up' ? -1 : 0;

        const startX = animX;
        const startY = animY;
        const currentX = startX + dx * progress;
        const currentY = startY + dy * progress;

        const screenX = (currentX * TILE - camX) * scale;
        const screenY = (currentY * TILE - camY) * scale;

        const sprite = Sprites.drawPushableBoulder();
        ctx.drawImage(sprite, screenX, screenY, TILE * scale, TILE * scale);
    }

    function renderHMAnimation(ctx, canvasW, canvasH) {
        if (!animActive) return;

        // Render HM name text at top of screen during animation
        const hmName = animType === 'cut' ? 'Cut' : 'Strength';
        const progress = Math.min(1, animTimer / (animType === 'cut' ? CUT_ANIM_DURATION : PUSH_ANIM_DURATION));

        if (progress < 0.5) {
            const textAlpha = Math.min(1, progress / 0.2);
            ctx.globalAlpha = textAlpha;
            ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
            ctx.fillRect(canvasW / 2 - 50, 8, 100, 24);
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(hmName + '!', canvasW / 2, 24);
            ctx.textAlign = 'left';
            ctx.globalAlpha = 1;
        }
    }

    // --- Map Change ---

    function onMapChange(mapId) {
        strengthActive = false; // Reset strength per map
        loadObstacles(mapId);
    }

    // --- Public API ---

    return {
        loadObstacles,
        getObstaclesForMap,
        isObstacleAt,
        getObstacleAtFacing,
        tryUseHM,
        showHMPrompt,
        confirmHMUse,
        cancelHMPrompt,
        isPromptActive,
        pushBoulder,
        update,
        isAnimating,
        renderObstacles,
        renderHMAnimation,
        onMapChange,
    };
})();
