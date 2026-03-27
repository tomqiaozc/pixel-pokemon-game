// pokecenter.js — Pokemon Center interior and healing system

const PokeCenter = (() => {
    const TILE = Sprites.TILE;

    let active = false;
    let phase = 'idle'; // idle, dialogue, healing, done
    let healTimer = 0;
    let healFrame = 0;
    let transitionAlpha = 0;
    let transitionDir = 0; // 1=fading in, -1=fading out

    // Interior map (15x12 tiles)
    const INT_W = 15;
    const INT_H = 12;

    // Tile types for interior
    const T = {
        FLOOR: 0,
        WALL: 1,
        COUNTER: 2,
        DOOR: 3,
        PC: 4,
        RUG: 5,
        PLANT: 6,
    };

    // Interior layout
    const interior = buildInterior();

    function buildInterior() {
        const m = [];
        for (let y = 0; y < INT_H; y++) {
            const row = [];
            for (let x = 0; x < INT_W; x++) {
                row.push(T.FLOOR);
            }
            m.push(row);
        }

        // Walls (top row and sides)
        for (let x = 0; x < INT_W; x++) { m[0][x] = T.WALL; m[1][x] = T.WALL; }
        for (let y = 0; y < INT_H; y++) { m[y][0] = T.WALL; m[y][INT_W - 1] = T.WALL; }

        // Counter (row 3, center)
        for (let x = 4; x <= 10; x++) m[3][x] = T.COUNTER;

        // Door (bottom center)
        m[INT_H - 1][7] = T.DOOR;

        // PC (top-right corner)
        m[2][12] = T.PC;
        m[2][13] = T.PC;

        // Rug (entrance area)
        for (let x = 5; x <= 9; x++) {
            for (let y = INT_H - 3; y <= INT_H - 2; y++) {
                m[y][x] = T.RUG;
            }
        }

        // Plants
        m[2][1] = T.PLANT;
        m[2][2] = T.PLANT;

        return m;
    }

    // Player position in interior
    let playerX = 7;
    let playerY = INT_H - 2;
    let playerDir = 1;
    let playerAnimFrame = 0;
    let playerAnimTimer = 0;
    let playerMoving = false;

    // Nurse Joy position
    const nurseX = 7;
    const nurseY = 2;

    function enter() {
        active = true;
        phase = 'idle';
        transitionAlpha = 1;
        transitionDir = -1; // Fade in
        playerX = 7;
        playerY = INT_H - 2;
        playerDir = 1;
        playerAnimFrame = 0;
        playerMoving = false;
        healTimer = 0;
    }

    function exit() {
        transitionDir = 1; // Fade out
    }

    function isActive() { return active; }

    function update(dt) {
        if (!active) return { exited: false };

        // Transition
        if (transitionDir !== 0) {
            transitionAlpha += transitionDir * dt * 0.003;
            if (transitionAlpha <= 0) { transitionAlpha = 0; transitionDir = 0; }
            if (transitionAlpha >= 1 && transitionDir > 0) {
                active = false;
                return { exited: true };
            }
            return { exited: false };
        }

        // Dialogue handling
        if (Dialogue.isActive()) {
            Dialogue.update(dt);
            return { exited: false };
        }

        // Healing animation
        if (phase === 'healing') {
            healTimer += dt;
            healFrame = Math.floor(healTimer / 200) % 4;
            if (healTimer > 2000) {
                phase = 'done';
                // Restore all party Pokemon to full HP
                if (Game.player.party) {
                    for (const poke of Game.player.party) {
                        poke.hp = poke.maxHp;
                    }
                }
                // Sync with backend (fire-and-forget)
                API.healParty();
                Dialogue.start('Nurse Joy', [
                    'Your Pokemon have been fully healed!',
                    'We hope to see you again!',
                ], {
                    onComplete: () => { phase = 'idle'; },
                });
            }
            return { exited: false };
        }

        // Player movement in interior
        const movement = Input.getMovement();
        const MOVE_SPEED = 1.5;

        // NPC interaction
        if (Input.isActionPressed()) {
            // Check if facing Nurse Joy
            const facingTileX = playerX + (playerDir === 3 ? 1 : playerDir === 2 ? -1 : 0);
            const facingTileY = playerY + (playerDir === 0 ? 1 : playerDir === 1 ? -1 : 0);

            if (Math.abs(facingTileX - nurseX) <= 1 && facingTileY === nurseY + 1) {
                // Interacting with counter near nurse
                Dialogue.startChoice('Nurse Joy',
                    'Welcome! Shall I heal your Pokemon?',
                    [
                        { text: 'Yes', value: 'yes' },
                        { text: 'No', value: 'no' },
                    ],
                    (choice) => {
                        if (choice === 'yes') {
                            phase = 'healing';
                            healTimer = 0;
                        } else {
                            Dialogue.start('Nurse Joy', ['Okay, come back anytime!']);
                        }
                    }
                );
                return { exited: false };
            }
        }

        if (movement) {
            playerMoving = true;
            playerDir = movement.dir;

            let newX = playerX + movement.dx * MOVE_SPEED * dt * 0.06;
            let newY = playerY + movement.dy * MOVE_SPEED * dt * 0.06;

            // Interior collision
            const tileX = Math.floor(newX + 0.5);
            const tileY = Math.floor(newY + 0.5);

            // Check door exit
            if (tileY >= INT_H - 1 && Math.abs(tileX - 7) < 1) {
                exit();
                return { exited: false };
            }

            // Boundary check
            if (tileX >= 1 && tileX < INT_W - 1 && tileY >= 2 && tileY < INT_H - 1) {
                const tile = interior[tileY][tileX];
                if (tile !== T.WALL && tile !== T.COUNTER && tile !== T.PC && tile !== T.PLANT) {
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
            playerMoving = false;
            playerAnimFrame = 0;
        }

        return { exited: false };
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        const scale = 3;
        const offsetX = (canvasW - INT_W * TILE * scale) / 2;
        const offsetY = (canvasH - INT_H * TILE * scale) / 2;

        // Draw interior tiles
        for (let y = 0; y < INT_H; y++) {
            for (let x = 0; x < INT_W; x++) {
                const tile = interior[y][x];
                const sx = offsetX + x * TILE * scale;
                const sy = offsetY + y * TILE * scale;

                drawInteriorTile(ctx, tile, sx, sy, TILE * scale);
            }
        }

        // Draw Nurse Joy
        const nurseScreenX = offsetX + nurseX * TILE * scale;
        const nurseScreenY = offsetY + nurseY * TILE * scale;
        drawNurseJoy(ctx, nurseScreenX, nurseScreenY, scale);

        // Healing machine animation
        if (phase === 'healing') {
            const machineX = offsetX + 7 * TILE * scale;
            const machineY = offsetY + 3 * TILE * scale;
            drawHealingMachine(ctx, machineX, machineY, scale, healFrame);
        }

        // Draw player
        const pScreenX = offsetX + playerX * TILE * scale;
        const pScreenY = offsetY + playerY * TILE * scale;
        const sprite = Sprites.drawPlayer(playerDir, playerAnimFrame);
        ctx.drawImage(sprite, pScreenX, pScreenY, TILE * scale, TILE * scale);

        // Dialogue overlay
        if (Dialogue.isActive()) {
            Dialogue.render(ctx, canvasW, canvasH);
        }

        // Map name banner
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(canvasW / 2 - 80, 8, 160, 24);
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 13px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Pokemon Center', canvasW / 2, 25);
        ctx.textAlign = 'left';

        // Transition overlay
        if (transitionAlpha > 0) {
            ctx.fillStyle = `rgba(0, 0, 0, ${transitionAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }
    }

    function drawInteriorTile(ctx, type, x, y, size) {
        switch (type) {
            case T.FLOOR:
                ctx.fillStyle = '#f0e8d0';
                ctx.fillRect(x, y, size, size);
                ctx.strokeStyle = '#e0d8c0';
                ctx.lineWidth = 1;
                ctx.strokeRect(x, y, size, size);
                break;
            case T.WALL:
                ctx.fillStyle = '#e8d0b0';
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#d8c0a0';
                ctx.fillRect(x, y + size * 0.7, size, size * 0.3);
                break;
            case T.COUNTER:
                ctx.fillStyle = '#f0e8d0';
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#c0a880';
                ctx.fillRect(x, y, size, size * 0.6);
                ctx.fillStyle = '#a89070';
                ctx.fillRect(x, y + size * 0.5, size, size * 0.15);
                break;
            case T.DOOR:
                ctx.fillStyle = '#806040';
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#906848';
                ctx.fillRect(x + size * 0.1, y, size * 0.8, size);
                break;
            case T.PC:
                ctx.fillStyle = '#e8d0b0';
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#304060';
                ctx.fillRect(x + size * 0.1, y + size * 0.1, size * 0.8, size * 0.6);
                ctx.fillStyle = '#60a0d0';
                ctx.fillRect(x + size * 0.15, y + size * 0.15, size * 0.7, size * 0.45);
                break;
            case T.RUG:
                ctx.fillStyle = '#c04040';
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#d05050';
                ctx.fillRect(x + size * 0.1, y + size * 0.1, size * 0.8, size * 0.8);
                break;
            case T.PLANT:
                ctx.fillStyle = '#e8d0b0';
                ctx.fillRect(x, y, size, size);
                ctx.fillStyle = '#48a048';
                ctx.fillRect(x + size * 0.2, y + size * 0.1, size * 0.6, size * 0.5);
                ctx.fillStyle = '#604020';
                ctx.fillRect(x + size * 0.35, y + size * 0.5, size * 0.3, size * 0.4);
                break;
        }
    }

    function drawNurseJoy(ctx, x, y, scale) {
        const s = scale;
        // Simple nurse sprite
        ctx.fillStyle = '#e07090';
        ctx.fillRect(x + 5 * s, y + 1 * s, 6 * s, 3 * s); // hat
        ctx.fillStyle = '#f8c098';
        ctx.fillRect(x + 4 * s, y + 4 * s, 8 * s, 4 * s); // face
        ctx.fillStyle = '#202020';
        ctx.fillRect(x + 5 * s, y + 5 * s, 2 * s, 2 * s); // eye
        ctx.fillRect(x + 9 * s, y + 5 * s, 2 * s, 2 * s); // eye
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(x + 3 * s, y + 8 * s, 10 * s, 6 * s); // coat
        ctx.fillStyle = '#e05070';
        ctx.fillRect(x + 6 * s, y + 8 * s, 4 * s, 2 * s); // cross on coat
    }

    function drawHealingMachine(ctx, x, y, scale, frame) {
        const s = scale;
        // Machine base
        ctx.fillStyle = '#d0d0d0';
        ctx.fillRect(x + 2 * s, y + 2 * s, 12 * s, 10 * s);
        ctx.fillStyle = '#a0a0a0';
        ctx.fillRect(x + 3 * s, y + 3 * s, 10 * s, 8 * s);

        // Pokeballs on machine
        const ballColors = ['#e03030', '#e03030', '#e03030'];
        for (let i = 0; i < 3; i++) {
            const bx = x + (4 + i * 3) * s;
            const by = y + 5 * s;
            ctx.fillStyle = ballColors[i];
            ctx.fillRect(bx, by, 2 * s, 2 * s);
            ctx.fillStyle = '#f0f0f0';
            ctx.fillRect(bx, by + s, 2 * s, s);
        }

        // Pulsing light
        const colors = ['#40c040', '#60e060', '#80ff80', '#60e060'];
        ctx.fillStyle = colors[frame];
        ctx.fillRect(x + 6 * s, y + 9 * s, 4 * s, 2 * s);
    }

    return { enter, exit, isActive, update, render };
})();
