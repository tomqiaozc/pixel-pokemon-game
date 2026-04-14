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

    // ---- Player surfing sprite ----
    // Player on water mount (blue base beneath player)
    function drawPlayerSurfing(dir, frame) {
        const key = `player_surf_${dir}_${frame}`;
        if (cache[key]) return cache[key];

        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');

        const isLeft = dir === 2;
        const isRight = dir === 3;
        const isUp = dir === 1;

        // Water mount base (bottom half)
        ctx.fillStyle = PAL.water;
        ctx.fillRect(2, 10, 12, 5);
        ctx.fillRect(3, 9, 10, 1);
        ctx.fillRect(1, 11, 14, 3);
        // Wave highlight
        ctx.fillStyle = PAL.waterLight;
        const waveOff = (frame % 2) * 3;
        ctx.fillRect(3 + waveOff, 14, 3, 1);
        ctx.fillRect(8 + waveOff, 13, 2, 1);

        // Smaller player torso on top of mount (rows 1-9)
        // Head (rows 1-4)
        for (let x = 5; x <= 10; x++) px(ctx, x, 1, PAL.hair);
        for (let x = 5; x <= 10; x++) px(ctx, x, 2, PAL.hair);
        for (let x = 5; x <= 10; x++) px(ctx, x, 3, PAL.skin);
        for (let x = 5; x <= 10; x++) px(ctx, x, 4, PAL.skin);

        // Eyes
        if (!isUp) {
            if (isLeft) { px(ctx, 6, 3, PAL.eye); }
            else if (isRight) { px(ctx, 9, 3, PAL.eye); }
            else { px(ctx, 6, 4, PAL.eye); px(ctx, 9, 4, PAL.eye); }
        }

        // Shirt (rows 5-8)
        for (let y = 5; y <= 8; y++) {
            for (let x = 5; x <= 10; x++) px(ctx, x, y, PAL.shirt);
        }

        // Seated legs hint (row 9)
        for (let x = 5; x <= 10; x++) px(ctx, x, 9, PAL.pants);

        cache[key] = c;
        return c;
    }

    // ---- Player fishing sprite ----
    // Player holding rod (arm extended in facing direction)
    function drawPlayerFishing(dir) {
        const key = `player_fish_${dir}`;
        if (cache[key]) return cache[key];

        // Start from standing player sprite
        const base = drawPlayer(dir, 0);
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        ctx.drawImage(base, 0, 0);

        // Rod arm extension
        ctx.fillStyle = '#805830'; // rod color (brown)
        if (dir === 0) {        // down
            ctx.fillRect(11, 8, 1, 3);
            ctx.fillRect(11, 11, 1, 5);
        } else if (dir === 1) { // up
            ctx.fillRect(4, 5, 1, 3);
            ctx.fillRect(4, 2, 1, 4);
        } else if (dir === 2) { // left
            ctx.fillRect(1, 8, 3, 1);
            ctx.fillRect(0, 8, 1, 3);
        } else {                // right
            ctx.fillRect(12, 8, 3, 1);
            ctx.fillRect(15, 8, 1, 3);
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

    // ---- HM obstacle sprites ----

    function drawCuttableTree() {
        if (cache.cuttableTree) return cache.cuttableTree;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Grass base
        ctx.fillStyle = PAL.grass;
        ctx.fillRect(0, 0, TILE, TILE);
        // Smaller tree (thinner than normal tree — cuttable)
        ctx.fillStyle = PAL.treeTrunk;
        ctx.fillRect(7, 11, 3, 5);
        // Canopy (smaller, rounder)
        ctx.fillStyle = '#3a7a3a';
        ctx.fillRect(4, 3, 8, 4);
        ctx.fillRect(3, 4, 10, 4);
        ctx.fillRect(4, 8, 8, 3);
        // Highlight
        ctx.fillStyle = '#5cb85c';
        ctx.fillRect(5, 4, 3, 2);
        // Dashed outline indicating cuttability
        ctx.strokeStyle = '#ffe040';
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 2]);
        ctx.strokeRect(2.5, 2.5, 11, 10);
        ctx.setLineDash([]);
        cache.cuttableTree = c;
        return c;
    }

    function drawPushableBoulder() {
        if (cache.pushableBoulder) return cache.pushableBoulder;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Grass base
        ctx.fillStyle = PAL.grass;
        ctx.fillRect(0, 0, TILE, TILE);
        // Round boulder body
        ctx.fillStyle = '#8a8a8a';
        ctx.fillRect(3, 5, 10, 8);
        ctx.fillRect(4, 4, 8, 1);
        ctx.fillRect(4, 13, 8, 1);
        ctx.fillRect(2, 7, 1, 4);
        ctx.fillRect(13, 7, 1, 4);
        // Dark shading
        ctx.fillStyle = '#6a6a6a';
        ctx.fillRect(7, 10, 5, 3);
        ctx.fillRect(10, 7, 3, 5);
        // Highlight
        ctx.fillStyle = '#aaaaaa';
        ctx.fillRect(4, 5, 3, 3);
        // Directional arrow hints (small triangles)
        ctx.fillStyle = 'rgba(255, 224, 64, 0.5)';
        // Up arrow
        px(ctx, 7, 2, '#ffe040'); px(ctx, 8, 2, '#ffe040');
        px(ctx, 7, 3, '#ffe040'); px(ctx, 8, 3, '#ffe040');
        cache.pushableBoulder = c;
        return c;
    }

    // ---- Pokemon species sprites ----

    // #23 Ekans — Purple snake, coiled, yellow rattle
    function drawSpecies23() {
        if (cache.species23) return cache.species23;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Coiled body
        ctx.fillStyle = '#9060b0';
        ctx.fillRect(5, 8, 8, 3);
        ctx.fillRect(4, 7, 3, 1);
        ctx.fillRect(10, 7, 3, 1);
        ctx.fillRect(3, 8, 2, 4);
        ctx.fillRect(11, 8, 2, 4);
        ctx.fillRect(5, 11, 8, 2);
        // Inner coil darker
        ctx.fillStyle = '#704890';
        ctx.fillRect(6, 9, 6, 2);
        // Yellow belly stripes
        ctx.fillStyle = '#e8d040';
        ctx.fillRect(5, 10, 2, 1);
        ctx.fillRect(9, 10, 2, 1);
        // Head (raised up from coil)
        ctx.fillStyle = '#9060b0';
        ctx.fillRect(5, 3, 4, 4);
        ctx.fillRect(4, 4, 6, 3);
        // Eyes
        px(ctx, 5, 4, '#e02020');
        px(ctx, 8, 4, '#e02020');
        // Tongue
        px(ctx, 6, 7, '#e04060');
        px(ctx, 7, 7, '#e04060');
        // Yellow rattle tail
        ctx.fillStyle = '#e8d040';
        ctx.fillRect(12, 11, 2, 1);
        ctx.fillRect(13, 10, 2, 2);
        cache.species23 = c;
        return c;
    }

    // #24 Arbok — Larger purple cobra, hood pattern
    function drawSpecies24() {
        if (cache.species24) return cache.species24;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Body coil (bottom)
        ctx.fillStyle = '#7848a0';
        ctx.fillRect(4, 10, 9, 4);
        ctx.fillRect(3, 11, 11, 3);
        // Yellow belly
        ctx.fillStyle = '#e8d040';
        ctx.fillRect(6, 12, 5, 2);
        // Hood (wide)
        ctx.fillStyle = '#9060b0';
        ctx.fillRect(2, 3, 12, 7);
        ctx.fillRect(3, 2, 10, 1);
        ctx.fillRect(1, 5, 1, 3);
        ctx.fillRect(14, 5, 1, 3);
        // Hood pattern (face design)
        ctx.fillStyle = '#e02020';
        ctx.fillRect(5, 5, 2, 2);
        ctx.fillRect(9, 5, 2, 2);
        // Hood eyes pattern
        ctx.fillStyle = '#202020';
        px(ctx, 6, 5, '#202020');
        px(ctx, 9, 5, '#202020');
        // Actual eyes
        px(ctx, 6, 3, '#e02020');
        px(ctx, 9, 3, '#e02020');
        // Mouth
        px(ctx, 7, 8, '#e04060');
        px(ctx, 8, 8, '#e04060');
        cache.species24 = c;
        return c;
    }

    // #29 Nidoran-F — Small blue quadruped, spots, horn
    function drawSpecies29() {
        if (cache.species29) return cache.species29;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Body
        ctx.fillStyle = '#80a0d0';
        ctx.fillRect(4, 7, 8, 5);
        ctx.fillRect(3, 8, 10, 4);
        // Head
        ctx.fillRect(3, 5, 6, 4);
        ctx.fillRect(4, 4, 4, 1);
        // Ears
        ctx.fillRect(4, 2, 2, 3);
        ctx.fillRect(7, 2, 2, 3);
        // Ear inner
        ctx.fillStyle = '#c0a0c0';
        px(ctx, 5, 3, '#c0a0c0');
        px(ctx, 7, 3, '#c0a0c0');
        // Eye
        px(ctx, 5, 6, '#e02020');
        // Horn
        px(ctx, 4, 1, '#e8e8e8');
        // Spots
        ctx.fillStyle = '#5878a8';
        px(ctx, 6, 8, '#5878a8');
        px(ctx, 9, 9, '#5878a8');
        px(ctx, 7, 10, '#5878a8');
        // Legs
        ctx.fillStyle = '#80a0d0';
        ctx.fillRect(4, 12, 2, 2);
        ctx.fillRect(9, 12, 2, 2);
        // Feet
        ctx.fillStyle = '#6888b0';
        ctx.fillRect(4, 13, 2, 1);
        ctx.fillRect(9, 13, 2, 1);
        cache.species29 = c;
        return c;
    }

    // #30 Nidorina — Larger blue, spines, darker spots
    function drawSpecies30() {
        if (cache.species30) return cache.species30;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Body (larger)
        ctx.fillStyle = '#6890c0';
        ctx.fillRect(3, 7, 10, 6);
        ctx.fillRect(2, 8, 12, 5);
        // Head
        ctx.fillRect(2, 4, 7, 5);
        ctx.fillRect(3, 3, 5, 1);
        // Ears
        ctx.fillRect(3, 1, 2, 3);
        ctx.fillRect(6, 1, 2, 3);
        // Ear inner
        px(ctx, 4, 2, '#c0a0c0');
        px(ctx, 6, 2, '#c0a0c0');
        // Eye
        px(ctx, 4, 5, '#e02020');
        // Horn
        px(ctx, 3, 0, '#e8e8e8');
        // Spines on back
        ctx.fillStyle = '#5070a0';
        px(ctx, 7, 6, '#5070a0');
        px(ctx, 9, 6, '#5070a0');
        px(ctx, 11, 6, '#5070a0');
        // Darker spots
        ctx.fillStyle = '#4868a0';
        px(ctx, 5, 9, '#4868a0');
        px(ctx, 8, 10, '#4868a0');
        px(ctx, 10, 9, '#4868a0');
        px(ctx, 6, 11, '#4868a0');
        // Legs
        ctx.fillStyle = '#6890c0';
        ctx.fillRect(3, 13, 2, 2);
        ctx.fillRect(10, 13, 2, 2);
        // Feet
        ctx.fillStyle = '#5878a8';
        ctx.fillRect(3, 14, 2, 1);
        ctx.fillRect(10, 14, 2, 1);
        cache.species30 = c;
        return c;
    }

    // #32 Nidoran-M — Small purple quadruped, large ears, horn
    function drawSpecies32() {
        if (cache.species32) return cache.species32;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Body
        ctx.fillStyle = '#b070c0';
        ctx.fillRect(4, 7, 8, 5);
        ctx.fillRect(3, 8, 10, 4);
        // Head
        ctx.fillRect(3, 5, 6, 4);
        ctx.fillRect(4, 4, 4, 1);
        // Large ears (taller than Nidoran-F)
        ctx.fillRect(3, 1, 2, 4);
        ctx.fillRect(7, 1, 2, 4);
        // Ear inner
        px(ctx, 4, 2, '#d0a0d0');
        px(ctx, 7, 2, '#d0a0d0');
        // Eye
        px(ctx, 5, 6, '#e02020');
        // Larger horn
        px(ctx, 5, 0, '#e8e8e8');
        px(ctx, 5, 1, '#e8e8e8');
        // Spots
        ctx.fillStyle = '#8850a0';
        px(ctx, 6, 8, '#8850a0');
        px(ctx, 9, 9, '#8850a0');
        // Legs
        ctx.fillStyle = '#b070c0';
        ctx.fillRect(4, 12, 2, 2);
        ctx.fillRect(9, 12, 2, 2);
        // Feet
        ctx.fillStyle = '#9058a0';
        ctx.fillRect(4, 13, 2, 1);
        ctx.fillRect(9, 13, 2, 1);
        cache.species32 = c;
        return c;
    }

    // #33 Nidorino — Larger purple, bigger horn, spines
    function drawSpecies33() {
        if (cache.species33) return cache.species33;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Body (larger)
        ctx.fillStyle = '#9858b0';
        ctx.fillRect(3, 7, 10, 6);
        ctx.fillRect(2, 8, 12, 5);
        // Head
        ctx.fillRect(2, 4, 7, 5);
        ctx.fillRect(3, 3, 5, 1);
        // Large ears
        ctx.fillRect(2, 1, 2, 3);
        ctx.fillRect(6, 1, 2, 3);
        // Ear inner
        px(ctx, 3, 2, '#d0a0d0');
        px(ctx, 6, 2, '#d0a0d0');
        // Eye
        px(ctx, 4, 5, '#e02020');
        // Bigger horn
        ctx.fillStyle = '#e8e8e8';
        px(ctx, 4, 0, '#e8e8e8');
        ctx.fillRect(3, 1, 2, 2);
        // Spines on back
        ctx.fillStyle = '#7840a0';
        px(ctx, 7, 6, '#7840a0');
        px(ctx, 9, 6, '#7840a0');
        px(ctx, 11, 6, '#7840a0');
        px(ctx, 8, 5, '#7840a0');
        px(ctx, 10, 5, '#7840a0');
        // Spots
        px(ctx, 5, 9, '#7840a0');
        px(ctx, 8, 10, '#7840a0');
        px(ctx, 10, 9, '#7840a0');
        // Legs
        ctx.fillStyle = '#9858b0';
        ctx.fillRect(3, 13, 2, 2);
        ctx.fillRect(10, 13, 2, 2);
        // Feet
        ctx.fillStyle = '#7840a0';
        ctx.fillRect(3, 14, 2, 1);
        ctx.fillRect(10, 14, 2, 1);
        cache.species33 = c;
        return c;
    }

    // #39 Jigglypuff — Round pink circle, tuft, big eyes
    function drawSpecies39() {
        if (cache.species39) return cache.species39;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Round body
        ctx.fillStyle = '#f8a0b8';
        ctx.fillRect(4, 4, 8, 8);
        ctx.fillRect(3, 5, 10, 6);
        ctx.fillRect(5, 3, 6, 1);
        ctx.fillRect(5, 12, 6, 1);
        // Hair tuft
        ctx.fillStyle = '#f8a0b8';
        ctx.fillRect(6, 1, 3, 3);
        px(ctx, 7, 0, '#f8a0b8');
        // Tuft curl
        ctx.fillStyle = '#e888a0';
        px(ctx, 8, 1, '#e888a0');
        px(ctx, 7, 2, '#e888a0');
        // Big eyes
        ctx.fillStyle = '#40a0e0';
        ctx.fillRect(5, 6, 2, 2);
        ctx.fillRect(9, 6, 2, 2);
        // Pupils
        px(ctx, 5, 7, '#202020');
        px(ctx, 9, 7, '#202020');
        // Eye shine
        px(ctx, 6, 6, '#e8f8ff');
        px(ctx, 10, 6, '#e8f8ff');
        // Mouth
        px(ctx, 7, 9, '#e04060');
        px(ctx, 8, 9, '#e04060');
        // Ear points
        ctx.fillStyle = '#f8a0b8';
        px(ctx, 2, 4, '#f8a0b8');
        px(ctx, 13, 4, '#f8a0b8');
        // Ear inner
        px(ctx, 2, 4, '#e888a0');
        px(ctx, 13, 4, '#e888a0');
        // Feet
        ctx.fillStyle = '#e888a0';
        ctx.fillRect(5, 13, 2, 1);
        ctx.fillRect(9, 13, 2, 1);
        cache.species39 = c;
        return c;
    }

    // #40 Wigglytuff — Taller pink, rabbit ears, big eyes
    function drawSpecies40() {
        if (cache.species40) return cache.species40;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Tall ears
        ctx.fillStyle = '#f8a0b8';
        ctx.fillRect(4, 0, 2, 4);
        ctx.fillRect(10, 0, 2, 4);
        // Ear inner
        ctx.fillStyle = '#e888a0';
        px(ctx, 5, 1, '#e888a0');
        px(ctx, 10, 1, '#e888a0');
        // Round body (taller/wider than Jigglypuff)
        ctx.fillStyle = '#f8a0b8';
        ctx.fillRect(3, 4, 10, 9);
        ctx.fillRect(2, 5, 12, 7);
        ctx.fillRect(4, 3, 8, 1);
        ctx.fillRect(4, 13, 8, 1);
        // Big eyes
        ctx.fillStyle = '#40a0e0';
        ctx.fillRect(4, 6, 3, 3);
        ctx.fillRect(9, 6, 3, 3);
        // Pupils
        ctx.fillStyle = '#202020';
        ctx.fillRect(5, 7, 2, 2);
        ctx.fillRect(10, 7, 2, 2);
        // Eye shine
        px(ctx, 5, 6, '#e8f8ff');
        px(ctx, 10, 6, '#e8f8ff');
        // Mouth
        px(ctx, 7, 10, '#e04060');
        px(ctx, 8, 10, '#e04060');
        // White belly
        ctx.fillStyle = '#f8e0e8';
        ctx.fillRect(6, 10, 4, 3);
        // Feet
        ctx.fillStyle = '#e888a0';
        ctx.fillRect(4, 14, 3, 1);
        ctx.fillRect(9, 14, 3, 1);
        cache.species40 = c;
        return c;
    }

    // #43 Oddish — Blue body, green leaves on top
    function drawSpecies43() {
        if (cache.species43) return cache.species43;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Green leaves (top)
        ctx.fillStyle = '#48a048';
        ctx.fillRect(4, 1, 2, 5);
        ctx.fillRect(7, 0, 2, 5);
        ctx.fillRect(10, 1, 2, 5);
        // Darker leaf veins
        px(ctx, 5, 2, '#388038');
        px(ctx, 7, 1, '#388038');
        px(ctx, 11, 2, '#388038');
        // Additional leaf
        ctx.fillStyle = '#48a048';
        ctx.fillRect(2, 3, 2, 3);
        ctx.fillRect(12, 3, 2, 3);
        // Blue body (round)
        ctx.fillStyle = '#5070c0';
        ctx.fillRect(4, 6, 8, 6);
        ctx.fillRect(3, 7, 10, 5);
        ctx.fillRect(5, 5, 6, 1);
        // Eyes (red)
        px(ctx, 5, 8, '#e02020');
        px(ctx, 9, 8, '#e02020');
        // Mouth
        px(ctx, 7, 10, '#e04060');
        // Feet
        ctx.fillStyle = '#4060a0';
        ctx.fillRect(4, 12, 2, 2);
        ctx.fillRect(9, 12, 2, 2);
        cache.species43 = c;
        return c;
    }

    // #44 Gloom — Larger blue, droopy flower, drool
    function drawSpecies44() {
        if (cache.species44) return cache.species44;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Droopy flower petals (top)
        ctx.fillStyle = '#c04040';
        ctx.fillRect(3, 0, 3, 3);
        ctx.fillRect(6, 0, 4, 2);
        ctx.fillRect(10, 0, 3, 3);
        // Droopy petal tips
        ctx.fillRect(2, 2, 2, 2);
        ctx.fillRect(12, 2, 2, 2);
        // Flower center
        ctx.fillStyle = '#e8d040';
        ctx.fillRect(6, 1, 4, 2);
        // Blue body (larger)
        ctx.fillStyle = '#4868b0';
        ctx.fillRect(3, 5, 10, 7);
        ctx.fillRect(2, 6, 12, 6);
        ctx.fillRect(4, 4, 8, 1);
        // Eyes (half-closed, sleepy)
        ctx.fillStyle = '#e02020';
        ctx.fillRect(4, 7, 3, 1);
        ctx.fillRect(9, 7, 3, 1);
        // Eyelids
        ctx.fillStyle = '#4868b0';
        px(ctx, 4, 7, '#4868b0');
        px(ctx, 11, 7, '#4868b0');
        // Drool
        ctx.fillStyle = '#d0e8f8';
        px(ctx, 6, 10, '#d0e8f8');
        px(ctx, 6, 11, '#d0e8f8');
        px(ctx, 7, 10, '#d0e8f8');
        // Mouth
        px(ctx, 7, 9, '#804040');
        px(ctx, 8, 9, '#804040');
        // Feet
        ctx.fillStyle = '#3858a0';
        ctx.fillRect(3, 12, 3, 2);
        ctx.fillRect(10, 12, 3, 2);
        cache.species44 = c;
        return c;
    }

    // #63 Abra — Yellow, seated pose, fox-like
    function drawSpecies63() {
        if (cache.species63) return cache.species63;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Body (seated, yellow)
        ctx.fillStyle = '#e8c848';
        ctx.fillRect(4, 7, 8, 5);
        ctx.fillRect(3, 8, 10, 4);
        // Head (fox-like, pointed)
        ctx.fillRect(4, 3, 7, 5);
        ctx.fillRect(5, 2, 5, 1);
        // Ears (pointed, tall)
        ctx.fillRect(4, 0, 2, 3);
        ctx.fillRect(9, 0, 2, 3);
        // Ear inner
        ctx.fillStyle = '#c0a040';
        px(ctx, 5, 1, '#c0a040');
        px(ctx, 9, 1, '#c0a040');
        // Eyes (closed — Abra is always sleeping)
        ctx.fillStyle = '#202020';
        ctx.fillRect(5, 5, 2, 1);
        ctx.fillRect(8, 5, 2, 1);
        // Snout/nose
        ctx.fillStyle = '#c0a040';
        ctx.fillRect(6, 6, 3, 2);
        // Brown armor segments
        ctx.fillStyle = '#a08030';
        ctx.fillRect(5, 8, 6, 1);
        ctx.fillRect(5, 10, 6, 1);
        // Arms (crossed in front — seated meditation)
        ctx.fillStyle = '#e8c848';
        ctx.fillRect(3, 9, 2, 2);
        ctx.fillRect(10, 9, 2, 2);
        // Legs (tucked, seated)
        ctx.fillRect(5, 12, 2, 2);
        ctx.fillRect(8, 12, 2, 2);
        // Tail
        ctx.fillStyle = '#c0a040';
        ctx.fillRect(11, 10, 2, 1);
        ctx.fillRect(12, 9, 2, 1);
        cache.species63 = c;
        return c;
    }

    // #64 Kadabra — Yellow/brown, spoon, mustache
    function drawSpecies64() {
        if (cache.species64) return cache.species64;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Body (standing, yellow-brown)
        ctx.fillStyle = '#d0a838';
        ctx.fillRect(5, 7, 6, 6);
        ctx.fillRect(4, 8, 8, 5);
        // Head (fox-like, larger)
        ctx.fillRect(4, 2, 8, 6);
        ctx.fillRect(5, 1, 6, 1);
        // Star on forehead
        px(ctx, 7, 2, '#e02020');
        px(ctx, 8, 2, '#e02020');
        // Ears (pointed)
        ctx.fillRect(3, 0, 2, 3);
        ctx.fillRect(11, 0, 2, 3);
        // Ear inner
        px(ctx, 4, 1, '#a08030');
        px(ctx, 11, 1, '#a08030');
        // Eyes (open, narrow)
        px(ctx, 5, 4, '#202020');
        px(ctx, 10, 4, '#202020');
        // Mustache
        ctx.fillStyle = '#d0a838';
        ctx.fillRect(4, 6, 2, 1);
        ctx.fillRect(10, 6, 2, 1);
        // Brown armor
        ctx.fillStyle = '#8a6828';
        ctx.fillRect(5, 9, 6, 1);
        ctx.fillRect(5, 11, 6, 1);
        // Spoon in right hand
        ctx.fillStyle = '#c0c0c0';
        ctx.fillRect(13, 5, 1, 4);
        ctx.fillRect(12, 5, 3, 1);
        ctx.fillRect(12, 4, 3, 1);
        // Right arm holding spoon
        ctx.fillStyle = '#d0a838';
        ctx.fillRect(11, 7, 2, 3);
        // Left arm
        ctx.fillRect(3, 8, 2, 2);
        // Legs
        ctx.fillRect(5, 13, 2, 2);
        ctx.fillRect(9, 13, 2, 2);
        // Tail
        ctx.fillStyle = '#a08030';
        ctx.fillRect(3, 11, 2, 1);
        ctx.fillRect(2, 10, 2, 1);
        cache.species64 = c;
        return c;
    }

    // Rocket Grunt NPC sprite (16x16)
    function drawRocketGrunt() {
        if (cache.rocketGrunt) return cache.rocketGrunt;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Black cap/hat
        ctx.fillStyle = '#202020';
        ctx.fillRect(5, 0, 6, 3);
        ctx.fillRect(4, 2, 8, 1);
        // Skin face
        ctx.fillStyle = '#f8b878';
        ctx.fillRect(5, 3, 6, 3);
        // Eyes
        px(ctx, 6, 4, '#202020');
        px(ctx, 9, 4, '#202020');
        // Black outfit body
        ctx.fillStyle = '#202020';
        ctx.fillRect(4, 6, 8, 5);
        // White "R" on chest
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(6, 7, 1, 3);
        ctx.fillRect(7, 7, 2, 1);
        ctx.fillRect(7, 8, 2, 1);
        px(ctx, 9, 9, '#f0f0f0');
        // Dark gray pants
        ctx.fillStyle = '#404040';
        ctx.fillRect(5, 11, 3, 3);
        ctx.fillRect(8, 11, 3, 3);
        // Black shoes
        ctx.fillStyle = '#202020';
        ctx.fillRect(4, 14, 3, 2);
        ctx.fillRect(9, 14, 3, 2);
        cache.rocketGrunt = c;
        return c;
    }

    // Gate Guard NPC sprite (16x16)
    function drawGateGuard() {
        if (cache.gateGuard) return cache.gateGuard;
        const c = createCanvas(TILE, TILE);
        const ctx = c.getContext('2d');
        // Blue cap
        ctx.fillStyle = '#3050c0';
        ctx.fillRect(5, 0, 6, 3);
        ctx.fillRect(4, 2, 8, 1);
        // Skin face
        ctx.fillStyle = '#f8b878';
        ctx.fillRect(5, 3, 6, 3);
        // Eyes
        px(ctx, 6, 4, '#202020');
        px(ctx, 9, 4, '#202020');
        // Blue uniform body
        ctx.fillStyle = '#3050c0';
        ctx.fillRect(4, 6, 8, 5);
        // Gold badge
        ctx.fillStyle = '#d0a838';
        ctx.fillRect(6, 7, 2, 2);
        // Dark pants
        ctx.fillStyle = '#303060';
        ctx.fillRect(5, 11, 3, 3);
        ctx.fillRect(8, 11, 3, 3);
        // Black shoes
        ctx.fillStyle = '#202020';
        ctx.fillRect(4, 14, 3, 2);
        ctx.fillRect(9, 14, 3, 2);
        cache.gateGuard = c;
        return c;
    }

    // Lt. Surge sprite — tall military man, green camo, blonde hair
    function drawLtSurge() {
        if (cache.ltSurge) return cache.ltSurge;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Blonde hair
        ctx.fillStyle = '#FFD700';
        ctx.fillRect(5, 1, 6, 3);
        // Skin
        ctx.fillStyle = '#FDBCB4';
        ctx.fillRect(5, 3, 6, 4);
        // Eyes
        ctx.fillStyle = '#333';
        ctx.fillRect(6, 4, 2, 1);
        ctx.fillRect(10, 4, 2, 1);
        // Camo green body
        ctx.fillStyle = '#556B2F';
        ctx.fillRect(4, 7, 8, 5);
        // Dark green belt
        ctx.fillStyle = '#2E4A1B';
        ctx.fillRect(4, 11, 8, 1);
        // Pants
        ctx.fillStyle = '#8B7D3C';
        ctx.fillRect(5, 12, 3, 3);
        ctx.fillRect(9, 12, 3, 3);
        // Boots
        ctx.fillStyle = '#333';
        ctx.fillRect(5, 15, 3, 1);
        ctx.fillRect(9, 15, 3, 1);
        cache.ltSurge = c;
        return c;
    }

    // Sailor sprite — white uniform, sailor hat
    function drawSailor() {
        if (cache.sailor) return cache.sailor;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Sailor hat
        ctx.fillStyle = '#FFF';
        ctx.fillRect(5, 1, 6, 2);
        ctx.fillStyle = '#1E90FF';
        ctx.fillRect(5, 2, 6, 1);
        // Skin
        ctx.fillStyle = '#FDBCB4';
        ctx.fillRect(5, 3, 6, 4);
        // Eyes
        ctx.fillStyle = '#333';
        ctx.fillRect(6, 4, 2, 1);
        ctx.fillRect(10, 4, 2, 1);
        // White shirt
        ctx.fillStyle = '#FFF';
        ctx.fillRect(4, 7, 8, 4);
        // Blue collar
        ctx.fillStyle = '#1E90FF';
        ctx.fillRect(5, 7, 6, 1);
        // Blue pants
        ctx.fillStyle = '#1E90FF';
        ctx.fillRect(5, 11, 3, 4);
        ctx.fillRect(9, 11, 3, 4);
        // Shoes
        ctx.fillStyle = '#333';
        ctx.fillRect(5, 14, 3, 2);
        ctx.fillRect(9, 14, 3, 2);
        cache.sailor = c;
        return c;
    }

    // Ship captain sprite — white cap, white jacket, beard
    function drawCaptain() {
        if (cache.captain) return cache.captain;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // White captain hat
        ctx.fillStyle = '#FFF';
        ctx.fillRect(4, 0, 8, 3);
        ctx.fillStyle = '#333';
        ctx.fillRect(4, 2, 8, 1);
        // Skin
        ctx.fillStyle = '#FDBCB4';
        ctx.fillRect(5, 3, 6, 4);
        // Grey beard
        ctx.fillStyle = '#999';
        ctx.fillRect(5, 6, 6, 2);
        // Eyes
        ctx.fillStyle = '#333';
        ctx.fillRect(6, 4, 2, 1);
        ctx.fillRect(10, 4, 2, 1);
        // White jacket
        ctx.fillStyle = '#FFF';
        ctx.fillRect(3, 7, 10, 5);
        // Gold buttons
        ctx.fillStyle = '#FFD700';
        ctx.fillRect(7, 8, 1, 1);
        ctx.fillRect(7, 10, 1, 1);
        // Blue pants
        ctx.fillStyle = '#1E3D6F';
        ctx.fillRect(5, 12, 3, 3);
        ctx.fillRect(9, 12, 3, 3);
        // Black shoes
        ctx.fillStyle = '#333';
        ctx.fillRect(5, 15, 3, 1);
        ctx.fillRect(9, 15, 3, 1);
        cache.captain = c;
        return c;
    }

    // Trash can sprite — grey can with lid
    function drawTrashCan() {
        if (cache.trashCan) return cache.trashCan;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Can body
        ctx.fillStyle = '#888';
        ctx.fillRect(3, 4, 10, 10);
        // Lid
        ctx.fillStyle = '#666';
        ctx.fillRect(2, 2, 12, 3);
        // Handle
        ctx.fillStyle = '#555';
        ctx.fillRect(6, 1, 4, 1);
        // Rim
        ctx.fillStyle = '#555';
        ctx.fillRect(3, 14, 10, 1);
        cache.trashCan = c;
        return c;
    }

    // Channeler sprite — purple robe, mystical headdress
    function drawChanneler() {
        if (cache.channeler) return cache.channeler;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Purple headdress
        ctx.fillStyle = '#7B2D8E';
        ctx.fillRect(4, 0, 8, 4);
        // Skin
        ctx.fillStyle = '#FDBCB4';
        ctx.fillRect(5, 3, 6, 4);
        // Eyes (closed/mystical)
        ctx.fillStyle = '#333';
        ctx.fillRect(6, 4, 2, 1);
        ctx.fillRect(10, 4, 2, 1);
        // Purple robe
        ctx.fillStyle = '#9B30FF';
        ctx.fillRect(3, 7, 10, 7);
        // Gold sash
        ctx.fillStyle = '#FFD700';
        ctx.fillRect(5, 9, 6, 1);
        // Dark purple hem
        ctx.fillStyle = '#6A1B9A';
        ctx.fillRect(3, 13, 10, 2);
        cache.channeler = c;
        return c;
    }

    // Mr. Fuji sprite — old man, white hair, kind
    function drawMrFuji() {
        if (cache.mrFuji) return cache.mrFuji;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // White hair
        ctx.fillStyle = '#E8E8E8';
        ctx.fillRect(5, 1, 6, 3);
        // Skin
        ctx.fillStyle = '#FDBCB4';
        ctx.fillRect(5, 3, 6, 4);
        // Glasses
        ctx.fillStyle = '#333';
        ctx.fillRect(6, 4, 2, 1);
        ctx.fillRect(9, 4, 2, 1);
        ctx.fillRect(8, 4, 1, 1);
        // White beard
        ctx.fillStyle = '#E8E8E8';
        ctx.fillRect(6, 6, 4, 2);
        // Brown robe
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(4, 7, 8, 5);
        // Sash
        ctx.fillStyle = '#D2691E';
        ctx.fillRect(6, 8, 4, 1);
        // Legs
        ctx.fillStyle = '#555';
        ctx.fillRect(5, 12, 3, 3);
        ctx.fillRect(9, 12, 3, 3);
        // Sandals
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(5, 15, 3, 1);
        ctx.fillRect(9, 15, 3, 1);
        cache.mrFuji = c;
        return c;
    }

    // Ghost sprite — purple hazy form (unidentified tower ghost)
    function drawGhost() {
        if (cache.ghost) return cache.ghost;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Ghostly body — semi-transparent purple
        ctx.fillStyle = '#6A0DAD';
        ctx.fillRect(4, 2, 8, 8);
        ctx.fillRect(3, 4, 10, 6);
        ctx.fillRect(2, 6, 12, 4);
        // Wispy bottom
        ctx.fillStyle = '#8B5CF6';
        ctx.fillRect(2, 10, 3, 3);
        ctx.fillRect(6, 10, 4, 4);
        ctx.fillRect(11, 10, 3, 3);
        // Eyes — glowing white
        ctx.fillStyle = '#FFF';
        ctx.fillRect(5, 4, 2, 2);
        ctx.fillRect(9, 4, 2, 2);
        // Pupils
        ctx.fillStyle = '#333';
        ctx.fillRect(6, 5, 1, 1);
        ctx.fillRect(10, 5, 1, 1);
        cache.ghost = c;
        return c;
    }

    // Tombstone sprite — grey stone marker
    function drawTombstone() {
        if (cache.tombstone) return cache.tombstone;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Stone body
        ctx.fillStyle = '#808080';
        ctx.fillRect(3, 3, 10, 12);
        // Rounded top
        ctx.fillRect(4, 2, 8, 1);
        ctx.fillRect(5, 1, 6, 1);
        // Cross engraving
        ctx.fillStyle = '#666';
        ctx.fillRect(7, 4, 2, 6);
        ctx.fillRect(5, 6, 6, 2);
        // Base
        ctx.fillStyle = '#696969';
        ctx.fillRect(2, 14, 12, 2);
        cache.tombstone = c;
        return c;
    }

    // Erika — Celadon Gym Leader — black hair, kimono, flowers
    function drawErika() {
        if (cache.erika) return cache.erika;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Hair (black, long)
        ctx.fillStyle = '#222';
        ctx.fillRect(4, 1, 8, 5);
        ctx.fillRect(3, 3, 2, 4);
        ctx.fillRect(11, 3, 2, 4);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 3, 6, 4);
        // Eyes
        ctx.fillStyle = '#2a2';
        ctx.fillRect(6, 4, 2, 1);
        ctx.fillRect(9, 4, 2, 1);
        // Mouth
        ctx.fillStyle = '#c66';
        ctx.fillRect(7, 6, 2, 1);
        // Kimono body (yellow-green)
        ctx.fillStyle = '#8c8';
        ctx.fillRect(4, 7, 8, 5);
        // Kimono sash (red)
        ctx.fillStyle = '#d44';
        ctx.fillRect(6, 8, 4, 1);
        // Flower ornament in hair
        ctx.fillStyle = '#f88';
        ctx.fillRect(10, 2, 2, 2);
        // Arms
        ctx.fillStyle = '#8c8';
        ctx.fillRect(3, 8, 1, 3);
        ctx.fillRect(12, 8, 1, 3);
        // Legs
        ctx.fillStyle = '#654';
        ctx.fillRect(5, 12, 2, 3);
        ctx.fillRect(9, 12, 2, 3);
        // Sandals
        ctx.fillStyle = '#a86';
        ctx.fillRect(5, 14, 2, 1);
        ctx.fillRect(9, 14, 2, 1);
        cache.erika = c;
        return c;
    }

    // Biker — leather jacket, bandana
    function drawBiker() {
        if (cache.biker) return cache.biker;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Bandana (red)
        ctx.fillStyle = '#c22';
        ctx.fillRect(4, 1, 8, 3);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 3, 6, 4);
        // Sunglasses
        ctx.fillStyle = '#222';
        ctx.fillRect(5, 4, 3, 1);
        ctx.fillRect(9, 4, 3, 1);
        // Mouth
        ctx.fillStyle = '#a66';
        ctx.fillRect(7, 6, 2, 1);
        // Leather jacket (black)
        ctx.fillStyle = '#333';
        ctx.fillRect(3, 7, 10, 5);
        // Jacket zipper
        ctx.fillStyle = '#888';
        ctx.fillRect(7, 7, 1, 5);
        // Arms
        ctx.fillStyle = '#333';
        ctx.fillRect(2, 8, 1, 3);
        ctx.fillRect(13, 8, 1, 3);
        // Pants (blue jeans)
        ctx.fillStyle = '#448';
        ctx.fillRect(5, 12, 3, 3);
        ctx.fillRect(9, 12, 3, 3);
        // Boots
        ctx.fillStyle = '#222';
        ctx.fillRect(5, 14, 3, 1);
        ctx.fillRect(9, 14, 3, 1);
        cache.biker = c;
        return c;
    }

    // Slot Machine — for Game Corner
    function drawSlotMachine() {
        if (cache.slotMachine) return cache.slotMachine;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Machine body (dark grey)
        ctx.fillStyle = '#555';
        ctx.fillRect(2, 1, 12, 14);
        // Screen area (bright)
        ctx.fillStyle = '#4a4';
        ctx.fillRect(3, 2, 10, 6);
        // Three reels
        ctx.fillStyle = '#fff';
        ctx.fillRect(4, 3, 2, 4);
        ctx.fillRect(7, 3, 2, 4);
        ctx.fillRect(10, 3, 2, 4);
        // Symbols on reels
        ctx.fillStyle = '#c22';
        ctx.fillRect(4, 4, 2, 2);
        ctx.fillStyle = '#22c';
        ctx.fillRect(7, 4, 2, 2);
        ctx.fillStyle = '#cc2';
        ctx.fillRect(10, 4, 2, 2);
        // Coin slot
        ctx.fillStyle = '#aa8';
        ctx.fillRect(6, 10, 4, 2);
        // Handle
        ctx.fillStyle = '#c22';
        ctx.fillRect(14, 4, 1, 4);
        ctx.fillRect(14, 3, 2, 2);
        cache.slotMachine = c;
        return c;
    }

    // Giovanni — Team Rocket Boss — suit, slicked hair
    function drawGiovanni() {
        if (cache.giovanni) return cache.giovanni;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Hair (slicked back, dark)
        ctx.fillStyle = '#333';
        ctx.fillRect(4, 1, 8, 3);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 3, 6, 4);
        // Eyes (stern)
        ctx.fillStyle = '#422';
        ctx.fillRect(6, 4, 2, 1);
        ctx.fillRect(9, 4, 2, 1);
        // Mouth
        ctx.fillStyle = '#a66';
        ctx.fillRect(7, 6, 2, 1);
        // Suit (dark orange/brown — boss look)
        ctx.fillStyle = '#844';
        ctx.fillRect(3, 7, 10, 5);
        // Suit lapels
        ctx.fillStyle = '#622';
        ctx.fillRect(5, 7, 2, 3);
        ctx.fillRect(9, 7, 2, 3);
        // Tie
        ctx.fillStyle = '#c22';
        ctx.fillRect(7, 7, 2, 4);
        // Arms
        ctx.fillStyle = '#844';
        ctx.fillRect(2, 8, 1, 3);
        ctx.fillRect(13, 8, 1, 3);
        // Pants
        ctx.fillStyle = '#333';
        ctx.fillRect(5, 12, 3, 3);
        ctx.fillRect(9, 12, 3, 3);
        // Shoes
        ctx.fillStyle = '#222';
        ctx.fillRect(5, 14, 3, 1);
        ctx.fillRect(9, 14, 3, 1);
        cache.giovanni = c;
        return c;
    }

    // Rocket Admin — black uniform, red R
    function drawRocketAdmin() {
        if (cache.rocketAdmin) return cache.rocketAdmin;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Hat (black beret)
        ctx.fillStyle = '#222';
        ctx.fillRect(4, 0, 8, 3);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 3, 6, 4);
        // Eyes
        ctx.fillStyle = '#444';
        ctx.fillRect(6, 4, 2, 1);
        ctx.fillRect(9, 4, 2, 1);
        // Uniform (black)
        ctx.fillStyle = '#222';
        ctx.fillRect(3, 7, 10, 5);
        // Red R
        ctx.fillStyle = '#c22';
        ctx.fillRect(6, 8, 1, 3);
        ctx.fillRect(7, 8, 2, 1);
        ctx.fillRect(9, 9, 1, 1);
        ctx.fillRect(7, 10, 2, 1);
        ctx.fillRect(9, 10, 1, 2);
        // Boots
        ctx.fillStyle = '#333';
        ctx.fillRect(5, 12, 3, 3);
        ctx.fillRect(9, 12, 3, 3);
        cache.rocketAdmin = c;
        return c;
    }

    // Sabrina — Saffron Gym Leader — long dark hair, red outfit
    function drawSabrina() {
        if (cache.sabrina) return cache.sabrina;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Hair (long, dark blue-black)
        ctx.fillStyle = '#226';
        ctx.fillRect(3, 0, 10, 7);
        ctx.fillRect(2, 4, 2, 5);
        ctx.fillRect(12, 4, 2, 5);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 2, 6, 5);
        // Eyes (red/psychic)
        ctx.fillStyle = '#c22';
        ctx.fillRect(6, 3, 2, 1);
        ctx.fillRect(9, 3, 2, 1);
        // Mouth
        ctx.fillStyle = '#a66';
        ctx.fillRect(7, 5, 2, 1);
        // Body (red dress)
        ctx.fillStyle = '#c33';
        ctx.fillRect(4, 7, 8, 5);
        // Belt
        ctx.fillStyle = '#222';
        ctx.fillRect(4, 9, 8, 1);
        // Legs
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 12, 2, 3);
        ctx.fillRect(9, 12, 2, 3);
        // Shoes
        ctx.fillStyle = '#c33';
        ctx.fillRect(5, 14, 2, 1);
        ctx.fillRect(9, 14, 2, 1);
        cache.sabrina = c;
        return c;
    }

    // Blackbelt — fighting dojo trainer
    function drawBlackbelt() {
        if (cache.blackbelt) return cache.blackbelt;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Headband
        ctx.fillStyle = '#c22';
        ctx.fillRect(4, 1, 8, 2);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 3, 6, 4);
        // Eyes
        ctx.fillStyle = '#333';
        ctx.fillRect(6, 4, 2, 1);
        ctx.fillRect(9, 4, 2, 1);
        // Gi top (white)
        ctx.fillStyle = '#eee';
        ctx.fillRect(3, 7, 10, 5);
        // Belt (black)
        ctx.fillStyle = '#222';
        ctx.fillRect(4, 9, 8, 1);
        // Gi pants
        ctx.fillStyle = '#eee';
        ctx.fillRect(5, 12, 3, 3);
        ctx.fillRect(9, 12, 3, 3);
        // Bare feet
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 14, 3, 1);
        ctx.fillRect(9, 14, 3, 1);
        cache.blackbelt = c;
        return c;
    }

    // Koga — Fuchsia City Gym Leader (ninja, purple scarf)
    function drawKoga() {
        if (cache.koga) return cache.koga;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Hair (dark, spiky)
        ctx.fillStyle = '#222';
        ctx.fillRect(4, 0, 8, 4);
        ctx.fillRect(3, 1, 1, 2);
        ctx.fillRect(12, 1, 1, 2);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 2, 6, 4);
        // Eyes (narrow, sharp)
        ctx.fillStyle = '#202';
        ctx.fillRect(6, 3, 2, 1);
        ctx.fillRect(9, 3, 2, 1);
        // Mouth
        ctx.fillStyle = '#a66';
        ctx.fillRect(7, 5, 2, 1);
        // Purple scarf
        ctx.fillStyle = '#808';
        ctx.fillRect(4, 6, 8, 2);
        // Body (dark ninja outfit)
        ctx.fillStyle = '#303';
        ctx.fillRect(4, 8, 8, 4);
        // Belt
        ctx.fillStyle = '#a0a';
        ctx.fillRect(4, 10, 8, 1);
        // Legs
        ctx.fillStyle = '#303';
        ctx.fillRect(5, 12, 2, 2);
        ctx.fillRect(9, 12, 2, 2);
        // Shoes
        ctx.fillStyle = '#222';
        ctx.fillRect(5, 14, 2, 1);
        ctx.fillRect(9, 14, 2, 1);
        cache.koga = c;
        return c;
    }

    // Juggler — Fuchsia Gym trainer (colorful outfit, balls)
    function drawJuggler() {
        if (cache.juggler) return cache.juggler;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Hat (jester-like, purple)
        ctx.fillStyle = '#808';
        ctx.fillRect(4, 0, 8, 3);
        ctx.fillRect(3, 2, 2, 1);
        ctx.fillRect(11, 2, 2, 1);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 3, 6, 4);
        // Eyes
        ctx.fillStyle = '#222';
        ctx.fillRect(6, 4, 1, 1);
        ctx.fillRect(9, 4, 1, 1);
        // Smile
        ctx.fillStyle = '#c44';
        ctx.fillRect(7, 6, 2, 1);
        // Juggling balls (floating above)
        ctx.fillStyle = '#e44';
        ctx.fillRect(2, 0, 2, 2);
        ctx.fillStyle = '#44e';
        ctx.fillRect(12, 0, 2, 2);
        // Body (colorful vest)
        ctx.fillStyle = '#cc0';
        ctx.fillRect(4, 7, 8, 5);
        // Vest stripe
        ctx.fillStyle = '#808';
        ctx.fillRect(7, 7, 2, 5);
        // Legs
        ctx.fillStyle = '#44c';
        ctx.fillRect(5, 12, 2, 3);
        ctx.fillRect(9, 12, 2, 3);
        // Shoes
        ctx.fillStyle = '#222';
        ctx.fillRect(5, 14, 2, 1);
        ctx.fillRect(9, 14, 2, 1);
        cache.juggler = c;
        return c;
    }

    // Blaine — Cinnabar Island Gym Leader (bald, sunglasses, mustache)
    function drawBlaine() {
        if (cache.blaine) return cache.blaine;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Bald head
        ctx.fillStyle = '#fdd';
        ctx.fillRect(4, 0, 8, 7);
        // Sunglasses
        ctx.fillStyle = '#222';
        ctx.fillRect(5, 2, 3, 2);
        ctx.fillRect(9, 2, 3, 2);
        ctx.fillRect(8, 2, 1, 1);
        // Mustache (white)
        ctx.fillStyle = '#ddd';
        ctx.fillRect(6, 5, 4, 1);
        // Body (red/orange lab coat)
        ctx.fillStyle = '#e63';
        ctx.fillRect(3, 7, 10, 5);
        // Collar
        ctx.fillStyle = '#fff';
        ctx.fillRect(6, 7, 4, 1);
        // Legs
        ctx.fillStyle = '#633';
        ctx.fillRect(5, 12, 2, 3);
        ctx.fillRect(9, 12, 2, 3);
        // Shoes
        ctx.fillStyle = '#422';
        ctx.fillRect(5, 14, 2, 1);
        ctx.fillRect(9, 14, 2, 1);
        cache.blaine = c;
        return c;
    }

    // Burglar — Cinnabar Gym trainer (mask, striped shirt)
    function drawBurglar() {
        if (cache.burglar) return cache.burglar;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Beanie (dark)
        ctx.fillStyle = '#333';
        ctx.fillRect(4, 0, 8, 3);
        // Face with mask
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 3, 6, 4);
        // Mask (covering lower face)
        ctx.fillStyle = '#333';
        ctx.fillRect(5, 5, 6, 2);
        // Eyes
        ctx.fillStyle = '#222';
        ctx.fillRect(6, 3, 1, 1);
        ctx.fillRect(9, 3, 1, 1);
        // Striped body
        ctx.fillStyle = '#222';
        ctx.fillRect(4, 7, 8, 5);
        ctx.fillStyle = '#ddd';
        ctx.fillRect(4, 8, 8, 1);
        ctx.fillRect(4, 10, 8, 1);
        // Legs
        ctx.fillStyle = '#333';
        ctx.fillRect(5, 12, 2, 3);
        ctx.fillRect(9, 12, 2, 3);
        // Shoes
        ctx.fillStyle = '#222';
        ctx.fillRect(5, 14, 2, 1);
        ctx.fillRect(9, 14, 2, 1);
        cache.burglar = c;
        return c;
    }

    // Swimmer — water route trainer (goggles, swimsuit)
    function drawSwimmer() {
        if (cache.swimmer) return cache.swimmer;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Hair
        ctx.fillStyle = '#c80';
        ctx.fillRect(4, 0, 8, 3);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 2, 6, 5);
        // Goggles
        ctx.fillStyle = '#4af';
        ctx.fillRect(5, 3, 3, 2);
        ctx.fillRect(9, 3, 3, 2);
        // Goggle strap
        ctx.fillStyle = '#222';
        ctx.fillRect(8, 3, 1, 1);
        // Mouth
        ctx.fillStyle = '#a66';
        ctx.fillRect(7, 5, 2, 1);
        // Swimsuit body
        ctx.fillStyle = '#28c';
        ctx.fillRect(4, 7, 8, 4);
        // Arms (skin)
        ctx.fillStyle = '#fdd';
        ctx.fillRect(3, 7, 1, 3);
        ctx.fillRect(12, 7, 1, 3);
        // Legs
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 11, 2, 4);
        ctx.fillRect(9, 11, 2, 4);
        // Water splash
        ctx.fillStyle = '#4af';
        ctx.fillRect(3, 13, 10, 2);
        cache.swimmer = c;
        return c;
    }

    // Cooltrainer — Victory Road / Viridian Gym trainer
    function drawCooltrainer() {
        if (cache.cooltrainer) return cache.cooltrainer;
        const c = document.createElement('canvas');
        c.width = TILE; c.height = TILE;
        const ctx = c.getContext('2d');
        // Hair (styled, brown)
        ctx.fillStyle = '#863';
        ctx.fillRect(4, 0, 8, 4);
        ctx.fillRect(3, 2, 1, 2);
        // Face
        ctx.fillStyle = '#fdd';
        ctx.fillRect(5, 2, 6, 5);
        // Eyes
        ctx.fillStyle = '#222';
        ctx.fillRect(6, 3, 1, 1);
        ctx.fillRect(9, 3, 1, 1);
        // Mouth
        ctx.fillStyle = '#a66';
        ctx.fillRect(7, 5, 2, 1);
        // Body (blue jacket, white collar)
        ctx.fillStyle = '#fff';
        ctx.fillRect(5, 7, 6, 1);
        ctx.fillStyle = '#36c';
        ctx.fillRect(4, 8, 8, 4);
        // Belt
        ctx.fillStyle = '#c22';
        ctx.fillRect(4, 10, 8, 1);
        // Legs
        ctx.fillStyle = '#447';
        ctx.fillRect(5, 12, 2, 3);
        ctx.fillRect(9, 12, 2, 3);
        // Shoes
        ctx.fillStyle = '#333';
        ctx.fillRect(5, 14, 2, 1);
        ctx.fillRect(9, 14, 2, 1);
        cache.cooltrainer = c;
        return c;
    }

    return {
        TILE,
        PAL,
        drawPlayer,
        drawPlayerSurfing,
        drawPlayerFishing,
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
        drawCuttableTree,
        drawPushableBoulder,
        drawSpecies23,
        drawSpecies24,
        drawSpecies29,
        drawSpecies30,
        drawSpecies32,
        drawSpecies33,
        drawSpecies39,
        drawSpecies40,
        drawSpecies43,
        drawSpecies44,
        drawSpecies63,
        drawSpecies64,
        drawRocketGrunt,
        drawGateGuard,
        drawLtSurge,
        drawSailor,
        drawCaptain,
        drawTrashCan,
        drawChanneler,
        drawMrFuji,
        drawGhost,
        drawTombstone,
        drawErika,
        drawBiker,
        drawSlotMachine,
        drawGiovanni,
        drawRocketAdmin,
        drawSabrina,
        drawBlackbelt,
        drawKoga,
        drawJuggler,
        drawBlaine,
        drawBurglar,
        drawSwimmer,
        drawCooltrainer,
    };
})();
