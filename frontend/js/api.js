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

    // --- Helper ---

    async function post(url, body) {
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    async function get(url) {
        try {
            const res = await fetch(url);
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    async function del(url) {
        try {
            const res = await fetch(url, { method: 'DELETE' });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    }

    // --- Game Session ---

    async function createGame(playerName, starterName) {
        const starterId = STARTER_IDS[starterName];
        if (!starterId) return null;
        const data = await post(`${BASE_URL}/game/choose-starter`, {
            player_name: playerName || 'Red',
            starter_id: starterId,
        });
        if (data) gameId = data.id;
        return data;
    }

    function getGameId() { return gameId; }

    async function getGameState() {
        if (!gameId) return null;
        return get(`${BASE_URL}/game/${gameId}`);
    }

    async function saveGame(playerData) {
        if (!gameId) return null;
        return post(`${BASE_URL}/game/${gameId}/save`, { player: playerData });
    }

    async function updatePlayTime(seconds) {
        if (!gameId) return null;
        return post(`${BASE_URL}/game/${gameId}/play-time`, { seconds });
    }

    // --- Pokemon Center ---

    async function healParty() {
        if (!gameId) return null;
        return post(`${BASE_URL}/pokemon-center/heal/${gameId}`, {});
    }

    // --- Pokedex ---

    async function registerSeen(speciesId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/pokedex/register-seen`, {
            game_id: gameId, species_id: speciesId,
        });
    }

    async function registerCaught(speciesId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/pokedex/register-caught`, {
            game_id: gameId, species_id: speciesId,
        });
    }

    // --- Inventory ---

    async function getInventory() {
        if (!gameId) return null;
        return get(`${BASE_URL}/inventory/${gameId}`);
    }

    async function getItems() {
        return get(`${BASE_URL}/items`);
    }

    async function useItem(itemId, targetPokemonIndex) {
        if (!gameId) return null;
        return post(`${BASE_URL}/inventory/use`, {
            game_id: gameId,
            item_id: itemId,
            target_pokemon_index: targetPokemonIndex,
        });
    }

    async function tossItem(itemId, quantity) {
        if (!gameId) return null;
        return post(`${BASE_URL}/inventory/toss`, {
            game_id: gameId,
            item_id: itemId,
            quantity: quantity || 1,
        });
    }

    // --- Shop ---

    async function getShop(shopId) {
        return get(`${BASE_URL}/shop/${shopId}`);
    }

    async function buyItem(shopId, itemId, quantity) {
        if (!gameId) return null;
        return post(`${BASE_URL}/shop/buy`, {
            game_id: gameId,
            shop_id: shopId,
            item_id: itemId,
            quantity: quantity || 1,
        });
    }

    async function sellItem(itemId, quantity) {
        if (!gameId) return null;
        return post(`${BASE_URL}/shop/sell`, {
            game_id: gameId,
            item_id: itemId,
            quantity: quantity || 1,
        });
    }

    // --- Battle ---

    async function startBattle(wildPokemon) {
        if (!gameId) return null;
        return post(`${BASE_URL}/battle/start`, {
            game_id: gameId,
            wild_pokemon: wildPokemon || null,
        });
    }

    async function battleAction(battleId, action, moveIndex) {
        if (!gameId) return null;
        return post(`${BASE_URL}/battle/action`, {
            battle_id: battleId,
            action,
            move_index: moveIndex,
            game_id: gameId,
        });
    }

    async function getBattleState(battleId) {
        return get(`${BASE_URL}/battle/state/${battleId}`);
    }

    async function battleAiAction(battleId, difficulty) {
        return post(`${BASE_URL}/battle/ai-action`, {
            battle_id: battleId,
            difficulty: difficulty || 'normal',
        });
    }

    async function battleCatch(battleId, itemId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/battle/catch`, {
            battle_id: battleId,
            item_id: itemId,
            game_id: gameId,
        });
    }

    // --- Encounter ---

    async function checkEncounter(areaId) {
        return post(`${BASE_URL}/encounter/check`, { area_id: areaId });
    }

    async function getSpecies(speciesId) {
        if (speciesId) return get(`${BASE_URL}/encounter/species/${speciesId}`);
        return get(`${BASE_URL}/encounter/species`);
    }

    async function getStarters() {
        return get(`${BASE_URL}/encounter/starters`);
    }

    // --- Evolution ---

    async function awardExp(pokemonIndex, defeatedSpeciesId, defeatedLevel) {
        if (!gameId) return null;
        return post(`${BASE_URL}/evolution/award-exp`, {
            game_id: gameId,
            pokemon_index: pokemonIndex,
            defeated_species_id: defeatedSpeciesId,
            defeated_level: defeatedLevel,
        });
    }

    // --- Gyms & Trainers ---

    async function getGyms() {
        return get(`${BASE_URL}/gyms`);
    }

    async function getGym(gymId) {
        return get(`${BASE_URL}/gyms/${gymId}`);
    }

    async function challengeGym(gymId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/gyms/${gymId}/challenge/${gameId}`, {});
    }

    async function awardBadge(gymId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/gyms/${gymId}/award-badge/${gameId}`, {});
    }

    async function getBadges() {
        if (!gameId) return null;
        return get(`${BASE_URL}/badges/${gameId}`);
    }

    async function getTrainers(mapId) {
        const url = gameId
            ? `${BASE_URL}/trainers/${mapId}?game_id=${gameId}`
            : `${BASE_URL}/trainers/${mapId}`;
        return get(url);
    }

    async function getTrainer(trainerId) {
        return get(`${BASE_URL}/trainers/detail/${trainerId}`);
    }

    async function startTrainerBattle(trainerId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/trainers/${trainerId}/battle/${gameId}`, {});
    }

    async function defeatTrainer(trainerId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/trainers/${trainerId}/defeat/${gameId}`, {});
    }

    // --- NPCs & Dialogue ---

    async function getNpcs(mapId) {
        return get(`${BASE_URL}/npcs/${mapId}`);
    }

    async function getDialogue(npcId) {
        return get(`${BASE_URL}/dialogue/${npcId}`);
    }

    async function dialogueChoice(npcId, nodeId, choiceIndex) {
        return post(`${BASE_URL}/dialogue/choice`, {
            npc_id: npcId,
            node_id: nodeId,
            choice_index: choiceIndex,
        });
    }

    // --- Trading API ---

    async function tradeCreate() {
        if (!gameId) return null;
        return post(`${BASE_URL}/trade/create`, { player_id: gameId });
    }

    async function tradeJoin(tradeCode) {
        if (!gameId) return null;
        return post(`${BASE_URL}/trade/join/${tradeCode}`, { player_id: gameId });
    }

    async function tradeOffer(sessionId, pokemonIndex) {
        if (!gameId) return null;
        return post(`${BASE_URL}/trade/offer`, {
            session_id: sessionId,
            player_id: gameId,
            pokemon_index: pokemonIndex,
        });
    }

    async function tradeConfirm(sessionId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/trade/confirm`, {
            session_id: sessionId,
            player_id: gameId,
        });
    }

    async function tradeCancel(sessionId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/trade/cancel`, {
            session_id: sessionId,
            player_id: gameId,
        });
    }

    async function tradeStatus(sessionId) {
        return get(`${BASE_URL}/trade/session/${sessionId}`);
    }

    async function tradeDelete(sessionId) {
        return del(`${BASE_URL}/trade/session/${sessionId}`);
    }

    async function tradeHistory() {
        if (!gameId) return null;
        return get(`${BASE_URL}/trade/history/${gameId}`);
    }

    // --- PvP API ---

    async function pvpCreate() {
        if (!gameId) return null;
        return post(`${BASE_URL}/pvp/create`, { player_id: gameId });
    }

    async function pvpJoin(battleCode) {
        if (!gameId) return null;
        return post(`${BASE_URL}/pvp/join/${battleCode}`, { player_id: gameId });
    }

    async function pvpReady(sessionId, leadPokemonIndex) {
        if (!gameId) return null;
        return post(`${BASE_URL}/pvp/ready`, {
            session_id: sessionId,
            player_id: gameId,
            lead_pokemon_index: leadPokemonIndex || 0,
        });
    }

    async function pvpAction(sessionId, action, moveIndex) {
        if (!gameId) return null;
        return post(`${BASE_URL}/pvp/action`, {
            session_id: sessionId,
            player_id: gameId,
            action,
            move_index: moveIndex,
        });
    }

    async function pvpForfeit(sessionId) {
        if (!gameId) return null;
        return post(`${BASE_URL}/pvp/forfeit`, {
            session_id: sessionId,
            player_id: gameId,
        });
    }

    async function pvpState(sessionId) {
        return get(`${BASE_URL}/pvp/session/${sessionId}`);
    }

    async function pvpResult(sessionId) {
        return get(`${BASE_URL}/pvp/result/${sessionId}`);
    }

    async function pvpHistory() {
        if (!gameId) return null;
        return get(`${BASE_URL}/pvp/history/${gameId}`);
    }

    // --- Leaderboard API ---

    async function getLeaderboard(category) {
        return get(`${BASE_URL}/leaderboard/${category}`);
    }

    // --- Player Stats & Achievements API ---

    async function getPlayerStats() {
        if (!gameId) return null;
        return get(`${BASE_URL}/player/${gameId}/stats`);
    }

    async function savePlayerStats(statsData) {
        if (!gameId) return null;
        return post(`${BASE_URL}/player/${gameId}/stats`, statsData);
    }

    async function getAchievements() {
        if (!gameId) return null;
        return get(`${BASE_URL}/player/${gameId}/achievements`);
    }

    async function saveAchievements(achievementIds) {
        if (!gameId) return null;
        return post(`${BASE_URL}/player/${gameId}/achievements`, {
            achievements: achievementIds,
        });
    }

    // --- Maps ---

    async function getMaps() {
        return get(`${BASE_URL}/maps`);
    }

    return {
        // Game
        createGame, getGameId, getGameState, saveGame, updatePlayTime,
        // Pokemon Center
        healParty,
        // Pokedex
        registerSeen, registerCaught,
        // Inventory
        getInventory, getItems, useItem, tossItem,
        // Shop
        getShop, buyItem, sellItem,
        // Battle
        startBattle, battleAction, getBattleState, battleAiAction, battleCatch,
        // Encounter
        checkEncounter, getSpecies, getStarters,
        // Evolution
        awardExp,
        // Gyms & Trainers
        getGyms, getGym, challengeGym, awardBadge, getBadges,
        getTrainers, getTrainer, startTrainerBattle, defeatTrainer,
        // NPCs
        getNpcs, getDialogue, dialogueChoice,
        // Trading
        tradeCreate, tradeJoin, tradeOffer, tradeConfirm, tradeCancel,
        tradeStatus, tradeDelete, tradeHistory,
        // PvP
        pvpCreate, pvpJoin, pvpReady, pvpAction, pvpForfeit,
        pvpState, pvpResult, pvpHistory,
        // Leaderboard
        getLeaderboard,
        // Stats & Achievements
        getPlayerStats, savePlayerStats, getAchievements, saveAchievements,
        // Maps
        getMaps,
    };
})();
