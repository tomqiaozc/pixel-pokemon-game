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
        battlesByPokemon: {},
    };

    let saveTimer = 0;
    const SAVE_INTERVAL = 30000;

    function load() {
        try {
            const saved = localStorage.getItem('pokemon_player_stats');
            if (saved) {
                const data = JSON.parse(saved);
                for (const key of Object.keys(data)) {
                    if (key in stats) stats[key] = data[key];
                }
            }
        } catch { /* ignore */ }

        API.getPlayerStats().then(data => {
            if (data && typeof data === 'object') {
                for (const key of Object.keys(data)) {
                    if (key in stats) stats[key] = data[key];
                }
                persistLocal();
            }
        });
    }

    function persistLocal() {
        try {
            localStorage.setItem('pokemon_player_stats', JSON.stringify(stats));
        } catch { /* ignore */ }
    }

    function save() {
        persistLocal();
        API.savePlayerStats(stats);
    }

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

        let maxName = 'None';
        let maxCount = 0;
        for (const [n, c] of Object.entries(stats.battlesByPokemon)) {
            if (c > maxCount) { maxCount = c; maxName = n; }
        }
        stats.favoritePokemon = maxName;
    }

    function updatePlayTime(dt) {
        stats.playTimeMs += dt;
        saveTimer += dt;
        if (saveTimer >= SAVE_INTERVAL) {
            saveTimer = 0;
            save();
        }
    }

    function getStats() {
        if (typeof Pokedex !== 'undefined' && Pokedex.entries) {
            let seen = 0;
            let caught = 0;
        }

        const totalMs = stats.playTimeMs;
        const hours = Math.floor(totalMs / 3600000);
        const minutes = Math.floor((totalMs % 3600000) / 60000);

        return {
            ...stats,
            playTime: `${hours}:${String(minutes).padStart(2, '0')}`,
        };
    }

    return { increment, set, get, getStats, recordBattlePokemon, updatePlayTime, load, save };
})();
