// secretareas.js — Secret area discovery and rendering

const SecretAreas = (() => {
    const TILE = Sprites.TILE;

    // Discovered areas: mapId -> Set of "x,y" keys
    let discovered = {};

    // Discovery animation state
    let animActive = false;
    let animX = 0;
    let animY = 0;
    let animTimer = 0;
    let animMessage = '';
    const ANIM_DURATION = 2000;

    // Shimmer effect for undiscovered hints
    let shimmerTimer = 0;
    let shimmerFrame = 0;

    // --- API Wiring ---

    function loadDiscoveredAreas() {
        API.getSecretProgress().then(data => {
            if (data && Array.isArray(data.areas)) {
                for (const area of data.areas) {
                    const mapId = area.map_id;
                    if (!discovered[mapId]) discovered[mapId] = new Set();
                    discovered[mapId].add(`${area.x},${area.y}`);
                }
            }
        }).catch(err => console.error('Failed to load secret area progress:', err));
    }

    function checkForSecretArea(mapId, tileX, tileY) {
        // Skip if already discovered
        if (discovered[mapId] && discovered[mapId].has(`${tileX},${tileY}`)) return;

        API.checkSecretArea(mapId, tileX, tileY).then(data => {
            if (data && data.is_secret && !data.discovered) {
                // Secret area found — trigger discovery
                discoverArea(mapId, tileX, tileY);
            }
        }).catch(err => console.error('Failed to check secret area:', err));
    }

    function discoverArea(mapId, tileX, tileY) {
        API.discoverSecretArea(mapId, tileX, tileY).then(data => {
            // Mark discovered locally
            if (!discovered[mapId]) discovered[mapId] = new Set();
            discovered[mapId].add(`${tileX},${tileY}`);

            // Start discovery animation
            const message = (data && data.message) || 'Secret area discovered!';
            startAnimation(tileX, tileY, message);

            // Notify player stats
            PlayerStats.increment('secretsFound');

            // Check quest progress
            Quests.setFlag(`secret_${mapId}_${tileX}_${tileY}`);
        }).catch(err => console.error('Failed to discover secret area:', err));
    }

    // --- Animation ---

    function startAnimation(tileX, tileY, message) {
        animActive = true;
        animX = tileX;
        animY = tileY;
        animTimer = 0;
        animMessage = message;
    }

    function update(dt) {
        // Shimmer timer for undiscovered hints
        shimmerTimer += dt;
        if (shimmerTimer > 400) {
            shimmerFrame = (shimmerFrame + 1) % 4;
            shimmerTimer = 0;
        }

        // Discovery animation
        if (animActive) {
            animTimer += dt;
            if (animTimer >= ANIM_DURATION) {
                animActive = false;
            }
        }
    }

    function isAnimating() {
        return animActive;
    }

    // --- Rendering ---

    function renderDiscoveryAnimation(ctx, camX, camY, scale, canvasW, canvasH) {
        if (!animActive) return;

        const progress = Math.min(1, animTimer / ANIM_DURATION);
        const screenX = (animX * TILE + TILE / 2 - camX) * scale;
        const screenY = (animY * TILE + TILE / 2 - camY) * scale;

        // Phase 1 (0-0.5): sparkle burst expanding outward
        if (progress < 0.5) {
            const burstProgress = progress / 0.5;
            const sparkleCount = 12;
            const radius = burstProgress * 40 * scale;
            const alpha = 1 - burstProgress * 0.5;

            ctx.globalAlpha = alpha;
            for (let i = 0; i < sparkleCount; i++) {
                const angle = (Math.PI * 2 * i / sparkleCount) + burstProgress * Math.PI;
                const sx = screenX + Math.cos(angle) * radius;
                const sy = screenY + Math.sin(angle) * radius;
                const size = (1 - burstProgress) * 4 * scale;

                // Star sparkle
                ctx.fillStyle = i % 3 === 0 ? '#ffee88' : i % 3 === 1 ? '#ffffff' : '#88ddff';
                ctx.fillRect(sx - size / 2, sy - size / 2, size, size);
                // Cross arms
                ctx.fillRect(sx - size, sy - size / 4, size * 2, size / 2);
                ctx.fillRect(sx - size / 4, sy - size, size / 2, size * 2);
            }
            ctx.globalAlpha = 1;
        }

        // Phase 2 (0.3-0.9): reveal flash
        if (progress > 0.3 && progress < 0.9) {
            const flashProgress = (progress - 0.3) / 0.6;
            const flashAlpha = flashProgress < 0.3 ? flashProgress / 0.3 * 0.4 : (1 - flashProgress) * 0.4;
            ctx.fillStyle = `rgba(255, 255, 200, ${flashAlpha})`;
            const flashSize = TILE * scale * (1 + flashProgress);
            ctx.fillRect(screenX - flashSize / 2, screenY - flashSize / 2, flashSize, flashSize);
        }

        // Phase 3 (0.4-1.0): message text floating up
        if (progress > 0.4) {
            const textProgress = (progress - 0.4) / 0.6;
            const textAlpha = textProgress < 0.3 ? textProgress / 0.3 : Math.max(0, 1 - (textProgress - 0.7) / 0.3);
            const textY = canvasH / 2 - 30 - textProgress * 20;

            ctx.globalAlpha = textAlpha;
            // Text background
            ctx.font = 'bold 14px monospace';
            const textW = ctx.measureText(animMessage).width + 20;
            const boxX = (canvasW - textW) / 2;
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(boxX, textY - 14, textW, 24);
            ctx.strokeStyle = '#ffdd44';
            ctx.lineWidth = 1;
            ctx.strokeRect(boxX, textY - 14, textW, 24);

            // Text
            ctx.fillStyle = '#ffee88';
            ctx.textAlign = 'center';
            ctx.fillText(animMessage, canvasW / 2, textY + 2);
            ctx.textAlign = 'left';
            ctx.globalAlpha = 1;
        }
    }

    function renderHiddenEntrance(ctx, camX, camY, scale, mapId) {
        if (!discovered[mapId]) return;

        for (const key of discovered[mapId]) {
            const [tx, ty] = key.split(',').map(Number);
            const screenX = (tx * TILE - camX) * scale;
            const screenY = (ty * TILE - camY) * scale;
            const s = scale;

            // Draw visible entrance (cave-like opening)
            ctx.fillStyle = '#3a2a1a';
            ctx.fillRect(screenX + 2 * s, screenY + 4 * s, 12 * s, 10 * s);
            // Arch top
            ctx.fillStyle = '#5a4a3a';
            ctx.fillRect(screenX + 3 * s, screenY + 2 * s, 10 * s, 3 * s);
            ctx.fillRect(screenX + 4 * s, screenY + s, 8 * s, 2 * s);
            // Dark interior
            ctx.fillStyle = '#1a0a0a';
            ctx.fillRect(screenX + 4 * s, screenY + 6 * s, 8 * s, 8 * s);
            // Stone border pixels
            ctx.fillStyle = '#7a6a5a';
            ctx.fillRect(screenX + 2 * s, screenY + 4 * s, 2 * s, 10 * s);
            ctx.fillRect(screenX + 12 * s, screenY + 4 * s, 2 * s, 10 * s);
        }
    }

    function renderShimmer(ctx, camX, camY, scale, mapId) {
        // Subtle shimmer hints for undiscovered secret areas
        // This only renders a generic ambient shimmer — actual locations
        // come from backend check, not hardcoded here
        // The shimmer is rendered during the discovery animation phase
        if (animActive) return; // Don't shimmer during discovery
    }

    // --- Collision ---

    function isSecretEntrance(mapId, tileX, tileY) {
        return discovered[mapId] && discovered[mapId].has(`${tileX},${tileY}`);
    }

    // --- Public API ---

    return {
        loadDiscoveredAreas,
        checkForSecretArea,
        discoverArea,
        update,
        isAnimating,
        renderDiscoveryAnimation,
        renderHiddenEntrance,
        renderShimmer,
        isSecretEntrance,
    };
})();
