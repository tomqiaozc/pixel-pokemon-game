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
        fishCaught: 0,
        movesLearned: 0,
        legendariesCaught: 0,
        playTimeMs: 0,
        favoritePokemon: 'None',
        battlesByPokemon: {},
    };

    let saveTimer = 0;
    const SAVE_INTERVAL = 30000;

    // Map backend snake_case keys to frontend camelCase keys
    const SNAKE_TO_CAMEL = {
        total_battles_won: 'battlesWon',
        pvp_wins: 'battlesWon', // fallback alias
        pvp_losses: 'battlesLost',
        total_pokemon_caught: 'pokemonCaught',
        pokedex_seen: 'pokemonSeen',
        play_time_seconds: 'playTimeMs',
    };

    function applyBackendStats(data) {
        for (const key of Object.keys(data)) {
            // Direct camelCase match
            if (key in stats) {
                stats[key] = data[key];
            }
            // snake_case → camelCase mapping
            const mapped = SNAKE_TO_CAMEL[key];
            if (mapped && mapped in stats) {
                if (key === 'play_time_seconds') {
                    stats[mapped] = data[key] * 1000; // seconds → ms
                } else {
                    stats[mapped] = data[key];
                }
            }
        }
    }

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
                applyBackendStats(data);
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
        // Send snake_case payload to backend
        API.savePlayerStats({
            total_battles_won: stats.battlesWon,
            pvp_losses: stats.battlesLost,
            total_pokemon_caught: stats.pokemonCaught,
            pokedex_seen: stats.pokemonSeen,
            play_time_seconds: Math.floor(stats.playTimeMs / 1000),
            pvp_wins: stats.battlesWon,
        });
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
