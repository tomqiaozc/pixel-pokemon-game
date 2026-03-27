// playerstats.js — Centralized player statistics tracking

const PlayerStats = (() => {
    const stats = {
        battlesWon: 0,
        battlesLost: 0,
        trainersDefeated: 0,
        pokemonCaught: 0,
        pokemonSeen: 0,
        pokemonEvolved: 0,
        steps: 0,
        money: 3000,
        itemsUsed: 0,
        playTimeMs: 0,
        favoritePokemon: 'None',
        battlesByPokemon: {}, // { name: count } to determine favorite
    };

    function increment(key, amount) {
        if (typeof stats[key] === 'number') {
            stats[key] += (amount || 1);
        }
    }

    function set(key, value) {
        stats[key] = value;
    }

    function get(key) {
        return stats[key];
    }

    function recordBattlePokemon(name) {
        if (!stats.battlesByPokemon[name]) stats.battlesByPokemon[name] = 0;
        stats.battlesByPokemon[name]++;

        // Update favorite (most battles)
        let maxName = 'None';
        let maxCount = 0;
        for (const [n, c] of Object.entries(stats.battlesByPokemon)) {
            if (c > maxCount) { maxCount = c; maxName = n; }
        }
        stats.favoritePokemon = maxName;
    }

    function updatePlayTime(dt) {
        stats.playTimeMs += dt;
    }

    function getStats() {
        // Count Pokedex stats from entries if available
        if (typeof Pokedex !== 'undefined' && Pokedex.entries) {
            let seen = 0;
            let caught = 0;
            // Pokedex status is internal, estimate from entries
            // We track our own counts via increment
        }

        const totalMs = stats.playTimeMs;
        const hours = Math.floor(totalMs / 3600000);
        const minutes = Math.floor((totalMs % 3600000) / 60000);

        return {
            ...stats,
            playTime: `${hours}:${String(minutes).padStart(2, '0')}`,
        };
    }

    return { increment, set, get, getStats, recordBattlePokemon, updatePlayTime };
})();
