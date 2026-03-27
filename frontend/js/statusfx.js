// statusfx.js — Status condition visuals and stat change animations for battle

const StatusFx = (() => {
    // Active visual effects
    let effects = [];
    let statArrows = [];
    let statusParticles = [];

    // Status icon colors and abbreviations
    const STATUS_INFO = {
        poison:    { abbr: 'PSN', color: '#a040a0', darkColor: '#803080' },
        burn:      { abbr: 'BRN', color: '#f08030', darkColor: '#c06020' },
        paralysis: { abbr: 'PAR', color: '#f8d030', darkColor: '#c0a020' },
        sleep:     { abbr: 'SLP', color: '#8898b0', darkColor: '#607088' },
        freeze:    { abbr: 'FRZ', color: '#98d8d8', darkColor: '#70b0b0' },
        toxic:     { abbr: 'TOX', color: '#702070', darkColor: '#501050' },
        confusion: { abbr: 'CNF', color: '#f85888', darkColor: '#c04060' },
    };

    function reset() {
        effects = [];
        statArrows = [];
        statusParticles = [];
    }

    // Spawn status application visual effect
    function showStatusApplied(status, cx, cy) {
        const info = STATUS_INFO[status];
        if (!info) return;

        if (status === 'poison' || status === 'toxic') {
            // Purple bubbles rising
            for (let i = 0; i < 6; i++) {
                statusParticles.push({
                    x: cx + (Math.random() - 0.5) * 40,
                    y: cy + Math.random() * 20,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: -1.5 - Math.random(),
                    size: 3 + Math.random() * 4,
                    color: info.color,
                    life: 600 + Math.random() * 300,
                    age: 0,
                    type: 'bubble',
                });
            }
        } else if (status === 'burn') {
            // Fire flicker particles
            for (let i = 0; i < 8; i++) {
                statusParticles.push({
                    x: cx + (Math.random() - 0.5) * 30,
                    y: cy + (Math.random() - 0.5) * 20,
                    vx: (Math.random() - 0.5) * 0.3,
                    vy: -1 - Math.random() * 0.5,
                    size: 3 + Math.random() * 3,
                    color: Math.random() > 0.5 ? '#f08030' : '#f8c830',
                    life: 500 + Math.random() * 200,
                    age: 0,
                    type: 'fire',
                });
            }
        } else if (status === 'paralysis') {
            // Yellow electric sparks
            for (let i = 0; i < 5; i++) {
                statusParticles.push({
                    x: cx + (Math.random() - 0.5) * 40,
                    y: cy + (Math.random() - 0.5) * 30,
                    vx: (Math.random() - 0.5) * 2,
                    vy: (Math.random() - 0.5) * 2,
                    size: 2 + Math.random() * 3,
                    color: '#f8d030',
                    life: 400 + Math.random() * 200,
                    age: 0,
                    type: 'spark',
                });
            }
        } else if (status === 'sleep') {
            // Zzz floating up
            effects.push({
                type: 'zzz',
                x: cx + 15,
                y: cy - 10,
                age: 0,
                life: 1200,
            });
        } else if (status === 'freeze') {
            // Ice crystals
            for (let i = 0; i < 6; i++) {
                statusParticles.push({
                    x: cx + (Math.random() - 0.5) * 40,
                    y: cy + (Math.random() - 0.5) * 30,
                    vx: 0,
                    vy: 0,
                    size: 4 + Math.random() * 4,
                    color: '#98d8d8',
                    life: 700 + Math.random() * 300,
                    age: 0,
                    type: 'ice',
                });
            }
        } else if (status === 'confusion') {
            // Wobble effect
            effects.push({
                type: 'confusion',
                x: cx,
                y: cy - 20,
                age: 0,
                life: 1000,
            });
        }
    }

    // Show stat change arrow animation
    function showStatChange(statName, stages, cx, cy) {
        const isUp = stages > 0;
        const sharp = Math.abs(stages) >= 2;

        statArrows.push({
            x: cx,
            y: cy,
            stat: statName,
            up: isUp,
            sharp: sharp,
            age: 0,
            life: 1200,
        });
    }

    function update(dt) {
        // Update status particles
        for (const p of statusParticles) {
            p.age += dt;
            p.x += p.vx * dt * 0.06;
            p.y += p.vy * dt * 0.06;
        }
        statusParticles = statusParticles.filter(p => p.age < p.life);

        // Update effects
        for (const e of effects) {
            e.age += dt;
        }
        effects = effects.filter(e => e.age < e.life);

        // Update stat arrows
        for (const a of statArrows) {
            a.age += dt;
        }
        statArrows = statArrows.filter(a => a.age < a.life);
    }

    function render(ctx) {
        // Render status particles
        for (const p of statusParticles) {
            const alpha = 1 - p.age / p.life;
            ctx.globalAlpha = alpha;

            if (p.type === 'bubble') {
                ctx.fillStyle = p.color;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = 'rgba(255,255,255,0.4)';
                ctx.beginPath();
                ctx.arc(p.x - p.size * 0.3, p.y - p.size * 0.3, p.size * 0.3, 0, Math.PI * 2);
                ctx.fill();
            } else if (p.type === 'fire') {
                ctx.fillStyle = p.color;
                const flicker = Math.sin(p.age * 0.02) * 2;
                ctx.fillRect(p.x - p.size / 2 + flicker, p.y - p.size / 2, p.size, p.size);
            } else if (p.type === 'spark') {
                ctx.strokeStyle = p.color;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p.x + p.vx * 3, p.y + p.vy * 3);
                ctx.stroke();
            } else if (p.type === 'ice') {
                ctx.fillStyle = p.color;
                ctx.fillRect(p.x - p.size / 2, p.y - p.size / 2, p.size, p.size);
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(p.x - 1, p.y - 1, 2, 2);
            }
        }
        ctx.globalAlpha = 1;

        // Render effects
        for (const e of effects) {
            const alpha = 1 - e.age / e.life;
            ctx.globalAlpha = alpha;

            if (e.type === 'zzz') {
                const offset = e.age * 0.02;
                ctx.font = 'bold 16px monospace';
                ctx.fillStyle = '#8898b0';
                ctx.textAlign = 'center';
                ctx.fillText('Z', e.x, e.y - offset);
                if (e.age > 300) {
                    ctx.font = 'bold 12px monospace';
                    ctx.fillText('z', e.x + 10, e.y - offset + 8);
                }
                if (e.age > 600) {
                    ctx.font = 'bold 10px monospace';
                    ctx.fillText('z', e.x + 18, e.y - offset + 14);
                }
                ctx.textAlign = 'left';
            } else if (e.type === 'confusion') {
                // Spinning circles/stars
                const angle = e.age * 0.006;
                ctx.fillStyle = '#f85888';
                for (let i = 0; i < 3; i++) {
                    const a = angle + (i * Math.PI * 2 / 3);
                    const px = e.x + Math.cos(a) * 15;
                    const py = e.y + Math.sin(a) * 6;
                    ctx.font = '10px monospace';
                    ctx.textAlign = 'center';
                    ctx.fillText('\u2605', px, py);
                }
                ctx.textAlign = 'left';
            }
        }
        ctx.globalAlpha = 1;

        // Render stat arrows
        for (const a of statArrows) {
            const alpha = 1 - a.age / a.life;
            const rise = Math.min(a.age / 400, 1) * 30;
            ctx.globalAlpha = alpha;

            const ax = a.x;
            const ay = a.y - rise;
            const color = a.up ? '#48c048' : '#e04038';

            // Arrow
            ctx.fillStyle = color;
            ctx.font = 'bold 20px monospace';
            ctx.textAlign = 'center';
            const arrow = a.up ? '\u25B2' : '\u25BC';
            ctx.fillText(arrow, ax, ay);
            if (a.sharp) {
                ctx.fillText(arrow, ax, ay + (a.up ? 14 : -14));
            }

            // Stat label
            if (a.age > 200) {
                ctx.font = 'bold 11px monospace';
                ctx.fillStyle = '#ffffff';
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 2;
                const label = a.stat;
                ctx.strokeText(label, ax, ay + (a.up ? -10 : 20));
                ctx.fillText(label, ax, ay + (a.up ? -10 : 20));
            }

            ctx.textAlign = 'left';
        }
        ctx.globalAlpha = 1;
    }

    // Render status icon badge next to HP bar
    function renderStatusIcon(ctx, status, x, y) {
        const info = STATUS_INFO[status];
        if (!info) return;

        // Badge background
        ctx.fillStyle = info.color;
        ctx.fillRect(x, y, 30, 14);
        ctx.strokeStyle = info.darkColor;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, 30, 14);

        // Abbreviation text
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(info.abbr, x + 15, y + 11);
        ctx.textAlign = 'left';
    }

    // Get battle text for status damage
    function getStatusDamageText(status, pokemonName) {
        if (status === 'poison' || status === 'toxic') {
            return `${pokemonName} is hurt by poison!`;
        }
        if (status === 'burn') {
            return `${pokemonName} is hurt by its burn!`;
        }
        return '';
    }

    // Get battle text for status prevention
    function getStatusPreventText(status, pokemonName) {
        if (status === 'paralysis') {
            return `${pokemonName} is paralyzed! It can't move!`;
        }
        if (status === 'sleep') {
            return `${pokemonName} is fast asleep!`;
        }
        if (status === 'freeze') {
            return `${pokemonName} is frozen solid!`;
        }
        if (status === 'confusion') {
            return `${pokemonName} is confused!`;
        }
        return '';
    }

    // Get battle text for status cure
    function getStatusCureText(status, pokemonName) {
        if (status === 'sleep') return `${pokemonName} woke up!`;
        if (status === 'freeze') return `${pokemonName} thawed out!`;
        if (status === 'paralysis') return `${pokemonName} was cured of paralysis!`;
        if (status === 'poison' || status === 'toxic') return `${pokemonName} was cured of poison!`;
        if (status === 'burn') return `${pokemonName}'s burn was healed!`;
        if (status === 'confusion') return `${pokemonName} snapped out of its confusion!`;
        return `${pokemonName}'s status was cured!`;
    }

    // Get stat change text
    function getStatChangeText(pokemonName, statName, stages) {
        const abs = Math.abs(stages);
        if (stages > 0) {
            if (abs >= 3) return `${pokemonName}'s ${statName} rose drastically!`;
            if (abs >= 2) return `${pokemonName}'s ${statName} rose sharply!`;
            return `${pokemonName}'s ${statName} rose!`;
        } else {
            if (abs >= 3) return `${pokemonName}'s ${statName} severely fell!`;
            if (abs >= 2) return `${pokemonName}'s ${statName} fell harshly!`;
            return `${pokemonName}'s ${statName} fell!`;
        }
    }

    return {
        reset, update, render,
        showStatusApplied, showStatChange, renderStatusIcon,
        getStatusDamageText, getStatusPreventText, getStatusCureText, getStatChangeText,
        STATUS_INFO,
    };
})();
