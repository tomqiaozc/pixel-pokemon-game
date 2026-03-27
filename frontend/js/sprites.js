// sprites.js — Programmatic pixel art sprite definitions
// All sprites are drawn via Canvas API, no external images needed.

const Sprites = (() => {
    const TILE = 16;

    // Color palettes
    const PAL = {
        // Player (trainer)
        skin: '#f8b878',
        hair: '#402820',
        shirt: '#e04040',
        pants: '#3050c0',
        shoes: '#402820',
        eye: '#202020',
        // Terrain
        grass: '#48a048',
        grassDark: '#388038',
        dirt: '#c0a060',
        dirtDark: '#a08848',
        water: '#4090d0',
        waterLight: '#60b0e8',
        tree: '#286028',
        treeTrunk: '#805830',
        rock: '#909090',
        rockDark: '#686868',
        flower1: '#e84040',
        flower2: '#e8d040',
        flower3: '#d040d0',
        wallTop: '#b0a090',
        wallFront: '#908070',
        roofTop: '#c04040',
        door: '#604020',
    };

    // Cache for rendered sprites
    const cache = {};

    function createCanvas(w, h) {
        const c = document.createElement('canvas');
        c.width = w;
        c.height = h;
        return c;
    }

    // Draw a single pixel on a context
    function px(ctx, x, y, color) {
        ctx.fillStyle = color;
        ctx.fillRect(x, y, 1, 1);
    }

    // ---- Player sprite frames ----
    // direction: 0=down, 1=up, 2=left, 3=right
    // frame: 0=stand, 1=walk1, 2=walk2

    function drawPlayer(dir, frame) {
        const key = `player_${dir}_${frame}`;
        if (cache[key]) return cache[key];

        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');

        // Body base — simple 16x16 character
        // Head (rows 1-6), body (rows 7-11), legs (rows 12-15)

        const isLeft = dir === 2;
        const isRight = dir === 3;
        const isUp = dir === 1;

        // Hair / head top (rows 1-3)
        for (let x = 5; x <= 10; x++) px(ctx, x, 1, PAL.hair);
        for (let x = 4; x <= 11; x++) px(ctx, x, 2, PAL.hair);
        for (let x = 4; x <= 11; x++) px(ctx, x, 3, PAL.hair);

        // Face (rows 4-6)
        for (let x = 4; x <= 11; x++) px(ctx, x, 4, PAL.skin);
        for (let x = 4; x <= 11; x++) px(ctx, x, 5, PAL.skin);
        for (let x = 4; x <= 11; x++) px(ctx, x, 6, PAL.skin);

        // Eyes
        if (!isUp) {
            if (isLeft) {
                px(ctx, 5, 5, PAL.eye);
                px(ctx, 5, 4, PAL.eye);
            } else if (isRight) {
                px(ctx, 10, 5, PAL.eye);
                px(ctx, 10, 4, PAL.eye);
            } else {
                px(ctx, 6, 5, PAL.eye);
                px(ctx, 9, 5, PAL.eye);
            }
        }

        // Shirt (rows 7-10)
        for (let y = 7; y <= 10; y++) {
            for (let x = 4; x <= 11; x++) px(ctx, x, y, PAL.shirt);
        }
        // Arms extend on walk frames
        if (frame === 1) {
            px(ctx, 3, 8, PAL.shirt); px(ctx, 12, 9, PAL.shirt);
            px(ctx, 3, 9, PAL.skin); px(ctx, 12, 10, PAL.skin);
        } else if (frame === 2) {
            px(ctx, 12, 8, PAL.shirt); px(ctx, 3, 9, PAL.shirt);
            px(ctx, 12, 9, PAL.skin); px(ctx, 3, 10, PAL.skin);
        }

        // Pants (rows 11-13)
        for (let y = 11; y <= 13; y++) {
            for (let x = 5; x <= 10; x++) px(ctx, x, y, PAL.pants);
        }
        // Leg animation
        if (frame === 1) {
            px(ctx, 5, 13, PAL.pants); px(ctx, 4, 14, PAL.pants);
            px(ctx, 10, 12, PAL.pants); px(ctx, 11, 13, PAL.pants);
        } else if (frame === 2) {
            px(ctx, 10, 13, PAL.pants); px(ctx, 11, 14, PAL.pants);
            px(ctx, 5, 12, PAL.pants); px(ctx, 4, 13, PAL.pants);
        }

        // Shoes (row 14-15)
        for (let x = 5; x <= 7; x++) px(ctx, x, 14, PAL.shoes);
        for (let x = 8; x <= 10; x++) px(ctx, x, 14, PAL.shoes);
        if (frame === 0) {
            for (let x = 5; x <= 7; x++) px(ctx, x, 15, PAL.shoes);
            for (let x = 8; x <= 10; x++) px(ctx, x, 15, PAL.shoes);
        }

        cache[key] = c;
        return c;
    }

    // ---- Tile sprites ----

    function drawGrass() {
        if (cache.grass) return cache.grass;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.fillStyle = PAL.grass;
        ctx.fillRect(0, 0, TILE, TILE);
        // Tufts
        const rng = [2,5,9,13, 1,7,11,14, 3,8,12,6];
        for (let i = 0; i < rng.length; i += 2) {
            px(ctx, rng[i], rng[i+1], PAL.grassDark);
        }
        cache.grass = c;
        return c;
    }

    function drawTallGrass() {
        if (cache.tallGrass) return cache.tallGrass;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.fillStyle = PAL.grass;
        ctx.fillRect(0, 0, TILE, TILE);
        // Tall grass blades
        ctx.fillStyle = PAL.grassDark;
        for (let x = 1; x < TILE; x += 3) {
            ctx.fillRect(x, 2, 1, 10);
            ctx.fillRect(x+1, 4, 1, 8);
        }
        ctx.fillStyle = '#5cb85c';
        for (let x = 2; x < TILE; x += 4) {
            ctx.fillRect(x, 1, 1, 6);
        }
        cache.tallGrass = c;
        return c;
    }

    function drawDirt() {
        if (cache.dirt) return cache.dirt;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.fillStyle = PAL.dirt;
        ctx.fillRect(0, 0, TILE, TILE);
        px(ctx, 3, 4, PAL.dirtDark);
        px(ctx, 10, 8, PAL.dirtDark);
        px(ctx, 7, 12, PAL.dirtDark);
        cache.dirt = c;
        return c;
    }

    function drawWater(frame) {
        const key = `water_${frame % 2}`;
        if (cache[key]) return cache[key];
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.fillStyle = PAL.water;
        ctx.fillRect(0, 0, TILE, TILE);
        // Animated wave highlights
        const off = (frame % 2) * 4;
        ctx.fillStyle = PAL.waterLight;
        for (let x = off; x < TILE; x += 8) {
            ctx.fillRect(x, 4, 3, 1);
            ctx.fillRect(x + 2, 10, 3, 1);
        }
        cache[key] = c;
        return c;
    }

    function drawTree() {
        if (cache.tree) return cache.tree;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Grass base
        ctx.fillStyle = PAL.grass;
        ctx.fillRect(0, 0, TILE, TILE);
        // Trunk
        ctx.fillStyle = PAL.treeTrunk;
        ctx.fillRect(6, 10, 4, 6);
        // Canopy (circle-ish)
        ctx.fillStyle = PAL.tree;
        ctx.fillRect(3, 2, 10, 4);
        ctx.fillRect(2, 3, 12, 5);
        ctx.fillRect(3, 8, 10, 3);
        ctx.fillRect(4, 1, 8, 2);
        // Highlights
        ctx.fillStyle = '#4cb84c';
        ctx.fillRect(4, 3, 3, 2);
        cache.tree = c;
        return c;
    }

    function drawRock() {
        if (cache.rock) return cache.rock;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.fillStyle = PAL.grass;
        ctx.fillRect(0, 0, TILE, TILE);
        // Rock body
        ctx.fillStyle = PAL.rock;
        ctx.fillRect(3, 6, 10, 8);
        ctx.fillRect(4, 5, 8, 1);
        ctx.fillRect(5, 4, 6, 1);
        // Shading
        ctx.fillStyle = PAL.rockDark;
        ctx.fillRect(3, 12, 10, 2);
        ctx.fillRect(8, 7, 4, 4);
        // Highlight
        ctx.fillStyle = '#b0b0b0';
        ctx.fillRect(5, 6, 3, 2);
        cache.rock = c;
        return c;
    }

    function drawFlower() {
        if (cache.flower) return cache.flower;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.fillStyle = PAL.grass;
        ctx.fillRect(0, 0, TILE, TILE);
        // Flowers
        px(ctx, 4, 8, PAL.flower1); px(ctx, 5, 7, PAL.flower1);
        px(ctx, 3, 7, PAL.flower1); px(ctx, 4, 6, PAL.flower1);
        px(ctx, 4, 7, '#f8f860'); // center

        px(ctx, 10, 10, PAL.flower2); px(ctx, 11, 9, PAL.flower2);
        px(ctx, 9, 9, PAL.flower2); px(ctx, 10, 8, PAL.flower2);
        px(ctx, 10, 9, '#f8f860');

        px(ctx, 7, 5, PAL.flower3); px(ctx, 8, 4, PAL.flower3);
        px(ctx, 6, 4, PAL.flower3); px(ctx, 7, 3, PAL.flower3);
        px(ctx, 7, 4, '#f8f860');
        cache.flower = c;
        return c;
    }

    function drawHouseWall() {
        if (cache.houseWall) return cache.houseWall;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.fillStyle = PAL.wallFront;
        ctx.fillRect(0, 0, TILE, TILE);
        // Brick pattern
        ctx.fillStyle = PAL.wallTop;
        for (let y = 0; y < TILE; y += 4) {
            ctx.fillRect(0, y, TILE, 1);
            const offset = (y % 8 === 0) ? 0 : 6;
            ctx.fillRect(offset, y, 1, 4);
            ctx.fillRect(offset + 8, y, 1, 4);
        }
        cache.houseWall = c;
        return c;
    }

    function drawHouseRoof() {
        if (cache.houseRoof) return cache.houseRoof;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.fillStyle = PAL.roofTop;
        ctx.fillRect(0, 0, TILE, TILE);
        // Shingle lines
        ctx.fillStyle = '#a03030';
        for (let y = 3; y < TILE; y += 4) {
            ctx.fillRect(0, y, TILE, 1);
        }
        cache.houseRoof = c;
        return c;
    }

    function drawDoor() {
        if (cache.door) return cache.door;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.fillStyle = PAL.wallFront;
        ctx.fillRect(0, 0, TILE, TILE);
        // Door
        ctx.fillStyle = PAL.door;
        ctx.fillRect(3, 2, 10, 14);
        ctx.fillStyle = '#805020';
        ctx.fillRect(4, 3, 8, 12);
        // Knob
        px(ctx, 10, 9, '#d0c040');
        cache.door = c;
        return c;
    }

    return {
        TILE,
        PAL,
        drawPlayer,
        drawGrass,
        drawTallGrass,
        drawDirt,
        drawWater,
        drawTree,
        drawRock,
        drawFlower,
        drawHouseWall,
        drawHouseRoof,
        drawDoor,
    };
})();
