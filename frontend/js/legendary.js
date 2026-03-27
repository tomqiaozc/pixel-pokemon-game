// legendary.js — Legendary Pokemon encounter visual effects and battle enhancements

const LegendaryFx = (() => {
    let active = false;
    let introTimer = 0;
    let introPhase = 0; // 0=glow, 1=flash, 2=reveal
    let glowParticles = [];
    let shakeIntensity = 0;
    let legendaryData = null;

    // Legendary Pokemon registry
    const LEGENDARY_DATA = {
        'Mewtwo':   { color: '#b080d0', aura: '#9060c0', tier: 'mythic' },
        'Mew':      { color: '#f0a0c0', aura: '#e080a0', tier: 'mythic' },
        'Articuno': { color: '#90d8f0', aura: '#70b8d8', tier: 'legend' },
        'Zapdos':   { color: '#f8d030', aura: '#d8b020', tier: 'legend' },
        'Moltres':  { color: '#f08030', aura: '#d06820', tier: 'legend' },
    };

    function isLegendary(pokemonName) {
        return !!LEGENDARY_DATA[pokemonName];
    }

    function getLegendaryInfo(pokemonName) {
        return LEGENDARY_DATA[pokemonName] || null;
    }

    function startIntro(pokemon) {
        active = true;
        introTimer = 0;
        introPhase = 0;
        shakeIntensity = 0;
        legendaryData = LEGENDARY_DATA[pokemon.name] || { color: '#f8d030', aura: '#d8b020', tier: 'legend' };
        glowParticles = [];

        for (let i = 0; i < 20; i++) {
            glowParticles.push({
                x: Math.random(),
                y: Math.random(),
                vx: (Math.random() - 0.5) * 0.001,
                vy: -0.001 - Math.random() * 0.001,
                size: 2 + Math.random() * 4,
                alpha: 0.3 + Math.random() * 0.5,
                life: 1500 + Math.random() * 1000,
                age: Math.random() * 500,
            });
        }
    }

    function isIntroActive() { return active; }

    function updateIntro(dt) {
        if (!active) return;
        introTimer += dt;

        // Phase transitions
        if (introPhase === 0 && introTimer > 1500) {
            introPhase = 1;
            shakeIntensity = 6;
        }
        if (introPhase === 1 && introTimer > 2000) {
            introPhase = 2;
            shakeIntensity = 0;
        }
        if (introPhase === 2 && introTimer > 3000) {
            active = false;
        }

        // Shake decay
        if (shakeIntensity > 0) {
            shakeIntensity = Math.max(0, shakeIntensity - dt * 0.005);
        }

        // Update particles
        for (const p of glowParticles) {
            p.age += dt;
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            if (p.age > p.life) {
                p.age = 0;
                p.x = Math.random();
                p.y = 0.8 + Math.random() * 0.2;
            }
        }
    }

    function renderIntro(ctx, canvasW, canvasH) {
        if (!active || !legendaryData) return;

        const progress = Math.min(1, introTimer / 3000);

        // Dark vignette
        if (introPhase <= 1) {
            const vigAlpha = Math.min(0.7, introTimer / 1000);
            ctx.fillStyle = `rgba(0, 0, 0, ${vigAlpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }

        // Glow particles rising
        for (const p of glowParticles) {
            const alpha = p.alpha * (1 - p.age / p.life);
            ctx.globalAlpha = alpha;
            ctx.fillStyle = legendaryData.color;
            ctx.beginPath();
            ctx.arc(p.x * canvasW, p.y * canvasH, p.size, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.globalAlpha = 1;

        // White flash on phase 1
        if (introPhase === 1) {
            const flashProgress = (introTimer - 1500) / 500;
            const flashAlpha = flashProgress < 0.3 ? flashProgress / 0.3 : 1 - (flashProgress - 0.3) / 0.7;
            ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0, flashAlpha * 0.8)})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }

        // Aura glow around battle area during reveal
        if (introPhase === 2) {
            const fadeIn = Math.min(1, (introTimer - 2000) / 500);
            const cx = canvasW / 2;
            const cy = canvasH * 0.35;
            const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 80);
            grad.addColorStop(0, `rgba(255, 255, 255, ${0.2 * fadeIn})`);
            grad.addColorStop(0.5, legendaryData.aura.replace(')', `, ${0.15 * fadeIn})`).replace('rgb', 'rgba'));
            grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
            ctx.fillStyle = grad;
            ctx.fillRect(cx - 80, cy - 80, 160, 160);
        }
    }

    function getShakeOffset() {
        if (shakeIntensity <= 0) return { x: 0, y: 0 };
        return {
            x: (Math.random() - 0.5) * shakeIntensity * 2,
            y: (Math.random() - 0.5) * shakeIntensity * 2,
        };
    }

    // Render gold HP bar for legendary Pokemon
    function renderGoldHpBar(ctx, x, y, width, hpRatio) {
        // Gold bar background
        ctx.fillStyle = '#4a3a10';
        ctx.fillRect(x, y, width, 12);
        ctx.strokeStyle = '#f8d030';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, width, 12);

        // Gold gradient fill
        const grad = ctx.createLinearGradient(x, y, x + width * hpRatio, y);
        grad.addColorStop(0, '#f8d030');
        grad.addColorStop(0.5, '#f8e870');
        grad.addColorStop(1, '#d8a020');
        ctx.fillStyle = grad;
        ctx.fillRect(x + 1, y + 1, (width - 2) * hpRatio, 10);

        // Shimmer effect
        const shimmer = (Date.now() % 2000) / 2000;
        const shimX = x + shimmer * width;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.fillRect(shimX, y + 1, 3, 10);
    }

    // Dramatic pokeball shake animation data
    function getPokeballShakePattern(catchAttempt) {
        // Legendary: more shakes, longer pauses
        return {
            shakeCount: 4,
            shakeDuration: 400,
            pauseBetween: 300,
            shakeAngle: 15,
            catchRate: Math.max(0.05, 0.15 - catchAttempt * 0.02),
        };
    }

    // Overworld glow aura for legendary spawn points
    function renderOverworldAura(ctx, worldX, worldY, camX, camY, scale, pokemonName) {
        const info = LEGENDARY_DATA[pokemonName];
        if (!info) return;

        const sx = (worldX - camX) * scale;
        const sy = (worldY - camY) * scale;
        const time = Date.now();
        const pulse = Math.sin(time * 0.003) * 0.2 + 0.5;

        const grad = ctx.createRadialGradient(sx, sy, 0, sx, sy, 24 * scale);
        grad.addColorStop(0, info.color.replace(')', `, ${0.4 * pulse})`).replace('#', 'rgba(').replace(/([a-f0-9]{2})/gi, (m) => parseInt(m, 16) + ','));

        // Simplified aura circle
        ctx.globalAlpha = pulse * 0.4;
        ctx.fillStyle = info.color;
        ctx.beginPath();
        ctx.arc(sx, sy, 20 * scale, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;

        // Sparkle particles
        for (let i = 0; i < 3; i++) {
            const angle = (time * 0.002 + i * Math.PI * 2 / 3);
            const dist = 16 * scale;
            const px = sx + Math.cos(angle) * dist;
            const py = sy + Math.sin(angle) * dist;
            ctx.fillStyle = '#ffffff';
            ctx.globalAlpha = 0.6 * pulse;
            ctx.fillRect(px - 1, py - 1, 2, 2);
        }
        ctx.globalAlpha = 1;
    }

    return {
        isLegendary, getLegendaryInfo,
        startIntro, isIntroActive, updateIntro, renderIntro, getShakeOffset,
        renderGoldHpBar, getPokeballShakePattern, renderOverworldAura,
        LEGENDARY_DATA,
    };
})();
