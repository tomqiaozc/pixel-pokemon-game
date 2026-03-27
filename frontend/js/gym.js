// gym.js — Gym interior layouts and gym system

const Gym = (() => {
    const TILE = Sprites.TILE;

    // Tile types for gym interiors
    const T = {
        FLOOR:      0,
        WALL:       1,
        STATUE:     2,
        PLATFORM:   3,  // Gym leader platform
        PUZZLE:     4,  // Puzzle floor tile
        BARRIER:    5,  // Blocking barrier
        DOOR:       6,
        RUG:        7,
    };

    // Gym definitions
    const gyms = {
        pewter: {
            name: 'Pewter City Gym',
            leader: { name: 'Brock', type: 'Rock', title: 'The Rock-Solid Pokemon Trainer!' },
            badge: { name: 'Boulder Badge', index: 0 },
            interior: buildPewterGym(),
            width: 13,
            height: 15,
            leaderPos: { x: 6, y: 2 },
            trainers: [
                { x: 4, y: 8, name: 'Camper Liam', type: 'Rock', dir: 3, pokemon: [
                    { name: 'Geodude', level: 7, hp: 22, maxHp: 22, type: 'Rock' },
                ] },
            ],
        },
        viridian: {
            name: 'Viridian City Gym',
            leader: { name: 'Giovanni', type: 'Ground', title: 'The Self-Proclaimed Strongest Trainer!' },
            badge: { name: 'Earth Badge', index: 7 },
            interior: buildViridianGym(),
            width: 15,
            height: 17,
            leaderPos: { x: 7, y: 2 },
            trainers: [
                { x: 3, y: 6, name: 'Cooltrainer Samuel', type: 'Ground', dir: 3, pokemon: [
                    { name: 'Sandslash', level: 40, hp: 90, maxHp: 90, type: 'Ground' },
                ] },
                { x: 11, y: 10, name: 'Cooltrainer Yuji', type: 'Ground', dir: 2, pokemon: [
                    { name: 'Dugtrio', level: 38, hp: 80, maxHp: 80, type: 'Ground' },
                ] },
            ],
        },
    };

    function buildPewterGym() {
        const W = 13, H = 15;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.FLOOR);
            m.push(row);
        }

        // Walls
        for (let x = 0; x < W; x++) { m[0][x] = T.WALL; m[1][x] = T.WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.WALL; m[y][W - 1] = T.WALL; }

        // Gym leader platform (top center)
        for (let x = 4; x <= 8; x++) {
            m[2][x] = T.PLATFORM;
            m[3][x] = T.PLATFORM;
        }

        // Statues at entrance
        m[12][2] = T.STATUE;
        m[12][10] = T.STATUE;

        // Puzzle floor - rock pattern
        for (let x = 2; x <= 10; x += 2) {
            m[6][x] = T.PUZZLE;
            m[10][x] = T.PUZZLE;
        }

        // Barriers creating path
        for (let x = 2; x <= 4; x++) m[5][x] = T.BARRIER;
        for (let x = 8; x <= 10; x++) m[5][x] = T.BARRIER;
        for (let x = 3; x <= 5; x++) m[9][x] = T.BARRIER;
        for (let x = 7; x <= 9; x++) m[9][x] = T.BARRIER;

        // Door
        m[H - 1][6] = T.DOOR;

        // Rug at entrance
        for (let x = 5; x <= 7; x++) {
            m[H - 2][x] = T.RUG;
            m[H - 3][x] = T.RUG;
        }

        return m;
    }

    function buildViridianGym() {
        const W = 15, H = 17;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.FLOOR);
            m.push(row);
        }

        // Walls
        for (let x = 0; x < W; x++) { m[0][x] = T.WALL; m[1][x] = T.WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.WALL; m[y][W - 1] = T.WALL; }

        // Gym leader platform (larger)
        for (let x = 5; x <= 9; x++) {
            m[2][x] = T.PLATFORM;
            m[3][x] = T.PLATFORM;
            m[4][x] = T.PLATFORM;
        }

        // Statues flanking platform
        m[3][3] = T.STATUE;
        m[3][11] = T.STATUE;

        // Maze-like puzzle layout with barriers
        // Row 6 barriers
        for (let x = 1; x <= 5; x++) m[6][x] = T.BARRIER;
        for (let x = 9; x <= 13; x++) m[6][x] = T.BARRIER;

        // Row 8 barriers
        for (let x = 3; x <= 7; x++) m[8][x] = T.BARRIER;
        for (let x = 11; x <= 13; x++) m[8][x] = T.BARRIER;

        // Row 10 barriers
        for (let x = 1; x <= 3; x++) m[10][x] = T.BARRIER;
        for (let x = 7; x <= 11; x++) m[10][x] = T.BARRIER;

        // Row 12 barriers
        for (let x = 3; x <= 5; x++) m[12][x] = T.BARRIER;
        for (let x = 9; x <= 11; x++) m[12][x] = T.BARRIER;

        // Puzzle floor tiles
        m[7][7] = T.PUZZLE;
        m[9][3] = T.PUZZLE;
        m[9][11] = T.PUZZLE;
        m[11][7] = T.PUZZLE;
        m[13][5] = T.PUZZLE;
        m[13][9] = T.PUZZLE;

        // Statues at entrance
        m[14][3] = T.STATUE;
        m[14][11] = T.STATUE;

        // Door
        m[H - 1][7] = T.DOOR;

        // Rug
        for (let x = 6; x <= 8; x++) {
            m[H - 2][x] = T.RUG;
            m[H - 3][x] = T.RUG;
        }

        return m;
    }

    let activeGym = null;
    let playerX = 0;
    let playerY = 0;
    let playerDir = 1;
    let playerAnimFrame = 0;
    let playerAnimTimer = 0;
    let transitionAlpha = 0;
    let transitionDir = 0;

    function enter(gymId) {
        const gym = gyms[gymId];
        if (!gym) return;
        activeGym = gym;
        playerX = Math.floor(gym.width / 2);
        playerY = gym.height - 2;
        playerDir = 1;
        playerAnimFrame = 0;
        transitionAlpha = 1;
        transitionDir = -1;
    }

    function exit() {
        transitionDir = 1;
    }

    function isActive() { return activeGym !== null; }
    function getActiveGym() { return activeGym; }

    function update(dt) {
        if (!activeGym) return { exited: false };

        // Handle transition
        if (transitionDir !== 0) {
            transitionAlpha += transitionDir * dt * 0.003;
            if (transitionAlpha <= 0) { transitionAlpha = 0; transitionDir = 0; }
            if (transitionAlpha >= 1 && transitionDir > 0) {
                const gym = activeGym;
                activeGym = null;
                return { exited: true, gym };
            }
            return { exited: false };
        }

        // Dialogue check
        if (Dialogue.isActive()) {
            Dialogue.update(dt);
            return { exited: false };
        }

        // NPC/Leader interaction
        if (Input.isActionPressed()) {
            const facingX = playerX + (playerDir === 3 ? 1 : playerDir === 2 ? -1 : 0);
            const facingY = playerY + (playerDir === 0 ? 1 : playerDir === 1 ? -1 : 0);

            // Check gym leader
            if (facingX === activeGym.leaderPos.x && facingY === activeGym.leaderPos.y) {
                return {
                    exited: false,
                    battleLeader: true,
                    leader: activeGym.leader,
                    badge: activeGym.badge,
                };
            }

            // Check trainers
            for (const trainer of activeGym.trainers) {
                if (facingX === trainer.x && facingY === trainer.y) {
                    return {
                        exited: false,
                        battleTrainer: true,
                        trainer,
                    };
                }
            }
        }

        // Movement
        const movement = Input.getMovement();
        const MOVE_SPEED = 1.5;

        if (movement) {
            playerDir = movement.dir;
            let newX = playerX + movement.dx * MOVE_SPEED * dt * 0.06;
            let newY = playerY + movement.dy * MOVE_SPEED * dt * 0.06;

            const tileX = Math.floor(newX + 0.5);
            const tileY = Math.floor(newY + 0.5);

            // Door exit
            if (tileY >= activeGym.height - 1 && Math.abs(tileX - Math.floor(activeGym.width / 2)) < 1) {
                exit();
                return { exited: false };
            }

            // Collision check
            if (tileX >= 1 && tileX < activeGym.width - 1 && tileY >= 2 && tileY < activeGym.height - 1) {
                const tile = activeGym.interior[tileY][tileX];
                if (tile !== T.WALL && tile !== T.STATUE && tile !== T.BARRIER && tile !== T.PLATFORM) {
                    playerX = newX;
                    playerY = newY;
                }
            }

            playerAnimTimer += dt;
            if (playerAnimTimer >= 150) {
                playerAnimFrame = (playerAnimFrame % 2) + 1;
                playerAnimTimer = 0;
            }
        } else {
            playerAnimFrame = 0;
        }

        return { exited: false };
    }

    function render(ctx, canvasW, canvasH) {
        if (!activeGym) return;

        const scale = 3;
        const offsetX = (canvasW - activeGym.width * TILE * scale) / 2;
        const offsetY = (canvasH - activeGym.height * TILE * scale) / 2;

        // Draw tiles
        for (let y = 0; y < activeGym.height; y++) {
            for (let x = 0; x < activeGym.width; x++) {
                const tile = activeGym.interior[y][x];
                const sx = offsetX + x * TILE * scale;
                const sy = offsetY + y * TILE * scale;
                drawGymTile(ctx, tile, sx, sy, TILE * scale, activeGym.leader.type);
            }
        }

        // Draw trainers
        for (const trainer of activeGym.trainers) {
            const tx = offsetX + trainer.x * TILE * scale;
            const ty = offsetY + trainer.y * TILE * scale;
            drawTrainerSprite(ctx, tx, ty, scale, trainer.dir || 0, trainer.type);
        }

        // Draw gym leader
        const lx = offsetX + activeGym.leaderPos.x * TILE * scale;
        const ly = offsetY + activeGym.leaderPos.y * TILE * scale;
        drawLeaderSprite(ctx, lx, ly, scale, activeGym.leader.type);

        // Draw player
        const pScreenX = offsetX + playerX * TILE * scale;
        const pScreenY = offsetY + playerY * TILE * scale;
        const sprite = Sprites.drawPlayer(playerDir, playerAnimFrame);
        ctx.drawImage(sprite, pScreenX, pScreenY, TILE * scale, TILE * scale);

        // Dialogue overlay
        if (Dialogue.isActive()) {
            Dialogue.render(ctx, canvasW, canvasH);
        }

        // Gym name banner
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        const bannerW = Math.max(160, activeGym.name.length * 10 + 30);
        ctx.fillRect(canvasW / 2 - bannerW / 2, 8, bannerW, 24);
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 13px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(activeGym.name, canvasW / 2, 25);
        ctx.textAlign = 'left';

        // Transition overlay
        if (transitionAlpha > 0) {
            ctx.fillStyle = `rgba(0, 0, 0, ${transitionAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }
    }

    function drawGymTile(ctx, type, x, y, size, gymType) {
        // Type-themed gym colors
        const themeColors = {
            Rock:   { floor: '#d0c8b0', wall: '#a09080', platform: '#c0a070', puzzle: '#b8a060', barrier: '#908060' },
            Ground: { floor: '#d8d0b8', wall: '#806040', platform: '#a08050', puzzle: '#c0a868', barrier: '#705830' },
        };
        const theme = themeColors[gymType] || themeColors.Rock;

        switch (type) {
            case T.FLOOR:
                ctx.fillStyle = theme.floor;
                ctx.fillRect(x, y, size, size);
                ctx.strokeStyle = '#c0b8a0';
                ctx.lineWidth = 0.5;
                ctx.strokeRect(x, y, size, size);
                break;
            case T.WALL:
                ctx.fillStyle = theme.wall;
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#00000020';
                ctx.fillRect(x, y + size * 0.7, size, size * 0.3);
                break;
            case T.PLATFORM:
                ctx.fillStyle = theme.platform;
                ctx.fillRect(x, y, size, size);
                ctx.strokeStyle = '#f8d830';
                ctx.lineWidth = 2;
                ctx.strokeRect(x + 1, y + 1, size - 2, size - 2);
                break;
            case T.PUZZLE:
                ctx.fillStyle = theme.puzzle;
                ctx.fillRect(x, y, size, size);
                // Diamond pattern
                ctx.fillStyle = '#00000015';
                ctx.beginPath();
                ctx.moveTo(x + size / 2, y);
                ctx.lineTo(x + size, y + size / 2);
                ctx.lineTo(x + size / 2, y + size);
                ctx.lineTo(x, y + size / 2);
                ctx.closePath();
                ctx.fill();
                break;
            case T.BARRIER:
                ctx.fillStyle = theme.barrier;
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#00000030';
                ctx.fillRect(x + size * 0.1, y + size * 0.1, size * 0.8, size * 0.8);
                break;
            case T.STATUE:
                ctx.fillStyle = theme.floor;
                ctx.fillRect(x, y, size, size);
                // Pokeball statue
                ctx.fillStyle = '#808080';
                ctx.fillRect(x + size * 0.15, y + size * 0.3, size * 0.7, size * 0.6);
                ctx.fillStyle = '#b0b0b0';
                ctx.fillRect(x + size * 0.2, y + size * 0.1, size * 0.6, size * 0.4);
                ctx.fillStyle = '#e04040';
                ctx.fillRect(x + size * 0.25, y + size * 0.15, size * 0.5, size * 0.2);
                break;
            case T.DOOR:
                ctx.fillStyle = '#604020';
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#805030';
                ctx.fillRect(x + size * 0.1, y, size * 0.8, size);
                break;
            case T.RUG:
                ctx.fillStyle = '#c04040';
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#d05050';
                ctx.fillRect(x + size * 0.1, y + size * 0.1, size * 0.8, size * 0.8);
                break;
        }
    }

    function drawTrainerSprite(ctx, x, y, scale, dir, type) {
        const s = scale;
        const typeColor = type === 'Rock' ? '#a08060' : type === 'Ground' ? '#c0a050' : '#4080c0';

        // Head
        ctx.fillStyle = '#f8c098';
        ctx.fillRect(x + 4 * s, y + 2 * s, 8 * s, 5 * s);
        // Hair
        ctx.fillStyle = '#403020';
        ctx.fillRect(x + 4 * s, y + 1 * s, 8 * s, 2 * s);
        // Eyes
        ctx.fillStyle = '#202020';
        ctx.fillRect(x + 5 * s, y + 4 * s, 2 * s, 1 * s);
        ctx.fillRect(x + 9 * s, y + 4 * s, 2 * s, 1 * s);
        // Body
        ctx.fillStyle = typeColor;
        ctx.fillRect(x + 3 * s, y + 7 * s, 10 * s, 6 * s);
        // Legs
        ctx.fillStyle = '#404040';
        ctx.fillRect(x + 4 * s, y + 13 * s, 3 * s, 3 * s);
        ctx.fillRect(x + 9 * s, y + 13 * s, 3 * s, 3 * s);
    }

    function drawLeaderSprite(ctx, x, y, scale, type) {
        const s = scale;
        const typeColor = type === 'Rock' ? '#a08060' : type === 'Ground' ? '#805020' : '#4080c0';

        // Hair (spiky for Brock, slicked for Giovanni)
        ctx.fillStyle = '#302010';
        ctx.fillRect(x + 3 * s, y, 10 * s, 4 * s);
        ctx.fillRect(x + 5 * s, y - s, 6 * s, 2 * s);
        // Face
        ctx.fillStyle = '#f8b878';
        ctx.fillRect(x + 3 * s, y + 3 * s, 10 * s, 5 * s);
        // Eyes (squinting for Brock)
        ctx.fillStyle = '#202020';
        ctx.fillRect(x + 4 * s, y + 5 * s, 3 * s, 1 * s);
        ctx.fillRect(x + 9 * s, y + 5 * s, 3 * s, 1 * s);
        // Body (bigger/more imposing)
        ctx.fillStyle = typeColor;
        ctx.fillRect(x + 2 * s, y + 8 * s, 12 * s, 6 * s);
        // Belt
        ctx.fillStyle = '#303030';
        ctx.fillRect(x + 2 * s, y + 12 * s, 12 * s, s);
        // Legs
        ctx.fillStyle = '#504030';
        ctx.fillRect(x + 3 * s, y + 14 * s, 4 * s, 2 * s);
        ctx.fillRect(x + 9 * s, y + 14 * s, 4 * s, 2 * s);
    }

    return { enter, exit, isActive, getActiveGym, update, render, gyms };
})();
