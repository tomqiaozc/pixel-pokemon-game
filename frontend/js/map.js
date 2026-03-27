// map.js — Tile map system with collision detection

const GameMap = (() => {
    const TILE = Sprites.TILE;

    // Tile types
    const T = {
        GRASS:      0,
        TALL_GRASS: 1,
        DIRT:       2,
        WATER:      3,
        TREE:       4,
        ROCK:       5,
        FLOWER:     6,
        HOUSE_WALL: 7,
        HOUSE_ROOF: 8,
        DOOR:       9,
    };

    // Which tiles block movement
    const SOLID = new Set([T.WATER, T.TREE, T.ROCK, T.HOUSE_WALL, T.HOUSE_ROOF]);

    // Map data — a small starter town (30x25 tiles)
    let MAP_W = 30;
    let MAP_H = 25;

    // prettier-ignore
    let mapData = buildStarterMap();

    // Load new map data (for multi-map support)
    function loadMapData(data, width, height) {
        mapData = data;
        MAP_W = width;
        MAP_H = height;
    }

    function buildStarterMap() {
        const m = [];
        for (let y = 0; y < MAP_H; y++) {
            const row = [];
            for (let x = 0; x < MAP_W; x++) {
                row.push(T.GRASS);
            }
            m.push(row);
        }

        // Border with trees
        for (let x = 0; x < MAP_W; x++) {
            m[0][x] = T.TREE;
            m[MAP_H - 1][x] = T.TREE;
        }
        for (let y = 0; y < MAP_H; y++) {
            m[y][0] = T.TREE;
            m[y][MAP_W - 1] = T.TREE;
        }

        // Dirt path (horizontal main road)
        for (let x = 1; x < MAP_W - 1; x++) {
            m[12][x] = T.DIRT;
            m[13][x] = T.DIRT;
        }
        // Vertical path
        for (let y = 1; y < MAP_H - 1; y++) {
            m[y][14] = T.DIRT;
            m[y][15] = T.DIRT;
        }

        // House 1 — top left area
        buildHouse(m, 3, 3, 5, 4);
        // House 2 — top right area
        buildHouse(m, 20, 3, 5, 4);
        // House 3 — bottom left
        buildHouse(m, 3, 16, 5, 4);

        // Pond (water area)
        for (let y = 17; y <= 21; y++) {
            for (let x = 21; x <= 26; x++) {
                if (y === 17 && (x === 21 || x === 26)) continue;
                if (y === 21 && (x === 21 || x === 26)) continue;
                m[y][x] = T.WATER;
            }
        }

        // Tall grass patches (wild pokemon encounter zones)
        for (let y = 8; y <= 10; y++) {
            for (let x = 3; x <= 8; x++) {
                m[y][x] = T.TALL_GRASS;
            }
        }
        for (let y = 15; y <= 17; y++) {
            for (let x = 22; x <= 27; x++) {
                if (m[y][x] === T.GRASS) m[y][x] = T.TALL_GRASS;
            }
        }

        // Scattered rocks
        m[6][18] = T.ROCK;
        m[10][24] = T.ROCK;
        m[20][10] = T.ROCK;

        // Flowers
        m[9][12] = T.FLOWER;
        m[10][13] = T.FLOWER;
        m[14][22] = T.FLOWER;
        m[5][11] = T.FLOWER;
        m[18][8] = T.FLOWER;

        // Extra trees for scenery
        m[7][17] = T.TREE;
        m[5][20] = T.TREE;
        m[16][10] = T.TREE;
        m[22][13] = T.TREE;

        return m;
    }

    function buildHouse(m, sx, sy, w, h) {
        // Roof
        for (let x = sx; x < sx + w; x++) {
            m[sy][x] = T.HOUSE_ROOF;
            m[sy + 1][x] = T.HOUSE_ROOF;
        }
        // Walls
        for (let y = sy + 2; y < sy + h; y++) {
            for (let x = sx; x < sx + w; x++) {
                m[y][x] = T.HOUSE_WALL;
            }
        }
        // Door at center bottom
        const doorX = sx + Math.floor(w / 2);
        m[sy + h - 1][doorX] = T.DOOR;
    }

    function getTile(x, y) {
        if (x < 0 || y < 0 || x >= MAP_W || y >= MAP_H) return T.TREE; // OOB = solid
        return mapData[y][x];
    }

    function isSolid(tileX, tileY) {
        return SOLID.has(getTile(tileX, tileY));
    }

    function isTallGrass(tileX, tileY) {
        return getTile(tileX, tileY) === T.TALL_GRASS;
    }

    return {
        T,
        get MAP_W() { return MAP_W; },
        get MAP_H() { return MAP_H; },
        TILE,
        getTile,
        isSolid,
        isTallGrass,
        get mapData() { return mapData; },
        loadMapData,
    };
})();
