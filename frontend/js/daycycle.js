// daycycle.js — Day/Night cycle with time-based visuals

const DayCycle = (() => {
    // Time periods: morning (6-10), day (10-17), evening (17-20), night (20-6)
    const PERIODS = {
        morning: { start: 6, end: 10, tint: 'rgba(255, 200, 100, 0.15)', label: 'Morning' },
        day:     { start: 10, end: 17, tint: null, label: 'Day' },
        evening: { start: 17, end: 20, tint: 'rgba(255, 140, 60, 0.25)', label: 'Evening' },
        night:   { start: 20, end: 6,  tint: 'rgba(20, 20, 80, 0.45)', label: 'Night' },
    };

    // 1 real minute = 1 game hour (configurable)
    const REAL_MS_PER_GAME_HOUR = 60 * 1000;

    let gameHour = 10;    // Start at 10am (daytime)
    let gameMinute = 0;
    let accumulator = 0;

    // Transition smoothing
    let currentTintAlpha = 0;
    let currentTintR = 0;
    let currentTintG = 0;
    let currentTintB = 0;

    // Stars for night sky (generated once)
    const stars = [];
    for (let i = 0; i < 40; i++) {
        stars.push({
            x: Math.random(),
            y: Math.random() * 0.6,
            size: 1 + Math.random() * 2,
            twinkleSpeed: 0.002 + Math.random() * 0.003,
            twinkleOffset: Math.random() * Math.PI * 2,
        });
    }

    function update(dt) {
        accumulator += dt;
        const msPerMinute = REAL_MS_PER_GAME_HOUR / 60;

        while (accumulator >= msPerMinute) {
            accumulator -= msPerMinute;
            gameMinute++;
            if (gameMinute >= 60) {
                gameMinute = 0;
                gameHour = (gameHour + 1) % 24;
            }
        }

        // Smoothly interpolate tint
        const target = getTargetTint();
        const lerpSpeed = dt * 0.002;
        currentTintR = lerp(currentTintR, target.r, lerpSpeed);
        currentTintG = lerp(currentTintG, target.g, lerpSpeed);
        currentTintB = lerp(currentTintB, target.b, lerpSpeed);
        currentTintAlpha = lerp(currentTintAlpha, target.a, lerpSpeed);
    }

    function getTargetTint() {
        const t = gameHour + gameMinute / 60;

        if (t >= 10 && t < 17) {
            // Day — no tint
            return { r: 0, g: 0, b: 0, a: 0 };
        } else if (t >= 6 && t < 10) {
            // Morning — golden
            const progress = (t - 6) / 4; // 0 at 6am, 1 at 10am
            const alpha = 0.15 * (1 - progress);
            return { r: 255, g: 200, b: 100, a: alpha };
        } else if (t >= 17 && t < 20) {
            // Evening — amber
            const progress = (t - 17) / 3; // 0 at 5pm, 1 at 8pm
            return {
                r: lerp(255, 20, progress),
                g: lerp(140, 20, progress),
                b: lerp(60, 80, progress),
                a: lerp(0.25, 0.45, progress),
            };
        } else {
            // Night — dark blue
            return { r: 20, g: 20, b: 80, a: 0.45 };
        }
    }

    function getPeriod() {
        const t = gameHour + gameMinute / 60;
        if (t >= 6 && t < 10) return 'morning';
        if (t >= 10 && t < 17) return 'day';
        if (t >= 17 && t < 20) return 'evening';
        return 'night';
    }

    function isNight() {
        return getPeriod() === 'night';
    }

    function getTimeString() {
        const h = gameHour % 12 || 12;
        const m = String(gameMinute).padStart(2, '0');
        const ampm = gameHour < 12 ? 'AM' : 'PM';
        return `${h}:${m} ${ampm}`;
    }

    function getTimeIcon() {
        const period = getPeriod();
        if (period === 'night') return '\u263E'; // moon
        return '\u2600'; // sun
    }

    // Render the tint overlay on the overworld
    function renderOverlay(ctx, canvasW, canvasH, timestamp) {
        if (currentTintAlpha < 0.01) return;

        ctx.fillStyle = `rgba(${Math.round(currentTintR)}, ${Math.round(currentTintG)}, ${Math.round(currentTintB)}, ${currentTintAlpha.toFixed(3)})`;
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Stars at night
        if (isNight() && currentTintAlpha > 0.3) {
            const ts = timestamp || Date.now();
            ctx.fillStyle = '#ffffff';
            for (const star of stars) {
                const twinkle = 0.4 + 0.6 * Math.abs(Math.sin(ts * star.twinkleSpeed + star.twinkleOffset));
                ctx.globalAlpha = twinkle * Math.min(1, (currentTintAlpha - 0.3) / 0.15);
                ctx.fillRect(
                    star.x * canvasW,
                    star.y * canvasH,
                    star.size,
                    star.size,
                );
            }
            ctx.globalAlpha = 1;
        }
    }

    // Render lamp glow effects at night (reads lamp positions from map config)
    function renderLamps(ctx, camX, camY, scale, mapId) {
        if (!isNight() || currentTintAlpha < 0.2) return;

        const mapConfig = MapLoader.getCurrentMap();
        const lamps = mapConfig ? mapConfig.lamps : [];
        if (!lamps || lamps.length === 0) return;

        const TILE = 16;
        const glowAlpha = Math.min(1, (currentTintAlpha - 0.2) / 0.25) * 0.6;

        for (const lamp of lamps) {
            const sx = (lamp.x * TILE + TILE / 2 - camX) * scale;
            const sy = (lamp.y * TILE + TILE / 2 - camY) * scale;

            const gradient = ctx.createRadialGradient(sx, sy, 0, sx, sy, 60 * scale / 3);
            gradient.addColorStop(0, `rgba(255, 220, 100, ${glowAlpha})`);
            gradient.addColorStop(0.5, `rgba(255, 200, 80, ${glowAlpha * 0.4})`);
            gradient.addColorStop(1, 'rgba(255, 200, 80, 0)');

            ctx.fillStyle = gradient;
            ctx.fillRect(sx - 60 * scale / 3, sy - 60 * scale / 3, 120 * scale / 3, 120 * scale / 3);
        }
    }

    // Render time display for pause menu
    function renderTimeDisplay(ctx, x, y) {
        const icon = getTimeIcon();
        const timeStr = getTimeString();
        const period = getPeriod();
        const periodLabel = PERIODS[period].label;

        ctx.font = '12px monospace';
        ctx.textAlign = 'left';
        ctx.fillStyle = '#f8f8f8';
        ctx.fillText(`${icon} ${timeStr} - ${periodLabel}`, x, y);
    }

    // Debug: set time manually
    function setTime(hour, minute) {
        gameHour = hour % 24;
        gameMinute = (minute || 0) % 60;
    }

    function lerp(a, b, t) {
        return a + (b - a) * Math.min(1, Math.max(0, t));
    }

    return {
        update, renderOverlay, renderLamps, renderTimeDisplay,
        getPeriod, isNight, getTimeString, getTimeIcon, setTime,
    };
})();
