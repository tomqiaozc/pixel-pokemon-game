// cave.js — Cave rendering, darkness mechanics, and Flash illumination

const Cave = (() => {
    const TILE = Sprites.TILE;

    // Cave state per map
    let caveStates = {}; // mapId -> { isDark, isLit, visibilityRadius }
    const DEFAULT_DARK_RADIUS = 2;   // tiles visible without Flash
    const LIT_RADIUS = 10;           // tiles visible with Flash

    // Flash animation state
    let flashAnimActive = false;
    let flashAnimTimer = 0;
    let flashAnimStartRadius = DEFAULT_DARK_RADIUS;
    let flashAnimEndRadius = LIT_RADIUS;
    const FLASH_ANIM_DURATION = 800; // ms
    const FLASH_ANIM_FRAMES = 10;

    // --- API Wiring ---

    function loadCaveState(mapId) {
        API.getCaveState(mapId).then(data => {
            if (data) {
                caveStates[mapId] = {
                    isDark: data.is_dark !== undefined ? data.is_dark : true,
                    isLit: data.is_lit || false,
                    visibilityRadius: data.visibility_radius || DEFAULT_DARK_RADIUS,
                };
            }
        }).catch(err => console.error('Failed to load cave state:', err));
    }

    function enterCave(mapId) {
        // Set default state immediately for responsive UI
        if (!caveStates[mapId]) {
            caveStates[mapId] = {
                isDark: true,
                isLit: false,
                visibilityRadius: DEFAULT_DARK_RADIUS,
            };
        }
        // Fetch actual state from backend
        loadCaveState(mapId);
    }

    function exitCave(mapId) {
        // Clear cave state when leaving
        delete caveStates[mapId];
    }

    function useFlash(mapId, pokemonIndex) {
        API.useFlash(mapId, pokemonIndex).then(data => {
            if (data && data.success) {
                const state = caveStates[mapId];
                if (state) {
                    flashAnimStartRadius = state.visibilityRadius;
                    flashAnimEndRadius = data.visibility_radius || LIT_RADIUS;
                    state.isLit = true;
                    state.visibilityRadius = flashAnimEndRadius;
                    startFlashAnimation();
                }
            }
        }).catch(err => console.error('Failed to use Flash:', err));
    }

    // --- Flash Animation ---

    function startFlashAnimation() {
        flashAnimActive = true;
        flashAnimTimer = 0;
    }

    function update(dt) {
        if (flashAnimActive) {
            flashAnimTimer += dt;
            if (flashAnimTimer >= FLASH_ANIM_DURATION) {
                flashAnimActive = false;
            }
        }
    }

    function isFlashAnimating() {
        return flashAnimActive;
    }

    // --- State Queries ---

    function isDarkCave(mapId) {
        const state = caveStates[mapId];
        return state ? state.isDark && !state.isLit : false;
    }

    function isInCave(mapId) {
        return !!caveStates[mapId];
    }

    function getVisibilityRadius(mapId) {
        const state = caveStates[mapId];
        if (!state) return LIT_RADIUS;

        // During flash animation, interpolate radius
        if (flashAnimActive) {
            const progress = Math.min(1, flashAnimTimer / FLASH_ANIM_DURATION);
            // Ease-out curve for smooth expansion
            const eased = 1 - Math.pow(1 - progress, 3);
            return flashAnimStartRadius + (flashAnimEndRadius - flashAnimStartRadius) * eased;
        }

        return state.visibilityRadius;
    }

    // --- Darkness Rendering ---

    function renderDarkness(ctx, playerScreenX, playerScreenY, visibilityRadius, canvasW, canvasH, scale) {
        const radiusPx = visibilityRadius * TILE * scale;

        ctx.save();

        // Draw full dark overlay
        ctx.fillStyle = 'rgba(0, 0, 0, 0.95)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Punch a radial gradient hole centered on the player
        ctx.globalCompositeOperation = 'destination-out';
        const gradient = ctx.createRadialGradient(
            playerScreenX, playerScreenY, 0,
            playerScreenX, playerScreenY, radiusPx
        );
        gradient.addColorStop(0, 'rgba(0, 0, 0, 1)');
        gradient.addColorStop(0.6, 'rgba(0, 0, 0, 0.8)');
        gradient.addColorStop(0.85, 'rgba(0, 0, 0, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvasW, canvasH);

        ctx.restore();
    }

    function renderFlashAnimation(ctx, playerScreenX, playerScreenY, canvasW, canvasH, scale) {
        if (!flashAnimActive) return;

        const progress = Math.min(1, flashAnimTimer / FLASH_ANIM_DURATION);

        // White flash overlay that fades out
        if (progress < 0.3) {
            const flashAlpha = (1 - progress / 0.3) * 0.6;
            ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }

        // Expanding ring effect
        const frame = Math.floor(progress * FLASH_ANIM_FRAMES);
        if (frame < FLASH_ANIM_FRAMES) {
            const ringRadius = (flashAnimStartRadius + (flashAnimEndRadius - flashAnimStartRadius) * progress) * TILE * scale;
            const ringAlpha = Math.max(0, 0.5 * (1 - progress));

            ctx.save();
            ctx.globalAlpha = ringAlpha;
            ctx.strokeStyle = '#ffffaa';
            ctx.lineWidth = 3 * scale;
            ctx.beginPath();
            ctx.arc(playerScreenX, playerScreenY, ringRadius, 0, Math.PI * 2);
            ctx.stroke();
            ctx.restore();
        }
    }

    // --- Cave Tile Rendering ---

    function renderCaveTiles(ctx, camX, camY, scale, mapId) {
        // Cave-specific overlays (stalagmites, dripping water) if needed
        // The base tiles are handled by the normal renderer via map data
        // This function adds cave ambiance effects
        if (!caveStates[mapId]) return;

        // Subtle ambient particles (dust motes) in lit areas
        const time = performance.now();
        const particleCount = 5;
        for (let i = 0; i < particleCount; i++) {
            const px = Math.sin(time * 0.0003 + i * 1.7) * 80 + ctx.canvas.width / 2;
            const py = Math.cos(time * 0.0004 + i * 2.3) * 60 + ctx.canvas.height / 2;
            const alpha = Math.sin(time * 0.001 + i) * 0.15 + 0.15;
            ctx.fillStyle = `rgba(200, 200, 180, ${Math.max(0, alpha)})`;
            ctx.fillRect(px, py, 2 * scale, 2 * scale);
        }
    }

    // --- Cave Floor Transition ---

    function transitionCaveFloor(fromMapId, ladderX, ladderY) {
        API.caveTransition(fromMapId, ladderX, ladderY).then(data => {
            if (data && data.target_map_id) {
                // Trigger map transition via MapLoader
                MapLoader.transitionTo(data.target_map_id, data.spawn_x, data.spawn_y, 0);
                // Set up darkness for new floor
                if (data.is_dark) {
                    caveStates[data.target_map_id] = {
                        isDark: true,
                        isLit: false,
                        visibilityRadius: DEFAULT_DARK_RADIUS,
                    };
                }
            }
        }).catch(err => console.error('Failed to transition cave floor:', err));
    }

    // --- Public API ---

    return {
        enterCave,
        exitCave,
        loadCaveState,
        useFlash,
        update,
        isFlashAnimating,
        isDarkCave,
        isInCave,
        getVisibilityRadius,
        renderDarkness,
        renderFlashAnimation,
        renderCaveTiles,
        transitionCaveFloor,
    };
})();
