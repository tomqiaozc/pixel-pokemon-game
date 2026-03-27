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
        if (step.type === 'dialogue') {
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
        rival_route2: (rivalName, rivalStarter) => [
            { type: 'fade', target: 0.5, speed: 0.004 },
            { type: 'wait', duration: 300 },
            { type: 'dialogue', speaker: '???', lines: ['Hey! Wait up!'] },
            { type: 'fade', target: 0, speed: 0.004 },
            { type: 'dialogue', speaker: rivalName, lines: [
                `${rivalName}: I\'ve been looking for you!`,
                'My Pokemon have gotten way stronger since we last met.',
                'Let\'s see if yours have too!',
            ]},
            { type: 'shake', intensity: 3, duration: 300 },
            { type: 'battle', enemyData: {
                name: rivalStarter.name,
                type: rivalStarter.type,
                level: 12,
                hp: 38,
                maxHp: 38,
            }, options: { canRun: false, battleType: 'trainer' }},
            { type: 'set_flag', flag: 'rival_route2_defeated' },
            { type: 'dialogue', speaker: rivalName, lines: [
                'Not bad... You\'ve gotten stronger.',
                'But next time, I won\'t lose!',
            ]},
        ],

        gym_leader_intro: (leaderName, leaderTitle) => [
            { type: 'dialogue', speaker: leaderName, lines: [
                `${leaderName}: So, a new challenger approaches!`,
                `I am ${leaderName}, ${leaderTitle}.`,
                'Show me what you\'ve got!',
            ]},
            { type: 'shake', intensity: 2, duration: 200 },
        ],

        gym_leader_defeat: (leaderName, badgeName) => [
            { type: 'dialogue', speaker: leaderName, lines: [
                `${leaderName}: Incredible... You\'ve earned this.`,
                `Take the ${badgeName}. You deserve it.`,
            ]},
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
