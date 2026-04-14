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

    // --- Sprint 13: Vermilion City & S.S. Anne maps ---

    // Build Vermilion City (30x25)
    function buildVermilionCity() {
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

        // Main roads: horizontal through center, vertical from north
        for (let x = 1; x < W - 1; x++) { m[12][x] = T.DIRT; m[13][x] = T.DIRT; }
        for (let y = 1; y < H - 1; y++) { m[y][14] = T.DIRT; m[y][15] = T.DIRT; }

        // Pokemon Center (top-left area)
        buildHouse(m, 6, 7, 5, 4);

        // Pokemart (top-center)
        buildHouse(m, 14, 7, 5, 4);

        // Pokemon Fan Club (top-right)
        buildHouse(m, 22, 7, 5, 4);

        // Vermilion Gym (bottom-left, larger — Lightning bolt aesthetic)
        for (let x = 5; x <= 10; x++) {
            m[16][x] = T.HOUSE_ROOF; m[17][x] = T.HOUSE_ROOF;
            m[18][x] = T.HOUSE_WALL;
        }
        m[18][8] = T.DOOR;

        // Dock building (bottom-right)
        for (let x = 20; x <= 26; x++) {
            m[18][x] = T.HOUSE_ROOF; m[19][x] = T.HOUSE_ROOF;
            m[20][x] = T.HOUSE_WALL;
        }
        m[20][23] = T.DOOR;

        // Diglett's Cave entrance (top-left corner)
        m[2][2] = T.HOUSE_WALL; m[2][3] = T.HOUSE_WALL; m[2][4] = T.HOUSE_WALL;
        m[3][2] = T.HOUSE_WALL; m[3][4] = T.HOUSE_WALL;
        m[3][3] = T.DOOR;

        // Residential house (bottom-center)
        buildHouse(m, 13, 16, 4, 3);

        // Water feature — port area at bottom
        for (let y = 22; y <= 23; y++) {
            for (let x = 18; x <= 28; x++) {
                m[y][x] = T.WATER;
            }
        }

        // Flowers around gym
        m[15][4] = T.FLOWER; m[15][11] = T.FLOWER;
        m[14][7] = T.FLOWER; m[14][9] = T.FLOWER;

        // Rocks
        m[20][3] = T.ROCK; m[20][12] = T.ROCK;

        // Exit north (to Route 6)
        m[0][14] = T.DIRT; m[0][15] = T.DIRT;

        // Exit east (to Route 11)
        m[12][W - 1] = T.DIRT; m[13][W - 1] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Vermilion Pokemon Center interior (8x8)
    function buildVermilionPokemonCenter() {
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
        // Counter
        m[2][3] = T.HOUSE_WALL; m[2][4] = T.HOUSE_WALL; m[2][5] = T.HOUSE_WALL;
        // Door
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Vermilion Pokemart interior (8x8)
    function buildVermilionPokemart() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Shelves
        m[2][1] = T.ROCK; m[2][2] = T.ROCK;
        m[4][1] = T.ROCK; m[4][2] = T.ROCK;
        // Counter
        m[2][5] = T.HOUSE_WALL; m[2][6] = T.HOUSE_WALL;
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Pokemon Fan Club interior (8x8)
    function buildVermilionFanClub() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Table and chairs
        m[3][3] = T.ROCK; m[3][4] = T.ROCK;
        m[5][2] = T.ROCK; m[5][5] = T.ROCK;
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Vermilion Gym interior (10x12) with trash can puzzle area
    function buildVermilionGymInterior() {
        const W = 10, H = 12;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Electric-themed floor pattern (alternating)
        for (let y = 3; y <= 9; y++) {
            for (let x = 1; x <= 8; x++) {
                if ((x + y) % 3 === 0) m[y][x] = T.FLOWER;
            }
        }
        // Lt. Surge platform
        m[1][4] = T.ROCK; m[1][5] = T.ROCK; m[1][6] = T.ROCK;
        // Door
        m[H - 1][5] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Vermilion Dock interior (12x8)
    function buildVermilionDock() {
        const W = 12, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Dock walkway to ship
        for (let x = 7; x <= 10; x++) { m[3][x] = T.DIRT; }
        // Water on sides
        for (let y = 1; y <= 2; y++) {
            for (let x = 1; x <= 4; x++) m[y][x] = T.WATER;
            for (let x = 8; x <= 10; x++) m[y][x] = T.WATER;
        }
        // Gate
        m[3][5] = T.HOUSE_WALL; m[3][6] = T.HOUSE_WALL;
        // Ship entry
        m[3][10] = T.DOOR;
        // Exit
        m[H - 1][6] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Diglett's Cave entrance (6x6)
    function buildDiglettsCaveEntrance() {
        const W = 6, H = 6;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.ROCK);
            m.push(row);
        }
        // Cave interior path
        for (let y = 1; y <= 4; y++) {
            for (let x = 1; x <= 4; x++) m[y][x] = T.DIRT;
        }
        // Ladder (door) to deeper cave
        m[1][3] = T.DOOR;
        // Exit
        m[5][3] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // S.S. Anne Deck (20x10) — top deck with railings
    function buildSSAnneDeck() {
        const W = 20, H = 10;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        // Railing (water visible beyond)
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Water below the ship
        for (let x = 0; x < W; x++) { m[H - 1][x] = T.WATER; }
        // Stairs down to cabins
        m[0][10] = T.DOOR;
        // Captain's quarters door
        m[0][18] = T.DOOR;
        // Exit — gangway
        m[H - 1][2] = T.DOOR;
        // Decorative life rings
        m[4][4] = T.ROCK; m[4][15] = T.ROCK;
        return { data: m, width: W, height: H };
    }

    // S.S. Anne Cabins (20x12) — rooms with beds
    function buildSSAnneCabins() {
        const W = 20, H = 12;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Cabin walls dividing rooms
        for (let y = 1; y <= 5; y++) { m[y][7] = T.HOUSE_WALL; m[y][13] = T.HOUSE_WALL; }
        // Beds (rocks as furniture)
        m[2][2] = T.ROCK; m[2][3] = T.ROCK;
        m[2][9] = T.ROCK; m[2][10] = T.ROCK;
        m[2][15] = T.ROCK; m[2][16] = T.ROCK;
        // Hallway
        for (let x = 1; x < W - 1; x++) { m[7][x] = T.DIRT; m[8][x] = T.DIRT; }
        // Doors from hallway to cabins
        m[6][3] = T.DOOR; m[6][10] = T.DOOR; m[6][16] = T.DOOR;
        // Stairs up to deck
        m[H - 1][10] = T.DOOR;
        // Door to kitchen
        m[0][1] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // S.S. Anne Kitchen (10x8)
    function buildSSAnneKitchen() {
        const W = 10, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Counters/stoves
        m[1][1] = T.ROCK; m[1][2] = T.ROCK; m[1][3] = T.ROCK;
        m[1][6] = T.ROCK; m[1][7] = T.ROCK; m[1][8] = T.ROCK;
        // Table
        m[4][4] = T.ROCK; m[4][5] = T.ROCK;
        // Door
        m[H - 1][5] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // S.S. Anne Captain's Room (8x6) — small quarters
    function buildSSAnneCaptainsRoom() {
        const W = 8, H = 6;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Captain's desk
        m[1][5] = T.ROCK; m[1][6] = T.ROCK;
        // Bed
        m[3][1] = T.ROCK; m[3][2] = T.ROCK;
        // Door
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Build Route 11 (30x20) — east of Vermilion
    function buildRoute11() {
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

        // Main path
        for (let x = 0; x < W; x++) { m[9][x] = T.DIRT; m[10][x] = T.DIRT; m[11][x] = T.DIRT; }

        // Tall grass patches
        for (let y = 3; y <= 7; y++) {
            for (let x = 4; x <= 10; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 13; y <= 17; y++) {
            for (let x = 15; x <= 24; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 4; y <= 7; y++) {
            for (let x = 18; x <= 24; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }

        // Rocks
        m[5][14] = T.ROCK; m[14][8] = T.ROCK; m[8][22] = T.ROCK;

        // Trees
        m[6][13] = T.TREE; m[15][12] = T.TREE; m[3][25] = T.TREE;

        // Flowers
        m[13][5] = T.FLOWER; m[7][20] = T.FLOWER;

        // Exit west
        m[9][0] = T.DIRT; m[10][0] = T.DIRT; m[11][0] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Route 11 trainers
    const route11Trainers = [
        { x: 8, y: 8, name: 'Youngster Dave', dir: 0, sightRange: 3,
          dialogue: ['I train out here every day!'],
          pokemon: [
            { name: 'Ekans', level: 21, hp: 44, maxHp: 44, type: 'Poison' },
            { name: 'Sandshrew', level: 21, hp: 46, maxHp: 46, type: 'Ground' },
          ] },
        { x: 16, y: 12, name: 'Gambler Stan', dir: 2, sightRange: 4,
          dialogue: ['Feeling lucky, kid?'],
          pokemon: [
            { name: 'Voltorb', level: 22, hp: 42, maxHp: 42, type: 'Electric' },
            { name: 'Magnemite', level: 22, hp: 40, maxHp: 40, type: 'Electric' },
          ] },
        { x: 24, y: 6, name: 'Bug Catcher Rod', dir: 0, sightRange: 3,
          dialogue: ['Check out my bug collection!'],
          pokemon: [
            { name: 'Venonat', level: 20, hp: 50, maxHp: 50, type: 'Bug' },
          ] },
    ];

    // S.S. Anne trainers
    const ssAnneTrainers = [
        { x: 6, y: 4, name: 'Gentleman Arthur', dir: 0, sightRange: 2,
          dialogue: ['A fine day for a cruise, wouldn\'t you say?'],
          pokemon: [
            { name: 'Growlithe', level: 19, hp: 44, maxHp: 44, type: 'Fire' },
          ] },
        { x: 14, y: 6, name: 'Lass Ann', dir: 2, sightRange: 3,
          dialogue: ['This ship is so romantic!'],
          pokemon: [
            { name: 'Oddish', level: 18, hp: 38, maxHp: 38, type: 'Grass' },
            { name: 'Pidgey', level: 18, hp: 34, maxHp: 34, type: 'Flying' },
          ] },
        { x: 5, y: 4, name: 'Youngster Tyler', dir: 3, sightRange: 2,
          dialogue: ['I snuck on board without a ticket!'],
          pokemon: [
            { name: 'Rattata', level: 20, hp: 36, maxHp: 36, type: 'Normal' },
          ] },
        { x: 15, y: 8, name: 'Sailor Huey', dir: 2, sightRange: 3,
          dialogue: ['I\'ve sailed the seven seas!'],
          pokemon: [
            { name: 'Machop', level: 20, hp: 48, maxHp: 48, type: 'Fighting' },
            { name: 'Machop', level: 20, hp: 48, maxHp: 48, type: 'Fighting' },
          ] },
        { x: 5, y: 4, name: 'Sailor Eddie', dir: 0, sightRange: 2,
          dialogue: ['The kitchen is off-limits to passengers!'],
          pokemon: [
            { name: 'Machop', level: 21, hp: 50, maxHp: 50, type: 'Fighting' },
          ] },
    ];

    // --- Sprint 14: Lavender Town, Pokemon Tower, Routes 7/8/12 ---

    // Build Lavender Town (20x20) — eerie town with Pokemon Tower
    function buildLavenderTown() {
        const W = 20, H = 20;
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
        for (let y = 1; y < H - 1; y++) { m[y][10] = T.DIRT; }

        // Pokemon Center
        buildHouse(m, 4, 5, 5, 4);

        // Pokemart
        buildHouse(m, 12, 5, 5, 4);

        // Pokemon Tower (large building, top-right)
        for (let x = 12; x <= 17; x++) {
            m[1][x] = T.HOUSE_ROOF; m[2][x] = T.HOUSE_ROOF;
            m[3][x] = T.HOUSE_WALL; m[4][x] = T.HOUSE_WALL;
        }
        m[4][15] = T.DOOR;

        // Volunteer House (Mr. Fuji's house)
        buildHouse(m, 4, 13, 5, 4);

        // Eerie purple flowers scattered
        m[7][3] = T.FLOWER; m[7][4] = T.FLOWER;
        m[7][16] = T.FLOWER; m[7][17] = T.FLOWER;
        m[14][15] = T.FLOWER; m[14][16] = T.FLOWER;
        m[18][3] = T.FLOWER; m[18][8] = T.FLOWER;

        // Rocks (grave markers)
        m[13][13] = T.ROCK; m[13][15] = T.ROCK; m[13][17] = T.ROCK;

        // Exit west (to Route 8)
        m[10][0] = T.DIRT; m[11][0] = T.DIRT;

        // Exit south (to Route 12)
        m[H - 1][10] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Lavender Pokemon Center (8x8)
    function buildLavenderPokemonCenter() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        m[2][3] = T.HOUSE_WALL; m[2][4] = T.HOUSE_WALL; m[2][5] = T.HOUSE_WALL;
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Lavender Pokemart (8x8)
    function buildLavenderPokemart() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        m[2][1] = T.ROCK; m[2][2] = T.ROCK;
        m[4][1] = T.ROCK; m[4][2] = T.ROCK;
        m[2][5] = T.HOUSE_WALL; m[2][6] = T.HOUSE_WALL;
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Volunteer House — Mr. Fuji's home (8x8)
    function buildVolunteerHouse() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Table
        m[3][3] = T.ROCK; m[3][4] = T.ROCK;
        // Bookshelves
        m[1][1] = T.ROCK; m[1][2] = T.ROCK;
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Pokemon Tower 1F — lobby (12x12)
    function buildPokemonTower1F() {
        const W = 12, H = 12;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Tombstones in lobby
        m[3][3] = T.ROCK; m[3][5] = T.ROCK; m[3][7] = T.ROCK;
        m[5][4] = T.ROCK; m[5][6] = T.ROCK; m[5][8] = T.ROCK;
        // Stairs up
        m[0][9] = T.DOOR;
        // Exit
        m[H - 1][6] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Pokemon Tower 2F (12x12)
    function buildPokemonTower2F() {
        const W = 12, H = 12;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Dense tombstones
        for (let y = 2; y <= 8; y += 2) {
            for (let x = 2; x <= 9; x += 2) {
                m[y][x] = T.ROCK;
            }
        }
        // Stairs
        m[0][9] = T.DOOR;   // up
        m[H - 1][9] = T.DOOR; // down
        return { data: m, width: W, height: H };
    }

    // Pokemon Tower 3F (12x12)
    function buildPokemonTower3F() {
        const W = 12, H = 12;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // More tombstones — scattered pattern
        m[2][2] = T.ROCK; m[2][5] = T.ROCK; m[2][8] = T.ROCK;
        m[4][3] = T.ROCK; m[4][7] = T.ROCK;
        m[6][2] = T.ROCK; m[6][5] = T.ROCK; m[6][9] = T.ROCK;
        m[8][4] = T.ROCK; m[8][7] = T.ROCK;
        // Stairs
        m[0][9] = T.DOOR;   // up
        m[H - 1][9] = T.DOOR; // down
        return { data: m, width: W, height: H };
    }

    // Pokemon Tower Top Floor (12x12) — Mr. Fuji and Rockets
    function buildPokemonTowerTop() {
        const W = 12, H = 12;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Open space for boss fight area
        // Altar/shrine
        m[1][5] = T.ROCK; m[1][6] = T.ROCK;
        m[2][4] = T.ROCK; m[2][7] = T.ROCK;
        // Stairs down
        m[H - 1][9] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Build Route 7 (20x10) — short connector west of Lavender
    function buildRoute7() {
        const W = 20, H = 10;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        // Path through center
        for (let x = 0; x < W; x++) { m[4][x] = T.DIRT; m[5][x] = T.DIRT; }
        // Trees
        m[2][5] = T.TREE; m[2][14] = T.TREE;
        m[7][8] = T.TREE; m[7][12] = T.TREE;
        // Flowers
        m[3][3] = T.FLOWER; m[3][16] = T.FLOWER;
        m[6][10] = T.FLOWER;
        // Exit east (to route_8)
        m[4][W - 1] = T.DIRT; m[5][W - 1] = T.DIRT;
        return { data: m, width: W, height: H };
    }

    // Build Route 8 (30x20) — between Route 7 and Lavender
    function buildRoute8() {
        const W = 30, H = 20;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        for (let y = 0; y < H; y++) { m[y][0] = T.TREE; }
        // Main path
        for (let x = 0; x < W; x++) { m[9][x] = T.DIRT; m[10][x] = T.DIRT; m[11][x] = T.DIRT; }
        // Tall grass
        for (let y = 3; y <= 7; y++) {
            for (let x = 5; x <= 12; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 13; y <= 17; y++) {
            for (let x = 16; x <= 24; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        // Rocks
        m[5][18] = T.ROCK; m[14][7] = T.ROCK;
        // Trees
        m[6][22] = T.TREE; m[15][10] = T.TREE;
        // Exit west
        m[9][0] = T.DIRT; m[10][0] = T.DIRT; m[11][0] = T.DIRT;
        // Exit east
        m[9][W - 1] = T.DIRT; m[10][W - 1] = T.DIRT; m[11][W - 1] = T.DIRT;
        return { data: m, width: W, height: H };
    }

    // Build Route 12 (15x35) — vertical route south of Lavender with Snorlax
    function buildRoute12() {
        const W = 15, H = 35;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }
        for (let y = 0; y < H; y++) { m[y][0] = T.TREE; m[y][W - 1] = T.TREE; }
        // Main path
        for (let y = 0; y < H; y++) { m[y][7] = T.DIRT; }
        // Snorlax blockade (rock standing in for sleeping Snorlax)
        m[15][6] = T.ROCK; m[15][7] = T.ROCK; m[15][8] = T.ROCK;
        // Tall grass patches
        for (let y = 3; y <= 8; y++) {
            for (let x = 2; x <= 5; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 20; y <= 27; y++) {
            for (let x = 9; x <= 13; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 10; y <= 13; y++) {
            for (let x = 9; x <= 12; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }
        // Water on east side (fishing spots)
        for (let y = 18; y <= 25; y++) {
            for (let x = 11; x <= 13; x++) {
                m[y][x] = T.WATER;
            }
        }
        // Rocks
        m[8][10] = T.ROCK; m[28][4] = T.ROCK;
        // Flowers
        m[5][10] = T.FLOWER; m[30][3] = T.FLOWER;
        // Exit north
        m[0][7] = T.DIRT;
        return { data: m, width: W, height: H };
    }

    // Route 8 trainers
    const route8Trainers = [
        { x: 8, y: 7, name: 'Lass Megan', dir: 0, sightRange: 3,
          dialogue: ['I love walking through the grass here!'],
          pokemon: [
            { name: 'Clefairy', level: 20, hp: 52, maxHp: 52, type: 'Normal' },
            { name: 'Jigglypuff', level: 20, hp: 50, maxHp: 50, type: 'Normal' },
          ] },
        { x: 18, y: 14, name: 'Super Nerd Glenn', dir: 2, sightRange: 4,
          dialogue: ['I study electromagnetic Pokemon!'],
          pokemon: [
            { name: 'Magnemite', level: 22, hp: 40, maxHp: 40, type: 'Electric' },
            { name: 'Voltorb', level: 22, hp: 42, maxHp: 42, type: 'Electric' },
          ] },
        { x: 24, y: 6, name: 'Gambler Rich', dir: 0, sightRange: 3,
          dialogue: ['Feeling lucky?'],
          pokemon: [
            { name: 'Growlithe', level: 21, hp: 44, maxHp: 44, type: 'Fire' },
            { name: 'Vulpix', level: 21, hp: 40, maxHp: 40, type: 'Fire' },
          ] },
    ];

    // Route 12 trainers
    const route12Trainers = [
        { x: 5, y: 6, name: 'Fisherman Andrew', dir: 3, sightRange: 3,
          dialogue: ['The fish are biting today!'],
          pokemon: [
            { name: 'Magikarp', level: 22, hp: 28, maxHp: 28, type: 'Water' },
            { name: 'Poliwag', level: 22, hp: 42, maxHp: 42, type: 'Water' },
            { name: 'Goldeen', level: 22, hp: 44, maxHp: 44, type: 'Water' },
          ] },
        { x: 4, y: 24, name: 'Youngster Ben', dir: 3, sightRange: 3,
          dialogue: ['I train here every day!'],
          pokemon: [
            { name: 'Rattata', level: 23, hp: 40, maxHp: 40, type: 'Normal' },
            { name: 'Raticate', level: 23, hp: 52, maxHp: 52, type: 'Normal' },
          ] },
    ];

    // Pokemon Tower channeler trainers
    const towerChannelers = [
        { x: 4, y: 5, name: 'Channeler Hope', dir: 0, sightRange: 2,
          dialogue: ['The spirits... they speak to me...'],
          pokemon: [{ name: 'Gastly', level: 22, hp: 34, maxHp: 34, type: 'Ghost' }] },
        { x: 8, y: 3, name: 'Channeler Patricia', dir: 2, sightRange: 2,
          dialogue: ['Ke ke ke ke!'],
          pokemon: [{ name: 'Gastly', level: 23, hp: 36, maxHp: 36, type: 'Ghost' }] },
        { x: 3, y: 7, name: 'Channeler Carly', dir: 3, sightRange: 2,
          dialogue: ['Be careful... the ghosts are restless...'],
          pokemon: [{ name: 'Gastly', level: 22, hp: 34, maxHp: 34, type: 'Ghost' }] },
        { x: 7, y: 6, name: 'Channeler Laurel', dir: 0, sightRange: 2,
          dialogue: ['The spirits wander these halls...'],
          pokemon: [{ name: 'Gastly', level: 24, hp: 38, maxHp: 38, type: 'Ghost' }] },
        { x: 5, y: 4, name: 'Channeler Tammy', dir: 1, sightRange: 2,
          dialogue: ['This place gives me chills...'],
          pokemon: [{ name: 'Haunter', level: 24, hp: 42, maxHp: 42, type: 'Ghost' }] },
    ];

    // ═══════════════════════════════════════════════
    //  Sprint 15: Celadon City, Game Corner, Erika's Gym, Routes 16 & Cycling Road
    // ═══════════════════════════════════════════════

    // Celadon City (30x30)
    function buildCeladonCity() {
        const W = 30, H = 30;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }

        // Tree border
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        for (let y = 0; y < H; y++) { m[y][0] = T.TREE; m[y][W - 1] = T.TREE; }

        // Main roads: horizontal mid, vertical through
        for (let x = 1; x < W - 1; x++) { m[14][x] = T.DIRT; m[15][x] = T.DIRT; }
        for (let y = 1; y < H - 1; y++) { m[y][14] = T.DIRT; m[y][15] = T.DIRT; }

        // Pokemon Center (left area)
        buildHouse(m, 5, 8, 4, 3);

        // Pokemart (center-left)
        buildHouse(m, 12, 8, 4, 3);

        // Department Store (large, upper-right)
        for (let x = 18; x <= 23; x++) {
            m[4][x] = T.HOUSE_ROOF; m[5][x] = T.HOUSE_ROOF;
            m[6][x] = T.HOUSE_WALL; m[7][x] = T.HOUSE_WALL;
        }
        m[7][20] = T.DOOR;

        // Game Corner (right side, middle)
        for (let x = 18; x <= 23; x++) {
            m[16][x] = T.HOUSE_ROOF; m[17][x] = T.HOUSE_ROOF;
            m[18][x] = T.HOUSE_WALL; m[19][x] = T.HOUSE_WALL;
        }
        m[19][20] = T.DOOR;

        // Celadon Gym (left side, lower — with flower garden)
        for (let x = 3; x <= 8; x++) {
            m[18][x] = T.HOUSE_ROOF; m[19][x] = T.HOUSE_ROOF;
            m[20][x] = T.HOUSE_WALL; m[21][x] = T.HOUSE_WALL;
        }
        m[21][5] = T.DOOR;
        // Flower garden around gym
        for (let x = 2; x <= 9; x++) { m[17][x] = T.FLOWER; m[22][x] = T.FLOWER; }
        for (let y = 18; y <= 21; y++) { m[y][2] = T.FLOWER; m[y][9] = T.FLOWER; }

        // Celadon Mansion (bottom center-left)
        buildHouse(m, 10, 22, 4, 3);

        // Celadon Condominiums (bottom right)
        buildHouse(m, 20, 22, 4, 3);

        // Decorative pond
        for (let y = 10; y <= 12; y++) {
            for (let x = 22; x <= 26; x++) m[y][x] = T.WATER;
        }

        // Flowers throughout
        m[3][5] = T.FLOWER; m[3][8] = T.FLOWER; m[3][12] = T.FLOWER;
        m[26][5] = T.FLOWER; m[26][10] = T.FLOWER; m[26][20] = T.FLOWER;

        // Rocks
        m[25][3] = T.ROCK; m[25][27] = T.ROCK;

        // Exit east (to Route 7)
        m[14][W - 1] = T.DIRT; m[15][W - 1] = T.DIRT;

        // Exit west (to Route 16)
        m[14][0] = T.DIRT; m[15][0] = T.DIRT;

        return { data: m, width: W, height: H };
    }

    // Celadon Pokemon Center (8x8)
    function buildCeladonPokemonCenter() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        m[2][3] = T.HOUSE_WALL; m[2][4] = T.HOUSE_WALL; m[2][5] = T.HOUSE_WALL;
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Celadon Pokemart (8x8)
    function buildCeladonPokemart() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        m[2][2] = T.HOUSE_WALL; m[2][3] = T.HOUSE_WALL;
        m[4][5] = T.HOUSE_WALL; m[4][6] = T.HOUSE_WALL;
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Celadon Department Store 1F (12x10)
    function buildCeladonDepartmentStore1F() {
        const W = 12, H = 10;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Counter
        for (let x = 3; x <= 8; x++) m[2][x] = T.HOUSE_WALL;
        // Shelves
        m[5][2] = T.HOUSE_WALL; m[5][3] = T.HOUSE_WALL;
        m[5][8] = T.HOUSE_WALL; m[5][9] = T.HOUSE_WALL;
        // Stairs up (right side)
        m[1][10] = T.DOOR;
        // Entrance
        m[H - 1][5] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Celadon Department Store 2F (12x10)
    function buildCeladonDepartmentStore2F() {
        const W = 12, H = 10;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Counter
        for (let x = 3; x <= 8; x++) m[2][x] = T.HOUSE_WALL;
        // TM display shelves
        m[5][2] = T.HOUSE_WALL; m[5][3] = T.HOUSE_WALL; m[5][4] = T.HOUSE_WALL;
        m[5][7] = T.HOUSE_WALL; m[5][8] = T.HOUSE_WALL; m[5][9] = T.HOUSE_WALL;
        // Stairs down (right side)
        m[H - 1][10] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Celadon Gym interior (12x12) — garden aesthetic with flowers
    function buildCeladonGym() {
        const W = 12, H = 12;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Dirt path to leader
        for (let y = 1; y < H - 1; y++) { m[y][5] = T.DIRT; m[y][6] = T.DIRT; }
        // Cut tree barriers (aesthetic only — use T.TREE as cut-tree stand-in)
        m[3][3] = T.TREE; m[3][8] = T.TREE;
        m[6][3] = T.TREE; m[6][8] = T.TREE;
        m[9][3] = T.TREE; m[9][8] = T.TREE;
        // Flower decorations
        m[2][2] = T.FLOWER; m[2][4] = T.FLOWER; m[2][7] = T.FLOWER; m[2][9] = T.FLOWER;
        m[5][2] = T.FLOWER; m[5][4] = T.FLOWER; m[5][7] = T.FLOWER; m[5][9] = T.FLOWER;
        m[8][2] = T.FLOWER; m[8][4] = T.FLOWER; m[8][7] = T.FLOWER; m[8][9] = T.FLOWER;
        // Entrance
        m[H - 1][5] = T.DOOR; m[H - 1][6] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Celadon Game Corner (14x12)
    function buildCeladonGameCorner() {
        const W = 14, H = 12;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Rows of slot machines (use ROCK as stand-in tiles)
        for (let x = 2; x <= 5; x++) { m[3][x] = T.ROCK; m[5][x] = T.ROCK; m[7][x] = T.ROCK; }
        for (let x = 8; x <= 11; x++) { m[3][x] = T.ROCK; m[5][x] = T.ROCK; m[7][x] = T.ROCK; }
        // Suspicious poster (Team Rocket hideout entrance hint)
        m[1][10] = T.HOUSE_ROOF;
        // Entrance
        m[H - 1][7] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Celadon Mansion (10x10)
    function buildCeladonMansion() {
        const W = 10, H = 10;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        // Furniture
        m[2][2] = T.HOUSE_WALL; m[2][3] = T.HOUSE_WALL;
        m[5][6] = T.HOUSE_WALL; m[5][7] = T.HOUSE_WALL;
        // Flowers inside
        m[3][5] = T.FLOWER; m[7][3] = T.FLOWER;
        m[H - 1][5] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Celadon Condominiums (8x8)
    function buildCeladonCondominiums() {
        const W = 8, H = 8;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.DIRT);
            m.push(row);
        }
        for (let x = 0; x < W; x++) { m[0][x] = T.HOUSE_WALL; m[H - 1][x] = T.HOUSE_WALL; }
        for (let y = 0; y < H; y++) { m[y][0] = T.HOUSE_WALL; m[y][W - 1] = T.HOUSE_WALL; }
        m[3][3] = T.HOUSE_WALL; m[3][4] = T.HOUSE_WALL;
        m[H - 1][4] = T.DOOR;
        return { data: m, width: W, height: H };
    }

    // Route 16 (20x15)
    function buildRoute16() {
        const W = 20, H = 15;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }
        // Tree borders
        for (let x = 0; x < W; x++) { m[0][x] = T.TREE; m[H - 1][x] = T.TREE; }
        for (let y = 0; y < H; y++) { m[y][0] = T.TREE; m[y][W - 1] = T.TREE; }
        // Main path
        for (let x = 1; x < W - 1; x++) { m[7][x] = T.DIRT; m[8][x] = T.DIRT; }
        // Tall grass patches
        for (let y = 3; y <= 5; y++) {
            for (let x = 3; x <= 8; x++) m[y][x] = T.TALL_GRASS;
        }
        for (let y = 9; y <= 12; y++) {
            for (let x = 11; x <= 16; x++) m[y][x] = T.TALL_GRASS;
        }
        // Fence/gate (rocks at entrance to cycling road)
        m[6][0] = T.ROCK; m[9][0] = T.ROCK;
        // Exit east (to Celadon City)
        m[7][W - 1] = T.DIRT; m[8][W - 1] = T.DIRT;
        // Exit west (to Cycling Road)
        m[7][0] = T.DIRT; m[8][0] = T.DIRT;
        return { data: m, width: W, height: H };
    }

    // Cycling Road (10x40) — long downhill route
    function buildCyclingRoad() {
        const W = 10, H = 40;
        const m = [];
        for (let y = 0; y < H; y++) {
            const row = [];
            for (let x = 0; x < W; x++) row.push(T.GRASS);
            m.push(row);
        }
        // Fence borders (rocks for guard rails)
        for (let y = 0; y < H; y++) { m[y][0] = T.ROCK; m[y][W - 1] = T.ROCK; }
        // Cycling lane (center, 4 tiles wide)
        for (let y = 0; y < H; y++) {
            for (let x = 3; x <= 6; x++) m[y][x] = T.DIRT;
        }
        // Lane markings (grass tiles periodically on the road edges)
        for (let y = 0; y < H; y += 5) {
            m[y][3] = T.GRASS;
            m[y][6] = T.GRASS;
        }
        // Tall grass along sides
        for (let y = 5; y <= 14; y++) { m[y][1] = T.TALL_GRASS; m[y][2] = T.TALL_GRASS; }
        for (let y = 25; y <= 34; y++) { m[y][7] = T.TALL_GRASS; m[y][8] = T.TALL_GRASS; }
        // Exit north
        m[0][4] = T.DIRT; m[0][5] = T.DIRT;
        // Exit south (future — connects to Fuchsia City area)
        m[H - 1][4] = T.DIRT; m[H - 1][5] = T.DIRT;
        return { data: m, width: W, height: H };
    }

    // Celadon trainers
    const celadonGymTrainers = [
        { x: 3, y: 5, name: 'Lass Lisa', dir: 3, sightRange: 3,
          dialogue: ['Our Gym Leader Erika is so elegant!'],
          pokemon: [
              { name: 'Bellsprout', level: 23, hp: 45, maxHp: 45, type: 'Grass' },
              { name: 'Weepinbell', level: 23, hp: 50, maxHp: 50, type: 'Grass' },
          ] },
        { x: 8, y: 5, name: 'Beauty Bridget', dir: 2, sightRange: 3,
          dialogue: ['Grass Pokemon are so beautiful!'],
          pokemon: [
              { name: 'Oddish', level: 24, hp: 46, maxHp: 46, type: 'Grass' },
              { name: 'Exeggcute', level: 24, hp: 52, maxHp: 52, type: 'Grass' },
          ] },
        { x: 5, y: 8, name: 'Lass Kay', dir: 0, sightRange: 3,
          dialogue: ['Do you know about Grass-type Pokemon?'],
          pokemon: [
              { name: 'Tangela', level: 26, hp: 54, maxHp: 54, type: 'Grass' },
          ] },
    ];

    const route16Trainers = [
        { x: 10, y: 7, name: 'Biker Lao', dir: 3, sightRange: 4,
          dialogue: ['You think you can take the Cycling Road? Ha!'],
          pokemon: [
              { name: 'Grimer', level: 25, hp: 52, maxHp: 52, type: 'Poison' },
              { name: 'Muk', level: 25, hp: 58, maxHp: 58, type: 'Poison' },
          ] },
        { x: 15, y: 5, name: 'Bird Keeper Boris', dir: 2, sightRange: 4,
          dialogue: ['My birds rule the skies of Route 16!'],
          pokemon: [
              { name: 'Pidgeotto', level: 26, hp: 54, maxHp: 54, type: 'Flying' },
              { name: 'Fearow', level: 26, hp: 56, maxHp: 56, type: 'Flying' },
          ] },
    ];

    const cyclingRoadTrainers = [
        { x: 5, y: 8, name: 'Biker Ruben', dir: 2, sightRange: 3,
          dialogue: ['Cycling Road belongs to us bikers!'],
          pokemon: [
              { name: 'Grimer', level: 26, hp: 54, maxHp: 54, type: 'Poison' },
              { name: 'Koffing', level: 26, hp: 50, maxHp: 50, type: 'Poison' },
          ] },
        { x: 5, y: 20, name: 'Biker Billy', dir: 3, sightRange: 3,
          dialogue: ['Three on one? That\'s how we roll!'],
          pokemon: [
              { name: 'Koffing', level: 25, hp: 48, maxHp: 48, type: 'Poison' },
              { name: 'Koffing', level: 25, hp: 48, maxHp: 48, type: 'Poison' },
              { name: 'Weezing', level: 27, hp: 56, maxHp: 56, type: 'Poison' },
          ] },
        { x: 5, y: 32, name: 'Biker Jaxon', dir: 2, sightRange: 3,
          dialogue: ['You made it this far? Not bad!'],
          pokemon: [
              { name: 'Muk', level: 28, hp: 62, maxHp: 62, type: 'Poison' },
          ] },
    ];

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
            exits: [
                { edge: 'south', targetMap: 'vermilion_city', spawnX: 14, spawnY: 1, spawnDir: 0 },
            ],
            doors: [
                { x: 10, y: 3, targetMap: 'underground_path', spawnX: 1, spawnY: 28 },
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

        // --- Sprint 13: Vermilion City ---

        const vermilionCity = buildVermilionCity();
        MapLoader.registerMap('vermilion_city', {
            name: 'Vermilion City',
            width: vermilionCity.width,
            height: vermilionCity.height,
            data: vermilionCity.data,
            exits: [
                { edge: 'north', targetMap: 'route_6', spawnX: 10, spawnY: 23, spawnDir: 1 },
                { edge: 'east', targetMap: 'route_11', spawnX: 1, spawnY: 10, spawnDir: 3 },
            ],
            doors: [
                { x: 8, y: 10, targetMap: 'vermilion_pokemon_center', spawnX: 4, spawnY: 6 },
                { x: 16, y: 10, targetMap: 'vermilion_pokemart', spawnX: 4, spawnY: 6 },
                { x: 24, y: 10, targetMap: 'vermilion_fan_club', spawnX: 4, spawnY: 6 },
                { x: 8, y: 19, targetMap: 'vermilion_gym_interior', spawnX: 5, spawnY: 10 },
                { x: 23, y: 21, targetMap: 'vermilion_dock', spawnX: 6, spawnY: 6 },
                { x: 3, y: 4, targetMap: 'digletts_cave_entrance', spawnX: 3, spawnY: 4 },
            ],
            lamps: [{ x: 6, y: 12 }, { x: 16, y: 12 }, { x: 24, y: 12 }, { x: 8, y: 22 }],
            npcs: [
                { name: 'Sailor', type: 'sailor', x: 22, y: 16, dir: 0,
                  dialogue: ['The S.S. Anne is docked at the port!', 'You need a ticket to board.'] },
                { name: 'Vermilion Fan', type: 'townsfolk', x: 12, y: 14, dir: 2,
                  dialogue: ['Lt. Surge is the Gym Leader here!', 'He uses Electric-type Pokemon.', 'Watch out for his trash can puzzle!'] },
                { name: 'Fisherman', type: 'townsfolk', x: 26, y: 4, dir: 0,
                  dialogue: ['Vermilion City is known as the Port of Exquisite Sunsets!'] },
            ],
        });

        const vermilionPC = buildVermilionPokemonCenter();
        MapLoader.registerMap('vermilion_pokemon_center', {
            name: 'Vermilion Pokemon Center',
            width: vermilionPC.width,
            height: vermilionPC.height,
            data: vermilionPC.data,
            doors: [
                { x: 4, y: 7, targetMap: 'vermilion_city', spawnX: 8, spawnY: 11 },
            ],
            npcs: [
                { name: 'Nurse Joy', type: 'nurse', x: 4, y: 2, dir: 0,
                  dialogue: ['Welcome to the Vermilion Pokemon Center!', 'We\'ll restore your Pokemon to full health.'] },
            ],
        });

        const vermilionMart = buildVermilionPokemart();
        MapLoader.registerMap('vermilion_pokemart', {
            name: 'Vermilion Pokemart',
            width: vermilionMart.width,
            height: vermilionMart.height,
            data: vermilionMart.data,
            doors: [
                { x: 4, y: 7, targetMap: 'vermilion_city', spawnX: 16, spawnY: 11 },
            ],
            npcs: [
                { name: 'Clerk', type: 'shopkeeper', x: 4, y: 2, dir: 0,
                  dialogue: ['Welcome to Vermilion Pokemart!', 'We stock Super Potions and Great Balls.'] },
            ],
        });

        const fanClub = buildVermilionFanClub();
        MapLoader.registerMap('vermilion_fan_club', {
            name: 'Pokemon Fan Club',
            width: fanClub.width,
            height: fanClub.height,
            data: fanClub.data,
            doors: [
                { x: 4, y: 7, targetMap: 'vermilion_city', spawnX: 24, spawnY: 11 },
            ],
            npcs: [
                { name: 'Fan Club Chairman', type: 'townsfolk', x: 4, y: 2, dir: 0,
                  dialogue: ['Welcome to the Pokemon Fan Club!', 'Let me tell you about my favorite Pokemon...', 'It\'s so cute! So adorable!', 'Here, take this Bike Voucher as thanks for listening!'] },
            ],
        });

        const gymInterior = buildVermilionGymInterior();
        MapLoader.registerMap('vermilion_gym_interior', {
            name: 'Vermilion Gym',
            width: gymInterior.width,
            height: gymInterior.height,
            data: gymInterior.data,
            doors: [
                { x: 5, y: 11, targetMap: 'vermilion_city', spawnX: 8, spawnY: 20 },
            ],
            npcs: [
                { name: 'Lt. Surge', type: 'lt_surge', x: 5, y: 1, dir: 0,
                  dialogue: ['Hey kid! You managed to solve my puzzle?', 'Not bad! But you won\'t beat my Electric Pokemon!'] },
            ],
        });

        const dock = buildVermilionDock();
        MapLoader.registerMap('vermilion_dock', {
            name: 'Vermilion Dock',
            width: dock.width,
            height: dock.height,
            data: dock.data,
            doors: [
                { x: 6, y: 7, targetMap: 'vermilion_city', spawnX: 23, spawnY: 22 },
                { x: 10, y: 3, targetMap: 'ss_anne_deck', spawnX: 2, spawnY: 8 },
            ],
            npcs: [
                { name: 'Dock Guard', type: 'gate_guard', x: 6, y: 3, dir: 0,
                  dialogue: ['You need an S.S. Ticket to board the ship!', 'Show your ticket and you may pass.'] },
            ],
        });

        const caveEntrance = buildDiglettsCaveEntrance();
        MapLoader.registerMap('digletts_cave_entrance', {
            name: 'Diglett\'s Cave',
            width: caveEntrance.width,
            height: caveEntrance.height,
            data: caveEntrance.data,
            doors: [
                { x: 3, y: 5, targetMap: 'vermilion_city', spawnX: 3, spawnY: 5 },
            ],
        });

        // --- S.S. Anne rooms ---

        const ssAnneDeck = buildSSAnneDeck();
        MapLoader.registerMap('ss_anne_deck', {
            name: 'S.S. Anne - Deck',
            width: ssAnneDeck.width,
            height: ssAnneDeck.height,
            data: ssAnneDeck.data,
            doors: [
                { x: 2, y: 9, targetMap: 'vermilion_dock', spawnX: 10, spawnY: 4 },
                { x: 10, y: 0, targetMap: 'ss_anne_cabins', spawnX: 10, spawnY: 11 },
                { x: 18, y: 0, targetMap: 'ss_anne_captains_room', spawnX: 4, spawnY: 4 },
            ],
            trainers: ssAnneTrainers.slice(0, 2),
        });

        const ssAnneCabins = buildSSAnneCabins();
        MapLoader.registerMap('ss_anne_cabins', {
            name: 'S.S. Anne - Cabins',
            width: ssAnneCabins.width,
            height: ssAnneCabins.height,
            data: ssAnneCabins.data,
            doors: [
                { x: 10, y: 11, targetMap: 'ss_anne_deck', spawnX: 10, spawnY: 1 },
                { x: 1, y: 0, targetMap: 'ss_anne_kitchen', spawnX: 5, spawnY: 7 },
            ],
            trainers: ssAnneTrainers.slice(2, 4),
            npcs: [
                { name: 'Passenger', type: 'townsfolk', x: 4, y: 3, dir: 0,
                  dialogue: ['This ship is wonderful!', 'I hear the Captain isn\'t feeling well though...'] },
                { name: 'Passenger', type: 'townsfolk', x: 16, y: 8, dir: 2,
                  dialogue: ['Have you explored the kitchen?', 'The food here is amazing!'] },
            ],
        });

        const ssAnneKitchen = buildSSAnneKitchen();
        MapLoader.registerMap('ss_anne_kitchen', {
            name: 'S.S. Anne - Kitchen',
            width: ssAnneKitchen.width,
            height: ssAnneKitchen.height,
            data: ssAnneKitchen.data,
            doors: [
                { x: 5, y: 7, targetMap: 'ss_anne_cabins', spawnX: 1, spawnY: 1 },
            ],
            trainers: ssAnneTrainers.slice(4, 5),
            npcs: [
                { name: 'Chef', type: 'townsfolk', x: 3, y: 2, dir: 0,
                  dialogue: ['I\'m preparing a feast for the passengers!', 'Don\'t touch anything!'] },
            ],
        });

        const captainsRoom = buildSSAnneCaptainsRoom();
        MapLoader.registerMap('ss_anne_captains_room', {
            name: 'Captain\'s Room',
            width: captainsRoom.width,
            height: captainsRoom.height,
            data: captainsRoom.data,
            doors: [
                { x: 4, y: 5, targetMap: 'ss_anne_deck', spawnX: 18, spawnY: 1 },
            ],
            npcs: [
                { name: 'Captain', type: 'captain', x: 4, y: 2, dir: 0,
                  dialogue: ['Urp... I feel seasick...', 'Could you rub my back?', 'Thank you! I feel much better now.', 'Here, take this HM01 Cut as thanks!'] },
            ],
        });

        // --- Route 11 ---

        const route11 = buildRoute11();
        MapLoader.registerMap('route_11', {
            name: 'Route 11',
            width: route11.width,
            height: route11.height,
            data: route11.data,
            exits: [
                { edge: 'west', targetMap: 'vermilion_city', spawnX: 28, spawnY: 12, spawnDir: 2 },
            ],
            trainers: route11Trainers,
            lamps: [{ x: 10, y: 10 }, { x: 20, y: 10 }],
        });

        // --- Sprint 14: Lavender Town & Pokemon Tower ---

        const lavenderTown = buildLavenderTown();
        MapLoader.registerMap('lavender_town', {
            name: 'Lavender Town',
            width: lavenderTown.width,
            height: lavenderTown.height,
            data: lavenderTown.data,
            exits: [
                { edge: 'west', targetMap: 'route_8', spawnX: 28, spawnY: 10, spawnDir: 2 },
                { edge: 'south', targetMap: 'route_12', spawnX: 7, spawnY: 1, spawnDir: 0 },
            ],
            doors: [
                { x: 6, y: 8, targetMap: 'lavender_pokemon_center', spawnX: 4, spawnY: 6 },
                { x: 14, y: 8, targetMap: 'lavender_pokemart', spawnX: 4, spawnY: 6 },
                { x: 6, y: 16, targetMap: 'lavender_volunteer_house', spawnX: 4, spawnY: 6 },
                { x: 15, y: 4, targetMap: 'pokemon_tower_1f', spawnX: 6, spawnY: 10 },
            ],
            lamps: [{ x: 6, y: 10 }, { x: 14, y: 10 }, { x: 10, y: 16 }],
            npcs: [
                { name: 'Old Woman', type: 'townsfolk', x: 8, y: 14, dir: 0,
                  dialogue: ['This town is haunted...', 'Strange sounds come from Pokemon Tower at night.'] },
                { name: 'Name Rater', type: 'townsfolk', x: 12, y: 12, dir: 2,
                  dialogue: ['I\'m the Name Rater!', 'Want me to rate your Pokemon\'s nickname?', 'Hmm... that\'s a good name!'] },
                { name: 'Mourner', type: 'townsfolk', x: 16, y: 14, dir: 1,
                  dialogue: ['My poor Cubone...', 'Its mother was taken from it...'] },
            ],
        });

        const lavPC = buildLavenderPokemonCenter();
        MapLoader.registerMap('lavender_pokemon_center', {
            name: 'Lavender Pokemon Center',
            width: lavPC.width,
            height: lavPC.height,
            data: lavPC.data,
            doors: [
                { x: 4, y: 7, targetMap: 'lavender_town', spawnX: 6, spawnY: 9 },
            ],
            npcs: [
                { name: 'Nurse Joy', type: 'nurse', x: 4, y: 2, dir: 0,
                  dialogue: ['Welcome to Lavender Town Pokemon Center!', 'We\'ll heal your Pokemon.'] },
            ],
        });

        const lavMart = buildLavenderPokemart();
        MapLoader.registerMap('lavender_pokemart', {
            name: 'Lavender Pokemart',
            width: lavMart.width,
            height: lavMart.height,
            data: lavMart.data,
            doors: [
                { x: 4, y: 7, targetMap: 'lavender_town', spawnX: 14, spawnY: 9 },
            ],
            npcs: [
                { name: 'Clerk', type: 'shopkeeper', x: 5, y: 2, dir: 0,
                  dialogue: ['Welcome to Lavender Pokemart!', 'We stock Revives and Full Heals.'] },
            ],
        });

        const volunteerHouse = buildVolunteerHouse();
        MapLoader.registerMap('lavender_volunteer_house', {
            name: 'Volunteer House',
            width: volunteerHouse.width,
            height: volunteerHouse.height,
            data: volunteerHouse.data,
            doors: [
                { x: 4, y: 7, targetMap: 'lavender_town', spawnX: 6, spawnY: 17 },
            ],
            npcs: [
                { name: 'Mr. Fuji', type: 'mr_fuji', x: 4, y: 3, dir: 0,
                  dialogue: ['I care for abandoned and orphaned Pokemon here.', 'The Pokemon Tower is sacred...', 'The spirits are restless lately.'] },
            ],
        });

        const tower1f = buildPokemonTower1F();
        MapLoader.registerMap('pokemon_tower_1f', {
            name: 'Pokemon Tower 1F',
            width: tower1f.width,
            height: tower1f.height,
            data: tower1f.data,
            doors: [
                { x: 6, y: 11, targetMap: 'lavender_town', spawnX: 15, spawnY: 5 },
                { x: 9, y: 0, targetMap: 'pokemon_tower_2f', spawnX: 9, spawnY: 10 },
            ],
        });

        const tower2f = buildPokemonTower2F();
        MapLoader.registerMap('pokemon_tower_2f', {
            name: 'Pokemon Tower 2F',
            width: tower2f.width,
            height: tower2f.height,
            data: tower2f.data,
            doors: [
                { x: 9, y: 11, targetMap: 'pokemon_tower_1f', spawnX: 9, spawnY: 1 },
                { x: 9, y: 0, targetMap: 'pokemon_tower_3f', spawnX: 9, spawnY: 10 },
            ],
            trainers: towerChannelers.slice(0, 2),
        });

        const tower3f = buildPokemonTower3F();
        MapLoader.registerMap('pokemon_tower_3f', {
            name: 'Pokemon Tower 3F',
            width: tower3f.width,
            height: tower3f.height,
            data: tower3f.data,
            doors: [
                { x: 9, y: 11, targetMap: 'pokemon_tower_2f', spawnX: 9, spawnY: 1 },
                { x: 9, y: 0, targetMap: 'pokemon_tower_top', spawnX: 9, spawnY: 10 },
            ],
            trainers: towerChannelers.slice(2, 5),
        });

        const towerTop = buildPokemonTowerTop();
        MapLoader.registerMap('pokemon_tower_top', {
            name: 'Pokemon Tower Top',
            width: towerTop.width,
            height: towerTop.height,
            data: towerTop.data,
            doors: [
                { x: 9, y: 11, targetMap: 'pokemon_tower_3f', spawnX: 9, spawnY: 1 },
            ],
            npcs: [
                { name: 'Mr. Fuji', type: 'mr_fuji', x: 5, y: 3, dir: 0,
                  dialogue: ['Thank you for saving me!', 'Those Team Rocket ruffians were holding me captive!', 'Please, come to my house. I have something for you.'] },
                { name: 'Rocket Grunt', type: 'rocket', x: 3, y: 6, dir: 3,
                  dialogue: ['Get out of our way!', 'Team Rocket has business here!'] },
                { name: 'Rocket Grunt', type: 'rocket', x: 8, y: 6, dir: 2,
                  dialogue: ['You dare challenge Team Rocket?', 'You\'ll regret this!'] },
            ],
        });

        // --- Routes 7, 8, 12 ---

        const route7 = buildRoute7();
        MapLoader.registerMap('route_7', {
            name: 'Route 7',
            width: route7.width,
            height: route7.height,
            data: route7.data,
            exits: [
                { edge: 'east', targetMap: 'route_8', spawnX: 1, spawnY: 10, spawnDir: 3 },
            ],
        });

        const route8 = buildRoute8();
        MapLoader.registerMap('route_8', {
            name: 'Route 8',
            width: route8.width,
            height: route8.height,
            data: route8.data,
            exits: [
                { edge: 'west', targetMap: 'route_7', spawnX: 18, spawnY: 5, spawnDir: 2 },
                { edge: 'east', targetMap: 'lavender_town', spawnX: 1, spawnY: 10, spawnDir: 3 },
            ],
            trainers: route8Trainers,
            lamps: [{ x: 10, y: 10 }, { x: 20, y: 10 }],
        });

        const route12 = buildRoute12();
        MapLoader.registerMap('route_12', {
            name: 'Route 12',
            width: route12.width,
            height: route12.height,
            data: route12.data,
            exits: [
                { edge: 'north', targetMap: 'lavender_town', spawnX: 10, spawnY: 18, spawnDir: 1 },
            ],
            trainers: route12Trainers,
            lamps: [{ x: 7, y: 8 }, { x: 7, y: 22 }],
            npcs: [
                { name: 'Snorlax Watcher', type: 'townsfolk', x: 4, y: 14, dir: 3,
                  dialogue: ['A huge Snorlax is sleeping on the road!', 'I wonder if there\'s a way to wake it up...', 'I heard a flute might do the trick.'] },
            ],
        });

        // --- Sprint 15: Celadon City & surroundings ---

        const celadonCity = buildCeladonCity();
        MapLoader.registerMap('celadon_city', {
            name: 'Celadon City',
            width: celadonCity.width,
            height: celadonCity.height,
            data: celadonCity.data,
            exits: [
                { edge: 'east', targetMap: 'route_7', spawnX: 1, spawnY: 5, spawnDir: 3 },
                { edge: 'west', targetMap: 'route_16', spawnX: 18, spawnY: 7, spawnDir: 2 },
            ],
            doors: [
                { x: 7, y: 10, targetMap: 'celadon_pokemon_center', spawnX: 4, spawnY: 6 },
                { x: 14, y: 10, targetMap: 'celadon_pokemart', spawnX: 4, spawnY: 6 },
                { x: 20, y: 7, targetMap: 'celadon_department_store_1f', spawnX: 5, spawnY: 8 },
                { x: 20, y: 19, targetMap: 'celadon_game_corner', spawnX: 7, spawnY: 10 },
                { x: 5, y: 21, targetMap: 'celadon_gym', spawnX: 5, spawnY: 10 },
                { x: 12, y: 24, targetMap: 'celadon_mansion', spawnX: 5, spawnY: 8 },
                { x: 22, y: 24, targetMap: 'celadon_condominiums', spawnX: 4, spawnY: 6 },
            ],
            npcs: [
                { name: 'Lass', type: 'townsfolk', x: 10, y: 12, dir: 0,
                  dialogue: ['Erika is so elegant! She\'s the Gym Leader here.', 'Her Grass Pokemon are really strong!'] },
                { name: 'Old Man', type: 'townsfolk', x: 22, y: 10, dir: 0,
                  dialogue: ['Celadon City is famous for its Department Store!', 'You can buy all sorts of items there.'] },
                { name: 'Suspicious Man', type: 'rocket', x: 20, y: 20, dir: 2,
                  dialogue: ['Move along, nothing to see here!', 'The Game Corner is totally legit...'] },
            ],
            lamps: [{ x: 8, y: 6 }, { x: 16, y: 6 }, { x: 8, y: 20 }, { x: 24, y: 12 }],
        });

        const celadonPC = buildCeladonPokemonCenter();
        MapLoader.registerMap('celadon_pokemon_center', {
            name: 'Celadon Pokemon Center',
            width: celadonPC.width,
            height: celadonPC.height,
            data: celadonPC.data,
            npcs: [
                { name: 'Nurse Joy', type: 'nurse', x: 4, y: 2, dir: 0,
                  dialogue: ['Welcome to the Pokemon Center!', 'We\'ll heal your Pokemon to full health.'] },
            ],
        });

        const celadonMart = buildCeladonPokemart();
        MapLoader.registerMap('celadon_pokemart', {
            name: 'Celadon Pokemart',
            width: celadonMart.width,
            height: celadonMart.height,
            data: celadonMart.data,
            npcs: [
                { name: 'Clerk', type: 'townsfolk', x: 4, y: 2, dir: 0,
                  dialogue: ['Welcome! We have a great selection.', 'For even more items, visit the Department Store!'] },
            ],
        });

        const deptStore1F = buildCeladonDepartmentStore1F();
        MapLoader.registerMap('celadon_department_store_1f', {
            name: 'Celadon Dept. Store 1F',
            width: deptStore1F.width,
            height: deptStore1F.height,
            data: deptStore1F.data,
            doors: [
                { x: 10, y: 1, targetMap: 'celadon_department_store_2f', spawnX: 10, spawnY: 8 },
            ],
            npcs: [
                { name: 'Shop Clerk', type: 'townsfolk', x: 5, y: 2, dir: 0,
                  dialogue: ['Welcome to the Celadon Department Store!', 'Take the stairs to browse each floor.'] },
            ],
        });

        const deptStore2F = buildCeladonDepartmentStore2F();
        MapLoader.registerMap('celadon_department_store_2f', {
            name: 'Celadon Dept. Store 2F',
            width: deptStore2F.width,
            height: deptStore2F.height,
            data: deptStore2F.data,
            doors: [
                { x: 10, y: 9, targetMap: 'celadon_department_store_1f', spawnX: 10, spawnY: 2 },
            ],
            npcs: [
                { name: 'Shop Clerk', type: 'townsfolk', x: 5, y: 2, dir: 0,
                  dialogue: ['This floor has TMs and special items!', 'We have a wide variety of TMs for sale.'] },
            ],
        });

        const celadonGym = buildCeladonGym();
        MapLoader.registerMap('celadon_gym', {
            name: 'Celadon City Gym',
            width: celadonGym.width,
            height: celadonGym.height,
            data: celadonGym.data,
            trainers: celadonGymTrainers,
            npcs: [
                { name: 'Erika', type: 'erika', x: 5, y: 2, dir: 0,
                  dialogue: ['Hello... I am Erika, the Gym Leader of Celadon.', 'I love Grass-type Pokemon.', 'Oh, you wish to challenge me? Very well.'] },
            ],
        });

        const gameCorner = buildCeladonGameCorner();
        MapLoader.registerMap('celadon_game_corner', {
            name: 'Celadon Game Corner',
            width: gameCorner.width,
            height: gameCorner.height,
            data: gameCorner.data,
            npcs: [
                { name: 'Gambler', type: 'townsfolk', x: 5, y: 5, dir: 3,
                  dialogue: ['I keep winning! Today\'s my lucky day!', 'Try the slot machines, you might get lucky!'] },
                { name: 'Suspicious Man', type: 'rocket', x: 10, y: 4, dir: 1,
                  dialogue: ['Hey! Don\'t go poking around the poster!', 'There\'s nothing behind it, I swear!'] },
            ],
        });

        const celadonMansion = buildCeladonMansion();
        MapLoader.registerMap('celadon_mansion', {
            name: 'Celadon Mansion',
            width: celadonMansion.width,
            height: celadonMansion.height,
            data: celadonMansion.data,
            npcs: [
                { name: 'Game Designer', type: 'townsfolk', x: 5, y: 3, dir: 0,
                  dialogue: ['I\'m the game designer!', 'I made this game. It\'s called Pokemon!'] },
                { name: 'Pokemon Collector', type: 'townsfolk', x: 3, y: 6, dir: 3,
                  dialogue: ['I collect rare Pokemon!', 'Would you like this Eevee? It can evolve into many different Pokemon!'] },
            ],
        });

        const celadonCondo = buildCeladonCondominiums();
        MapLoader.registerMap('celadon_condominiums', {
            name: 'Celadon Condominiums',
            width: celadonCondo.width,
            height: celadonCondo.height,
            data: celadonCondo.data,
            npcs: [
                { name: 'Tea Lady', type: 'townsfolk', x: 4, y: 3, dir: 0,
                  dialogue: ['Would you like some tea? It\'s very refreshing.', 'Tea is the best drink, don\'t you think?'] },
            ],
        });

        const route16 = buildRoute16();
        MapLoader.registerMap('route_16', {
            name: 'Route 16',
            width: route16.width,
            height: route16.height,
            data: route16.data,
            exits: [
                { edge: 'east', targetMap: 'celadon_city', spawnX: 1, spawnY: 14, spawnDir: 3 },
                { edge: 'west', targetMap: 'cycling_road', spawnX: 4, spawnY: 1, spawnDir: 0 },
            ],
            trainers: route16Trainers,
            lamps: [{ x: 10, y: 4 }, { x: 15, y: 10 }],
        });

        const cyclingRoad = buildCyclingRoad();
        MapLoader.registerMap('cycling_road', {
            name: 'Cycling Road',
            width: cyclingRoad.width,
            height: cyclingRoad.height,
            data: cyclingRoad.data,
            exits: [
                { edge: 'north', targetMap: 'route_16', spawnX: 10, spawnY: 13, spawnDir: 1 },
            ],
            trainers: cyclingRoadTrainers,
        });
    }

    return {
        buildRoute1,
        buildRoute2,
        buildRoute4,
        buildRoute5,
        buildRoute6,
        buildRoute7,
        buildRoute8,
        buildRoute11,
        buildRoute12,
        buildRoute24,
        buildRoute25,
        buildBillsHouse,
        buildUndergroundPath,
        buildCeruleanBurgledHouse,
        buildVermilionCity,
        buildVermilionPokemonCenter,
        buildVermilionPokemart,
        buildVermilionFanClub,
        buildVermilionGymInterior,
        buildVermilionDock,
        buildDiglettsCaveEntrance,
        buildSSAnneDeck,
        buildSSAnneCabins,
        buildSSAnneKitchen,
        buildSSAnneCaptainsRoom,
        buildLavenderTown,
        buildLavenderPokemonCenter,
        buildLavenderPokemart,
        buildVolunteerHouse,
        buildPokemonTower1F,
        buildPokemonTower2F,
        buildPokemonTower3F,
        buildPokemonTowerTop,
        buildCeladonCity,
        buildCeladonPokemonCenter,
        buildCeladonPokemart,
        buildCeladonDepartmentStore1F,
        buildCeladonDepartmentStore2F,
        buildCeladonGym,
        buildCeladonGameCorner,
        buildCeladonMansion,
        buildCeladonCondominiums,
        buildRoute16,
        buildCyclingRoad,
        buildPalletTown,
        buildViridianCity,
        buildPewterCity,
        buildCeruleanCity,
        registerAll,
        route1Trainers,
        route2Trainers,
        route4Trainers,
        route6Trainers,
        route8Trainers,
        route11Trainers,
        route12Trainers,
        ssAnneTrainers,
        towerChannelers,
        celadonGymTrainers,
        route16Trainers,
        cyclingRoadTrainers,
        nuggetBridgeTrainers,
        route25Trainers,
    };
})();
