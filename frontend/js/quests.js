// quests.js — Quest journal, tracker HUD, quest flags, and quest-giver markers

const Quests = (() => {
    // Quest states: active, completed, locked
    let quests = [];
    let flags = {};         // story flags: { 'delivered_parcel': true, ... }
    let activeQuestId = null;
    let journalOpen = false;
    let journalTab = 0;    // 0=Main Story, 1=Side Quests
    let journalIndex = 0;
    let actionCooldown = 0;

    // HUD state
    let hudVisible = true;
    let objectiveFlash = 0; // flash timer when objective completes
    let objectiveText = '';

    // Seed quests
    const QUEST_TEMPLATES = [
        {
            id: 'new_adventure',
            name: 'A New Adventure',
            type: 'main',
            objectives: [
                { desc: 'Choose your starter Pokemon', flag: 'chose_starter' },
                { desc: 'Receive the Pokedex from Prof. Oak', flag: 'received_pokedex' },
            ],
        },
        {
            id: 'oaks_parcel',
            name: "Oak's Parcel",
            type: 'main',
            objectives: [
                { desc: 'Travel to Viridian City', flag: 'reached_viridian' },
                { desc: 'Pick up the parcel from the Mart', flag: 'got_parcel' },
                { desc: "Deliver the parcel to Prof. Oak", flag: 'delivered_parcel' },
            ],
            requires: 'received_pokedex',
        },
        {
            id: 'boulder_badge',
            name: 'The Boulder Badge',
            type: 'main',
            objectives: [
                { desc: 'Travel to Pewter City', flag: 'reached_pewter' },
                { desc: 'Defeat Gym Leader Brock', flag: 'defeated_brock' },
            ],
            requires: 'delivered_parcel',
        },
        {
            id: 'rival_showdown',
            name: 'Rival Showdown',
            type: 'main',
            objectives: [
                { desc: 'Encounter your Rival on Route 2', flag: 'rival_route2_met' },
                { desc: 'Defeat your Rival', flag: 'rival_route2_defeated' },
            ],
            requires: 'defeated_brock',
        },
        {
            id: 'cascade_badge',
            name: 'The Cascade Badge',
            type: 'main',
            objectives: [
                { desc: 'Travel to Cerulean City', flag: 'reached_cerulean' },
                { desc: 'Defeat Gym Leader Misty', flag: 'defeated_misty' },
            ],
            requires: 'rival_route2_defeated',
        },
    ];

    function init() {
        quests = [];
        flags = {};
        activeQuestId = null;

        // Initialize quests from templates
        for (const tmpl of QUEST_TEMPLATES) {
            quests.push({
                id: tmpl.id,
                name: tmpl.name,
                type: tmpl.type,
                objectives: tmpl.objectives.map(o => ({ ...o, done: false })),
                requires: tmpl.requires || null,
                state: tmpl.requires ? 'locked' : 'active',
            });
        }

        // Auto-set first active quest
        activeQuestId = 'new_adventure';
        updateObjectiveText();
    }

    function setFlag(flagName) {
        if (flags[flagName]) return; // already set
        flags[flagName] = true;

        // Update quest objectives
        for (const quest of quests) {
            if (quest.state !== 'active') continue;
            for (const obj of quest.objectives) {
                if (obj.flag === flagName && !obj.done) {
                    obj.done = true;
                    objectiveFlash = 2000; // flash for 2 seconds
                }
            }

            // Check if all objectives done
            if (quest.objectives.every(o => o.done)) {
                quest.state = 'completed';
                // Unlock next quest
                unlockNextQuests();
            }
        }

        updateObjectiveText();
    }

    function hasFlag(flagName) {
        return !!flags[flagName];
    }

    function unlockNextQuests() {
        for (const quest of quests) {
            if (quest.state === 'locked' && quest.requires && flags[quest.requires]) {
                quest.state = 'active';
                if (!activeQuestId || getQuest(activeQuestId).state === 'completed') {
                    activeQuestId = quest.id;
                }
            }
        }
    }

    function getQuest(id) {
        return quests.find(q => q.id === id);
    }

    function getActiveQuest() {
        return activeQuestId ? getQuest(activeQuestId) : null;
    }

    function getCurrentObjective() {
        const quest = getActiveQuest();
        if (!quest) return null;
        return quest.objectives.find(o => !o.done) || null;
    }

    function updateObjectiveText() {
        const obj = getCurrentObjective();
        objectiveText = obj ? obj.desc : '';
    }

    // Journal UI
    function openJournal() {
        journalOpen = true;
        journalTab = 0;
        journalIndex = 0;
        actionCooldown = 250;
    }

    function closeJournal() {
        journalOpen = false;
    }

    function isJournalOpen() { return journalOpen; }

    function updateJournal(dt) {
        if (!journalOpen) return;
        actionCooldown = Math.max(0, actionCooldown - dt);

        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        const filtered = quests.filter(q => journalTab === 0 ? q.type === 'main' : q.type === 'side');

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { journalIndex = Math.max(0, journalIndex - 1); actionCooldown = 150; }
            if (mov.dy > 0) { journalIndex = Math.min(Math.max(0, filtered.length - 1), journalIndex + 1); actionCooldown = 150; }
            if (mov.dx !== 0) {
                journalTab = journalTab === 0 ? 1 : 0;
                journalIndex = 0;
                actionCooldown = 200;
            }
        }

        if (action && filtered[journalIndex] && filtered[journalIndex].state === 'active') {
            activeQuestId = filtered[journalIndex].id;
            updateObjectiveText();
            actionCooldown = 200;
        }

        if (back) { closeJournal(); actionCooldown = 200; }
    }

    function renderJournal(ctx, canvasW, canvasH) {
        if (!journalOpen) return;

        const panelW = canvasW - 40;
        const panelH = canvasH - 40;
        const px = 20;
        const py = 20;

        // Background
        ctx.fillStyle = '#2a2a3a';
        ctx.fillRect(px, py, panelW, panelH);
        ctx.strokeStyle = '#f8d030';
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, panelW, panelH);

        // Title
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Quest Journal', px + panelW / 2, py + 22);

        // Tabs
        const tabs = ['Main Story', 'Side Quests'];
        const tabW = panelW / 2;
        for (let i = 0; i < 2; i++) {
            const tx = px + i * tabW;
            ctx.fillStyle = i === journalTab ? '#404060' : '#303048';
            ctx.fillRect(tx, py + 30, tabW, 22);
            ctx.strokeStyle = '#606080';
            ctx.lineWidth = 1;
            ctx.strokeRect(tx, py + 30, tabW, 22);
            ctx.fillStyle = i === journalTab ? '#f8f8f8' : '#808090';
            ctx.font = i === journalTab ? 'bold 12px monospace' : '11px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(tabs[i], tx + tabW / 2, py + 46);
        }

        // Quest list
        const filtered = quests.filter(q => journalTab === 0 ? q.type === 'main' : q.type === 'side');
        const listY = py + 58;

        if (filtered.length === 0) {
            ctx.fillStyle = '#606070';
            ctx.font = '13px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('No quests yet', px + panelW / 2, listY + 40);
        }

        for (let i = 0; i < filtered.length; i++) {
            const quest = filtered[i];
            const qy = listY + i * 50;
            if (qy + 50 > py + panelH - 20) break;

            // Quest row
            const isSelected = i === journalIndex;
            const isActive = quest.id === activeQuestId;
            ctx.fillStyle = isSelected ? 'rgba(80, 80, 120, 0.6)' : 'rgba(255, 255, 255, 0.05)';
            ctx.fillRect(px + 6, qy, panelW - 12, 46);
            if (isSelected) {
                ctx.strokeStyle = '#8080c0';
                ctx.lineWidth = 1;
                ctx.strokeRect(px + 6, qy, panelW - 12, 46);
            }

            // Status indicator
            if (quest.state === 'completed') {
                ctx.fillStyle = '#48c048';
                ctx.font = 'bold 14px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('\u2713', px + 14, qy + 18);
            } else if (quest.state === 'locked') {
                ctx.fillStyle = '#606060';
                ctx.font = 'bold 14px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('\u{1F512}', px + 14, qy + 18);
            } else if (isActive) {
                ctx.fillStyle = '#f8d030';
                ctx.font = 'bold 14px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('\u25B6', px + 14, qy + 18);
            }

            // Quest name
            ctx.fillStyle = quest.state === 'completed' ? '#808080'
                          : quest.state === 'locked' ? '#505050'
                          : '#f8f8f8';
            ctx.font = 'bold 13px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(quest.name, px + 32, qy + 18);

            // Current objective or "Completed"
            if (quest.state === 'completed') {
                ctx.fillStyle = '#48c048';
                ctx.font = '10px monospace';
                ctx.fillText('Completed', px + 32, qy + 34);
            } else if (quest.state === 'active') {
                const currObj = quest.objectives.find(o => !o.done);
                if (currObj) {
                    ctx.fillStyle = '#b0b0c0';
                    ctx.font = '10px monospace';
                    ctx.fillText(currObj.desc, px + 32, qy + 34);
                }
                // Progress
                const done = quest.objectives.filter(o => o.done).length;
                const total = quest.objectives.length;
                ctx.fillStyle = '#a0a0b0';
                ctx.font = '10px monospace';
                ctx.textAlign = 'right';
                ctx.fillText(`${done}/${total}`, px + panelW - 14, qy + 18);
            } else {
                ctx.fillStyle = '#505050';
                ctx.font = '10px monospace';
                ctx.fillText('Locked', px + 32, qy + 34);
            }
        }

        // Back hint
        ctx.fillStyle = '#606070';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('Z: Track | B/Esc: Back', px + panelW - 10, py + panelH - 8);
        ctx.textAlign = 'left';
    }

    // HUD overlay for overworld
    function updateHUD(dt) {
        if (objectiveFlash > 0) {
            objectiveFlash = Math.max(0, objectiveFlash - dt);
        }
    }

    function renderHUD(ctx, canvasW, canvasH) {
        if (!hudVisible || !objectiveText) return;

        const hudX = 10;
        const hudY = canvasH - 36;
        const hudW = Math.min(280, canvasW - 20);

        // Background
        ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        ctx.fillRect(hudX, hudY, hudW, 26);

        // Objective flash
        if (objectiveFlash > 0) {
            const flash = Math.sin(objectiveFlash * 0.008) * 0.3 + 0.3;
            ctx.fillStyle = `rgba(72, 192, 72, ${flash})`;
            ctx.fillRect(hudX, hudY, hudW, 26);

            ctx.fillStyle = '#48c048';
            ctx.font = 'bold 10px monospace';
            ctx.textAlign = 'left';
            ctx.fillText('\u2713 Objective Complete!', hudX + 6, hudY + 16);
        } else {
            ctx.fillStyle = '#f8d030';
            ctx.font = '9px monospace';
            ctx.textAlign = 'left';
            ctx.fillText('\u25B6 ' + objectiveText, hudX + 6, hudY + 16);
        }
        ctx.textAlign = 'left';
    }

    function toggleHUD() {
        hudVisible = !hudVisible;
    }

    // Quest-giver markers ("!" and "?")
    function renderQuestMarkers(ctx, camX, camY, scale, npcs) {
        const TILE = 16;
        const time = Date.now();

        for (const npc of npcs) {
            // Check if NPC is a quest giver or turn-in
            const marker = getQuestMarker(npc.name);
            if (!marker) continue;

            const sx = (npc.x * TILE + TILE / 2 - camX) * scale;
            const sy = (npc.y * TILE - 6 - camY) * scale;
            const bounce = Math.sin(time * 0.004) * 3;

            // Marker background
            ctx.fillStyle = marker === '!' ? '#f8d030' : '#4888e0';
            ctx.beginPath();
            ctx.arc(sx, sy + bounce - 4, 8, 0, Math.PI * 2);
            ctx.fill();

            // Marker text
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(marker, sx, sy + bounce);
            ctx.textAlign = 'left';
        }
    }

    function getQuestMarker(npcName) {
        // Quest-giver "!" — NPC has a quest to give
        if (npcName === 'Prof. Oak' || npcName === 'Professor Oak') {
            if (!hasFlag('chose_starter')) return '!';
            if (hasFlag('got_parcel') && !hasFlag('delivered_parcel')) return '?';
            if (!hasFlag('received_pokedex') && hasFlag('chose_starter')) return '!';
        }
        if (npcName === 'Shopkeeper' && !hasFlag('got_parcel') && hasFlag('reached_viridian')) {
            return '!';
        }
        return null;
    }

    // Auto-set certain flags based on game events
    function onMapEnter(mapId) {
        if (mapId === 'viridian_city') setFlag('reached_viridian');
        if (mapId === 'pewter_city') setFlag('reached_pewter');
    }

    function onStarterChosen() {
        setFlag('chose_starter');
    }

    function onBadgeEarned(badgeIndex) {
        if (badgeIndex === 0) setFlag('defeated_brock');
        if (badgeIndex === 1) setFlag('defeated_misty');
    }

    return {
        init, setFlag, hasFlag, getActiveQuest, getCurrentObjective,
        openJournal, closeJournal, isJournalOpen, updateJournal, renderJournal,
        updateHUD, renderHUD, toggleHUD, renderQuestMarkers, getQuestMarker,
        onMapEnter, onStarterChosen, onBadgeEarned,
    };
})();
