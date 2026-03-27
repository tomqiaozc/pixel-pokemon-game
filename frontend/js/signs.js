// signs.js — Sign interaction system

const Signs = (() => {
    const TILE = Sprites.TILE;

    // Sign data per map
    const signData = {
        route_1: [
            { x: 9, y: 2, text: ['Route 1', 'Pallet Town - Viridian City'] },
            { x: 9, y: 37, text: ['Route 1', 'Viridian City - Pallet Town'] },
        ],
        route_2: [
            { x: 10, y: 2, text: ['Route 2', 'Viridian City - Pewter City'] },
            { x: 10, y: 33, text: ['Route 2', 'Pewter City - Viridian City'] },
        ],
        pallet_town: [
            { x: 12, y: 12, text: ['Pallet Town', 'Shades of your journey await!'] },
        ],
        viridian_city: [
            { x: 14, y: 10, text: ['Viridian City', 'The Eternally Green Paradise'] },
        ],
        pewter_city: [
            { x: 13, y: 9, text: ['Pewter City', 'A Stone Gray City'] },
        ],
    };

    // Check if player is facing a sign and action is pressed
    function checkInteraction(playerX, playerY, playerDir) {
        const tileX = Math.floor((playerX + TILE / 2) / TILE);
        const tileY = Math.floor((playerY + TILE / 2) / TILE);

        // Calculate facing tile
        const facingX = tileX + (playerDir === 3 ? 1 : playerDir === 2 ? -1 : 0);
        const facingY = tileY + (playerDir === 0 ? 1 : playerDir === 1 ? -1 : 0);

        const mapId = MapLoader.getCurrentMapId();
        const signs = signData[mapId];
        if (!signs) return null;

        for (const sign of signs) {
            if (facingX === sign.x && facingY === sign.y) {
                return sign;
            }
        }

        return null;
    }

    // Get signs for the current map (for rendering sign posts)
    function getSignsForMap(mapId) {
        return signData[mapId] || [];
    }

    // Register additional signs for a map
    function addSign(mapId, x, y, text) {
        if (!signData[mapId]) signData[mapId] = [];
        signData[mapId].push({ x, y, text });
    }

    return { checkInteraction, getSignsForMap, addSign };
})();
