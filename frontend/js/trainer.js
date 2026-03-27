// trainer.js — Trainer battle UI enhancements

const TrainerBattle = (() => {
    let active = false;
    let phase = 'idle'; // idle, intro_slide, intro_text, battle, victory, badge_award
    let introTimer = 0;
    let trainerData = null;
    let isGymLeader = false;
    let badgeData = null;

    // Intro animation
    let trainerSlideX = 0; // slides from offscreen
    let playerSlideX = 0;
    let slideComplete = false;

    // Victory screen
    let victoryTimer = 0;
    let rewardMoney = 0;

    // Badge award
    let badgeTimer = 0;
    let badgeShineAngle = 0;

    function startTrainerBattle(trainer, gymLeader, badge) {
        active = true;
        trainerData = trainer;
        isGymLeader = gymLeader || false;
        badgeData = badge || null;
        phase = 'intro_slide';
        introTimer = 0;
        trainerSlideX = 800; // start offscreen right
        playerSlideX = -200; // start offscreen left
        slideComplete = false;
        rewardMoney = isGymLeader ? 5000 : trainer.pokemon ? trainer.pokemon[0].level * 50 : 200;
    }

    function isActive() { return active; }

    function update(dt, ctx, canvasW, canvasH) {
        if (!active) return { done: false };

        introTimer += dt;

        if (phase === 'intro_slide') {
            // Slide trainers in from sides
            trainerSlideX = Math.max(0, trainerSlideX - dt * 0.8);
            playerSlideX = Math.min(0, playerSlideX + dt * 0.8);

            if (trainerSlideX <= 0 && playerSlideX >= 0) {
                phase = 'intro_text';
                introTimer = 0;
            }
            return { done: false };
        }

        if (phase === 'intro_text') {
            // Show trainer intro text with dialogue
            if (!Dialogue.isActive() && introTimer > 100) {
                const introLines = isGymLeader
                    ? [`Gym Leader ${trainerData.name} wants to battle!`, trainerData.title || 'Prepare yourself!']
                    : [`${trainerData.name} wants to battle!`];

                Dialogue.start(trainerData.name, introLines, {
                    onComplete: () => {
                        phase = 'battle';
                    },
                });
            }
            if (Dialogue.isActive()) {
                Dialogue.update(dt);
            }
            return { done: false };
        }

        if (phase === 'battle') {
            // Delegate to regular Battle system
            return { done: false, startBattle: true, pokemon: trainerData.pokemon };
        }

        if (phase === 'victory') {
            victoryTimer += dt;
            if (Dialogue.isActive()) {
                Dialogue.update(dt);
            } else if (victoryTimer > 300) {
                if (isGymLeader && badgeData) {
                    phase = 'badge_award';
                    badgeTimer = 0;
                } else {
                    active = false;
                    return { done: true, won: true };
                }
            }
            return { done: false };
        }

        if (phase === 'badge_award') {
            badgeTimer += dt;
            badgeShineAngle += dt * 0.005;

            if (Dialogue.isActive()) {
                Dialogue.update(dt);
            } else if (badgeTimer > 500 && !Dialogue.isActive()) {
                if (badgeTimer < 600) {
                    Dialogue.start(trainerData.name, [
                        `You've earned the ${badgeData.name}!`,
                        'Congratulations on your victory!',
                    ], {
                        onComplete: () => {
                            active = false;
                        },
                    });
                }
            }

            if (!active) {
                return { done: true, won: true, badge: badgeData };
            }
            return { done: false };
        }

        return { done: false };
    }

    function showVictory() {
        phase = 'victory';
        victoryTimer = 0;
        const defeatLines = isGymLeader
            ? [`I can't believe I lost...`, `You are a truly skilled trainer!`]
            : [`You're stronger than I thought!`];

        Dialogue.start(trainerData.name, [
            ...defeatLines,
            `You received $${rewardMoney} for winning!`,
        ]);
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        if (phase === 'intro_slide' || phase === 'intro_text') {
            renderTrainerIntro(ctx, canvasW, canvasH);
        }

        if (phase === 'badge_award') {
            renderBadgeAward(ctx, canvasW, canvasH);
        }

        // Dialogue overlay
        if (Dialogue.isActive()) {
            Dialogue.render(ctx, canvasW, canvasH);
        }
    }

    function renderTrainerIntro(ctx, canvasW, canvasH) {
        // Dark background
        ctx.fillStyle = '#181818';
        ctx.fillRect(0, 0, canvasW, canvasH);

        // VS flash
        if (phase === 'intro_text') {
            ctx.fillStyle = '#f8f8f8';
            ctx.font = 'bold 48px monospace';
            ctx.textAlign = 'center';
            const flash = Math.sin(introTimer * 0.01) * 0.3 + 0.7;
            ctx.globalAlpha = flash;
            ctx.fillText('VS', canvasW / 2, canvasH / 2 - 20);
            ctx.globalAlpha = 1;
        }

        // Trainer sprite (right side, sliding in)
        const trainerX = canvasW * 0.65 + trainerSlideX;
        const trainerY = canvasH * 0.3;
        drawLargeTrainerSprite(ctx, trainerX, trainerY, 5, trainerData);

        // Trainer name plate
        if (phase === 'intro_text') {
            const nameW = Math.max(180, trainerData.name.length * 14 + 40);
            ctx.fillStyle = 'rgba(200, 50, 50, 0.9)';
            ctx.fillRect(canvasW - nameW - 20, trainerY + 130, nameW, 32);
            ctx.fillStyle = '#f8f8f8';
            ctx.font = 'bold 16px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(trainerData.name, canvasW - nameW / 2 - 20, trainerY + 152);
        }

        // Player sprite (left side, sliding in)
        const playerXPos = canvasW * 0.15 + playerSlideX;
        const playerYPos = canvasH * 0.45;
        const playerSprite = Sprites.drawPlayer(3, 0);
        ctx.drawImage(playerSprite, playerXPos, playerYPos, 16 * 5, 16 * 5);

        ctx.textAlign = 'left';
    }

    function renderBadgeAward(ctx, canvasW, canvasH) {
        // Dark overlay with spotlight
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        ctx.fillRect(0, 0, canvasW, canvasH);

        if (!badgeData) return;

        // Badge display
        const cx = canvasW / 2;
        const cy = canvasH / 2 - 30;
        const badgeSize = 40;

        // Shine rays
        ctx.save();
        ctx.translate(cx, cy);
        for (let i = 0; i < 8; i++) {
            const angle = badgeShineAngle + (i * Math.PI / 4);
            ctx.save();
            ctx.rotate(angle);
            ctx.fillStyle = `rgba(255, 215, 0, ${0.3 + Math.sin(badgeTimer * 0.003 + i) * 0.2})`;
            ctx.fillRect(-3, -badgeSize * 2, 6, badgeSize * 1.5);
            ctx.restore();
        }
        ctx.restore();

        // Badge shape (octagon)
        drawBadge(ctx, cx, cy, badgeSize, badgeData.index, true);

        // Badge name
        ctx.fillStyle = '#f8d830';
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(badgeData.name, cx, cy + badgeSize + 30);
        ctx.textAlign = 'left';
    }

    function drawLargeTrainerSprite(ctx, x, y, scale, trainer) {
        const s = scale;
        const type = trainer.type || 'Normal';
        const typeColor = {
            Rock: '#a08060', Ground: '#805020', Water: '#4080c0',
            Fire: '#c04020', Grass: '#408040', Electric: '#c0a020',
            Normal: '#808080',
        }[type] || '#808080';

        // Hair
        ctx.fillStyle = '#302010';
        ctx.fillRect(x + 3 * s, y, 10 * s, 4 * s);
        ctx.fillRect(x + 5 * s, y - s, 6 * s, 2 * s);
        // Face
        ctx.fillStyle = '#f8b878';
        ctx.fillRect(x + 3 * s, y + 3 * s, 10 * s, 5 * s);
        // Eyes
        ctx.fillStyle = '#202020';
        ctx.fillRect(x + 4 * s, y + 5 * s, 3 * s, s);
        ctx.fillRect(x + 9 * s, y + 5 * s, 3 * s, s);
        // Body
        ctx.fillStyle = typeColor;
        ctx.fillRect(x + 2 * s, y + 8 * s, 12 * s, 8 * s);
        // Belt
        ctx.fillStyle = '#303030';
        ctx.fillRect(x + 2 * s, y + 14 * s, 12 * s, s);
        // Legs
        ctx.fillStyle = '#404040';
        ctx.fillRect(x + 3 * s, y + 16 * s, 4 * s, 4 * s);
        ctx.fillRect(x + 9 * s, y + 16 * s, 4 * s, 4 * s);
        // Shoes
        ctx.fillStyle = '#302020';
        ctx.fillRect(x + 3 * s, y + 19 * s, 4 * s, 2 * s);
        ctx.fillRect(x + 9 * s, y + 19 * s, 4 * s, 2 * s);
    }

    // Draw a badge icon (reusable by BadgeCase)
    function drawBadge(ctx, cx, cy, size, badgeIndex, earned) {
        const badgeColors = [
            '#a09080', // Boulder (grey/brown)
            '#4090d0', // Cascade (blue)
            '#f8c830', // Thunder (yellow)
            '#78c850', // Rainbow (green)
            '#e85888', // Soul (pink)
            '#a08030', // Marsh (gold)
            '#f08030', // Volcano (orange)
            '#48d048', // Earth (green)
        ];

        const color = earned ? badgeColors[badgeIndex] || '#c0c0c0' : '#404040';
        const shine = earned ? '#ffffff30' : '#00000000';

        // Octagon shape
        ctx.fillStyle = color;
        ctx.beginPath();
        const sides = 8;
        for (let i = 0; i < sides; i++) {
            const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
            const px = cx + Math.cos(angle) * size;
            const py = cy + Math.sin(angle) * size;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fill();

        // Inner shine
        if (earned) {
            ctx.fillStyle = shine;
            ctx.beginPath();
            for (let i = 0; i < sides; i++) {
                const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
                const px = cx + Math.cos(angle) * size * 0.6;
                const py = cy + Math.sin(angle) * size * 0.6;
                if (i === 0) ctx.moveTo(px, py);
                else ctx.lineTo(px, py);
            }
            ctx.closePath();
            ctx.fill();
        }

        // Border
        ctx.strokeStyle = earned ? '#f8f8f8' : '#606060';
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (let i = 0; i < sides; i++) {
            const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
            const px = cx + Math.cos(angle) * size;
            const py = cy + Math.sin(angle) * size;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.stroke();
    }

    return { startTrainerBattle, isActive, update, render, showVictory, drawBadge };
})();
