// encounters.js — Wild Pokemon encounter system

const Encounters = (() => {
    const TILE = Sprites.TILE;
    const ENCOUNTER_RATE = 0.1; // 10% chance per step in tall grass
    const STEP_THRESHOLD = 8; // pixels moved before counting as a step

    // Encounter state
    let stepAccumulator = 0;
    let lastTileX = -1;
    let lastTileY = -1;
    let encounterCooldown = 0; // Prevent back-to-back encounters

    // Transition animation
    let transitioning = false;
    let transitionTimer = 0;
    let transitionPhase = 0; // 0=flash, 1=bars
    let pendingEnemy = null;

    // Visual effects
    let grassRustles = []; // particle effects for stepping in grass
    let exclamation = null; // "!" popup

    // Wild Pokemon pool
    const WILD_POKEMON = [
        { name: 'Pidgey',    type: 'Flying',  level: [2, 5], hp: 14, color: '#c0a870' },
        { name: 'Rattata',   type: 'Normal',  level: [2, 4], hp: 12, color: '#a060c0' },
        { name: 'Caterpie',  type: 'Bug',     level: [2, 4], hp: 11, color: '#68b838' },
        { name: 'Weedle',    type: 'Bug',     level: [2, 4], hp: 11, color: '#b08830' },
        { name: 'Oddish',    type: 'Grass',   level: [3, 5], hp: 15, color: '#4878c8' },
    ];

    function reset() {
        stepAccumulator = 0;
        lastTileX = -1;
        lastTileY = -1;
        encounterCooldown = 0;
        transitioning = false;
        transitionTimer = 0;
        pendingEnemy = null;
        grassRustles = [];
        exclamation = null;
    }

    function update(dt, player) {
        encounterCooldown = Math.max(0, encounterCooldown - dt);

        // Update grass rustle particles
        for (const gr of grassRustles) {
            gr.age += dt;
            gr.y -= dt * 0.02;
            gr.x += gr.vx * dt * 0.01;
        }
        grassRustles = grassRustles.filter(g => g.age < 400);

        // Update exclamation mark
        if (exclamation) {
            exclamation.age += dt;
            if (exclamation.age > 600) exclamation = null;
        }

        // Handle transition animation
        if (transitioning) {
            transitionTimer += dt;
            if (transitionPhase === 0) {
                // Screen flash phase (3 quick flashes)
                if (transitionTimer > 400) {
                    transitionPhase = 1;
                    transitionTimer = 0;
                }
            } else if (transitionPhase === 1) {
                // Black bars closing in
                if (transitionTimer > 500) {
                    // Start battle
                    transitioning = false;
                    return { startBattle: true, enemy: pendingEnemy };
                }
            }
            return { startBattle: false };
        }

        // Check if player moved to a new tile
        if (player.moving) {
            const tileX = Math.floor((player.x + TILE / 2) / TILE);
            const tileY = Math.floor((player.y + TILE / 2) / TILE);

            if (tileX !== lastTileX || tileY !== lastTileY) {
                lastTileX = tileX;
                lastTileY = tileY;

                // Check if we're in tall grass
                if (GameMap.isTallGrass(tileX, tileY)) {
                    // Spawn grass rustle particles
                    spawnGrassRustle(player.x + TILE / 2, player.y + TILE);

                    // Encounter check
                    if (encounterCooldown <= 0 && Math.random() < ENCOUNTER_RATE) {
                        triggerEncounter(player);
                    }
                }
            }
        }

        return { startBattle: false };
    }

    function spawnGrassRustle(wx, wy) {
        for (let i = 0; i < 4; i++) {
            grassRustles.push({
                wx: wx + (Math.random() - 0.5) * 12,
                wy: wy + (Math.random() - 0.5) * 6,
                x: 0,
                y: 0,
                vx: (Math.random() - 0.5) * 2,
                age: 0,
            });
        }
    }

    function triggerEncounter(player) {
        // Pick a random wild Pokemon
        const template = WILD_POKEMON[Math.floor(Math.random() * WILD_POKEMON.length)];
        const level = template.level[0] + Math.floor(Math.random() * (template.level[1] - template.level[0] + 1));
        const hp = template.hp + Math.floor(level * 1.5);

        pendingEnemy = {
            name: template.name,
            type: template.type,
            level: level,
            hp: hp,
            maxHp: hp,
        };

        // Show exclamation mark
        exclamation = {
            wx: player.x + TILE / 2,
            wy: player.y - 8,
            age: 0,
        };

        // Start transition after brief pause
        encounterCooldown = 3000; // 3s cooldown after encounter
        transitioning = true;
        transitionTimer = 0;
        transitionPhase = 0;
    }

    // Render overlay effects (called during overworld render)
    function renderOverlay(ctx, camX, camY, scale, canvasW, canvasH) {
        // Grass rustle particles
        ctx.fillStyle = '#90d848';
        for (const gr of grassRustles) {
            const alpha = 1 - gr.age / 400;
            ctx.globalAlpha = alpha;
            const sx = (gr.wx + gr.x - camX) * scale;
            const sy = (gr.wy + gr.y - camY) * scale;
            ctx.fillRect(sx - 2, sy - 2, 4, 4);
            ctx.fillRect(sx, sy - 4, 2, 2);
        }
        ctx.globalAlpha = 1;

        // Exclamation mark
        if (exclamation) {
            const sx = (exclamation.wx - camX) * scale;
            const sy = (exclamation.wy - camY) * scale;
            const bounce = Math.sin(exclamation.age * 0.015) * 4;

            ctx.fillStyle = '#f8f8f8';
            ctx.strokeStyle = '#202020';
            ctx.lineWidth = 2;
            ctx.font = 'bold 24px monospace';
            ctx.textAlign = 'center';
            ctx.strokeText('!', sx, sy + bounce);
            ctx.fillText('!', sx, sy + bounce);
            ctx.textAlign = 'left';
        }

        // Transition effects
        if (transitioning) {
            if (transitionPhase === 0) {
                // Quick screen flashes
                const flashCount = Math.floor(transitionTimer / 130);
                if (flashCount % 2 === 0) {
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                    ctx.fillRect(0, 0, canvasW, canvasH);
                }
            } else if (transitionPhase === 1) {
                // Black bars sliding in from top and bottom
                const progress = Math.min(1, transitionTimer / 500);
                const barH = canvasH * 0.5 * progress;
                ctx.fillStyle = '#000000';
                ctx.fillRect(0, 0, canvasW, barH);
                ctx.fillRect(0, canvasH - barH, canvasW, barH);
            }
        }
    }

    return { reset, update, renderOverlay, transitioning: () => transitioning };
})();
