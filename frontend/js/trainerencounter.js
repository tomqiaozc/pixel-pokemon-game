// trainerencounter.js — Trainer line-of-sight encounter system

const TrainerEncounter = (() => {
    const TILE = Sprites.TILE;

    // Tracked trainers on the current map
    let activeTrainers = [];
    let defeatedTrainers = new Set(); // "mapId:trainerName" keys

    // Encounter state
    let encounterPhase = 'idle'; // idle, exclamation, walk, dialogue
    let encounterTimer = 0;
    let encounterTrainer = null;
    let exclamationPos = { x: 0, y: 0 };

    // Trainer walk animation
    let walkStartX = 0;
    let walkStartY = 0;
    let walkTargetX = 0;
    let walkTargetY = 0;
    let walkProgress = 0;

    const EXCLAMATION_DURATION = 600;
    const WALK_SPEED = 0.003; // progress per ms

    // Load trainers for current map
    function loadTrainers(mapId, trainers) {
        activeTrainers = trainers.map(t => ({
            ...t,
            defeated: defeatedTrainers.has(`${mapId}:${t.name}`),
            currentX: t.x,
            currentY: t.y,
            animFrame: 0,
            animTimer: 0,
        }));
    }

    // Check if player entered any trainer's line of sight
    function checkLineOfSight(playerX, playerY) {
        if (encounterPhase !== 'idle') return null;

        const playerTileX = Math.floor((playerX + TILE / 2) / TILE);
        const playerTileY = Math.floor((playerY + TILE / 2) / TILE);

        for (const trainer of activeTrainers) {
            if (trainer.defeated) continue;

            const range = trainer.sightRange || 3;
            const dir = trainer.dir || 0;

            let inSight = false;

            // Check direction
            if (dir === 0) { // down
                inSight = playerTileX === trainer.x &&
                          playerTileY > trainer.y &&
                          playerTileY <= trainer.y + range;
            } else if (dir === 1) { // up
                inSight = playerTileX === trainer.x &&
                          playerTileY < trainer.y &&
                          playerTileY >= trainer.y - range;
            } else if (dir === 2) { // left
                inSight = playerTileY === trainer.y &&
                          playerTileX < trainer.x &&
                          playerTileX >= trainer.x - range;
            } else if (dir === 3) { // right
                inSight = playerTileY === trainer.y &&
                          playerTileX > trainer.x &&
                          playerTileX <= trainer.x + range;
            }

            if (inSight) {
                // Check for obstacles in line of sight
                let blocked = false;
                const dx = dir === 3 ? 1 : dir === 2 ? -1 : 0;
                const dy = dir === 0 ? 1 : dir === 1 ? -1 : 0;
                let checkX = trainer.x + dx;
                let checkY = trainer.y + dy;

                while (checkX !== playerTileX || checkY !== playerTileY) {
                    if (GameMap.isSolid(checkX, checkY)) {
                        blocked = true;
                        break;
                    }
                    checkX += dx;
                    checkY += dy;
                }

                if (!blocked) {
                    startEncounter(trainer, playerTileX, playerTileY);
                    return trainer;
                }
            }
        }

        return null;
    }

    function startEncounter(trainer, playerTileX, playerTileY) {
        encounterTrainer = trainer;
        encounterPhase = 'exclamation';
        encounterTimer = 0;
        exclamationPos = {
            x: trainer.x * TILE + TILE / 2,
            y: trainer.y * TILE - 6,
        };

        // Calculate walk target (1 tile from player)
        const dx = playerTileX - trainer.x;
        const dy = playerTileY - trainer.y;
        const dist = Math.abs(dx) + Math.abs(dy);

        if (dist > 1) {
            walkStartX = trainer.currentX;
            walkStartY = trainer.currentY;
            // Walk to 1 tile away from player
            walkTargetX = playerTileX - Math.sign(dx);
            walkTargetY = playerTileY - Math.sign(dy);
        } else {
            walkStartX = trainer.currentX;
            walkStartY = trainer.currentY;
            walkTargetX = trainer.currentX;
            walkTargetY = trainer.currentY;
        }

        walkProgress = 0;
    }

    function update(dt) {
        // Update idle animations for all trainers
        for (const trainer of activeTrainers) {
            trainer.animTimer += dt;
            if (trainer.animTimer >= 500) {
                trainer.animFrame = (trainer.animFrame + 1) % 2;
                trainer.animTimer = 0;
            }
        }

        if (encounterPhase === 'idle') return { encountering: false };

        encounterTimer += dt;

        if (encounterPhase === 'exclamation') {
            if (encounterTimer >= EXCLAMATION_DURATION) {
                encounterPhase = 'walk';
                encounterTimer = 0;
            }
            return { encountering: true, lockPlayer: true };
        }

        if (encounterPhase === 'walk') {
            walkProgress += WALK_SPEED * dt;

            // Update trainer position
            encounterTrainer.currentX = walkStartX + (walkTargetX - walkStartX) * Math.min(1, walkProgress);
            encounterTrainer.currentY = walkStartY + (walkTargetY - walkStartY) * Math.min(1, walkProgress);

            // Walk animation
            encounterTrainer.animFrame = Math.floor(walkProgress * 6) % 2 + 1;

            if (walkProgress >= 1) {
                encounterTrainer.currentX = walkTargetX;
                encounterTrainer.currentY = walkTargetY;
                encounterPhase = 'dialogue';
                encounterTimer = 0;
            }
            return { encountering: true, lockPlayer: true };
        }

        if (encounterPhase === 'dialogue') {
            if (!Dialogue.isActive() && encounterTimer > 100) {
                // Start pre-battle dialogue
                const dialogue = encounterTrainer.dialogue || [`${encounterTrainer.name} wants to battle!`];
                Dialogue.start(encounterTrainer.name, dialogue, {
                    onComplete: () => {
                        encounterPhase = 'idle';
                    },
                });
            }
            if (Dialogue.isActive()) {
                Dialogue.update(dt);
            }
            if (encounterPhase === 'idle') {
                // Dialogue finished, start battle
                return {
                    encountering: false,
                    startBattle: true,
                    trainer: encounterTrainer,
                };
            }
            return { encountering: true, lockPlayer: true };
        }

        return { encountering: false };
    }

    // Mark a trainer as defeated
    function defeatTrainer(mapId, trainerName) {
        defeatedTrainers.add(`${mapId}:${trainerName}`);
        for (const trainer of activeTrainers) {
            if (trainer.name === trainerName) {
                trainer.defeated = true;
            }
        }
    }

    // Render trainer sprites on the overworld
    function render(ctx, camX, camY, scale) {
        for (const trainer of activeTrainers) {
            const screenX = (trainer.currentX * TILE - camX) * scale;
            const screenY = (trainer.currentY * TILE - camY) * scale;

            // Dim defeated trainers
            if (trainer.defeated) {
                ctx.globalAlpha = 0.5;
            }

            drawOverworldTrainer(ctx, screenX, screenY, scale, trainer);

            ctx.globalAlpha = 1;
        }

        // Exclamation mark during encounter
        if (encounterPhase === 'exclamation') {
            const exX = (exclamationPos.x - camX) * scale;
            const exY = (exclamationPos.y - camY) * scale;
            const bounce = Math.sin(encounterTimer * 0.02) * 3;

            ctx.fillStyle = '#f8d830';
            ctx.font = `bold ${16 * scale}px monospace`;
            ctx.textAlign = 'center';
            ctx.fillText('!', exX, exY + bounce);
            ctx.textAlign = 'left';
        }
    }

    function drawOverworldTrainer(ctx, x, y, scale, trainer) {
        const s = scale;
        const typeColors = {
            Normal: '#808080', Rock: '#a08060', Ground: '#c0a050',
            Bug: '#88a020', Fire: '#e06030', Water: '#4080c0',
            Grass: '#408040', Flying: '#9080c0', Poison: '#8040a0',
            Electric: '#c0a020',
        };
        const color = typeColors[trainer.type] || '#606060';

        // Simple trainer sprite (similar to NPC sprites)
        // Head
        ctx.fillStyle = '#f8c098';
        ctx.fillRect(x + 4 * s, y + 2 * s, 8 * s, 5 * s);
        // Hair
        ctx.fillStyle = '#403020';
        ctx.fillRect(x + 4 * s, y + s, 8 * s, 2 * s);
        // Eyes
        ctx.fillStyle = '#202020';
        if (trainer.dir === 0) { // down
            ctx.fillRect(x + 5 * s, y + 4 * s, 2 * s, s);
            ctx.fillRect(x + 9 * s, y + 4 * s, 2 * s, s);
        } else if (trainer.dir === 1) { // up - no eyes visible
        } else if (trainer.dir === 2) { // left
            ctx.fillRect(x + 5 * s, y + 4 * s, 2 * s, s);
        } else { // right
            ctx.fillRect(x + 9 * s, y + 4 * s, 2 * s, s);
        }
        // Body
        ctx.fillStyle = color;
        ctx.fillRect(x + 3 * s, y + 7 * s, 10 * s, 6 * s);
        // Legs
        ctx.fillStyle = '#404040';
        const frame = trainer.animFrame || 0;
        if (frame === 0) {
            ctx.fillRect(x + 4 * s, y + 13 * s, 3 * s, 3 * s);
            ctx.fillRect(x + 9 * s, y + 13 * s, 3 * s, 3 * s);
        } else {
            ctx.fillRect(x + 3 * s, y + 13 * s, 3 * s, 3 * s);
            ctx.fillRect(x + 10 * s, y + 13 * s, 3 * s, 3 * s);
        }
    }

    function getActiveTrainers() { return activeTrainers; }
    function isEncountering() { return encounterPhase !== 'idle'; }

    return {
        loadTrainers,
        checkLineOfSight,
        update,
        defeatTrainer,
        render,
        getActiveTrainers,
        isEncountering,
    };
})();
