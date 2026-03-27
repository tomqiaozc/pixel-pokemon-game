// weather.js — Weather visual effects for battle and overworld

const Weather = (() => {
    // Weather types: clear, rain, sun, sandstorm, hail
    let currentWeather = 'clear';
    let weatherTimer = 0;
    let turnsRemaining = 0;
    let transitionAlpha = 0; // 0 = no overlay, 1 = full overlay
    let particles = [];
    let lightningTimer = 0;
    let lightningFlash = 0;

    // Battle weather state
    let battleActive = false;

    // Overworld weather system
    let overworldTimer = 0;
    const OVERWORLD_WEATHER_INTERVAL = 120000; // Check every 2 game-minutes
    let overworldWeatherActive = false;
    let overworldWeatherDuration = 0;

    // Per-map weather configuration
    const MAP_WEATHER = {
        route_1:        { types: ['rain'], chance: 0.15 },
        route_2:        { types: ['rain'], chance: 0.20 },
        viridian_city:  { types: ['rain'], chance: 0.10 },
        pewter_city:    { types: ['sandstorm'], chance: 0.10 },
        pallet_town:    { types: ['rain'], chance: 0.08 },
    };

    function setWeather(type, turns) {
        currentWeather = type;
        turnsRemaining = turns || 5;
        transitionAlpha = 0;
        particles = [];
        lightningTimer = 0;
        lightningFlash = 0;

        if (type !== 'clear') {
            initParticles(type);
        }
    }

    function clearWeather() {
        currentWeather = 'clear';
        turnsRemaining = 0;
    }

    function getWeather() {
        return currentWeather;
    }

    function initParticles(type) {
        particles = [];
        const count = type === 'rain' ? 60 : type === 'sandstorm' ? 40 : type === 'hail' ? 30 : 0;

        for (let i = 0; i < count; i++) {
            particles.push(createParticle(type, true));
        }
    }

    function createParticle(type, randomY) {
        const p = {
            x: Math.random(),
            y: randomY ? Math.random() : -0.05,
            speed: 0,
            vx: 0,
            size: 2,
            alpha: 1,
        };

        if (type === 'rain') {
            p.speed = 0.003 + Math.random() * 0.002;
            p.vx = 0.001;
            p.size = 2 + Math.random() * 2;
            p.alpha = 0.5 + Math.random() * 0.4;
        } else if (type === 'sandstorm') {
            p.speed = 0.0005 + Math.random() * 0.001;
            p.vx = 0.003 + Math.random() * 0.002;
            p.size = 2 + Math.random() * 3;
            p.alpha = 0.3 + Math.random() * 0.3;
        } else if (type === 'hail') {
            p.speed = 0.002 + Math.random() * 0.002;
            p.vx = 0.0005;
            p.size = 3 + Math.random() * 3;
            p.alpha = 0.6 + Math.random() * 0.3;
        }

        return p;
    }

    function update(dt) {
        if (currentWeather === 'clear') {
            transitionAlpha = Math.max(0, transitionAlpha - dt * 0.002);
            return;
        }

        // Fade in overlay
        transitionAlpha = Math.min(1, transitionAlpha + dt * 0.002);

        // Update particles
        for (const p of particles) {
            p.y += p.speed * dt;
            p.x += p.vx * dt;

            // Wrap around
            if (p.y > 1.1) {
                p.y = -0.05;
                p.x = Math.random();
            }
            if (p.x > 1.1) {
                p.x = -0.05;
            }
        }

        // Lightning for rain
        if (currentWeather === 'rain') {
            lightningTimer += dt;
            if (lightningTimer > 4000 + Math.random() * 6000) {
                lightningFlash = 200;
                lightningTimer = 0;
            }
            if (lightningFlash > 0) {
                lightningFlash = Math.max(0, lightningFlash - dt);
            }
        }
    }

    // Render weather in battle
    function renderBattle(ctx, canvasW, canvasH) {
        if (currentWeather === 'clear' && transitionAlpha <= 0) return;

        const alpha = transitionAlpha;

        // Tint overlay
        if (currentWeather === 'rain') {
            ctx.fillStyle = `rgba(40, 60, 120, ${0.15 * alpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH * 0.7);
        } else if (currentWeather === 'sun') {
            ctx.fillStyle = `rgba(255, 200, 60, ${0.12 * alpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH * 0.7);

            // Lens flare
            const flareX = canvasW * 0.85;
            const flareY = 30;
            const grad = ctx.createRadialGradient(flareX, flareY, 0, flareX, flareY, 50);
            grad.addColorStop(0, `rgba(255, 255, 200, ${0.4 * alpha})`);
            grad.addColorStop(0.5, `rgba(255, 240, 150, ${0.15 * alpha})`);
            grad.addColorStop(1, 'rgba(255, 240, 150, 0)');
            ctx.fillStyle = grad;
            ctx.fillRect(flareX - 50, flareY - 50, 100, 100);
        } else if (currentWeather === 'sandstorm') {
            ctx.fillStyle = `rgba(180, 150, 80, ${0.2 * alpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH * 0.7);
        } else if (currentWeather === 'hail') {
            ctx.fillStyle = `rgba(180, 210, 240, ${0.12 * alpha})`;
            ctx.fillRect(0, 0, canvasW, canvasH * 0.7);
        }

        // Draw particles
        for (const p of particles) {
            const px = p.x * canvasW;
            const py = p.y * (canvasH * 0.7);
            ctx.globalAlpha = p.alpha * alpha;

            if (currentWeather === 'rain') {
                ctx.strokeStyle = '#8090c0';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(px, py);
                ctx.lineTo(px + 2, py + p.size * 3);
                ctx.stroke();
            } else if (currentWeather === 'sandstorm') {
                ctx.fillStyle = '#c8b060';
                ctx.fillRect(px, py, p.size, p.size * 0.6);
            } else if (currentWeather === 'hail') {
                ctx.fillStyle = '#d8e8f8';
                ctx.fillRect(px - p.size / 2, py - p.size / 2, p.size, p.size);
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(px - p.size / 4, py - p.size / 4, p.size / 2, p.size / 2);
            }
        }
        ctx.globalAlpha = 1;

        // Lightning flash
        if (lightningFlash > 0) {
            ctx.fillStyle = `rgba(255, 255, 255, ${(lightningFlash / 200) * 0.3})`;
            ctx.fillRect(0, 0, canvasW, canvasH);
        }

        // Weather icon in corner
        renderWeatherIcon(ctx, canvasW - 35, 8);
    }

    // Render weather in overworld
    function renderOverworld(ctx, canvasW, canvasH) {
        if (currentWeather === 'clear' && transitionAlpha <= 0) return;

        const alpha = transitionAlpha * 0.7; // lighter in overworld

        // Particles
        for (const p of particles) {
            const px = p.x * canvasW;
            const py = p.y * canvasH;
            ctx.globalAlpha = p.alpha * alpha;

            if (currentWeather === 'rain') {
                ctx.strokeStyle = '#6080b0';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(px, py);
                ctx.lineTo(px + 1, py + p.size * 2);
                ctx.stroke();
            } else if (currentWeather === 'hail') {
                ctx.fillStyle = '#c8d8e8';
                ctx.fillRect(px, py, p.size * 0.8, p.size * 0.8);
            } else if (currentWeather === 'sandstorm') {
                ctx.fillStyle = '#b0a050';
                ctx.fillRect(px, py, p.size, p.size * 0.5);
            }
        }
        ctx.globalAlpha = 1;
    }

    function renderWeatherIcon(ctx, x, y) {
        if (currentWeather === 'clear') return;

        const icons = {
            rain: '\u{1F327}',
            sun: '\u2600',
            sandstorm: '\u{1F32A}',
            hail: '\u{1F328}',
        };

        // Icon background
        ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
        ctx.fillRect(x - 2, y - 2, 28, 22);

        ctx.font = '14px monospace';
        ctx.textAlign = 'center';
        ctx.fillStyle = '#ffffff';
        // Use text abbreviation since emoji support varies
        const labels = { rain: 'RN', sun: 'SN', sandstorm: 'SS', hail: 'HL' };
        ctx.fillText(labels[currentWeather] || '', x + 12, y + 14);
        ctx.textAlign = 'left';
    }

    // Get weather message for battle start
    function getWeatherMessage() {
        const messages = {
            rain: 'It started to rain!',
            sun: 'The sunlight turned harsh!',
            sandstorm: 'A sandstorm kicked up!',
            hail: 'It started to hail!',
        };
        return messages[currentWeather] || '';
    }

    function getEndMessage() {
        const messages = {
            rain: 'The rain stopped.',
            sun: 'The harsh sunlight faded.',
            sandstorm: 'The sandstorm subsided.',
            hail: 'The hail stopped.',
        };
        return messages[currentWeather] || '';
    }

    // Tick a turn in battle (returns damage messages if applicable)
    // turnsRemaining === 0 means indefinite (ability-triggered weather)
    function tickTurn() {
        if (currentWeather === 'clear') return null;

        if (turnsRemaining > 0) {
            turnsRemaining--;
            if (turnsRemaining <= 0) {
                const msg = getEndMessage();
                clearWeather();
                return { ended: true, message: msg };
            }
        }
        return { ended: false };
    }

    // Check if weather does end-of-turn damage
    function doesDamage() {
        return currentWeather === 'sandstorm' || currentWeather === 'hail';
    }

    // Types immune to weather damage (accepts single type string or array of types)
    function isImmuneToWeatherDamage(pokemonType) {
        const types = Array.isArray(pokemonType) ? pokemonType : [pokemonType];
        if (currentWeather === 'sandstorm') {
            return types.some(t => ['Rock', 'Ground', 'Steel'].includes(t));
        }
        if (currentWeather === 'hail') {
            return types.some(t => t === 'Ice');
        }
        return true;
    }

    function getWeatherDamageMessage(pokemonName) {
        if (currentWeather === 'sandstorm') {
            return `${pokemonName} is buffeted by the sandstorm!`;
        }
        if (currentWeather === 'hail') {
            return `${pokemonName} is pelted by hail!`;
        }
        return '';
    }

    // Update overworld weather (called from game loop)
    function updateOverworld(dt, mapId) {
        if (overworldWeatherActive) {
            overworldWeatherDuration -= dt;
            if (overworldWeatherDuration <= 0) {
                clearWeather();
                overworldWeatherActive = false;
            }
            return;
        }

        overworldTimer += dt;
        if (overworldTimer < OVERWORLD_WEATHER_INTERVAL) return;
        overworldTimer = 0;

        const config = MAP_WEATHER[mapId];
        if (!config) return;

        if (Math.random() < config.chance) {
            const type = config.types[Math.floor(Math.random() * config.types.length)];
            const duration = 30000 + Math.random() * 60000; // 30-90 seconds
            setWeather(type, 99); // 99 turns — overworld doesn't use turn counter
            overworldWeatherActive = true;
            overworldWeatherDuration = duration;
        }
    }

    // Called when player enters a new map
    function onMapChange(mapId) {
        // Clear overworld weather on map change (each map rolls its own)
        if (overworldWeatherActive) {
            clearWeather();
            overworldWeatherActive = false;
        }
        overworldTimer = 0;
    }

    return {
        setWeather, clearWeather, getWeather, update,
        renderBattle, renderOverworld, renderWeatherIcon,
        getWeatherMessage, getEndMessage,
        tickTurn, doesDamage, isImmuneToWeatherDamage, getWeatherDamageMessage,
        updateOverworld, onMapChange,
    };
})();
