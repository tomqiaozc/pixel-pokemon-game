// dialogue.js — NPC dialogue system

const Dialogue = (() => {
    let active = false;
    let npcName = '';
    let lines = [];
    let lineIndex = 0;
    let charIndex = 0;
    let textTimer = 0;
    let actionCooldown = 0;
    let slideProgress = 0; // 0-1 for box slide-up animation
    let choices = null;     // null or [{text, value}, ...]
    let choiceIndex = 0;
    let onComplete = null;
    let onChoice = null;

    const TEXT_SPEED = 28; // ms per character
    const BOX_H = 80;

    function start(name, dialogueLines, callbacks) {
        active = true;
        npcName = name;
        lines = dialogueLines;
        lineIndex = 0;
        charIndex = 0;
        textTimer = 0;
        actionCooldown = 250;
        slideProgress = 0;
        choices = null;
        choiceIndex = 0;
        onComplete = callbacks?.onComplete || null;
        onChoice = callbacks?.onChoice || null;
    }

    function startChoice(name, question, options, callback) {
        active = true;
        npcName = name;
        lines = [question];
        lineIndex = 0;
        charIndex = 0;
        textTimer = 0;
        actionCooldown = 250;
        slideProgress = 0;
        choices = options; // [{text: 'Yes', value: 'yes'}, ...]
        choiceIndex = 0;
        onChoice = callback;
        onComplete = null;
    }

    function isActive() { return active; }

    function update(dt) {
        if (!active) return;

        actionCooldown = Math.max(0, actionCooldown - dt);

        // Slide-up animation
        if (slideProgress < 1) {
            slideProgress = Math.min(1, slideProgress + dt * 0.005);
            return;
        }

        // Typewriter
        const currentLine = lines[lineIndex];
        if (currentLine) {
            textTimer += dt;
            charIndex = Math.min(currentLine.length, Math.floor(textTimer / TEXT_SPEED));
        }

        const action = Input.isActionPressed() && actionCooldown <= 0;

        // Holding action key speeds up text
        if (Input.isActionPressed() && charIndex < (currentLine?.length || 0)) {
            charIndex = Math.min(currentLine.length, charIndex + 2);
        }

        if (action) {
            actionCooldown = 200;

            if (charIndex < (currentLine?.length || 0)) {
                // Skip to end of current line
                charIndex = currentLine.length;
            } else if (choices && lineIndex === lines.length - 1) {
                // Confirm choice
                active = false;
                if (onChoice) onChoice(choices[choiceIndex].value);
            } else if (lineIndex < lines.length - 1) {
                // Advance to next line
                lineIndex++;
                charIndex = 0;
                textTimer = 0;
            } else {
                // End dialogue
                active = false;
                if (onComplete) onComplete();
            }
        }

        // Navigate choices
        if (choices && lineIndex === lines.length - 1 && charIndex >= (currentLine?.length || 0)) {
            const mov = Input.getMovement();
            if (mov && actionCooldown <= 0) {
                if (mov.dy < 0) { choiceIndex = Math.max(0, choiceIndex - 1); actionCooldown = 150; }
                if (mov.dy > 0) { choiceIndex = Math.min(choices.length - 1, choiceIndex + 1); actionCooldown = 150; }
            }
        }
    }

    function render(ctx, canvasW, canvasH) {
        if (!active) return;

        const boxY = canvasH - BOX_H * slideProgress;

        // Semi-transparent dark background
        ctx.fillStyle = 'rgba(16, 16, 32, 0.9)';
        ctx.fillRect(10, boxY, canvasW - 20, BOX_H - 5);

        // Border
        ctx.strokeStyle = '#f8f8f8';
        ctx.lineWidth = 2;
        ctx.strokeRect(10, boxY, canvasW - 20, BOX_H - 5);

        // Inner border
        ctx.strokeStyle = 'rgba(255,255,255,0.3)';
        ctx.lineWidth = 1;
        ctx.strokeRect(14, boxY + 4, canvasW - 28, BOX_H - 13);

        if (slideProgress < 1) return;

        // NPC name label
        if (npcName) {
            const nameW = ctx.measureText(npcName).width + 20;
            ctx.fillStyle = '#304080';
            ctx.fillRect(20, boxY - 14, Math.max(nameW, 80), 18);
            ctx.strokeStyle = '#f8f8f8';
            ctx.lineWidth = 1;
            ctx.strokeRect(20, boxY - 14, Math.max(nameW, 80), 18);

            ctx.fillStyle = '#f8f8f8';
            ctx.font = 'bold 12px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(npcName, 28, boxY - 1);
        }

        // Dialogue text
        const currentLine = lines[lineIndex] || '';
        const displayText = currentLine.substring(0, charIndex);

        ctx.fillStyle = '#f8f8f8';
        ctx.font = '15px monospace';
        ctx.textAlign = 'left';

        // Word wrap
        const maxWidth = canvasW - 60;
        const words = displayText.split(' ');
        let line = '';
        let y = boxY + 25;
        for (const word of words) {
            const testLine = line + (line ? ' ' : '') + word;
            if (ctx.measureText(testLine).width > maxWidth) {
                ctx.fillText(line, 24, y);
                line = word;
                y += 20;
            } else {
                line = testLine;
            }
        }
        ctx.fillText(line, 24, y);

        // Advance indicator
        if (charIndex >= currentLine.length && !choices) {
            if (Math.floor(Date.now() / 400) % 2 === 0) {
                ctx.fillStyle = '#f8f8f8';
                ctx.font = '14px monospace';
                ctx.fillText('\u25BC', canvasW - 40, boxY + BOX_H - 18);
            }
        }

        // Choices
        if (choices && charIndex >= currentLine.length) {
            const choiceBoxW = 120;
            const choiceBoxH = choices.length * 24 + 12;
            const choiceX = canvasW - choiceBoxW - 20;
            const choiceY = boxY - choiceBoxH - 4;

            ctx.fillStyle = 'rgba(16, 16, 32, 0.95)';
            ctx.fillRect(choiceX, choiceY, choiceBoxW, choiceBoxH);
            ctx.strokeStyle = '#f8f8f8';
            ctx.lineWidth = 2;
            ctx.strokeRect(choiceX, choiceY, choiceBoxW, choiceBoxH);

            ctx.font = '14px monospace';
            for (let i = 0; i < choices.length; i++) {
                const cy = choiceY + 20 + i * 24;
                if (i === choiceIndex) {
                    ctx.fillStyle = '#f8d030';
                    ctx.fillText('\u25B6', choiceX + 8, cy);
                }
                ctx.fillStyle = i === choiceIndex ? '#f8f8f8' : '#a0a0a0';
                ctx.fillText(choices[i].text, choiceX + 24, cy);
            }
        }

        ctx.textAlign = 'left';
    }

    return { start, startChoice, isActive, update, render };
})();
