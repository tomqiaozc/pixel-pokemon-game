// evolution.js — Pokemon evolution animation and sequence

const Evolution = (() => {
    let active = false;
    let phase = 'start'; // start, glow, morph, flash, reveal, done
    let timer = 0;
    let glowIntensity = 0;
    let cancelled = false;
    let actionCooldown = 0;

    let prePokemon = null;  // {name, type, color}
    let postPokemon = null; // {name, type, color}
    let onComplete = null;

    // Particle effects
    let sparkles = [];
    let lightRays = [];

    // Phase timings (ms)
    const PHASE_START = 2000;
    const PHASE_GLOW = 2500;
    const PHASE_MORPH = 1500;
    const PHASE_FLASH = 500;
    const PHASE_REVEAL = 2000;

    function start(pre, post, callback) {
        active = true;
        phase = 'start';
        timer = 0;
        glowIntensity = 0;
        cancelled = false;
        actionCooldown = 500;
        prePokemon = pre;
        postPokemon = post;
        onComplete = callback;
        sparkles = [];
        lightRays = [];
    }

    function isActive() { return active; }

    function update(dt) {
        if (!active) return;
        timer += dt;
        actionCooldown = Math.max(0, actionCooldown - dt);

        // B key to cancel during glow/morph phases
        if ((Input.isDown('b') || Input.isDown('B')) && actionCooldown <= 0 &&
            (phase === 'glow' || phase === 'morph')) {
            cancelled = true;
            phase = 'done';
            timer = 0;
            actionCooldown = 300;
        }

        // Update sparkles
        for (const sp of sparkles) {
            sp.age += dt;
            sp.x += sp.vx * dt * 0.05;
            sp.y += sp.vy * dt * 0.05;
        }
        sparkles = sparkles.filter(s => s.age < s.life);

        // Update light rays
        for (const r of lightRays) {
            r.age += dt;
            r.angle += r.speed * dt * 0.001;
        }
        lightRays = lightRays.filter(r => r.age < r.life);

        // Phase transitions
        if (phase === 'start' && timer > PHASE_START) {
            phase = 'glow';
            timer = 0;
        } else if (phase === 'glow') {
            glowIntensity = Math.min(1, timer / PHASE_GLOW);
            // Spawn sparkles during glow
            if (Math.random() < 0.1) {
                sparkles.push(makeSparkle());
            }
            if (timer > PHASE_GLOW) {
                phase = 'morph';
                timer = 0;
                // Spawn light rays
                for (let i = 0; i < 8; i++) {
                    lightRays.push({
                        angle: (Math.PI * 2 / 8) * i,
                        speed: 0.5 + Math.random() * 0.5,
                        length: 60 + Math.random() * 40,
                        width: 3 + Math.random() * 3,
                        age: 0,
                        life: PHASE_MORPH + PHASE_FLASH + 500,
                    });
                }
            }
        } else if (phase === 'morph' && timer > PHASE_MORPH) {
            phase = 'flash';
            timer = 0;
            // Burst of sparkles
            for (let i = 0; i < 20; i++) {
                sparkles.push(makeSparkle());
            }
        } else if (phase === 'flash' && timer > PHASE_FLASH) {
            phase = 'reveal';
            timer = 0;
            glowIntensity = 0;
        } else if (phase === 'reveal') {
            // Spawn celebration sparkles
            if (Math.random() < 0.05) {
                sparkles.push(makeSparkle());
            }
            if (timer > PHASE_REVEAL || (Input.isActionPressed() && actionCooldown <= 0 && timer > 500)) {
                phase = 'done';
                timer = 0;
            }
        } else if (phase === 'done') {
            if (timer > 500 || (Input.isActionPressed() && actionCooldown <= 0)) {
                active = false;
                if (onComplete) onComplete(cancelled);
            }
        }
    }

    function makeSparkle() {
        return {
            x: (Math.random() - 0.5) * 100,
            y: (Math.random() - 0.5) * 80,
            vx: (Math.random() - 0.5) * 2,
            vy: -Math.random() * 2 - 0.5,
            size: 2 + Math.random() * 4,
            age: 0,
            life: 800 + Math.random() * 600,
            color: Math.random() > 0.5 ? '#f8f8f8' : '#f8d830',
        };
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        const cx = canvasW / 2;
        const cy = canvasH * 0.4;

        // Dark starry background
        ctx.fillStyle = '#080818';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Stars
        const starSeed = 42;
        for (let i = 0; i < 50; i++) {
            const sx = ((starSeed * (i + 1) * 7) % canvasW);
            const sy = ((starSeed * (i + 1) * 13) % (canvasH * 0.7));
            const blink = Math.sin(Date.now() * 0.002 + i) * 0.3 + 0.7;
            ctx.fillStyle = `rgba(255, 255, 255, ${blink * 0.6})`;
            ctx.fillRect(sx, sy, 2, 2);
        }

        // Light rays
        for (const r of lightRays) {
            const alpha = (1 - r.age / r.life) * 0.5;
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(r.angle);
            ctx.fillStyle = `rgba(255, 255, 200, ${alpha})`;
            ctx.fillRect(0, -r.width / 2, r.length, r.width);
            ctx.restore();
        }

        // Pokemon sprite area
        const spriteSize = 80;

        if (phase === 'start' || phase === 'glow') {
            // Show pre-evolution form
            drawEvoSprite(ctx, prePokemon, cx, cy, spriteSize, glowIntensity);
        } else if (phase === 'morph') {
            // Cross-fade between forms
            const morphProgress = timer / PHASE_MORPH;
            ctx.globalAlpha = 1 - morphProgress;
            drawEvoSprite(ctx, prePokemon, cx, cy, spriteSize, 0.8);
            ctx.globalAlpha = morphProgress;
            drawEvoSprite(ctx, postPokemon, cx, cy, spriteSize, 0.8);
            ctx.globalAlpha = 1;
        } else if (phase === 'flash') {
            // White flash
            const flashAlpha = 1 - timer / PHASE_FLASH;
            ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
            drawEvoSprite(ctx, postPokemon, cx, cy, spriteSize, flashAlpha * 0.5);
        } else if (phase === 'reveal' || phase === 'done') {
            // Show post-evolution form (or pre if cancelled)
            const pokemon = cancelled ? prePokemon : postPokemon;
            drawEvoSprite(ctx, pokemon, cx, cy, spriteSize, 0);
        }

        // Sparkles
        for (const sp of sparkles) {
            const alpha = 1 - sp.age / sp.life;
            ctx.globalAlpha = alpha;
            ctx.fillStyle = sp.color;
            const sx = cx + sp.x;
            const sy = cy + sp.y;
            // Diamond shape
            ctx.beginPath();
            ctx.moveTo(sx, sy - sp.size);
            ctx.lineTo(sx + sp.size * 0.6, sy);
            ctx.lineTo(sx, sy + sp.size);
            ctx.lineTo(sx - sp.size * 0.6, sy);
            ctx.closePath();
            ctx.fill();
        }
        ctx.globalAlpha = 1;

        // White glow overlay during glow phase
        if (phase === 'glow') {
            const pulseAlpha = glowIntensity * 0.3 * (Math.sin(timer * 0.008) * 0.5 + 0.5);
            ctx.fillStyle = `rgba(255, 255, 255, ${pulseAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }

        // Text box at bottom
        ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
        ctx.fillRect(20, canvasH - 70, canvasW - 40, 55);
        ctx.strokeStyle = '#f8f8f8';
        ctx.lineWidth = 2;
        ctx.strokeRect(20, canvasH - 70, canvasW - 40, 55);

        ctx.fillStyle = '#f8f8f8';
        ctx.font = '15px monospace';
        ctx.textAlign = 'center';

        if (phase === 'start') {
            ctx.fillText(`What? ${prePokemon.name} is evolving!`, canvasW / 2, canvasH - 40);
        } else if (phase === 'glow' || phase === 'morph') {
            ctx.fillText(`${prePokemon.name} is evolving...`, canvasW / 2, canvasH - 45);
            ctx.font = '10px monospace';
            ctx.fillStyle = '#a0a0a0';
            ctx.fillText('Press B to cancel', canvasW / 2, canvasH - 25);
        } else if (phase === 'flash') {
            ctx.fillText('...', canvasW / 2, canvasH - 40);
        } else if (phase === 'reveal') {
            if (cancelled) {
                ctx.fillText(`${prePokemon.name} stopped evolving.`, canvasW / 2, canvasH - 40);
            } else {
                ctx.fillText(`Congratulations! Your ${prePokemon.name}`, canvasW / 2, canvasH - 48);
                ctx.fillText(`evolved into ${postPokemon.name}!`, canvasW / 2, canvasH - 28);
            }
        } else if (phase === 'done') {
            if (cancelled) {
                ctx.fillText(`${prePokemon.name} stopped evolving.`, canvasW / 2, canvasH - 40);
            } else {
                ctx.fillText(`${postPokemon.name} looks ready for battle!`, canvasW / 2, canvasH - 40);
            }
        }

        ctx.textAlign = 'left';
    }

    function drawEvoSprite(ctx, pokemon, cx, cy, size, glow) {
        if (!pokemon) return;

        const half = size / 2;

        // Body
        ctx.fillStyle = pokemon.color || '#a0a0a0';
        ctx.fillRect(cx - half * 0.6, cy - half * 0.6, size * 0.6, size * 0.7);
        ctx.fillRect(cx - half * 0.4, cy - half * 0.8, size * 0.4, size * 0.3);

        // Eyes
        ctx.fillStyle = '#202020';
        ctx.fillRect(cx - half * 0.3, cy - half * 0.4, 4, 4);
        ctx.fillRect(cx + half * 0.1, cy - half * 0.4, 4, 4);

        // Name label below
        ctx.fillStyle = '#f8f8f8';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(pokemon.name, cx, cy + half + 20);

        // Glow overlay
        if (glow > 0) {
            ctx.globalAlpha = glow * 0.6;
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(cx - half * 0.8, cy - half, size * 0.8, size);
            ctx.globalAlpha = 1;
        }

        ctx.textAlign = 'left';
    }

    return { start, isActive, update, render };
})();
