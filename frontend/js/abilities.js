// abilities.js — Pokemon ability display and visual effects in battle

const AbilityFx = (() => {
    // Active ability popups
    let popups = [];
    let abilityParticles = [];

    // Known abilities and their descriptions
    const ABILITY_DATA = {
        'Overgrow':     { desc: 'Powers up Grass-type moves in a pinch.', triggerType: 'passive' },
        'Blaze':        { desc: 'Powers up Fire-type moves in a pinch.', triggerType: 'passive' },
        'Torrent':      { desc: 'Powers up Water-type moves in a pinch.', triggerType: 'passive' },
        'Static':       { desc: 'May cause paralysis on contact.', triggerType: 'contact' },
        'Intimidate':   { desc: 'Lowers the foe\'s Attack on entry.', triggerType: 'switch_in' },
        'Sturdy':       { desc: 'Cannot be knocked out in one hit.', triggerType: 'damage_prevention' },
        'Levitate':     { desc: 'Gives immunity to Ground-type moves.', triggerType: 'immunity' },
        'Flame Body':   { desc: 'May burn the attacker on contact.', triggerType: 'contact' },
        'Poison Point': { desc: 'May poison the attacker on contact.', triggerType: 'contact' },
        'Speed Boost':  { desc: 'Speed rises each turn.', triggerType: 'end_of_turn' },
        'Moxie':        { desc: 'Attack rises after knocking out a foe.', triggerType: 'on_ko' },
        'Drizzle':      { desc: 'Summons rain when entering battle.', triggerType: 'weather' },
        'Drought':      { desc: 'Summons harsh sunlight when entering battle.', triggerType: 'weather' },
        'Sand Stream':  { desc: 'Summons a sandstorm when entering battle.', triggerType: 'weather' },
        'Snow Warning': { desc: 'Summons a hailstorm when entering battle.', triggerType: 'weather' },
        'Wonder Guard': { desc: 'Only super-effective moves hit.', triggerType: 'damage_prevention' },
        'Limber':       { desc: 'Prevents paralysis.', triggerType: 'status_immunity' },
        'Water Veil':   { desc: 'Prevents burns.', triggerType: 'status_immunity' },
        'Swift Swim':   { desc: 'Doubles Speed in rain.', triggerType: 'passive' },
        'Chlorophyll':  { desc: 'Doubles Speed in sun.', triggerType: 'passive' },
    };

    function reset() {
        popups = [];
        abilityParticles = [];
    }

    // Show ability activation popup
    function showActivation(pokemonName, abilityName, cx, cy) {
        popups.push({
            text: `${pokemonName}'s ${abilityName}!`,
            x: cx,
            y: cy - 30,
            age: 0,
            life: 1500,
        });

        // Spawn visual effect based on ability type
        const data = ABILITY_DATA[abilityName];
        if (!data) return;

        if (data.triggerType === 'contact') {
            // Sparks or poison particles around the Pokemon
            const color = abilityName === 'Static' ? '#f8d030'
                        : abilityName === 'Flame Body' ? '#f08030'
                        : '#a040a0';
            for (let i = 0; i < 5; i++) {
                abilityParticles.push({
                    x: cx + (Math.random() - 0.5) * 40,
                    y: cy + (Math.random() - 0.5) * 30,
                    vx: (Math.random() - 0.5) * 1.5,
                    vy: (Math.random() - 0.5) * 1.5,
                    size: 3 + Math.random() * 3,
                    color: color,
                    life: 600,
                    age: 0,
                });
            }
        } else if (data.triggerType === 'damage_prevention') {
            // Shield flash effect
            popups[popups.length - 1].shield = true;
            popups[popups.length - 1].shieldX = cx;
            popups[popups.length - 1].shieldY = cy;
        } else if (data.triggerType === 'switch_in' && abilityName === 'Intimidate') {
            // Screen shake effect indicator
            popups[popups.length - 1].shake = true;
        }
    }

    function update(dt) {
        for (const p of popups) {
            p.age += dt;
        }
        popups = popups.filter(p => p.age < p.life);

        for (const p of abilityParticles) {
            p.age += dt;
            p.x += p.vx * dt * 0.06;
            p.y += p.vy * dt * 0.06;
        }
        abilityParticles = abilityParticles.filter(p => p.age < p.life);
    }

    function render(ctx) {
        // Render ability particles
        for (const p of abilityParticles) {
            const alpha = 1 - p.age / p.life;
            ctx.globalAlpha = alpha;
            ctx.fillStyle = p.color;
            ctx.fillRect(p.x - p.size / 2, p.y - p.size / 2, p.size, p.size);
        }
        ctx.globalAlpha = 1;

        // Render popups
        for (const p of popups) {
            const alpha = p.age < 200 ? p.age / 200
                        : p.age > p.life - 300 ? (p.life - p.age) / 300
                        : 1;
            ctx.globalAlpha = alpha;

            // Shield flash
            if (p.shield && p.age < 400) {
                const shieldAlpha = (1 - p.age / 400) * 0.4;
                ctx.strokeStyle = `rgba(100, 200, 255, ${shieldAlpha})`;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(p.shieldX, p.shieldY, 30 + p.age * 0.03, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Text popup background
            const textW = ctx.measureText ? 200 : 200;
            const boxX = p.x - textW / 2;
            const boxY = p.y - 10;

            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(boxX, boxY, textW, 22);
            ctx.strokeStyle = '#f8d030';
            ctx.lineWidth = 1;
            ctx.strokeRect(boxX, boxY, textW, 22);

            ctx.fillStyle = '#f8f8f8';
            ctx.font = 'bold 11px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(p.text, p.x, p.y + 5);
            ctx.textAlign = 'left';
        }
        ctx.globalAlpha = 1;
    }

    // Render ability name on info panel (small text below HP)
    function renderAbilityLabel(ctx, abilityName, x, y) {
        if (!abilityName) return;

        ctx.fillStyle = '#808080';
        ctx.font = '9px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`[${abilityName}]`, x, y);
    }

    // Get ability description for tooltip
    function getDescription(abilityName) {
        const data = ABILITY_DATA[abilityName];
        return data ? data.desc : 'No data available.';
    }

    // Get ability activation message for battle log
    function getActivationMessage(pokemonName, abilityName) {
        return `${pokemonName}'s ${abilityName}!`;
    }

    // Check if ability triggers weather on switch-in
    function getWeatherAbility(abilityName) {
        const weatherMap = {
            'Drizzle': 'rain',
            'Drought': 'sun',
            'Sand Stream': 'sandstorm',
            'Snow Warning': 'hail',
        };
        return weatherMap[abilityName] || null;
    }

    return {
        reset, update, render,
        showActivation, renderAbilityLabel,
        getDescription, getActivationMessage, getWeatherAbility,
        ABILITY_DATA,
    };
})();
