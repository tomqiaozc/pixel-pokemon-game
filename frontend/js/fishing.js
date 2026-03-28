// fishing.js — Fishing mini-game & surfing overworld system
// Fishing: cast animation -> bobber wait -> QTE reel -> encounter trigger
// Surfing: water tile movement, water encounters, surf mount/dismount

const Fishing = (() => {
    const TILE = Sprites.TILE;

    // ---- Rod tiers ----
    const ROD_TIERS = { old: 'old', good: 'good', super: 'super' };
    let equippedRod = null; // null, 'old', 'good', 'super'

    // ---- Fishing state machine ----
    // States: idle -> casting -> bobber -> bite -> reeling -> done
    let fishState = 'idle';
    let fishTimer = 0;
    let bobberFrame = 0;
    let bobberTimer = 0;
    let biteWindow = 0;      // time remaining to press action during bite
    let reelProgress = 0;    // 0-100, fill by mashing action
    let reelDecay = 0;       // decay timer
    let reelTarget = 100;
    let fishResult = null;    // 'catch' or 'miss'
    let fishResultTimer = 0;
    let fishDir = 0;          // direction player faces while fishing
    let fishTileX = 0;        // water tile being fished
    let fishTileY = 0;
    let pendingFishData = null; // encounter data from backend

    // ---- Surfing state ----
    let surfing = false;
    let surfFrame = 0;
    let surfTimer = 0;

    // ---- Fishing config ----
    const CAST_DURATION = 600;    // ms for cast animation
    const BOBBER_MIN_WAIT = 1500; // min wait before bite
    const BOBBER_MAX_WAIT = 5000; // max wait before bite
    let bobberWaitTarget = 0;
    const BITE_WINDOW = 800;      // ms to react to bite
    const REEL_DECAY_RATE = 12;   // progress lost per second
    const REEL_GAIN = 18;         // progress gained per action press
    const FISH_RESULT_DISPLAY = 1500;

    // ---- Surfing config ----
    const SURF_ENCOUNTER_RATE = 0.15; // 15% per new water tile
    const SURF_ANIM_INTERVAL = 400;

    // ==================== FISHING ====================

    function isFishing() {
        return fishState !== 'idle';
    }

    function canFish() {
        return equippedRod !== null && fishState === 'idle' && !surfing;
    }

    function setRod(tier) {
        if (ROD_TIERS[tier]) equippedRod = tier;
    }

    function getRod() {
        return equippedRod;
    }

    // Try to start fishing — called when player presses action facing water
    function startFishing(playerX, playerY, playerDir) {
        if (!canFish()) return false;

        // Determine the water tile in front of the player
        const dirOffsets = [
            { dx: 0, dy: 1 },  // down
            { dx: 0, dy: -1 }, // up
            { dx: -1, dy: 0 }, // left
            { dx: 1, dy: 0 },  // right
        ];
        const off = dirOffsets[playerDir];
        const tileX = Math.floor((playerX + TILE / 2) / TILE) + off.dx;
        const tileY = Math.floor((playerY + TILE / 2) / TILE) + off.dy;

        if (!GameMap.isWater(tileX, tileY)) return false;

        fishDir = playerDir;
        fishTileX = tileX;
        fishTileY = tileY;
        fishState = 'casting';
        fishTimer = 0;
        fishResult = null;
        fishResultTimer = 0;
        pendingFishData = null;
        reelProgress = 0;

        // Fire backend encounter request early so data is ready by reel time
        const areaId = MapLoader.getCurrentMapId();
        API.fishEncounter(areaId, equippedRod).then(data => {
            if (data && data.pokemon) {
                pendingFishData = data;
            }
        }).catch(() => {});

        return true;
    }

    function cancelFishing() {
        fishState = 'idle';
        fishTimer = 0;
        pendingFishData = null;
    }

    function updateFishing(dt) {
        if (fishState === 'idle') return null;

        fishTimer += dt;

        // Bobber animation
        bobberTimer += dt;
        if (bobberTimer > 300) {
            bobberFrame = (bobberFrame + 1) % 2;
            bobberTimer = 0;
        }

        if (fishState === 'casting') {
            if (fishTimer >= CAST_DURATION) {
                fishState = 'bobber';
                fishTimer = 0;
                bobberWaitTarget = BOBBER_MIN_WAIT + Math.random() * (BOBBER_MAX_WAIT - BOBBER_MIN_WAIT);
            }
        } else if (fishState === 'bobber') {
            // Cancel with Escape or B
            if (Input.isDown('Escape') || Input.isDown('b')) {
                cancelFishing();
                return null;
            }
            if (fishTimer >= bobberWaitTarget) {
                fishState = 'bite';
                fishTimer = 0;
                biteWindow = BITE_WINDOW;
            }
        } else if (fishState === 'bite') {
            biteWindow -= dt;
            if (Input.isActionPressed()) {
                // Player reacted in time — start reeling
                fishState = 'reeling';
                fishTimer = 0;
                reelProgress = 25; // start with some progress for reacting
                reelDecay = 0;
                return null;
            }
            if (biteWindow <= 0) {
                // Missed the bite
                fishResult = 'miss';
                fishResultTimer = 0;
                fishState = 'done';
                return null;
            }
        } else if (fishState === 'reeling') {
            // Mash action to fill reel bar
            reelDecay += dt;
            if (reelDecay > 100) {
                reelProgress = Math.max(0, reelProgress - REEL_DECAY_RATE * (dt / 1000));
                reelDecay = 0;
            }
            if (Input.isActionPressed()) {
                reelProgress = Math.min(reelTarget, reelProgress + REEL_GAIN);
            }
            // Cancel
            if (Input.isDown('Escape')) {
                fishResult = 'miss';
                fishResultTimer = 0;
                fishState = 'done';
                return null;
            }
            // Progress depleted — fish escaped
            if (reelProgress <= 0) {
                fishResult = 'miss';
                fishResultTimer = 0;
                fishState = 'done';
                return null;
            }
            // Reel complete — caught!
            if (reelProgress >= reelTarget) {
                fishResult = 'catch';
                fishResultTimer = 0;
                fishState = 'done';
                return null;
            }
        } else if (fishState === 'done') {
            fishResultTimer += dt;
            if (fishResultTimer >= FISH_RESULT_DISPLAY) {
                const caught = fishResult === 'catch';
                fishState = 'idle';
                if (caught) {
                    return { startBattle: true, fishData: pendingFishData };
                }
                return null;
            }
        }

        return null;
    }

    // Build encounter enemy from fish data (backend or fallback)
    function buildFishEnemy() {
        if (pendingFishData && pendingFishData.pokemon) {
            const p = pendingFishData.pokemon;
            return {
                name: p.name,
                type: (p.types && p.types[0]) || 'Water',
                level: p.level || 10,
                hp: (p.stats && p.stats.hp) || p.hp || 20,
                maxHp: (p.stats && p.stats.hp) || p.max_hp || p.hp || 20,
                speciesId: p.species_id || 0,
                moves: p.moves || null,
                stats: p.stats || null,
            };
        }
        // Local fallback based on rod tier
        const fallbacks = {
            old:   [{ name: 'Magikarp', type: 'Water', level: [5, 10], hp: 15 }],
            good:  [
                { name: 'Magikarp', type: 'Water', level: [10, 15], hp: 18 },
                { name: 'Poliwag',  type: 'Water', level: [10, 15], hp: 20 },
                { name: 'Goldeen',  type: 'Water', level: [10, 15], hp: 18 },
            ],
            super: [
                { name: 'Poliwag',  type: 'Water', level: [15, 25], hp: 25 },
                { name: 'Goldeen',  type: 'Water', level: [15, 25], hp: 22 },
                { name: 'Staryu',   type: 'Water', level: [15, 25], hp: 24 },
                { name: 'Gyarados', type: 'Water', level: [20, 30], hp: 50 },
            ],
        };
        const pool = fallbacks[equippedRod] || fallbacks.old;
        const template = pool[Math.floor(Math.random() * pool.length)];
        const level = template.level[0] + Math.floor(Math.random() * (template.level[1] - template.level[0] + 1));
        const hp = template.hp + Math.floor(level * 1.2);
        return { name: template.name, type: template.type, level, hp, maxHp: hp };
    }

    // ---- Fishing render ----
    function renderFishing(ctx, camX, camY, scale) {
        if (fishState === 'idle') return;

        const dirOffsets = [
            { dx: 0, dy: 1 },  // down
            { dx: 0, dy: -1 }, // up
            { dx: -1, dy: 0 }, // left
            { dx: 1, dy: 0 },  // right
        ];
        const off = dirOffsets[fishDir];
        const bobX = (fishTileX * TILE + TILE / 2 - camX) * scale;
        const bobY = (fishTileY * TILE + TILE / 2 - camY) * scale;

        if (fishState === 'casting') {
            // Line extending animation
            const progress = Math.min(1, fishTimer / CAST_DURATION);
            ctx.strokeStyle = '#a0a0a0';
            ctx.lineWidth = scale;
            ctx.beginPath();
            const startX = bobX - off.dx * TILE * scale * (1 - progress);
            const startY = bobY - off.dy * TILE * scale * (1 - progress);
            ctx.moveTo(startX, startY);
            ctx.lineTo(bobX, bobY);
            ctx.stroke();
        }

        if (fishState === 'bobber' || fishState === 'bite' || fishState === 'reeling') {
            // Fishing line
            ctx.strokeStyle = '#a0a0a0';
            ctx.lineWidth = scale;
            ctx.beginPath();
            ctx.moveTo(bobX - off.dx * TILE * scale, bobY - off.dy * TILE * scale);
            ctx.lineTo(bobX, bobY);
            ctx.stroke();

            // Bobber
            const bobBounce = fishState === 'bite' ? Math.sin(fishTimer * 0.02) * 3 * scale : bobberFrame * scale;
            ctx.fillStyle = '#e04040';
            ctx.beginPath();
            ctx.arc(bobX, bobY - bobBounce, 3 * scale, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#f8f8f8';
            ctx.beginPath();
            ctx.arc(bobX, bobY - bobBounce - 3 * scale, 2 * scale, 0, Math.PI * 2);
            ctx.fill();
        }

        if (fishState === 'bite') {
            // Exclamation mark
            ctx.fillStyle = '#f8d030';
            ctx.font = `bold ${16 * scale}px monospace`;
            ctx.textAlign = 'center';
            ctx.fillText('!', bobX, bobY - 12 * scale);
            ctx.textAlign = 'left';
        }

        if (fishState === 'reeling') {
            // Reel progress bar
            const barW = 60 * scale;
            const barH = 6 * scale;
            const barX = bobX - barW / 2;
            const barY = bobY - 20 * scale;

            ctx.fillStyle = 'rgba(0,0,0,0.5)';
            ctx.fillRect(barX - scale, barY - scale, barW + 2 * scale, barH + 2 * scale);
            ctx.fillStyle = '#404040';
            ctx.fillRect(barX, barY, barW, barH);
            const fillW = (reelProgress / reelTarget) * barW;
            ctx.fillStyle = reelProgress > 70 ? '#48c048' : reelProgress > 30 ? '#f8d030' : '#e04040';
            ctx.fillRect(barX, barY, fillW, barH);

            // "Mash Z!" hint
            ctx.fillStyle = '#f8f8f8';
            ctx.font = `bold ${8 * scale}px monospace`;
            ctx.textAlign = 'center';
            ctx.fillText('Mash Z!', bobX, barY - 2 * scale);
            ctx.textAlign = 'left';
        }
    }

    // Render result overlay
    function renderFishResult(ctx, canvasW, canvasH) {
        if (fishState !== 'done') return;

        const alpha = Math.min(1, fishResultTimer / 300);
        ctx.globalAlpha = alpha;
        ctx.fillStyle = 'rgba(0,0,0,0.4)';
        ctx.fillRect(0, canvasH / 2 - 30, canvasW, 60);

        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        if (fishResult === 'catch') {
            ctx.fillStyle = '#48c048';
            ctx.fillText('Hooked a Pokemon!', canvasW / 2, canvasH / 2 + 6);
        } else {
            ctx.fillStyle = '#e04040';
            ctx.fillText('It got away...', canvasW / 2, canvasH / 2 + 6);
        }
        ctx.textAlign = 'left';
        ctx.globalAlpha = 1;
    }

    // ==================== SURFING ====================

    function isSurfing() {
        return surfing;
    }

    // Try to mount surf — called when player presses action facing water and has Surf
    function tryStartSurf(playerX, playerY, playerDir) {
        if (surfing || isFishing()) return false;

        // Check if player has a water-type Pokemon that can surf
        const party = Game.player.party;
        const canSurf = party.some(p => p.type === 'Water');
        if (!canSurf) return false;

        const dirOffsets = [
            { dx: 0, dy: 1 },  // down
            { dx: 0, dy: -1 }, // up
            { dx: -1, dy: 0 }, // left
            { dx: 1, dy: 0 },  // right
        ];
        const off = dirOffsets[playerDir];
        const tileX = Math.floor((playerX + TILE / 2) / TILE) + off.dx;
        const tileY = Math.floor((playerY + TILE / 2) / TILE) + off.dy;

        if (!GameMap.isWater(tileX, tileY)) return false;

        // Move player onto water tile and start surfing
        surfing = true;
        surfFrame = 0;
        surfTimer = 0;
        return { tileX, tileY };
    }

    // Check if player should dismount (moved onto a non-water tile)
    function checkDismount(playerX, playerY) {
        if (!surfing) return false;
        const tileX = Math.floor((playerX + TILE / 2) / TILE);
        const tileY = Math.floor((playerY + TILE / 2) / TILE);
        if (!GameMap.isWater(tileX, tileY)) {
            surfing = false;
            surfFrame = 0;
            return true;
        }
        return false;
    }

    function updateSurf(dt) {
        if (!surfing) return;
        surfTimer += dt;
        if (surfTimer > SURF_ANIM_INTERVAL) {
            surfFrame = (surfFrame + 1) % 2;
            surfTimer = 0;
        }
    }

    function getSurfFrame() {
        return surfFrame;
    }

    // Check for water encounter while surfing (called per new tile)
    function checkWaterEncounter() {
        if (!surfing) return false;
        return Math.random() < SURF_ENCOUNTER_RATE;
    }

    // ---- Init: check inventory for rods ----
    function init() {
        // Try to detect rods from backend inventory
        API.getInventory().then(data => {
            if (data && Array.isArray(data)) {
                for (const item of data) {
                    const name = (item.name || '').toLowerCase();
                    if (name.includes('super rod')) { equippedRod = 'super'; return; }
                    if (name.includes('good rod'))  { equippedRod = 'good'; return; }
                    if (name.includes('old rod'))   { equippedRod = 'old'; return; }
                }
            }
        }).catch(() => {});
    }

    return {
        // Fishing
        isFishing, canFish, startFishing, cancelFishing, updateFishing,
        buildFishEnemy, renderFishing, renderFishResult,
        setRod, getRod,
        // Surfing
        isSurfing, tryStartSurf, checkDismount, updateSurf, getSurfFrame,
        checkWaterEncounter,
        // Init
        init,
        // Expose rod tiers
        ROD_TIERS,
    };
})();
