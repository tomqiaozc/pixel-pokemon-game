// rival.js — Rival NPC system with team scaling and encounters

const Rival = (() => {
    const TILE = Sprites.TILE;

    let rivalName = 'Blue';
    let rivalStarter = null;  // { name, type }
    let rivalTeam = [];
    let encountered = {};  // { 'oaks_lab': true, 'route_2': true }

    // Counter-starter selection: player picks X, rival picks advantage
    const COUNTER_STARTERS = {
        'Bulbasaur':  { name: 'Charmander', type: 'Fire' },
        'Charmander': { name: 'Squirtle',   type: 'Water' },
        'Squirtle':   { name: 'Bulbasaur',  type: 'Grass' },
    };

    // Rival team templates by story stage
    const TEAM_STAGES = {
        oaks_lab: (starter) => [
            { name: starter.name, type: starter.type, level: 5,
              hp: 20, maxHp: 20, moves: getStarterMoves(starter.name) },
        ],
        route_2: (starter) => [
            { name: starter.name, type: starter.type, level: 15,
              hp: 42, maxHp: 42, moves: getStarterMoves(starter.name) },
            { name: 'Pidgeotto', type: 'Flying', level: 14,
              hp: 38, maxHp: 38, moves: [
                { name: 'Gust', type: 'Flying', power: 40, pp: 35, maxPp: 35 },
                { name: 'Quick Attack', type: 'Normal', power: 40, pp: 30, maxPp: 30 },
            ]},
        ],
        pre_elite: (starter) => {
            const evolved = getEvolvedForm(starter);
            return [
                { name: evolved.name, type: evolved.type, level: 48,
                  hp: 140, maxHp: 140, moves: getStarterMoves(evolved.name) },
                { name: 'Pidgeot', type: 'Flying', level: 47,
                  hp: 135, maxHp: 135, moves: [
                    { name: 'Air Slash', type: 'Flying', power: 75, pp: 15, maxPp: 15 },
                    { name: 'Quick Attack', type: 'Normal', power: 40, pp: 30, maxPp: 30 },
                ]},
                { name: 'Alakazam', type: 'Psychic', level: 46,
                  hp: 125, maxHp: 125, moves: [
                    { name: 'Psychic', type: 'Psychic', power: 90, pp: 10, maxPp: 10 },
                    { name: 'Shadow Ball', type: 'Ghost', power: 80, pp: 15, maxPp: 15 },
                ]},
            ];
        },
    };

    // Encounter points: map where rival appears and which cutscene stage
    const ENCOUNTER_POINTS = {
        pallet_town: { stage: 'oaks_lab', flag: 'rival_oaks_lab_met',    requires: 'chose_starter' },
        route_2:     { stage: 'route_2',  flag: 'rival_route2_met',      requires: 'defeated_brock' },
    };

    function getStarterMoves(name) {
        const movesets = {
            'Bulbasaur':  [
                { name: 'Vine Whip', type: 'Grass', power: 45, pp: 25, maxPp: 25 },
                { name: 'Tackle', type: 'Normal', power: 40, pp: 35, maxPp: 35 },
            ],
            'Charmander': [
                { name: 'Ember', type: 'Fire', power: 40, pp: 25, maxPp: 25 },
                { name: 'Scratch', type: 'Normal', power: 40, pp: 35, maxPp: 35 },
            ],
            'Squirtle':   [
                { name: 'Water Gun', type: 'Water', power: 40, pp: 25, maxPp: 25 },
                { name: 'Tackle', type: 'Normal', power: 40, pp: 35, maxPp: 35 },
            ],
            'Ivysaur':    [
                { name: 'Razor Leaf', type: 'Grass', power: 55, pp: 25, maxPp: 25 },
                { name: 'Tackle', type: 'Normal', power: 40, pp: 35, maxPp: 35 },
            ],
            'Charmeleon': [
                { name: 'Flamethrower', type: 'Fire', power: 90, pp: 15, maxPp: 15 },
                { name: 'Slash', type: 'Normal', power: 70, pp: 20, maxPp: 20 },
            ],
            'Wartortle':  [
                { name: 'Water Pulse', type: 'Water', power: 60, pp: 20, maxPp: 20 },
                { name: 'Bite', type: 'Dark', power: 60, pp: 25, maxPp: 25 },
            ],
            'Venusaur':   [
                { name: 'Solar Beam', type: 'Grass', power: 120, pp: 10, maxPp: 10 },
                { name: 'Sludge Bomb', type: 'Poison', power: 90, pp: 10, maxPp: 10 },
            ],
            'Charizard':  [
                { name: 'Flamethrower', type: 'Fire', power: 90, pp: 15, maxPp: 15 },
                { name: 'Air Slash', type: 'Flying', power: 75, pp: 15, maxPp: 15 },
            ],
            'Blastoise':  [
                { name: 'Hydro Pump', type: 'Water', power: 110, pp: 5, maxPp: 5 },
                { name: 'Ice Beam', type: 'Ice', power: 90, pp: 10, maxPp: 10 },
            ],
        };
        return movesets[name] || movesets['Charmander'];
    }

    function getEvolvedForm(starter) {
        const evolutions = {
            'Bulbasaur':  { name: 'Venusaur',  type: 'Grass' },
            'Charmander': { name: 'Charizard',  type: 'Fire' },
            'Squirtle':   { name: 'Blastoise',  type: 'Water' },
        };
        return evolutions[starter.name] || starter;
    }

    function init(playerStarterName) {
        rivalStarter = COUNTER_STARTERS[playerStarterName] || COUNTER_STARTERS['Charmander'];
        encountered = {};
        rivalTeam = TEAM_STAGES.oaks_lab(rivalStarter);

        // Try loading rival data from backend
        API.getRival().then(data => {
            if (data && data.name) {
                rivalName = data.name;
                if (data.starter) {
                    rivalStarter = { name: data.starter.name || rivalStarter.name, type: data.starter.type || rivalStarter.type };
                }
                if (data.team && data.team.length > 0) {
                    rivalTeam = data.team.map(p => ({
                        name: p.name,
                        type: p.types ? p.types[0] : p.type || 'Normal',
                        level: p.level || 5,
                        hp: p.current_hp || p.stats?.hp || 20,
                        maxHp: p.stats?.hp || 20,
                        moves: p.moves || getStarterMoves(p.name),
                    }));
                }
                if (data.encountered) {
                    encountered = data.encountered;
                }
            }
        }).catch(() => {});
    }

    // Check if the rival should appear on this map
    function checkEncounter(mapId) {
        const point = ENCOUNTER_POINTS[mapId];
        if (!point) return null;

        // Already encountered here
        if (encountered[point.flag]) return null;

        // Prerequisite flag not met
        if (point.requires && !Quests.hasFlag(point.requires)) return null;

        return point;
    }

    // Mark an encounter as done and get the team for that stage
    function triggerEncounter(mapId) {
        const point = ENCOUNTER_POINTS[mapId];
        if (!point) return null;

        encountered[point.flag] = true;
        Quests.setFlag(point.flag);

        // Update rival team to this stage
        const stageBuilder = TEAM_STAGES[point.stage];
        if (stageBuilder && rivalStarter) {
            rivalTeam = stageBuilder(rivalStarter);
        }

        return {
            stage: point.stage,
            flag: point.flag,
            team: rivalTeam,
            lead: rivalTeam[0] || null,
        };
    }

    function getName() { return rivalName; }
    function getStarter() { return rivalStarter; }
    function getTeam() { return rivalTeam; }
    function hasEncountered(flag) { return !!encountered[flag]; }

    // Draw rival overworld sprite
    function drawSprite(ctx, x, y, scale, dir) {
        const s = scale;
        // Hair (spiky, blue-ish)
        ctx.fillStyle = '#604020';
        ctx.fillRect(x + 4 * s, y + s, 8 * s, 3 * s);
        // Spiky hair points
        ctx.fillRect(x + 3 * s, y, 2 * s, 2 * s);
        ctx.fillRect(x + 7 * s, y, 2 * s, 2 * s);
        ctx.fillRect(x + 11 * s, y, 2 * s, 2 * s);
        // Face
        ctx.fillStyle = '#f8c098';
        ctx.fillRect(x + 4 * s, y + 4 * s, 8 * s, 4 * s);
        // Eyes
        if (dir !== 1) {
            ctx.fillStyle = '#202020';
            if (dir === 2) {
                ctx.fillRect(x + 5 * s, y + 5 * s, 2 * s, 2 * s);
            } else if (dir === 3) {
                ctx.fillRect(x + 9 * s, y + 5 * s, 2 * s, 2 * s);
            } else {
                ctx.fillRect(x + 5 * s, y + 5 * s, 2 * s, 2 * s);
                ctx.fillRect(x + 9 * s, y + 5 * s, 2 * s, 2 * s);
            }
        }
        // Jacket (purple — rival color)
        ctx.fillStyle = '#6040a0';
        ctx.fillRect(x + 3 * s, y + 8 * s, 10 * s, 5 * s);
        // Collar
        ctx.fillStyle = '#503080';
        ctx.fillRect(x + 6 * s, y + 8 * s, 4 * s, 2 * s);
        // Pants
        ctx.fillStyle = '#404040';
        ctx.fillRect(x + 4 * s, y + 13 * s, 3 * s, 3 * s);
        ctx.fillRect(x + 9 * s, y + 13 * s, 3 * s, 3 * s);
    }

    return {
        init, checkEncounter, triggerEncounter,
        getName, getStarter, getTeam, hasEncountered,
        drawSprite,
    };
})();
