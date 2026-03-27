// npc.js — NPC system for overworld

const NPC = (() => {
    const TILE = Sprites.TILE;

    // NPC type visuals
    const NPC_TYPES = {
        townsfolk: {
            hair: '#604020',
            shirt: '#4080c0',
            pants: '#404040',
        },
        professor: {
            hair: '#808080',
            shirt: '#f0f0f0',
            pants: '#604020',
        },
        nurse: {
            hair: '#e07090',
            shirt: '#f0f0f0',
            pants: '#f0f0f0',
            hat: '#e05070',
        },
        shopkeeper: {
            hair: '#302010',
            shirt: '#40a040',
            pants: '#505050',
        },
    };

    // NPC sprite cache
    const spriteCache = {};

    // NPC instances on the current map
    const npcs = [];

    // Animation
    let animTimer = 0;
    let animFrame = 0;

    function init() {
        npcs.length = 0;

        // Place NPCs in the starter town
        addNPC('Prof. Oak', 'professor', 10, 11, 0, [
            "Hello there! Welcome to the world of Pokemon!",
            "This town is peaceful, but wild Pokemon lurk in the tall grass.",
            "Be careful out there, young trainer!",
        ]);

        addNPC('Nurse Joy', 'nurse', 5, 6, 0, [
            "Welcome to the Pokemon Center!",
            "Let me heal your Pokemon to full health.",
            "Your Pokemon are fighting fit! Come back anytime.",
        ]);

        addNPC('Shopkeeper', 'shopkeeper', 22, 6, 0, [
            "Welcome to the Poke Mart!",
            "We have Potions, Poke Balls, and more!",
            "Come back when you need supplies.",
        ]);

        addNPC('Youngster', 'townsfolk', 18, 14, 2, [
            "I love Pokemon! Do you have one too?",
            "The tall grass to the west has lots of wild Pokemon!",
            "I want to catch them all someday!",
        ]);

        addNPC('Girl', 'townsfolk', 6, 18, 3, [
            "Have you seen the pond to the east?",
            "I heard there are water Pokemon there, but I can't reach them.",
            "Maybe someday someone will teach a Pokemon to Surf!",
        ]);
    }

    function addNPC(name, type, tileX, tileY, dir, dialogue) {
        npcs.push({
            name,
            type,
            x: tileX * TILE,
            y: tileY * TILE,
            dir,           // 0=down, 1=up, 2=left, 3=right
            dialogue,
            originalDir: dir,
        });
    }

    function drawNPCSprite(type, dir, frame) {
        const key = `npc_${type}_${dir}_${frame}`;
        if (spriteCache[key]) return spriteCache[key];

        const c = document.createElement('canvas');
        c.width = TILE;
        c.height = TILE;
        const ctx = c.getContext('2d');

        const colors = NPC_TYPES[type] || NPC_TYPES.townsfolk;
        const isLeft = dir === 2;
        const isRight = dir === 3;
        const isUp = dir === 1;

        function px(x, y, color) {
            ctx.fillStyle = color;
            ctx.fillRect(x, y, 1, 1);
        }

        // Hat (for nurse)
        if (colors.hat) {
            for (let x = 5; x <= 10; x++) px(x, 0, colors.hat);
            for (let x = 4; x <= 11; x++) px(x, 1, colors.hat);
        }

        // Hair
        const hairStart = colors.hat ? 2 : 1;
        for (let x = 5; x <= 10; x++) px(x, hairStart, colors.hair);
        for (let x = 4; x <= 11; x++) px(x, hairStart + 1, colors.hair);

        // Face
        const faceStart = hairStart + 2;
        for (let y = faceStart; y <= faceStart + 2; y++) {
            for (let x = 4; x <= 11; x++) px(x, y, '#f8b878');
        }

        // Eyes
        if (!isUp) {
            if (isLeft) {
                px(5, faceStart + 1, '#202020');
            } else if (isRight) {
                px(10, faceStart + 1, '#202020');
            } else {
                px(6, faceStart + 1, '#202020');
                px(9, faceStart + 1, '#202020');
            }
        }

        // Shirt
        const shirtStart = faceStart + 3;
        for (let y = shirtStart; y <= shirtStart + 3; y++) {
            for (let x = 4; x <= 11; x++) px(x, y, colors.shirt);
        }

        // Pants
        const pantsStart = shirtStart + 4;
        for (let y = pantsStart; y <= pantsStart + 2; y++) {
            for (let x = 5; x <= 10; x++) px(x, y, colors.pants);
        }

        // Feet
        const feetY = pantsStart + 3;
        if (frame === 0) {
            for (let x = 5; x <= 7; x++) px(x, feetY, '#402820');
            for (let x = 8; x <= 10; x++) px(x, feetY, '#402820');
        } else {
            for (let x = 4; x <= 6; x++) px(x, feetY, '#402820');
            for (let x = 9; x <= 11; x++) px(x, feetY, '#402820');
        }

        spriteCache[key] = c;
        return c;
    }

    function update(dt) {
        animTimer += dt;
        if (animTimer > 800) {
            animFrame = 1 - animFrame;
            animTimer = 0;
        }
    }

    function render(ctx, camX, camY, scale) {
        for (const npc of npcs) {
            const screenX = (npc.x - camX) * scale;
            const screenY = (npc.y - camY) * scale;

            // Only render if on screen (with margin)
            if (screenX < -TILE * scale || screenX > ctx.canvas.width + TILE * scale) continue;
            if (screenY < -TILE * scale || screenY > ctx.canvas.height + TILE * scale) continue;

            const sprite = drawNPCSprite(npc.type, npc.dir, animFrame);
            ctx.drawImage(sprite, screenX, screenY, TILE * scale, TILE * scale);
        }
    }

    // Check if player is facing an NPC within interaction range
    function checkInteraction(playerX, playerY, playerDir) {
        const playerTileX = Math.floor((playerX + TILE / 2) / TILE);
        const playerTileY = Math.floor((playerY + TILE / 2) / TILE);

        // Tile player is facing
        let facingX = playerTileX;
        let facingY = playerTileY;
        if (playerDir === 0) facingY++;
        else if (playerDir === 1) facingY--;
        else if (playerDir === 2) facingX--;
        else if (playerDir === 3) facingX++;

        for (const npc of npcs) {
            const npcTileX = Math.floor((npc.x + TILE / 2) / TILE);
            const npcTileY = Math.floor((npc.y + TILE / 2) / TILE);

            if (npcTileX === facingX && npcTileY === facingY) {
                // Turn NPC to face player
                const oppositeDir = [1, 0, 3, 2]; // down<->up, left<->right
                npc.dir = oppositeDir[playerDir];
                return npc;
            }
        }
        return null;
    }

    // Register NPCs as solid tiles for collision
    function isSolid(tileX, tileY) {
        for (const npc of npcs) {
            const npcTileX = Math.floor((npc.x + TILE / 2) / TILE);
            const npcTileY = Math.floor((npc.y + TILE / 2) / TILE);
            if (npcTileX === tileX && npcTileY === tileY) return true;
        }
        return false;
    }

    return { init, update, render, checkInteraction, isSolid, npcs };
})();
