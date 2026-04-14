// routes.js — Route and town map prototypes

const Routes = (() => {
    const TILE = Sprites.TILE;

    // Reuse tile types from GameMap
    const T = GameMap.T;

    // Build Route 1: Vertical path from Pallet Town to Viridian City (20x40 tiles)
    function buildRoute1() {
        const W = 20, H = 40;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree borders on left and right
        for (let y = 0; y < H; y++) {
            m[y][0] = T.TREE;
            m[y][1] = T.TREE;
            m[y][W - 1] = T.TREE;
            m[y][W - 2] = T.TREE;
        }

        // Main dirt path (center, 3 tiles wide, winding)
        for (let y = 0; y < H; y++) {
            const offset = Math.floor(Math.sin(y * 0.2) * 2);
            const pathX = 9 + offset;
            for (let x = pathX - 1; x <= pathX + 1; x++) {
                if (x >= 2 && x < W - 2) m[y][x] = T.DIRT;
            }
        }

        // Tall grass patches
        // Patch 1: left side
        for (let y = 6; y <= 10; y++) {
            for (let x = 3; x <= 7; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        // Patch 2: right side
        for (let y = 15; y <= 20; y++) {
            for (let x = 13; x <= 17; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        // Patch 3: left side lower
        for (let y = 26; y <= 30; y++) {
            for (let x = 3; x <= 6; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        // Patch 4: right side lower
        for (let y = 33; y <= 37; y++) {
            for (let x = 14; x <= 17; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }

        // Ledges (rocks player can jump down from — rendered as low rocks)
        for (let x = 3; x <= 7; x++) m[12][x] = T.ROCK;
        for (let x = 13; x <= 17; x++) m[22][x] = T.ROCK;

        // Scattered trees
        m[5][12] = T.TREE;
        m[14][4] = T.TREE;
        m[23][15] = T.TREE;
        m[31][5] = T.TREE;

        // Flowers
        m[8][12] = T.FLOWER;
        m[18][5] = T.FLOWER;
        m[28][14] = T.FLOWER;
        m[35][6] = T.FLOWER;

        // Sign posts (use rocks as placeholders)
        m[2][9] = T.ROCK; // "Route 1" sign at top
        m[H - 3][9] = T.ROCK; // sign at bottom

        // Daycare building (near NPC at 15,23)
        // Roof
        m[20][13] = T.HOUSE_ROOF; m[20][14] = T.HOUSE_ROOF; m[20][15] = T.HOUSE_ROOF;
        m[20][16] = T.HOUSE_ROOF; m[20][17] = T.HOUSE_ROOF;
        m[21][13] = T.HOUSE_ROOF; m[21][14] = T.HOUSE_ROOF; m[21][15] = T.HOUSE_ROOF;
        m[21][16] = T.HOUSE_ROOF; m[21][17] = T.HOUSE_ROOF;
        // Walls
        m[22][13] = T.HOUSE_WALL; m[22][14] = T.HOUSE_WALL; m[22][15] = T.HOUSE_WALL;
        m[22][16] = T.HOUSE_WALL; m[22][17] = T.HOUSE_WALL;
        // Door
        m[22][15] = T.DOOR;

        return { data: m, width: W, height: H };
    }

    // Build Route 2: Path through forest area (20x35 tiles)
    function buildRoute2() {
        const W = 20, H = 35;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Dense tree border (wider — forest feel)
        for (let y = 0; y < H; y++) {
            m[y][0] = T.TREE; m[y][1] = T.TREE; m[y][2] = T.TREE;
            m[y][W - 1] = T.TREE; m[y][W - 2] = T.TREE; m[y][W - 3] = T.TREE;
        }

        // Main path (narrower, more winding)
        for (let y = 0; y < H; y++) {
            const offset = Math.floor(Math.sin(y * 0.3) * 3);
            const pathX = 10 + offset;
            for (let x = pathX - 1; x <= pathX + 1; x++) {
                if (x >= 3 && x < W - 3) m[y][x] = T.DIRT;
            }
        }

        // Dense tall grass patches (forest area)
        for (let y = 5; y <= 12; y++) {
            for (let x = 4; x <= 8; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 18; y <= 25; y++) {
            for (let x = 12; x <= 16; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 27; y <= 32; y++) {
            for (let x = 4; x <= 7; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }

        // Interior trees (forest feel)
        m[4][5] = T.TREE;
        m[7][14] = T.TREE;
        m[10][6] = T.TREE;
        m[15][13] = T.TREE;
        m[20][5] = T.TREE;
        m[24][14] = T.TREE;
        m[28][6] = T.TREE;

        // Flowers
        m[6][11] = T.FLOWER;
        m[16][7] = T.FLOWER;
        m[22][12] = T.FLOWER;

        // Water puddles
        m[14][5] = T.WATER;
        m[14][6] = T.WATER;
        m[15][5] = T.WATER;

        return { data: m, width: W, height: H };
    }

    // Build Pallet Town map (25x20 tiles)
    function buildPalletTown() {
        const W = 25, H = 20;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree border
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        for (let y = 0; y < H; y++) { m[y][0] = T.TREE; m[y][W - 1] = T.TREE; }

        // Main roads
        for (let x = 1; x < W - 1; x++) { m[10][x] = T.DIRT; m[11][x] = T.DIRT; }
        for (let y = 1; y < H - 1; y++) { m[y][12] = T.DIRT; m[y][13] = T.DIRT; }

        // Player's house (top-left)
        buildHouse(m, 3, 3, 5, 4);
        // Rival's house (top-right)
        buildHouse(m, 17, 3, 5, 4);
        // Prof Oak's lab (bottom, larger)
        for (let x = 8; x <= 16; x++) {
            m[13][x] = T.HOUSE_ROOF; m[14][x] = T.HOUSE_ROOF;
            m[15][x] = T.HOUSE_WALL; m[16][x] = T.HOUSE_WALL;
        }
        m[16][12] = T.DOOR; // Lab door

        // Small pond
        for (let y = 4; y <= 6; y++) {
            for (let x = 10; x <= 12; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.WATER;
            }
        }

        // Flowers
        m[8][4] = T.FLOWER;
        m[8][5] = T.FLOWER;
        m[8][20] = T.FLOWER;

        // Exit north (to Route 1)
        m[0][12] = T.DIRT; m[0][13] = T.DIRT; // Gap in trees

        return { data: m, width: W, height: H };
    }

    // Build Viridian City map (30x25 tiles)
    function buildViridianCity() {
        const W = 30, H = 25;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree border
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        for (let y = 0; y < H; y++) { m[y][0] = T.TREE; m[y][W - 1] = T.TREE; }

        // Main roads
        for (let x = 1; x < W - 1; x++) { m[12][x] = T.DIRT; m[13][x] = T.DIRT; }
        for (let y = 1; y < H - 1; y++) { m[y][14] = T.DIRT; m[y][15] = T.DIRT; }

        // Pokemon Center (left side)
        buildHouse(m, 3, 4, 6, 4);

        // Poke Mart (right side)
        buildHouse(m, 21, 4, 5, 4);

        // Gym (top area — locked until 7 badges)
        for (let x = 10; x <= 18; x++) {
            m[2][x] = T.HOUSE_ROOF; m[3][x] = T.HOUSE_ROOF;
            m[4][x] = T.HOUSE_WALL; m[5][x] = T.HOUSE_WALL;
        }
        m[5][14] = T.DOOR;

        // Houses
        buildHouse(m, 3, 16, 5, 4);
        buildHouse(m, 22, 16, 5, 4);

        // Flowers and decorations
        m[8][5] = T.FLOWER; m[8][6] = T.FLOWER;
        m[8][24] = T.FLOWER; m[8][25] = T.FLOWER;
        m[18][10] = T.FLOWER;

        // Rocks
        m[10][20] = T.ROCK;
        m[17][8] = T.ROCK;

        // Exit south (to Route 1)
        m[H - 1][14] = T.DIRT; m[H - 1][15] = T.DIRT;
        // Exit north (to Route 2)
        m[0][14] = T.DIRT; m[0][15] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Build Pewter City map (28x22 tiles)
    function buildPewterCity() {
        const W = 28, H = 22;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree border
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        for (let y = 0; y < H; y++) { m[y][0] = T.TREE; m[y][W - 1] = T.TREE; }

        // Main roads
        for (let x = 1; x < W - 1; x++) { m[11][x] = T.DIRT; m[12][x] = T.DIRT; }
        for (let y = 1; y < H - 1; y++) { m[y][13] = T.DIRT; m[y][14] = T.DIRT; }

        // Pokemon Center (left)
        buildHouse(m, 3, 4, 6, 4);

        // Gym (right, larger — Brock's gym)
        for (let x = 18; x <= 25; x++) {
            m[3][x] = T.HOUSE_ROOF; m[4][x] = T.HOUSE_ROOF;
            m[5][x] = T.HOUSE_WALL; m[6][x] = T.HOUSE_WALL;
        }
        m[6][21] = T.DOOR;

        // Museum (top-center, decorative)
        for (let x = 9; x <= 17; x++) {
            m[2][x] = T.HOUSE_ROOF; m[3][x] = T.HOUSE_ROOF;
            m[4][x] = T.HOUSE_WALL; m[5][x] = T.HOUSE_WALL;
        }
        m[5][13] = T.DOOR;

        // Houses
        buildHouse(m, 3, 14, 5, 4);
        buildHouse(m, 20, 14, 5, 4);

        // Rocks (fitting the rocky theme)
        m[8][5] = T.ROCK; m[8][6] = T.ROCK;
        m[9][22] = T.ROCK;
        m[15][10] = T.ROCK;

        // Flowers
        m[9][8] = T.FLOWER;
        m[16][20] = T.FLOWER;

        // Exit west (to Route 2)
        m[11][0] = T.DIRT; m[12][0] = T.DIRT;
        // Exit east (to Route 3, future)
        m[11][W - 1] = T.DIRT; m[12][W - 1] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    function buildHouse(m, sx, sy, w, h) {
        for (let x = sx; x < sx + w; x++) {
            m[sy][x] = T.HOUSE_ROOF;
            m[sy + 1][x] = T.HOUSE_ROOF;
        }
        for (let y = sy + 2; y < sy + h; y++) {
            for (let x = sx; x < sx + w; x++) {
                m[y][x] = T.HOUSE_WALL;
            }
        }
        m[sy + h - 1][sx + Math.floor(w / 2)] = T.DOOR;
    }

    // Build Route 4: Path from Mt. Moon to Cerulean City (30x20 tiles)
    function buildRoute4() {
        const W = 30, H = 20;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree borders (top and bottom)
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        // Left/right borders (with gaps for exits)
        for (let y = 0; y < H; y++) {
            m[y][0] = T.TREE;
            m[y][W - 1] = T.TREE;
        }

        // Main dirt path — winding east-west
        for (let x = 0; x < W; x++) {
            const offset = Math.floor(Math.sin(x * 0.25) * 2);
            const pathY = 10 + offset;
            for (let y = pathY - 1; y <= pathY; y++) {
                if (y >= 1 && y < H - 1) m[y][x] = T.DIRT;
            }
        }
        // Widen path at exits
        for (let y = 8; y <= 11; y++) {
            m[y][1] = T.DIRT;
            m[y][W - 2] = T.DIRT;
        }

        // Tall grass encounter zone 1 — upper left
        for (let y = 3; y <= 6; y++) {
            for (let x = 4; x <= 10; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        // Tall grass encounter zone 2 — lower right
        for (let y = 13; y <= 16; y++) {
            for (let x = 18; x <= 25; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }

        // South-facing ledges (shortcuts going south)
        for (let x = 5; x <= 9; x++) m[7][x] = T.ROCK;
        for (let x = 20; x <= 25; x++) m[12][x] = T.ROCK;

        // Scattered trees for decoration
        m[3][15] = T.TREE;
        m[5][22] = T.TREE;
        m[14][8] = T.TREE;
        m[16][13] = T.TREE;
        m[4][26] = T.TREE;

        // Flowers
        m[6][13] = T.FLOWER;
        m[8][20] = T.FLOWER;
        m[15][5] = T.FLOWER;
        m[3][24] = T.FLOWER;
        m[17][17] = T.FLOWER;

        // Rocks
        m[5][17] = T.ROCK;
        m[15][27] = T.ROCK;

        // Small water feature (puddle)
        m[14][3] = T.WATER;
        m[14][4] = T.WATER;
        m[15][3] = T.WATER;

        // Exit west (to mt_moon_entrance) — gap in left border
        m[9][0] = T.DIRT; m[10][0] = T.DIRT;
        // Exit east (to cerulean_city) — gap in right border
        m[9][W - 1] = T.DIRT; m[10][W - 1] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Build Cerulean City: Water-themed town (25x25 tiles)
    function buildCeruleanCity() {
        const W = 25, H = 25;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree border
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        for (let y = 0; y < H; y++) { m[y][0] = T.TREE; m[y][W - 1] = T.TREE; }

        // Main roads
        for (let x = 1; x < W - 1; x++) { m[12][x] = T.DIRT; m[13][x] = T.DIRT; }
        for (let y = 1; y < H - 1; y++) { m[y][12] = T.DIRT; m[y][13] = T.DIRT; }

        // Pokemon Center (left side, red roof feel — uses standard house)
        buildHouse(m, 3, 4, 6, 4);

        // Poke Mart (center-left)
        buildHouse(m, 12, 4, 5, 4);

        // Cerulean Gym (right side, larger — Misty's gym)
        for (let x = 18; x <= 23; x++) {
            m[4][x] = T.HOUSE_ROOF; m[5][x] = T.HOUSE_ROOF;
            m[6][x] = T.HOUSE_WALL; m[7][x] = T.HOUSE_WALL;
        }
        m[7][20] = T.DOOR;

        // Bike Shop (lower left)
        buildHouse(m, 3, 16, 5, 4);

        // Residential house (lower right)
        buildHouse(m, 18, 16, 5, 4);

        // Surfable water pond in southeast corner
        for (let y = 17; y <= 22; y++) {
            for (let x = 16; x <= 23; x++) {
                if (y === 17 && (x === 16 || x === 23)) continue;
                if (y === 22 && (x === 16 || x === 23)) continue;
                if (m[y][x] === T.GRASS) m[y][x] = T.WATER;
            }
        }

        // Flowers — water-themed decorations
        m[9][3] = T.FLOWER; m[9][4] = T.FLOWER;
        m[9][21] = T.FLOWER; m[9][22] = T.FLOWER;
        m[14][6] = T.FLOWER;
        m[15][18] = T.FLOWER;

        // Rocks
        m[10][8] = T.ROCK;
        m[21][10] = T.ROCK;

        // Extra trees
        m[15][10] = T.TREE;
        m[22][5] = T.TREE;

        // Exit west (to Route 4)
        m[12][0] = T.DIRT; m[13][0] = T.DIRT;

        // Exit south (to Route 5)
        m[H - 1][12] = T.DIRT; m[H - 1][13] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Trainer NPC positions for routes
    const route1Trainers = [
        { x: 12, y: 8, name: 'Youngster Joey', dir: 2, sightRange: 3,
          dialogue: ['Hey! My Rattata is in the top percentage of all Rattata!'],
          pokemon: [{ name: 'Rattata', level: 4, hp: 14, maxHp: 14, type: 'Normal' }] },
        { x: 5, y: 25, name: 'Lass Crissy', dir: 3, sightRange: 3,
          dialogue: ['I just caught this cute Pokemon!'],
          pokemon: [{ name: 'Pidgey', level: 5, hp: 16, maxHp: 16, type: 'Flying' }] },
    ];

    const route2Trainers = [
        { x: 7, y: 10, name: 'Bug Catcher Doug', dir: 3, sightRange: 4,
          dialogue: ['I love bug Pokemon!'],
          pokemon: [
            { name: 'Caterpie', level: 6, hp: 18, maxHp: 18, type: 'Bug' },
            { name: 'Weedle', level: 6, hp: 17, maxHp: 17, type: 'Bug' },
          ] },
        { x: 14, y: 22, name: 'Lass Robin', dir: 2, sightRange: 3,
          dialogue: ['Have you been to the forest?'],
          pokemon: [{ name: 'Oddish', level: 7, hp: 20, maxHp: 20, type: 'Grass' }] },
    ];

    const route4Trainers = [
        { x: 8, y: 5, name: 'Hiker Marcos', dir: 0, sightRange: 4,
          dialogue: ['I just came through Mt. Moon! What a trip!'],
          pokemon: [
            { name: 'Geodude', level: 12, hp: 32, maxHp: 32, type: 'Rock' },
            { name: 'Onix', level: 13, hp: 36, maxHp: 36, type: 'Rock' },
          ] },
        { x: 20, y: 9, name: 'Lass Dana', dir: 2, sightRange: 3,
          dialogue: ['Cerulean City is just ahead!'],
          pokemon: [
            { name: 'Oddish', level: 13, hp: 34, maxHp: 34, type: 'Grass' },
            { name: 'Jigglypuff', level: 12, hp: 38, maxHp: 38, type: 'Normal' },
          ] },
        { x: 14, y: 15, name: 'Youngster Timmy', dir: 1, sightRange: 3,
          dialogue: ['I train here every day!'],
          pokemon: [
            { name: 'Ekans', level: 14, hp: 35, maxHp: 35, type: 'Poison' },
          ] },
    ];

    // Build Route 5: Vertical path south of Cerulean City (20x25 tiles)
    function buildRoute5() {
        const W = 20, H = 25;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree borders
        for (let y = 0; y < H; y++) {
            m[y][0] = T.TREE; m[y][1] = T.TREE;
            m[y][W - 1] = T.TREE; m[y][W - 2] = T.TREE;
        }

        // Central dirt path (3 tiles wide)
        for (let y = 0; y < H; y++) {
            m[y][9] = T.DIRT; m[y][10] = T.DIRT; m[y][11] = T.DIRT;
        }

        // Tall grass patches
        for (let y = 4; y <= 8; y++) {
            for (let x = 3; x <= 7; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 10; y <= 14; y++) {
            for (let x = 13; x <= 17; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 16; y <= 19; y++) {
            for (let x = 3; x <= 6; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }

        // Scattered trees
        m[6][13] = T.TREE;
        m[12][4] = T.TREE;
        m[18][15] = T.TREE;

        // Flowers
        m[3][14] = T.FLOWER;
        m[9][5] = T.FLOWER;
        m[15][16] = T.FLOWER;

        // Rocks
        m[7][15] = T.ROCK;
        m[20][4] = T.ROCK;

        // Underground entrance building at south (y=20-23)
        buildHouse(m, 8, 20, 5, 4);

        // Exit north (to Cerulean City)
        m[0][9] = T.DIRT; m[0][10] = T.DIRT; m[0][11] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Build Underground Path: Long narrow corridor (4x30 tiles)
    function buildUndergroundPath() {
        const W = 4, H = 30;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }

        // Stone walls on sides
        for (let y = 0; y < H; y++) {
            m[y][0] = T.ROCK;
            m[y][W - 1] = T.ROCK;
        }

        // Entry/exit points (doors at top and bottom)
        m[0][1] = T.DOOR; m[0][2] = T.DOOR;
        m[H - 1][1] = T.DOOR; m[H - 1][2] = T.DOOR;

        return { data: m, width: W, height: H };
    }

    // Build Route 6: Vertical path to Vermilion City (20x25 tiles)
    function buildRoute6() {
        const W = 20, H = 25;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree borders
        for (let y = 0; y < H; y++) {
            m[y][0] = T.TREE; m[y][1] = T.TREE;
            m[y][W - 1] = T.TREE; m[y][W - 2] = T.TREE;
        }

        // Central dirt path (3 tiles wide)
        for (let y = 0; y < H; y++) {
            m[y][9] = T.DIRT; m[y][10] = T.DIRT; m[y][11] = T.DIRT;
        }

        // Tall grass patches
        for (let y = 5; y <= 9; y++) {
            for (let x = 3; x <= 7; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 11; y <= 15; y++) {
            for (let x = 13; x <= 17; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 17; y <= 20; y++) {
            for (let x = 4; x <= 7; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }

        // Scattered trees
        m[3][14] = T.TREE;
        m[10][4] = T.TREE;
        m[16][15] = T.TREE;

        // Flowers
        m[4][5] = T.FLOWER;
        m[13][16] = T.FLOWER;
        m[19][6] = T.FLOWER;

        // Rocks
        m[8][16] = T.ROCK;
        m[14][3] = T.ROCK;

        // Underground entrance building at north (y=0-3)
        buildHouse(m, 8, 0, 5, 4);

        // Gate building at south end (y=21-24)
        buildHouse(m, 8, 21, 5, 4);

        return { data: m, width: W, height: H };
    }

    // Build Cerulean Burgled House interior (8x8)
    function buildCeruleanBurgledHouse() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }

        // Walls
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }

        // Door at bottom center
        m[H - 1][4] = T.DOOR;

        // Bookshelf (top-left corner, uses ROCK as placeholder)
        m[1][1] = T.ROCK; m[1][2] = T.ROCK; m[1][3] = T.ROCK;

        // Table (center, uses ROCK as placeholder)
        m[3][3] = T.ROCK; m[3][4] = T.ROCK;

        return { data: m, width: W, height: H };
    }

    // Trainers for Route 6
    const route6Trainers = [
        { x: 6, y: 8, name: 'Bug Catcher Elijah', dir: 3, sightRange: 3,
          dialogue: ['These bugs are tougher than they look!'],
          pokemon: [
            { name: 'Butterfree', level: 16, hp: 42, maxHp: 42, type: 'Bug' },
          ] },
        { x: 14, y: 14, name: 'Youngster Dave', dir: 2, sightRange: 3,
          dialogue: ['I train on this route every day!'],
          pokemon: [
            { name: 'Rattata', level: 15, hp: 38, maxHp: 38, type: 'Normal' },
            { name: 'Spearow', level: 15, hp: 37, maxHp: 37, type: 'Flying' },
          ] },
    ];

    // Build Route 24: Nugget Bridge (10x40 tiles, narrow bridge over water)
    function buildRoute24() {
        const W = 10, H = 40;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.WATER);
            m.push(row);
        }

        // Bridge deck — 4 tiles wide in center
        for (let y = 0; y < H; y++) {
            for (let x = 3; x <= 6; x++) m[y][x] = T.DIRT;
        }

        // Grass areas at top and bottom
        for (let y = 0; y < 5; y++) {
            for (let x = 0; x < W; x++) m[y][x] = T.GRASS;
        }
        for (let y = H - 5; y < H; y++) {
            for (let x = 0; x < W; x++) m[y][x] = T.GRASS;
        }

        // Tall grass encounter zones at top
        for (let y = 1; y <= 3; y++) {
            for (let x = 0; x <= 2; x++) m[y][x] = T.TALL_GRASS;
            for (let x = 7; x <= 9; x++) m[y][x] = T.TALL_GRASS;
        }

        // Bridge railing (rocks on sides of bridge)
        for (let y = 5; y < H - 5; y++) {
            m[y][2] = T.ROCK;
            m[y][7] = T.ROCK;
        }

        // Trees at top corners
        m[0][0] = T.TREE; m[0][1] = T.TREE;
        m[0][8] = T.TREE; m[0][9] = T.TREE;

        // Exit south (to Cerulean City)
        m[H - 1][4] = T.DIRT; m[H - 1][5] = T.DIRT;
        // Exit north (to Route 25)
        m[0][4] = T.DIRT; m[0][5] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Trainers for Nugget Bridge (Route 24)
    const nuggetBridgeTrainers = [
        { x: 5, y: 32, name: 'Bug Catcher Ethan', dir: 0, sightRange: 2,
          dialogue: ['I caught all these bugs on Route 24!'],
          pokemon: [
            { name: 'Caterpie', level: 14, hp: 33, maxHp: 33, type: 'Bug' },
            { name: 'Weedle', level: 14, hp: 32, maxHp: 32, type: 'Bug' },
          ] },
        { x: 5, y: 27, name: 'Lass Ali', dir: 0, sightRange: 2,
          dialogue: ['Aren\'t flowers lovely? My Pokemon think so too!'],
          pokemon: [
            { name: 'Oddish', level: 16, hp: 40, maxHp: 40, type: 'Grass' },
            { name: 'Pidgey', level: 16, hp: 38, maxHp: 38, type: 'Flying' },
          ] },
        { x: 5, y: 22, name: 'Youngster Calvin', dir: 0, sightRange: 2,
          dialogue: ['I\'m tougher than I look! Bring it on!'],
          pokemon: [
            { name: 'Rattata', level: 15, hp: 36, maxHp: 36, type: 'Normal' },
            { name: 'Ekans', level: 15, hp: 35, maxHp: 35, type: 'Poison' },
          ] },
        { x: 5, y: 17, name: 'Lass Shannon', dir: 0, sightRange: 2,
          dialogue: ['My Pokemon are so cute, but they pack a punch!'],
          pokemon: [
            { name: 'Nidoran-F', level: 16, hp: 40, maxHp: 40, type: 'Poison' },
            { name: 'Jigglypuff', level: 16, hp: 48, maxHp: 48, type: 'Normal' },
          ] },
        { x: 5, y: 12, name: 'Hiker Josh', dir: 0, sightRange: 2,
          dialogue: ['The mountains are my playground!'],
          pokemon: [
            { name: 'Geodude', level: 15, hp: 35, maxHp: 35, type: 'Rock' },
            { name: 'Onix', level: 13, hp: 30, maxHp: 30, type: 'Rock' },
          ] },
        { x: 5, y: 5, name: 'Rocket Grunt', dir: 0, sightRange: 3,
          dialogue: ['Hey kid! You beat all 5 trainers? Impressive!',
                     'How about joining Team Rocket? We could use someone like you!',
                     '...No?! Then I\'ll make you regret it!'],
          pokemon: [
            { name: 'Ekans', level: 15, hp: 37, maxHp: 37, type: 'Poison' },
            { name: 'Zubat', level: 15, hp: 35, maxHp: 35, type: 'Poison' },
          ] },
    ];

    // Build Route 25: Horizontal path to Bill's House (30x20 tiles)
    function buildRoute25() {
        const W = 30, H = 20;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree borders
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        for (let y = 0; y < H; y++) { m[y][W - 1] = T.TREE; }

        // Winding dirt path east
        for (let x = 0; x < W; x++) {
            const offset = Math.floor(Math.sin(x * 0.3) * 2);
            const pathY = 10 + offset;
            for (let y = pathY - 1; y <= pathY; y++) {
                if (y >= 1 && y < H - 1) m[y][x] = T.DIRT;
            }
        }

        // Tall grass patches
        for (let y = 3; y <= 6; y++) {
            for (let x = 3; x <= 10; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 12; y <= 16; y++) {
            for (let x = 15; x <= 22; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }

        // Fence border at top
        for (let x = 1; x < W - 1; x++) m[1][x] = T.ROCK;

        // Bill's House at east end (25-28, 3-6)
        buildHouse(m, 25, 3, 4, 4);

        // Scattered trees
        m[5][18] = T.TREE;
        m[14][7] = T.TREE;
        m[7][25] = T.TREE;

        // Flowers
        m[4][14] = T.FLOWER;
        m[13][5] = T.FLOWER;
        m[8][22] = T.FLOWER;

        // Exit south (to Route 24)
        m[H - 1][4] = T.DIRT; m[H - 1][5] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Route 25 trainers
    const route25Trainers = [
        { x: 10, y: 10, name: 'Hiker Wayne', dir: 2, sightRange: 3,
          dialogue: ['These mountains hide many secrets!'],
          pokemon: [
            { name: 'Geodude', level: 15, hp: 35, maxHp: 35, type: 'Rock' },
            { name: 'Onix', level: 15, hp: 32, maxHp: 32, type: 'Rock' },
          ] },
        { x: 20, y: 8, name: 'Lass Haley', dir: 0, sightRange: 3,
          dialogue: ['I love watching the ocean from here!'],
          pokemon: [
            { name: 'Oddish', level: 17, hp: 42, maxHp: 42, type: 'Grass' },
            { name: 'Pidgey', level: 17, hp: 40, maxHp: 40, type: 'Flying' },
          ] },
    ];

    // Build Bill's House interior (8x8)
    function buildBillsHouse() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }

        // Walls
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }

        // Door at bottom center
        m[H - 1][4] = T.DOOR;

        // Bookshelves (top wall, uses ROCK as furniture)
        m[1][1] = T.ROCK; m[1][2] = T.ROCK; m[1][3] = T.ROCK;

        // Cell Separation System / PC (top-right, uses ROCK as machine)
        m[1][5] = T.ROCK; m[1][6] = T.ROCK;

        // Table
        m[4][2] = T.ROCK; m[4][3] = T.ROCK;

        return { data: m, width: W, height: H };
    }

    // Register all maps with MapLoader
    function registerAll() {
        const palletTown = buildPalletTown();
        MapLoader.registerMap('pallet_town', {
            name: 'Pallet Town',
            width: palletTown.width,
            height: palletTown.height,
            data: palletTown.data,
            exits: [
                { edge: 'north', targetMap: 'route_1', spawnX: 9, spawnY: 38, spawnDir: 1 },
            ],
            doors: [
                { x: 5, y: 6, targetMap: 'pokecenter', spawnX: 7, spawnY: 9 },
            ],
            lamps: [{ x: 10, y: 8 }, { x: 18, y: 8 }, { x: 14, y: 14 }],
        });

        const route1 = buildRoute1();
        MapLoader.registerMap('route_1', {
            name: 'Route 1',
            width: route1.width,
            height: route1.height,
            data: route1.data,
            exits: [
                { edge: 'south', targetMap: 'pallet_town', spawnX: 12, spawnY: 1, spawnDir: 0 },
                { edge: 'north', targetMap: 'viridian_city', spawnX: 14, spawnY: 23, spawnDir: 1 },
            ],
            trainers: route1Trainers,
            doors: [
                { x: 15, y: 22, targetMap: 'daycare_interior', spawnX: 4, spawnY: 7 },
            ],
            ledges: [
                { x1: 3, x2: 7, y: 12 },
                { x1: 13, x2: 17, y: 22 },
            ],
        });

        const viridianCity = buildViridianCity();
        MapLoader.registerMap('viridian_city', {
            name: 'Viridian City',
            width: viridianCity.width,
            height: viridianCity.height,
            data: viridianCity.data,
            exits: [
                { edge: 'south', targetMap: 'route_1', spawnX: 9, spawnY: 1, spawnDir: 0 },
                { edge: 'north', targetMap: 'route_2', spawnX: 10, spawnY: 33, spawnDir: 1 },
            ],
            doors: [
                { x: 5, y: 7, targetMap: 'pokecenter', spawnX: 7, spawnY: 9 },
                { x: 14, y: 5, targetMap: 'viridian_gym', spawnX: 7, spawnY: 15 },
            ],
            lamps: [{ x: 8, y: 6 }, { x: 16, y: 6 }, { x: 12, y: 12 }, { x: 20, y: 12 }],
        });

        const route2 = buildRoute2();
        MapLoader.registerMap('route_2', {
            name: 'Route 2',
            width: route2.width,
            height: route2.height,
            data: route2.data,
            exits: [
                { edge: 'south', targetMap: 'viridian_city', spawnX: 14, spawnY: 1, spawnDir: 0 },
                { edge: 'north', targetMap: 'pewter_city', spawnX: 13, spawnY: 20, spawnDir: 1 },
            ],
            trainers: route2Trainers,
        });

        const pewterCity = buildPewterCity();
        MapLoader.registerMap('pewter_city', {
            name: 'Pewter City',
            width: pewterCity.width,
            height: pewterCity.height,
            data: pewterCity.data,
            exits: [
                { edge: 'west', targetMap: 'route_2', spawnX: 18, spawnY: 1, spawnDir: 1 },
            ],
            doors: [
                { x: 5, y: 7, targetMap: 'pokecenter', spawnX: 7, spawnY: 9 },
                { x: 21, y: 6, targetMap: 'pewter_gym', spawnX: 6, spawnY: 13 },
            ],
            lamps: [{ x: 10, y: 6 }, { x: 18, y: 6 }, { x: 14, y: 10 }],
        });

        const route4 = buildRoute4();
        MapLoader.registerMap('route_4', {
            name: 'Route 4',
            width: route4.width,
            height: route4.height,
            data: route4.data,
            exits: [
                { edge: 'west', targetMap: 'mt_moon_entrance', spawnX: 18, spawnY: 10, spawnDir: 3 },
                { edge: 'east', targetMap: 'cerulean_city', spawnX: 1, spawnY: 10, spawnDir: 3 },
            ],
            trainers: route4Trainers,
            ledges: [
                { x1: 5, x2: 9, y: 7 },
                { x1: 20, x2: 25, y: 12 },
            ],
            lamps: [{ x: 12, y: 9 }, { x: 22, y: 9 }],
        });

        const ceruleanCity = buildCeruleanCity();
        MapLoader.registerMap('cerulean_city', {
            name: 'Cerulean City',
            width: ceruleanCity.width,
            height: ceruleanCity.height,
            data: ceruleanCity.data,
            exits: [
                { edge: 'west', targetMap: 'route_4', spawnX: 28, spawnY: 9, spawnDir: 2 },
                { edge: 'north', targetMap: 'route_24', spawnX: 5, spawnY: 38, spawnDir: 1 },
                { edge: 'south', targetMap: 'route_5', spawnX: 10, spawnY: 1, spawnDir: 0 },
            ],
            doors: [
                { x: 5, y: 7, targetMap: 'pokecenter', spawnX: 7, spawnY: 9 },
                { x: 14, y: 7, targetMap: 'pokemart', spawnX: 5, spawnY: 9 },
                { x: 20, y: 7, targetMap: 'cerulean_gym', spawnX: 7, spawnY: 15 },
                { x: 5, y: 19, targetMap: 'bike_shop', spawnX: 5, spawnY: 7 },
                { x: 20, y: 19, targetMap: 'cerulean_burgled_house', spawnX: 4, spawnY: 6 },
            ],
            npcs: [
                { name: 'Nurse Joy', type: 'nurse', x: 4, y: 6, dir: 0,
                  dialogue: ['Welcome to the Cerulean Pokemon Center!', 'Let me heal your Pokemon to full health.'] },
                { name: 'Shopkeeper', type: 'shopkeeper', x: 14, y: 6, dir: 0,
                  dialogue: ['Welcome to the Poke Mart!', 'We have Great Balls and Super Potions in stock.'] },
                { name: 'Fisher', type: 'townsfolk', x: 19, y: 18, dir: 0,
                  dialogue: ['The water here is crystal clear.', 'I hear rare Water Pokemon live in this pond!'] },
                { name: 'Bike Fan', type: 'townsfolk', x: 10, y: 15, dir: 3,
                  dialogue: ['The Bike Shop here is famous!', 'A bicycle costs 1,000,000... but they have a voucher deal.'] },
                { name: 'Swimmer', type: 'townsfolk', x: 22, y: 12, dir: 2,
                  dialogue: ['Misty is the Gym Leader here.', 'She uses Water-type Pokemon. Watch out for her Starmie!'] },
            ],
            lamps: [{ x: 8, y: 6 }, { x: 16, y: 6 }, { x: 12, y: 12 }, { x: 20, y: 18 }],
        });

        const route24 = buildRoute24();
        MapLoader.registerMap('route_24', {
            name: 'Route 24 - Nugget Bridge',
            width: route24.width,
            height: route24.height,
            data: route24.data,
            exits: [
                { edge: 'south', targetMap: 'cerulean_city', spawnX: 12, spawnY: 1, spawnDir: 0 },
                { edge: 'north', targetMap: 'route_25', spawnX: 5, spawnY: 18, spawnDir: 1 },
            ],
            trainers: nuggetBridgeTrainers,
            lamps: [{ x: 5, y: 10 }, { x: 5, y: 20 }, { x: 5, y: 30 }],
        });

        const route25 = buildRoute25();
        MapLoader.registerMap('route_25', {
            name: 'Route 25',
            width: route25.width,
            height: route25.height,
            data: route25.data,
            exits: [
                { edge: 'south', targetMap: 'route_24', spawnX: 5, spawnY: 1, spawnDir: 0 },
            ],
            doors: [
                { x: 27, y: 7, targetMap: 'bills_house', spawnX: 4, spawnY: 6 },
            ],
            trainers: route25Trainers,
            lamps: [{ x: 10, y: 8 }, { x: 20, y: 10 }],
        });

        const billsHouse = buildBillsHouse();
        MapLoader.registerMap('bills_house', {
            name: 'Bill\'s House',
            width: billsHouse.width,
            height: billsHouse.height,
            data: billsHouse.data,
            doors: [
                { x: 4, y: 7, targetMap: 'route_25', spawnX: 27, spawnY: 8 },
            ],
            npcs: [
                { name: 'Bill', type: 'townsfolk', x: 4, y: 3, dir: 0,
                  dialogue: ['Help! I was experimenting with my Cell Separation System and got merged with a Pokemon!',
                             'Please run the Cell Separation System on my PC to change me back!'] },
            ],
        });

        const route5 = buildRoute5();
        MapLoader.registerMap('route_5', {
            name: 'Route 5',
            width: route5.width,
            height: route5.height,
            data: route5.data,
            exits: [
                { edge: 'north', targetMap: 'cerulean_city', spawnX: 12, spawnY: 23, spawnDir: 1 },
            ],
            doors: [
                { x: 10, y: 23, targetMap: 'underground_path', spawnX: 1, spawnY: 1 },
            ],
            lamps: [{ x: 10, y: 10 }, { x: 10, y: 20 }],
        });

        const undergroundPath = buildUndergroundPath();
        MapLoader.registerMap('underground_path', {
            name: 'Underground Path',
            width: undergroundPath.width,
            height: undergroundPath.height,
            data: undergroundPath.data,
            doors: [
                { x: 1, y: 0, targetMap: 'route_5', spawnX: 10, spawnY: 22 },
                { x: 2, y: 0, targetMap: 'route_5', spawnX: 10, spawnY: 22 },
                { x: 1, y: 29, targetMap: 'route_6', spawnX: 10, spawnY: 2 },
                { x: 2, y: 29, targetMap: 'route_6', spawnX: 10, spawnY: 2 },
            ],
        });

        const route6 = buildRoute6();
        MapLoader.registerMap('route_6', {
            name: 'Route 6',
            width: route6.width,
            height: route6.height,
            data: route6.data,
            doors: [
                { x: 10, y: 3, targetMap: 'underground_path', spawnX: 1, spawnY: 28 },
                { x: 10, y: 24, targetMap: 'vermilion_gate', spawnX: 4, spawnY: 7 },
            ],
            trainers: route6Trainers,
            lamps: [{ x: 10, y: 10 }, { x: 10, y: 20 }],
        });

        const burgledHouse = buildCeruleanBurgledHouse();
        MapLoader.registerMap('cerulean_burgled_house', {
            name: 'Burgled House',
            width: burgledHouse.width,
            height: burgledHouse.height,
            data: burgledHouse.data,
            doors: [
                { x: 4, y: 7, targetMap: 'cerulean_city', spawnX: 20, spawnY: 20 },
            ],
            npcs: [
                { name: 'House Owner', type: 'townsfolk', x: 2, y: 4, dir: 0,
                  dialogue: ['Someone broke in and stole my TM!', 'I think it was a Team Rocket member...', 'They ran off toward Route 5!'] },
            ],
        });
    }

    return {
        buildRoute1,
        buildRoute2,
        buildRoute4,
        buildRoute5,
        buildRoute6,
        buildRoute24,
        buildRoute25,
        buildBillsHouse,
        buildUndergroundPath,
        buildCeruleanBurgledHouse,
        buildPalletTown,
        buildViridianCity,
        buildPewterCity,
        buildCeruleanCity,
        registerAll,
        route1Trainers,
        route2Trainers,
        route4Trainers,
        route6Trainers,
        nuggetBridgeTrainers,
        route25Trainers,
    };
})();
