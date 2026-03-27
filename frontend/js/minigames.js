// minigames.js — Mini-game framework: slots, memory match, quiz

const MiniGames = (() => {
    let active = false;
    let currentGame = null;  // 'slots', 'memory', 'quiz'
    let coins = 0;
    let actionCooldown = 0;

    // ---- Slot Machine ----
    const SLOT_SYMBOLS = [
        { name: 'Cherry',   color: '#e04040', char: 'C', payout: 5 },
        { name: 'Pokeball', color: '#e05040', char: 'P', payout: 8 },
        { name: 'Bar',      color: '#a0a0a0', char: 'B', payout: 15 },
        { name: '7',        color: '#f8d030', char: '7', payout: 100 },
        { name: 'Pikachu',  color: '#f8d830', char: '\u26A1', payout: 300 },
    ];
    let reels = [0, 0, 0]; // current symbol index per reel
    let reelSpeeds = [0, 0, 0];
    let reelTimers = [0, 0, 0];
    let reelsStopped = [false, false, false];
    let spinning = false;
    let slotResult = null;  // null, 'win', 'lose'
    let slotWinAmount = 0;
    let slotResultTimer = 0;

    // ---- Memory Match ----
    let memoryCards = [];
    let memoryRevealed = [];
    let memoryMatched = [];
    let memoryFirst = -1;   // index of first flipped card
    let memorySecond = -1;
    let memoryTimer = 0;
    let memoryGridW = 4;
    let memoryGridH = 4;
    let memoryCheckTimer = 0;
    let memoryMoves = 0;
    let memoryTimeLeft = 60;
    let memoryDone = false;

    // ---- Quiz ----
    let quizQuestion = '';
    let quizOptions = [];
    let quizAnswer = -1;
    let quizChoice = 0;
    let quizScore = 0;
    let quizRound = 0;
    let quizTotal = 5;
    let quizResult = null; // null, 'correct', 'wrong'
    let quizResultTimer = 0;
    let quizDone = false;

    const QUIZ_BANK = [
        { q: 'What type is Pikachu?', opts: ['Electric', 'Normal', 'Fire', 'Water'], a: 0 },
        { q: 'What does Bulbasaur evolve into?', opts: ['Ivysaur', 'Charmeleon', 'Wartortle', 'Metapod'], a: 0 },
        { q: 'Which type is super effective against Water?', opts: ['Grass', 'Fire', 'Rock', 'Ice'], a: 0 },
        { q: 'What is the first Gym Leader\'s name?', opts: ['Brock', 'Misty', 'Lt. Surge', 'Erika'], a: 0 },
        { q: 'How many Pokemon types are there?', opts: ['18', '15', '12', '20'], a: 0 },
        { q: 'Which Pokemon is number 25 in the Pokedex?', opts: ['Pikachu', 'Raichu', 'Jolteon', 'Electabuzz'], a: 0 },
        { q: 'What type is Geodude?', opts: ['Rock', 'Ground', 'Steel', 'Normal'], a: 0 },
        { q: 'What move does Charmander learn first?', opts: ['Scratch', 'Ember', 'Tackle', 'Growl'], a: 0 },
        { q: 'Which berry heals HP?', opts: ['Oran Berry', 'Cheri Berry', 'Rawst Berry', 'Lum Berry'], a: 0 },
        { q: 'What is Brock\'s specialty type?', opts: ['Rock', 'Ground', 'Steel', 'Normal'], a: 0 },
    ];

    function getCoins() { return coins; }
    function addCoins(n) { coins += n; }
    function isActive() { return active; }
    function getCurrentGame() { return currentGame; }

    // ---- Start games ----
    function startSlots() {
        if (coins < 3) return false;
        active = true;
        currentGame = 'slots';
        coins -= 3;
        spinning = false;
        slotResult = null;
        slotWinAmount = 0;
        reels = [0, 0, 0];
        reelsStopped = [true, true, true];
        actionCooldown = 300;
        return true;
    }

    function startMemory(difficulty) {
        active = true;
        currentGame = 'memory';
        memoryGridW = difficulty === 'hard' ? 6 : difficulty === 'medium' ? 5 : 4;
        memoryGridH = 4;
        const totalCards = memoryGridW * memoryGridH;
        const pairs = totalCards / 2;

        // Generate pairs
        const symbols = [];
        for (let i = 0; i < pairs; i++) {
            symbols.push(i % SLOT_SYMBOLS.length, i % SLOT_SYMBOLS.length);
        }
        // Shuffle
        for (let i = symbols.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [symbols[i], symbols[j]] = [symbols[j], symbols[i]];
        }

        memoryCards = symbols;
        memoryRevealed = new Array(totalCards).fill(false);
        memoryMatched = new Array(totalCards).fill(false);
        memoryFirst = -1;
        memorySecond = -1;
        memoryCheckTimer = 0;
        memoryMoves = 0;
        memoryTimeLeft = difficulty === 'hard' ? 90 : difficulty === 'medium' ? 75 : 60;
        memoryDone = false;
        actionCooldown = 300;
    }

    function startQuiz() {
        active = true;
        currentGame = 'quiz';
        quizScore = 0;
        quizRound = 0;
        quizChoice = 0;
        quizResult = null;
        quizResultTimer = 0;
        quizDone = false;
        actionCooldown = 300;
        nextQuizQuestion();
    }

    function nextQuizQuestion() {
        if (quizRound >= quizTotal) {
            quizDone = true;
            const reward = quizScore * 5 + (quizScore === quizTotal ? 50 : 0);
            coins += reward;
            return;
        }
        const q = QUIZ_BANK[quizRound % QUIZ_BANK.length];
        quizQuestion = q.q;
        quizOptions = [...q.opts];
        quizAnswer = q.a;
        quizChoice = 0;
        quizResult = null;
    }

    function exit() {
        active = false;
        currentGame = null;
    }

    // ---- Update ----
    function update(dt) {
        if (!active) return;
        actionCooldown = Math.max(0, actionCooldown - dt);

        if (currentGame === 'slots') updateSlots(dt);
        else if (currentGame === 'memory') updateMemory(dt);
        else if (currentGame === 'quiz') updateQuiz(dt);
    }

    function updateSlots(dt) {
        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b')) && actionCooldown <= 0;

        if (back && !spinning) { exit(); return; }

        // Result display
        if (slotResult) {
            slotResultTimer += dt;
            if (slotResultTimer > 2000 || action) {
                slotResult = null;
                slotResultTimer = 0;
                actionCooldown = 200;
            }
            return;
        }

        // Spin reels
        if (!spinning && action) {
            if (coins < 3) return;
            coins -= 3;
            spinning = true;
            reelsStopped = [false, false, false];
            reelSpeeds = [0.3, 0.3, 0.3];
            reelTimers = [800, 1300, 1800]; // stagger stops
            actionCooldown = 200;
        }

        if (spinning) {
            for (let i = 0; i < 3; i++) {
                if (!reelsStopped[i]) {
                    reelTimers[i] -= dt;
                    reels[i] = (reels[i] + reelSpeeds[i] * dt * 0.01) % SLOT_SYMBOLS.length;

                    if (reelTimers[i] <= 0) {
                        reelsStopped[i] = true;
                        reels[i] = Math.floor(reels[i]) % SLOT_SYMBOLS.length;
                    }
                }
            }

            if (reelsStopped.every(s => s)) {
                spinning = false;
                checkSlotResult();
            }
        }
    }

    function checkSlotResult() {
        const r0 = Math.floor(reels[0]) % SLOT_SYMBOLS.length;
        const r1 = Math.floor(reels[1]) % SLOT_SYMBOLS.length;
        const r2 = Math.floor(reels[2]) % SLOT_SYMBOLS.length;

        if (r0 === r1 && r1 === r2) {
            slotResult = 'win';
            slotWinAmount = SLOT_SYMBOLS[r0].payout;
            coins += slotWinAmount;
        } else if (r0 === r1 || r1 === r2) {
            slotResult = 'win';
            slotWinAmount = 2;
            coins += 2;
        } else {
            slotResult = 'lose';
            slotWinAmount = 0;
        }
        slotResultTimer = 0;
    }

    function updateMemory(dt) {
        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (memoryDone) {
            if (action || back) { exit(); return; }
            return;
        }

        if (back) { exit(); return; }

        memoryTimeLeft -= dt / 1000;
        if (memoryTimeLeft <= 0) {
            memoryDone = true;
            return;
        }

        // Check match after reveal delay
        if (memoryCheckTimer > 0) {
            memoryCheckTimer -= dt;
            if (memoryCheckTimer <= 0) {
                if (memoryCards[memoryFirst] === memoryCards[memorySecond]) {
                    memoryMatched[memoryFirst] = true;
                    memoryMatched[memorySecond] = true;
                } else {
                    memoryRevealed[memoryFirst] = false;
                    memoryRevealed[memorySecond] = false;
                }
                memoryFirst = -1;
                memorySecond = -1;

                // Check win
                if (memoryMatched.every(m => m)) {
                    memoryDone = true;
                    const timeBonus = Math.floor(memoryTimeLeft * 1.5);
                    const reward = 10 + timeBonus;
                    coins += reward;
                }
            }
            return;
        }

        // Card selection - use simple cursor based on flat index
        if (!memoryDone && memoryFirst >= 0 && memorySecond >= 0) return;

        // Use cursor index stored in memoryMoves as a proxy — actually let's use a cursor var
        // (using memoryFirst/Second tracking instead)
    }

    function updateQuiz(dt) {
        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (quizDone) {
            if (action || back) { exit(); return; }
            return;
        }

        if (back) { exit(); return; }

        if (quizResult) {
            quizResultTimer += dt;
            if (quizResultTimer > 1500 || action) {
                quizRound++;
                nextQuizQuestion();
                actionCooldown = 200;
            }
            return;
        }

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { quizChoice = Math.max(0, quizChoice - 1); actionCooldown = 150; }
            if (mov.dy > 0) { quizChoice = Math.min(quizOptions.length - 1, quizChoice + 1); actionCooldown = 150; }
        }

        if (action) {
            actionCooldown = 200;
            if (quizChoice === quizAnswer) {
                quizResult = 'correct';
                quizScore++;
            } else {
                quizResult = 'wrong';
            }
            quizResultTimer = 0;
        }
    }

    // ---- Render ----
    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        if (currentGame === 'slots') renderSlots(ctx, canvasW, canvasH);
        else if (currentGame === 'memory') renderMemory(ctx, canvasW, canvasH);
        else if (currentGame === 'quiz') renderQuiz(ctx, canvasW, canvasH);
    }

    function renderCoinCounter(ctx, x, y) {
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`\u{1F4B0} ${coins}`, x, y);
        ctx.textAlign = 'left';
    }

    function renderSlots(ctx, canvasW, canvasH) {
        // Background
        ctx.fillStyle = '#1a0a2a';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Title
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('SLOT MACHINE', canvasW / 2, 35);

        // Coin counter
        renderCoinCounter(ctx, canvasW - 20, 30);

        // Machine frame
        const mw = 240;
        const mh = 120;
        const mx = (canvasW - mw) / 2;
        const my = 55;

        ctx.fillStyle = '#c02020';
        ctx.fillRect(mx - 10, my - 10, mw + 20, mh + 20);
        ctx.fillStyle = '#800010';
        ctx.strokeStyle = '#f8d030';
        ctx.lineWidth = 3;
        ctx.strokeRect(mx - 10, my - 10, mw + 20, mh + 20);
        ctx.fillStyle = '#202020';
        ctx.fillRect(mx, my, mw, mh);

        // Reels
        for (let i = 0; i < 3; i++) {
            const rx = mx + 10 + i * 78;
            const ry = my + 10;
            const rw = 60;
            const rh = mh - 20;

            ctx.fillStyle = '#f8f8f0';
            ctx.fillRect(rx, ry, rw, rh);
            ctx.strokeStyle = '#404040';
            ctx.lineWidth = 2;
            ctx.strokeRect(rx, ry, rw, rh);

            // Symbol
            const symIdx = Math.floor(reels[i]) % SLOT_SYMBOLS.length;
            const sym = SLOT_SYMBOLS[symIdx];
            ctx.fillStyle = sym.color;
            ctx.font = 'bold 32px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(sym.char, rx + rw / 2, ry + rh / 2 + 12);
        }

        // Cost info
        ctx.fillStyle = '#c0c0c0';
        ctx.font = '11px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Cost: 3 coins per spin', canvasW / 2, my + mh + 24);

        // Result
        if (slotResult) {
            ctx.fillStyle = slotResult === 'win' ? '#48c048' : '#c04040';
            ctx.font = 'bold 18px monospace';
            ctx.fillText(
                slotResult === 'win' ? `WIN! +${slotWinAmount} coins!` : 'No match...',
                canvasW / 2, my + mh + 50
            );
        }

        // Instructions
        ctx.fillStyle = '#808080';
        ctx.font = '10px monospace';
        ctx.fillText(spinning ? 'Spinning...' : 'Z: Spin | Esc: Exit', canvasW / 2, canvasH - 15);
        ctx.textAlign = 'left';
    }

    function renderMemory(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#0a2a1a';
        ctx.fillRect(0, 0, canvasW, canvasH);

        ctx.fillStyle = '#48c048';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('MEMORY MATCH', canvasW / 2, 30);

        renderCoinCounter(ctx, canvasW - 20, 28);

        // Timer
        ctx.fillStyle = memoryTimeLeft < 10 ? '#e04040' : '#c0c0c0';
        ctx.font = '12px monospace';
        ctx.fillText(`Time: ${Math.ceil(memoryTimeLeft)}s`, canvasW / 2, 48);

        // Cards grid
        const cardW = 40;
        const cardH = 50;
        const gap = 6;
        const gridTotalW = memoryGridW * (cardW + gap) - gap;
        const startX = (canvasW - gridTotalW) / 2;
        const startY = 60;

        for (let i = 0; i < memoryCards.length; i++) {
            const col = i % memoryGridW;
            const row = Math.floor(i / memoryGridW);
            const cx = startX + col * (cardW + gap);
            const cy = startY + row * (cardH + gap);

            if (memoryMatched[i]) {
                // Matched — show faded
                ctx.fillStyle = 'rgba(72, 192, 72, 0.2)';
                ctx.fillRect(cx, cy, cardW, cardH);
            } else if (memoryRevealed[i]) {
                // Revealed — show symbol
                ctx.fillStyle = '#f8f8f0';
                ctx.fillRect(cx, cy, cardW, cardH);
                const sym = SLOT_SYMBOLS[memoryCards[i] % SLOT_SYMBOLS.length];
                ctx.fillStyle = sym.color;
                ctx.font = 'bold 22px monospace';
                ctx.fillText(sym.char, cx + cardW / 2, cy + cardH / 2 + 8);
            } else {
                // Face down
                ctx.fillStyle = '#3060a0';
                ctx.fillRect(cx, cy, cardW, cardH);
                ctx.strokeStyle = '#4080c0';
                ctx.lineWidth = 1;
                ctx.strokeRect(cx, cy, cardW, cardH);
                ctx.fillStyle = '#4080c0';
                ctx.font = '18px monospace';
                ctx.fillText('?', cx + cardW / 2, cy + cardH / 2 + 6);
            }
        }

        if (memoryDone) {
            ctx.fillStyle = 'rgba(0,0,0,0.6)';
            ctx.fillRect(0, 0, canvasW, canvasH);
            ctx.fillStyle = memoryMatched.every(m => m) ? '#48c048' : '#e04040';
            ctx.font = 'bold 20px monospace';
            ctx.fillText(memoryMatched.every(m => m) ? 'YOU WIN!' : 'TIME UP!', canvasW / 2, canvasH / 2);
        }

        ctx.fillStyle = '#606060';
        ctx.font = '10px monospace';
        ctx.fillText('Esc: Exit', canvasW / 2, canvasH - 10);
        ctx.textAlign = 'left';
    }

    function renderQuiz(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#1a1a3a';
        ctx.fillRect(0, 0, canvasW, canvasH);

        ctx.fillStyle = '#f85888';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('POKEMON QUIZ', canvasW / 2, 30);

        renderCoinCounter(ctx, canvasW - 20, 28);

        // Score
        ctx.fillStyle = '#c0c0c0';
        ctx.font = '12px monospace';
        ctx.fillText(`Question ${quizRound + 1}/${quizTotal}  Score: ${quizScore}`, canvasW / 2, 48);

        if (quizDone) {
            ctx.fillStyle = '#f8d030';
            ctx.font = 'bold 20px monospace';
            ctx.fillText(`Final Score: ${quizScore}/${quizTotal}`, canvasW / 2, canvasH / 2 - 20);
            const reward = quizScore * 5 + (quizScore === quizTotal ? 50 : 0);
            ctx.fillStyle = '#48c048';
            ctx.font = '14px monospace';
            ctx.fillText(`Earned: ${reward} coins!`, canvasW / 2, canvasH / 2 + 10);
            ctx.fillStyle = '#808080';
            ctx.font = '10px monospace';
            ctx.fillText('Press Z to exit', canvasW / 2, canvasH / 2 + 40);
            ctx.textAlign = 'left';
            return;
        }

        // Question
        ctx.fillStyle = '#f8f8f8';
        ctx.font = '14px monospace';
        ctx.fillText(quizQuestion, canvasW / 2, 80);

        // Options
        for (let i = 0; i < quizOptions.length; i++) {
            const oy = 100 + i * 36;
            const ow = 280;
            const ox = (canvasW - ow) / 2;

            let bg = 'rgba(255,255,255,0.1)';
            if (quizResult && i === quizAnswer) bg = 'rgba(72,192,72,0.4)';
            else if (quizResult === 'wrong' && i === quizChoice) bg = 'rgba(224,64,56,0.4)';
            else if (i === quizChoice && !quizResult) bg = 'rgba(80,80,200,0.4)';

            ctx.fillStyle = bg;
            ctx.fillRect(ox, oy, ow, 30);
            if (i === quizChoice && !quizResult) {
                ctx.strokeStyle = '#8080c0';
                ctx.lineWidth = 1;
                ctx.strokeRect(ox, oy, ow, 30);
            }

            ctx.fillStyle = '#f8f8f8';
            ctx.font = '13px monospace';
            ctx.fillText(quizOptions[i], canvasW / 2, oy + 20);
        }

        // Result feedback
        if (quizResult) {
            ctx.fillStyle = quizResult === 'correct' ? '#48c048' : '#e04040';
            ctx.font = 'bold 16px monospace';
            ctx.fillText(quizResult === 'correct' ? 'Correct! +5 coins' : 'Wrong!', canvasW / 2, 270);
        }

        ctx.fillStyle = '#606060';
        ctx.font = '10px monospace';
        ctx.fillText('Esc: Exit', canvasW / 2, canvasH - 10);
        ctx.textAlign = 'left';
    }

    return {
        isActive, getCurrentGame, getCoins, addCoins, exit,
        startSlots, startMemory, startQuiz,
        update, render, renderCoinCounter,
    };
})();
