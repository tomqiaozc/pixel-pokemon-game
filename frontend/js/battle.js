// battle.js — Turn-based battle system UI

const Battle = (() => {
    // Battle phases
    // intro -> menu -> fight_select -> animating -> text -> result
    let phase = 'intro';
    let canvas, ctx, canvasW, canvasH;

    // Pokemon data for the current battle
    let playerPokemon = null;
    let enemyPokemon = null;

    // Animation state
    let introTimer = 0;
    let textQueue = [];
    let textIndex = 0;
    let charIndex = 0;
    let textTimer = 0;
    let actionCooldown = 0;

    // Menu state
    let menuChoice = 0;     // 0=Fight, 1=Bag, 2=Pokemon, 3=Run
    let moveChoice = 0;     // 0-3 for moves
    let menuMode = 'main';  // main, fight

    // Animation
    let playerShake = 0;
    let enemyShake = 0;
    let playerFlash = 0;
    let enemyFlash = 0;
    let damageNumbers = [];
    let particles = [];
    let playerFaint = 0;  // 0-1 faint progress
    let enemyFaint = 0;
    let hpAnimTimer = 0;
    let playerHpDisplay = 0;
    let enemyHpDisplay = 0;

    // Transition
    let transitionAlpha = 1;
    let transitionDir = -1; // -1 = fading in, 1 = fading out
    let battleOver = false;
    let battleResult = null; // 'win', 'lose', 'run'

    const TEXT_SPEED = 25;
    const TYPE_COLORS = {
        Normal:   '#a8a878',
        Fire:     '#f08030',
        Water:    '#6890f0',
        Grass:    '#78c850',
        Electric: '#f8d030',
        Ice:      '#98d8d8',
        Fighting: '#c03028',
        Poison:   '#a040a0',
        Ground:   '#e0c068',
        Flying:   '#a890f0',
        Psychic:  '#f85888',
        Bug:      '#a8b820',
        Rock:     '#b8a038',
        Ghost:    '#705898',
        Dragon:   '#7038f8',
        Dark:     '#705848',
        Steel:    '#b8b8d0',
        Fairy:    '#ee99ac',
    };

    // Default moves if none provided
    const DEFAULT_MOVES = [
        { name: 'Tackle', type: 'Normal', power: 40, pp: 35, maxPp: 35 },
        { name: 'Growl', type: 'Normal', power: 0, pp: 40, maxPp: 40 },
        { name: 'Scratch', type: 'Normal', power: 40, pp: 35, maxPp: 35 },
        { name: '---', type: 'Normal', power: 0, pp: 0, maxPp: 0 },
    ];

    function start(playerData, enemyData) {
        playerPokemon = {
            name: playerData.name || 'Pikachu',
            level: playerData.level || 5,
            hp: playerData.hp || 20,
            maxHp: playerData.maxHp || 20,
            exp: playerData.exp || 0,
            maxExp: playerData.maxExp || 100,
            type: playerData.type || 'Normal',
            moves: playerData.moves || DEFAULT_MOVES.slice(),
            colors: playerData.colors || null,
        };
        enemyPokemon = {
            name: enemyData.name || 'Pidgey',
            level: enemyData.level || 3,
            hp: enemyData.hp || 15,
            maxHp: enemyData.maxHp || 15,
            type: enemyData.type || 'Normal',
            colors: enemyData.colors || null,
        };

        phase = 'intro';
        introTimer = 0;
        transitionAlpha = 1;
        transitionDir = -1;
        battleOver = false;
        battleResult = null;
        menuChoice = 0;
        moveChoice = 0;
        menuMode = 'main';
        playerShake = 0;
        enemyShake = 0;
        playerFlash = 0;
        enemyFlash = 0;
        damageNumbers = [];
        particles = [];
        playerFaint = 0;
        enemyFaint = 0;
        playerHpDisplay = playerPokemon.hp;
        enemyHpDisplay = enemyPokemon.hp;
        textQueue = [`Wild ${enemyPokemon.name} appeared!`];
        textIndex = 0;
        charIndex = 0;
        textTimer = 0;
        actionCooldown = 300;

        canvas = document.getElementById('game-canvas');
        ctx = canvas.getContext('2d');
        canvasW = canvas.width;
        canvasH = canvas.height;
    }

    function update(dt) {
        actionCooldown = Math.max(0, actionCooldown - dt);
        const action = Input.isActionPressed() && actionCooldown <= 0;

        // Animate HP bars toward target
        hpAnimTimer += dt;
        playerHpDisplay = lerp(playerHpDisplay, playerPokemon.hp, dt * 0.005);
        enemyHpDisplay = lerp(enemyHpDisplay, enemyPokemon.hp, dt * 0.005);

        // Update shakes
        if (playerShake > 0) playerShake = Math.max(0, playerShake - dt);
        if (enemyShake > 0) enemyShake = Math.max(0, enemyShake - dt);
        if (playerFlash > 0) playerFlash = Math.max(0, playerFlash - dt);
        if (enemyFlash > 0) enemyFlash = Math.max(0, enemyFlash - dt);

        // Update damage numbers
        for (const dn of damageNumbers) {
            dn.age += dt;
            dn.y -= dt * 0.05;
        }
        damageNumbers = damageNumbers.filter(d => d.age < 1000);

        // Update particles
        for (const p of particles) {
            p.age += dt;
            p.x += p.vx * dt * 0.06;
            p.y += p.vy * dt * 0.06;
            p.vy += 0.002 * dt; // gravity
        }
        particles = particles.filter(p => p.age < p.life);

        // Transition fade
        if (transitionDir !== 0) {
            transitionAlpha += transitionDir * dt * 0.003;
            if (transitionAlpha <= 0) {
                transitionAlpha = 0;
                transitionDir = 0;
            }
            if (transitionAlpha >= 1 && transitionDir > 0) {
                transitionAlpha = 1;
                transitionDir = 0;
                return { done: true, result: battleResult, playerHp: playerPokemon ? playerPokemon.hp : 0 };
            }
        }

        // Phase logic
        if (phase === 'intro') {
            introTimer += dt;
            // Typewriter for intro text
            textTimer += dt;
            charIndex = Math.min(textQueue[0].length, Math.floor(textTimer / TEXT_SPEED));

            if (action && introTimer > 500) {
                if (charIndex < textQueue[0].length) {
                    charIndex = textQueue[0].length;
                } else {
                    phase = 'menu';
                    menuMode = 'main';
                    menuChoice = 0;
                }
                actionCooldown = 200;
            }
        } else if (phase === 'menu') {
            const mov = Input.getMovement();
            if (mov && actionCooldown <= 0) {
                if (menuMode === 'main') {
                    if (mov.dy < 0 && menuChoice >= 2) { menuChoice -= 2; actionCooldown = 150; }
                    if (mov.dy > 0 && menuChoice < 2) { menuChoice += 2; actionCooldown = 150; }
                    if (mov.dx < 0 && menuChoice % 2 === 1) { menuChoice--; actionCooldown = 150; }
                    if (mov.dx > 0 && menuChoice % 2 === 0) { menuChoice++; actionCooldown = 150; }
                    menuChoice = Math.max(0, Math.min(3, menuChoice));
                } else if (menuMode === 'fight') {
                    if (mov.dy < 0 && moveChoice >= 2) { moveChoice -= 2; actionCooldown = 150; }
                    if (mov.dy > 0 && moveChoice < 2) { moveChoice += 2; actionCooldown = 150; }
                    if (mov.dx < 0 && moveChoice % 2 === 1) { moveChoice--; actionCooldown = 150; }
                    if (mov.dx > 0 && moveChoice % 2 === 0) { moveChoice++; actionCooldown = 150; }
                    moveChoice = Math.max(0, Math.min(3, moveChoice));
                }
            }

            if (action) {
                actionCooldown = 200;
                if (menuMode === 'main') {
                    if (menuChoice === 0) {
                        // Fight
                        menuMode = 'fight';
                        moveChoice = 0;
                    } else if (menuChoice === 3) {
                        // Run
                        executeRun();
                    }
                    // Bag and Pokemon not implemented yet
                } else if (menuMode === 'fight') {
                    const move = playerPokemon.moves[moveChoice];
                    if (move.name !== '---' && move.pp > 0) {
                        executeTurn(move);
                    }
                }
            }

            // B key to go back
            if ((Input.isDown('b') || Input.isDown('B') || Input.isDown('Escape')) && menuMode === 'fight' && actionCooldown <= 0) {
                menuMode = 'main';
                actionCooldown = 200;
            }
        } else if (phase === 'animating') {
            // Wait for animations to complete, then move to text
            introTimer += dt;
            if (introTimer > 800) {
                phase = 'text';
                textIndex = 0;
                charIndex = 0;
                textTimer = 0;
            }
        } else if (phase === 'text') {
            if (textQueue.length > 0) {
                textTimer += dt;
                charIndex = Math.min(textQueue[textIndex].length, Math.floor(textTimer / TEXT_SPEED));

                if (action) {
                    actionCooldown = 200;
                    if (charIndex < textQueue[textIndex].length) {
                        charIndex = textQueue[textIndex].length;
                    } else {
                        textIndex++;
                        charIndex = 0;
                        textTimer = 0;
                        if (textIndex >= textQueue.length) {
                            // All text displayed
                            if (battleOver) {
                                // Faint animation then exit
                                phase = 'result';
                                introTimer = 0;
                            } else {
                                phase = 'menu';
                                menuMode = 'main';
                                menuChoice = 0;
                            }
                        }
                    }
                }
            }
        } else if (phase === 'result') {
            introTimer += dt;
            // Faint animation
            if (battleResult === 'win') {
                enemyFaint = Math.min(1, enemyFaint + dt * 0.002);
            } else if (battleResult === 'lose') {
                playerFaint = Math.min(1, playerFaint + dt * 0.002);
            }

            if (introTimer > 1500 || action) {
                transitionDir = 1; // Fade out
            }
        }

        return { done: false };
    }

    function executeTurn(playerMove) {
        phase = 'animating';
        introTimer = 0;
        textQueue = [];

        // Player attacks
        playerMove.pp--;
        const playerDmg = calculateDamage(playerMove.power, playerPokemon.level);
        textQueue.push(`${playerPokemon.name} used ${playerMove.name}!`);

        // Spawn attack particles
        spawnAttackParticles(playerMove.type, canvasW * 0.7, canvasH * 0.25);

        enemyPokemon.hp = Math.max(0, enemyPokemon.hp - playerDmg);
        enemyShake = 300;
        enemyFlash = 200;

        if (playerDmg > 0) {
            damageNumbers.push({
                x: canvasW * 0.7,
                y: canvasH * 0.2,
                value: playerDmg,
                age: 0,
            });
        }

        if (enemyPokemon.hp <= 0) {
            textQueue.push(`Wild ${enemyPokemon.name} fainted!`);
            battleOver = true;
            battleResult = 'win';
            return;
        }

        // Enemy attacks (pick random move)
        const enemyMoves = [
            { name: 'Tackle', type: 'Normal', power: 40 },
            { name: 'Scratch', type: 'Normal', power: 40 },
        ];
        const enemyMove = enemyMoves[Math.floor(Math.random() * enemyMoves.length)];
        const enemyDmg = calculateDamage(enemyMove.power, enemyPokemon.level);

        textQueue.push(`Wild ${enemyPokemon.name} used ${enemyMove.name}!`);

        playerPokemon.hp = Math.max(0, playerPokemon.hp - enemyDmg);

        // Delayed player hit effects (set in animation timer)
        setTimeout(() => {
            playerShake = 300;
            playerFlash = 200;
            if (enemyDmg > 0) {
                damageNumbers.push({
                    x: canvasW * 0.25,
                    y: canvasH * 0.5,
                    value: enemyDmg,
                    age: 0,
                });
            }
        }, 400);

        if (playerPokemon.hp <= 0) {
            textQueue.push(`${playerPokemon.name} fainted!`);
            battleOver = true;
            battleResult = 'lose';
        }
    }

    function executeRun() {
        phase = 'text';
        textQueue = ['Got away safely!'];
        textIndex = 0;
        charIndex = 0;
        textTimer = 0;
        battleOver = true;
        battleResult = 'run';
    }

    function calculateDamage(power, level) {
        if (power === 0) return 0;
        const base = Math.floor(((2 * level / 5 + 2) * power / 50) + 2);
        const rand = 0.85 + Math.random() * 0.15;
        return Math.max(1, Math.floor(base * rand));
    }

    function spawnAttackParticles(type, cx, cy) {
        const color = TYPE_COLORS[type] || '#ffffff';
        for (let i = 0; i < 8; i++) {
            particles.push({
                x: cx + (Math.random() - 0.5) * 40,
                y: cy + (Math.random() - 0.5) * 30,
                vx: (Math.random() - 0.5) * 3,
                vy: -Math.random() * 2 - 1,
                color: color,
                size: 3 + Math.random() * 4,
                life: 400 + Math.random() * 300,
                age: 0,
            });
        }
    }

    function lerp(a, b, t) {
        return a + (b - a) * Math.min(1, t);
    }

    function render() {
        if (!ctx) return;

        // Battle background
        drawBattleBackground();

        // Enemy Pokemon (top-right)
        const enemyX = canvasW * 0.68;
        const enemyY = canvasH * 0.22;
        drawBattlePokemon(enemyPokemon, enemyX, enemyY, 4, false,
            enemyShake, enemyFlash, enemyFaint);

        // Player Pokemon (bottom-left)
        const playerX = canvasW * 0.22;
        const playerY = canvasH * 0.52;
        drawBattlePokemon(playerPokemon, playerX, playerY, 5, true,
            playerShake, playerFlash, playerFaint);

        // Enemy info panel (top-left)
        drawInfoPanel(enemyPokemon, enemyHpDisplay, 20, 20, false);

        // Player info panel (bottom-right)
        drawInfoPanel(playerPokemon, playerHpDisplay, canvasW - 260, canvasH * 0.42, true);

        // Particles
        for (const p of particles) {
            const alpha = 1 - p.age / p.life;
            ctx.globalAlpha = alpha;
            ctx.fillStyle = p.color;
            ctx.fillRect(p.x - p.size / 2, p.y - p.size / 2, p.size, p.size);
        }
        ctx.globalAlpha = 1;

        // Damage numbers
        for (const dn of damageNumbers) {
            const alpha = 1 - dn.age / 1000;
            ctx.globalAlpha = alpha;
            ctx.fillStyle = '#ffffff';
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 3;
            ctx.font = 'bold 24px monospace';
            ctx.textAlign = 'center';
            ctx.strokeText(`-${dn.value}`, dn.x, dn.y);
            ctx.fillText(`-${dn.value}`, dn.x, dn.y);
        }
        ctx.globalAlpha = 1;
        ctx.textAlign = 'left';

        // Bottom panel (menu or text)
        drawBottomPanel();

        // Transition overlay
        if (transitionAlpha > 0) {
            ctx.fillStyle = `rgba(0, 0, 0, ${transitionAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }
    }

    function drawBattleBackground() {
        // Sky gradient
        const grad = ctx.createLinearGradient(0, 0, 0, canvasH * 0.6);
        grad.addColorStop(0, '#88c8e8');
        grad.addColorStop(1, '#c8e8c0');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, canvasW, canvasH * 0.65);

        // Ground
        ctx.fillStyle = '#90c868';
        ctx.fillRect(0, canvasH * 0.55, canvasW, canvasH * 0.15);

        // Enemy platform
        ctx.fillStyle = '#78a850';
        ctx.beginPath();
        ctx.ellipse(canvasW * 0.68, canvasH * 0.32, 80, 20, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#689840';
        ctx.beginPath();
        ctx.ellipse(canvasW * 0.68, canvasH * 0.34, 80, 20, 0, 0, Math.PI);
        ctx.fill();

        // Player platform
        ctx.fillStyle = '#78a850';
        ctx.beginPath();
        ctx.ellipse(canvasW * 0.22, canvasH * 0.62, 100, 24, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#689840';
        ctx.beginPath();
        ctx.ellipse(canvasW * 0.22, canvasH * 0.64, 100, 24, 0, 0, Math.PI);
        ctx.fill();
    }

    function drawBattlePokemon(pokemon, cx, cy, scale, isPlayer, shake, flash, faint) {
        if (!pokemon) return;

        ctx.save();

        // Faint: slide down + fade
        if (faint > 0) {
            ctx.globalAlpha = 1 - faint;
            cy += faint * 40;
        }

        // Shake offset
        let shakeX = 0;
        if (shake > 0) {
            shakeX = Math.sin(shake * 0.05) * 4;
        }

        // Draw Pokemon sprite using starter sprites if available
        if (pokemon.colors) {
            // Find matching starter
            const starter = StarterSelect.starters.find(s => s.name === pokemon.name);
            if (starter) {
                StarterSelect.render; // just accessing module
                drawGenericPokemonSprite(ctx, pokemon, cx + shakeX, cy, scale);
            } else {
                drawGenericPokemonSprite(ctx, pokemon, cx + shakeX, cy, scale);
            }
        } else {
            drawGenericPokemonSprite(ctx, pokemon, cx + shakeX, cy, scale);
        }

        // Flash white on hit
        if (flash > 0) {
            ctx.globalAlpha = flash / 200;
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(cx - 20 * scale / 2 + shakeX, cy - 20 * scale / 2, 20 * scale, 20 * scale);
        }

        ctx.restore();
    }

    function drawGenericPokemonSprite(ctx, pokemon, cx, cy, scale) {
        const s = scale;
        const color = TYPE_COLORS[pokemon.type] || '#a0a0a0';
        const darkColor = shadeColor(color, -30);
        const lightColor = shadeColor(color, 30);

        const ox = cx - 8 * s;
        const oy = cy - 10 * s;

        // Body
        ctx.fillStyle = color;
        ctx.fillRect(ox + 2 * s, oy + 4 * s, 12 * s, 10 * s);
        ctx.fillRect(ox + 3 * s, oy + 2 * s, 10 * s, 2 * s);
        ctx.fillRect(ox + 3 * s, oy + 14 * s, 10 * s, 2 * s);

        // Belly highlight
        ctx.fillStyle = lightColor;
        ctx.fillRect(ox + 4 * s, oy + 7 * s, 8 * s, 4 * s);

        // Eyes
        ctx.fillStyle = '#202020';
        ctx.fillRect(ox + 4 * s, oy + 5 * s, 2 * s, 2 * s);
        ctx.fillRect(ox + 10 * s, oy + 5 * s, 2 * s, 2 * s);
        // Eye shine
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(ox + 4 * s, oy + 5 * s, s, s);
        ctx.fillRect(ox + 10 * s, oy + 5 * s, s, s);

        // Feet
        ctx.fillStyle = darkColor;
        ctx.fillRect(ox + 3 * s, oy + 15 * s, 3 * s, 2 * s);
        ctx.fillRect(ox + 10 * s, oy + 15 * s, 3 * s, 2 * s);

        // Type-specific detail
        if (pokemon.type === 'Fire') {
            // Flame tail
            ctx.fillStyle = '#f83030';
            ctx.fillRect(ox + 13 * s, oy + 6 * s, 2 * s, 4 * s);
            ctx.fillStyle = '#f8c830';
            ctx.fillRect(ox + 14 * s, oy + 4 * s, 2 * s, 3 * s);
        } else if (pokemon.type === 'Water') {
            // Tail curl
            ctx.fillStyle = darkColor;
            ctx.fillRect(ox + 13 * s, oy + 8 * s, 3 * s, 2 * s);
            ctx.fillRect(ox + 15 * s, oy + 6 * s, 2 * s, 3 * s);
        } else if (pokemon.type === 'Grass') {
            // Leaf on head
            ctx.fillStyle = '#48a048';
            ctx.fillRect(ox + 6 * s, oy, 4 * s, 3 * s);
            ctx.fillRect(ox + 5 * s, oy + s, 2 * s, s);
        }
    }

    function shadeColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const r = Math.min(255, Math.max(0, (num >> 16) + percent));
        const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + percent));
        const b = Math.min(255, Math.max(0, (num & 0x0000FF) + percent));
        return `rgb(${r},${g},${b})`;
    }

    function drawInfoPanel(pokemon, hpDisplay, x, y, isPlayer) {
        if (!pokemon) return;

        const panelW = 240;
        const panelH = isPlayer ? 75 : 55;

        // Panel background
        ctx.fillStyle = 'rgba(248, 248, 240, 0.95)';
        ctx.fillRect(x, y, panelW, panelH);
        ctx.strokeStyle = '#404040';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, panelW, panelH);

        // Name and level
        ctx.fillStyle = '#202020';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(pokemon.name, x + 10, y + 18);
        ctx.font = '12px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`Lv${pokemon.level}`, x + panelW - 10, y + 18);

        // HP bar
        const barX = x + 50;
        const barY = y + 26;
        const barW = panelW - 65;
        const barH = 8;
        const hpRatio = Math.max(0, hpDisplay / pokemon.maxHp);

        ctx.fillStyle = '#303030';
        ctx.fillRect(barX, barY, barW, barH);

        let hpColor = '#48c048';
        if (hpRatio < 0.5) hpColor = '#f8c830';
        if (hpRatio < 0.2) hpColor = '#e04038';

        ctx.fillStyle = hpColor;
        ctx.fillRect(barX + 1, barY + 1, (barW - 2) * hpRatio, barH - 2);

        // HP label
        ctx.fillStyle = '#404040';
        ctx.font = 'bold 10px monospace';
        ctx.textAlign = 'left';
        ctx.fillText('HP', x + 10, y + 34);

        // HP numbers (player only)
        if (isPlayer) {
            ctx.font = '12px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(
                `${Math.ceil(Math.max(0, hpDisplay))} / ${pokemon.maxHp}`,
                x + panelW - 10,
                y + 50
            );

            // EXP bar
            const expBarY = y + 58;
            const expRatio = pokemon.exp / pokemon.maxExp;
            ctx.fillStyle = '#303030';
            ctx.fillRect(barX, expBarY, barW, 5);
            ctx.fillStyle = '#5890f0';
            ctx.fillRect(barX + 1, expBarY + 1, (barW - 2) * expRatio, 3);
            ctx.fillStyle = '#404040';
            ctx.font = '8px monospace';
            ctx.textAlign = 'left';
            ctx.fillText('EXP', x + 10, expBarY + 5);
        }

        ctx.textAlign = 'left';
    }

    function drawBottomPanel() {
        const panelY = canvasH * 0.7;
        const panelH = canvasH * 0.3;

        // Panel background
        ctx.fillStyle = '#f8f8f0';
        ctx.fillRect(0, panelY, canvasW, panelH);
        ctx.strokeStyle = '#404040';
        ctx.lineWidth = 3;
        ctx.strokeRect(2, panelY, canvasW - 4, panelH - 2);

        if (phase === 'intro' || phase === 'text' || phase === 'animating') {
            // Text box
            drawTextBox(panelY);
        } else if (phase === 'menu') {
            if (menuMode === 'main') {
                drawMainMenu(panelY, panelH);
            } else if (menuMode === 'fight') {
                drawFightMenu(panelY, panelH);
            }
        } else if (phase === 'result') {
            drawTextBox(panelY);
        }
    }

    function drawTextBox(panelY) {
        let displayText = '';
        if (textQueue.length > 0 && textIndex < textQueue.length) {
            displayText = textQueue[textIndex].substring(0, charIndex);
        }

        ctx.fillStyle = '#202020';
        ctx.font = '16px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(displayText, 30, panelY + 35);

        // Blinking advance indicator
        if (textQueue.length > 0 && textIndex < textQueue.length &&
            charIndex >= textQueue[textIndex].length &&
            Math.floor(Date.now() / 400) % 2 === 0) {
            ctx.fillText('▼', canvasW - 50, panelY + 55);
        }
    }

    function drawMainMenu(panelY, panelH) {
        // Text area (left side)
        ctx.fillStyle = '#202020';
        ctx.font = '16px monospace';
        ctx.textAlign = 'left';
        ctx.fillText('What will', 30, panelY + 30);
        ctx.fillText(`${playerPokemon.name} do?`, 30, panelY + 52);

        // Menu buttons (right side)
        const menuX = canvasW * 0.55;
        const menuW = canvasW * 0.42;
        const menuItemH = panelH * 0.4;
        const labels = ['FIGHT', 'BAG', 'POKeMON', 'RUN'];
        const colors = ['#e05038', '#e8c838', '#48a848', '#5888d0'];

        for (let i = 0; i < 4; i++) {
            const col = i % 2;
            const row = Math.floor(i / 2);
            const bx = menuX + col * (menuW / 2 + 4);
            const by = panelY + 10 + row * (menuItemH + 4);
            const bw = menuW / 2 - 4;
            const bh = menuItemH - 2;

            // Button background
            ctx.fillStyle = i === menuChoice ? colors[i] : '#d0d0c8';
            ctx.fillRect(bx, by, bw, bh);
            ctx.strokeStyle = '#404040';
            ctx.lineWidth = 2;
            ctx.strokeRect(bx, by, bw, bh);

            // Button text
            ctx.fillStyle = i === menuChoice ? '#ffffff' : '#404040';
            ctx.font = 'bold 13px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(labels[i], bx + bw / 2, by + bh / 2 + 5);
        }

        ctx.textAlign = 'left';
    }

    function drawFightMenu(panelY, panelH) {
        const moves = playerPokemon.moves;
        const gridW = canvasW - 20;
        const cellW = gridW / 2 - 6;
        const cellH = panelH * 0.4;

        for (let i = 0; i < 4; i++) {
            const col = i % 2;
            const row = Math.floor(i / 2);
            const mx = 14 + col * (cellW + 8);
            const my = panelY + 10 + row * (cellH + 4);
            const move = moves[i];

            // Move button background (type colored)
            const typeColor = TYPE_COLORS[move.type] || '#a0a0a0';
            ctx.fillStyle = i === moveChoice ? typeColor : shadeColor(typeColor, 40);
            ctx.fillRect(mx, my, cellW, cellH);
            ctx.strokeStyle = i === moveChoice ? '#202020' : '#808080';
            ctx.lineWidth = i === moveChoice ? 3 : 1;
            ctx.strokeRect(mx, my, cellW, cellH);

            // Move name
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(move.name, mx + cellW / 2, my + cellH / 2);

            // PP
            if (move.maxPp > 0) {
                ctx.font = '10px monospace';
                ctx.fillStyle = 'rgba(255,255,255,0.8)';
                ctx.fillText(`PP ${move.pp}/${move.maxPp}`, mx + cellW / 2, my + cellH - 6);
            }
        }

        // Back hint
        ctx.fillStyle = '#808080';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('B / Esc: Back', canvasW - 20, panelY + panelH - 8);

        ctx.textAlign = 'left';
    }

    return { start, update, render };
})();
