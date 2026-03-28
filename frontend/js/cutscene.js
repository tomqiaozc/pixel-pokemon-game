// cutscene.js — Scripted event/cutscene engine for story sequences

const Cutscene = (() => {
    let active = false;
    let steps = [];
    let stepIndex = 0;
    let stepTimer = 0;
    let waitingForInput = false;

    // Camera pan state
    let panTarget = null;
    let panSpeed = 0;
    let panDone = false;

    // NPC movement in cutscene
    let movingNpc = null;
    let moveTarget = null;
    let moveDone = false;

    // Screen effects
    let fadeAlpha = 0;
    let fadeTarget = 0;
    let fadeSpeed = 0;
    let shakeIntensity = 0;
    let shakeTimer = 0;

    // Cutscene step types:
    // { type: 'dialogue', speaker, lines }
    // { type: 'wait', duration }
    // { type: 'camera_pan', x, y, speed }
    // { type: 'npc_move', npcName, toX, toY, speed }
    // { type: 'fade', target, speed }  — 0=clear, 1=black
    // { type: 'shake', intensity, duration }
    // { type: 'set_flag', flag }
    // { type: 'battle', enemyData, options }
    // { type: 'callback', fn }
    // { type: 'npc_face', npcName, dir }
    // { type: 'choice', speaker, prompt, choices }

    function start(cutsceneSteps) {
        active = true;
        steps = cutsceneSteps;
        stepIndex = 0;
        stepTimer = 0;
        waitingForInput = false;
        panTarget = null;
        movingNpc = null;
        fadeAlpha = 0;
        fadeTarget = 0;
        shakeIntensity = 0;
        shakeTimer = 0;
        beginStep();
    }

    function isActive() { return active; }

    function beginStep() {
        if (stepIndex >= steps.length) {
            active = false;
            return;
        }

        const step = steps[stepIndex];
        stepTimer = 0;

        if (step.type === 'dialogue') {
            Dialogue.start(step.speaker, step.lines);
            waitingForInput = true;
        } else if (step.type === 'wait') {
            waitingForInput = false;
        } else if (step.type === 'camera_pan') {
            panTarget = { x: step.x, y: step.y };
            panSpeed = step.speed || 2;
            panDone = false;
            waitingForInput = false;
        } else if (step.type === 'npc_move') {
            movingNpc = step.npcName;
            moveTarget = { x: step.toX, y: step.toY };
            moveDone = false;
            waitingForInput = false;
        } else if (step.type === 'fade') {
            fadeTarget = step.target;
            fadeSpeed = step.speed || 0.003;
            waitingForInput = false;
        } else if (step.type === 'shake') {
            shakeIntensity = step.intensity || 5;
            shakeTimer = step.duration || 500;
            waitingForInput = false;
        } else if (step.type === 'set_flag') {
            Quests.setFlag(step.flag);
            advanceStep();
        } else if (step.type === 'battle') {
            // Will be handled by game.js checking the result
            waitingForInput = false;
        } else if (step.type === 'callback') {
            if (typeof step.fn === 'function') step.fn();
            advanceStep();
        } else if (step.type === 'npc_face') {
            NPC.setDirection(step.npcName, step.dir);
            advanceStep();
        } else if (step.type === 'choice') {
            Dialogue.startChoice(step.speaker, step.prompt, step.choices);
            waitingForInput = true;
        }
    }

    function advanceStep() {
        stepIndex++;
        beginStep();
    }

    function update(dt) {
        if (!active) return null;

        const step = steps[stepIndex];
        if (!step) { active = false; return null; }

        stepTimer += dt;

        // Update fade
        if (fadeTarget !== fadeAlpha) {
            const dir = fadeTarget > fadeAlpha ? 1 : -1;
            fadeAlpha += dir * fadeSpeed * dt;
            if ((dir > 0 && fadeAlpha >= fadeTarget) || (dir < 0 && fadeAlpha <= fadeTarget)) {
                fadeAlpha = fadeTarget;
            }
        }

        // Update shake
        if (shakeTimer > 0) {
            shakeTimer = Math.max(0, shakeTimer - dt);
            if (shakeTimer <= 0) shakeIntensity = 0;
        }

        // Step-specific updates
        if (step.type === 'dialogue' || step.type === 'choice') {
            if (!Dialogue.isActive()) {
                advanceStep();
            }
        } else if (step.type === 'wait') {
            if (stepTimer >= step.duration) {
                advanceStep();
            }
        } else if (step.type === 'camera_pan') {
            // Camera panning handled by renderer reading panTarget
            if (panDone) advanceStep();
        } else if (step.type === 'npc_move') {
            if (moveDone) advanceStep();
        } else if (step.type === 'fade') {
            if (fadeAlpha === fadeTarget) {
                advanceStep();
            }
        } else if (step.type === 'shake') {
            if (shakeTimer <= 0) {
                advanceStep();
            }
        } else if (step.type === 'battle') {
            // Return battle trigger for game.js to handle
            return { startBattle: true, enemy: step.enemyData, options: step.options };
        }

        return null;
    }

    // Called by game.js after cutscene battle ends
    function onBattleEnd(result) {
        if (active && steps[stepIndex] && steps[stepIndex].type === 'battle') {
            advanceStep();
        }
    }

    function renderOverlay(ctx, canvasW, canvasH) {
        // Fade overlay
        if (fadeAlpha > 0) {
            ctx.fillStyle = `rgba(0, 0, 0, ${fadeAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }
    }

    // Get shake offset for renderer
    function getShakeOffset() {
        if (shakeIntensity <= 0) return { x: 0, y: 0 };
        return {
            x: (Math.random() - 0.5) * shakeIntensity * 2,
            y: (Math.random() - 0.5) * shakeIntensity * 2,
        };
    }

    function getPanTarget() { return panTarget; }
    function setPanDone() { panDone = true; }
    function getMovingNpc() { return movingNpc; }
    function getMoveTarget() { return moveTarget; }
    function setMoveDone() { moveDone = true; movingNpc = null; moveTarget = null; }

    // Pre-built cutscene sequences
    const SCENES = {
        oak_post_starter: () => [
            { type: 'dialogue', speaker: 'Prof. Oak', lines: [
                'Excellent choice!',
                'Your very own Pokemon legend is about to unfold!',
                'A world of dreams and adventures with Pokemon awaits!',
            ]},
            { type: 'set_flag', flag: 'received_pokedex' },
            { type: 'dialogue', speaker: 'Prof. Oak', lines: [
                'Here, take this Pokedex with you.',
                'It will automatically record data on every Pokemon you encounter.',
                'Now go! The wide world of Pokemon awaits!',
            ]},
        ],

        rival_oaks_lab: (rivalName, rivalStarter) => [
            { type: 'wait', duration: 400 },
            { type: 'dialogue', speaker: '???', lines: ["Gramps! I'm here too!"] },
            { type: 'dialogue', speaker: rivalName, lines: [
                rivalName + ": Hey, so you picked your Pokemon already?",
                "Then I'll take this one!",
            ]},
            { type: 'dialogue', speaker: rivalName, lines: [
                "Heh, " + rivalStarter.name + "! A fine choice.",
                "My Pokemon is way tougher than yours!",
                "Smell ya later!",
            ]},
            { type: 'set_flag', flag: 'rival_oaks_lab_met' },
        ],

        rival_route2: (rivalName, rivalStarter, rivalTeam) => {
            const lead = rivalTeam && rivalTeam.length > 0 ? rivalTeam[0] : {
                name: rivalStarter.name, type: rivalStarter.type,
                level: 15, hp: 42, maxHp: 42,
            };
            return [
                { type: 'fade', target: 0.5, speed: 0.004 },
                { type: 'wait', duration: 300 },
                { type: 'dialogue', speaker: '???', lines: ['Hey! Wait up!'] },
                { type: 'fade', target: 0, speed: 0.004 },
                { type: 'set_flag', flag: 'rival_route2_met' },
                { type: 'dialogue', speaker: rivalName, lines: [
                    rivalName + ": I've been training since we last met at the lab.",
                    "My Pokemon are way stronger now!",
                    "Let me show you what real training looks like!",
                ]},
                { type: 'shake', intensity: 3, duration: 300 },
                { type: 'battle', enemyData: lead,
                  options: { canRun: false, battleType: 'trainer' }},
                { type: 'set_flag', flag: 'rival_route2_defeated' },
                { type: 'dialogue', speaker: rivalName, lines: [
                    "Hmph... Not bad. You actually beat me.",
                    "But don't get cocky! I'll be even stronger next time!",
                    "See you around, loser!",
                ]},
            ];
        },

        gym_leader_intro: (leaderName, leaderTitle) => [
            { type: 'dialogue', speaker: leaderName, lines: [
                leaderName + ': So, a new challenger approaches!',
                'I am ' + leaderName + ', ' + leaderTitle + '.',
                "Show me what you've got!",
            ]},
            { type: 'shake', intensity: 2, duration: 200 },
        ],

        gym_leader_defeat: (leaderName, badgeName) => [
            { type: 'dialogue', speaker: leaderName, lines: [
                leaderName + ": Incredible... You've earned this.",
                'Take the ' + badgeName + '. You deserve it.',
            ]},
        ],

        shopkeeper_parcel: () => [
            { type: 'dialogue', speaker: 'Shopkeeper', lines: [
                'Oh! You must be the trainer Prof. Oak mentioned.',
                'Here, take this parcel back to him.',
                "He's been waiting for it!",
            ]},
            { type: 'set_flag', flag: 'got_parcel' },
            { type: 'dialogue', speaker: 'Shopkeeper', lines: [
                'Safe travels, young trainer!',
            ]},
        ],

        oak_receives_parcel: () => [
            { type: 'dialogue', speaker: 'Prof. Oak', lines: [
                'Ah, you brought the parcel! Thank you!',
                'Let me see... Ah yes, this is exactly what I needed.',
                'As thanks, let me upgrade your Pokedex.',
                'The National Pokedex will now record even more data!',
            ]},
            { type: 'set_flag', flag: 'delivered_parcel' },
            { type: 'dialogue', speaker: 'Prof. Oak', lines: [
                'I hear the Gym Leader in Pewter City is quite strong.',
                "With your skills, I'm sure you'll do great!",
            ]},
        ],

        area_blocked: (npcName, reason) => [
            { type: 'dialogue', speaker: npcName, lines: [reason] },
        ],
    };

    return {
        start, isActive, update, onBattleEnd,
        renderOverlay, getShakeOffset,
        getPanTarget, setPanDone,
        getMovingNpc, getMoveTarget, setMoveDone,
        SCENES,
    };
})();
