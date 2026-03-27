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
        });
    }

    return {
        buildRoute1,
        buildRoute2,
        buildPalletTown,
        buildViridianCity,
        buildPewterCity,
        registerAll,
        route1Trainers,
        route2Trainers,
    };
})();
