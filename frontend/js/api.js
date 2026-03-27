// api.js — Backend API client for game session management

const API = (() => {
    const BASE_URL = 'http://localhost:8000/api';

    let gameId = null;

    // Starter name to species ID mapping
    const STARTER_IDS = {
        'Bulbasaur': 1,
        'Charmander': 4,
        'Squirtle': 7,
    };

    async function createGame(playerName, starterName) {
        const starterId = STARTER_IDS[starterName];
        if (!starterId) return null;

        try {
            const res = await fetch(`${BASE_URL}/game/choose-starter`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_name: playerName || 'Red',
                    starter_id: starterId,
                }),
            });
            if (!res.ok) return null;
            const data = await res.json();
            gameId = data.id;
            return data;
        } catch {
            return null;
        }
    }

    function getGameId() { return gameId; }

    async function healParty() {
        if (!gameId) return null;
        try {
            const res = await fetch(`${BASE_URL}/pokemon-center/heal/${gameId}`, {
                method: 'POST',
            });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    async function registerSeen(speciesId) {
        if (!gameId) return null;
        try {
            const res = await fetch(`${BASE_URL}/pokedex/register-seen`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ game_id: gameId, species_id: speciesId }),
            });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    async function registerCaught(speciesId) {
        if (!gameId) return null;
        try {
            const res = await fetch(`${BASE_URL}/pokedex/register-caught`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ game_id: gameId, species_id: speciesId }),
            });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    async function saveGame(playerData) {
        if (!gameId) return null;
        try {
            const res = await fetch(`${BASE_URL}/game/${gameId}/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player: playerData }),
            });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    async function getInventory() {
        if (!gameId) return null;
        try {
            const res = await fetch(`${BASE_URL}/inventory/${gameId}`);
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    async function useItem(itemId, targetPokemonIndex) {
        if (!gameId) return null;
        try {
            const res = await fetch(`${BASE_URL}/inventory/use`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    game_id: gameId,
                    item_id: itemId,
                    target_pokemon_index: targetPokemonIndex,
                }),
            });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    async function awardExp(pokemonIndex, defeatedSpeciesId, defeatedLevel) {
        if (!gameId) return null;
        try {
            const res = await fetch(`${BASE_URL}/evolution/award-exp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    game_id: gameId,
                    pokemon_index: pokemonIndex,
                    defeated_species_id: defeatedSpeciesId,
                    defeated_level: defeatedLevel,
                }),
            });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    async function checkEncounter(areaId) {
        try {
            const res = await fetch(`${BASE_URL}/encounter/check`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ area_id: areaId }),
            });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    return {
        createGame, getGameId, healParty, registerSeen,
        registerCaught, saveGame, getInventory, useItem,
        awardExp, checkEncounter,
    };
})();
