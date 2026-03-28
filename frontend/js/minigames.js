// minigames.js — Mini-game framework: slots, memory match, quiz, prize exchange
// ALL game results go through the backend API. Coins are server-authoritative.

const MiniGames = (() => {
    let active = false;
    let currentGame = null;  // 'slots', 'memory', 'quiz', 'prizes', 'buy_coins'
    let coins = 0;           // local cache — always synced from API
    let actionCooldown = 0;
    let loading = false;     // true while waiting for an API response

    // ---- Sync coins from backend ----
    async function syncCoins() {
        const data = await API.getCoins();
        if (data && data.coins !== undefined) {
            coins = data.coins;
        }
        return coins;
    }

    // ---- Slot Machine ----
    const SLOT_SYMBOLS = [
        { name: 'Pokeball', color: '#e05040', char: 'P' },
        { name: 'Cherry',   color: '#e04040', char: 'C' },
        { name: 'Bar',      color: '#a0a0a0', char: 'B' },
        { name: '7',        color: '#f8d030', char: '7' },
        { name: 'Pikachu',  color: '#f8d830', char: '\u26A1' },
        { name: 'Mewtwo',   color: '#9060c0', char: 'M' },
    ];
    // Symbol name → display index for rendering server results
    const SYMBOL_INDEX = {};
    SLOT_SYMBOLS.forEach((s, i) => SYMBOL_INDEX[s.name] = i);

    let reels = [0, 0, 0];
    let reelSpeeds = [0, 0, 0];
    let reelTimers = [0, 0, 0];
    let reelsStopped = [false, false, false];
    let spinning = false;
    let slotResult = null;  // null, 'win', 'lose'
    let slotWinAmount = 0;
    let slotResultTimer = 0;
    let slotBet = 1;
    let pendingSpinResult = null; // server response stored until reels stop

    // ---- Memory Match ----
    let memoryCards = [];
    let memoryRevealed = [];
    let memoryMatched = [];
    let memoryFirst = -1;
    let memorySecond = -1;
    let memoryCheckTimer = 0;
    let memoryMoves = 0;
    let memoryTimeLeft = 60;
    let memoryDone = false;
    let memoryGridW = 4;
    let memoryGridH = 4;
    let memoryCursor = 0;      // flat index for card selection
    let memoryDifficulty = 'easy';
    let memoryStartTime = 0;
    let memoryPairsMatched = 0;

    // ---- Quiz ----
    let quizQuestion = '';
    let quizOptions = [];
    let quizChoice = 0;
    let quizScore = 0;
    let quizRound = 0;
    let quizTotal = 10;
    let quizResult = null;
    let quizResultTimer = 0;
    let quizDone = false;
    let quizSessionId = null;
    let quizQuestions = [];     // questions from backend
    let quizAnswers = [];       // player's answers to send on submit

    // ---- Prize Exchange ----
    let prizes = [];
    let prizeCursor = 0;
    let prizeMessage = '';
    let prizeMessageTimer = 0;

    // ---- Buy Coins ----
    const COIN_PACKAGES = [
        { money: 1000, coins: 50, label: '$1000 = 50 coins' },
        { money: 2000, coins: 100, label: '$2000 = 100 coins' },
        { money: 5000, coins: 250, label: '$5000 = 250 coins' },
    ];
    let buyCoinsCursor = 0;
    let buyCoinsMessage = '';
    let buyCoinsMessageTimer = 0;

    // ---- Local quiz fallback bank ----
    const QUIZ_BANK = [
        { q: 'What type is Pikachu?', opts: ['Electric', 'Normal', 'Fire', 'Water'], a: 0 },
        { q: 'What does Bulbasaur evolve into?', opts: ['Ivysaur', 'Charmeleon', 'Wartortle', 'Metapod'], a: 0 },
        { q: 'Which type is super effective against Water?', opts: ['Grass', 'Fire', 'Rock', 'Ice'], a: 0 },
        { q: "What is the first Gym Leader's name?", opts: ['Brock', 'Misty', 'Lt. Surge', 'Erika'], a: 0 },
        { q: 'How many Pokemon types are there?', opts: ['18', '15', '12', '20'], a: 0 },
        { q: 'Which Pokemon is number 25 in the Pokedex?', opts: ['Pikachu', 'Raichu', 'Jolteon', 'Electabuzz'], a: 0 },
        { q: 'What type is Geodude?', opts: ['Rock', 'Ground', 'Steel', 'Normal'], a: 0 },
        { q: 'What move does Charmander learn first?', opts: ['Scratch', 'Ember', 'Tackle', 'Growl'], a: 0 },
        { q: 'Which berry heals HP?', opts: ['Oran Berry', 'Cheri Berry', 'Rawst Berry', 'Lum Berry'], a: 0 },
        { q: "What is Brock's specialty type?", opts: ['Rock', 'Ground', 'Steel', 'Normal'], a: 0 },
    ];

    function getCoins() { return coins; }
    function isActive() { return active; }
    function getCurrentGame() { return currentGame; }

    // ---- Start games ----

    async function startSlots() {
        active = true;
        currentGame = 'slots';
        spinning = false;
        slotResult = null;
        slotWinAmount = 0;
        slotBet = 1;
        reels = [0, 0, 0];
        reelsStopped = [true, true, true];
        pendingSpinResult = null;
        actionCooldown = 300;
        loading = true;
        await syncCoins();
        loading = false;
        return true;
    }

    async function startMemory(difficulty) {
        memoryDifficulty = difficulty || 'easy';
        active = true;
        currentGame = 'memory';
        memoryGridW = memoryDifficulty === 'hard' ? 6 : memoryDifficulty === 'medium' ? 5 : 4;
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
        memoryCursor = 0;
        memoryPairsMatched = 0;
        memoryTimeLeft = memoryDifficulty === 'hard' ? 90 : memoryDifficulty === 'medium' ? 75 : 60;
        memoryDone = false;
        memoryStartTime = Date.now();
        actionCooldown = 300;

        // Register game start with backend
        loading = true;
        await syncCoins();
        API.startMemoryGame(memoryDifficulty).catch(() => {});
        loading = false;
    }

    async function startQuiz() {
        active = true;
        currentGame = 'quiz';
        quizScore = 0;
        quizRound = 0;
        quizChoice = 0;
        quizResult = null;
        quizResultTimer = 0;
        quizDone = false;
        quizSessionId = null;
        quizQuestions = [];
        quizAnswers = [];
        actionCooldown = 300;

        // Fetch quiz from backend
        loading = true;
        await syncCoins();
        const data = await API.startQuiz();
        loading = false;

        if (data && data.session_id && data.questions && data.questions.length > 0) {
            quizSessionId = data.session_id;
            quizQuestions = data.questions;
            quizTotal = quizQuestions.length;
            loadQuizQuestion(0);
        } else {
            // Fallback to local quiz
            quizSessionId = null;
            quizQuestions = [];
            quizTotal = 5;
            nextLocalQuizQuestion();
        }
    }

    async function startPrizes() {
        active = true;
        currentGame = 'prizes';
        prizeCursor = 0;
        prizeMessage = '';
        prizeMessageTimer = 0;
        actionCooldown = 300;

        loading = true;
        await syncCoins();
        const data = await API.getPrizes();
        loading = false;

        if (data && Array.isArray(data)) {
            prizes = data;
        } else {
            prizes = [];
        }
    }

    async function startBuyCoins() {
        active = true;
        currentGame = 'buy_coins';
        buyCoinsCursor = 0;
        buyCoinsMessage = '';
        buyCoinsMessageTimer = 0;
        actionCooldown = 300;

        loading = true;
        await syncCoins();
        loading = false;
    }

    function loadQuizQuestion(index) {
        if (index >= quizQuestions.length) {
            finishQuiz();
            return;
        }
        const q = quizQuestions[index];
        quizQuestion = q.question;
        quizOptions = q.options || q.choices || [];
        quizChoice = 0;
        quizResult = null;
    }

    function nextLocalQuizQuestion() {
        if (quizRound >= quizTotal) {
            quizDone = true;
            // Offline mode — no coin reward without backend
            quizResult = 'Offline mode — practice only, no coins awarded';
            return;
        }
        const q = QUIZ_BANK[quizRound % QUIZ_BANK.length];
        quizQuestion = q.q;
        quizOptions = [...q.opts];
        quizChoice = 0;
        quizResult = null;
    }

    async function finishQuiz() {
        loading = true;
        if (quizSessionId) {
            const result = await API.submitQuiz(quizSessionId, quizAnswers);
            if (result) {
                quizScore = result.score || quizScore;
                if (result.coins_after !== undefined) coins = result.coins_after;
            }
        }
        loading = false;
        quizDone = true;
    }

    function exit() {
        active = false;
        currentGame = null;
    }

    // ---- Update ----
    function update(dt) {
        if (!active) return;
        actionCooldown = Math.max(0, actionCooldown - dt);

        if (loading) return; // wait for API response

        if (currentGame === 'slots') updateSlots(dt);
        else if (currentGame === 'memory') updateMemory(dt);
        else if (currentGame === 'quiz') updateQuiz(dt);
        else if (currentGame === 'prizes') updatePrizes(dt);
        else if (currentGame === 'buy_coins') updateBuyCoins(dt);
    }

    function updateSlots(dt) {
        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b')) && actionCooldown <= 0;
        const mov = Input.getMovement();

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

        // Bet adjustment (left/right when not spinning)
        if (!spinning && mov && actionCooldown <= 0) {
            if (mov.dx > 0) { slotBet = Math.min(3, slotBet + 1); actionCooldown = 150; }
            if (mov.dx < 0) { slotBet = Math.max(1, slotBet - 1); actionCooldown = 150; }
        }

        // Spin reels via backend
        if (!spinning && action) {
            if (coins < slotBet) return;
            spinning = true;
            pendingSpinResult = null;
            reelsStopped = [false, false, false];
            reelSpeeds = [0.3, 0.3, 0.3];
            reelTimers = [800, 1300, 1800];
            actionCooldown = 200;

            // Fire API call — response arrives while reels animate
            API.spinSlots(slotBet).then(data => {
                if (data) {
                    pendingSpinResult = data;
                    if (data.coins_after !== undefined) coins = data.coins_after;
                } else {
                    // Offline fallback
                    coins = Math.max(0, coins - slotBet);
                    pendingSpinResult = { reels: ['Cherry', 'Bar', 'Pokeball'], win: false, payout: 0 };
                }
            }).catch(() => {
                coins = Math.max(0, coins - slotBet);
                pendingSpinResult = { reels: ['Cherry', 'Bar', 'Pokeball'], win: false, payout: 0 };
            });
        }

        if (spinning) {
            let allStopped = true;
            for (let i = 0; i < 3; i++) {
                if (!reelsStopped[i]) {
                    reelTimers[i] -= dt;
                    reels[i] = (reels[i] + reelSpeeds[i] * dt * 0.01) % SLOT_SYMBOLS.length;

                    if (reelTimers[i] <= 0 && pendingSpinResult) {
                        reelsStopped[i] = true;
                        // Snap to server-dictated symbol
                        const serverSymbol = pendingSpinResult.reels[i];
                        reels[i] = SYMBOL_INDEX[serverSymbol] !== undefined ? SYMBOL_INDEX[serverSymbol] : 0;
                    } else if (reelTimers[i] <= 0 && !pendingSpinResult) {
                        // Server hasn't responded yet; keep spinning slowly
                        reelTimers[i] = 200;
                        reelSpeeds[i] = 0.15;
                    }

                    if (!reelsStopped[i]) allStopped = false;
                }
            }

            if (allStopped) {
                spinning = false;
                // Use server result
                if (pendingSpinResult) {
                    if (pendingSpinResult.win) {
                        slotResult = 'win';
                        slotWinAmount = pendingSpinResult.payout;
                    } else {
                        slotResult = 'lose';
                        slotWinAmount = 0;
                    }
                }
                pendingSpinResult = null;
                slotResultTimer = 0;
            }
        }
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
            completeMemoryToBackend();
            return;
        }

        // Check match after reveal delay
        if (memoryCheckTimer > 0) {
            memoryCheckTimer -= dt;
            if (memoryCheckTimer <= 0) {
                if (memoryCards[memoryFirst] === memoryCards[memorySecond]) {
                    memoryMatched[memoryFirst] = true;
                    memoryMatched[memorySecond] = true;
                    memoryPairsMatched++;
                } else {
                    memoryRevealed[memoryFirst] = false;
                    memoryRevealed[memorySecond] = false;
                }
                memoryFirst = -1;
                memorySecond = -1;

                // Check win
                if (memoryMatched.every(m => m)) {
                    memoryDone = true;
                    completeMemoryToBackend();
                }
            }
            return;
        }

        // Cursor movement
        if (mov && actionCooldown <= 0) {
            const totalCards = memoryGridW * memoryGridH;
            if (mov.dx > 0) { memoryCursor = Math.min(totalCards - 1, memoryCursor + 1); actionCooldown = 120; }
            if (mov.dx < 0) { memoryCursor = Math.max(0, memoryCursor - 1); actionCooldown = 120; }
            if (mov.dy > 0) { memoryCursor = Math.min(totalCards - 1, memoryCursor + memoryGridW); actionCooldown = 120; }
            if (mov.dy < 0) { memoryCursor = Math.max(0, memoryCursor - memoryGridW); actionCooldown = 120; }
        }

        // Card selection
        if (action) {
            actionCooldown = 200;
            // Can't select matched or already-revealed cards
            if (memoryMatched[memoryCursor] || memoryRevealed[memoryCursor]) return;
            // Already have two cards waiting to be checked
            if (memoryFirst >= 0 && memorySecond >= 0) return;

            memoryRevealed[memoryCursor] = true;
            memoryMoves++;

            if (memoryFirst < 0) {
                memoryFirst = memoryCursor;
            } else {
                memorySecond = memoryCursor;
                memoryCheckTimer = 600; // delay before checking match
            }
        }
    }

    async function completeMemoryToBackend() {
        const timeSeconds = Math.floor((Date.now() - memoryStartTime) / 1000);
        loading = true;
        const result = await API.completeMemoryGame(memoryDifficulty, timeSeconds, memoryPairsMatched);
        if (result) {
            if (result.coins_after !== undefined) coins = result.coins_after;
        }
        loading = false;
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
                if (quizSessionId && quizQuestions.length > 0) {
                    loadQuizQuestion(quizRound);
                } else {
                    nextLocalQuizQuestion();
                }
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
            quizAnswers.push(quizChoice);

            if (quizSessionId) {
                // Server will grade on submit; show tentative feedback
                // For backend quizzes, correct answer index may not be available locally
                // We'll show neutral feedback until submit
                quizResult = 'answered';
            } else {
                // Local fallback — grade immediately
                const q = QUIZ_BANK[quizRound % QUIZ_BANK.length];
                if (quizChoice === q.a) {
                    quizResult = 'correct';
                    quizScore++;
                } else {
                    quizResult = 'wrong';
                }
            }
            quizResultTimer = 0;
        }
    }

    function updatePrizes(dt) {
        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (prizeMessageTimer > 0) {
            prizeMessageTimer -= dt;
            if (prizeMessageTimer <= 0) prizeMessage = '';
        }

        if (back) { exit(); return; }

        if (prizes.length === 0) return;

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { prizeCursor = Math.max(0, prizeCursor - 1); actionCooldown = 150; }
            if (mov.dy > 0) { prizeCursor = Math.min(prizes.length - 1, prizeCursor + 1); actionCooldown = 150; }
        }

        if (action) {
            actionCooldown = 300;
            const prize = prizes[prizeCursor];
            if (coins < prize.coin_cost) {
                prizeMessage = 'Not enough coins!';
                prizeMessageTimer = 2000;
                return;
            }
            loading = true;
            API.redeemPrize(prize.id).then(result => {
                loading = false;
                if (result && result.success) {
                    if (result.coins_after !== undefined) coins = result.coins_after;
                    prizeMessage = `Got ${result.prize_name || prize.name}!`;
                } else {
                    prizeMessage = (result && result.message) || 'Redemption failed!';
                }
                prizeMessageTimer = 2500;
            }).catch(() => {
                loading = false;
                prizeMessage = 'Network error!';
                prizeMessageTimer = 2000;
            });
        }
    }

    function updateBuyCoins(dt) {
        const action = Input.isActionPressed() && actionCooldown <= 0;
        const back = (Input.isDown('Escape') || Input.isDown('b')) && actionCooldown <= 0;
        const mov = Input.getMovement();

        if (buyCoinsMessageTimer > 0) {
            buyCoinsMessageTimer -= dt;
            if (buyCoinsMessageTimer <= 0) buyCoinsMessage = '';
        }

        if (back) { exit(); return; }

        if (mov && actionCooldown <= 0) {
            if (mov.dy < 0) { buyCoinsCursor = Math.max(0, buyCoinsCursor - 1); actionCooldown = 150; }
            if (mov.dy > 0) { buyCoinsCursor = Math.min(COIN_PACKAGES.length - 1, buyCoinsCursor + 1); actionCooldown = 150; }
        }

        if (action) {
            actionCooldown = 300;
            const pkg = COIN_PACKAGES[buyCoinsCursor];
            loading = true;
            API.buyCoins(pkg.money).then(result => {
                loading = false;
                if (result && result.coins_after !== undefined) {
                    coins = result.coins_after;
                    buyCoinsMessage = `Bought ${result.amount || pkg.coins} coins!`;
                } else {
                    buyCoinsMessage = (result && result.message) || 'Not enough money!';
                }
                buyCoinsMessageTimer = 2000;
            }).catch(() => {
                loading = false;
                buyCoinsMessage = 'Network error!';
                buyCoinsMessageTimer = 2000;
            });
        }
    }

    // ---- Render ----
    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        if (currentGame === 'slots') renderSlots(ctx, canvasW, canvasH);
        else if (currentGame === 'memory') renderMemory(ctx, canvasW, canvasH);
        else if (currentGame === 'quiz') renderQuiz(ctx, canvasW, canvasH);
        else if (currentGame === 'prizes') renderPrizes(ctx, canvasW, canvasH);
        else if (currentGame === 'buy_coins') renderBuyCoins(ctx, canvasW, canvasH);

        // Loading overlay
        if (loading) {
            ctx.fillStyle = 'rgba(0,0,0,0.4)';
            ctx.fillRect(0, 0, canvasW, canvasH);
            ctx.fillStyle = '#f8d030';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('Loading...', canvasW / 2, canvasH / 2);
            ctx.textAlign = 'left';
        }
    }

    function renderCoinCounter(ctx, x, y) {
        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`\u{1F4B0} ${coins}`, x, y);
        ctx.textAlign = 'left';
    }

    function renderSlots(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#1a0a2a';
        ctx.fillRect(0, 0, canvasW, canvasH);

        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('SLOT MACHINE', canvasW / 2, 35);

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

            const symIdx = Math.floor(reels[i]) % SLOT_SYMBOLS.length;
            const sym = SLOT_SYMBOLS[symIdx];
            ctx.fillStyle = sym.color;
            ctx.font = 'bold 32px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(sym.char, rx + rw / 2, ry + rh / 2 + 12);
        }

        // Bet display
        ctx.fillStyle = '#c0c0c0';
        ctx.font = '11px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Bet: ${slotBet} coin${slotBet > 1 ? 's' : ''}  (\u2190\u2192 to adjust)`, canvasW / 2, my + mh + 24);

        // Result
        if (slotResult) {
            ctx.fillStyle = slotResult === 'win' ? '#48c048' : '#c04040';
            ctx.font = 'bold 18px monospace';
            ctx.fillText(
                slotResult === 'win' ? `WIN! +${slotWinAmount} coins!` : 'No match...',
                canvasW / 2, my + mh + 50
            );
        }

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
        ctx.fillText(`Time: ${Math.ceil(memoryTimeLeft)}s  Moves: ${memoryMoves}`, canvasW / 2, 48);

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
                ctx.fillStyle = 'rgba(72, 192, 72, 0.2)';
                ctx.fillRect(cx, cy, cardW, cardH);
            } else if (memoryRevealed[i]) {
                ctx.fillStyle = '#f8f8f0';
                ctx.fillRect(cx, cy, cardW, cardH);
                const sym = SLOT_SYMBOLS[memoryCards[i] % SLOT_SYMBOLS.length];
                ctx.fillStyle = sym.color;
                ctx.font = 'bold 22px monospace';
                ctx.fillText(sym.char, cx + cardW / 2, cy + cardH / 2 + 8);
            } else {
                ctx.fillStyle = '#3060a0';
                ctx.fillRect(cx, cy, cardW, cardH);
                ctx.strokeStyle = '#4080c0';
                ctx.lineWidth = 1;
                ctx.strokeRect(cx, cy, cardW, cardH);
                ctx.fillStyle = '#4080c0';
                ctx.font = '18px monospace';
                ctx.fillText('?', cx + cardW / 2, cy + cardH / 2 + 6);
            }

            // Cursor highlight
            if (i === memoryCursor && !memoryDone) {
                ctx.strokeStyle = '#f8d030';
                ctx.lineWidth = 2;
                ctx.strokeRect(cx - 2, cy - 2, cardW + 4, cardH + 4);
            }
        }

        if (memoryDone) {
            ctx.fillStyle = 'rgba(0,0,0,0.6)';
            ctx.fillRect(0, 0, canvasW, canvasH);
            ctx.fillStyle = memoryMatched.every(m => m) ? '#48c048' : '#e04040';
            ctx.font = 'bold 20px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(memoryMatched.every(m => m) ? 'YOU WIN!' : 'TIME UP!', canvasW / 2, canvasH / 2 - 10);
            ctx.fillStyle = '#c0c0c0';
            ctx.font = '12px monospace';
            ctx.fillText('Press Z to exit', canvasW / 2, canvasH / 2 + 20);
        }

        ctx.fillStyle = '#606060';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Arrows: Move | Z: Flip | Esc: Exit', canvasW / 2, canvasH - 10);
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

        ctx.fillStyle = '#c0c0c0';
        ctx.font = '12px monospace';
        ctx.fillText(`Question ${quizRound + 1}/${quizTotal}  Score: ${quizScore}`, canvasW / 2, 48);

        if (quizDone) {
            ctx.fillStyle = '#f8d030';
            ctx.font = 'bold 20px monospace';
            ctx.fillText(`Final Score: ${quizScore}/${quizTotal}`, canvasW / 2, canvasH / 2 - 20);
            ctx.fillStyle = '#48c048';
            ctx.font = '14px monospace';
            const reward = quizScore * 5 + (quizScore === quizTotal ? 50 : 0);
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
            if (quizResult === 'correct' && i === quizChoice) bg = 'rgba(72,192,72,0.4)';
            else if (quizResult === 'wrong' && i === quizChoice) bg = 'rgba(224,64,56,0.4)';
            else if (quizResult === 'answered' && i === quizChoice) bg = 'rgba(248,216,48,0.3)';
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

        if (quizResult) {
            ctx.font = 'bold 16px monospace';
            if (quizResult === 'correct') {
                ctx.fillStyle = '#48c048';
                ctx.fillText('Correct! +5 coins', canvasW / 2, 270);
            } else if (quizResult === 'wrong') {
                ctx.fillStyle = '#e04040';
                ctx.fillText('Wrong!', canvasW / 2, 270);
            } else {
                ctx.fillStyle = '#f8d030';
                ctx.fillText('Answer recorded!', canvasW / 2, 270);
            }
        }

        ctx.fillStyle = '#606060';
        ctx.font = '10px monospace';
        ctx.fillText('Esc: Exit', canvasW / 2, canvasH - 10);
        ctx.textAlign = 'left';
    }

    function renderPrizes(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#1a0a2a';
        ctx.fillRect(0, 0, canvasW, canvasH);

        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('PRIZE EXCHANGE', canvasW / 2, 30);

        renderCoinCounter(ctx, canvasW - 20, 28);

        if (prizes.length === 0) {
            ctx.fillStyle = '#c0c0c0';
            ctx.font = '14px monospace';
            ctx.fillText('No prizes available', canvasW / 2, canvasH / 2);
            ctx.fillStyle = '#606060';
            ctx.font = '10px monospace';
            ctx.fillText('Esc: Exit', canvasW / 2, canvasH - 10);
            ctx.textAlign = 'left';
            return;
        }

        const listY = 55;
        const itemH = 28;
        const maxVisible = Math.min(prizes.length, 7);
        const scrollOffset = Math.max(0, prizeCursor - 5);

        for (let i = 0; i < maxVisible; i++) {
            const pi = i + scrollOffset;
            if (pi >= prizes.length) break;
            const prize = prizes[pi];
            const y = listY + i * itemH;

            // Selection highlight
            if (pi === prizeCursor) {
                ctx.fillStyle = 'rgba(248,216,48,0.2)';
                ctx.fillRect(20, y - 2, canvasW - 40, itemH - 2);
                ctx.strokeStyle = '#f8d030';
                ctx.lineWidth = 1;
                ctx.strokeRect(20, y - 2, canvasW - 40, itemH - 2);
            }

            const canAfford = coins >= prize.coin_cost;
            ctx.fillStyle = canAfford ? '#f8f8f8' : '#606060';
            ctx.font = '12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(prize.name, 30, y + 14);
            ctx.textAlign = 'right';
            ctx.fillStyle = canAfford ? '#f8d030' : '#804040';
            ctx.fillText(`${prize.coin_cost}C`, canvasW - 30, y + 14);
        }

        // Description of selected prize
        if (prizes[prizeCursor]) {
            ctx.fillStyle = '#a0a0a0';
            ctx.font = '11px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(prizes[prizeCursor].description || '', canvasW / 2, canvasH - 40);
        }

        // Message
        if (prizeMessage) {
            ctx.fillStyle = '#48c048';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(prizeMessage, canvasW / 2, canvasH - 55);
        }

        ctx.fillStyle = '#606060';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Z: Redeem | Esc: Exit', canvasW / 2, canvasH - 10);
        ctx.textAlign = 'left';
    }

    function renderBuyCoins(ctx, canvasW, canvasH) {
        ctx.fillStyle = '#1a1a0a';
        ctx.fillRect(0, 0, canvasW, canvasH);

        ctx.fillStyle = '#f8d030';
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('BUY COINS', canvasW / 2, 30);

        renderCoinCounter(ctx, canvasW - 20, 28);

        const listY = 70;
        const itemH = 36;

        for (let i = 0; i < COIN_PACKAGES.length; i++) {
            const pkg = COIN_PACKAGES[i];
            const y = listY + i * itemH;

            if (i === buyCoinsCursor) {
                ctx.fillStyle = 'rgba(248,216,48,0.2)';
                ctx.fillRect(40, y - 4, canvasW - 80, itemH - 4);
                ctx.strokeStyle = '#f8d030';
                ctx.lineWidth = 1;
                ctx.strokeRect(40, y - 4, canvasW - 80, itemH - 4);
            }

            ctx.fillStyle = '#f8f8f8';
            ctx.font = '13px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(pkg.label, canvasW / 2, y + 16);
        }

        if (buyCoinsMessage) {
            ctx.fillStyle = '#48c048';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(buyCoinsMessage, canvasW / 2, canvasH - 50);
        }

        ctx.fillStyle = '#606060';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Z: Buy | Esc: Exit', canvasW / 2, canvasH - 10);
        ctx.textAlign = 'left';
    }

    return {
        isActive, getCurrentGame, getCoins, exit,
        startSlots, startMemory, startQuiz, startPrizes, startBuyCoins,
        update, render, renderCoinCounter, syncCoins,
    };
})();
