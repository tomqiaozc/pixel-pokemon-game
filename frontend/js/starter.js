// starter.js — Starter Pokemon selection screen

const StarterSelect = (() => {
    const TILE = Sprites.TILE;

    // State
    let selected = 1; // 0=Bulbasaur, 1=Charmander, 2=Squirtle
    let phase = 'intro'; // intro, select, confirm, celebrate
    let textIndex = 0;
    let textTimer = 0;
    let charIndex = 0;
    let bounceTimer = 0;
    let bounceFrame = 0;
    let sparkleTimer = 0;
    let sparkles = [];
    let confirmChoice = 0; // 0=Yes, 1=No
    let celebrateTimer = 0;
    let actionCooldown = 0;
    let chosenStarter = null;

    const TEXT_SPEED = 30; // ms per character
    const BOUNCE_SPEED = 400;

    const starters = [
        {
            name: 'Bulbasaur',
            type: 'Grass',
            typeColor: '#48a048',
            desc: 'A grass-type Pokemon. It carries a seed on its back that grows over time.',
            colors: { body: '#68b868', bodyDark: '#489848', spot: '#486838', eye: '#c03030', bulb: '#48a068', bulbDark: '#387850' },
        },
        {
            name: 'Charmander',
            type: 'Fire',
            typeColor: '#e07030',
            desc: 'A fire-type Pokemon. The flame on its tail shows its life force.',
            colors: { body: '#e88040', bodyDark: '#c06830', belly: '#f8d878', eye: '#304080', flame: '#f83030', flameInner: '#f8c830' },
        },
        {
            name: 'Squirtle',
            type: 'Water',
            typeColor: '#4890d0',
            desc: 'A water-type Pokemon. It shelters in its shell and sprays water at foes.',
            colors: { body: '#58a8d8', bodyDark: '#4088b0', belly: '#f0e8a0', shell: '#a07028', shellLight: '#c89848', eye: '#c03030' },
        },
    ];

    const introTexts = [
        "Welcome to the world of Pokemon!",
        "I'm Professor Oak. I study Pokemon.",
        "Now, choose your very first Pokemon!",
    ];

    function reset() {
        selected = 1;
        phase = 'intro';
        textIndex = 0;
        charIndex = 0;
        textTimer = 0;
        bounceTimer = 0;
        bounceFrame = 0;
        sparkles = [];
        confirmChoice = 0;
        celebrateTimer = 0;
        actionCooldown = 0;
        chosenStarter = null;
    }

    // Draw a starter Pokemon sprite (large, 32x32 logical pixels)
    function drawStarterSprite(ctx, pokemon, cx, cy, scale, frame) {
        const s = scale;
        const c = pokemon.colors;
        const ox = cx - 16 * s;
        const oy = cy - 16 * s + (frame ? -2 * s : 0); // bounce offset

        function px(x, y, color) {
            ctx.fillStyle = color;
            ctx.fillRect(ox + x * s, oy + y * s, s, s);
        }
        function rect(x, y, w, h, color) {
            ctx.fillStyle = color;
            ctx.fillRect(ox + x * s, oy + y * s, w * s, h * s);
        }

        if (pokemon.name === 'Bulbasaur') {
            // Body
            rect(8, 16, 16, 10, c.body);
            rect(6, 18, 20, 6, c.body);
            rect(10, 14, 12, 4, c.body);
            // Spots
            px(10, 18, c.spot); px(14, 20, c.spot); px(20, 19, c.spot);
            // Legs
            rect(8, 25, 4, 4, c.bodyDark);
            rect(20, 25, 4, 4, c.bodyDark);
            // Bulb on back
            rect(11, 8, 10, 8, c.bulb);
            rect(12, 6, 8, 4, c.bulb);
            rect(13, 5, 6, 2, c.bulbDark);
            px(14, 4, c.bulbDark); px(17, 4, c.bulbDark);
            // Head
            rect(4, 14, 10, 8, c.body);
            rect(2, 16, 4, 4, c.body);
            // Eyes
            px(5, 16, c.eye); px(5, 17, c.eye);
            px(10, 16, c.eye); px(10, 17, c.eye);
            // Mouth
            rect(4, 20, 6, 1, c.bodyDark);
        } else if (pokemon.name === 'Charmander') {
            // Body
            rect(10, 12, 12, 12, c.body);
            rect(8, 14, 16, 8, c.body);
            // Belly
            rect(12, 16, 8, 6, c.belly);
            // Head
            rect(8, 6, 12, 8, c.body);
            rect(6, 8, 4, 4, c.body);
            rect(22, 8, 2, 4, c.body);
            // Eyes
            px(10, 9, c.eye); px(10, 10, c.eye);
            px(16, 9, c.eye); px(16, 10, c.eye);
            // Mouth
            rect(10, 12, 8, 1, c.bodyDark);
            // Arms
            rect(6, 16, 4, 2, c.body);
            rect(22, 16, 4, 2, c.body);
            // Legs
            rect(10, 24, 4, 4, c.bodyDark);
            rect(18, 24, 4, 4, c.bodyDark);
            // Tail
            rect(22, 18, 2, 6, c.body);
            rect(24, 16, 2, 4, c.body);
            rect(26, 14, 2, 4, c.body);
            // Tail flame
            rect(26, 10, 4, 4, c.flame);
            rect(27, 9, 2, 2, c.flameInner);
            rect(28, 8, 2, 3, c.flame);
        } else if (pokemon.name === 'Squirtle') {
            // Shell (back)
            rect(10, 12, 12, 12, c.shell);
            rect(12, 11, 8, 2, c.shellLight);
            rect(12, 22, 8, 2, c.shellLight);
            // Head
            rect(8, 4, 12, 10, c.body);
            rect(6, 6, 4, 6, c.body);
            rect(22, 6, 2, 6, c.body);
            // Eyes
            px(10, 8, c.eye); px(10, 9, c.eye);
            px(16, 8, c.eye); px(16, 9, c.eye);
            // Mouth
            rect(10, 12, 6, 1, c.bodyDark);
            // Belly
            rect(8, 14, 6, 8, c.belly);
            // Arms
            rect(4, 14, 4, 2, c.body);
            rect(24, 14, 4, 2, c.body);
            // Legs
            rect(8, 24, 5, 4, c.body);
            rect(18, 24, 5, 4, c.body);
            // Tail
            rect(22, 20, 2, 4, c.body);
            rect(24, 18, 2, 4, c.body);
            rect(26, 16, 2, 3, c.body);
        }
    }

    // Draw a Pokeball
    function drawPokeball(ctx, cx, cy, size, isOpen) {
        const r = size / 2;
        ctx.save();
        // Top half (red)
        ctx.fillStyle = '#e03030';
        ctx.beginPath();
        ctx.arc(cx, cy, r, Math.PI, 0);
        ctx.fill();
        // Bottom half (white)
        ctx.fillStyle = '#f0f0f0';
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI);
        ctx.fill();
        // Center band
        ctx.fillStyle = '#303030';
        ctx.fillRect(cx - r, cy - 2, size, 4);
        // Center button
        ctx.fillStyle = '#f0f0f0';
        ctx.beginPath();
        ctx.arc(cx, cy, r * 0.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#303030';
        ctx.beginPath();
        ctx.arc(cx, cy, r * 0.12, 0, Math.PI * 2);
        ctx.fill();

        if (isOpen) {
            // Open effect - top lid rotated up
            ctx.fillStyle = '#e03030';
            ctx.beginPath();
            ctx.arc(cx, cy - r * 0.3, r, Math.PI + 0.3, -0.3);
            ctx.fill();
        }
        ctx.restore();
    }

    // Draw Professor Oak (simple NPC)
    function drawProfessor(ctx, cx, cy, scale) {
        const s = scale;
        const ox = cx - 8 * s;
        const oy = cy - 16 * s;

        function rect(x, y, w, h, color) {
            ctx.fillStyle = color;
            ctx.fillRect(ox + x * s, oy + y * s, w * s, h * s);
        }
        function px(x, y, color) {
            ctx.fillStyle = color;
            ctx.fillRect(ox + x * s, oy + y * s, s, s);
        }

        // Hair
        for (let x = 4; x <= 11; x++) px(x, 1, '#808080');
        for (let x = 3; x <= 12; x++) { px(x, 2, '#808080'); px(x, 3, '#808080'); }
        // Face
        for (let y = 4; y <= 6; y++) for (let x = 3; x <= 12; x++) px(x, y, '#f8c098');
        // Eyes
        px(5, 5, '#202020'); px(10, 5, '#202020');
        // Lab coat (white)
        for (let y = 7; y <= 12; y++) for (let x = 2; x <= 13; x++) px(x, y, '#f0f0f0');
        // Collar
        px(5, 7, '#d0d0d0'); px(10, 7, '#d0d0d0');
        // Pants
        for (let y = 13; y <= 15; y++) { rect(4, y, 3, 1, '#604020'); rect(9, y, 3, 1, '#604020'); }
    }

    function update(dt, canvas) {
        actionCooldown = Math.max(0, actionCooldown - dt);
        bounceTimer += dt;
        if (bounceTimer >= BOUNCE_SPEED) {
            bounceFrame = 1 - bounceFrame;
            bounceTimer = 0;
        }

        const action = Input.isActionPressed() && actionCooldown <= 0;

        if (phase === 'intro') {
            textTimer += dt;
            const currentText = introTexts[textIndex];
            if (charIndex < currentText.length) {
                charIndex = Math.min(currentText.length, Math.floor(textTimer / TEXT_SPEED));
            }
            if (action) {
                actionCooldown = 250;
                if (charIndex < currentText.length) {
                    charIndex = currentText.length;
                } else if (textIndex < introTexts.length - 1) {
                    textIndex++;
                    charIndex = 0;
                    textTimer = 0;
                } else {
                    phase = 'select';
                }
            }
        } else if (phase === 'select') {
            const mov = Input.getMovement();
            if (mov && actionCooldown <= 0) {
                if (mov.dx < 0) { selected = Math.max(0, selected - 1); actionCooldown = 200; }
                if (mov.dx > 0) { selected = Math.min(2, selected + 1); actionCooldown = 200; }
            }
            if (action) {
                phase = 'confirm';
                confirmChoice = 0;
                actionCooldown = 250;
            }
        } else if (phase === 'confirm') {
            const mov = Input.getMovement();
            if (mov && actionCooldown <= 0) {
                if (mov.dx !== 0 || mov.dy !== 0) {
                    confirmChoice = 1 - confirmChoice;
                    actionCooldown = 200;
                }
            }
            if (action) {
                actionCooldown = 250;
                if (confirmChoice === 0) {
                    // Yes — celebrate
                    phase = 'celebrate';
                    celebrateTimer = 0;
                    chosenStarter = starters[selected];
                    // Create sparkles
                    sparkles = [];
                    for (let i = 0; i < 12; i++) {
                        sparkles.push({
                            x: Math.random() * 200 - 100,
                            y: Math.random() * -100 - 20,
                            vx: (Math.random() - 0.5) * 2,
                            vy: Math.random() * 1 + 0.5,
                            life: 1500 + Math.random() * 1000,
                            age: 0,
                        });
                    }
                } else {
                    // No — back to select
                    phase = 'select';
                }
            }
        } else if (phase === 'celebrate') {
            celebrateTimer += dt;
            // Update sparkles
            for (const sp of sparkles) {
                sp.age += dt;
                sp.x += sp.vx;
                sp.y += sp.vy;
            }
            // Auto-finish after 3 seconds
            if (action && celebrateTimer > 1000) {
                return { done: true, starter: chosenStarter };
            }
            if (celebrateTimer > 4000) {
                return { done: true, starter: chosenStarter };
            }
        }

        return { done: false };
    }

    function render(ctx, canvasW, canvasH) {
        // Background — lab interior
        ctx.fillStyle = '#f0e8d0';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Floor tiles
        ctx.fillStyle = '#e0d8c0';
        for (let y = canvasH * 0.6; y < canvasH; y += 40) {
            for (let x = 0; x < canvasW; x += 40) {
                ctx.fillRect(x + 1, y + 1, 38, 38);
            }
        }

        // Shelves / back wall detail
        ctx.fillStyle = '#c0b090';
        ctx.fillRect(0, 0, canvasW, canvasH * 0.2);
        ctx.fillStyle = '#a09070';
        for (let x = 30; x < canvasW; x += 100) {
            ctx.fillRect(x, canvasH * 0.05, 60, canvasH * 0.12);
        }
        // Book spines
        const bookColors = ['#c04040', '#4040c0', '#40a040', '#c0a040'];
        for (let x = 35; x < canvasW; x += 100) {
            for (let i = 0; i < 4; i++) {
                ctx.fillStyle = bookColors[i];
                ctx.fillRect(x + i * 12, canvasH * 0.06, 10, canvasH * 0.1);
            }
        }

        const midX = canvasW / 2;

        // Professor Oak
        if (phase === 'intro' || phase === 'select') {
            drawProfessor(ctx, midX, canvasH * 0.32, 4);
        }

        // Table
        const tableY = canvasH * 0.55;
        ctx.fillStyle = '#806040';
        ctx.fillRect(midX - 180, tableY, 360, 20);
        ctx.fillStyle = '#906848';
        ctx.fillRect(midX - 170, tableY + 2, 340, 16);

        // Pokeballs on table
        const ballY = tableY - 10;
        const spacing = 120;
        for (let i = 0; i < 3; i++) {
            const bx = midX + (i - 1) * spacing;
            const isSelected = i === selected && (phase === 'select' || phase === 'confirm');
            const isChosen = phase === 'celebrate' && i === selected;
            const ballSize = isSelected ? 36 : 28;

            if (!isChosen) {
                drawPokeball(ctx, bx, ballY, ballSize, false);
            }

            // Selection indicator
            if (isSelected && phase !== 'celebrate') {
                ctx.fillStyle = '#f8d030';
                const indY = ballY - ballSize / 2 - 16 - (bounceFrame ? 4 : 0);
                // Arrow pointing down
                ctx.beginPath();
                ctx.moveTo(bx, indY + 10);
                ctx.lineTo(bx - 8, indY);
                ctx.lineTo(bx + 8, indY);
                ctx.fill();
            }
        }

        // Pokemon preview for selected starter (during select/confirm)
        if (phase === 'select' || phase === 'confirm') {
            const pokemon = starters[selected];
            const previewX = midX;
            const previewY = canvasH * 0.82;

            // Preview panel background
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(midX - 200, previewY - 50, 400, 100);
            ctx.strokeStyle = pokemon.typeColor;
            ctx.lineWidth = 2;
            ctx.strokeRect(midX - 200, previewY - 50, 400, 100);

            // Pokemon name
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 20px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(pokemon.name, midX, previewY - 25);

            // Type badge
            ctx.fillStyle = pokemon.typeColor;
            const badgeW = ctx.measureText(pokemon.type).width + 16;
            ctx.fillRect(midX - badgeW / 2, previewY - 15, badgeW, 22);
            ctx.fillStyle = '#ffffff';
            ctx.font = '14px monospace';
            ctx.fillText(pokemon.type, midX, previewY);

            // Description
            ctx.fillStyle = '#c0c0c0';
            ctx.font = '12px monospace';
            ctx.fillText(pokemon.desc, midX, previewY + 30);
        }

        // Celebrate phase — show chosen Pokemon with sparkles
        if (phase === 'celebrate' && chosenStarter) {
            const pokeY = canvasH * 0.42;
            drawStarterSprite(ctx, chosenStarter, midX, pokeY, 5, bounceFrame);

            // Sparkles
            ctx.fillStyle = '#f8d030';
            for (const sp of sparkles) {
                if (sp.age < sp.life) {
                    const alpha = 1 - sp.age / sp.life;
                    ctx.globalAlpha = alpha;
                    const sx = midX + sp.x;
                    const sy = pokeY + sp.y;
                    // Star shape (simple diamond)
                    ctx.fillRect(sx - 2, sy, 5, 1);
                    ctx.fillRect(sx, sy - 2, 1, 5);
                }
            }
            ctx.globalAlpha = 1;
        }

        // Text box
        ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
        ctx.fillRect(20, canvasH - 80, canvasW - 40, 65);
        ctx.strokeStyle = '#f8f8f8';
        ctx.lineWidth = 2;
        ctx.strokeRect(20, canvasH - 80, canvasW - 40, 65);

        ctx.fillStyle = '#f8f8f8';
        ctx.font = '16px monospace';
        ctx.textAlign = 'left';

        if (phase === 'intro') {
            const fullText = introTexts[textIndex];
            const displayText = fullText.substring(0, charIndex);
            ctx.fillText(displayText, 40, canvasH - 50);
            // Blinking advance indicator
            if (charIndex >= fullText.length && Math.floor(Date.now() / 500) % 2 === 0) {
                ctx.fillText('▼', canvasW - 60, canvasH - 30);
            }
        } else if (phase === 'select') {
            ctx.fillText(`Choose: ${starters[selected].name}`, 40, canvasH - 55);
            ctx.font = '12px monospace';
            ctx.fillStyle = '#a0a0a0';
            ctx.fillText('← → to choose, Space/Enter to select', 40, canvasH - 30);
        } else if (phase === 'confirm') {
            ctx.fillText(`Choose ${starters[selected].name}. Are you sure?`, 40, canvasH - 55);
            // Yes / No buttons
            const yesX = canvasW - 200;
            const noX = canvasW - 100;
            const btnY = canvasH - 42;

            ctx.fillStyle = confirmChoice === 0 ? '#f8d030' : '#808080';
            ctx.font = 'bold 16px monospace';
            ctx.fillText('Yes', yesX, btnY);

            ctx.fillStyle = confirmChoice === 1 ? '#f8d030' : '#808080';
            ctx.fillText('No', noX, btnY);
        } else if (phase === 'celebrate') {
            ctx.fillText(`You received ${chosenStarter.name}!`, 40, canvasH - 50);
            if (celebrateTimer > 1000) {
                ctx.font = '12px monospace';
                ctx.fillStyle = '#a0a0a0';
                ctx.fillText('Press Space/Enter to continue', 40, canvasH - 30);
            }
        }

        ctx.textAlign = 'start'; // Reset
    }

    return { reset, update, render, starters };
})();
